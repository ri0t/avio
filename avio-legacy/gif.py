"""Uses code adapted from 'GIFImage' by Matthew Roe"""

from PIL import Image
from circuits import Worker, task
import pygame
from pygame.locals import *
from avio_core.gui import GUIComponent, handler
from avio_core.gui import paintrequest
from avio_core.logger import error

import time


#def load_image(data):
#    return [], [], 'Hello'


def load_image(data):
    """
    Threadable function to retrieve map tiles from the internet
    :param image:
    :param ignore_timings:
    """

    filename, ignore_timings, scale = data
    log = ""
    frames = []
    durations = []

    try:

        image = Image.open(filename)
        pal = image.getpalette()
        base_palette = []
        for i in range(0, len(pal), 3):
            rgb = pal[i:i + 3]
            base_palette.append(rgb)
        log += "\nPalette read"
        all_tiles = []
        try:
            while 1:
                if not image.tile:
                    image.seek(0)
                if image.tile:
                    all_tiles.append(image.tile[0][3][0])
                image.seek(image.tell() + 1)
        except EOFError:
            image.seek(0)

        log += "\nTiles collected"

        all_tiles = tuple(set(all_tiles))

        try:
            while 1:
                if not ignore_timings:
                    duration = image.info.get("duration", 100)
                else:
                    duration = 1000 / 30.0

                duration *= .001  # convert to milliseconds!
                cons = False

                x0, y0, x1, y1 = (0, 0) + image.size
                if image.tile:
                    tile = image.tile
                else:
                    image.seek(0)
                    tile = image.tile
                if len(tile) > 0:
                    x0, y0, x1, y1 = tile[0][1]

                if all_tiles:
                    if all_tiles in ((6,), (7,)):
                        cons = True
                        pal = image.getpalette()
                        palette = []
                        for i in range(0, len(pal), 3):
                            rgb = pal[i:i + 3]
                            palette.append(rgb)
                    elif all_tiles in ((7, 8), (8, 7)):
                        pal = image.getpalette()
                        palette = []
                        for i in range(0, len(pal), 3):
                            rgb = pal[i:i + 3]
                            palette.append(rgb)
                    else:
                        palette = base_palette
                else:
                    palette = base_palette

                pi = pygame.image.fromstring(image.tobytes(), image.size,
                                             image.mode)
                pi.set_palette(palette)
                # if "transparency" in image.info:
                #    pi.set_colorkey(image.info["transparency"])
                pi2 = pygame.Surface(image.size)
                if cons:
                    for i in frames:
                        pi2.blit(i[0], (0, 0))
                pi2.blit(pi, (x0, y0), (x0, y0, x1 - x0, y1 - y0))
                pi2 = pygame.transform.smoothscale(pi2, scale)

                frames.append([pi2, duration])
                durations.append(duration)
                image.seek(image.tell() + 1)
        except EOFError:
            pass
    except Exception as e:
        log += "\nERROR:" + str(e)

    log += "\nDone"

    return frames, durations, log


class GIFImage(GUIComponent):
    def __init__(self, dataname, filename, x=0, y=0, width=0, height=0,
                 transparency=255, scale=(1920, 1200),
                 ignore_timings=True, immediately=False):
        super(GIFImage, self).__init__(dataname)
        self.filename = filename

        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.transparency = transparency
        self.ignore_timings = ignore_timings
        self.factor = 1
        self.scale = scale

        self.delta = 0.0

        self.frames = []
        self.durations = []

        self.worker = Worker(process=False, workers=2,
                             channel="gifimport_"+dataname).register(self)

        # if transparency < 255:
        #    self.log('Setting alpha to %i' % transparency)
        #    for frame in self.frames:
        #        frame[0].set_alpha(transparency)
        self.cur = 0
        self.ptime = 0

        self.playing = False
        self.breakpoint = 0
        self.startpoint = 0
        self.reversed = False

        if immediately:
            self.get_frames()

    def started(self, event, thing):
        self.log('Converting image')
        self.get_frames()

    def get_rect(self):
        return pygame.rect.Rect((0, 0), self.image.size)

    def get_frames(self):
        self.log('Getting frames')
        try:
            # frames, durations, log = \
            data = self.filename, self.ignore_timings, self.scale
            self.fireEvent(
                task(
                    load_image, data
                ),
                "gifimport_"+self.dataname)
        except Exception as e:
            self.log("[GIF_WORKERS]", e, type(e), exc=True)

    def task_success(self, event, call, result):
        self.log(event.channels[0], pretty=True)
        if event.channels[0] != "gifimport_" + self.dataname:
            return
        if len(result) == 3:
            frames, durations, log = result
        else:
            self.log(result, pretty=True)
            return

        if len(frames) > 0:
            self.frames = frames
            self.durations = durations

            self.cur = 0
            self.ptime = time.time()

            self.playing = True
            self.breakpoint = len(self.frames) - 1
            self.startpoint = 0
            self.reversed = False

    def render(self):
        # pos = self.x, self.y
        # self.log('Rendering %s at %i, %i' % (self.filename, self.x, self.y))

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

            self.ptime = time.time()

        try:
            frame = self.frames[self.cur][0]
            self.fireEvent(
                paintrequest(
                    frame,
                    self.x, self.y,
                    pygame.BLEND_RGBA_MAX),
                "gui")
        except IndexError:
            pass

    def set_speed(self, factor):
        self.log('Setting new speed: %f' % factor)
        for i, duration in enumerate(self.durations):
            self.frames[i][1] = duration * factor

    @handler('keypress')
    def keypress(self, event):
        k = event.ev.key
        if k in (pygame.K_PLUS, pygame.K_MINUS):
            if event.ev.key == pygame.K_PLUS:
                self.factor /= 2
            if event.ev.key == pygame.K_MINUS:
                self.factor *= 2

            self.factor = max(0.0001, self.factor)
            self.factor = min(50, self.factor)

            self.set_speed(self.factor)

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

    def pause(self):
        self.playing = False

    def play(self):
        self.playing = True

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

    def copy(self):
        new = GIFImage(self.filename)
        new.playing = self.playing
        new.breakpoint = self.breakpoint
        new.startpoint = self.startpoint
        new.cur = self.cur
        new.ptime = self.ptime
        new.reversed = self.reversed
        return new

    @handler('repaint', channel="gui")
    def repaint(self):
        self.render()
