import random
from pacman.entities import Direction, GhostType, GhostMode, Vector2D
from pacman.entities.base import BaseEntity, can_move


def init_ghosts(
    maze_width: int, maze_height: int, ghost_speed: float
) -> dict[GhostType, "Ghost"]:
    # Relative grid offsets from the board center
    center_x = maze_width / 2.0
    center_y = maze_height / 2.0

    return {
        GhostType.BLINKY: Ghost(
            ghost_id=0,
            home_corner=Vector2D(x=maze_width - 1.0, y=0.0),
            position=Vector2D(x=center_x, y=center_y - 2),
            speed=ghost_speed,
            is_in_house=False,
        ),
        GhostType.PINKY: Ghost(
            ghost_id=1,
            home_corner=Vector2D(x=0.0, y=0.0),
            position=Vector2D(x=center_x, y=center_y),
            speed=ghost_speed,
            is_in_house=True,
        ),
        GhostType.INKY: Ghost(
            ghost_id=2,
            home_corner=Vector2D(x=maze_width - 1.0, y=maze_height - 1.0),
            position=Vector2D(x=center_x - 1, y=center_y),
            speed=ghost_speed,
            is_in_house=True,
        ),
        GhostType.CLYDE: Ghost(
            ghost_id=3,
            home_corner=Vector2D(x=0.0, y=maze_height - 1.0),
            position=Vector2D(x=center_x + 1, y=center_y),
            speed=ghost_speed,
        ),
    }


class Ghost(BaseEntity):
    """AI-controlled Ghost entity."""

    def __init__(
        self,
        ghost_id: int,
        home_corner: Vector2D | None = None,
        position: Vector2D | None = None,
        speed: float = 4.0,
        is_in_house: bool = False
    ) -> None:
        super().__init__(position=position, speed=speed)
        self.id = ghost_id
        self.home_corner = home_corner
        self.mode = GhostMode.CHASE
        self.frightened_timer = 0.0
        self.is_in_house = is_in_house

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
