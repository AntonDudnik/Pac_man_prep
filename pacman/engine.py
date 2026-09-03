from pacman.entities.state import (
    Direction,
    GameState,
    GhostMode,
    GhostState,
    PlayerState,
    Vector2D
)
from pacman.config import GameConfig
from pacman.adapters.maze import MazeAdapter
import os
import random

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame  # noqa: E402
from pacman.ui import PygameUI  # noqa: E402


class GameEngine:
    def __init__(self, config: GameConfig) -> None:
        self.config = config
        self.state = GameState.MENU
        # 1. Generate Maze using config dimensions and seed
        self.maze_adapter = self.generate_maze()
        self.board = self.maze_adapter.grid

        self.ui = PygameUI(
            self.config.width, self.config.height,
            config.cell_size, config.spritesheet_path)

        self.current_level = 1
        self.score = 0
        self.lives = config.lives
        self.time_remaining = float(config.level_max_time)
        self.state = GameState.MENU
        self.menu_options = ["PLAY GAME", "OPTIONS", "QUIT"]
        self.menu_index = 0
        # Cheats
        self.cheat_invincible = False
        self.cheat_freeze_ghosts = False
        self.cheat_speed_boost: bool = False

        # 2. Initialize Player and Ghosts matching your model fields
        self.player = PlayerState()
        self.ghosts = [
            GhostState(id=0, home_corner=Vector2D(x=1, y=1)),
            GhostState(id=1, home_corner=Vector2D(x=self.config.width - 2, y=1)),
            GhostState(id=2, home_corner=Vector2D(x=1, y=self.config.height - 2)),
            GhostState(
                id=3,
                home_corner=Vector2D(
                    x=self.config.width - 2, y=self.config.height - 2
                ),
            ),
        ]

        # 3. Position Player on spawn point derived from maze generator
        if hasattr(self.maze_adapter, "player_spawn"):
            px, py = self.maze_adapter.player_spawn
            self.player.position = Vector2D(x=float(px), y=float(py))

    def generate_maze(self) -> MazeAdapter:
        """Instantiate MazeAdapter with current config parameters."""
        adapter = MazeAdapter(size=self.config.maze_size, seed=self.config.seed,)
        print(f"[ENGINE] Maze Generated: {adapter.width}x{adapter.height} tile grid.")
        print(f"[ENGINE] Solution Path: {adapter.get_shortest_path()}")
        return adapter

    def reset_level(self, new_seed: int | None = None) -> None:
        """Regenerate the maze for level transitions or seed updates."""
        if new_seed is not None:
            self.config.seed = new_seed
        self.maze_adapter = self.generate_maze()
        self.board = self.maze_adapter.grid

    def handle_input(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        if self.state == GameState.MENU:
            if event.key == pygame.K_UP:
                self.menu_index = (self.menu_index - 1) % len(self.menu_options)
            elif event.key == pygame.K_DOWN:
                self.menu_index = (self.menu_index + 1) % len(self.menu_options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._execute_menu_selection()
            elif event.key == pygame.K_q:
                self.running = False

    def _execute_menu_selection(self) -> None:
        if self.menu_index == 0:     # PLAY GAME
            self.state = GameState.PLAYING
        elif self.menu_index == 1:   # OPTIONS
            pass  # Future state transition to GameState.OPTIONS
        elif self.menu_index == 2:   # QUIT
            self.running = False

    def handle_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                # -------------------------------------------------------------
                # 1. CONFIRM QUIT OVERLAY CONTROLS
                # -------------------------------------------------------------
                if self.state == GameState.CONFIRM_QUIT:
                    if event.key in (pygame.K_y, pygame.K_RETURN, pygame.K_KP_ENTER):
                        return False  # Confirm Quit -> Exit loop
                    elif event.key in (pygame.K_n, pygame.K_ESCAPE, pygame.K_q):
                        # Cancel -> Return to previous state (PLAYING or PAUSED)
                        self.state = getattr(self, "previous_state", GameState.PLAYING)

                # -------------------------------------------------------------
                # 2. TRIGGER QUIT DIALOG (ESC or Q from Gameplay/Pause)
                # -------------------------------------------------------------
                elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                    if self.state in (GameState.PLAYING, GameState.PAUSED):
                        self.previous_state = self.state
                        self.state = GameState.CONFIRM_QUIT
                    elif self.state == GameState.MENU:
                        return False  # Exit directly from main menu

                # -------------------------------------------------------------
                # 3. MENU STATE CONTROLS
                # -------------------------------------------------------------
                elif self.state == GameState.MENU:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        self.menu_index = (self.menu_index - 1) % len(self.menu_options)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.menu_index = (self.menu_index + 1) % len(self.menu_options)
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                        if self.menu_index == 0:     # PLAY GAME
                            self.state = GameState.PLAYING
                        elif self.menu_index == 2:   # QUIT
                            return False

                # -------------------------------------------------------------
                # 4. PAUSE / PLAYING CONTROLS
                # -------------------------------------------------------------
                elif event.key == pygame.K_p:
                    if self.state == GameState.PLAYING:
                        self.state = GameState.PAUSED
                    elif self.state == GameState.PAUSED:
                        self.state = GameState.PLAYING

                elif self.state == GameState.PLAYING:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        self.player.direction = Direction.UP
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.player.direction = Direction.DOWN
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        self.player.direction = Direction.LEFT
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        self.player.direction = Direction.RIGHT

                    # Visual Debugging Hotkeys
                    elif event.key == pygame.K_f:
                        for ghost in self.ghosts:
                            ghost.mode = GhostMode.FRIGHTENED
                            ghost.frightened_timer = 7.0
                    elif event.key == pygame.K_e:
                        for ghost in self.ghosts:
                            ghost.mode = GhostMode.EATEN
                    elif event.key == pygame.K_c:
                        for ghost in self.ghosts:
                            ghost.mode = GhostMode.CHASE
                            ghost.frightened_timer = 0.0

                    # Gameplay Cheats
                    elif event.key == pygame.K_i:
                        self.cheat_invincible = not self.cheat_invincible
                        print(f"[CHEAT] Invincible: {self.cheat_invincible}")
                    elif event.key == pygame.K_z:
                        self.cheat_freeze_ghosts = not self.cheat_freeze_ghosts
                        print(f"[CHEAT] Freeze: {self.cheat_freeze_ghosts}")
                    elif event.key == pygame.K_b:
                        self.cheat_speed_boost = not self.cheat_speed_boost
                        print(f"[CHEAT] Speed Boost: {self.cheat_speed_boost}")

        return True

    def update(self, dt: float) -> None:
        if self.state != GameState.PLAYING:
            return

        self.ui.update_anim_timer(dt)

        self.time_remaining -= dt
        if self.time_remaining <= 0:
            self.state = GameState.GAME_OVER

        # Player Movement
        effective_speed = self.player.speed * (2.0 if self.cheat_speed_boost else 1.0)
        distance = effective_speed * dt
        new_pos = self.player.position.move_continuous(self.player.direction, distance)

        px = max(0.0, min(float(self.config.width - 1), new_pos.x))
        py = max(0.0, min(float(self.config.height - 1), new_pos.y))
        self.player.position = Vector2D(x=px, y=py)

        # Update ghost mode timers & state transitions
        for ghost in self.ghosts:
            if ghost.mode == GhostMode.FRIGHTENED:
                ghost.frightened_timer -= dt
                if ghost.frightened_timer <= 0.0:
                    ghost.frightened_timer = 0.0
                    ghost.mode = GhostMode.CHASE

        # Move ghosts if not frozen by cheat
        if not self.cheat_freeze_ghosts:
            for ghost in self.ghosts:
                self._update_ghost(ghost, dt)

    def _update_ghost(self, ghost: GhostState, dt: float) -> None:
        """Update a single ghost's continuous position, boundary checks, and direction timers."""
        ghost.dir_change_timer += dt

        # Frightened ghosts move at half speed
        speed = ghost.speed * (0.5 if ghost.mode == GhostMode.FRIGHTENED else 1.0)
        dist = speed * dt

        # Calculate proposed continuous position
        next_pos = ghost.position.move_continuous(ghost.direction, dist)

        # Boundary limits (clamp to board dimensions from self.config)
        is_blocked = (
            next_pos.x <= 0.0 or next_pos.x >= (self.config.width - 1) or
            next_pos.y <= 0.0 or next_pos.y >= (self.config.height - 1)
        )

        # Switch direction if 5 seconds have elapsed OR ghost hits board boundaries
        if ghost.dir_change_timer >= 5.0 or is_blocked or ghost.direction == Direction.NONE:
            ghost.direction = self._get_random_valid_direction(ghost)
            ghost.dir_change_timer = 0.0
            next_pos = ghost.position.move_continuous(ghost.direction, dist)

        # Clamp position safely within board boundaries
        gx = max(0.0, min(float(self.config.width - 1), next_pos.x))
        gy = max(0.0, min(float(self.config.height - 1), next_pos.y))
        ghost.position = Vector2D(x=gx, y=gy)

    def _get_random_valid_direction(self, ghost: GhostState) -> Direction:
        """Pick a new random direction, avoiding immediate 180-degree reversals when possible."""
        possible_dirs = [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]

        # Prevent 180-degree turnbacks if alternatives exist
        opposites = {
            Direction.UP: Direction.DOWN, Direction.DOWN: Direction.UP,
            Direction.LEFT: Direction.RIGHT, Direction.RIGHT: Direction.LEFT,
        }

        opposite = opposites.get(ghost.direction)
        non_reversing = [d for d in possible_dirs if d != opposite]

        return random.choice(non_reversing if non_reversing else possible_dirs)

    def render(self) -> None:
        if self.state == GameState.MENU:
            self.ui.draw_menu(options=self.menu_options, selected_index=self.menu_index)

        elif self.state in (GameState.PLAYING, GameState.PAUSED, GameState.CONFIRM_QUIT):
            self.ui.clear()
            self.ui.draw_hud(self.score, self.player.lives, self.time_remaining, self.current_level)
            self.ui.draw_maze_border()
            self.ui.draw_board(self.board)
            self.ui.draw_grid_overlay(alpha=20)
            self.ui.draw_player(self.player)
            self.ui.draw_ghosts(self.ghosts)

            if self.state == GameState.PAUSED:
                self.ui.draw_pause()
            elif self.state == GameState.CONFIRM_QUIT:
                self.ui.draw_confirm_quit()

        self.ui.present()

    def run(self) -> None:
        running = True
        fps = 60
        dt = 1.0 / fps

        while running:
            running = self.handle_events()
            self.update(dt)
            self.render()

        self.ui.close()
