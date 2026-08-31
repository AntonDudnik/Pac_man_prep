from enum import Enum
from typing import Tuple
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


class Vector2D(BaseModel):
    model_config = ConfigDict(frozen=True)

    x: float = Field(default=0.0)
    y: float = Field(default=0.0)

    def to_tuple(self) -> Tuple[int, int]:
        return (self.x, self.y)

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
