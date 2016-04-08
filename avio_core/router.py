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
import json
import os.path

from avio_core.component import AVIOComponent

from avio_core.events import midicc, resetcclock, loadscene

from pprint import pprint

routerevents = {'midicc': midicc,
                'loadscene': loadscene,
                'resetcclock': resetcclock
                }


class Router(AVIOComponent):
    def __init__(self, program='default', *args):
        super(Router, self).__init__(*args)
        print("Initializing router")

        self.scenes = {
            'default': {
                'axis': {
                    '0': {'event': 'midicc', 'args': 20},
                    '1': {'event': 'midicc', 'args': 21},
                    '2': {'event': 'midicc', 'args': 22},
                    '3': {'event': 'midicc', 'args': 23}
                },
                'buttons': {
                    '0': {'shiftcc': 4},
                    '1': {'mute': True},
                    '2': {'event': 'loadscene', 'args': 'second', 'mode': 'down'},
                    '3': {'nop': None},
                    '4': {'nop': None},
                    '5': {'nop': None},
                    '6': {'nop': None},
                    '7': {'nop': None},
                    '8': {'nop': None},
                    '9': {'nop': None},
                    '10': {'nop': None},
                    '11': {'nop': None}
                },
                'hat': {
                }
            },
            'second': {
                'buttons': {
                    '7': {'event': 'loadscene', 'args': 'default'},
                    '8': {'event': 'loadscene', 'args': 'third'}
                }
            },
            'third': {
                'buttons': {
                    '0': {'event': 'loadscene', 'args': 'default'}
                }

            }
        }
        self.routes = self.scenes['default']

        if program:
            self._loadprogram(program)

        try:
            self.routes = self.scenes['default']
        except KeyError:
            print("Router has no valid default program!")

        self.shiftcc = {}
        self.muted = False

    def started(self, *args):
        print("Starting router")

    def getshift(self):
        shift = 0
        for item in self.shiftcc.values():
            shift += item

        return shift

    def _saveprogram(self, programname):
        realname = os.path.abspath(os.path.expanduser("~/.avio/router_" + programname + ".json"))
        print("Router storing program " + programname + " to " + realname)
        try:
            with open(realname, "w") as fp:
                json.dump(self.scenes, fp, indent=4)
        #except IOError as e:

        except Exception as e:
            print("Program save failed for %s: %s (%s)" % (programname, e, type(e)))

    def _loadprogram(self, programname):
        backup = (self.scenes, self.routes)
        realname = os.path.abspath(os.path.expanduser("~/.avio/router_" + programname + ".json"))
        print("Router loading program " + programname + " from " + realname)
        try:
            with open(realname, 'r') as fp:
                self.scenes = json.load(fp)
            self.routes = self.scenes['default']
        except Exception as e:
            print("Program load failed for %s: %s (%s)" % (programname, e, type(e)))
            self.scenes, self.routes = backup

    def saveprogram(self, event):
        self._saveprogram(event.program)

    def loadprogram(self, event):
        self._loadprogram(event.program)

    def loadscene(self, event):
        print("Loading new scene: " + str(event.scene))
        self.routes = self.scenes[event.scene]

    def joystickchange(self, event):
        # print("Router change received: " + str(event.input))

        key = None
        identity = None

        if event.input.type == pygame.JOYAXISMOTION:
            key = 'axis'
            identity = event.input.axis
        elif event.input.type in (pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP):
            # print("Button action")
            key = 'buttons'
            identity = event.input.button

        # print(key, identity)
        if key != None and identity != None:
            cat = self.routes[key]
            if not str(identity) in cat:
                print("No routing rule for %s - %s" % (key, identity))
                return
            route = cat[str(identity)]

            evtype = event.input.type

            if 'mute' in route:
                print("Muted control")
                self.muted = evtype == pygame.JOYBUTTONDOWN

            if 'shiftcc' in route:
                print("Shifting CC")
                if evtype == pygame.JOYBUTTONDOWN:
                    self.shiftcc[identity] = route['shiftcc']
                else:
                    del (self.shiftcc[identity])

            if not self.muted and 'event' in route:
                signal = routerevents[route['event']](route['args'])
                if 'mode' in route:
                    if (route['mode'] == 'down' and evtype == pygame.JOYBUTTONUP) or (
                            route['mode'] == 'up' and evtype == pygame.JOYBUTTONDOWN):
                        print("Wrong mode for route: " + str(route))
                        return
                if type(signal) == midicc:
                    if len(self.shiftcc) > 0:
                        signal.cc += self.getshift()
                    signal.data = int(127 * abs((event.input.value + 1) / 2))

                self.fireEvent(signal)
