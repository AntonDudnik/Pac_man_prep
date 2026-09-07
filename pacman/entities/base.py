from enum import Enum
from typing import Tuple
from pydantic import BaseModel, ConfigDict, Field


# Wall Bitwise Flags
NORTH: int = 1
EAST: int = 2
SOUTH: int = 4
WEST: int = 8
DOT = 16
SUPER_DOT = 32
GHOST_HOUSE: int = 64
GATE: int = 128


class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)
    NONE = (0, 0)

    @property
    def dx(self) -> int:
        return self.value[0]

    @property
    def dy(self) -> int:
        return self.value[1]


class Vector2D(BaseModel):
    model_config = ConfigDict(frozen=False)

    x: float = Field(default=0.0)
    y: float = Field(default=0.0)

    def to_grid(self) -> Tuple[int, int]:
        """Return integer grid cell indices."""
        return (int(self.x), int(self.y))

    def move_continuous(self, direction: Direction, distance: float) -> "Vector2D":
        """Move position smoothly by distance in direction."""
        return Vector2D(
            x=self.x + direction.dx * distance,
            y=self.y + direction.dy * distance,
        )

    def move(self, direction: Direction) -> "Vector2D":
        """Discrete grid step move for backward compatibility with unit tests."""
        return self.move_continuous(direction, 1.0)


class BaseEntity:
    """Base class for dynamic runtime game objects."""

    def __init__(self, position: Vector2D | None = None, speed: float = 5.0) -> None:
        self.position = position if position is not None else Vector2D(x=0.0, y=0.0)
        self.speed = speed
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
    if cell & GATE:
        if is_ghost:
            return True
        # Player sees GATE as solid wall
        if direction in (Direction.UP, Direction.DOWN):
            return False

    # Standard directional wall bit evaluation
    if direction == Direction.UP:
        return not bool(cell & NORTH)
    elif direction == Direction.RIGHT:
        return not bool(cell & EAST)
    elif direction == Direction.DOWN:
        return not bool(cell & SOUTH)
    elif direction == Direction.LEFT:
        return not bool(cell & WEST)

    return True
