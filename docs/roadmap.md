# Pac_Man Project Roadmap (42 School)
## Roadmap Summary
Phase 1: Project Setup & Core Models (Pydantic models for config & entities, # comment JSON parser).
Phase 2: Graphics & Event Adapter (Pygame encapsulated drawing primitives and input mapping).
Phase 3: External Maze Adapter (A-Maze-ing package wrapper, seed management, gum placement).
Phase 4: Game Entities & AI Mechanics (Pac-Man movement, ghost state machines: Chase/Frightened/Eaten).
Phase 5: Game Engine & Progression Loop (State machine, menu flow, HUD, level progression, Top 10 highscore I/O).
Phase 6: Quality Assurance, Packaging & Docs (make lint, README.md compliance, docs/ tracking, build packaging).

## Overview
This roadmap breaks down the development of the 42 **Pac_Man** project into incremental, testable phases. It incorporates **Pydantic** for robust configuration/state validation, **Pygame** (encapsulation for MLX-like usage), and `uv` for dependency management.

---

## Phase 1: Project Setup & Core Models (Pydantic Integration)
- [X] **Dependencies**: Add `pydantic` and `pygame` to `pyproject.toml` (`uv add pydantic pygame`).
- [X] **Configuration Module (`pacman/config.py`)**:
  - Implement Pydantic schema models (`GameConfig`, `LevelConfig`).
  - Write custom JSON parser stripping `#` and `//` comments.
  - Test fallback to safe defaults on invalid/missing JSON fields without tracebacks.
- [X] **Data Models (`pacman/entities/`)**:
  - Define `Vector2D` / `Direction` models for grid coordinates.
  - Define entity states (Player position/lives, Ghost modes: *Chase*, *Frightened*, *Eaten*).

---

## Phase 2: Graphics & Event Adapter (Pygame Wrapper)
- [ ] **UI Encapsulation (`pacman/ui.py`)**:
  - Create standard window initialization & game clock / frame-rate limiter.
  - Build simple pixel-drawing primitives (cells, pacgums, walls, entities) to keep logic decoupled from Pygame.
  - Implement font rendering for score, lives, level, and time remaining.
- [ ] **Input Management**:
  - Map key events (WASD / Arrow Keys) to movement intent.
  - Map evaluation cheat shortcuts (e.g., Invincibility, Ghost Freeze, Level Skip, Extra Lives).

---

## Phase 3: External Maze Generator Adapter
- [ ] **Package Integration (`pacman/maze.py`)**:
  - Install assigned external `A-Maze-ing` package via `uv`.
  - Create adapter class converting external maze data into internal game grid (`PERFECT=False`).
  - Support fixed seed (e.g., `42`) for Level 1, random seed for levels 2+.
  - Place Pacgums, Super-pacgums (4 corners), and Ghost/Player start positions.

---

## Phase 4: Game Entities & AI Mechanics
- [ ] **Player Logic (`pacman/entities/player.py`)**:
  - Implement grid-aligned movement and wall collision checks.
  - Handle item collection (Pacgums, Super-pacgums) and score updates.
- [ ] **Ghost Logic & AI (`pacman/entities/ghost.py`)**:
  - Implement state machine: *Chase*, *Frightened* (run away/edible), and *Eaten* (respawn to home corner).
  - Target-tracking algorithms (e.g., shortest path / BFS through corridors).
- [ ] **Collision Engine**:
  - Detect Player-Ghost interactions based on current Ghost state.
  - Handle invincibility cheat rules during collisions.

---

## Phase 5: Game Engine & Progression Loop
- [ ] **State Machine (`pacman/engine.py`)**:
  - Main Menu $\rightarrow$ Gameplay $\rightarrow$ Pause Menu $\rightarrow$ Win/Game Over.
- [ ] **Level Flow**:
  - Implement level-timer countdown.
  - Transition across levels (retain score and remaining lives).
- [ ] **Highscore System (`pacman/highscore.py`)**:
  - Implement persistent JSON highscore storage (Top 10 scores with player name $\le 10$ chars).
  - Add text-input prompt at Game Over / Victory screen.

---

## Phase 6: Quality Assurance, Packaging & Documentation
- [ ] **Static Analysis**:
  - Run `make lint` (`flake8` + `mypy --disallow-untyped-defs`).
- [ ] **Documentation Requirements (`README.md` & `docs/`)**:
  - First-line mandatory author tag.
  - Sections: Description, Instructions, Resources (including AI usage log), Config, Highscore, Maze Integration, Architecture, Project Management.
  - Maintain timeline/Gantt/test plans in `docs/`.
- [ ] **Packaging**:
  - Prepare executable build/script for release platform (Steam/Itch.io specs).