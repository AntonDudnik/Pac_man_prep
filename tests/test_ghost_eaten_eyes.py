"""Unit tests for EATEN ghost eyes return navigation and revival."""

from pacman.ai.ghost_manager import GhostManager
from pacman.ai.targeting import GHOST_HOUSE_DOOR, GHOST_HOUSE_SPAWN, get_eaten_target_tile
from pacman.entities import Direction, GhostMode, GhostType, Vector2D
from pacman.entities.ghost import Ghost


def test_eaten_eyes_target_door_when_outside() -> None:
    outside_pos = Vector2D(x=1.0, y=1.0)
    target = get_eaten_target_tile(outside_pos)
    assert (target.x, target.y) == (GHOST_HOUSE_DOOR.x, GHOST_HOUSE_DOOR.y)


def test_eaten_eyes_target_spawn_when_at_door() -> None:
    at_door_pos = Vector2D(x=9.0, y=8.0)
    target = get_eaten_target_tile(at_door_pos)
    assert (target.x, target.y) == (GHOST_HOUSE_SPAWN.x, GHOST_HOUSE_SPAWN.y)


def test_eaten_eyes_revive_upon_reaching_spawn() -> None:
    blinky = Ghost(ghost_id=0, home_corner=Vector2D())
    blinky.mode = GhostMode.EATEN
    blinky.position = GHOST_HOUSE_SPAWN

    manager = GhostManager({GhostType.BLINKY: blinky})
    dummy_board = [[0] * 19 for _ in range(22)]

    manager._update_ghost_direction(
        ghost=blinky,
        ghost_type=GhostType.BLINKY,
        board=dummy_board,
        pacman_pos=Vector2D(),
        pacman_dir=Direction.NONE,
        blinky_pos=blinky.position,
    )

    assert blinky.mode == GhostMode.CHASE
    assert blinky.speed == 4.0
