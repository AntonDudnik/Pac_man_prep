from pacman.entities import Direction, GhostMode, GhostState, PlayerState, Vector2D


def test_vector_movement() -> None:
    start = Vector2D(x=9, y=10)
    moved_up = start.move(Direction.UP)
    assert moved_up.to_tuple() == (9, 9)

    moved_right = start.move(Direction.RIGHT)
    assert moved_right.to_tuple() == (10, 10)


def test_player_state_defaults() -> None:
    player = PlayerState(position=Vector2D(x=9, y=10), lives=3)
    assert player.lives == 3
    assert player.score == 0
    assert player.direction == Direction.NONE


def test_ghost_state_modes() -> None:
    ghost = GhostState(
        id=0,
        position=Vector2D(x=1, y=1),
        home_corner=Vector2D(x=1, y=1),
        mode=GhostMode.CHASE,
    )
    assert ghost.mode == GhostMode.CHASE
    ghost.mode = GhostMode.FRIGHTENED
    ghost.frightened_timer = 7.5
    assert ghost.mode == GhostMode.FRIGHTENED
    assert ghost.frightened_timer == 7.5
