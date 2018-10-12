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
from avio_core.matelight import transmit_ml


def to_rgb1(im):
    # I think this will be slow
    w, h = im.shape
    ret = np.empty((w, h, 3), dtype=np.uint8)
    ret[:, :, 0] = im
    ret[:, :, 1] = im
    ret[:, :, 2] = im
    return ret


class Sequencer(AVIOComponent):
    def __init__(self, channel="matelight", *args):
        super(Sequencer, self).__init__(*args)
        self.log("Initializing Sequencer component")

        self.channel = channel

        self.size = (16, 40, 3)
        self.frame = np.zeros(self.size, np.uint8)
        self.last_frame = None

        self.mode = self.column = self.row = 0

        self.steps = np.zeros(self.size, np.uint8)

    def started(self, *args):
        self.log("Starting Sequencer. Output to:", self.channel)

    def _clear(self):
        self.log('Clearing')
        self.frame = np.zeros(self.size, np.uint8)
        self._transmit()

    def clear_ml(self, event):
        self._clear()

    def _transmit(self):
        self.log('Transmitting frame')
        self.last_frame = self.frame
        self.fireEvent(transmit_ml(self.frame), self.channel)

    @handler("keypress")
    def keypress(self, event):

        step = self.steps[self.row][self.column][self.mode]
        mod = event.ev.mod

        move = 1
        if mod == 1:
            move = 5

        if event.ev.key == pygame.K_RIGHT:
            self.column += move
        elif event.ev.key == pygame.K_LEFT:
            self.column -= move
        elif event.ev.key == pygame.K_DOWN:
            self.row += move
        elif event.ev.key == pygame.K_UP:
            self.row -= move
        elif event.ev.key == pygame.K_TAB:
            self.mode += 1
            self.mode = self.mode % 2
        elif event.ev.key == pygame.K_SPACE:
            self.steps[self.row][self.column][self.mode] = 255 if step == 0 else 0
        elif event.ev.key == pygame.K_PLUS:
            value = step + 5 * ((1 + mod) * 5)
            self.steps[self.row][self.column][self.mode] = min(value, 255)
        elif event.ev.key == pygame.K_MINUS:
            value = step - 5 * ((1 + mod) * 5)
            self.steps[self.row][self.column][self.mode] = max(value, 0)
        elif event.ev.key == pygame.K_PRINT:
            for i in range(self.size[1]):
                line = ""
                for j in range(self.size[0]):
                    data = self.steps[j][i][self.mode]
                    line += "%s" % ("#" if data else "-")
                print(line)

        self.row = self.row % self.size[0]
        self.column = self.column % self.size[1]

        matrix = self.steps[:, :, self.mode]
        self.frame = to_rgb1(matrix)
        self.log(self.frame.shape)

        self.frame[self.row][self.column] = [64, 196, 255]
        self._transmit()
