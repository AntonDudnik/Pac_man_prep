import pytest
import pygame
from unittest.mock import patch

from pacman.engine import GameEngine, GameState
from pacman.config import GameConfig


@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    """Headless Pygame setup for test suite."""
    pygame.init()
    pygame.display.set_mode((1, 1), pygame.NOFRAME)
    yield
    pygame.quit()


@pytest.fixture
def dummy_config():
    return GameConfig(
        width=28,
        height=36,
        cell_size=24,
        lives=3,
        level_max_time=200,
        player_speed=5.0,
        ghost_speed=4.0,
        spritesheet_path="assets/spritesheet.png"
    )


@pytest.fixture
def engine_instance(dummy_config):
    with patch("pacman.engine.PygameUI"):
        return GameEngine(dummy_config)


def _send_key(engine: GameEngine, key: int) -> bool:
    """Helper to post a KEYDOWN event and return handle_events result."""
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))
    return engine.handle_events()


def test_menu_navigation_wraparound(engine_instance):
    """Verify UP/DOWN keys navigate menu and wrap around bounds correctly."""
    engine = engine_instance
    engine.state = GameState.MENU
    engine.menu_index = 0

    # Down arrow -> index 1
    _send_key(engine, pygame.K_DOWN)
    assert engine.menu_index == 1

    # Up arrow -> index 0
    _send_key(engine, pygame.K_UP)
    assert engine.menu_index == 0

    # Up arrow at top -> wraps around to last option (index 2)
    _send_key(engine, pygame.K_UP)
    assert engine.menu_index == 2


def test_quit_confirmation_flow(engine_instance):
    """Verify Q triggers confirmation modal and Y/N handles exit/resume."""
    engine = engine_instance
    engine.state = GameState.PLAYING

    # Press Q during gameplay -> Transition to CONFIRM_QUIT
    running = _send_key(engine, pygame.K_q)
    assert running is True
    assert engine.state == GameState.CONFIRM_QUIT

    # Press N to cancel -> Return to PLAYING
    running = _send_key(engine, pygame.K_n)
    assert running is True
    assert engine.state == GameState.PLAYING

    # Press ESC -> Open CONFIRM_QUIT again
    running = _send_key(engine, pygame.K_ESCAPE)
    assert running is True
    assert engine.state == GameState.CONFIRM_QUIT

    # Press Y -> Confirm exit (returns False to stop game loop)
    running = _send_key(engine, pygame.K_y)
    assert running is False
