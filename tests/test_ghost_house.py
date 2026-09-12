"""Unit tests for Ghost House release queue and dot limits."""

from pacman.ai.ghost_house import GhostHouseManager
from pacman.entities import GhostType, Vector2D
from pacman.entities.ghost import Ghost


def _build_test_ghosts() -> dict[GhostType, Ghost]:
    return {
        GhostType.BLINKY: Ghost(ghost_id=0, home_corner=Vector2D()),
        GhostType.PINKY: Ghost(ghost_id=1, home_corner=Vector2D(), is_in_house=True),
        GhostType.INKY: Ghost(ghost_id=2, home_corner=Vector2D(), is_in_house=True),
        GhostType.CLYDE: Ghost(ghost_id=3, home_corner=Vector2D(), is_in_house=True),
    }


def test_ghost_initial_house_positions() -> None:
    ghosts = _build_test_ghosts()
    house = GhostHouseManager(ghosts)
    house.inactivity_timer = 0.0

    assert not ghosts[GhostType.BLINKY].is_in_house
    assert ghosts[GhostType.PINKY].is_in_house
    assert ghosts[GhostType.INKY].is_in_house
    assert ghosts[GhostType.CLYDE].is_in_house


def test_pinky_releases_at_zero_dots() -> None:
    ghosts = _build_test_ghosts()
    house = GhostHouseManager(ghosts)

    house.update(0.1)  # Pinky threshold is 0 dots
    assert not ghosts[GhostType.PINKY].is_in_house


def test_inky_releases_at_thirty_dots() -> None:
    ghosts = _build_test_ghosts()
    house = GhostHouseManager(ghosts)

    for _ in range(30):
        house.on_dot_eaten()

    house.update(0.1)
    assert not ghosts[GhostType.INKY].is_in_house


def test_inactivity_timer_force_releases() -> None:
    ghosts = _build_test_ghosts()
    house = GhostHouseManager(ghosts)

    house.update(0.1)  # Pinky exits at 0
    assert not ghosts[GhostType.PINKY].is_in_house

    # Pass 4.1s without eating dots -> Inky gets force released
    house.update(4.1)
    assert not ghosts[GhostType.INKY].is_in_house
