import pytest
from pacman.entities.base import (
    Direction,
    Vector2D,
    can_move,
    CellType
)
from pacman.entities.player import Player
from pacman.entities.ghost import Ghost
from pacman.entities.state import GhostMode, GhostType
from pacman.ai.ghost_manager import GhostManager


@pytest.fixture
def empty_3x3_board() -> list[list[int]]:
    """Generates a 3x3 open grid with no outer wall bitmasks."""
    return [
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0],
    ]


@pytest.fixture
def walled_board() -> list[list[int]]:
    """
    3x3 Grid layout for movement testing:
    Cell (1,1) is blocked on NORTH (1) and WEST (8).
    Cell (1,0) contains a GATE (128).
    """
    return [
        [0, CellType.GATE, 0],
        [0, CellType.NORTH | CellType.WEST, 0],
        [0, 0, 0],
    ]


# --- Vector2D & Direction Tests ---

def test_vector2d_grid_and_movement():
    v = Vector2D(x=1.8, y=2.2)
    assert v.to_grid() == (1, 2)

    moved = v.move_continuous(Direction.RIGHT, 0.5)
    assert pytest.approx(moved.x) == 2.3
    assert pytest.approx(moved.y) == 2.2


def test_direction_deltas():
    assert Direction.UP.dx == 0 and Direction.UP.dy == -1
    assert Direction.RIGHT.dx == 1 and Direction.RIGHT.dy == 0
    assert Direction.DOWN.dx == 0 and Direction.DOWN.dy == 1
    assert Direction.LEFT.dx == -1 and Direction.LEFT.dy == 0


# --- Collision (can_move) Tests ---

def test_can_move_wall_collisions(walled_board):
    # Cell (1,1) has NORTH and WEST walls
    assert not can_move(walled_board, 1, 1, Direction.UP)
    assert not can_move(walled_board, 1, 1, Direction.LEFT)
    assert can_move(walled_board, 1, 1, Direction.RIGHT)
    assert can_move(walled_board, 1, 1, Direction.DOWN)


def test_can_move_gate_permissions(walled_board):
    # Cell (1,0) is a GATE tile
    # Player cannot move UP/DOWN through GATE
    assert not can_move(walled_board, 1, 0, Direction.UP, is_ghost=False)
    assert not can_move(walled_board, 1, 0, Direction.DOWN, is_ghost=False)

    # Ghost CAN move through GATE
    assert can_move(walled_board, 1, 0, Direction.UP, is_ghost=True)


def test_can_move_out_of_bounds(empty_3x3_board):
    assert not can_move(empty_3x3_board, -1, 0, Direction.LEFT)
    assert not can_move(empty_3x3_board, 0, 3, Direction.DOWN)


# --- BaseEntity & Player Tests ---

def test_player_initialization():
    player = Player(position=Vector2D(x=1.0, y=1.0), speed=5.0, lives=3)
    assert player.grid_x == 1
    assert player.grid_y == 1
    assert player.lives == 3


def test_player_movement_and_turn(empty_3x3_board):
    player = Player(position=Vector2D(x=1.0, y=1.0), speed=1.0)
    player.next_direction = Direction.RIGHT

    # Process frame step
    player.update(empty_3x3_board, dt=0.1)

    assert player.direction == Direction.RIGHT
    assert player.position.x > 1.0


def test_player_stops_at_wall(walled_board):
    # Player facing NORTH at (1,1) where NORTH has a wall flag
    player = Player(position=Vector2D(x=1.0, y=1.0))
    player.direction = Direction.UP
    player.next_direction = Direction.UP

    player.update(walled_board, dt=0.1)

    assert player.direction == Direction.NONE
    assert player.position.x == 1.0
    assert player.position.y == 1.0


# --- Ghost Tests ---

def test_ghost_initialization():
    home = Vector2D(x=0.0, y=0.0)
    ghost = Ghost(ghost_id=0, home_corner=home, position=Vector2D(x=1.0, y=1.0))

    assert ghost.id == 0
    assert ghost.mode == GhostMode.CHASE
    assert ghost.home_corner == home


def test_ghost_frightened_timer_expiry(empty_3x3_board) -> None:
    ghost = Ghost(ghost_id=1, home_corner=Vector2D(x=0.0, y=0.0))
    ghost.mode = GhostMode.FRIGHTENED
    ghost.frightened_timer = 2.0

    manager = GhostManager({GhostType.PINKY: ghost})

    # Pass 1 second
    manager.update(
        board=empty_3x3_board,
        dt=1.0,
        pacman_pos=Vector2D(x=0.0, y=0.0),
        pacman_dir=Direction.NONE,
    )
    assert ghost.mode == GhostMode.FRIGHTENED
    assert pytest.approx(ghost.frightened_timer) == 1.0

    # Pass another 1.5 seconds -> Expiry back to active wave mode (CHASE/SCATTER)
    manager.update(
        board=empty_3x3_board,
        dt=1.5,
        pacman_pos=Vector2D(x=0.0, y=0.0),
        pacman_dir=Direction.NONE,
    )
    assert ghost.mode != GhostMode.FRIGHTENED
    assert ghost.frightened_timer == 0.0


def test_ghost_frozen_state(empty_3x3_board) -> None:
    ghost = Ghost(ghost_id=0, home_corner=Vector2D(x=0.0, y=0.0), position=Vector2D(x=1.0, y=1.0))
    ghost.direction = Direction.RIGHT

    manager = GhostManager({GhostType.BLINKY: ghost})

    # Frozen state passed to manager should block position/movement updates
    manager.update(
        board=empty_3x3_board,
        dt=0.1,
        pacman_pos=Vector2D(x=0.0, y=0.0),
        pacman_dir=Direction.NONE,
        frozen=True,
    )
    assert ghost.position.x == 1.0
    assert ghost.position.y == 1.0
