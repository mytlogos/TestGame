import time
from abc import ABC, abstractmethod
from datetime import datetime
from sys import exit
from typing import Tuple, List, Callable

import pygame
from pygame.locals import *

from balls.game import Game, Ball, Player, GameState, AiPlayer
from vector2 import Vector2

pygame.init()

clock = pygame.time.Clock()

bar_dimension = (10, 100)
Color = Tuple[int, int, int]
WHITE: Color = (255, 255, 255)
BLACK: Color = (0, 0, 0)


def diff_time(end, start):
    diff = (end - start).total_seconds()
    d = int(diff / 86400)
    h = int((diff - (d * 86400)) / 3600)
    m = int((diff - (d * 86400 + h * 3600)) / 60)
    s = int((diff - (d * 86400 + h * 3600 + m * 60)))
    if d > 0:
        result = f'{d}d {h}h {m}m {s}s'
    elif h > 0:
        result = f'{h}h {m}m {s}s'
    elif m > 0:
        result = f'{m}m {s}s'
    else:
        result = f'{s}s'
    return result


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
    game: Game
    left_player_name: pygame.Surface
    right_player_name: pygame.Surface

    def __init__(self, rect: Rect, current_game: Game) -> None:
        super().__init__()
        self.rect = rect
        self.game = current_game
        self.font = pygame.font.SysFont("arial", 16)
        self.left_player_name = self.font.render(current_game.left_player.name, True, WHITE)
        self.right_player_name = self.font.render(current_game.right_player.name, True, WHITE)

    def render(self, surface: pygame.Surface):
        left_player_rect = surface.blit(self.left_player_name, (self.rect.left + 5, self.rect.top + 5))

        right_player_beginning = self.rect.right - self.right_player_name.get_width() - 5
        surface.blit(self.right_player_name, (right_player_beginning, self.rect.top + 5))

        time_running = diff_time(datetime.now(), self.game.started_at)
        time_surface = self.font.render(time_running, True, WHITE)
        surface.blit(time_surface, (self.rect.left + 5, left_player_rect.bottom + 5))

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


ClickHandler = Callable[[], None]


class MenuItem(Texture):
    rect: Rect
    index: int
    text_rect: Rect
    text_surface: pygame.Surface
    hovering: bool
    click_handler: ClickHandler

    def __init__(self, index: int, parent_rect: Rect, text: str, handler: ClickHandler) -> None:
        super().__init__()
        left, width = parent_rect.left, parent_rect.width
        height = 50
        top = parent_rect.top + (index * height)
        self.rect = Rect(left, top, width, height)
        padding = 5
        font = pygame.font.SysFont("arial", height - (padding * 2))
        self.text_surface = font.render(text, True, WHITE, BLACK)
        self.text_surface_hovered = font.render(text, True, BLACK, WHITE)
        text_rect = self.text_surface.get_clip()

        padding_x = int((width - text_rect.width) / 2)
        padding_y = int((height - text_rect.height) / 2)
        self.text_rect = Rect(left + padding_x, top + padding_y, width - (padding_x * 2), height - (padding_y * 2))
        self.index = index
        self.click_handler = handler

    def on_click(self):
        if self.click_handler:
            self.click_handler()

    def render(self, surface: pygame.Surface):
        if self.hovering:
            pygame.draw.rect(surface, WHITE, self.rect)
            surface.blit(self.text_surface_hovered, self.text_rect)
        else:
            pygame.draw.rect(surface, WHITE, self.rect, 2)
            surface.blit(self.text_surface, self.text_rect)


class StartupGameRenderer(Renderer):
    menu_items: List[MenuItem]
    background_game: "RunningGameRenderer"

    def __init__(self, master: "PingPongRenderer") -> None:
        super().__init__(master)
        rect: Rect = master.screen.get_clip()
        width = 300
        height = 200
        top = int(rect.centery - (height / 2))
        left = int(rect.centerx - (width / 2))
        self.rect = Rect((left, top), (width, height))
        sub_rect = Rect(0, 0, width, height)
        self.menu_items = [
            MenuItem(0, sub_rect, "Create Game", self.create_game),
            MenuItem(1, sub_rect, "Highscore", self.display_highscore),
            MenuItem(2, sub_rect, "About", self.display_about)
        ]
        self.background_surface = pygame.Surface((rect.width, rect.height))
        self.background_surface.set_alpha(100)
        self.foreground_surface = pygame.Surface((width, height))
        self.foreground_surface.set_alpha(255)
        self.background_game = self.create_background_game()

    def create_background_game(self) -> "RunningGameRenderer":
        renderer = self.start_game()
        renderer.game.start()
        clock.tick()
        return renderer

    def tick(self) -> "Renderer":
        renderer = self.background_game.tick()

        # when previous game finished, create a new game
        if renderer != self.background_game:
            self.background_game = self.create_background_game()
        return super().tick()

    def draw(self, surface: pygame.Surface):
        surface.fill(WHITE)
        super(StartupGameRenderer, self).draw(self.background_surface)
        super(StartupGameRenderer, self).draw(self.foreground_surface)

        self.background_game.draw(self.background_surface)

        mouse_x, mouse_y = pygame.mouse.get_pos()
        # translate mouse position from screen to subsurface
        mouse_x -= self.rect.left
        mouse_y -= self.rect.top

        for item in self.menu_items:
            item.hovering = item.rect.collidepoint(mouse_x, mouse_y)
            item.render(self.foreground_surface)

        surface.blit(self.background_surface, self.background_surface.get_clip())
        surface.blit(self.foreground_surface, self.rect)

    def handle_event(self, event: pygame.event.EventType):
        if event.type == MOUSEBUTTONDOWN:
            for item in self.menu_items:
                if item.rect.collidepoint(*event.pos):
                    item.on_click()

    def create_game(self):
        renderer = self.start_game()
        self.master.renderer = renderer
        renderer.game.start()
        clock.tick()
        pygame.mouse.set_visible(False)

    def display_highscore(self):
        print(self)

    def display_about(self):
        print(self)

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
        self.screen = pygame.display.set_mode((640, 480), pygame.RESIZABLE, 32)
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
