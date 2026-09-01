import pytest
import pygame
from pacman.entities import Direction, GhostMode
from pacman.spritesheet import (
    SpriteSheet,
    AnimationManager,
    PALETTE_BLOCK_WIDTH,
    PALETTE_BLOCK_HEIGHT,
    FONT_STRIDE,
    ENTITY_STRIDE,
)


@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    """Ensure Pygame display mode is initialized headless for tests."""
    pygame.init()
    pygame.display.set_mode((1, 1), pygame.NOFRAME)
    yield
    pygame.quit()


@pytest.fixture
def mock_spritesheet(tmp_path):
    """Create a dummy PNG spritesheet to test loading and surface cutting."""
    img_path = str(tmp_path / "test_sheet.png")
    surface = pygame.Surface((1000, 1000))
    surface.fill((255, 0, 255))  # Fill pink
    pygame.image.save(surface, img_path)

    return SpriteSheet(filename=img_path, target_size=24)


def test_spritesheet_geometry_constants():
    """Verify geometry formulas compile accurately to calculated pixel dimensions."""
    expected_width = (22 * FONT_STRIDE) + 2    # 22 * 9 + 2 = 200px
    expected_height = (9 * FONT_STRIDE) + (6 * ENTITY_STRIDE) + 3  # 81 + 108 + 3 = 186px

    assert PALETTE_BLOCK_WIDTH == expected_width
    assert PALETTE_BLOCK_HEIGHT == expected_height


def test_get_entity_tile_dimensions_and_caching(mock_spritesheet):
    """Test that extracted tiles return exact target size and hit the cache."""
    tile1 = mock_spritesheet.get_entity_tile(col=0, row=0)
    assert tile1.get_width() == 24
    assert tile1.get_height() == 24

    # Second fetch should return identical cached surface reference
    tile2 = mock_spritesheet.get_entity_tile(col=0, row=0)
    assert tile1 is tile2


def test_animation_manager_frame_extraction(mock_spritesheet):
    """Verify AnimationManager loads all directional animation buffers without failing."""
    anim_mgr = AnimationManager(mock_spritesheet)

    # Check Pac-Man directions
    for direction in [Direction.RIGHT, Direction.LEFT, Direction.UP, Direction.DOWN]:
        sprite = anim_mgr.get_pacman_sprite(direction, anim_time=0.1)
        assert isinstance(sprite, pygame.Surface)
        assert sprite.get_size() == (24, 24)

    # Fetch standard mode attribute dynamically from GhostMode enum
    # (Falls back to first available non-FRIGHTENED/EATEN mode enum value)
    normal_ghost_mode = getattr(GhostMode, "CHASE", list(GhostMode)[0])

    # Check Ghosts (Normal, Frightened, Eaten)
    for ghost_id in range(4):
        ghost_sprite = anim_mgr.get_ghost_sprite(
            ghost_id, normal_ghost_mode, Direction.RIGHT, anim_time=0.0)
        assert isinstance(ghost_sprite, pygame.Surface)

    frightened_sprite = anim_mgr.get_ghost_sprite(
        0, GhostMode.FRIGHTENED, Direction.UP, anim_time=0.0)
    assert isinstance(frightened_sprite, pygame.Surface)

    eaten_sprite = anim_mgr.get_ghost_sprite(0, GhostMode.EATEN, Direction.LEFT, anim_time=0.0)
    assert isinstance(eaten_sprite, pygame.Surface)
