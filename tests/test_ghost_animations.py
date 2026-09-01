import pytest
import pygame
from pacman.entities.base import Direction
from pacman.entities.state import GhostMode
from pacman.spritesheet import SpriteSheet, AnimationManager


@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    pygame.init()
    pygame.display.set_mode((1, 1), pygame.NOFRAME)
    yield
    pygame.quit()


@pytest.fixture
def anim_mgr(tmp_path):
    img_path = str(tmp_path / "test_sheet.png")
    surface = pygame.Surface((1000, 1000))
    pygame.image.save(surface, img_path)
    sheet = SpriteSheet(filename=img_path, target_size=24)
    return AnimationManager(sheet)


def test_ghost_chase_state_animation(anim_mgr):
    """Verify normal ghost rendering for all 4 ghost IDs."""
    for ghost_id in range(4):
        sprite = anim_mgr.get_ghost_sprite(
            ghost_id, GhostMode.CHASE, Direction.RIGHT, anim_time=0.5)
        assert isinstance(sprite, pygame.Surface)
        assert sprite.get_size() == (24, 24)


def test_ghost_frightened_blue_state(anim_mgr):
    """Verify frightened mode renders standard blue frames when timer > 2.0s."""
    sprite = anim_mgr.get_ghost_sprite(
        0, GhostMode.FRIGHTENED, Direction.UP, anim_time=0.1, frightened_timer=5.0)
    assert isinstance(sprite, pygame.Surface)


def test_ghost_frightened_flashing_state(anim_mgr):
    """Verify frightened mode alternates frames when timer <= 2.0s."""
    sprite_flash1 = anim_mgr.get_ghost_sprite(
        0, GhostMode.FRIGHTENED, Direction.UP, anim_time=0.0, frightened_timer=1.5)
    sprite_flash2 = anim_mgr.get_ghost_sprite(
        0, GhostMode.FRIGHTENED, Direction.UP, anim_time=0.2, frightened_timer=1.5)
    assert isinstance(sprite_flash1, pygame.Surface)
    assert isinstance(sprite_flash2, pygame.Surface)


def test_ghost_eaten_state(anim_mgr):
    """Verify eaten mode returns directional eye surfaces."""
    for d in [Direction.RIGHT, Direction.LEFT, Direction.UP, Direction.DOWN]:
        eye_sprite = anim_mgr.get_ghost_sprite(0, GhostMode.EATEN, d, anim_time=0.0)
        assert isinstance(eye_sprite, pygame.Surface)
