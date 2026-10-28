"""Behavior checks for the Snake game."""

import os
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame

import main


class SnakeGameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def setUp(self) -> None:
        pygame.event.clear()
        screen = pygame.display.set_mode(
            (main.WINDOW_WIDTH, main.WINDOW_HEIGHT)
        )
        self.game = main.SnakeGame(screen)

    def test_speed_starts_slow_and_has_a_safe_floor(self) -> None:
        self.assertAlmostEqual(
            self.game.move_interval,
            main.INITIAL_MOVE_INTERVAL,
        )

        self.game.snake = [(5, 5), (4, 5), (3, 5)]
        self.game.direction = main.RIGHT
        self.game.next_direction = main.RIGHT
        self.game.foods = [(6, 5), (10, 10)]
        self.game._step()

        self.assertLess(
            self.game.move_interval,
            main.INITIAL_MOVE_INTERVAL,
        )
        self.assertGreaterEqual(
            self.game.move_interval,
            main.MIN_MOVE_INTERVAL,
        )

        self.game.score = 200
        self.game.snake = [(5, 5), (4, 5), (3, 5)]
        self.game.direction = main.RIGHT
        self.game.next_direction = main.RIGHT
        self.game.foods = [(6, 5), (10, 10)]
        self.game._step()
        self.assertEqual(
            self.game.move_interval,
            main.MIN_MOVE_INTERVAL,
        )

    def test_red_fruit_supply_is_replenished(self) -> None:
        self.assertEqual(len(self.game.foods), main.MAX_FRUITS)
        old_fruits = set(self.game.foods)

        target = self.game.foods[0]
        self.game.snake = [
            (target[0] - 1, target[1]),
            (target[0] - 2, target[1]),
            (target[0] - 3, target[1]),
        ]
        self.game.direction = main.RIGHT
        self.game.next_direction = main.RIGHT
        self.game._step()

        self.assertEqual(self.game.score, main.FRUIT_SCORE)
        self.assertEqual(len(self.game.foods), main.MAX_FRUITS)
        self.assertNotIn(target, self.game.foods)
        self.assertTrue(old_fruits & set(self.game.foods))

    def test_space_pauses_and_resumes_without_moving(self) -> None:
        pygame.event.post(
            pygame.event.Event(
                pygame.KEYDOWN,
                key=pygame.K_SPACE,
            )
        )
        self.game._handle_events()
        self.assertTrue(self.game.paused)

        snake_before_pause = list(self.game.snake)
        self.game.elapsed = self.game.move_interval
        self.game.run(max_frames=4)
        self.assertEqual(self.game.snake, snake_before_pause)

        self.game.running = True
        pygame.event.post(
            pygame.event.Event(
                pygame.KEYDOWN,
                key=pygame.K_SPACE,
            )
        )
        self.game._handle_events()
        self.assertFalse(self.game.paused)

    def test_entering_own_body_does_not_end_the_game(self) -> None:
        self.game.snake = [
            (2, 2),
            (2, 3),
            (1, 3),
            (1, 2),
            (1, 1),
        ]
        self.game.direction = main.DOWN
        self.game.next_direction = main.DOWN
        self.game.foods = [(10, 10), (11, 10)]

        self.game._step()

        self.assertFalse(self.game.game_over)
        self.assertEqual(self.game.snake[0], (2, 3))

    def test_wall_collision_ends_the_game(self) -> None:
        self.game.snake = [(0, 0), (1, 0), (2, 0)]
        self.game.direction = main.LEFT
        self.game.next_direction = main.LEFT

        self.game._step()

        self.assertTrue(self.game.game_over)

    def test_pause_overlay_renders(self) -> None:
        self.game.paused = True
        self.game._draw()
        self.assertFalse(self.game.game_over)


if __name__ == "__main__":
    unittest.main()
