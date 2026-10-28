"""A small desktop Snake game built with pygame."""

import argparse
import math
import random
from typing import List, Optional, Tuple

import pygame


WINDOW_WIDTH = 640
WINDOW_HEIGHT = 660
CELL_SIZE = 24
BOARD_COLUMNS = 24
BOARD_ROWS = 21
BOARD_X = (WINDOW_WIDTH - BOARD_COLUMNS * CELL_SIZE) // 2
BOARD_Y = 64
BOARD_WIDTH = BOARD_COLUMNS * CELL_SIZE
BOARD_HEIGHT = BOARD_ROWS * CELL_SIZE

UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

INITIAL_MOVE_INTERVAL = 0.22
MIN_MOVE_INTERVAL = 0.12
MAX_FRUITS = 2
FRUIT_SCORE = 10

BG_TOP = (6, 14, 27)
BG_BOTTOM = (10, 31, 31)
PANEL = (16, 34, 44)
PANEL_EDGE = (43, 76, 80)
BOARD_TOP = (19, 40, 51)
BOARD_BOTTOM = (9, 23, 33)
GRID_COLOR = (50, 76, 82)
TEXT_COLOR = (236, 247, 242)
MUTED_TEXT = (133, 166, 165)
SNAKE_HEAD_TOP = (190, 255, 208)
SNAKE_HEAD_BOTTOM = (48, 212, 144)
SNAKE_BODY_TOP = (115, 244, 174)
SNAKE_BODY_BOTTOM = (30, 158, 110)
SNAKE_TAIL = (20, 116, 86)
SNAKE_EDGE = (13, 83, 62)
FOOD_COLOR = (255, 83, 101)
FOOD_DARK = (154, 31, 64)
FOOD_HIGHLIGHT = (255, 187, 151)
LEAF_COLOR = (91, 211, 126)
OVERLAY_COLOR = (3, 9, 15, 210)

Color = Tuple[int, int, int]


def _vertical_gradient(
    size: Tuple[int, int],
    top_color: Color,
    bottom_color: Color,
) -> pygame.Surface:
    """Create a cached vertical gradient surface."""
    width, height = size
    surface = pygame.Surface(size)
    denominator = max(1, height - 1)
    for y in range(height):
        ratio = y / denominator
        color = tuple(
            round(top_color[channel] * (1 - ratio) + bottom_color[channel] * ratio)
            for channel in range(3)
        )
        pygame.draw.line(surface, color, (0, y), (width, y))
    return surface


def _rounded_gradient(
    size: Tuple[int, int],
    top_color: Color,
    bottom_color: Color,
    radius: int,
) -> pygame.Surface:
    """Create a gradient with transparent rounded corners."""
    surface = _vertical_gradient(size, top_color, bottom_color).convert_alpha()
    mask = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.rect(
        mask,
        (255, 255, 255, 255),
        mask.get_rect(),
        border_radius=radius,
    )
    surface.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return surface


def _radial_glow(
    size: int,
    color: Color,
    max_alpha: int = 70,
) -> pygame.Surface:
    """Create a soft circular glow for the snake head."""
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    center = size // 2
    for radius in range(center, 1, -2):
        strength = 1 - radius / center
        alpha = max(1, int(max_alpha * strength * strength))
        pygame.draw.circle(surface, (*color, alpha), (center, center), radius)
    return surface


class SnakeGame:
    """Owns the game state and renders one Snake game session."""

    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.board = pygame.Rect(BOARD_X, BOARD_Y, BOARD_WIDTH, BOARD_HEIGHT)
        self.title_font = pygame.font.SysFont("segoeui", 38, bold=True)
        self.subtitle_font = pygame.font.SysFont("segoeui", 12, bold=True)
        self.score_font = pygame.font.SysFont("segoeui", 24, bold=True)
        self.label_font = pygame.font.SysFont("segoeui", 12, bold=True)
        self.footer_font = pygame.font.SysFont("segoeui", 15)
        self.large_font = pygame.font.SysFont("segoeui", 54, bold=True)
        self.message_font = pygame.font.SysFont("segoeui", 22, bold=True)
        self.hint_font = pygame.font.SysFont("segoeui", 16)
        self.clock = pygame.time.Clock()
        self.running = True
        self.background = self._build_background()
        self.board_surface = self._build_board_surface()
        self.head_surface = _rounded_gradient(
            (22, 22),
            SNAKE_HEAD_TOP,
            SNAKE_HEAD_BOTTOM,
            7,
        )
        self.body_surface = _rounded_gradient(
            (20, 20),
            SNAKE_BODY_TOP,
            SNAKE_BODY_BOTTOM,
            6,
        )
        self.tail_surface = _rounded_gradient(
            (16, 16),
            SNAKE_BODY_TOP,
            SNAKE_TAIL,
            5,
        )
        self.head_glow = _radial_glow(38, (54, 255, 173), 82)
        self.dialog_surface = _rounded_gradient(
            (370, 218),
            (30, 58, 63),
            (13, 30, 39),
            20,
        )
        self.reset()

    def reset(self) -> None:
        """Start a fresh game or restart after a game over."""
        center_x = BOARD_COLUMNS // 2
        center_y = BOARD_ROWS // 2
        self.snake: List[Tuple[int, int]] = [
            (center_x, center_y),
            (center_x - 1, center_y),
            (center_x - 2, center_y),
        ]
        self.direction = RIGHT
        self.next_direction = RIGHT
        self.score = 0
        self.game_over = False
        self.paused = False
        self.elapsed = 0.0
        self.move_interval = INITIAL_MOVE_INTERVAL
        self.foods: List[Tuple[int, int]] = []
        self._replenish_food()

    def _new_food_position(self) -> Optional[Tuple[int, int]]:
        free_cells = [
            (column, row)
            for row in range(BOARD_ROWS)
            for column in range(BOARD_COLUMNS)
            if (column, row) not in self.snake
            and (column, row) not in self.foods
        ]
        if not free_cells:
            return None
        return random.choice(free_cells)

    def _replenish_food(self) -> None:
        """Keep red fruit plentiful without placing two berries in one cell."""
        while len(self.foods) < MAX_FRUITS:
            position = self._new_food_position()
            if position is None:
                return
            self.foods.append(position)

    def _build_background(self) -> pygame.Surface:
        surface = _vertical_gradient(
            (WINDOW_WIDTH, WINDOW_HEIGHT),
            BG_TOP,
            BG_BOTTOM,
        ).convert()

        glow = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(glow, (29, 164, 126, 16), (88, 86), 250)
        pygame.draw.circle(glow, (40, 112, 173, 12), (584, 460), 270)
        pygame.draw.circle(glow, (255, 93, 114, 8), (560, 90), 130)

        stars = random.Random(18)
        for _ in range(34):
            point = (stars.randrange(WINDOW_WIDTH), stars.randrange(WINDOW_HEIGHT))
            radius = stars.choice((1, 1, 1, 2))
            alpha = stars.randrange(14, 42)
            pygame.draw.circle(glow, (217, 255, 239, alpha), point, radius)

        surface.blit(glow, (0, 0))
        return surface

    def _build_board_surface(self) -> pygame.Surface:
        surface = _rounded_gradient(
            (BOARD_WIDTH, BOARD_HEIGHT),
            BOARD_TOP,
            BOARD_BOTTOM,
            12,
        )
        grid = pygame.Surface((BOARD_WIDTH, BOARD_HEIGHT), pygame.SRCALPHA)

        for column in range(1, BOARD_COLUMNS):
            x = column * CELL_SIZE
            pygame.draw.line(
                grid,
                (*GRID_COLOR, 18),
                (x, 0),
                (x, BOARD_HEIGHT),
            )
        for row in range(1, BOARD_ROWS):
            y = row * CELL_SIZE
            pygame.draw.line(
                grid,
                (*GRID_COLOR, 18),
                (0, y),
                (BOARD_WIDTH, y),
            )
        for row in range(BOARD_ROWS):
            for column in range(BOARD_COLUMNS):
                center = (
                    column * CELL_SIZE + CELL_SIZE // 2,
                    row * CELL_SIZE + CELL_SIZE // 2,
                )
                pygame.draw.circle(grid, (177, 229, 206, 10), center, 1)

        surface.blit(grid, (0, 0))
        return surface

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                continue

            if event.type != pygame.KEYDOWN:
                continue

            if event.key == pygame.K_ESCAPE:
                self.running = False
            elif self.game_over:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_r):
                    self.reset()
            elif event.key == pygame.K_SPACE:
                self.paused = not self.paused
            elif self.paused:
                continue
            elif event.key in (pygame.K_UP, pygame.K_w):
                self._queue_direction(UP)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._queue_direction(DOWN)
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self._queue_direction(LEFT)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self._queue_direction(RIGHT)

    def _queue_direction(self, new_direction: Tuple[int, int]) -> None:
        committed_opposite = (-self.direction[0], -self.direction[1])
        queued_opposite = (-self.next_direction[0], -self.next_direction[1])
        if (
            new_direction != committed_opposite
            and new_direction != queued_opposite
        ):
            self.next_direction = new_direction

    def _step(self) -> None:
        self.direction = self.next_direction
        head_x, head_y = self.snake[0]
        direction_x, direction_y = self.direction
        new_head = (head_x + direction_x, head_y + direction_y)

        hit_wall = not (
            0 <= new_head[0] < BOARD_COLUMNS
            and 0 <= new_head[1] < BOARD_ROWS
        )

        if hit_wall:
            self.game_over = True
            return

        ate_food = new_head in self.foods
        self.snake.insert(0, new_head)
        if ate_food:
            self.foods.remove(new_head)
            self.score += FRUIT_SCORE
            self.move_interval = max(
                MIN_MOVE_INTERVAL,
                INITIAL_MOVE_INTERVAL - self.score * 0.00055,
            )
        else:
            self.snake.pop()
        self._replenish_food()

    def _draw_text(
        self,
        text: str,
        font: pygame.font.Font,
        color: Tuple[int, int, int],
        center: Tuple[int, int],
    ) -> None:
        surface = font.render(text, True, color)
        rect = surface.get_rect(center=center)
        shadow = font.render(text, True, (2, 8, 11))
        self.screen.blit(shadow, rect.move(1, 2))
        self.screen.blit(surface, rect)

    def _draw_metric_card(
        self,
        rect: pygame.Rect,
        label: str,
        value: str,
        accent: Color,
    ) -> None:
        pygame.draw.rect(
            self.screen,
            (4, 12, 17),
            rect.move(0, 3),
            border_radius=12,
        )
        pygame.draw.rect(self.screen, PANEL, rect, border_radius=12)
        pygame.draw.rect(
            self.screen,
            PANEL_EDGE,
            rect,
            width=1,
            border_radius=12,
        )
        pygame.draw.rect(
            self.screen,
            accent,
            (rect.x + 10, rect.y + 10, 3, 20),
            border_radius=2,
        )

        label_surface = self.label_font.render(label, True, MUTED_TEXT)
        label_rect = label_surface.get_rect(
            midleft=(rect.x + 20, rect.centery)
        )
        self.screen.blit(label_surface, label_rect)

        value_surface = self.score_font.render(value, True, accent)
        value_rect = value_surface.get_rect(
            midright=(rect.right - 11, rect.centery)
        )
        self.screen.blit(value_surface, value_rect)

    def _draw_header(self) -> None:
        title_shadow = self.title_font.render("SNAKE", True, (2, 9, 13))
        title = self.title_font.render("SNAKE", True, TEXT_COLOR)
        self.screen.blit(title_shadow, (BOARD_X + 1, 9))
        self.screen.blit(title, (BOARD_X, 7))

        subtitle = self.subtitle_font.render(
            "NEON GARDEN",
            True,
            SNAKE_BODY_TOP,
        )
        self.screen.blit(subtitle, (BOARD_X + 2, 45))

        right_edge = BOARD_X + BOARD_WIDTH
        speed_rect = pygame.Rect(right_edge - 116, 11, 116, 41)
        score_rect = pygame.Rect(speed_rect.x - 128, 11, 116, 41)
        speed_ratio = INITIAL_MOVE_INTERVAL / self.move_interval
        self._draw_metric_card(
            score_rect,
            "SCORE",
            f"{self.score:03d}",
            SNAKE_BODY_TOP,
        )
        self._draw_metric_card(
            speed_rect,
            "SPEED",
            f"{speed_ratio:.1f}x",
            FOOD_HIGHLIGHT,
        )

    def _draw_board(self) -> None:
        pygame.draw.rect(
            self.screen,
            (2, 8, 12),
            self.board.move(0, 7),
            border_radius=16,
        )
        pygame.draw.rect(
            self.screen,
            (42, 91, 86),
            self.board.inflate(4, 4),
            width=1,
            border_radius=14,
        )
        self.screen.blit(self.board_surface, self.board.topleft)
        pygame.draw.rect(
            self.screen,
            (50, 91, 91),
            self.board,
            width=1,
            border_radius=12,
        )
        pygame.draw.line(
            self.screen,
            (89, 139, 126),
            (self.board.left + 18, self.board.top + 1),
            (self.board.right - 18, self.board.top + 1),
        )

    def _cell_center(self, cell: Tuple[int, int]) -> Tuple[int, int]:
        column, row = cell
        return (
            BOARD_X + column * CELL_SIZE + CELL_SIZE // 2,
            BOARD_Y + row * CELL_SIZE + CELL_SIZE // 2,
        )

    def _draw_food(self) -> None:
        for index, fruit in enumerate(self.foods):
            self._draw_fruit(self._cell_center(fruit), index * 1.7)

    def _draw_fruit(
        self,
        center: Tuple[int, int],
        phase: float,
    ) -> None:
        ticks = pygame.time.get_ticks() / 1000.0
        bob = round(math.sin(ticks * 2.8 + phase) * 1.5)
        fruit_center = (center[0], center[1] + bob)
        pulse = (math.sin(ticks * 3.2 + phase) + 1) / 2

        halo = pygame.Surface((38, 38), pygame.SRCALPHA)
        for radius in (18, 14, 10):
            pygame.draw.circle(
                halo,
                (255, 77, 102, int(8 + pulse * 9)),
                (19, 19),
                radius - round(pulse),
            )
        self.screen.blit(
            halo,
            (fruit_center[0] - 19, fruit_center[1] - 19),
        )

        pygame.draw.ellipse(
            self.screen,
            (4, 17, 20),
            (
                fruit_center[0] - 7,
                fruit_center[1] + 7,
                16,
                6,
            ),
        )
        pygame.draw.circle(
            self.screen,
            FOOD_DARK,
            fruit_center,
            9,
        )
        pygame.draw.circle(
            self.screen,
            FOOD_COLOR,
            (fruit_center[0] - 1, fruit_center[1] - 1),
            8,
        )
        pygame.draw.circle(
            self.screen,
            FOOD_HIGHLIGHT,
            (fruit_center[0] - 3, fruit_center[1] - 3),
            3,
        )
        pygame.draw.circle(
            self.screen,
            (255, 239, 215),
            (fruit_center[0] - 4, fruit_center[1] - 4),
            1,
        )

        stem_top = (fruit_center[0], fruit_center[1] - 13)
        pygame.draw.line(
            self.screen,
            (48, 112, 67),
            (fruit_center[0], fruit_center[1] - 8),
            stem_top,
            2,
        )
        leaf = [
            stem_top,
            (stem_top[0] + 7, stem_top[1] - 3),
            (stem_top[0] + 8, stem_top[1] + 2),
            (fruit_center[0] + 1, fruit_center[1] - 9),
        ]
        pygame.draw.polygon(self.screen, LEAF_COLOR, leaf)

    def _draw_snake(self) -> None:
        centers = [self._cell_center(cell) for cell in self.snake]
        if len(centers) > 1:
            shadow_points = [(x + 2, y + 3) for x, y in centers]
            pygame.draw.lines(
                self.screen,
                (3, 12, 16),
                False,
                shadow_points,
                width=18,
            )
            pygame.draw.lines(
                self.screen,
                SNAKE_EDGE,
                False,
                centers,
                width=17,
            )
            pygame.draw.lines(
                self.screen,
                SNAKE_BODY_BOTTOM,
                False,
                centers,
                width=13,
            )

        for index in range(len(centers) - 1, -1, -1):
            center = centers[index]
            if index == 0:
                size = 22
                segment_surface = self.head_surface
                glow_rect = self.head_glow.get_rect(center=center)
                self.screen.blit(self.head_glow, glow_rect)
            elif index == len(centers) - 1:
                size = 16
                segment_surface = self.tail_surface
            else:
                size = 20
                segment_surface = self.body_surface

            shadow_rect = pygame.Rect(
                center[0] - size // 2 + 2,
                center[1] - size // 2 + 3,
                size,
                size,
            )
            pygame.draw.rect(
                self.screen,
                (3, 12, 16),
                shadow_rect,
                border_radius=7,
            )
            segment = pygame.Rect(
                center[0] - size // 2,
                center[1] - size // 2,
                size,
                size,
            )
            self.screen.blit(segment_surface, segment.topleft)
            pygame.draw.rect(
                self.screen,
                SNAKE_EDGE,
                segment,
                width=1,
                border_radius=7,
            )

            if index == 0:
                self._draw_head_eyes(segment)

    def _draw_head_eyes(self, head: pygame.Rect) -> None:
        if self.direction == RIGHT:
            offsets = ((15, 7), (15, 15))
        elif self.direction == LEFT:
            offsets = ((7, 7), (7, 15))
        elif self.direction == UP:
            offsets = ((7, 7), (15, 7))
        else:
            offsets = ((7, 15), (15, 15))

        for offset_x, offset_y in offsets:
            eye_center = (head.x + offset_x, head.y + offset_y)
            pygame.draw.circle(self.screen, (242, 255, 247), eye_center, 3)
            pygame.draw.circle(
                self.screen,
                (8, 42, 34),
                (
                    eye_center[0] + self.direction[0],
                    eye_center[1] + self.direction[1],
                ),
                1,
            )

    def _draw_footer(self) -> None:
        panel = pygame.Rect(
            BOARD_X + 10,
            WINDOW_HEIGHT - 70,
            BOARD_WIDTH - 20,
            38,
        )
        pygame.draw.rect(self.screen, (10, 25, 31), panel, border_radius=13)
        pygame.draw.rect(
            self.screen,
            (36, 69, 70),
            panel,
            width=1,
            border_radius=13,
        )
        text = self.footer_font.render(
            "ARROWS / WASD   MOVE       SPACE   PAUSE       ESC   QUIT",
            True,
            MUTED_TEXT,
        )
        rect = text.get_rect(center=panel.center)
        self.screen.blit(text, rect)

    def _draw_overlay_backdrop(self) -> None:
        overlay = pygame.Surface((BOARD_WIDTH, BOARD_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(
            overlay,
            OVERLAY_COLOR,
            overlay.get_rect(),
            border_radius=12,
        )
        self.screen.blit(overlay, (BOARD_X, BOARD_Y))

    def _draw_dialog(self) -> pygame.Rect:
        board_center_x = BOARD_X + BOARD_WIDTH // 2
        board_center_y = BOARD_Y + BOARD_HEIGHT // 2
        dialog = self.dialog_surface.get_rect(
            center=(board_center_x, board_center_y)
        )
        pygame.draw.rect(
            self.screen,
            (2, 8, 12),
            dialog.move(0, 9),
            border_radius=21,
        )
        self.screen.blit(self.dialog_surface, dialog)
        pygame.draw.rect(
            self.screen,
            (57, 106, 99),
            dialog,
            width=1,
            border_radius=20,
        )
        pygame.draw.line(
            self.screen,
            (96, 163, 139),
            (dialog.left + 24, dialog.top + 1),
            (dialog.right - 24, dialog.top + 1),
        )
        return dialog

    def _draw_paused(self) -> None:
        self._draw_overlay_backdrop()
        dialog = self._draw_dialog()
        center_x = dialog.centerx

        bar_y = dialog.top + 37
        pygame.draw.rect(
            self.screen,
            SNAKE_BODY_TOP,
            (center_x - 17, bar_y, 12, 42),
            border_radius=5,
        )
        pygame.draw.rect(
            self.screen,
            SNAKE_BODY_TOP,
            (center_x + 5, bar_y, 12, 42),
            border_radius=5,
        )
        self._draw_text(
            "PAUSED",
            self.large_font,
            TEXT_COLOR,
            (center_x, dialog.top + 119),
        )
        self._draw_text(
            "PRESS SPACE TO CONTINUE",
            self.message_font,
            FOOD_HIGHLIGHT,
            (center_x, dialog.top + 171),
        )

    def _draw_game_over(self) -> None:
        self._draw_overlay_backdrop()
        dialog = self._draw_dialog()
        center_x = dialog.centerx
        self._draw_text(
            "GAME OVER",
            self.large_font,
            FOOD_COLOR,
            (center_x, dialog.top + 58),
        )
        self._draw_text(
            f"FINAL SCORE  {self.score}",
            self.message_font,
            TEXT_COLOR,
            (center_x, dialog.top + 112),
        )
        self._draw_text(
            "PRESS ENTER / SPACE / R TO RESTART",
            self.hint_font,
            MUTED_TEXT,
            (center_x, dialog.top + 170),
        )

    def _draw(self) -> None:
        self.screen.blit(self.background, (0, 0))
        self._draw_header()
        self._draw_board()
        self._draw_food()
        self._draw_snake()
        self._draw_footer()
        if self.game_over:
            self._draw_game_over()
        elif self.paused:
            self._draw_paused()
        pygame.display.flip()

    def run(self, max_frames: Optional[int] = None) -> int:
        """Run the event loop and return after quitting or reaching max_frames."""
        frame_count = 0
        while self.running:
            delta_seconds = self.clock.tick(60) / 1000.0
            self._handle_events()

            if not self.game_over and not self.paused and self.running:
                self.elapsed += min(delta_seconds, 0.25)
                while self.elapsed >= self.move_interval:
                    self.elapsed -= self.move_interval
                    self._step()
                    if self.game_over:
                        break

            self._draw()
            frame_count += 1
            if max_frames is not None and frame_count >= max_frames:
                self.running = False

        return frame_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Play Snake with pygame.")
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pygame.init()
    try:
        screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Snake")
        game = SnakeGame(screen)
        frames = game.run(max_frames=5 if args.smoke_test else None)
        if args.smoke_test:
            print(
                f"Startup smoke test passed: display initialized and {frames} "
                "frames rendered."
            )
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
