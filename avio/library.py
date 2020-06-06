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

import os
from base64 import b64encode

import pygame
from PIL import Image
from isomer.component import ConfigurableComponent, handler, authorized_event
from isomer.events.client import send
from isomer.logger import verbose


class unsubscribe(authorized_event):
    pass


class subscribe(authorized_event):
    pass


class Library(ConfigurableComponent):
    """"""

    channel = "AVIO"

    configprops = {
        'cache_directory': {'type': 'string', 'default': '../../cache'}
    }

    def __init__(self, *args):
        super(Library, self).__init__("LIBRARY", args)
        self.log("Initializing Simple Library")

        pygame.font.init()

        self.clients = []

        self.storage_path = os.path.abspath(os.path.join(__file__, "../../library"))

        self.files = {
            'gif': {},
            'ttf': {},
        }

        for location in self.files:
            os.makedirs(
                os.path.abspath(
                    os.path.join(__file__, self.config.cache_directory, location)
                ),
                exist_ok=True
            )

        for root, dirs, files in os.walk(self.storage_path):
            for file in files:
                extension = str(os.path.splitext(file)[1]).lstrip('.')
                self.log(extension, os.path.splitext(file), lvl=verbose)
                self.log(root, file, lvl=verbose)
                self.files[extension][os.path.join(root, file)] = {'image': ''}

        for filename, item in self.files['gif'].items():
            self.log("Scanning:", filename)

            with open(filename, "rb") as f:
                image = b64encode(f.read())
                base64 = image.decode('utf-8')

            item['image'] = base64
            item['name'] = os.path.basename(filename)

        for filename, item in self.files['ttf'].items():
            self.log("Scanning:", filename)
            preview_file = os.path.abspath(
                os.path.join(
                    __file__, self.config.cache_directory, 'ttf',
                    os.path.basename(filename) + ".jpg"
                )
            )

            try:
                with open(preview_file, "rb") as f:
                    preview = b64encode(f.read())

            except FileNotFoundError:
                font = pygame.font.Font(filename, 12)
                rendered = font.render("AaBbCc", True, (255, 255, 255))
                surface = pygame.Surface((40, 16))
                surface.blit(rendered, (2, 2))
                data = pygame.image.tostring(surface, 'RGB')
                img = Image.frombytes('RGB', (40, 16), data)

                with open(preview_file, "wb") as f:
                    img.save(f, 'JPEG')

                preview = b64encode(img.tobytes())

            base64 = preview.decode('utf-8')
            item['image'] = base64
            item['name'] = os.path.basename(filename)

    @handler(subscribe, channel="isomer-web")
    def subscribe(self, event):
        self.log("Subscription Event:", event.client)
        if event.client.uuid not in self.clients:
            self.clients.append(event.client.uuid)
            packet = {
                'component': 'avio.library',
                'action': 'library',
                'data': self.files
            }
            self.fireEvent(send(event.client.uuid, packet), "isomer-web")

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

    def stop_client(self, event):
        try:
            if event.clientuuid in self.clients:
                self.clients.remove(event.clientuuid)

                self.log("Remote simulator disconnected")
            else:
                self.log("Client not subscribed")
        except Exception as e:
            self.log("Strange thing while client disconnected", e, type(e))
