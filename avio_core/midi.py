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
from avio_core.logger import verbose


class MidiOutput(AVIOComponent):
    def __init__(self, deviceid, latency=0, buffer_size=4096, *args):
        super(MidiOutput, self).__init__(*args)
        self.log("Initializing midi output")

        self.total_ppn = 0
        self.ppn = 0

        self.output = pygame.midi.Output(deviceid, latency, buffer_size)
        self.output.set_instrument(0, 0)
        self.deviceid = deviceid
        self.lastcc = {}

        self.notes_playing = []

    def started(self, *args):
        self.log("Starting midi output on device " + str(self.deviceid))

    def midicc(self, event):

        #if not event.force and event.cc in self.lastcc:
        #    if abs(self.lastcc[event.cc] - event.data) > 20:
        #        #self.log("Not sending, due to too contrasting change")
        #        return

        if event.cc in self.lastcc and self.lastcc[event.cc] == event.data:
            return

        self.log("Midi cc signal received: %i -> %i (%s) " % (event.cc, event.data, event.force))

        self.lastcc[event.cc] = event.data
        self.output.write_short(0xb0, event.cc, event.data)

    def midinote(self, event):
        event.start = self.total_ppn
        self.notes_playing.append(event)
        self.log('Playing note:', event.note, 'on', event.midi_channel, lvl=verbose)
        #self.output.note_on(event.note, event.velocity, event.midi_channel)
        self.output.write_short(0x90, event.note, event.velocity)

    def midiinput(self, event):
        if event.code == 248:
            self.total_ppn += 1
            self.ppn += 1
            self.ppn %= 24
            removable = []
            for note in self.notes_playing:
                self.log('PPN:', note.start + note.length, self.total_ppn, note.start, note.length)
                if note.start + note.length <= self.total_ppn:
                    self.log('Note off again:', note.note, note.midi_channel)
                    self.output.write_short(0x80, note.note, note.velocity)
                    removable.append(note)

            for item in removable:
                self.notes_playing.remove(item)

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
        self.ppn = 0

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
                    self.log(mididata, pretty=True)

                self.fireEvent(midiinput(mididata))

