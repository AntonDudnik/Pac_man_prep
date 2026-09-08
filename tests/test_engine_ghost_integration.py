"""Integration test for GameEngine and GhostManager wiring."""

from pacman.config import GameConfig
from pacman.engine import GameEngine
from pacman.entities import GhostMode, GhostType, Vector2D
from pacman.entities.state import GameState


def test_engine_updates_ghosts_and_wave_timer() -> None:
    # Initialize engine with standard config
    config = GameConfig()
    engine = GameEngine(config)
    engine.state = GameState.PLAYING

    # blinky = engine.ghosts[GhostType.BLINKY]

    # Advance engine loop
    engine.update(dt=0.5)

    # Verify wave timer advanced
    assert engine.ghost_manager.wave_timer.time_in_wave == 0.5


def test_ghost_collision_kills_player() -> None:
    config = GameConfig()
    engine = GameEngine(config)
    engine.state = GameState.PLAYING

    # Place Pac-Man and Blinky at identical grid coordinate
    engine.player.position = Vector2D(x=5.0, y=5.0)
    blinky = engine.ghosts[GhostType.BLINKY]
    blinky.position = Vector2D(x=5.0, y=5.0)
    blinky.mode = GhostMode.CHASE

    initial_lives = engine.player.lives

    engine.update(dt=0.01)

    # Player loses a life and positions reset
    assert engine.player.lives == initial_lives - 1
