from enum import Enum, auto


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


class GhostType(str, Enum):
    BLINKY = "blinky"
    PINKY = "pinky"
    INKY = "inky"
    CLYDE = "clyde"
