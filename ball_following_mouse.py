import time
from sys import exit

import pygame
from vector2 import Vector2
from pygame.locals import *

pygame.init()
screen = pygame.display.set_mode((640, 480), 0, 32)
sprite = pygame.image.load("images/play.png").convert_alpha()
clock = pygame.time.Clock()
position = Vector2(100.0, 100.0)
speed = 250
heading = Vector2()

while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            exit()

    destination = Vector2(*pygame.mouse.get_pos()) - (Vector2(*sprite.get_size()) / 2)
    heading = Vector2.from_points(position, destination)
    heading.normalize()

    screen.blit(sprite, (int(position.x), int(position.y)))
    time_passed = clock.tick()
    time_passed_seconds = time_passed / 1000.0

    distance_moved = time_passed_seconds * speed
    position += heading * distance_moved
    pygame.display.update()
    time.sleep(0.01)
