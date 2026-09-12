"""Ghost House release queue and exit path management."""

from typing import Dict, Optional
from pacman.ai.targeting import GHOST_HOUSE_DOOR
from pacman.entities import GhostType, Vector2D
from pacman.entities.ghost import Ghost


# Individual dot thresholds for Level 1
DEFAULT_DOT_LIMITS: Dict[GhostType, int] = {
    GhostType.PINKY: 0,
    GhostType.INKY: 5,
    GhostType.CLYDE: 10,
}

RELEASE_ORDER = [GhostType.PINKY, GhostType.INKY, GhostType.CLYDE]


class GhostHouseManager:

    def __init__(self, ghosts: Dict[GhostType, Ghost]) -> None:
        self.ghosts = ghosts
        self.dots_eaten: int = 0
        self.inactivity_timer: float = 0.0
        self.inactivity_limit: float = 4.0  # Force release if no dots eaten for 4s

    def on_dot_eaten(self) -> None:
        """Call whenever Pac-Man eats a dot/super-dot."""
        self.dots_eaten += 1
        self.inactivity_timer = 0.0  # Reset inactivity timer

    def update(self, dt: float) -> None:
        """Updates inactivity timer and releases any ghosts meeting dot thresholds."""
        self.inactivity_timer += dt

        while True:
            next_ghost_type = self._get_next_trapped_ghost()
            if not next_ghost_type:
                break

            limit = DEFAULT_DOT_LIMITS.get(next_ghost_type, 0)

            # Release if dot count threshold met or inactivity timeout triggered
            if self.dots_eaten >= limit or self.inactivity_timer >= self.inactivity_limit:
                self._release_ghost(next_ghost_type)
            else:
                break

    def _get_next_trapped_ghost(self) -> Optional[GhostType]:
        for gtype in RELEASE_ORDER:
            ghost = self.ghosts.get(gtype)
            if ghost and ghost.is_in_house:
                return gtype
        return None

    def _release_ghost(self, ghost_type: GhostType) -> None:
        ghost = self.ghosts[ghost_type]
        ghost.is_in_house = False
        ghost.position = Vector2D(x=GHOST_HOUSE_DOOR.x, y=GHOST_HOUSE_DOOR.y)
        self.inactivity_timer = 0.0
