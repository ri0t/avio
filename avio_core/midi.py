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

import pygame
import pygame.midi

from circuits import Component

class MidiOutput(Component):
    def __init__(self, deviceid, latency=0, buffer_size=4096, *args):
        super(MidiOutput, self).__init__(*args)
        print("Initializing midi output")

        self.output = pygame.midi.Output(deviceid, latency, buffer_size)
        self.deviceid = deviceid
        self.lastcc = {}

    def started(self, *args):
        print("Starting midioutput on device " + str(self.deviceid))

    def midicc(self, event):
        print("Midi cc signal received: %i -> %i (%s) " % (event.cc, event.data, event.force))

        if not event.force and event.cc in self.lastcc:
            if abs(self.lastcc[event.cc] - event.data) > 20:
                print("Not sending, due to too contrasting change")
                return

        self.lastcc[event.cc] = event.data
        self.output.write_short(0xb0, event.cc, event.data)

    def resetcclock(self, event):
        print("Midi cc lock resetting")
        self.lastcc = {}
