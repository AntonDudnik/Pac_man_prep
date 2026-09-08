"""Unit tests for Phase 4 Ghost AI targeting mechanics and WaveTimer transitions."""

from pacman.ai.ghost_manager import GhostManager
from pacman.ai.targeting import (
    DEFAULT_SCATTER_CORNERS,
    get_next_intersection_direction,
    get_target_tile,
)
from pacman.ai.wave_timer import GlobalWaveMode, WaveTimer
from pacman.entities import Direction, GhostMode, GhostType, Vector2D
from pacman.entities.ghost import Ghost


# ---------------------------------------------------------------------------
# 1. Pure Targeting Vector Tests
# ---------------------------------------------------------------------------


class TestGhostTargeting:
    def test_blinky_targeting_directs_to_pacman(self) -> None:
        pacman_pos = Vector2D(x=10.0, y=12.0)
        target = get_target_tile(
            ghost_type=GhostType.BLINKY,
            ghost_pos=Vector2D(x=2.0, y=2.0),
            pacman_pos=pacman_pos,
            pacman_dir=Direction.RIGHT,
            blinky_pos=Vector2D(x=2.0, y=2.0),
        )
        assert (target.x, target.y) == (10.0, 12.0)

    def test_pinky_targeting_cardinal_offsets(self) -> None:
        pacman_pos = Vector2D(x=10.0, y=10.0)

        # RIGHT -> +4 X
        t_right = get_target_tile(
            GhostType.PINKY, Vector2D(), pacman_pos, Direction.RIGHT, Vector2D()
        )
        assert (t_right.x, t_right.y) == (14.0, 10.0)

        # DOWN -> +4 Y
        t_down = get_target_tile(
            GhostType.PINKY, Vector2D(), pacman_pos, Direction.DOWN, Vector2D()
        )
        assert (t_down.x, t_down.y) == (10.0, 14.0)

        # LEFT -> -4 X
        t_left = get_target_tile(
            GhostType.PINKY, Vector2D(), pacman_pos, Direction.LEFT, Vector2D()
        )
        assert (t_left.x, t_left.y) == (6.0, 10.0)

    def test_pinky_targeting_arcade_up_overflow_bug(self) -> None:
        """Verify Arcade UP overflow bug: UP offset adds (-4, -4)."""
        pacman_pos = Vector2D(x=10.0, y=10.0)
        t_up = get_target_tile(
            GhostType.PINKY, Vector2D(), pacman_pos, Direction.UP, Vector2D()
        )
        assert (t_up.x, t_up.y) == (6.0, 6.0)

    def test_inky_dual_vector_targeting(self) -> None:
        pacman_pos = Vector2D(x=10.0, y=10.0)
        pacman_dir = Direction.RIGHT  # 2 tiles ahead -> (12, 10)
        blinky_pos = Vector2D(x=8.0, y=10.0)

        # Vector from Blinky (8,10) to intermediate (12,10) is (+4, 0).
        # Doubling vector from Blinky -> (8 + 2*4, 10 + 2*0) = (16, 10).
        target = get_target_tile(
            GhostType.INKY, Vector2D(), pacman_pos, pacman_dir, blinky_pos
        )
        assert (target.x, target.y) == (16.0, 10.0)

    def test_clyde_proximity_targeting_threshold(self) -> None:
        pacman_pos = Vector2D(x=10.0, y=10.0)

        # Far distance (>= 8 tiles away) -> Chases Pac-Man
        clyde_far_pos = Vector2D(x=10.0, y=2.0)  # Dist = 8 tiles (dist^2 = 64)
        t_far = get_target_tile(
            GhostType.CLYDE, clyde_far_pos, pacman_pos, Direction.RIGHT, Vector2D()
        )
        assert (t_far.x, t_far.y) == (10.0, 10.0)

        # Close proximity (< 8 tiles away) -> Retreats to Clyde scatter corner
        clyde_close_pos = Vector2D(x=10.0, y=5.0)  # Dist = 5 tiles (dist^2 = 25)
        t_close = get_target_tile(
            GhostType.CLYDE, clyde_close_pos, pacman_pos, Direction.RIGHT, Vector2D()
        )
        scatter_corner = DEFAULT_SCATTER_CORNERS[GhostType.CLYDE]
        assert (t_close.x, t_close.y) == (scatter_corner.x, scatter_corner.y)


# ---------------------------------------------------------------------------
# 2. Intersection Decision & Tie-Breaking Tests
# ---------------------------------------------------------------------------


class TestIntersectionDecision:
    def test_tie_breaking_priority_order(self) -> None:
        """Priority tie-breaker order: UP > LEFT > DOWN > RIGHT."""

        # Mock open cell with no wall restrictions
        def dummy_can_move(board, gx, gy, direction, is_ghost=True):
            return True

        # Target equidistant from UP (1, 0) and LEFT (0, 1) when starting at (1, 1)
        # UP cell (1, 0) -> dist sq to (0, 0) = 1^2 + 0^2 = 1
        # LEFT cell (0, 1) -> dist sq to (0, 0) = 0^2 + 1^2 = 1
        target = Vector2D(x=0.0, y=0.0)
        chosen = get_next_intersection_direction(
            board=[],
            grid_x=1,
            grid_y=1,
            current_dir=Direction.RIGHT,
            target_tile=target,
            can_move_fn=dummy_can_move,
        )
        # UP takes priority over LEFT
        assert chosen == Direction.UP

    def test_prevents_180_reversal(self) -> None:
        def dummy_can_move(board, gx, gy, direction, is_ghost=True):
            return True

        # Target is directly behind the ghost (LEFT of x=2, y=0)
        target = Vector2D(x=0.0, y=0.0)
        chosen = get_next_intersection_direction(
            board=[],
            grid_x=2,
            grid_y=0,
            current_dir=Direction.RIGHT,  # Moving RIGHT, opposite is LEFT
            target_tile=target,
            can_move_fn=dummy_can_move,
        )
        # Must not choose LEFT even though it's closer to target
        assert chosen != Direction.LEFT


# ---------------------------------------------------------------------------
# 3. WaveTimer Schedule Tests
# ---------------------------------------------------------------------------


class TestWaveTimer:
    def test_wave_timer_transitions(self) -> None:
        # Custom short schedule for deterministic testing
        timer = WaveTimer(
            schedule=[
                (GlobalWaveMode.SCATTER, 2.0),
                (GlobalWaveMode.CHASE, 5.0),
            ]
        )

        assert timer.current_mode == GlobalWaveMode.SCATTER

        # Advance timer partially
        swapped = timer.update(1.0)
        assert not swapped
        assert timer.current_mode == GlobalWaveMode.SCATTER

        # Crossing 2.0s threshold triggers wave advance
        swapped = timer.update(1.1)
        assert swapped
        assert timer.current_mode == GlobalWaveMode.CHASE

    def test_ghost_manager_frightened_mode(self) -> None:
        blinky = Ghost(ghost_id=0, home_corner=Vector2D(x=17.0, y=-2.0))
        ghosts = {GhostType.BLINKY: blinky}
        manager = GhostManager(ghosts)

        # Trigger Frightened
        manager.trigger_frightened(duration=5.0)
        assert blinky.mode == GhostMode.FRIGHTENED
        assert blinky.frightened_timer == 5.0

        # Update manager to tick down frightened timer
        dummy_board = [[0] * 10 for _ in range(10)]
        manager.update(
            board=dummy_board,
            dt=5.5,
            pacman_pos=Vector2D(x=1.0, y=1.0),
            pacman_dir=Direction.NONE,
        )

        # Mode returns to CHASE once expired
        assert blinky.mode == GhostMode.CHASE
        assert blinky.frightened_timer == 0.0
