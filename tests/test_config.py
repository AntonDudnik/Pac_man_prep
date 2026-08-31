import json
from pacman.config import GameConfig, LevelConfig, load_config, strip_json_comments


def test_strip_json_comments() -> None:
    json_with_comments = """
    {
        # Hash style comment
        "lives": 5, // C++ style inline comment
        /* Multi-line
           comment block */
        "seed": 100
    }
    """
    cleaned = strip_json_comments(json_with_comments)
    parsed = json.loads(cleaned)
    assert parsed["lives"] == 5
    assert parsed["seed"] == 100


def test_load_config_defaults_on_missing_file() -> None:
    config = load_config("non_existent_file.json")
    assert isinstance(config, GameConfig)
    assert config.lives == 3
    assert config.width == 19


def test_load_config_from_valid_file() -> None:
    config = load_config("config.json")
    assert isinstance(config, GameConfig)
    assert config.lives == 3
    assert config.points_per_ghost == 200
    assert config.seed == 42


def test_level_config_defaults() -> None:
    level = LevelConfig()
    assert level.player_start == (9, 10)
    assert len(level.ghost_starts) == 4
