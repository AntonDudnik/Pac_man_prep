import random
from pacman.entities import Direction, GhostMode, Vector2D
from pacman.entities.base import BaseEntity, can_move


class Ghost(BaseEntity):
    """AI-controlled Ghost entity."""

    def __init__(
        self,
        ghost_id: int,
        home_corner: Vector2D,
        position: Vector2D | None = None,
        speed: float = 4.0,
    ) -> None:
        super().__init__(position=position, speed=speed)
        self.id = ghost_id
        self.home_corner = home_corner
        self.mode = GhostMode.CHASE
        self.frightened_timer = 0.0

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
                if can_move(board, gx, gy, d, True)
            ]
            if valid_dirs and (self.direction not in valid_dirs or len(valid_dirs) > 2):
                self.next_direction = random.choice(valid_dirs)

        self.update_position(board, dt)
