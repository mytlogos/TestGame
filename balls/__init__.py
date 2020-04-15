import time
from abc import ABC, abstractmethod
from sys import exit
from typing import Union, Tuple

import pygame
from pygame.locals import *

from balls.game import Game, Ball, Player, GameState, AiPlayer
from vector2 import Vector2

pygame.init()

clock = pygame.time.Clock()

bar_dimension = (10, 100)

Color = Tuple[int, int, int]


class Texture(ABC):

    @abstractmethod
    def render(self, surface: pygame.Surface):
        pass


class PlayerTexture(Texture):
    player: Player
    color: Color

    def __init__(self, player: Player, color: Color) -> None:
        self.color = color
        self.player = player

    def render(self, surface: pygame.Surface):
        pygame.draw.rect(surface, (200, 200, 200), self.player.rect)


class BallTexture(Texture):
    ball: Ball
    color: Color

    def __init__(self, ball: Ball, color: Color) -> None:
        self.color = color
        self.ball = ball

    def render(self, surface: pygame.Surface):
        x = int(self.ball.rect.x)
        y = int(self.ball.rect.y)
        pygame.draw.circle(surface, (255, 255, 255), (x, y), 5)


class GameRenderer:
    game: Union[Game, None]
    ball: BallTexture
    left_player: PlayerTexture
    right_player: PlayerTexture
    screen: pygame.Surface
    time_between_loop = 0.01
    game_area: Rect
    info_area: Rect
    game_border: pygame.Surface

    def draw(self):
        self.screen.fill((0, 0, 0))

        if self.game.is_running():
            self.time_between_loop = 0.015
            self.draw_running_game()
        elif self.game.before_running():
            self.time_between_loop = 0.1
            self.draw_startup()
        elif self.game.is_finished():
            self.time_between_loop = 0.1
            self.draw_finished_game()

    def draw_running_game(self):
        screen_rect = self.screen.get_clip()
        rect_y_position = min(pygame.mouse.get_pos()[1], screen_rect.bottom - bar_dimension[1])
        time_passed = clock.tick()
        time_passed_seconds = time_passed / 1000.0

        self.game.time_to_last_tick = time_passed_seconds
        # self.game.time_to_last_tick = self.time_between_loop
        # is not really part of drawing, move it somewhere else?
        self.game.tick(rect_y_position, rect_y_position)

        self.left_player.render(self.screen)
        self.right_player.render(self.screen)
        self.ball.render(self.screen)

    def draw_startup(self):
        self.left_player.render(self.screen)
        self.right_player.render(self.screen)
        self.ball.render(self.screen)

    def draw_finished_game(self):
        pass

    def start(self):
        self.screen = pygame.display.set_mode((640, 480), 0, 32)
        screen_rect = self.screen.get_clip()
        self.info_area = Rect(screen_rect.left, screen_rect.top, screen_rect.width, 50)
        self.game_area = Rect(screen_rect.left, screen_rect.top + 50, screen_rect.width, screen_rect.height - 50)

        left_player_rect = Rect((self.game_area.left, self.game_area.centery), bar_dimension)
        left_player = AiPlayer(left_player_rect, self.game_area, "Player 1", False)

        right_player_rect = Rect((self.game_area.right - bar_dimension[0], self.game_area.centery), bar_dimension)
        right_player = AiPlayer(right_player_rect, self.game_area, "Player 2", True)

        self.left_player = PlayerTexture(left_player, (255, 255, 255))
        self.right_player = PlayerTexture(right_player, (255, 255, 255))

        ball = Ball(Rect(self.game_area.center, (10, 5)), self.game_area, Vector2(), 5, 250)
        self.ball = BallTexture(ball, (255, 255, 255))
        self.game = Game(ball, left_player, right_player, self.game_area)
        right_player.game = self.game
        left_player.game = self.game
        self.loop()

    def loop(self):
        while True:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    exit()
                if event.type == MOUSEBUTTONDOWN and self.game.game_state == GameState.WAIT_TO_START:
                    self.game.start()
                    clock.tick()
                    pygame.mouse.set_visible(False)

            self.draw()

            if self.game.game_state != GameState.RUNNING:
                pygame.mouse.set_visible(True)

            pygame.display.update()
            time.sleep(self.time_between_loop)


if __name__ == '__main__':
    GameRenderer().start()
