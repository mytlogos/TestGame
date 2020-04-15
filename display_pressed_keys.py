import time
from sys import exit

import pygame
from pygame.locals import *

pygame.init()
screen = pygame.display.set_mode((640, 480), 0, 32)
font = pygame.font.SysFont("arial", 32)
font_height = font.get_linesize()
while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            exit()
    screen.fill((255, 255, 255))
    pressed_key_text = []
    pressed_keys = pygame.key.get_pressed()
    y = font_height
    for key_constant, pressed in enumerate(pressed_keys):
        if pressed:
            key_name = pygame.key.name(key_constant)
            text_surface = font.render()
            screen.blit(text_surface, (8, y))
            y += font_height
    pygame.display.update()
    time.sleep(0.01)
