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
import cv2 as cv
import socket
import os
import numpy as np

from circuits import Event, Timer, handler

from avio_core.component import AVIOComponent


class clear_ml(Event):
    """Send a black frame"""
    pass


class fade_out_ml(Event):
    pass

class refresh_ml(Event):
    pass


class transmit_ml(Event):
    def __init__(self, frame, *args, **kwargs):
        super(transmit_ml, self).__init__(*args, **kwargs)
        self.frame = frame


class Matelight(AVIOComponent):
    channel = "matelight"

    def __init__(self, host="matelight", port=1337, *args):
        super(Matelight, self).__init__(*args)
        self.log("Initializing matelight output")

        self.host = host
        self.port = port

        self.size = (40, 16)

        self.fading = None

        self.last_frame = np.zeros(self.size, np.uint8)

        path = os.path.abspath("./images/startscreen_matelight.png")
        boot_image = cv.imread(path)

        self.boot_image = cv.cvtColor(boot_image, cv.COLOR_BGR2RGB)
        self._transmit(self.boot_image)

        self.fade_timer = None
        self.init_timer = Timer(5, fade_out_ml()).register(self)
        self.refresh_timer = Timer(1, refresh_ml(), persist=True).register(self)

    def started(self, *args):
        self.log("Starting matelight output on device %s:%i" % (self.host, self.port))

    def fade_out_ml(self, event):
        if self.fading is None:
            self.fading = 20
            self.fade_timer = Timer(1 / 60.0, fade_out_ml(), persist=True).register(self)
        elif self.fading > 0:
            new_frame = (self.last_frame * 0.9).astype(np.uint8)
            self._transmit(new_frame)
            self.fading -= 1
        elif self.fading <= 0:
            self._clear()
            self.fade_timer.unregister()
            self.fading = None

    def _clear(self):
        self.log('Clearing')
        img = np.zeros((40, 16, 3), np.uint8)
        self._transmit(img)

    def clear_ml(self, event):
        self._clear()

    @handler('refresh_ml')
    def refresh_ml(self, event):
        self._transmit(self.last_frame)

    def _transmit(self, image):
        self.log('Transmitting image, shape:', image.shape)
        ml_data = bytearray(image) + b"\00\00\00\00"
        self.last_frame = image
        # data_c = bytearray([x for x in list(ml_data)])
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(ml_data, (self.host, self.port))
        except Exception as e:
            self.log("Meeeh: ", e)

    def transmit_ml(self, event):
        self._transmit(event.frame)

    @handler('keypress')
    def keypress(self, event):
        if event.ev.key == 223 and event.ev.mod == 1:
            self._transmit(self.boot_image)
            Timer(2, fade_out_ml()).register(self)
