"""Unit tests for Super Pac-gum activation and progressive ghost scoring."""

from pacman.config import GameConfig
from pacman.engine import GameEngine
from pacman.entities import GhostMode, GhostType, Vector2D
from pacman.entities.base import CellType


def test_super_dot_triggers_frightened_mode() -> None:
    engine = GameEngine(GameConfig())
    engine.state = engine.state.PLAYING

    px, py = engine.player.grid_x, engine.player.grid_y
    # Place a SUPER_DOT directly beneath Pac-Man
    engine.board[py][px] |= CellType.SUPER_DOT

    engine._check_tile_consumption()

    # Check score increased by 50 and ghosts entered FRIGHTENED
    assert engine.score == 50
    assert engine.ghosts[GhostType.BLINKY].mode == GhostMode.FRIGHTENED


def test_progressive_ghost_eating_score() -> None:
    engine = GameEngine(GameConfig())
    engine.ghost_manager.trigger_frightened(duration=7.0)

    ghosts = list(engine.ghosts.values())
    expected_scores = [200, 400, 800, 1600]

    for idx, expected_points in enumerate(expected_scores):
        ghost = ghosts[idx]

        # Align position with player
        engine.player.position = Vector2D(x=5.0, y=5.0)
        ghost.position = Vector2D(x=5.0, y=5.0)

        initial_score = engine.score
        engine._check_ghost_collisions()

        assert ghost.mode == GhostMode.EATEN
        assert engine.score == initial_score + expected_points
