import json
import re
import sys
from typing import List, Tuple
from pydantic import BaseModel, Field, ValidationError
from pacman.entities.base import Vector2D


class LevelConfig(BaseModel):
    width: int = Field(default=19, ge=5)
    height: int = Field(default=21, ge=5)
    pacgum: int = Field(default=42, ge=0)
    level_max_time: float = Field(default=90.0, gt=0)
    # Entity spawn location mocks (x, y)
    player_start: tuple[int, int] = Field(default=(9, 10))
    ghost_starts: tuple[tuple[int, int], ...] = Field(
        default=((1, 1), (17, 1), (1, 19), (17, 19))
    )


class GameConfig(BaseModel):
    highscore_filename: str = "highscores.json"
    spritesheet_path: str = "assets/spritesheet.png"
    width: int = Field(default=19, ge=5)
    height: int = Field(default=21, ge=5)
    cell_size: int = Field(default=24, ge=8, le=120)
    lives: int = Field(default=3, ge=1)
    pacgum: int = Field(default=42, ge=0)
    points_per_pacgum: int = 10
    points_per_super_pacgum: int = 50
    points_per_ghost: int = 200
    player_speed: float = Field(default=5.0, gt=0.0)  # Cells per second
    ghost_speed: float = Field(default=4.0, gt=0.0)   # Cells per second
    seed: int = 42
    level_max_time: float = Field(default=90.0, gt=0)
    levels: List[LevelConfig] = Field(default_factory=list)

    @property
    def maze_size(self) -> Tuple[int, int]:
        """Convert game width/height into raw tuple dimensions for MazeGenerator."""
        return (self.width, self.height)

    @property
    def player_init_position(self) -> Vector2D:
        return Vector2D(x=self.width // 2, y=self.height // 4 * 3)


def strip_json_comments(content: str) -> str:
    """Remove single-line (#, //) and multi-line (/* */) comments from raw JSON string."""
    content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    lines: List[str] = []
    for line in content.splitlines():
        stripped = line.split("#")[0].split("//")[0].strip()
        if stripped:
            lines.append(stripped)
    return "\n".join(lines)


def load_config(filepath: str) -> GameConfig:
    """Load JSON config with comments, returning a validated GameConfig instance."""
    default_config = GameConfig()

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            raw_data = f.read()

        cleaned_data = strip_json_comments(raw_data)
        raw_json = json.loads(cleaned_data)

        if not isinstance(raw_json, dict):
            print("[WARN] JSON root must be an object. Falling back to defaults.", file=sys.stderr)
            return default_config

        return GameConfig(**raw_json)

    except FileNotFoundError:
        print(f"[WARN] Config file '{filepath}' not found. Using defaults.", file=sys.stderr)
    except json.JSONDecodeError as e:
        print(f"[WARN] Invalid JSON syntax in '{filepath}': {e}. Using defaults.", file=sys.stderr)
    except ValidationError as e:
        print(f"[WARN] Config validation error: {e}. Using defaults.", file=sys.stderr)
    except Exception as e:
        print(f"[WARN] Unexpected config error: {e}. Using defaults.", file=sys.stderr)

    return default_config
