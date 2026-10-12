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
    NORTH = 1
    EAST = 2
    SOUTH = 4
    WEST = 8
    DOT = 16
    SUPER_DOT = 32
    GHOST_HOUSE = 64
    GATE = 128
