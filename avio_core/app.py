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
from .events import guiresize

from pprint import pprint


class App(Component):
    def __init__(self, *args):
        super(App, self).__init__(args)
        print("Initializing core")

        self.screen_width = 640
        self.screen_height = 480

    def started(self, *args):
        print("Starting up core")

        pygame.display.set_caption('AVIO Core')
        self.mainfont = pygame.font.Font('/home/riot/src/avio/fonts/editundo.ttf', 48)
        self.caption = self.mainfont.render('AVIO Core', True, (238, 126, 17))
        self.fireEvent(guiresize(self.screen_width, self.screen_height))

    def guiresize(self, event):
        self.screen_width, self.screen_height = event.width, event.height
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        self.screen.fill((31, 31, 31))
        pygame.draw.rect(self.screen, (31, 31, 31), (0, 0, self.screen_width, self.screen_height))

        self.screen.blit(self.caption, (
            (self.screen_width / 2) - self.caption.get_width() / 2,
            (self.screen_height / 2) - self.caption.get_height() / 2))
        pygame.display.flip()

    def quit(self, *args):
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

    app.run()
