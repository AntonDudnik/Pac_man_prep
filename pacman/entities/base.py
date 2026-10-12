from pacman.data_structure import Direction, Vector2D
from pacman.entities.state import CellType
from pacman.config import GameConfig


class BaseEntity():
    """Base class for dynamic runtime game objects."""

    def __init__(self, config: GameConfig) -> None:
        self.config = config
        self.position = Vector2D(x=0.0, y=0.0)
        self.speed = 0.0
        self.direction = Direction.NONE
        self.next_direction = Direction.NONE

    @property
    def grid_x(self) -> int:
        return int(round(self.position.x))

    @property
    def grid_y(self) -> int:
        return int(round(self.position.y))

    def update_position(self, board: list[list[int]], dt: float) -> None:
        gx, gy = self.grid_x, self.grid_y

        aligned_x = abs(self.position.x - gx) < 0.05
        aligned_y = abs(self.position.y - gy) < 0.05

        if aligned_x and aligned_y:
            # 1. Turn into buffered direction if unblocked
            if self.next_direction != self.direction:
                if can_move(board, gx, gy, self.next_direction):
                    self.direction = self.next_direction
                    self.position.x, self.position.y = float(gx), float(gy)

            # 2. Stop at wall along current path
            if not can_move(board, gx, gy, self.direction):
                self.direction = Direction.NONE
                self.position.x, self.position.y = float(gx), float(gy)

        # 3. Advance vector position
        dx, dy = self.direction.value
        self.position.x += dx * self.speed * dt
        self.position.y += dy * self.speed * dt


def can_move(
    board: list[list[int]],
    grid_x: int,
    grid_y: int,
    direction: Direction,
    is_ghost: bool = False,
) -> bool:
    """Evaluates if movement from cell (grid_x, grid_y) along direction is unblocked."""
    height = len(board)
    width = len(board[0])

    if not (0 <= grid_x < width and 0 <= grid_y < height):
        return False

    cell = board[grid_y][grid_x]

    # Gate handling: Only ghosts can pass through the Gate door
    if (cell & CellType.GATE):
        if is_ghost:
            return True
        # Player sees GATE as solid wall
        if direction in (Direction.UP, Direction.DOWN):
            return False

    # Standard directional wall bit evaluation
    if direction == Direction.UP:
        return not bool(cell & CellType.NORTH)
    elif direction == Direction.RIGHT:
        return not bool(cell & CellType.EAST)
    elif direction == Direction.DOWN:
        return not bool(cell & CellType.SOUTH)
    elif direction == Direction.LEFT:
        return not bool(cell & CellType.WEST)

    return True
