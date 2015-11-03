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

from circuits import Component, Timer, Event

from .events import joystickchange, guiquit, guiresize

from .gui import mouseevent

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


class Controller(Component):
    """
    """

    def __init__(self, delay=0.010, *args):

        super(Controller, self).__init__(args)
        print("Initializing controller")

        self.delay = delay
        self.acting = True

        self.joystick_count = pygame.joystick.get_count()
        self.joysticks = {}

        # Initialize each joystick:
        for no in range(self.joystick_count):
            self.joysticks[no] = getJoystick(no)

    def started(self, *args):
        """
        """

        print("Starting controller input loop at %i Hz" % int(1 / self.delay))
        Timer(self.delay, Event.create('peek'), self.channel, persist=True).register(self)

    def peek(self, event):

        if pygame.event.peek():
            for event in pygame.event.get():
                #print("EVENT:  " + str(event))

                if event == pygame.QUIT:
                    self.fireEvent(guiquit("close"))
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_q:
                        self.fireEvent(guiquit("key"))
                elif event.type == pygame.VIDEORESIZE:
                    self.fireEvent(guiresize(event.w, event.h), "gui")
                elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                    self.fireEvent(mouseevent(event), "gui")
                elif event.type in (pygame.JOYAXISMOTION,
                                  pygame.JOYHATMOTION,
                                  pygame.JOYBUTTONDOWN,
                                  pygame.JOYBUTTONUP,
                                  pygame.JOYBALLMOTION):
                    self.fireEvent(joystickchange(event))


