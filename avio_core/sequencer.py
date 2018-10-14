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
from avio_core.logger import verbose
from avio_core.events import midinote


def to_rgb1(im):
    """Convert grayscale image to RGB"""
    w, h = im.shape
    ret = np.empty((w, h, 3), dtype=np.uint8)
    ret[:, :, 0] = im
    ret[:, :, 1] = im
    ret[:, :, 2] = im
    return ret


class Sequencer(AVIOComponent):
    def __init__(self, channel="matelight", *args):
        """Step sequencer"""

        super(Sequencer, self).__init__(*args)
        self.log("Initializing Sequencer component")

        self.channel = channel
        self.midi_channel = 0

        self.size = (16, 40, 3)
        self.matrix = self.frame = np.zeros(self.size, np.uint8)

        self.last_frame = None

        self.step = 0
        self.playing_row = 0
        self.ppn = 0

        self.mode = self.column = self.row = 0

        self.steps = np.zeros(self.size, np.uint8)

        self.default_note = 64

        self.last_note = None

        self.routing = {
            0: 'note',
            1: 'velocity',
            2: 'channel'
        }

    def started(self, *args):
        self.log("Starting Sequencer. Output to:", self.channel)

    def _transmit(self):
        self.log('Transmitting frame', lvl=verbose)
        self.last_frame = self.frame
        self.fireEvent(transmit_ml(self.frame), self.channel)
        self.frame = np.zeros(self.size, np.uint8)

    def _send_step(self):
        step = self.steps[self.playing_row][self.step]
        if step[0] > 0:
            self.fireEvent(midinote(step[0], step[1], self.midi_channel, step[2]))

    @handler("midiinput")
    def midi_input(self, event):
        """Handles incoming midi data like clock"""

        if event.code == 248:
            self.ppn = self.ppn + 1
            self.ppn %= 24
            if self.debug:
                print("#" if self.ppn == 0 else ".", end="", flush=True)
            if self.ppn == 0:
                self.step = (self.step + 1) % self.size[1]
                self._send_step()
                self._render()

    def _render(self):
        self.frame = to_rgb1(self.steps[:, :, self.mode])
        self.frame[self.row][self.column] = [64, 196, 255]
        self.frame[self.playing_row][self.step] = [196, 64, 64]
        self._transmit()

    @handler("keypress")
    def keypress(self, event):

        step = self.steps[self.row][self.column][self.mode]
        mod = event.ev.mod

        move = 1

        matrix_changed = False
        old_row = self.row
        old_col = self.column

        alt = mod & pygame.KMOD_LALT
        lshift = mod & pygame.KMOD_LSHIFT
        ctrl = mod & pygame.KMOD_LCTRL

        # self.log('MODS:', alt, lshift, ctrl)

        if alt:
            move = 4
        if ctrl:
            move = move * 2

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
            self.mode = self.mode % 3
            matrix_changed = True
        elif event.ev.key == pygame.K_SPACE:
            if self.mode == 0:
                value = self.default_note
            elif self.mode == 1:
                value = 127
            elif self.mode == 2:
                value = 16

            self.steps[self.row][self.column][self.mode] = value
            matrix_changed = True
        elif event.ev.key == pygame.K_PLUS and mod == 0:
            value = step + 5 * ((1 + mod) * 5)
            self.steps[self.row][self.column][self.mode] = min(value, 127)
            matrix_changed = True
        elif event.ev.key == pygame.K_MINUS and mod == 0:
            value = step - 5 * ((1 + mod) * 5)
            self.steps[self.row][self.column][self.mode] = max(value, 0)
            matrix_changed = True
        elif event.ev.key == pygame.K_PRINT:
            for i in range(self.size[1]):
                line = ""
                for j in range(self.size[0]):
                    data = self.steps[j][i][self.mode]
                    line += "%s" % ("#" if data else "-")
                print(line)

        self.row = self.row % self.size[0]
        self.column = self.column % self.size[1]


        if matrix_changed or (self.row != old_row or self.column != old_col):
            self._render()
