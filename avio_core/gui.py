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

import os.path

import pygame

from circuits import Component, Event, Timer, handler

from .events import guiresize, guiquit

from pprint import pprint
from random import randint

hilight = (238, 126, 17)
background = (31, 31, 31)
white = (255, 255, 255)
black = (0, 0, 0)

pygame.init()

fonts = {
    'main': os.path.abspath('fonts/editundo.ttf')  # TODO: Make sure this works when using installed AVIO package
}

guifont = pygame.font.Font(fonts['main'], 12)

names = []


def shade(a, b):
    return map(lambda x: x / 2, map(sum, zip(a, b)))

def inhitbox(coords, rect):
    if (coords[0] > rect[0] and coords[0] < rect[2] and coords[1] > rect[1] and coords[1] < rect[3]):
        return True

class paintrequest(Event):
    def __init__(self, srf, x, y, *args):
        super(paintrequest, self).__init__(*args)
        self.srf = srf
        self.x = x
        self.y = y


class registerhitbox(Event):
    def __init__(self, origin, rect, draggable=False, *args):
        super(registerhitbox, self).__init__(*args)
        self.origin = origin
        self.rect = rect
        self.draggable = draggable


class mouseevent(Event):
    def __init__(self, event, *args):
        super(mouseevent, self).__init__(*args)
        self.event = event


class draw(Event):
    pass


class buttonevent(Event):
    def __init__(self, origin, state, *args):
        super(buttonevent, self).__init__(*args)
        print('ButtonEvent')
        self.origin = origin
        self.state = state


class toggle(Event):
    def __init__(self, target, *args):
        super(toggle, self).__init__(*args)
        self.target = target

class GUIComponent(Component):
    def __init__(self, dataname, *args):
        super(GUIComponent, self).__init__(args)
        self.dataname = dataname

        global names
        while True:
            uniquename = "%s%s" % (self.name, randint(0, 32768))
            if uniquename not in names:
                names.append(uniquename)
                self.uniquename = uniquename
                break

        self.channel = self.uniquename

class Container(Component):
    def __init__(self, dataname, rect, *args, **kwargs):
        super(Container, self).__init__(dataname, *args, **kwargs)
        print("Initializing Container")

        self.rect = rect

        self.hitboxes = {}
        self.hitlist = []

    def registerhitbox(self, event):
        print("Hitbox registered.")
        self.hitboxes[event.rect] = {'origin': event.origin, 'draggable': event.draggable}

    @handler('mouseevent')
    def mouseevent(self, event):
        coords = event.event.pos[0], event.event.pos[1]
        print("Mouse event from " + str(self.uniquename) + str(self.channel))

        hitbox = None
        for rect in self.hitboxes.keys():
            if inhitbox(coords, rect):
                if hitbox:
                    print("Multiple hitboxes hit for " + str(hitbox) + " and " + str(self.hitboxes[rect]))
                hitbox = self.hitboxes[rect]

        if not hitbox:
            return
        else:
            origin = hitbox['origin']

        if event.event.type == pygame.MOUSEBUTTONDOWN:
            self.dragging = coords
            if not (origin in self.hitlist and hitbox['draggable']):

                self.fireEvent(toggle(origin), self.channel)
                self.hitlist.append(origin)
        if event.event.type == pygame.MOUSEMOTION and event.event.buttons[0] == 1:
            print("Click dragging!")
            for rect in self.hitboxes.keys():
                if inhitbox(coords, rect):
                    if not origin in self.hitlist and hitbox['draggable']:
                        self.fireEvent(toggle(origin), self.channel)
                        self.hitlist.append(origin)

        if event.event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
            self.hitlist = []

class GUI(Component):
    channel = "gui"

    def __init__(self, *args):
        super(GUI, self).__init__("gui", args)
        print("Initializing GUI")

        self.screen_width = 640
        self.screen_height = 480
        self.rect = (0, 0, 640, 480)  # TODO: Reevaluate upon resize
        self.screen = None

        self.delay = 0.005

    def started(self, *args):
        pygame.display.set_caption('AVIO Core')
        self.mainfont = pygame.font.Font('/home/riot/src/avio/fonts/editundo.ttf', 48)
        self.caption = self.mainfont.render('AVIO Core', True, (238, 126, 17))
        self.fireEvent(guiresize(self.screen_width, self.screen_height))

        Timer(self.delay, Event.create('repaint'), self.channel, persist=True).register(self)

    def guiresize(self, event):
        self.screen_width, self.screen_height = event.width, event.height
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        self.screen.fill((31, 31, 31))
        pygame.draw.rect(self.screen, (31, 31, 31), (0, 0, self.screen_width, self.screen_height))

        self.screen.blit(self.caption, (
            (self.screen_width / 2) - self.caption.get_width() / 2,
            (self.screen_height / 2) - self.caption.get_height() / 2))
        pygame.display.flip()

        self.fireEvent(draw())

    def paintrequest(self, event):
        print("Painting by request: %i %i" % (event.x, event.y))
        self.screen.blit(event.srf, (event.x, event.y))

    def repaint(self):
        pygame.display.flip()

    def buttonevent(self, event):
        if event.origin == "btnQuit":
            self.fireEvent(guiquit('btnQuit'))


class Label(GUIComponent):

    def __init__(self, dataname, label, rect, disabled=False, *args, **kwargs):
        super(Label, self).__init__(dataname, *args, **kwargs)
        print("Initializing label")

        self.label = label
        self.rect = rect
        self.disabled = disabled

        self.width = rect[2] - rect[0]
        self.height = rect[3] - rect[1]

    def started(self, *args):
        print("Starting up label " + self.uniquename)

        self.fireEvent(registerhitbox(self.channel, self.rect), "gui")

    @handler('draw', channel="gui")
    def draw(self):
        print("Label drawing")
        srf = pygame.Surface((self.width, self.height))
        if self.disabled:
            bright = shade(hilight, background)
        else:
            bright = hilight

        srf.fill(background)
        lbl = guifont.render(self.label, True, bright)

        center = ((self.width / 2) - lbl.get_width() / 2, (self.height / 2) - lbl.get_height() / 2)
        srf.blit(lbl, center)

        self.fireEvent(paintrequest(srf, self.rect[0], self.rect[1]), "gui")



class Button(Component):

    def __init__(self, dataname, label, rect, state=False, disabled=False, draggable=False, *args, **kwargs):
        super(Button, self).__init__(dataname, *args, **kwargs)
        print("Initializing button")

        if label != '':
            self.label = label
        else:
            self.label = None
        self.rect = rect
        self.state = state
        self.disabled = disabled
        self.draggable = draggable

        self.width = rect[2] - rect[0]
        self.height = rect[3] - rect[1]

    def started(self, *args):
        print("Starting up button " + self.uniquename)

        self.fireEvent(registerhitbox(self.channel, self.rect, self.draggable), "gui")

    @handler('draw', channel="gui")
    def draw(self):
        print("Button drawing!")
        srf = pygame.Surface((self.width, self.height))
        if self.disabled:
            bright = shade(hilight, background)
        else:
            bright = hilight

        if self.state:
            srf.fill(background)
            if self.label:
                lbl = guifont.render(self.label, True, bright)
        else:
            srf.fill(bright)
            if self.label:
                lbl = guifont.render(self.label, True, background)

        if self.label:
            center = ((self.width / 2) - lbl.get_width() / 2, (self.height / 2) - lbl.get_height() / 2)
            srf.blit(lbl, center)

        self.fireEvent(paintrequest(srf, self.rect[0], self.rect[1]), "gui")

    def toggle(self, event):

        if not self.disabled and event.target == self.uniquename:
            print(self.uniquename + " toggling.")
            self.state = not self.state
            self.draw()
            self.fireEvent(buttonevent(self.uniquename, self.state), self.channel)


class ButtonGrid(Container):
    def __init__(self, dataname, left, top, width=10, height=10, size=16, *args, **kwargs):

        rect = (left, top, left + min(100, width * (size + 1)), top + 15 + height * (size + 1))

        super(ButtonGrid, self).__init__(dataname, rect, *args, **kwargs)

        print("Initializing buttongrid")

        self.left = left
        self.top = top
        self.width = width
        self.height = height
        self.size = size

        Button('btnInvert', 'Invert', (self.left, self.top, self.left + 100, self.top + 15), state=True).register(self)

        for x in range(self.width):
            for y in range(self.height):
                rect = (self.left + (x * self.size), self.top + 16 + (y * self.size), self.left + (x * self.size) + self.size - 1, self.top + 16 + (y * self.size) + self.size - 1)
                button = Button('btn' + str(x) + '-' + str(y), '', rect, draggable=True).register(self)

    def buttonevent(self, event):
        print("Hello grid event")
        if event.origin == "btnInvert":
            print("Inverted Grid toggling: " + str(event.state))
            self.inverting = event.state

    def started(self, *args):
        print("Starting up buttongrid " + self.uniquename)
