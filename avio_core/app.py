# AVIO - The Python Audio Video Input Output Suite
# ================================================
# Copyright (C) 2015 riot <riot@c-base.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


__author__ = 'riot'

import os
import sys

import pygame

from circuits import Timer
from avio_core.component import AVIOComponent


from avio_core.controller import Controller, getJoystick

from avio_core.camera import CVCamera, CameraDisplay
from avio_core.gif import GIFImage
from avio_core.midi import MidiOutput, MidiInput
from avio_core.router import Router
from avio_core.gui import GUI, Button, ButtonGrid, Label, Meter, setvalue

from pprint import pprint

from avio_core.events import guiquit, saveprogram


class App(AVIOComponent):
    def __init__(self, sysargs, *args):
        super(App, self).__init__(args)
        self.log("Initializing core")
        self.sysargs = sysargs
        if sysargs.debug:
            AVIOComponent.debug = True

    def started(self, *args):
        self.log("Starting core")

        # Timer(0.5, setvalue('testmeter', 76), persist=True).register(self)

        configpath = os.path.abspath(os.path.expanduser("~/.avio"))
        if not os.path.exists(configpath):
            self.log("Creating configuration folder " + configpath)
            os.mkdir(configpath)
        if not os.path.exists(os.path.join(configpath, "router_default.json")):
            self.fireEvent(saveprogram('default'))

    def guiquit(self, *args):
        self.log("Quitting by request: " + str(args))
        sys.exit()

    def keypress(self, event):
        if event.ev.key == pygame.K_v:
            GIFImage('testgif5', 'test5.gif', immediately=True).register(self)


def get_io():
    midicount = pygame.midi.get_count()
    joystickcount = pygame.joystick.get_count()

    mididevices = {}
    joystickdevices = {}

    for i in range(midicount):
        mididevice = pygame.midi.get_device_info(i)
        info = {
            'type': mididevice[0],
            'name': mididevice[1],
        }
        if mididevice[2] == 1:
            info['dir'] = 'input'
        else:
            info['dir'] = 'output'
        mididevices[i] = info

    for i in range(joystickcount):
        joystickdevice = getJoystick(i)
        joystickdevices[i] = joystickdevice

    return mididevices, joystickdevices


def Launch(args):
    pygame.init()
    pygame.midi.init()
    pygame.joystick.init()

    mididevices, joystickdevices = get_io()

    if args.io:
        print("MIDI Devices:")
        pprint(mididevices)
        print("Joystick-like Devices:")
        pprint(joystickdevices)
        sys.exit()

    default_midiin = default_midiout = -1

    for key, item in mididevices.items():
        if item['name'] == b'Midi Through Port-0':
            if item['dir'] == 'output':
                default_midiout = key
                continue
            if item['dir'] == 'input':
                default_midiin = key
                continue
        else:
            continue

    if args.midiin is None:
        print('Using default midi input: %i' % default_midiin)
        args.midiin = default_midiin
    if args.midiout is None:
        print('Using default midi output: %i' % default_midiout)
        args.midiout = default_midiout

    app = App(args)

    if args.debug:
        from circuits import Debugger
        dbg = Debugger().register(app)
        dbg.IgnoreEvents.extend(["peek", "repaint", "paintrequest",
                                 "task_success",
                                 "read", "_read",
                                 "write", "_write",
                                 "stream_success", "stream_complete",
                                 "stream"])

    input = Controller().register(app)
    router = Router(program=args.program).register(app)
    midiout = MidiOutput(deviceid=args.midiout).register(app)
    midiin = MidiInput(deviceid=args.midiin).register(app)
    if args.cam:
        camera = CVCamera(targetresolution=(1920, 1200)).register(app)
        camdisp = CameraDisplay().register(app)

    gui = GUI().register(app)

    if args.gui:
        # This is only a test setup.
        #hellobutton = Button('btnHello', 'Hello World!', (10, 10, 150, 20),
        #                     True).register(gui)
        #quitbutton = Button('btnQuit', 'Quit', (10, 32, 150, 42), False,
        #                    False).register(gui)
        #grid = ButtonGrid('beatGrid', 25, 100, 2, 2).register(gui)
        # qqqgrid2 = ButtonGrid('synthGrid', 285, 100, 3, 3).register(gui)
        #meter = Meter('testmeter', 'dB', 5, 100, max=100).register(gui)
        gif = GIFImage('testgif1', 'test.gif').register(gui)
        #gif2 = GIFImage('testgif2', 'test2.gif').register(gui)
        #gif3 = GIFImage('testgif3', 'test3.gif').register(gui)
        #gif4 = GIFImage('testgif4', 'test4.gif').register(gui)
        #gif5 = GIFImage('testgif5', 'test5.gif').register(gui)

    app.run()
