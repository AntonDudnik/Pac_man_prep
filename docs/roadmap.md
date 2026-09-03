# Project Roadmap & Progress Tracker

## Phase 1: Project Setup & Core Models (Pydantic Integration)
- [x] Dependencies & virtual environment (`uv`).
- [x] Pydantic configuration (`GameConfig`, `LevelConfig`, comment stripping parser).
- [x] Data models (`Vector2D`, `Direction`, entity states).
- [x] Unit testing pipeline (`pytest`, `make test`).

## Phase 2: Graphics, Event Adapter & Visual Debugging (Pygame) [DONE]
- [x] Pygame window initialization & FPS clock adapter.
- [x] Menu state machine navigation (Space/Enter to play, P to pause, Q/Esc quit dialog).
- [x] Dynamic cell scaling (`cell_size`) & configuration parameters (`player_speed`, `ghost_speed`).
- [x] Debug grid overlay rendering (`alpha` transparent grid).
- [x] Load & render classic Pac-Man / Ghost directional sprites & animations.

## Phase 3: External Maze Adapter & Dynamic Generation
- [ ] Integrate A-Maze-ing algorithm interface.
- [ ] Add classic 1980 arcade maze fallback grid layout (19x22).
- [ ] Pac-gum & Super Pac-gum tile placement logic.

## Phase 4: Classical Pac-Man Ghost AI & Collision Engine
- [ ] Implement classic targeting vectors (Blinky, Pinky, Inky, Clyde).
- [ ] Dot-eating speed penalty mechanics (1-frame pause / speed reduction).
- [ ] Global Scatter / Chase wave state timer.
- [ ] Frightened state mechanics, edible ghost scoring ($200 \rightarrow 400 \rightarrow 800 \rightarrow 1600$), and eyes returning home.

## Phase 5: Highscores & Evaluation Cheat Shortcuts
- [ ] Persistent highscore IO with input validation.
- [ ] Cheat mode hotkeys (Invincibility, Freeze Ghosts, Speed Boost, Level Skip).

## Phase 6: Refinement, Packaging & Defense Prep
- [ ] Zero traceback audit across malformed inputs.
- [ ] Final compliance check with 42 School subject guidelines.