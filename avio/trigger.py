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

import pygame

from circuits import Timer, Event
from isomer.component import ConfigurableComponent, handler
from isomer.logger import debug


class Trigger(ConfigurableComponent):
    """Listens for configurable joystick/gamepad button combos and triggers
    preconfigured events"""

    channel = "AVIO"

    configprops = {
        'triggers': {
            'type': 'array',
            'default': [{'button': 'X', 'event': 'tap'}],
            'items': {
                'type': 'object',
                'properties': {
                    'button': {
                        'type': 'string',
                        'maxLength': 1,
                        'minLength': 1,
                        'description':
                            'X = X key, O = O key, A = Triangle key, S = Square key'},
                    'event': {'type': 'string'}
                }
            }
        }
    }

    def __init__(self, *args):
        super(Trigger, self).__init__("TRIGGER", args)
        self.log("Initializing Trigger controller")

        self.triggers = {}
        self._build_combo_lookup()

    @handler("reload_configuration", channel="isomer-web")
    def reload_configuration(self, event):
        """Reload the current configuration and set up everything depending on it"""

        super(Trigger, self).reload_configuration(event)
        if event.target != self.uniquename:
            return

        self._build_combo_lookup()

    def _build_combo_lookup(self):
        self.log("Updating trigger lookup")
        self.triggers = {}
        for item in self.config.triggers:
            self.triggers[item['button']] = item['event']

    @handler("joystickchange")
    def joystickchange(self, event):
        if event.input.type != pygame.JOYBUTTONDOWN:
            return

        button = event.input.button
        key = ""

        if button == 0:
            key = "X"
        elif button == 1:
            key = "O"
        elif button == 2:
            key = "A"
        elif button == 3:
            key = "S"

        if key in self.triggers:
            self.log("Firing trigger:", key, lvl=debug)
            self.fireEvent(Event.create(self.triggers[key]))
