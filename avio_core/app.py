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
import argparse

import pygame

from circuits import Component

from .controller import Controller, getJoystick
from .midi import MidiOutput
from .router import Router
from .gui import GUI, Button, ButtonGrid, Label

from pprint import pprint

from .events import guiquit

class App(Component):
    def __init__(self, *args):
        super(App, self).__init__(args)
        print("Initializing core")

    def started(self, *args):
        print("Starting core")

    def guiquit(self, *args):
        print("Quitting by request: " + str(args))
        sys.exit()


def print_io():
    midicount = pygame.midi.get_count()
    joystickcount = pygame.joystick.get_count()

    mididevices = {}
    joystickdevices = {}

    for i in range(midicount):
        mididevice = pygame.midi.get_device_info(i)
        mididevices[i] = mididevice

    for i in range(joystickcount):
        joystickdevice = getJoystick(i)
        joystickdevices[i] = joystickdevice

    print("MIDI Devices:")
    pprint(mididevices)
    print("Joystick-like Devices:")
    pprint(joystickdevices)


def Launch():
    parser = argparse.ArgumentParser()
    parser.add_argument("--io", help="Show io options", action="store_true")
    parser.add_argument("--gui", help="Activate GUI (EXPERIMENTAL!)", action="store_true")
    parser.add_argument("--mididev", help="Select MIDI device id", type=int,
                        default=0)

    args = parser.parse_args()

    if args.io:
        print_io()
        sys.exit()

    pygame.init()
    pygame.midi.init()
    pygame.joystick.init()

    app = App()
    input = Controller().register(app)
    router = Router().register(app)
    midiout = MidiOutput(deviceid=args.mididev).register(app)

    gui = GUI().register(app)

    if args.gui:
        # This is only a test setup.
        hellobutton = Button('btnHello', 'Hello World!', (10, 10, 150, 20), True).register(gui)
        quitbutton = Button('btnQuit', 'Quit', (10, 32, 150, 42), False, False).register(gui)
        grid = ButtonGrid('beatGrid', 20, 100, 16, 1).register(gui)
        grid2 = ButtonGrid('synthGrid', 280, 100, 16, 1).register(gui)
    else:
        os.environ['SDL_VIDEODRIVER'] = 'dummy'  # Does not work. :(

        # Warn the user about the necessity of the GUI
        label = Label('nogui', 'GUI inactive - do not close while operating.', (0, 0, 260, 15)).register(gui)
        label2 = Label('nogui2', 'Check the README on how to deactivate the GUI completely.', (0, 15, 348, 30)).register(gui)
    app.run()
