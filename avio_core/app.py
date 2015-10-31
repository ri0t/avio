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

import sys
import argparse

import pygame

from circuits import Component

from .controller import Controller, getJoystick
from .midi import MidiOutput
from .router import Router
from .gui import GUI, Button, ButtonGrid

from pprint import pprint

from .events import guiquit

class App(Component):
    def __init__(self, *args):
        super(App, self).__init__(args)
        print("Initializing core")

    def started(self, *args):
        print("Starting up core")

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
    print("Joystick Devices:")
    pprint(joystickdevices)


def Launch():
    pygame.init()
    pygame.midi.init()
    pygame.joystick.init()

    parser = argparse.ArgumentParser()
    parser.add_argument("--io", help="show io options", action="store_true")
    parser.add_argument("--mididev", help="Select MIDI device id", type=int,
                        default=pygame.midi.get_default_output_id())

    args = parser.parse_args()

    if args.io:
        print_io()
        sys.exit()

    app = App()
    input = Controller().register(app)
    router = Router().register(app)
    midiout = MidiOutput(deviceid=args.mididev).register(app)
    gui = GUI().register(app)
    hellobutton = Button('btnHello', 'Hello World!', (10, 10, 150, 20), True).register(gui)
    quitbutton = Button('btnQuit', 'Quit', (10, 32, 150, 42), False, False).register(gui)
    grid = ButtonGrid('beatGrid', 20, 100, 16, 1).register(gui)


    app.run()
