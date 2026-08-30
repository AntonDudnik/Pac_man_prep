import json
import re
import sys
from typing import Any, Dict, List
from pydantic import BaseModel, Field, ValidationError


class LevelConfig(BaseModel):
    width: int = Field(default=19, ge=5)
    height: int = Field(default=21, ge=5)
    pacgum: int = Field(default=42, ge=0)
    level_max_time: float = Field(default=90.0, gt=0)


class GameConfig(BaseModel):
    highscore_filename: str = "highscores.json"
    width: int = Field(default=19, ge=5)
    height: int = Field(default=21, ge=5)
    lives: int = Field(default=3, ge=1)
    pacgum: int = Field(default=42, ge=0)
    points_per_pacgum: int = 10
    points_per_super_pacgum: int = 50
    points_per_ghost: int = 200  # Fixed: type annotation added
    seed: int = 42
    level_max_time: float = Field(default=90.0, gt=0)
    levels: List[LevelConfig] = []


def _strip_json_comments(content: str) -> str:
    """Strip single-line (# or //) and block (/* ... */) comments from raw JSON string."""
    content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    lines: List[str] = []
    for line in content.splitlines():
        stripped = line.split("#")[0].split("//")[0]
        lines.append(stripped)
    return "\n".join(lines)


def load_config(filepath: str) -> Dict[str, Any]:
    """Load JSON config, handle comments, ignore unknown keys, and clamp to defaults on error."""
    default_model = GameConfig()

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            raw_data = f.read()

        cleaned_data = _strip_json_comments(raw_data)
        raw_json = json.loads(cleaned_data)

        if not isinstance(raw_json, dict):
            print("[WARN] JSON root must be an object. Falling back to defaults.", file=sys.stderr)
            return default_model.model_dump()

        # Pydantic validates known fields and ignores unknown extra keys by default
        validated_config = GameConfig(**raw_json)
        return validated_config.model_dump()

    except FileNotFoundError:
        print(f"[WARN] Config file '{filepath}' not found. Using defaults.", file=sys.stderr)
    except json.JSONDecodeError as e:
        print(f"[WARN] Invalid JSON syntax in '{filepath}': {e}. Using defaults.", file=sys.stderr)
    except ValidationError as e:
        print(f"[WARN] Config validation error: {e}. Using defaults.", file=sys.stderr)
    except Exception as e:
        print(f"[WARN] Unexpected config error: {e}. Using defaults.", file=sys.stderr)

    return default_model.model_dump()
