import time
from abc import ABC, abstractmethod
from datetime import datetime
from sys import exit
from typing import Tuple, List, Callable, Any

import pygame
from pygame import locals

from balls.game import Game, Ball, Player, GameState, AiPlayer
from balls.text import TextInput
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
    rect: locals.Rect
    game: Game
    left_player_name: pygame.Surface
    right_player_name: pygame.Surface

    def __init__(self, rect: locals.Rect, current_game: Game) -> None:
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

    def handle_events(self, events: List[pygame.event.EventType]):
        pass


ClickHandler = Callable[[], None]


class MenuItem(Texture):
    rect: locals.Rect
    index: int
    text_rect: locals.Rect
    text_surface: pygame.Surface
    hovering: bool
    click_handler: ClickHandler

    def __init__(self, index: int, parent_rect: locals.Rect, text: str, handler: ClickHandler) -> None:
        super().__init__()
        left, width = parent_rect.left, parent_rect.width
        height = 50
        top = parent_rect.top + (index * height)
        self.rect = locals.Rect(left, top, width, height)
        padding = 5
        font = pygame.font.SysFont("arial", height - (padding * 2))
        self.text_surface = font.render(text, True, WHITE, BLACK)
        self.text_surface_hovered = font.render(text, True, BLACK, WHITE)
        text_rect = self.text_surface.get_clip()

        padding_x = int((width - text_rect.width) / 2)
        padding_y = int((height - text_rect.height) / 2)
        self.text_rect = locals.Rect(left + padding_x, top + padding_y, width - (padding_x * 2),
                                     height - (padding_y * 2))
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


class CheckBox(Texture):
    text: str
    checked: bool
    focused: bool
    font: pygame.font.Font
    rect: locals.Rect
    text_surface: pygame.Surface
    box_rect: locals.Rect
    last_checked_change_time: float

    def __init__(self, text: str, font: pygame.font.Font, rect: locals.Rect) -> None:
        super().__init__()
        self.text = text
        self.font = font
        self.text_surface = self.font.render(text, True, BLACK)
        self.rect = rect
        self.focused = False
        self.checked = False
        self.box_rect = self.rect.copy()
        self.box_rect.width = rect.height - 10
        self.box_rect.height = self.box_rect.width
        self.box_rect.left = self.rect.left + self.text_surface.get_width() + 5
        self.box_rect.centery = self.rect.centery
        self.last_checked_change_time = 0

    def on_click(self):
        self.toggle_checked()

    def toggle_checked(self):
        current_time = time.monotonic() * 1000

        if current_time - self.last_checked_change_time > 200:
            self.checked = not self.checked
            self.last_checked_change_time = current_time

    def render(self, surface: pygame.Surface):
        surface.blit(self.text_surface, self.rect)
        pygame.draw.rect(surface, BLACK, self.box_rect, 1)

        if self.checked:
            bottom = self.box_rect.bottom - 2
            left = self.box_rect.left + 2
            top = self.box_rect.top + 2
            right = self.box_rect.right - 2
            pygame.draw.line(surface, BLACK, (left, bottom), (right, top), 3)
            pygame.draw.line(surface, BLACK, (right, bottom), (left, top), 3)


class Button(Texture):
    text: str
    text_surface: pygame.Surface
    text_surface_active: pygame.Surface
    rect: locals.Rect
    text_rect: locals.Rect
    hovering: bool
    focused: bool
    action_handler: ClickHandler

    def __init__(self, text: str, font: pygame.font.Font, action_handler: ClickHandler) -> None:
        super().__init__()
        self.text = text
        self.text_surface = font.render(text, True, BLACK)
        self.text_surface_active = font.render(text, True, WHITE)
        self.text_rect = self.text_surface.get_rect()
        self.rect = self.text_surface.get_rect().copy()
        self.rect.width += 10
        self.rect.height += 10
        self.action_handler = action_handler
        self.focused = False
        self.hovering = False

    def set_right(self, right: int):
        self.rect.right = right
        self.text_rect.right = right - 5

    def set_bottom(self, bottom: int):
        self.rect.bottom = bottom
        self.text_rect.bottom = bottom - 5

    def on_action(self):
        if self.action_handler:
            self.action_handler()

    def on_click(self):
        self.on_action()

    def render(self, surface: pygame.Surface):
        if self.focused or self.hovering:
            pygame.draw.rect(surface, BLACK, self.rect)
            surface.blit(self.text_surface_active, self.text_rect)
        else:
            pygame.draw.rect(surface, BLACK, self.rect, 1)
            surface.blit(self.text_surface, self.text_rect)


class CreateGameRenderer(Renderer):
    left_player_text: pygame.Surface
    left_player_text_rect: locals.Rect
    right_player_text: pygame.Surface
    right_player_text_rect: locals.Rect
    left_player_input: TextInput
    left_player_input_rect: locals.Rect
    right_player_input: TextInput
    right_player_input_rect: locals.Rect
    right_player_ai_checkbox: CheckBox
    left_player_ai_checkbox: CheckBox
    focus_chain: List[Any]
    focused: int
    last_focus_change: float

    def __init__(self, master: "PingPongRenderer") -> None:
        super().__init__(master)
        rect: locals.Rect = master.screen.get_clip()
        width = 500
        height = 200
        top = int(rect.centery - (height / 2))
        left = int(rect.centerx - (width / 2))
        self.rect = locals.Rect((left, top), (width, height))

        font_family = "arial"
        font_size = 30
        self.font = font = pygame.font.SysFont(font_family, font_size)
        self.left_player_text = font.render("Left Player:", True, BLACK)
        self.right_player_text = font.render("Right Player:", True, BLACK)
        self.right_player_ai_text = font.render("Right Player AI:", True, BLACK)

        self.left_player_text_rect = self.left_player_text.get_clip()
        self.left_player_text_rect.top = top
        self.left_player_text_rect.left = left

        self.right_player_text_rect = self.right_player_text.get_clip()
        self.right_player_text_rect.top = self.left_player_text_rect.bottom + 5
        self.right_player_text_rect.left = left

        self.left_player_input = TextInput(text_color=BLACK, font_family=font_family, font_size=font_size)
        self.right_player_input = TextInput(text_color=BLACK, font_family=font_family, font_size=font_size)
        self.left_player_input.width = self.rect.right - self.left_player_text_rect.right - 10
        self.right_player_input.width = self.rect.right - self.right_player_text_rect.right - 10

        self.left_player_input_rect = self.left_player_text_rect.copy()
        self.left_player_input_rect.left = self.left_player_text_rect.right + 5
        self.left_player_input_rect.width = self.left_player_input.width + 5

        self.right_player_input_rect = self.right_player_text_rect.copy()
        self.right_player_input_rect.left = self.right_player_text_rect.right + 5
        self.right_player_input_rect.width = self.right_player_input.width + 5

        top = self.right_player_text_rect.bottom + 5
        left_player_ai_check_rect = locals.Rect(left, top, width, font.get_height())
        top = left_player_ai_check_rect.bottom + 5
        right_player_ai_check_rect = locals.Rect(left, top, width, font.get_height())

        self.left_player_ai_checkbox = CheckBox("Left Player AI:", font, left_player_ai_check_rect)
        self.right_player_ai_checkbox = CheckBox("Right Player AI:", font, right_player_ai_check_rect)

        self.start_button = Button("Start", font, self.create_game)
        self.start_button.set_right(self.rect.right - 5)
        self.start_button.set_bottom(self.rect.bottom - 5)

        self.cancel_button = Button("Cancel", font, self.return_to_start)
        self.cancel_button.set_right(self.start_button.rect.left - 5)
        self.cancel_button.set_bottom(self.rect.bottom - 5)

        self.focus_chain = [self.left_player_input, self.right_player_input, self.left_player_ai_checkbox,
                            self.right_player_ai_checkbox, self.cancel_button, self.start_button]
        self.focused = -1
        self.last_focus_change = 0

    def handle_event(self, event: pygame.event.EventType):
        if event.type == locals.MOUSEBUTTONDOWN:
            x, y = event.pos
            if self.right_player_input_rect.collidepoint(x, y):
                self.right_player_input.focused = True
                self.focused = self.focus_chain.index(self.right_player_input)
            elif self.left_player_input_rect.collidepoint(x, y):
                self.left_player_input.focused = True
                self.focused = self.focus_chain.index(self.left_player_input)
            elif self.left_player_ai_checkbox.rect.collidepoint(x, y):
                self.left_player_ai_checkbox.focused = True
                self.left_player_ai_checkbox.toggle_checked()
                self.focused = self.focus_chain.index(self.left_player_ai_checkbox)
            elif self.right_player_ai_checkbox.rect.collidepoint(x, y):
                self.right_player_ai_checkbox.focused = True
                self.right_player_ai_checkbox.toggle_checked()
                self.focused = self.focus_chain.index(self.right_player_ai_checkbox)
            elif self.cancel_button.rect.collidepoint(x, y):
                self.cancel_button.focused = True
                self.focused = self.focus_chain.index(self.cancel_button)
                self.cancel_button.on_click()
            elif self.start_button.rect.collidepoint(x, y):
                self.start_button.focused = True
                self.focused = self.focus_chain.index(self.start_button)
                self.start_button.on_click()

        elif event.type == locals.KEYDOWN:
            if event.key == locals.K_TAB:
                current_time = time.monotonic() * 1000

                if current_time - self.last_focus_change > 500:
                    self.focused += 1
                    self.focused = self.focused % len(self.focus_chain)

                    for item in self.focus_chain:
                        item.focused = False

                    self.focus_chain[self.focused].focused = True
                    self.last_focus_change = current_time
            elif event.key == locals.K_SPACE:
                if self.focused >= 0 and isinstance(self.focus_chain[self.focused], CheckBox):
                    check_box: CheckBox = self.focus_chain[self.focused]
                    check_box.toggle_checked()

    def create_game(self):
        pass

    def return_to_start(self):
        pass

    def handle_events(self, events: List[pygame.event.EventType]):
        self.left_player_input.update(events)
        self.right_player_input.update(events)

    def draw(self, surface: pygame.Surface):
        surface.fill(WHITE, self.rect)
        surface.blit(self.left_player_text, self.left_player_text_rect)
        surface.blit(self.left_player_input.get_surface(), self.left_player_input_rect)
        surface.blit(self.right_player_text, self.right_player_text_rect)
        surface.blit(self.right_player_input.get_surface(), self.right_player_input_rect)

        pygame.draw.line(surface, BLACK, self.left_player_input_rect.bottomleft,
                         self.left_player_input_rect.bottomright, 1)
        pygame.draw.line(surface, BLACK, self.right_player_input_rect.bottomleft,
                         self.right_player_input_rect.bottomright, 1)

        self.right_player_ai_checkbox.render(surface)
        self.left_player_ai_checkbox.render(surface)
        mouse_x, mouse_y = pygame.mouse.get_pos()

        self.cancel_button.hovering = self.cancel_button.rect.collidepoint(mouse_x, mouse_y)
        self.cancel_button.render(surface)
        self.start_button.hovering = self.start_button.rect.collidepoint(mouse_x, mouse_y)
        self.start_button.render(surface)


# noinspection SpellCheckingInspection
class HighscoreRenderer(Renderer):
    def draw(self, surface: pygame.Surface):
        pass


class AboutRenderer(Renderer):
    def draw(self, surface: pygame.Surface):
        pass


class StartupGameRenderer(Renderer):
    menu_items: List[MenuItem]
    background_game: "RunningGameRenderer"

    def __init__(self, master: "PingPongRenderer") -> None:
        super().__init__(master)
        rect: locals.Rect = master.screen.get_clip()
        width = 300
        height = 200
        top = int(rect.centery - (height / 2))
        left = int(rect.centerx - (width / 2))
        self.rect = locals.Rect((left, top), (width, height))
        sub_rect = locals.Rect(0, 0, width, height)
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
        mouse_x, mouse_y = self.translate_event_position(mouse_x, mouse_y)

        for item in self.menu_items:
            item.hovering = item.rect.collidepoint(mouse_x, mouse_y)
            item.render(self.foreground_surface)

        surface.blit(self.background_surface, self.background_surface.get_clip())
        surface.blit(self.foreground_surface, self.rect)

    def translate_event_position(self, mouse_x, mouse_y):
        # translate mouse position from screen to subsurface
        mouse_x -= self.rect.left
        mouse_y -= self.rect.top
        return mouse_x, mouse_y

    def handle_event(self, event: pygame.event.EventType):
        if event.type == locals.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = self.translate_event_position(*event.pos)
            for item in self.menu_items:
                if item.rect.collidepoint(mouse_x, mouse_y):
                    item.on_click()

    def create_game(self):
        self.master.renderer = CreateGameRenderer(self.master)

    def create_new_game(self):
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
        info_area = locals.Rect(screen_rect.left, screen_rect.top, screen_rect.width, 50)
        game_area = locals.Rect(screen_rect.left, screen_rect.top + 50, screen_rect.width, screen_rect.height - 50)

        left_player_rect = locals.Rect((game_area.left, game_area.centery), bar_dimension)
        left_player = AiPlayer(left_player_rect, game_area, "Player 1", False)

        right_player_rect = locals.Rect((game_area.right - bar_dimension[0], game_area.centery), bar_dimension)
        right_player = AiPlayer(right_player_rect, game_area, "Player 2", True)

        left_player_texture = PlayerTexture(left_player, WHITE)
        right_player_texture = PlayerTexture(right_player, WHITE)

        ball = Ball(locals.Rect(game_area.center, (10, 5)), game_area, Vector2(), 5, 250)
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
    game_area: locals.Rect

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
            events = pygame.event.get()
            for event in events:
                if event.type == locals.QUIT:
                    pygame.quit()
                    exit()
                self.renderer.handle_event(event)
            self.renderer.handle_events(events)

            self.renderer = self.renderer.tick()
            self.renderer.draw(self.screen)

            pygame.display.update()
            time.sleep(self.time_between_loop)


if __name__ == '__main__':
    PingPongRenderer().start()
