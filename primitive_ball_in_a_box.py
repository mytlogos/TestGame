import time
from sys import exit

import pygame
from pygame.locals import *

pygame.init()
screen = pygame.display.set_mode((640, 480), 0, 32)
points = []
sprite = pygame.image.load("images/play.png")
x, y = 0, 0

clock = pygame.time.Clock()
speed_x, speed_y = 0.150, 0.150

screen.fill((255, 255, 255))
while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            exit()

    # screen.fill((255, 255, 255))
    screen.blit(sprite, (x, y))
    time_passed_s = clock.tick(60)

    x += int(time_passed_s * speed_x)
    y += int(time_passed_s * speed_y)
    # x += 1
    # If the image goes off the end of the screen, move it back
    if x > 640 - sprite.get_width():
        speed_x = -speed_x
        x = 640 - sprite.get_width()
    elif x < 0:
        speed_x = -speed_x
        x = 0
    if y > 480 - sprite.get_height():
        speed_y = -speed_y
        y = 480 - sprite.get_height()
    elif y < 0:
        speed_y = -speed_y
    pygame.display.update()
    time.sleep(0.001)
