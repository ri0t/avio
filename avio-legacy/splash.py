#!/usr/bin/env python

import time
import pygame
import os
import screeninfo

splash_width = 555
splash_height = 542
duration = 10.0


def splash_screen():
    m = screeninfo.get_monitors()

    if len(m) > 1:
        # Find first screen and center splash there
        for screen in m:
            if screen.x == 0:
                x = (screen.width / 2) - (splash_width / 2.0)
                y = (screen.height / 2) - (splash_height / 2.0)
                os.environ['SDL_VIDEO_WINDOW_POS'] = str((x, y))
    else:
        os.environ['SDL_VIDEO_CENTERED'] = '1'

    pygame.init()

    pygame.display.set_caption('AVIO Splashscreen')

    screen = pygame.display.set_mode((splash_width, splash_height), pygame.NOFRAME)
    # TODO: Get correct image path
    background_image = pygame.image.load('images/startscreen.png')
    screen.blit(background_image, (0, 0))

    start = time.time()
    waited = 0
    clicked = False

    while waited < duration and not clicked:
        pygame.display.update()

        if pygame.event.peek():
            for event in pygame.event.get():
                if event.type in (pygame.KEYUP, pygame.MOUSEBUTTONDOWN):
                    clicked = True
        waited = time.time() - start


if __name__ == '__main__':
    splash_screen()
