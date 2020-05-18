#!/usr/bin/env python2.7

# Hello!
# This is matelight-jockey 0.1 or something.
# It is based on coon's ingenius simple matetv tool.
# (which you can find @ https://github.com/c-base/matetv )
#
# See LICENSE and README.md for more information, for now.
# (Inline docs etc. will follow - this is still a hack)

from PyQt4 import QtCore, QtGui, Qt, QtNetwork
from PyQt4.QtGui import QApplication, QLineEdit, QTableWidget, QTableWidgetItem, QWidget, QVBoxLayout, QFileDialog
# from gui import Ui_Form

import struct
import time
import sys

import cv2
import numpy as np

import socket

import os

import pygame
import pygame.midi
from pygame.locals import *

from Axon.ThreadedComponent import threadedcomponent
from Axon.ThreadedComponent import threadedadaptivecommscomponent
from Axon.Ipc import shutdownMicroprocess
from Axon.Scheduler import scheduler

from Kamaelia.Chassis.Pipeline import Pipeline
from Kamaelia.Chassis.Graphline import Graphline
from Kamaelia.Util.Console import ConsoleEchoer
from Kamaelia.Automata.Behaviours import loopingCounter

from pprint import pprint


IP = "localhost"  # "matelight.cbrp3.c-base.org"
PORT = 1337
RESX = 40
RESY = 16
RESOLUTION = (RESX, RESY)
#KAMERA_NR = 0
#TOTAL_PIXELS = RESX * RESY
#FRAMES_PER_SECOND = 50
#TIME_BETWEEN_FRAMES = 1.0 / FRAMES_PER_SECOND

#screennames = ['bitwiglogo.png', '1up.png', 'text-B.png', 'text-bit.png', 'text-wig.png', 'rauschen.png']
#screens = {}


class ImageRepository(threadedcomponent):
    def __init__(self, images=[]):
        super(ImageRepository, self).__init__()

        self.images = {}

        if len(images) > 0:
            for no, item in enumerate(images):
                self.images[no] = cv.LoadImage(os.path.abspath("./" + item))


    def finished(self):
        while self.dataReady("control"):
            msg = self.recv("control")
            if type(msg) in (shutdownMicroprocess):
                self.send(msg, "signal")
                return True
        return False


    def main(self):
        while not self.finished():

            while not self.anyReady():
                self.pause()

            while self.dataReady("inbox"):
                no = int(self.recv("inbox"))
                self.send(self.images[no], "outbox")


class MidiRouter(threadedadaptivecommscomponent):
    def __init__(self, routing={}):
        super(MidiRouter, self).__init__()

        self.routing = routing

        for boxname in routing.itervalues():
            self.addOutbox(boxname)

    def finished(self):
        while self.dataReady("control"):
            msg = self.recv("control")
            if type(msg) in (shutdownMicroprocess):
                self.send(msg, "signal")
                return True
        return False


    def main(self):
        while not self.finished():
            while not self.dataReady("inbox"):
                self.pause()

            while self.dataReady("inbox"):
                midiinput = self.recv("inbox")

                chan = midiinput[0][1]
                val = midiinput[0][2]

                if chan in self.routing.keys():
                    self.send(val, self.routing[chan])



class MidiInput(threadedcomponent):
    def __init__(self, device_id=None, debug=True):
        super(MidiInput, self).__init__()

        self.debug = debug

        pygame.midi.init()

        self.midi_print_device_info()

        if not device_id:
            self.midi_device = pygame.midi.get_default_input_id()
        else:
            self.midi_device = int(device_id)

        try:
            self.midi = pygame.midi.Input(self.midi_device, 0)
        except pygame.midi.MidiException as e:
            print("ERR: Could not open midi input device %s" % self.midi_device)
            print("ERR: Exception ", e.__dict__)
            sys.exit()

        print "INFO: Opened midi input device %s" % self.midi_device
        self.midi_print_device_info()

    def midi_print_device_info(self):
        for i in range(pygame.midi.get_count()):
            r = pygame.midi.get_device_info(i)
            (interf, name, inputs, outputs, opened) = r

            in_out = ""
            if inputs:
                in_out = "(input)"
            if outputs:
                in_out = "(output)"

            print ("%2i: interface :%s:, name :%s:, opened :%s:  %s" %
                   (i, interf, name, opened, in_out))

    def finished(self):
        while self.dataReady("control"):
            msg = self.recv("control")
            if type(msg) in (shutdownMicroprocess):
                self.send(msg, "signal")
                return True
        return False


    def main(self):
        while not self.finished():
            if self.midi.poll():
                while self.midi.poll():

                    mididata = self.midi.read(1)
                    if len(mididata) > 1:
                        mididata = mididata[-1]
                    else:
                        mididata = mididata[0]

                    if self.debug:
                        print(mididata)



                    self.send(mididata, "outbox")


class CVCamera(threadedcomponent):
    def __init__(self, device_id=0):
        super(CVCamera, self).__init__()
        self.cam = cv2.VideoCapture(device_id)
        self.cam.set(3, 320)
        self.cam.set(4, 240)


    def finished(self):
        while self.dataReady("control"):
            msg = self.recv("control")
            if type(msg) in (shutdownMicroprocess):
                self.send(msg, "signal")
                return True
        return False


    def main(self):
        while not self.finished():
            err, frame = self.cam.read()

            if frame == None:
                print("Oh, no camera attached! Change this and rerun!")
                sys.exit()

            newframe = cv2.resize(frame, RESOLUTION)
            self.send(newframe, "outbox")


class Matelight(threadedcomponent):
    def __init__(self, address='127.0.0.1', port=1337):
        super(Matelight, self).__init__()
        self.address = address
        self.port = port


    def finished(self):
        while self.dataReady("control"):
            msg = self.recv("control")
            if type(msg) in (shutdownMicroprocess):
                self.send(msg, "signal")
                return True
        return False

    def cmd_send_image(self, image):  # , brightness, gamma):
        ml_data = bytearray(image) + "\00\00\00\00"
        #data_c = bytearray([x for x in list(ml_data)])
        try:

            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(ml_data, (self.address, self.port))
        except Exception as e:
            print("Meeeh: ", e)

    def main(self):
        self.framecount = 0
        self.lasttime = 0
        while not self.finished():

            while not self.anyReady():
                self.pause()

            while self.dataReady("inbox"):
                frame = self.recv("inbox")

                self.cmd_send_image(frame)
                self.framecount += 1
                if time.time() >= self.lasttime + 1:
                    print(self.framecount)
                    self.framecount = 0
                    self.lasttime = time.time()



class ColorFilter(threadedcomponent):
    Inboxes = {'inbox': "Image input",
               'control': "Control input",
               'red': "Filter red hue",
               'green': "Filter green hue",
               'blue': "Filter blue hue",
               "brightness": "Filter Brightness",
               "gamma": "Filter Gamma"
    }

    def __init__(self, settings=[127, 127, 127, 127, 0]):
        super(ColorFilter, self).__init__()
        self.settings = settings

    def finished(self):
        while self.dataReady("control"):
            msg = self.recv("control")
            if type(msg) in (shutdownMicroprocess):
                self.send(msg, "signal")
                return True
        return False

    def correct_gamma(self, img):
        img = img / 255.0
        img = cv2.pow(img, 1 - self.settings[4] / 127.0)
        return np.uint8(img * 255.0)

    def correct_brightness(self, img):
        data_c = bytearray(img) + "\00\00\00\00"

        result = bytearray([int(((x / 255.0) ** (1 - self.settings[4] / 127.0)) * 255 * (self.settings[3] / 127.0)) for x in list(data_c)])

        return result

    def correct_color(self, img):
        rows, cols, colors = img.shape

        # This can probably be done 3 times as elegant.
        for row in xrange(rows):
            for column in xrange(cols):
                img[row, column][0] = int(img[row, column][0] * self.settings[0] / 127.0)  # red
                img[row, column][1] = int(img[row, column][1] * self.settings[1] / 127.0)  # green
                img[row, column][2] = int(img[row, column][2] * self.settings[2] / 127.0)  # blue

        return img

    def getlastmessage(self, boxname):
        while self.dataReady(boxname):
            data = self.recv(boxname)
        return data

    def main(self):
        while not self.finished():
            while not self.anyReady():
                self.pause()

            while self.anyReady():

                for no, param in enumerate(['red', 'green', 'blue', 'brightness', 'gamma']):
                     if self.dataReady(param):
                         self.settings[no] = self.recv(param)

                if self.dataReady("inbox"):
                    break

            while self.dataReady("inbox"):
                while self.dataReady("inbox"):
                    frame = self.recv("inbox")

                frame = np.array(frame)

                frame = self.correct_color(frame)
                #frame = self.correct_gamma(frame)
                frame = self.correct_brightness(frame)

                # for row in xrange(rows):
                #     for column in xrange(cols):
                #         red = int(frame[row, column][2] * self.settings[0] / 127.0 * brightness)
                #         green = int(frame[row, column][1] * self.settings[1] / 127.0 * brightness)
                #         blue = int(frame[row, column][0] * self.settings[2] / 127.0 * brightness)
                #         bitstring.extend(struct.pack('BBB', red, green, blue))

                self.send(frame, "outbox")



class MyForm(QtGui.QMainWindow):
    def __init__(self, parent=None, device_id=None):

        pygame.init()

        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        QtCore.QObject.connect(self.ui.pushButton_stream_webcam, QtCore.SIGNAL("clicked()"), self.cmd_stream_webcam)
        QtCore.QObject.connect(self.ui.horizontalSlider_fps, QtCore.SIGNAL("valueChanged(int)"), self.cmd_fps_changed)
        QtCore.QObject.connect(self.ui.verticalSlider_red, QtCore.SIGNAL("valueChanged(int)"),
                               self.cmd_red_slider_changed)
        QtCore.QObject.connect(self.ui.verticalSlider_green, QtCore.SIGNAL("valueChanged(int)"),
                               self.cmd_green_slider_changed)
        QtCore.QObject.connect(self.ui.verticalSlider_blue, QtCore.SIGNAL("valueChanged(int)"),
                               self.cmd_blue_slider_changed)
        QtCore.QObject.connect(self.ui.verticalSlider_gamma, QtCore.SIGNAL("valueChanged(int)"),
                               self.cmd_gamma_slider_changed)
        QtCore.QObject.connect(self.ui.verticalSlider_brightness, QtCore.SIGNAL("valueChanged(int)"),
                               self.cmd_brightness_slider_changed)


        # Network init
        self.sock = QtNetwork.QUdpSocket()
        self.sock.bind(QtNetwork.QHostAddress.Any, PORT)
        self.connect(self.sock, QtCore.SIGNAL("readyRead()"), self.on_recv_udp_packet)

        self.image = None
        self.streaming = False
        self.threshold = 128
        self.equalize = False
        self.fps = FRAMES_PER_SECOND
        self.time_between_frames = TIME_BETWEEN_FRAMES

        self.max_red = 100
        self.max_green = 100
        self.max_blue = 100
        self.max_gamma = 100
        self.max_brightness = 100


    def cv_resize_and_grayscale(self, input_image, threshold, doEqualize):
        image = cv.CreateImage((input_image.width, input_image.height), 8, 1)
        cv.CvtColor(input_image, image, cv.CV_BGR2GRAY)

        if doEqualize:
            cv.EqualizeHist(image, image)  # equalize the pixel brightness
        cv.Threshold(image, image, threshold, 255, cv.CV_THRESH_OTSU)  # convert to black / white image

        image_resized = cv.CreateImage((RESX, RESY), image.depth, image.channels)  # resize to fit into r0ket display
        cv.Resize(image, image_resized, cv.CV_INTER_NN)

        return image_resized


    # GUI events
    def cmd_load_image(self):
        file_path = str(self.ui.lineEdit_file_path.text())
        self.image = self.cv_load_image(file_path)
        print "image loaded!"

    def cmd_stream_webcam(self):
        end_time = 0
        counter = 1
        screenactive = 0

        while True:

            c = cv.WaitKey(2)

            if c == 27:  # esc
                return

            g = cv.CreateImage(cv.GetSize(frame), cv.IPL_DEPTH_8U, frame.channels)
            gr = frame[128: 384, 0: 640]  # Crop from x, y, w, h -> 100, 200, 100, 200
            ml = cv.CreateImage((40, 16), cv.IPL_DEPTH_8U, frame.channels)
            cv.Resize(gr, ml)
            cv.ShowImage("Matelight TV", gr)

            mididata = False
            if 0:
                if mididata:
                    if mididata[0][0][0] == 176:
                        value = mididata[0][0][2]
                        channel = mididata[0][0][1]
                        if value >= 100:
                            value = 100
                        if channel == 2:
                            self.max_red = value
                        elif channel == 3:
                            self.max_green = value
                        elif channel == 5:
                            self.max_blue = value
                    screennumber = mididata[0][0][1] - 60
                    if mididata[0][0][0] == 144:
                        print("MIDI Notedown received: ", screennumber)
                        screenactive = screennumber
                    elif mididata[0][0][0] == 128:
                        print("MIDI Noteup received: ", screennumber)
                        screenactive = -1
                    else:
                        print(mididata)

            if c >= 49 and c <= 59:
                if screenactive == c - 49:
                    screenactive = -1
                else:
                    screenactive = c - 49

            if screenactive in screens:
                ol = cv.CreateImage((40, 16), cv.IPL_DEPTH_8U, frame.channels)
                cv.Add(ml, screens[screenactive], ol)
                ml = ol
            c = 0

            if time.time() > end_time:
                end_time = time.time() + self.time_between_frames
                # self.cmd_send_image(ml, 0.25, 2)
                self.cmd_send_image(ml, self.max_brightness, self.max_gamma)

            counter += 1

    def cmd_send_image(self, image, brightness, gamma):
        mg_mat = cv.GetMat(image)
        ml_data = self.convert_img_matrix_to_matelight(mg_mat) + "\00\00\00\00"
        data_c = bytearray([int(((x / 255.0) ** (gamma / 100.0)) * 255 * (brightness / 100.0)) for x in list(ml_data)])
        try:

            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(data_c, (IP, PORT))
        except Exception as e:
            print("Meeeh: ", e)

    def cmd_fps_changed(self, value):
        self.fps = value
        self.time_between_frames = 1.0 / self.fps

    def cmd_red_slider_changed(self, value):
        self.max_red = value
        print "red slider changed to %d %%" % value

    def cmd_green_slider_changed(self, value):
        self.max_green = value
        print "green slider changed to %d %%" % value

    def cmd_blue_slider_changed(self, value):
        self.max_blue = value
        print "blue slider changed to %d %%" % value

    def cmd_gamma_slider_changed(self, value):
        self.max_gamma = value
        print "gamma slider changed to %d %%" % value

    def cmd_brightness_slider_changed(self, value):
        self.max_brightness = value
        print "brightness slider changed to %d %%" % value


    def cmd_equalize_changed(self, state):
        self.equalize = state
        print state

    def cmd_browse_file(self):
        self.ui.lineEdit_file_path.setText(QFileDialog.getOpenFileName())

    def send_udp_packet(self, payload):
        try:
            self.sock.writeDatagram(payload, QtNetwork.QHostAddress(IP), PORT)
        except Exception as e:
            print("Whuuuiii:", e)


    def on_recv_udp_packet(self):
        print "UDP packet received but ignored. TODO: implement handler."


def main():
    # app = QtGui.QApplication(sys.argv)
    #myapp = MyForm(device_id=3)
    #myapp.show()
    #sys.exit(app.exec_())
    #
    #Pipe = Pipeline(CVCamera(),
    #                 #ColorFilter(settings=(100, 100, 100, 100, 100)),
    #                 Matelight()
    #).activate()

    MidiPipe = Graphline(CAM=CVCamera(),
                         ML=Matelight(),
                         MI=MidiInput(5),
                         MR=MidiRouter({2: 'red',
                                        3: 'green',
                                        4: 'blue',
                                        14: 'brightness',
                                        15: 'gamma'}
                         ),
                         LC=loopingCounter(1,127),
                         CF=ColorFilter(),
                         CE=ConsoleEchoer(),
                         linkages={
                             ("MI", "outbox"): ("MR", "inbox"),
                             #("MR", "red"): ("CF", "red"),
                             ("LC", "outbox"): ("CF", "red"),
                             ("MR", "green"): ("CF", "green"),
                             ("MR", "blue"): ("CF", "blue"),
                             ("MR", "brightness"): ("CF", "brightness"),
                             ("MR", "gamma"): ("CF", "gamma"),
                             ("CAM", "outbox"): ("CF", "inbox"),
                             ("CF", "outbox"): ("ML", "inbox")
                         }
    ).activate()

    scheduler.run.runThreads()


if __name__ == "__main__":
    main()
