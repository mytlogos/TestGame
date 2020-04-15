from abc import ABC
from datetime import datetime
from enum import Enum
from typing import Union, Optional

from pygame.rect import Rect

from vector2 import Vector2


class MovableUnit(ABC):
    rect: Rect
    boundary: Rect

    def __init__(self, rect: Rect, boundary: Rect) -> None:
        self.rect = rect
        self.boundary = boundary

    def move(self, x: float, y: float):
        self.rect.move_ip(x, y)
        self.check_boundary()

    def check_boundary(self):
        if self.rect.left < self.boundary.left:
            self.rect.left = self.boundary.left

        if self.rect.right > self.boundary.right:
            self.rect.right = self.boundary.right

        if self.rect.top < self.boundary.top:
            self.rect.top = self.boundary.top

        if self.rect.bottom > self.boundary.bottom:
            self.rect.bottom = self.boundary.bottom


class Ball(MovableUnit):
    rect: Rect
    direction: Vector2
    radius: int
    speed: int
    position: Vector2
    speedup_factor: float

    def __init__(self, rect: Rect, boundary: Rect, direction: Vector2, radius: int, speed: int) -> None:
        super().__init__(rect, boundary)
        self.radius = radius
        self.direction = direction
        self.speed = speed
        self.position = Vector2(rect.left, rect.top)
        self.speedup_factor = 0.1

    def move(self, x: int, y: int):
        self.rect.move_ip(x, y)

    def move_to_time(self, time_to_last_tick: float):
        distance_moved = time_to_last_tick * self.speed
        self.position += self.direction * distance_moved
        self.rect.x = int(self.position.x)
        self.rect.y = int(self.position.y)
        self.check_boundary()
        self.speed += self.speed * self.speedup_factor * time_to_last_tick


class Player(MovableUnit):
    rect: Rect
    name: str

    def __init__(self, rect: Rect, boundary: Rect, name: str) -> None:
        super().__init__(rect, boundary)
        self.name = name

    def move(self, x: float, y: float):
        super(Player, self).move(0, y - self.rect.y)


lines = []


class AiPlayer(Player):
    game: "Game"
    speed: int
    right_side: bool
    speedup_factor: float

    def __init__(self, rect: Rect, boundary: Rect, name: str, right_side: bool) -> None:
        super().__init__(rect, boundary, name)
        self.speed = 300
        self.right_side = right_side
        self.speedup_factor = 0.09

    def move(self, x: float, y: float):
        ball_direction = self.game.ball.direction

        if ball_direction.x <= 0 and self.right_side:
            return
        elif not ball_direction.x <= 0 and not self.right_side:
            return

        if self.right_side:
            ticks = (self.game.screen_rect.right - self.game.ball.rect.right) // ball_direction.x
        else:
            ticks = (self.game.screen_rect.left - self.game.ball.rect.left) // ball_direction.x
        y = ticks * ball_direction.y + self.game.ball.rect.centery

        if y < self.rect.centery:
            direction = -1
        elif y > self.rect.centery:
            direction = 1
        else:
            direction = 0

        distance_moved = self.game.time_to_last_tick * self.speed
        moved = int(direction * distance_moved)
        super(Player, self).move(0, moved)
        self.speed += self.speed * self.speedup_factor * self.game.time_to_last_tick


class GameState(Enum):
    BEFORE_START = 0
    WAIT_TO_START = 1
    RUNNING = 2
    FINISHED = 3


class GameManager:
    pass


class Game:
    game_state: GameState
    ball: Ball
    left_player: Player
    right_player: Player
    screen_rect: Rect
    time_to_last_tick: float
    started_at: Optional[datetime]

    def __init__(self, ball: Ball, left_player: Player, right_player: Player, board_rect: Rect) -> None:
        self.screen_rect = board_rect
        self.right_player = right_player
        self.left_player = left_player
        self.ball = ball
        self.game_state = GameState.WAIT_TO_START
        self.time_to_last_tick = 0

    def start(self) -> None:
        destination = Vector2(self.left_player.rect.center) - (Vector2(5, 5) / 2)
        heading = Vector2.from_points(self.screen_rect.center, destination)
        heading.normalize()
        self.ball.direction = heading
        self.game_state = GameState.RUNNING
        self.started_at = datetime.now()

    def is_running(self):
        return self.game_state == GameState.RUNNING

    def before_running(self):
        return self.game_state != GameState.RUNNING and self.game_state != GameState.FINISHED

    def is_finished(self):
        return self.game_state == GameState.FINISHED

    def tick(self, left_player_pos: float, right_player_pos: float) -> None:
        if self.game_state != GameState.RUNNING:
            print("cannot tick when not running")
            return

        # handle collision of ball with other objects
        self.handle_bar_ball_collision(self.left_player.rect, self.ball)
        self.handle_bar_ball_collision(self.right_player.rect, self.ball)
        game_result = self.handle_wall_ball_collision(self.screen_rect, self.ball)

        if game_result is not None:
            self.game_state = GameState.FINISHED
        else:
            # move player bars
            self.left_player.move(0, left_player_pos)
            self.right_player.move(0, right_player_pos)

            # calculate the next position for the ball
            self.ball.move_to_time(self.time_to_last_tick)

    @staticmethod
    def handle_bar_ball_collision(bar_rect: Rect, ball: Ball):
        if bar_rect.top < ball.rect.bottom and bar_rect.bottom > ball.rect.top:
            # check if it should have collided with bar,
            # instead of 'warping' through and hitting behind it
            # for the right bar:
            if bar_rect.left:
                if ball.rect.right >= bar_rect.left:
                    if ball.direction.x > 0:
                        ball.direction.x = -ball.direction.x
                    ball.rect.right = bar_rect.left
                    return
            else:
                # for the left bar:
                if ball.rect.left <= bar_rect.right:
                    if ball.direction.x < 0:
                        ball.direction.x = -ball.direction.x
                    ball.rect.left = bar_rect.right
                    return

    def handle_object_ball_collision(self, rect: Rect, ball: Ball, x_bound, y_bound):
        if not rect.colliderect(ball.rect):
            return
        top_collision = abs(rect.top - ball.rect.bottom)
        bottom_collision = abs(rect.bottom - ball.rect.top)
        right_collision = abs(rect.right - ball.rect.left)
        left_collision = abs(rect.left - ball.rect.right)
        actual_side_collision = min([top_collision, bottom_collision, right_collision, left_collision])

        if actual_side_collision == right_collision:
            if ball.direction.x < 0:
                ball.direction.x = -ball.direction.x
            ball.move(rect.right + x_bound - ball.rect.x, 0)
        elif actual_side_collision == bottom_collision:
            if ball.direction.y < 0:
                ball.direction.y = -ball.direction.y
            ball.move(0, rect.bottom + y_bound - ball.rect.y)
        elif actual_side_collision == left_collision:
            if ball.direction.x > 0:
                ball.direction.x = -ball.direction.x
            ball.move(rect.left - ball.rect.width - ball.rect.x, 0)
        elif actual_side_collision == top_collision:
            if ball.direction.y > 0:
                ball.direction.y = -ball.direction.y
            ball.move(0, rect.top + y_bound - ball.rect.y)

        print("i am colliding: {} with {}, direction: {}".format(rect, self.ball.rect, self.ball.direction))

    def handle_wall_ball_collision(self, rect: Rect, ball: Ball) -> Union[bool, None]:
        # If the image goes off the end of the screen, move it back
        self.handle_wall_top_collision(rect, ball)
        self.handle_wall_bottom_collision(rect, ball)
        left_collided = self.handle_wall_left_collision(rect, ball)
        right_collided = self.handle_wall_right_collision(rect, ball)

        if left_collided:
            return False
        elif right_collided:
            return True
        else:
            return None

    @staticmethod
    def handle_wall_top_collision(rect: Rect, ball: Ball) -> bool:
        if ball.rect.top <= rect.top:
            if ball.direction.y < 0:
                ball.direction.y = -ball.direction.y
            ball.rect.top = rect.top
            return True
        return False

    @staticmethod
    def handle_wall_left_collision(rect: Rect, ball: Ball) -> bool:
        if ball.rect.left <= rect.left:
            if ball.direction.x < 0:
                ball.direction.x = -ball.direction.x
            ball.rect.left = rect.left
            return True
        return False

    @staticmethod
    def handle_wall_bottom_collision(rect: Rect, ball: Ball) -> bool:
        if ball.rect.bottom >= rect.bottom:
            if ball.direction.y > 0:
                ball.direction.y = -ball.direction.y
            ball.rect.bottom = rect.bottom
            return True
        return False

    @staticmethod
    def handle_wall_right_collision(rect: Rect, ball: Ball) -> bool:
        if ball.rect.right >= rect.right:
            if ball.direction.x > 0:
                ball.direction.x = -ball.direction.x
            ball.rect.right = rect.right
            return True
        return False
