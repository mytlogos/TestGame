import random
import time
from sys import exit

import pygame
from pygame.locals import *

pygame.init()
screen = pygame.display.set_mode((640, 480), 0, 32)
points = []

while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            exit()
        if event.type == MOUSEBUTTONDOWN:
            points.append(event.pos)
            print("point appended: " + str(event.pos))
    points.append((random.randint(0, 639), random.randint(0, 479)))
    screen.lock()
    screen.fill((255, 255, 255))

    if len(points) > 100:
        del points[0]

    if len(points) > 1:
        pygame.draw.aalines(screen, (0, 255, 0), False, points, 2)

    screen.unlock()
    pygame.display.update()
    time.sleep(0.01)
