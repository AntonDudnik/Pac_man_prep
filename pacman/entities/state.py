from enum import Enum, auto
from pydantic import BaseModel, Field
from pacman.entities.base import Direction, Vector2D


class GhostMode(Enum):
    CHASE = auto()
    FRIGHTENED = auto()  # Edible state after Pac-Man eats Super-pacgum
    EATEN = auto()       # Returning to spawn corner


class PlayerState(BaseModel):
    position: Vector2D = Field(default_factory=Vector2D)
    direction: Direction = Direction.NONE
    next_direction: Direction = Direction.NONE
    lives: int = Field(default=3, ge=0)
    score: int = Field(default=0, ge=0)
    speed: float = Field(default=5.0, gt=0.0)  # 5 cells per second


class GhostState(BaseModel):
    id: int
    position: Vector2D = Field(default_factory=Vector2D)
    home_corner: Vector2D = Field(default_factory=Vector2D)
    direction: Direction = Direction.NONE
    mode: GhostMode = GhostMode.CHASE
    frightened_timer: float = Field(default=0.0, ge=0.0)
    speed: float = Field(default=4.0, gt=0.0)  # Slightly slower than player
