from enum import Enum, IntEnum, auto


class GameState(Enum):
    MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    CONFIRM_QUIT = auto()
    GAME_OVER = auto()


class GhostMode(Enum):
    CHASE = auto()
    FRIGHTENED = auto()  # Edible state after Pac-Man eats Super-pacgum
    EATEN = auto()       # Returning to spawn corner
    SCATTER = auto()


class GhostType(str, Enum):
    BLINKY = "blinky"
    PINKY = "pinky"
    INKY = "inky"
    CLYDE = "clyde"


class CellType(IntEnum):
    # Wall Bitwise Flags
    NORTH: int = 1
    EAST: int = 2
    SOUTH: int = 4
    WEST: int = 8
    DOT = 16
    SUPER_DOT = 32
    GHOST_HOUSE: int = 64
    GATE: int = 128
