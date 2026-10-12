"""Pure targeting vector functions for classic arcade Pac-Man ghost AI."""

from typing import Callable
from pacman.entities import Direction, Vector2D
from pacman.entities.ghost import Ghost

# Default entrance tile directly above the Ghost House gate
GHOST_HOUSE_DOOR = Vector2D(x=9.0, y=8.0)
GHOST_HOUSE_SPAWN = Vector2D(x=9.0, y=10.0)


def get_eaten_target_tile(ghost_pos: Vector2D) -> Vector2D:
    """Returns target for EATEN eyes: Door if outside, Spawn if at/inside door."""
    if abs(ghost_pos.x - GHOST_HOUSE_DOOR.x) < 1.0 and ghost_pos.y >= GHOST_HOUSE_DOOR.y:
        return GHOST_HOUSE_SPAWN
    return GHOST_HOUSE_DOOR


def get_target_tile(
    ghost: Ghost,
    pacman_pos: Vector2D,
    pacman_dir: Direction,
    blinky_pos: Vector2D,
) -> Vector2D:
    """Calculates the target grid cell by triggering the target algorithm of the
    specific ghost instance."""
    return ghost.get_target_tile(
        pacman_pos=pacman_pos,
        pacman_dir=pacman_dir,
        blinky_pos=blinky_pos,
    )


def get_next_intersection_direction(
    board: list[list[int]],
    grid_x: int,
    grid_y: int,
    current_dir: Direction,
    target_tile: Vector2D,
    can_move_fn: Callable,
) -> Direction:
    """Determines next direction at an intersection by finding the min Euclidean
    distance squared.

    Fixed priority tie-breaker rule: UP > LEFT > DOWN > RIGHT.
    Prevents 180-degree immediate reversals.
    """
    opposite_dir = {
        Direction.UP: Direction.DOWN,
        Direction.DOWN: Direction.UP,
        Direction.LEFT: Direction.RIGHT,
        Direction.RIGHT: Direction.LEFT,
        Direction.NONE: Direction.NONE,
    }[current_dir]

    # Arcade Priority Order
    candidate_dirs = [Direction.UP, Direction.LEFT, Direction.DOWN, Direction.RIGHT]

    best_dir = current_dir
    min_dist_sq = float("inf")

    for d in candidate_dirs:
        # Rule: Ghosts cannot reverse 180 degrees during standard navigation
        if d == opposite_dir and current_dir != Direction.NONE:
            continue

        if can_move_fn(board, grid_x, grid_y, d, is_ghost=True):
            nx = grid_x + d.dx
            ny = grid_y + d.dy

            # Squared Euclidean distance: (x1 - x2)^2 + (y1 - y2)^2
            dx = nx - target_tile.x
            dy = ny - target_tile.y
            dist_sq = dx * dx + dy * dy

            # Strictly less than ensures strict tie-breaking by candidate_dirs order
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                best_dir = d

    return best_dir
