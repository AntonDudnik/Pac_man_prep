from enum import Enum, auto
from typing import Any, Dict


class GameState(Enum):
    MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    VICTORY = auto()


class GameEngine:
    """Core game engine managing state, loop execution, and cheat flags."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config: Dict[str, Any] = config
        self.state: GameState = GameState.MENU

        # Game stats initialized from config
        self.current_level: int = 1
        self.max_levels: int = len(config.get("levels", [])) or 10
        self.score: int = 0
        self.lives: int = config.get("lives", 3)
        self.time_remaining: float = float(config.get("level_max_time", 90))

        # Peer evaluation cheat mode flags
        self.cheat_invincible: bool = False
        self.cheat_freeze_ghosts: bool = False
        self.cheat_speed_boost: bool = False

    def toggle_cheat_invincibility(self) -> None:
        """Toggle invincibility cheat mode for evaluation."""
        self.cheat_invincible = not self.cheat_invincible
        print(f"[CHEAT] Invincibility: {self.cheat_invincible}")

    def toggle_cheat_freeze(self) -> None:
        """Toggle ghost freeze cheat mode for evaluation."""
        self.cheat_freeze_ghosts = not self.cheat_freeze_ghosts
        print(f"[CHEAT] Ghost Freeze: {self.cheat_freeze_ghosts}")

    def skip_level(self) -> None:
        """Cheat shortcut to skip the current level during peer-review."""
        print(f"[CHEAT] Skipping level {self.current_level}")
        self.next_level()

    def next_level(self) -> None:
        """Advance to the next level or trigger victory."""
        if self.current_level >= self.max_levels:
            self.state = GameState.VICTORY
        else:
            self.current_level += 1
            self.time_remaining = float(self.config.get("level_max_time", 90))

    def update(self, dt: float) -> None:
        """Update game loop state according to active GameState."""
        if self.state != GameState.PLAYING:
            return

        self.time_remaining -= dt
        if self.time_remaining <= 0:
            # Time expired behavior (e.g., restart or game over)
            self.lives -= 1
            if self.lives <= 0:
                self.state = GameState.GAME_OVER
            else:
                self.time_remaining = float(
                    self.config.get("level_max_time", 90))

    def render(self) -> None:
        """Render HUD and graphics based on current state."""
        # UI rendering calls will hook in here
        pass

    def run(self) -> None:
        """Start and run main application loop."""
        print("Starting Pac-Man Engine...")
        print(
            f"Loaded config parameters: Width={self.config.get('width')}, "
            f"Height={self.config.get('height')}"
        )

        # Skeleton loop stub for initialization verification
        self.state = GameState.MENU
        print("Engine initialized successfully. (Press Ctrl+C to stop if looping)")
