# Acceptance Test Plan

## 1. Automated Unit Testing Framework
- **Framework**: `pytest` executed via `make test` inside `uv` environment.
- **Coverage**: Core data models, schema validation, comment stripping, math operations.

### Executed Tests
- `tests/test_config.py`:
  - `test_strip_json_comments`: Verifies single-line and multi-line comment removal.
  - `test_load_config_defaults_on_missing_file`: Verifies fallback model when file is missing.
  - `test_load_config_from_valid_file`: Ensures JSON parses into `GameConfig`.
- `tests/test_entities.py`:
  - `test_vector_movement`: Verifies immutable grid steps in 4 cardinal directions.
  - `test_player_state_defaults`: Checks initial health, score, and position.
  - `test_ghost_state_modes`: Confirms mode transitions (*Chase*, *Frightened*, *Eaten*).

## 2. Integration & Manual Acceptance Criteria
- [ ] **Cheat Modes**: Invincibility, Ghost Freeze, Level Skip, Speed Boost triggered via hotkeys.
- [ ] **Highscore Persistence**: Save top 10 scores with validated player names (alphanumeric $\le$ 10 chars).
- [ ] **Faulty Config Handling**: Verify zero tracebacks when passing corrupt JSON files.