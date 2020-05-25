#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# AVIO - The Python Audio Video Input Output Suite
# ================================================
# Copyright (C) 2015-2020 riot <riot@c-base.org>
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

from datetime import datetime

from circuits import Event
from isomer.component import ConfigurableComponent


class bpm_tap(Event):
    pass


class BPM(ConfigurableComponent):
    """Listens for configurable joystick/gamepad button combos and triggers
    preconfigured events"""

    channel = "AVIO"

    configprops = {
    }

    def __init__(self, *args):
        super(BPM, self).__init__("BPM", args)
        self.log("Initializing BPM controller")

        self.timer = None

        self.offset = 0
        self.bpm = 0
        # Historic reference over taps
        self.taps = []
        # Minimum tap count
        self.tapcount = 2
        # Factor oldtaptimeout gets multiplied with, when we're still accurate
        self.approximationprecision = 2
        self.oldtaptimeout = 5

    def tap(self, event):
        self.log("TAP")

        bpm = 0

        self.taps.append(datetime.now())

        # first: Weed out old data and analyze precision of last taps
        latest = self.taps[-1]
        if len(self.taps) > 1:  # we have enough keys for a better approximation
            secondlatest = self.taps[-2]

            delta = latest - secondlatest
            deltamicroseconds = delta.seconds * 1000000 + delta.microseconds

            proposedbpm = 60000000.0 / deltamicroseconds

            if (proposedbpm - (proposedbpm * 0.1) < bpm) and \
                    (proposedbpm + (proposedbpm * 0.1) > bpm):
                # we're in range (+- 10%)
                self.oldtaptimeout *= self.approximationprecision

        # second: weed out those old keytaps. They sure do not form the beat anymore.
        while ((latest - self.taps[0]).seconds > self.oldtaptimeout) and len(
                self.taps) > 0:
            del self.taps[0]

        # if we still have enough of them keytaps: go on, get some bpm
        if len(self.taps) > self.tapcount:

            # third: calculate average time-delta
            count = 0
            oldtap = self.taps[0]
            deltasum = 0
            for tap in self.taps[1:]:
                delta = tap - oldtap
                deltamicrosecs = delta.seconds * 1000000 + delta.microseconds
                deltasum += deltamicrosecs
                oldtap = tap
                count += 1

            avgdelta = deltasum / count

            # third: calculate the current bpm and set a reasonable oldtaptimeout
            bpm = 60000000.0 / avgdelta

            oldtaptimeout = pow((60 / bpm) + 1, 2)

            self.log("BPM:", bpm, len(self.taps))
        else:
            self.log("TAP SOME MORE!")
