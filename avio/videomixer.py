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

import numpy as np
import cv2 as cv

from circuits import Timer, Event

from isomer.component import ConfigurableComponent, handler, authorized_event
from isomer.events.client import broadcast, send
from isomer.logger import verbose, hilight

# from avio.gui import mouseevent
from isomer.matelight import transmit_ml


class mix_image(Event):
    pass


class unsubscribe(authorized_event):
    pass


class get_data(authorized_event):
    pass


class subscribe(authorized_event):
    pass


class update_channel(authorized_event):
    pass


class VideoMixer(ConfigurableComponent):
    configprops = {
        'channels': {
            'type': 'array',
            'default': [],
            'items': {
                'type': 'object',
                'properties': {
                    'no': {'type': 'integer'},
                    'alpha': {'type': 'number', 'default': 0.5},
                    'gamma': {'type': 'number', 'default': 0.5},

                }
            }
        },
        'fps': {'type': 'integer', 'default': 30}
    }

    channel = "AVIO"

    def __init__(self, delay=0.010, *args):

        super(VideoMixer, self).__init__("VIDEOMIXER", args)
        self.log("Initializing Videomixer")

        self.channels = {}
        self.images = {}

        self.clients = []

        self.timer = Timer(1.0 / self.config.fps, Event.create("mix"),
                           persist=True).register(self)

    @handler(subscribe, channel="isomer-web")
    def subscribe(self, event):
        self.log("Subscription Event:", event.client)
        if event.client.uuid not in self.clients:
            self.clients.append(event.client.uuid)

    @handler(unsubscribe, channel="isomer-web")
    def unsubscribe(self, event):
        self.log("Unsubscription Event:", event.client)
        if event.client.uuid in self.clients:
            self.clients.remove(event.client.uuid)

    @handler("userlogout", channel="isomer-web")
    def userlogout(self, event):
        self.stop_client(event)

    @handler("clientdisconnect", channel="isomer-web")
    def clientdisconnect(self, event):
        """Handler to deal with a possibly disconnected simulation frontend

        :param event: ClientDisconnect Event
        """

        self.stop_client(event)

    @handler(get_data, channel="isomer-web")
    def get_data(self, event):
        self.log("Providing mixer config:", event.client, pretty=True)
        response = {
            'component': 'avio.videomixer',
            'action': 'get_data',
            'data': self.config.serializablefields()
        }
        self.fireEvent(send(event.client.uuid, response), "isomer-web")

    @handler(update_channel, channel="isomer-web")
    def update_channel(self, event):
        self.log('Updating channel:', event.data)
        self.channels[event.data['no']] = event.data['settings']

    def stop_client(self, event):
        try:
            if event.clientuuid in self.clients:
                self.clients.remove(event.clientuuid)

                self.log("Remote simulator disconnected")
            else:
                self.log("Client not subscribed")
        except Exception as e:
            self.log("Strange thing while client disconnected", e, type(e))

    def _notify_clients(self, event):
        if len(self.clients) == 0:
            return

        message = {
            'component': 'avio.mixer',
            'action': 'update',
            'data': None
        }
        self.fireEvent(
            broadcast("clientgroup", message, group=self.clients),
            "isomer-web"
        )

    def mix_image(self, channel, frame):
        self.images[channel] = frame

    def mix(self):
        self.log('Mixing down', lvl=verbose)
        output = np.zeros((16, 40, 3), np.uint8)

        for channel in self.config.channels:
            try:
                frame = self.images[channel['no']]
                alpha = channel['alpha']
                gamma = channel['gamma']
                beta = 0.5

                output = cv.addWeighted(output, alpha, frame, beta, gamma)
            except KeyError:
                pass

        self.fireEvent(transmit_ml(output), 'matelight')
