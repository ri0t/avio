#!/usr/bin/env python

import time
import pygame
import os


def splash_screen():
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    pygame.init()

    pygame.display.set_caption('AVIO Splashscreen')

    screen = pygame.display.set_mode((555, 542), pygame.NOFRAME)
    # TODO: Get correct image path
    background_image = pygame.image.load('images/startscreen.png')
    screen.blit(background_image, (0, 0))

    start = time.time()
    now = 0
    clicked = False

    while now < 10.0 and not clicked:
        pygame.display.update()

        if pygame.event.peek():
            for event in pygame.event.get():
                if event.type in (pygame.KEYUP, pygame.MOUSEBUTTONDOWN):
                    clicked = True
        now = time.time() - start


if __name__ == '__main__':
    splash_screen()
