from typing import List, Tuple
from mazegenerator import MazeGenerator


# Wall Bitwise Flags
NORTH: int = 1
EAST: int = 2
SOUTH: int = 4
WEST: int = 8
DOT = 16
SUPER_DOT = 32
GHOST_HOUSE: int = 64
GATE: int = 128


class MazeAdapter:
    """Adapts raw MazeGenerator bitmasks into a 1:1 Pac-Man board representation."""

    def __init__(self, size: Tuple[int, int] = (19, 22), seed: int = 0) -> None:
        self.width, self.height = size
        self.generator = MazeGenerator(size=size, perfect=False, seed=seed)

        # 2D grid storing integer bitmask flags directly
        self.grid: List[List[int]] = [
            [0 for _ in range(self.width)] for _ in range(self.height)
        ]

        self._load_bitmask()
        self._carve_ghost_house_and_spawns()
        self._populate_pellets()

    def get_shortest_path(self) -> str | bool:
        """Expose calculated BFS navigation string."""
        return self.generator.shortest_path

    def _load_bitmask(self) -> None:
        """Copy native 4-bit wall codes directly without spatial expansion."""
        raw = self.generator.maze
        for y in range(self.height):
            for x in range(self.width):
                self.grid[y][x] = raw[y][x]

    def _carve_ghost_house_and_spawns(self) -> None:
        """Reserve center region for Ghost Box and Player Spawn."""
        cx, cy = self.width // 2, self.height // 2

        # Mark Ghost Box region
        for y in range(cy - 1, cy + 2):
            for x in range(cx - 2, cx + 3):
                self.grid[y][x] |= GHOST_HOUSE

        # Door Gate at top of Ghost Box
        self.grid[cy - 2][cx] |= GATE

        # Player spawn coordinate
        self.player_spawn = (cx, cy + 3)

    def _populate_pellets(self) -> None:
        """Add dots to walkable paths and super-dots to grid corners."""
        corner_candidates = [
            (1, 1),
            (self.width - 2, 1),
            (1, self.height - 2),
            (self.width - 2, self.height - 2),
        ]

        for y in range(self.height):
            for x in range(self.width):
                cell = self.grid[y][x]
                # Populate dots on tiles that are not ghost house or solid obstacle blocks (15)
                if not (cell & GHOST_HOUSE) and cell != 15:
                    self.grid[y][x] |= DOT

        # Upgrade corner pellets to Super-Dots
        for cx, cy in corner_candidates:
            if 0 <= cx < self.width and 0 <= cy < self.height:
                if self.grid[cy][cx] & DOT:
                    self.grid[cy][cx] &= ~DOT  # Clear standard dot bit
                    self.grid[cy][cx] |= SUPER_DOT
