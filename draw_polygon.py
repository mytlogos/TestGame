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
    screen.fill((255, 255, 255))
    if len(points) >= 3:
        pygame.draw.polygon(screen, (0, 255, 0), points, 10)

    for point in points:
        pygame.draw.circle(screen, (0, 0, 255), point, 1000, 10)
    pygame.display.update()
    time.sleep(0.001)
