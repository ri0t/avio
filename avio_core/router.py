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

from circuits import Component

from .events import midicc


class Router(Component):
    def __init__(self, *args):
        super(Router, self).__init__(*args)
        print("Initializing router")

        self.routes = {}

        self.routes = {
            'axis': {
                0: 20,
                1: 21,
                2: 22,
                3: 23
            },
            'buttons': {
                0: 4,
                1: 5,
                2: 6,
                3: 7,
                4: 8,
                5: 9,
                6: 10,
                7: 11,
                8: 12,
                9: 13,
                10: 14,
                11: 15
            },
            'hat': {
            }
        }

    def started(self, *args):
        print("Starting router")

    def joystickchange(self, event):
        print("Router change received: " + str(event.input))

        cc = 0
        value = 0

        if event.input.type == pygame.JOYAXISMOTION:
            cc = self.routes['axis'][event.input.axis]
            value = int(127 * abs((event.input.value + 1) / 2))

            self.fireEvent(midicc(cc, value))
