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
import time

import pygame

from circuits import Event, Timer, handler

from avio_core.component import AVIOComponent
from avio_core.events import guiresize, guiquit

from pprint import pprint
from random import randint

hilight = (238, 126, 17, 128)
background = (31, 31, 31, 128)
dark = hilight
white = (255, 255, 255)
black = (0, 0, 0)

pygame.init()

fonts = {
    'main': os.path.abspath('fonts/editundo.ttf')
# TODO: Make sure this works when using installed AVIO package
}

guifont = pygame.font.Font(fonts['main'], 12)

names = []


def shade(a, b):
    if type(b) == float:
        return map(lambda x: int(x * b), a)
    elif type(b) == tuple:
        return map(lambda x: x / 2, map(sum, zip(a, b)))
    else:
        print("Bad shading requested! " + str(a) + str(b))
        return a


def inhitbox(coords, rect):
    if (coords[0] > rect[0] and coords[0] < rect[2] and coords[1] > rect[1] and
                coords[1] < rect[3]):
        return True


class paintrequest(Event):
    def __init__(self, srf, x, y, mode=0, clear=False,*args):
        super(paintrequest, self).__init__(*args)
        self.srf = srf
        self.x = x
        self.y = y
        self.mode = mode
        self.clear = clear


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


class setvalue(Event):
    def __init__(self, target, val, *args):
        super(setvalue, self).__init__(*args)
        self.target = target
        self.val = val
        print("Setting to " + str(self.val))


class toggle(Event):
    def __init__(self, target, *args):
        super(toggle, self).__init__(*args)
        self.target = target

class move(Event):
    def __init__(self, x, y, *args):
        super(move, self).__init__(*args)
        self.x = x
        self.y = y

class GUIComponent(AVIOComponent):
    screen = None

    def __init__(self, dataname=None, x=0, y=0, *args):
        super(GUIComponent, self).__init__(args)

        global names
        while True:
            uniquename = "%s%s" % (self.name, randint(0, 32768))
            if uniquename not in names:
                names.append(uniquename)
                break

        if not dataname:
            self.dataname = self.uniquename
        else:
            self.dataname = dataname

        #self.channel = self.dataname
        self.selected = False

        self.x = x
        self.y = y

    def move(self, event):
        self.x += event.x
        self.y += event.y

    def repaint(self, event):
        self.draw()


class Container(GUIComponent):
    def __init__(self, dataname, rect, *args, **kwargs):
        super(Container, self).__init__(dataname, *args, **kwargs)
        self.log("Initializing Container")

        self.rect = rect

        self.hitboxes = {}
        self.hitlist = []

    def registerhitbox(self, event):
        self.log("Hitbox registered:", event.origin, event.rect)
        self.hitboxes[event.rect] = {'origin': event.origin,
                                     'draggable': event.draggable}

    @handler('mouseevent')
    def mouseevent(self, event):
        coords = event.event.pos[0], event.event.pos[1]
        #self.log("Mouse event on " + str(self.channel))

        hitbox = None
        for rect in self.hitboxes.keys():
            if inhitbox(coords, rect):
                if hitbox:
                    self.log(
                    "Multiple hitboxes hit for " + str(hitbox) + " and " + str(
                        self.hitboxes[rect]))
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
        if event.event.type == pygame.MOUSEMOTION and event.event.buttons[
            0] == 1:
            #self.log("Click dragging!")
            for rect in self.hitboxes.keys():
                if inhitbox(coords, rect):
                    if not origin in self.hitlist and hitbox['draggable']:
                        self.fireEvent(toggle(origin))
                        self.hitlist.append(origin)

        if event.event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
            self.hitlist = []


class GUI(Container):
    channel = "gui"

    def __init__(self, *args, **kwargs):
        screensize = kwargs.get('screensize', (1920, 1200))
        self.screen_width, self.screen_height  = screensize
        self.rect = (0, 0, self.screen_width, self.screen_height)  # TODO: Reevaluate
        # upon resize

        super(GUI, self).__init__(self.rect, args)
        self.log("Initializing GUI")

        self.delay = 0.005

    def started(self, *args):
        pygame.display.set_caption('AVIO Core')
        self.fireEvent(guiresize(self.screen_width, self.screen_height))

        Timer(self.delay, Event.create('repaint'), self.channel,
              persist=True).register(self)

    def guiresize(self, event):
        self.log('Resize-Event:', event.width, event.height)
        GUIComponent.screen_width, self.screen_height = event.width, event.height
        GUIComponent.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height), pygame.RESIZABLE)
        GUIComponent.screen.fill(background)
        pygame.draw.rect(GUIComponent.screen, background,
                         (0, 0, self.screen_width, self.screen_height))

        self.fireEvent(draw())

    def paintrequest(self, event):
        #self.log("Painting by request: %i %i" % (event.x, event.y))
        if event.clear:
            pygame.draw.rect(GUIComponent.screen, background,
                             (event.x, event.y, event.srf.get_width(),
                              event.srf.get_height()))
        GUIComponent.screen.blit(event.srf, (event.x, event.y),
                                 special_flags=event.mode)

    def repaint(self):
        pygame.display.flip()
        GUIComponent.screen.fill(background)

    def buttonevent(self, event):
        if event.origin == "btnQuit":
            self.fireEvent(guiquit('btnQuit'))

    def keypress(self, event):

        k = event.ev.key
        if k == pygame.K_F11:
            self.log('Taking screenshot')
            filename = time.strftime("%Y-%m-%d_%H%M%S.jpg")
            filename = os.path.join(".", filename)

            pygame.image.save(GUIComponent.screen, filename)


class Label(GUIComponent):
    def __init__(self, dataname, label, rect, disabled=False, *args, **kwargs):
        super(Label, self).__init__(dataname, *args, **kwargs)
        self.log("Initializing label")

        self.label = label
        self.rect = rect
        self.disabled = disabled

        self.width = rect[2] - rect[0]
        self.height = rect[3] - rect[1]

    def started(self, *args):
        self.log("Starting up label " + self.dataname)

        self.fireEvent(registerhitbox(self.dataname, self.rect), "gui")

    @handler('draw', channel="gui")
    def draw(self):
        #super(Label, self).draw()
        #self.log("Label drawing")
        srf = pygame.Surface((self.width, self.height))
        if self.disabled:
            bright = shade(hilight, background)
        else:
            bright = hilight

        srf.fill(background)
        lbl = guifont.render(self.label, True, bright)

        center = ((self.width / 2) - lbl.get_width() / 2,
                  (self.height / 2) - lbl.get_height() / 2)
        srf.blit(lbl, center)

        self.fireEvent(paintrequest(srf, self.rect[0], self.rect[1]), "gui")


class Meter(GUIComponent):
    def __init__(self, dataname, label, left, top, width=20, height=100, val=0,
                 min=0, max=1, disabled=False, *args, **kwargs):
        super(Meter, self).__init__(dataname, *args, **kwargs)
        self.log("Initializing Meter")

        if label != '':
            self.label = label
        else:
            self.label = None
        self.top = top
        self.left = left
        self.disabled = disabled
        self.val = val
        self.min = min
        self.max = max

        self.width = width
        self.height = height
        self.rect = (left, top, left + width, top + height)

    def started(self, *args):
        self.log("Starting up label " + self.dataname)

    @handler('draw', channel="gui")
    def draw(self):
        #super(Meter, self).draw()
        #self.log("Meter drawing!")
        srf = pygame.Surface((self.width, self.height))
        if self.disabled:
            bright = shade(hilight, background)
        else:
            bright = hilight

        #pprint(("Meter data: ", self.val, self.max))

        #dark = shade(background, 0.6)
        #pprint(dark)
        srf.fill(dark)

        rect = (
        0, self.height - (self.height * (self.val - self.min) / self.max),
        self.width, self.height)
        #pprint(rect)
        pygame.draw.rect(srf, bright, rect)

        if self.label:
            lbl = guifont.render(self.label, True, background)

        if self.label:
            center = ((self.width / 2) - lbl.get_width() / 2,
                      (self.height / 2) - lbl.get_height() / 2)
            srf.blit(lbl, center)

        self.fireEvent(paintrequest(srf, self.left, self.top), "gui")

    def toggle(self, event):
        pass
        #self.log("HELLO:")
        #pprint(event)

    def setvalue(self, event):
        self.log("Meter received value event.")

        if event.target == self.dataname:
            self.log(self.dataname + " setting value: " + str(event.val))
            self.val = event.val
            self.draw()


class Button(GUIComponent):
    def __init__(self, dataname, label, rect, state=False, disabled=False,
                 draggable=False, *args, **kwargs):
        super(Button, self).__init__(dataname, *args, **kwargs)
        self.log("Initializing button")

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
        self.log("Starting up button " + self.dataname)

        self.fireEvent(registerhitbox(self.dataname, self.rect, self.draggable),
                       "gui")

    @handler('draw', channel="gui")
    def draw(self):
        #super(Button, self).draw()
        #self.log("Button drawing!")
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
            center = ((self.width / 2) - lbl.get_width() / 2,
                      (self.height / 2) - lbl.get_height() / 2)
            srf.blit(lbl, center)

        self.fireEvent(paintrequest(srf, self.rect[0], self.rect[1]), "gui")

    def toggle(self, event):
        #self.log("Button hit:", event.__dict__, pretty=True)

        if not self.disabled and event.target == self.dataname:
            self.log(self.dataname + " toggling.")
            self.state = not self.state
            self.draw()
            self.fireEvent(buttonevent(self.dataname, self.state),
                           self.channel)


class ButtonGrid(GUIComponent):
    def __init__(self, dataname, left, top, width=10, height=10, size=16,
                 *args, **kwargs):

        rect = (left, top, left + min(100, width * (size + 1)),
                top + 15 + height * (size + 1))

        super(ButtonGrid, self).__init__(dataname, rect, *args, **kwargs)

        self.log("Initializing buttongrid")

        self.left = left
        self.top = top
        self.width = width
        self.height = height
        self.size = size

        Button(self.dataname + '-btnInvert', 'Invert',
               (self.left, self.top, self.left + 100, self.top + 15),
               state=True).register(self)

        for x in range(self.width):
            for y in range(self.height):
                rect = (
                self.left + (x * self.size), self.top + 16 + (y * self.size),
                self.left + (x * self.size) + self.size - 1,
                self.top + 16 + (y * self.size) + self.size - 1)
                button = Button(self.dataname + '-btn' + str(x) + '-' + str(y),
                                '', rect, draggable=True).register(self)

    def draw(self):
        pass

    def buttonevent(self, event):
        self.log("Hello grid event")
        if event.origin == "btnInvert":
            self.log("Inverted Grid toggling: " + str(event.state))
            self.inverting = event.state

    def started(self, *args):
        self.log("Starting up buttongrid " + self.dataname)
