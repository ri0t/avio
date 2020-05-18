import pygame
import cv2
import numpy

from circuits import Timer, Event, handler, Worker, task

from avio_core.component import AVIOComponent
from avio_core.gui import GUIComponent, paintrequest


# Camera events

class cameraframe(Event):
    def __init__(self, frame, *args):
        super(cameraframe, self).__init__(*args)
        self.frame = frame

def take_picture(cam):
    err, frame = cam.read()

    return frame


class CVCamera(AVIOComponent):
    def __init__(self, device_id=0, targetresolution=(40, 16), *args,
                 **kwargs):
        super(CVCamera, self).__init__(*args, **kwargs)
        self.targetresolution = targetresolution
        self.cam = cv2.VideoCapture(device_id)
        self.cam.set(3, 320)
        self.cam.set(4, 240)

        self.framerate = 20 / 1000.0

        self.recording = True

        self.worker = Worker(process=False, workers=1,
                             channel="camera").register(self)

        self.cam_timer = Timer(2, Event.create('takepicture')).register(
            self)

        self.surface = pygame.Surface(targetresolution)
        self.log('Camera started')

    def takepicture(self):
        if self.recording:
            self.log('Taking a pic')
            self.fireEvent(task(take_picture, self.cam), 'camera')


    @handler('task_success', channel='camera')
    def task_success(self, event, call, result):
        frame = result

        if frame is None:
            self.log("Oh, no camera attached! Change this and rerun!")
            self.cam_timer.unregister()

            return

        newframe = numpy.rot90(frame)
        #newframe = cv2.resize(frame, self.targetresolution)
        surfarr = pygame.surfarray.make_surface(newframe)
        srf = pygame.transform.scale(surfarr, self.targetresolution)

        self.fireEvent(cameraframe(srf))
        self.fireEvent(Event.create('takepicture'))


class CameraDisplay(GUIComponent):
    def cameraframe(self, event):
        #self.log('New camera frame received:', event)
        self.fireEvent(paintrequest(event.frame, self.x, self.y), 'gui')
