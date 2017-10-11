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

from circuits import Event, Timer

from avio_core.component import AVIOComponent
from avio_core.events import midiinput


class MidiOutput(AVIOComponent):
    def __init__(self, deviceid, latency=0, buffer_size=4096, *args):
        super(MidiOutput, self).__init__(*args)
        self.log("Initializing midi output")

        self.output = pygame.midi.Output(deviceid, latency, buffer_size)
        self.deviceid = deviceid
        self.lastcc = {}

    def started(self, *args):
        self.log("Starting midi output on device " + str(self.deviceid))

    def midicc(self, event):
        self.log("Midi cc signal received: %i -> %i (%s) " % (event.cc, event.data, event.force))

        if not event.force and event.cc in self.lastcc:
            if abs(self.lastcc[event.cc] - event.data) > 20:
                self.log("Not sending, due to too contrasting change")
                return

        self.lastcc[event.cc] = event.data
        self.output.write_short(0xb0, event.cc, event.data)

    def resetcclock(self, event):
        self.log("Midi cc lock resetting")
        self.lastcc = {}


class MidiInput(AVIOComponent):
    def __init__(self, deviceid, latency=0, delay=0.01, *args):
        super(MidiInput, self).__init__(*args)
        self.log("Initializing midi input")

        self.input = pygame.midi.Input(deviceid, latency)
        self.deviceid = deviceid
        self.lastcc = {}
        self.delay = delay


    def started(self, *args):
        """
        """
        self.log("Starting midi input on device " + str(self.deviceid) + " at %i Hz" % int(1 / self.delay))
        Timer(self.delay, Event.create('peek'), self.channel, persist=True).register(self)

    def peek(self, event):
        if self.input.poll():
            while self.input.poll():

                mididata = self.input.read(1)
                if len(mididata) > 1:
                    mididata = mididata[-1]
                else:
                    mididata = mididata[0]

                if self.debug:
                    self.log(mididata)

                self.fireEvent(midiinput(mididata))

