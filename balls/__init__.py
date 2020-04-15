import time
from abc import ABC, abstractmethod
from sys import exit
from typing import Tuple

import pygame
from pygame.locals import *

from balls.game import Game, Ball, Player, GameState, AiPlayer
from vector2 import Vector2

pygame.init()

clock = pygame.time.Clock()

bar_dimension = (10, 100)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
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
        pygame.draw.circle(surface, WHITE, (x, y), 5)


class GameInfoTexture(Texture):
    rect: Rect

    def __init__(self, rect: Rect) -> None:
        super().__init__()
        self.rect = rect

    def render(self, surface: pygame.Surface):
        startpos = (self.rect.left, self.rect.bottom)
        endpos = (self.rect.right, self.rect.bottom)
        pygame.draw.aaline(surface, WHITE, startpos, endpos)


class Renderer(ABC):
    master: "PingPongRenderer"

    def __init__(self, master: "PingPongRenderer") -> None:
        self.master = master

    @abstractmethod
    def draw(self, surface: pygame.Surface):
        surface.fill(BLACK)

    def tick(self) -> "Renderer":
        return self

    def handle_event(self, event: pygame.event.EventType):
        pass


class StartupGameRenderer(Renderer):
    def __init__(self, master: "PingPongRenderer") -> None:
        super().__init__(master)

    def draw(self, surface: pygame.Surface):
        super(StartupGameRenderer, self).draw(surface)

    def handle_event(self, event: pygame.event.EventType):
        if event.type == MOUSEBUTTONDOWN:
            renderer = self.start_game()
            self.master.renderer = renderer
            renderer.game.start()
            clock.tick()
            pygame.mouse.set_visible(False)

    def start_game(self) -> "RunningGameRenderer":
        screen_rect = self.master.screen.get_clip()
        info_area = Rect(screen_rect.left, screen_rect.top, screen_rect.width, 50)
        game_area = Rect(screen_rect.left, screen_rect.top + 50, screen_rect.width, screen_rect.height - 50)

        left_player_rect = Rect((game_area.left, game_area.centery), bar_dimension)
        left_player = AiPlayer(left_player_rect, game_area, "Player 1", False)

        right_player_rect = Rect((game_area.right - bar_dimension[0], game_area.centery), bar_dimension)
        right_player = AiPlayer(right_player_rect, game_area, "Player 2", True)

        left_player_texture = PlayerTexture(left_player, WHITE)
        right_player_texture = PlayerTexture(right_player, WHITE)

        ball = Ball(Rect(game_area.center, (10, 5)), game_area, Vector2(), 5, 250)
        ball_texture = BallTexture(ball, WHITE)
        current_game = Game(ball, left_player, right_player, game_area)
        right_player.game = current_game
        left_player.game = current_game

        info_texture = GameInfoTexture(info_area, current_game)
        return RunningGameRenderer(self.master, current_game, ball_texture, left_player_texture,
                                   right_player_texture, info_texture)


class FinishedGameRenderer(Renderer):
    def __init__(self, master: "PingPongRenderer") -> None:
        super().__init__(master)

    def draw(self, surface: pygame.Surface):
        super(FinishedGameRenderer, self).draw(surface)


class RunningGameRenderer(Renderer):
    game: Game
    ball: BallTexture
    left_player: PlayerTexture
    right_player: PlayerTexture
    info: GameInfoTexture
    game_area: Rect

    def __init__(self, master: "PingPongRenderer", current_game: Game, ball: BallTexture, left_player: PlayerTexture,
                 right_player: PlayerTexture, info_texture: GameInfoTexture) -> None:
        super().__init__(master)
        self.game = current_game
        self.ball = ball
        self.left_player = left_player
        self.right_player = right_player
        self.info = info_texture

    def draw(self, surface: pygame.Surface):
        super(RunningGameRenderer, self).draw(surface)
        self.info.render(surface)
        self.left_player.render(surface)
        self.right_player.render(surface)
        self.ball.render(surface)

    def tick(self) -> Renderer:
        screen_rect = self.master.screen.get_clip()
        rect_y_position = min(pygame.mouse.get_pos()[1], screen_rect.bottom - bar_dimension[1])
        time_passed = clock.tick()
        time_passed_seconds = time_passed / 1000.0

        self.game.time_to_last_tick = time_passed_seconds
        # self.game.time_to_last_tick = self.time_between_loop
        # is not really part of drawing, move it somewhere else?
        self.game.tick(rect_y_position, rect_y_position)

        if self.game.game_state != GameState.RUNNING:
            pygame.mouse.set_visible(True)

        if self.game.game_state == GameState.FINISHED:
            return FinishedGameRenderer(self.master)
        return self


class PingPongRenderer:
    screen: pygame.Surface
    time_between_loop = 0.01
    renderer: Renderer

    def start(self):
        self.screen = pygame.display.set_mode((640, 480), 0, 32)
        self.renderer = StartupGameRenderer(self)
        self.loop()

    def loop(self):
        while True:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    exit()
                self.renderer.handle_event(event)

            self.renderer = self.renderer.tick()
            self.renderer.draw(self.screen)

            pygame.display.update()
            time.sleep(self.time_between_loop)


if __name__ == '__main__':
    PingPongRenderer().start()
