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

import os
import time

from circuits import Timer
from isomer.component import ConfigurableComponent, handler, \
    authorized_event
from isomer.events.system import isomer_event
from isomer.events.client import broadcast
from isomer.logger import verbose, warn, debug

from .videomixer import mix_image

class unsubscribe(authorized_event):
    pass


class subscribe(authorized_event):
    pass


class play(authorized_event):
    pass


class stop(authorized_event):
    pass


class cli_test_text(isomer_event):
    pass


class render(isomer_event):
    """Render another frame"""
    pass


class TextRender(ConfigurableComponent):
    """Text Renderer"""

    channel = "AVIO"

    configprops = {
        'channel': {'type': 'integer'},
        'playing': {'type': 'boolean', 'default': False},
        'movement': {
            'type': 'object',
            'properties': {
                'speed': {'type': 'number', 'default': 1.0},
                'direction': {'type': 'number', 'default': 90}
            },
        },
        'loop': {'type': 'boolean', 'default': True},
        'bounce': {'type': 'boolean', 'default': False},
        'font': {'type': 'string', 'default': ''}
    }

    def __init__(self):
        super(TextRender, self).__init__("GIFMASTER")

        self.timer = None

    @handler(subscribe, channel="isomer-web")
    def subscribe(self, event):
        self.log("Subscription Event:", event.client)
        if event.client.uuid not in self.players[event.data].clients:
            self.players[event.data].clients.append(event.client.uuid)

    @handler(unsubscribe, channel="isomer-web")
    def unsubscribe(self, event):
        self.log("Unsubscription Event:", event.client)
        if event.client.uuid in self.players[event.data].clients:
            self.players[event.data].clients.remove(event.client.uuid)

    @handler("userlogout", channel="isomer-web")
    def userlogout(self, event):
        self.stop_client(event)

    @handler("clientdisconnect", channel="isomer-web")
    def clientdisconnect(self, event):
        """Handler to deal with a possibly disconnected simulation frontend

        :param event: ClientDisconnect Event
        """

        self.stop_client(event)

    def stop_client(self, event):
        try:
            for player in self.players:
                if event.clientuuid in player.clients:
                    player.clients.remove(event.clientuuid)

                    self.log("Remote simulator disconnected")
                else:
                    self.log("Client not subscribed")
        except Exception as e:
            self.log("Strange thing while client disconnected", e, type(e))

    def cli_test_text(self, *args):
        if 'stop' in args:
            self.log("Stopping test video")
            self.stop()
        else:
            self.log('Running test video')
            self.config['filename'] = os.path.abspath(
                os.path.join(__file__, "../../test.gif"))
            self.get_frames()
            self.timer = Timer(self.config['delay'] / 1000.0, render(),
                               persist=True).register(self)

    def update(self):
        self.log('Updating', self.playing, self.config['playing'])
        if self.config['playing'] is True:
            if self.playing is False:
                self.log('Beginning playback')
                self.play()
        else:
            if self.playing is True:
                self.log('Beginning playback')
                self.stop()

    def started(self, event, thing):
        self.log('Converting image')

    def task_success(self, event, call, result):
        self.log("Worker finished:", event.channels[0], pretty=True, lvl=verbose)
        if event.channels[0] != "gifimport_" + self.uniquename:
            self.log("Not for us.", lvl=verbose)
            return
        if len(result) == 3:
            frames, durations, log = result
        else:
            self.log("Unexpected result:", result, pretty=True)
            return

        if len(frames) > 0:
            self.frames = frames
            self.durations = durations

            self.cur = 0

            self.breakpoint = len(self.frames) - 1
            self.startpoint = 0
            self.reversed = False
        else:
            self.log("No frames extracted:", log, lvl=warn)

    def render(self):
        # pos = self.x, self.y
        # self.log('Rendering %s' % self.config['filename'], lvl=verbose)

        if self.playing:
            self.delta += time.time() - self.ptime
            if self.delta > self.frames[self.cur][1]:

                while self.delta > self.frames[self.cur][1]:

                    self.delta -= self.frames[self.cur][1]
                    if self.reversed:
                        self.cur -= 1
                        if self.cur < self.startpoint:
                            self.cur = self.breakpoint
                    else:
                        self.cur += 1
                        if self.cur > self.breakpoint:
                            self.cur = self.startpoint

                    if self.frames[self.cur][1] == 0:
                        break

            self.ptime = time.time()

        try:
            frame = self.frames[self.cur][0]
            # self.log('Firing event', frame)
            if len(self.clients) > 0:
                self._broadcast(frame)
            self.fireEvent(mix_image(self.config['channel'], frame), "AVIO")
        except IndexError:
            pass

    def _broadcast(self, frame):
        message = {
            'component': 'avio.gifplayer',
            'action': 'frame_update',
            'data': {
                'channel': self.config['channel'],
                'frame': frame.tolist()
            }
        }
        self.fireEvent(
            broadcast("clientgroup", message, group=self.clients),
            "isomer-web"
        )

    def set_speed(self, factor):
        self.log('Setting new speed: %f' % factor)
        for i, duration in enumerate(self.durations):
            self.frames[i][1] = duration * factor

    def seek(self, num):
        self.cur = num
        if self.cur < 0:
            self.cur = 0
        if self.cur >= len(self.frames):
            self.cur = len(self.frames) - 1

    def set_bounds(self, start, end):
        if start < 0:
            start = 0
        if start >= len(self.frames):
            start = len(self.frames) - 1
        if end < 0:
            end = 0
        if end >= len(self.frames):
            end = len(self.frames) - 1
        if end < start:
            end = start
        self.startpoint = start
        self.breakpoint = end

    def stop(self):
        self.log('Stop!', lvl=debug)
        self.playing = False
        if self.timer is not None:
            self.timer.stop()
            self.timer.unregister()
            self.timer = None

    def play(self):
        self.log('Play!', lvl=debug)
        self.playing = True
        if self.timer is None:
            self.ptime = time.time()
            self.timer = Timer(self.config['delay'] / 1000.0, render(),
                               persist=True).register(self)

    def rewind(self):
        self.seek(0)

    def fastforward(self):
        self.seek(self.length() - 1)

    def get_height(self):
        return self.image.size[1]

    def get_width(self):
        return self.image.size[0]

    def get_size(self):
        return self.image.size

    def length(self):
        return len(self.frames)

    def reverse(self):
        self.reversed = not self.reversed

    def reset(self):
        self.cur = 0
        self.ptime = time.time()
        self.reversed = False
