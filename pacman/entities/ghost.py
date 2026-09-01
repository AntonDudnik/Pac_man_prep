import random
from pacman.entities import Direction, GhostMode, Vector2D


class Ghost:
    def __init__(self, ghost_id: int, position: Vector2D, speed: float = 4.0):
        self.ghost_id = ghost_id
        self.position = position
        self.speed = speed
        self.direction = Direction.RIGHT
        self.mode = GhostMode.NORMAL

        # Random Movement Timer
        self.dir_change_timer: float = 0.0
        self.dir_change_interval: float = 5.0

    def update(self, dt: float, board: list[list[int]]) -> None:
        """Update ghost position continuously with wall collision & random steering."""
        self.dir_change_timer += dt

        # Adjust speed based on state (e.g., Frightened = 50% speed)
        effective_speed = self.speed * (0.5 if self.mode == GhostMode.FRIGHTENED else 1.0)
        distance = effective_speed * dt

        # Calculate proposed next position
        next_pos = self.position.move_continuous(self.direction, distance)

        # Check if hitting a wall at target tile
        tile_x = int(next_pos.x)
        tile_y = int(next_pos.y)

        rows = len(board)
        cols = len(board[0])

        is_blocked = (
            tile_x < 0 or tile_x >= cols or
            tile_y < 0 or tile_y >= rows or
            board[tile_y][tile_x] != 0  # Assuming 0 is walkable path
        )

        # Change direction if timer hits 5s OR ghost hits a wall
        if self.dir_change_timer >= self.dir_change_interval or is_blocked:
            self._choose_random_direction(board, cols, rows)
            self.dir_change_timer = 0.0
            # Recalculate target position with new direction
            next_pos = self.position.move_continuous(self.direction, distance)

        # Update position if valid
        target_x = int(next_pos.x)
        target_y = int(next_pos.y)
        if 0 <= target_x < cols and 0 <= target_y < rows and board[target_y][target_x] == 0:
            self.position = next_pos

    def _choose_random_direction(self, board: list[list[int]], cols: int, rows: int) -> None:
        """Find valid non-wall directions and pick one at random."""
        dir_offsets = {
            Direction.UP: (0, -1),
            Direction.DOWN: (0, 1),
            Direction.LEFT: (-1, 0),
            Direction.RIGHT: (1, 0),
        }

        valid_dirs = []
        curr_x = int(self.position.x)
        curr_y = int(self.position.y)

        for d, (dx, dy) in dir_offsets.items():
            nx, ny = curr_x + dx, curr_y + dy
            if 0 <= nx < cols and 0 <= ny < rows and board[ny][nx] == 0:
                valid_dirs.append(d)

        if valid_dirs:
            # Avoid 180-degree immediate reversals if alternative paths exist
            opposite_map = {
                Direction.UP: Direction.DOWN, Direction.DOWN: Direction.UP,
                Direction.LEFT: Direction.RIGHT, Direction.RIGHT: Direction.LEFT
            }
            opposite = opposite_map.get(self.direction)
            non_reversing = [d for d in valid_dirs if d != opposite]

            self.direction = random.choice(non_reversing if non_reversing else valid_dirs)
