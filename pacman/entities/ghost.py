from abc import ABC, abstractmethod
import random

from pacman.config import GameConfig
from pacman.entities import Direction, GhostMode, GhostType, Vector2D
from pacman.entities.base import BaseEntity, can_move


class Ghost(BaseEntity, ABC):
    """Abstract Base Class for all AI-controlled Ghost entities."""

    def __init__(
        self,
        config: GameConfig,
        ghost_id: int,
        ghost_type: GhostType,
        is_in_house: bool = False,
    ) -> None:
        super().__init__(config=config)
        self.id = ghost_id
        self.type = ghost_type
        self.mode = GhostMode.CHASE
        self.frightened_timer = 0.0
        self.is_in_house = is_in_house
        self.speed = config.ghost_speed

        self.home_corner: Vector2D = self.get_home_corner()
        self.position: Vector2D = self.get_spawn_position()

    @abstractmethod
    def get_home_corner(self) -> Vector2D:
        """Return the scatter target corner for this ghost personality."""
        pass

    @abstractmethod
    def get_spawn_position(self) -> Vector2D:
        """Return the initial spawn position for this ghost personality."""
        pass

    @abstractmethod
    def get_target_tile(
        self,
        pacman_pos: Vector2D,
        pacman_dir: Direction,
        blinky_pos: Vector2D,
    ) -> Vector2D:
        """Calculate chase mode target tile based on ghost personality."""
        pass

    def reset_position(self) -> None:
        """Reset ghost state when Pac-Man loses a life."""
        self.position = self.get_spawn_position()
        self.direction = Direction.NONE
        self.next_direction = Direction.NONE
        self.mode = GhostMode.CHASE
        self.frightened_timer = 0.0
        self.is_in_house = self.type != GhostType.BLINKY

    def update(self, board: list[list[int]], dt: float, frozen: bool = False) -> None:
        if frozen:
            return

        if self.mode == GhostMode.FRIGHTENED:
            self.frightened_timer -= dt
            if self.frightened_timer <= 0.0:
                self.frightened_timer = 0.0
                self.mode = GhostMode.CHASE

        # Simple intersection decision algorithm
        gx, gy = self.grid_x, self.grid_y
        if abs(self.position.x - gx) < 0.05 and abs(self.position.y - gy) < 0.05:
            valid_dirs = [
                d for d in [Direction.UP, Direction.RIGHT, Direction.DOWN, Direction.LEFT]
                if can_move(board, gx, gy, d, is_ghost=True)
            ]
            if valid_dirs and (self.direction not in valid_dirs or len(valid_dirs) > 2):
                self.next_direction = random.choice(valid_dirs)

        self.update_position(board, dt)


class Blinky(Ghost):
    """Red Ghost (Shadow) - Targets Pac-Man directly."""

    def __init__(self, config: GameConfig) -> None:
        super().__init__(config=config, ghost_id=0, ghost_type=GhostType.BLINKY, is_in_house=False)

    def get_home_corner(self) -> Vector2D:
        return Vector2D(x=float(self.config.width - 1), y=0.0)

    def get_spawn_position(self) -> Vector2D:
        center_x = float(self.config.width // 2)
        center_y = float(self.config.height // 2)
        return Vector2D(x=center_x, y=center_y - 1.0)

    def get_target_tile(
        self,
        pacman_pos: Vector2D,
        pacman_dir: Direction,
        blinky_pos: Vector2D,
    ) -> Vector2D:
        px, py = pacman_pos.grid_x, pacman_pos.grid_y
        return Vector2D(x=float(px), y=float(py))


class Pinky(Ghost):
    """Pink Ghost (Speedy) - Ambushes 4 tiles ahead of Pac-Man."""

    def __init__(self, config: GameConfig) -> None:
        super().__init__(config=config, ghost_id=1, ghost_type=GhostType.PINKY, is_in_house=True)

    def get_home_corner(self) -> Vector2D:
        return Vector2D(x=0.0, y=0.0)

    def get_spawn_position(self) -> Vector2D:
        center_x = float(self.config.width // 2)
        center_y = float(self.config.height // 2)
        return Vector2D(x=center_x, y=center_y)

    def get_target_tile(
        self,
        pacman_pos: Vector2D,
        pacman_dir: Direction,
        blinky_pos: Vector2D,
    ) -> Vector2D:
        px, py = pacman_pos.grid_x, pacman_pos.grid_y
        if pacman_dir == Direction.UP:
            return Vector2D(x=float(px - 4), y=float(py - 4))
        return Vector2D(
            x=float(px + 4 * pacman_dir.dx),
            y=float(py + 4 * pacman_dir.dy),
        )


class Inky(Ghost):
    """Cyan Ghost (Bashful) - Dual-vector targeting based on Blinky and Pac-Man."""

    def __init__(self, config: GameConfig) -> None:
        super().__init__(config=config, ghost_id=2, ghost_type=GhostType.INKY, is_in_house=True)

    def get_home_corner(self) -> Vector2D:
        return Vector2D(x=float(self.config.width - 1), y=float(self.config.height - 1))

    def get_spawn_position(self) -> Vector2D:
        center_x = float(self.config.width // 2)
        center_y = float(self.config.height // 2)
        return Vector2D(x=center_x - 1.0, y=center_y)

    def get_target_tile(
        self,
        pacman_pos: Vector2D,
        pacman_dir: Direction,
        blinky_pos: Vector2D,
    ) -> Vector2D:
        px, py = pacman_pos.grid_x, pacman_pos.grid_y
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


class Clyde(Ghost):
    """Orange Ghost (Pokey) - Chases when far, retreats to corner when close."""

    def __init__(self, config: GameConfig) -> None:
        super().__init__(config=config, ghost_id=3, ghost_type=GhostType.CLYDE, is_in_house=True)

    def get_home_corner(self) -> Vector2D:
        return Vector2D(x=0.0, y=float(self.config.height - 1))

    def get_spawn_position(self) -> Vector2D:
        center_x = float(self.config.width // 2)
        center_y = float(self.config.height // 2)
        return Vector2D(x=center_x + 1.0, y=center_y)

    def get_target_tile(
        self,
        pacman_pos: Vector2D,
        pacman_dir: Direction,
        blinky_pos: Vector2D,
    ) -> Vector2D:
        px, py = pacman_pos.grid_x, pacman_pos.grid_y
        dx = self.grid_x - px
        dy = self.grid_y - py
        dist_sq = dx * dx + dy * dy

        if dist_sq >= 64:  # 8^2 = 64
            return Vector2D(x=float(px), y=float(py))

        # Dynamically returns home corner derived from config height
        return self.home_corner


def init_ghosts(config: GameConfig) -> dict[GhostType, Ghost]:
    """Factory function instantiating individual ghost subclasses."""
    ghosts: list[Ghost] = [
        Blinky(config),
        Pinky(config),
        Inky(config),
        Clyde(config),
    ]
    return {ghost.type: ghost for ghost in ghosts}
