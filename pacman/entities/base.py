from enum import Enum
from typing import Tuple, List
from pydantic import BaseModel, ConfigDict, Field


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


# Bitmask directional constants
NORTH_BIT: int = 1
EAST_BIT: int = 2
SOUTH_BIT: int = 4
WEST_BIT: int = 8


def can_move(board: List[List[int]], grid_x: int, grid_y: int, direction: Direction) -> bool:
    """
    Checks if movement in `direction` from cell (grid_x, grid_y) is blocked by a wall bit.
    """
    height = len(board)
    width = len(board[0])

    # Out of bounds safety check
    if not (0 <= grid_x < width and 0 <= grid_y < height):
        return False

    cell = board[grid_y][grid_x]

    if direction == Direction.UP:
        return not bool(cell & NORTH_BIT)
    elif direction == Direction.RIGHT:
        return not bool(cell & EAST_BIT)
    elif direction == Direction.DOWN:
        return not bool(cell & SOUTH_BIT)
    elif direction == Direction.LEFT:
        return not bool(cell & WEST_BIT)

    return True


class Vector2D(BaseModel):
    model_config = ConfigDict(frozen=True)

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
