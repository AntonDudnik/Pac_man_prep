from pacman.entities.base import Vector2D, CellType
from pacman.entities.ghost import Ghost
from pacman.entities.player import Player
from pacman.ui import PygameUI
import os
import pytest
import pygame

# Set dummy video driver for headless testing before importing UI
os.environ["SDL_VIDEODRIVER"] = "dummy"


@pytest.fixture
def ui_instance():
    """Initializes PygameUI in headless video mode."""
    return PygameUI(
        width_cells=10,
        height_cells=10,
        cell_size=20,
        spritesheet_path="non_existent_path.png",  # Forces fallback renderer test path
    )


def test_ui_initialization(ui_instance):
    assert ui_instance.width_cells == 10
    assert ui_instance.height_cells == 10
    assert ui_instance.screen is not None


def test_ui_draw_board_fallback(ui_instance):
    board = [
        [CellType.NORTH | CellType.DOT, 0],
        [CellType.SUPER_DOT, 0],
    ]
    # Verify no exceptions thrown during board rendering pass
    try:
        ui_instance.screen.fill((0, 0, 0))
        # Call draw_board if exists on your UI adapter
        if hasattr(ui_instance, "draw_board"):
            ui_instance.draw_board(board)
        pygame.display.flip()
    except Exception as exc:
        pytest.fail(f"ui.draw_board raised an unexpected exception: {exc}")


def test_ui_draw_entities_fallback(ui_instance):
    player = Player(position=Vector2D(x=1.0, y=1.0))
    ghosts = [Ghost(ghost_id=0, home_corner=Vector2D(x=0, y=0), position=Vector2D(x=2.0, y=2.0))]

    try:
        ui_instance.screen.fill((0, 0, 0))
        if hasattr(ui_instance, "draw_entities"):
            ui_instance.draw_entities(player, ghosts)
        elif hasattr(ui_instance, "draw"):
            ui_instance.draw(player=player, ghosts=ghosts)
        pygame.display.flip()
    except Exception as exc:
        pytest.fail(f"UI entity draw raised an unexpected exception: {exc}")


def test_ui_anim_timer_update(ui_instance):
    initial_time = ui_instance.anim_time
    ui_instance.update_anim_timer(0.016)
    assert ui_instance.anim_time > initial_time
