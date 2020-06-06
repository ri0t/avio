"""Uses code adapted from 'GIFImage' by Matthew Roe"""

import os
import time

import formal
from PIL import Image
from circuits import Worker, task, Timer
import pygame
from isomer.component import ConfigurableComponent, LoggingComponent, handler, authorized_event
from isomer.events.system import isomer_event
from isomer.events.client import broadcast, send
from isomer.logger import verbose, warn, debug, hilight
# from isomer.matelight import transmit_ml
from isomer.debugger import cli_register_event

from .videomixer import mix_image


# def load_image(data):
#     return [], [], 'Hello'


class unsubscribe(authorized_event):
    pass


class subscribe(authorized_event):
    pass


class add_player(authorized_event):
    pass


class remove_player(authorized_event):
    pass


class get_data(authorized_event):
    pass


class change_player(authorized_event):
    pass


class render(isomer_event):
    """Render another frame"""
    pass


class cli_test_gifplayer(isomer_event):
    pass


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
                pi2 = pygame.surfarray.array3d(pi2)

                frames.append([pi2, duration])
                durations.append(duration)
                image.seek(image.tell() + 1)
        except EOFError:
            pass
    except Exception as e:
        log += "\nERROR:" + str(e)

    log += "\nDone"

    return frames, durations, log


class GIFMaster(ConfigurableComponent):
    configprops = {
        'channels': {
            'type': 'array',
            'items': {
                'type': 'object',
                'id': 'gifplayersettings',
                'name': 'gifplayersettings',
                'properties': {
                    'playing': {'type': 'boolean', 'default': False},
                    'filename': {'type': 'string', 'default': ''},
                    'ignore_timings': {'type': 'boolean', 'default': True},
                    'immediately': {'type': 'boolean', 'default': True},
                    'loop':  {'type': 'boolean', 'default': True},
                    'bounce': {'type': 'boolean', 'default': False},
                    'reverse': {'type': 'boolean', 'default': False},
                    'bounds': {
                        'type': 'array',
                        'items': {'type': 'number', 'default': 0},
                        'maxItems': 2,
                        'default': [0, 100]
                    },
                    'scale': {
                        'type': 'object',
                        'properties': {
                            'width': {'type': 'integer', 'default': 40},
                            'height': {'type': 'integer', 'default': 16},
                        },
                        'default': {'width': 40, 'height': 16}
                    },
                    'delay': {'type': 'number', 'default': 30.0},
                    'channel': {'type': 'integer'}
                },
            }
        }
    }
    
    def __init__(self):
        super(GIFMaster, self).__init__("GIFMASTER")
        
        self.players = {}
        self.player_model = formal.model_factory(self.configprops['channels']['items'])

    @handler(add_player)
    def add_player(self, event):

        settings = self.player_model()

        settings.filename = event.data['filename']
        settings.channel = event.data['channel']

        # TODO: This is not determinable here, so we have to take it from the gifplayer
        settings.length = 0

        gifplayer_settings = settings.serializablefields()
        self.log(gifplayer_settings, pretty=True)
        self._add_player(gifplayer_settings)

        result = {
            'component': 'avio.gifplayer',
            'action': 'add_player',
            'data': gifplayer_settings
        }
        self.fireEvent(send(event.client.uuid, result))

    @handler(change_player)
    def change_player(self, event):
        self.log('Changing player:', event.data['channel'])
        settings = self.player_model(event.data).serializablefields()

        self.players[event.data['channel']].update(settings)

        result = {
            'component': 'avio.gifplayer',
            'action': 'change_player',
            'data': settings
        }
        self.fireEvent(send(event.client.uuid, result))

    def _add_player(self, settings):
        new_player = GIFPlayer(settings).register(self)
        self.players[settings['channel']] = new_player

    @handler(remove_player)
    def remove_player(self, event):

        player = self.players[int(event.data)]
        self.players[int(event.data)] = None
        player.stop()
        player.unregister()
        del player

        result = {
            'component': 'avio.gifplayer',
            'action': 'remove_player',
            'data': int(event.data)
        }
        self.fireEvent(send(event.client.uuid, result))

    @handler(get_data, channel="isomer-web")
    def get_data(self, event):
        self.log("Providing mixer config:", event.client, pretty=True)
        response = {
            'component': 'avio.gifmaster',
            'action': 'get_data',
            'data': {
                'schema': self.configprops['channels']['items'],
                'config': self.config.serializablefields()
            }
        }
        self.fireEvent(send(event.client.uuid, response), "isomer-web")

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


class GIFPlayer(LoggingComponent):
    """GIF Player with configurable output"""

    def __init__(self, settings):
        super(GIFPlayer, self).__init__()

        self.log('Player initializing')

        pygame.display.init()
        
        self.config = settings

        self.factor = 1

        self.delta = 0.0

        self.frames = []
        self.durations = []

        self.clients = []

        self.timer = None
        self.worker = Worker(process=False, workers=2,
                             channel="gifimport_" + self.uniquename).register(self)

        # if transparency < 255:
        #    self.log('Setting alpha to %i' % transparency)
        #    for frame in self.frames:
        #        frame[0].set_alpha(transparency)
        self.cur = 0
        self.ptime = 0

        self.playing = False
        self.breakpoint = 0
        self.startpoint = 0

        self.direction = True

        self.fireEvent(cli_register_event("test_gifplayer", cli_test_gifplayer))

        if self.config['immediately']:
            self.get_frames()

    def cli_test_gifplayer(self, *args):
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

    def update(self, settings):
        self.log('Updating', self.playing, self.config['playing'])

        if self.config['delay'] != settings['delay']:
            self.set_speed(settings['delay'])
        if self.config['bounds'] != settings['bounds']:
            self.set_bounds(*settings['bounds'])

        self.config = settings

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
        self.get_frames()

    def get_frames(self):
        self.log('Getting frames')
        if self.config['filename'] in (None, ""):
            self.log('No filename, cannot load gif')
            return
        try:
            # frames, durations, log = \
            scale = (self.config['scale']['height'], self.config['scale']['width'])
            data = self.config['filename'], self.config['ignore_timings'], scale
            self.fireEvent(
                task(
                    load_image, data
                ),
                "gifimport_" + self.uniquename)
            self.log('Worker started', lvl=verbose)
        except Exception as e:
            self.log("[GIF_WORKERS]", e, type(e), exc=True)

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
        else:
            self.log("No frames extracted:", log, lvl=warn)

    def render(self):
        # pos = self.x, self.y
        # self.log('Rendering %s' % self.config['filename'], lvl=verbose)

        if self.playing:
            self.delta += time.time() - self.ptime
            if self.delta > self.frames[self.cur][1]:
                # TODO: Rebuild this without loop, i.e. calculate the distance to jump
                while self.delta > self.frames[self.cur][1]:

                    self.delta -= self.frames[self.cur][1]
                    if self.config['reverse'] or (self.config['bounce'] and self.direction == -1):
                        self.cur -= 1
                        if self.cur < self.startpoint:
                            self.cur = self.breakpoint
                            if not self.config['loop']:
                                self.stop()
                            if self.config['bounce']:
                                self.direction = +1
                    else:
                        self.cur += 1
                        if self.cur > self.breakpoint:
                            self.cur = self.startpoint
                            if not self.config['loop']:
                                self.stop()
                            if self.config['bounce']:
                                self.direction = -1

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
        # TODO: Maybe only transmit necessary data, not statics like length or always
        #  the whole config
        message = {
            'component': 'avio.gifplayer',
            'action': 'frame_update',
            'data': {
                'channel': self.config['channel'],
                'config': self.config,
                'current': self.cur,
                'length': self.breakpoint - self.startpoint,
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
        length = len(self.frames)
        # TODO: I think, the outer min/max operations can be safely omitted
        self.startpoint = max(0, int(length * (max(0, start) / 100.0)))
        self.breakpoint = min(int(length * (min(100, end) / 100)), length) - 1

    def stop(self):
        self.log('Stop!', lvl=debug)
        self.playing = False
        if self.timer is not None:
            self.timer.stop()
            self.timer.unregister()
            self.timer = None
        self._broadcast(self.frames[self.cur][0])

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
