"""Pure targeting vector functions for classic arcade Pac-Man ghost AI."""

from pacman.entities import Direction, GhostType, Vector2D

# Classic Arcade Fixed Scatter Corners (19x22 or scaled grid equivalents)
# Adjust these coordinates to match your specific grid boundary corners
DEFAULT_SCATTER_CORNERS: dict[GhostType, Vector2D] = {
    GhostType.BLINKY: Vector2D(x=17.0, y=-2.0),  # Top-Right
    GhostType.PINKY: Vector2D(x=1.0, y=-2.0),    # Top-Left
    GhostType.INKY: Vector2D(x=18.0, y=21.0),   # Bottom-Right
    GhostType.CLYDE: Vector2D(x=0.0, y=21.0),    # Bottom-Left
}

# Default entrance tile directly above the Ghost House gate
GHOST_HOUSE_DOOR = Vector2D(x=9.0, y=8.0)
GHOST_HOUSE_SPAWN = Vector2D(x=9.0, y=10.0)


def get_eaten_target_tile(ghost_pos: Vector2D) -> Vector2D:
    """Returns target for EATEN eyes: Door if outside, Spawn if at/inside door."""
    # If the ghost has arrived at or passed through the door (y >= door y and close in x)
    if abs(ghost_pos.x - GHOST_HOUSE_DOOR.x) < 1.0 and ghost_pos.y >= GHOST_HOUSE_DOOR.y:
        return GHOST_HOUSE_SPAWN
    return GHOST_HOUSE_DOOR


def get_target_tile(
    ghost_type: GhostType,
    ghost_pos: Vector2D,
    pacman_pos: Vector2D,
    pacman_dir: Direction,
    blinky_pos: Vector2D,
    ghost_house_exit: Vector2D = Vector2D(x=9.0, y=8.0),
) -> Vector2D:
    """Calculates the target grid cell for a given ghost based on classic Arcade AI logic."""
    px, py = pacman_pos.grid_x, pacman_pos.grid_y

    if ghost_type == GhostType.BLINKY:
        # Direct targeting -> Pac-Man's current tile
        return Vector2D(x=float(px), y=float(py))

    elif ghost_type == GhostType.PINKY:
        # Offset targeting -> 4 tiles ahead of Pac-Man.
        # Recreates classic Arcade UP overflow bug: (+4 UP also offsets -4 LEFT)
        if pacman_dir == Direction.UP:
            return Vector2D(x=float(px - 4), y=float(py - 4))
        return Vector2D(
            x=float(px + 4 * pacman_dir.dx),
            y=float(py + 4 * pacman_dir.dy),
        )

    elif ghost_type == GhostType.INKY:
        # Dual-vector targeting -> Offset 2 tiles ahead of Pac-Man, double vector from Blinky
        if pacman_dir == Direction.UP:
            intermediate_x = px - 2
            intermediate_y = py - 2
        else:
            intermediate_x = px + 2 * pacman_dir.dx
            intermediate_y = py + 2 * pacman_dir.dy

        vec_x = intermediate_x - blinky_pos.grid_x
        vec_y = intermediate_y - blinky_pos.grid_y

        target_x = blinky_pos.grid_x + 2 * vec_x
        target_y = blinky_pos.grid_y + 2 * vec_y
        return Vector2D(x=float(target_x), y=float(target_y))

    elif ghost_type == GhostType.CLYDE:
        # Proximity targeting -> Chase if distance >= 8 tiles, retreat if < 8
        dx = ghost_pos.grid_x - px
        dy = ghost_pos.grid_y - py
        dist_sq = dx * dx + dy * dy

        if dist_sq >= 64:  # 8^2 = 64
            return Vector2D(x=float(px), y=float(py))
        return DEFAULT_SCATTER_CORNERS[GhostType.CLYDE]

    return Vector2D(x=float(px), y=float(py))


def get_next_intersection_direction(
    board: list[list[int]],
    grid_x: int,
    grid_y: int,
    current_dir: Direction,
    target_tile: Vector2D,
    can_move_fn,
) -> Direction:
    """Determines next direction at an intersection by finding the min Euclidean distance squared.

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
