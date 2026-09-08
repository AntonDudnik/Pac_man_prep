"""Ghost Manager orchestrating state transitions, targeting, and intersections."""

import random
from pacman.ai.targeting import (
    DEFAULT_SCATTER_CORNERS,
    get_next_intersection_direction,
    get_target_tile,
)
from pacman.ai.targeting import GHOST_HOUSE_SPAWN, get_eaten_target_tile
from pacman.ai.wave_timer import GlobalWaveMode, WaveTimer
from pacman.entities import Direction, GhostMode, GhostType, Vector2D
from pacman.entities.base import can_move
from pacman.entities.ghost import Ghost


class GhostManager:
    def __init__(self, ghosts: dict[GhostType, Ghost]) -> None:
        self.ghosts = ghosts
        self.wave_timer = WaveTimer()
        self.ghost_eat_streak: int = 0  # Resets when entering Frightened mode

    def update(
        self,
        board: list[list[int]],
        dt: float,
        pacman_pos: Vector2D,
        pacman_dir: Direction,
        frozen: bool = False,
    ) -> None:
        if frozen:
            return

        # 1. Advance global wave timer & force reversal on Scatter/Chase mode switch
        wave_changed = self.wave_timer.update(dt)
        if wave_changed:
            self._trigger_global_direction_reversal(board)

        blinky = self.ghosts.get(GhostType.BLINKY)
        blinky_pos = blinky.position if blinky else Vector2D()

        # 2. Update each ghost entity
        for ghost_type, ghost in self.ghosts.items():
            if ghost.mode == GhostMode.FRIGHTENED:
                ghost.frightened_timer -= dt
                if ghost.frightened_timer <= 0.0:
                    ghost.frightened_timer = 0.0
                    ghost.mode = GhostMode.CHASE

            # Update direction logic at intersection alignment point
            self._update_ghost_direction(
                ghost=ghost,
                ghost_type=ghost_type,
                board=board,
                pacman_pos=pacman_pos,
                pacman_dir=pacman_dir,
                blinky_pos=blinky_pos,
            )

            # Move physical entity position
            ghost.update_position(board, dt)

    def _trigger_global_direction_reversal(self, board: list[list[int]]) -> None:
        """Forces a 180-degree direction reversal when wave mode flips."""
        opposite = {
            Direction.UP: Direction.DOWN,
            Direction.DOWN: Direction.UP,
            Direction.LEFT: Direction.RIGHT,
            Direction.RIGHT: Direction.LEFT,
            Direction.NONE: Direction.NONE,
        }
        for ghost in self.ghosts.values():
            if ghost.mode in (GhostMode.CHASE, GhostMode.FRIGHTENED):
                rev = opposite[ghost.direction]
                if can_move(board, ghost.grid_x, ghost.grid_y, rev, is_ghost=True):
                    ghost.direction = rev
                    ghost.next_direction = rev

    def trigger_frightened(self, duration: float = 7.0) -> None:
        """Activates Frightened state across all active non-eaten ghosts."""
        self.ghost_eat_streak = 0  # Reset progressive kill counter
        for ghost in self.ghosts.values():
            if ghost.mode != GhostMode.EATEN:
                ghost.mode = GhostMode.FRIGHTENED
                ghost.frightened_timer = duration

    def consume_frightened_ghost(self, ghost: Ghost) -> int:
        """Eats a frightened ghost, sets EATEN state, and returns score value."""
        ghost.mode = GhostMode.EATEN

        # Progression: 200 -> 400 -> 800 -> 1600
        score_value = 200 * (2 ** self.ghost_eat_streak)
        self.ghost_eat_streak = min(self.ghost_eat_streak + 1, 3)
        return score_value

    def _update_ghost_direction(
        self,
        ghost: Ghost,
        ghost_type: GhostType,
        board: list[list[int]],
        pacman_pos: Vector2D,
        pacman_dir: Direction,
        blinky_pos: Vector2D,
    ) -> None:
        gx, gy = ghost.grid_x, ghost.grid_y
        aligned_x = abs(ghost.position.x - gx) < 0.05
        aligned_y = abs(ghost.position.y - gy) < 0.05

        if not (aligned_x and aligned_y):
            return

        # 1. EATEN Mode: Fast return pathing to Ghost House
        if ghost.mode == GhostMode.EATEN:
            ghost.speed = 8.0  # Double speed for returning eyes

            # Check if eyes have arrived inside the Ghost House
            if gx == GHOST_HOUSE_SPAWN.grid_x and gy == GHOST_HOUSE_SPAWN.grid_y:
                ghost.mode = GhostMode.CHASE
                ghost.speed = 4.0
                return

            target_tile = get_eaten_target_tile(ghost.position)
            ghost.next_direction = get_next_intersection_direction(
                board=board,
                grid_x=gx,
                grid_y=gy,
                current_dir=ghost.direction,
                target_tile=target_tile,
                can_move_fn=can_move,
            )
            return

        if ghost.mode == GhostMode.FRIGHTENED:
            # Random choice at intersections during Frightened mode
            valid_dirs = [
                d
                for d in [Direction.UP, Direction.RIGHT, Direction.DOWN, Direction.LEFT]
                if can_move(board, gx, gy, d, is_ghost=True)
            ]
            if valid_dirs:
                ghost.next_direction = random.choice(valid_dirs)
            return

        # Determine target tile depending on current global wave mode
        if self.wave_timer.current_mode == GlobalWaveMode.SCATTER:
            target_tile = DEFAULT_SCATTER_CORNERS.get(ghost_type, Vector2D())
        else:
            target_tile = get_target_tile(
                ghost_type=ghost_type,
                ghost_pos=ghost.position,
                pacman_pos=pacman_pos,
                pacman_dir=pacman_dir,
                blinky_pos=blinky_pos,
            )

        # Select deterministic min-distance direction
        next_dir = get_next_intersection_direction(
            board=board,
            grid_x=gx,
            grid_y=gy,
            current_dir=ghost.direction,
            target_tile=target_tile,
            can_move_fn=can_move,
        )
        ghost.next_direction = next_dir
