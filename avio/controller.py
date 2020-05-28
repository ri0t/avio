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

from circuits import Timer, Event

from isomer.component import ConfigurableComponent, handler, authorized_event
from isomer.events.client import broadcast
from avio.events import joystickchange, guiquit, guiresize, keypress

# from avio.gui import mouseevent


class unsubscribe(authorized_event):
    pass


class subscribe(authorized_event):
    pass


def getJoystick(no):
    joystick = pygame.joystick.Joystick(no)
    joystick.init()

    # Get the name from the OS for the controller/joystick
    name = joystick.get_name()
    axes = {}
    buttons = {}
    hats = {}

    # Usually axis run in pairs, up/down for one, and left/right for
    # the other.
    axesCount = joystick.get_numaxes()

    for i in range(axesCount):
        axis = joystick.get_axis(i)
        axes[i] = axis

    buttonsCount = joystick.get_numbuttons()

    for i in range(buttonsCount):
        button = joystick.get_button(i)
        buttons[i] = button

    # Hat switch. All or nothing for direction, not like joysticks.
    # Value comes back in an array.
    hatsCount = joystick.get_numhats()

    for i in range(hatsCount):
        hat = joystick.get_hat(i)
        hats[i] = hat

    return {'name': name, 'axes': axes, 'buttons': buttons, 'hats': hats}


class HIDController(ConfigurableComponent):

    configprops = {
        'dead_center': {'type': 'number', 'default': 0.1},
    }

    channel = "AVIO"

    def __init__(self, delay=0.010, *args):

        super(HIDController, self).__init__("HIDCONTROLLER", args)
        self.log("Initializing HID controller")

        self.delay = delay
        self.acting = True

        self.clients = []

        pygame.init()
        pygame.joystick.init()

        self.joystick_count = pygame.joystick.get_count()
        self.joysticks = {}

        # Initialize each joystick:
        for no in range(self.joystick_count):
            self.joysticks[no] = getJoystick(no)

        self.log("%i HID devices found" % self.joystick_count)

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
        # TODO: DIRTY HACK! DIIIIIRTY! REALLY DIRTY!
        # <Event(7-JoyAxisMotion {'joy': 0, 'axis': 4, 'value': 0.2989593188268685})>"}
        data = json.loads("{" + str(event).split("{")[1].rstrip(")>").replace("'", '"'))
        data['action'] = str(event).split("-")[1].split(" ")[0]
        message = {
            'component': 'avio.controller',
            'action': 'update',
            'data': data
        }
        self.fireEvent(
            broadcast("clientgroup", message, group=self.clients),
            "isomer-web"
        )

    @handler("ready", channel="*")
    def ready(self, *args):
        self.log("Starting controller input loop at %i Hz" % int(1 / self.delay))
        Timer(self.delay, Event.create('peek'), self.channel, persist=True).register(self)

    @handler("peek")
    def peek(self, event):
        if pygame.event.peek():
            for event in pygame.event.get():
                #self.log("EVENT:  " + str(event))

                if event.type in (pygame.JOYAXISMOTION,
                                  pygame.JOYHATMOTION,
                                  pygame.JOYBUTTONDOWN,
                                  pygame.JOYBUTTONUP,
                                  pygame.JOYBALLMOTION):
                    if event.type in (pygame.JOYAXISMOTION,
                                      pygame.JOYBALLMOTION):
                        if abs(event.value) < self.config.dead_center:
                            return
                    self.fireEvent(joystickchange(event))
                    self._notify_clients(event)


