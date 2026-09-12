from pacman.ai.ghost_manager import GhostManager
from pacman.entities import Direction, GhostMode, GhostType, Vector2D
from pacman.entities.ghost import Ghost, init_ghosts
from pacman.entities.player import Player
from pacman.entities.state import GameState
from pacman.config import GameConfig
from pacman.adapters.maze import MazeAdapter
from pacman.entities.base import CellType
from pacman.ai.ghost_house import GhostHouseManager

import os
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
        self.score: int = 0
        self.lives = config.lives
        self.time_remaining = float(config.level_max_time)
        self.state = GameState.MENU
        self.menu_options = ["PLAY GAME", "OPTIONS", "QUIT"]
        self.menu_index = 0
        # Cheats
        self.cheat_invincible = False
        self.cheat_freeze_ghosts = False
        self.cheat_speed_boost: bool = False

        # Player setup
        self.player = Player(
            position=config.player_init_position,
            speed=config.player_speed)

        # Ghosts setup with Arcade home scatter corners and spawn positions
        self.ghosts: dict[GhostType, Ghost] = init_ghosts(
            config.width, config.height, config.ghost_speed)

        # Initialize GhostManager with all 4 ghosts
        self.ghost_manager = GhostManager(self.ghosts)
        self.ghost_house_mgr = GhostHouseManager(self.ghosts)

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
                        self.player.next_direction = Direction.UP
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.player.next_direction = Direction.DOWN
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        self.player.next_direction = Direction.LEFT
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        self.player.next_direction = Direction.RIGHT

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
        self.ui.update_anim_timer(dt)
        if self.state == GameState.PLAYING:
            self.time_remaining -= dt
        if self.time_remaining <= 0:
            self.state = GameState.GAME_OVER

        """Main game state tick called on every frame."""
        if self.state != GameState.PLAYING:
            return

        # 1. Advance Player position
        self.player.update(self.board, dt)

        # 2. Process Tile Consumption (Pac-gum & Super Pac-gum)
        self._check_tile_consumption()

        # 3. Advance Ghost Manager
        self.ghost_house_mgr.update(dt)

        self.ghost_manager.update(
            board=self.board,
            dt=dt,
            pacman_pos=self.player.position,
            pacman_dir=self.player.direction,
        )
        self._check_ghost_collisions()

    def _check_tile_consumption(self) -> None:
        px, py = self.player.grid_x, self.player.grid_y

        if 0 <= py < len(self.board) and 0 <= px < len(self.board[0]):
            cell = self.board[py][px]

            if cell & (CellType.SUPER_DOT | CellType.DOT):
                if cell & CellType.SUPER_DOT:
                    self.board[py][px] &= ~CellType.SUPER_DOT
                    self.score += 50
                    self.ghost_manager.trigger_frightened(duration=7.0)
                else:
                    self.board[py][px] &= ~CellType.DOT
                    self.score += 10

                # Notify house manager of dot eating
                self.ghost_house_mgr.on_dot_eaten()

    def _check_ghost_collisions(self) -> None:
        px, py = self.player.grid_x, self.player.grid_y

        for ghost in self.ghosts.values():
            if ghost.grid_x == px and ghost.grid_y == py:
                if ghost.mode == GhostMode.FRIGHTENED:
                    # Award progressive bonus: 200, 400, 800, 1600
                    points = self.ghost_manager.consume_frightened_ghost(ghost)
                    self.score += points

                elif ghost.mode in (GhostMode.CHASE, GhostMode.SCATTER):
                    # Pac-Man dies
                    self.player.lives -= 1
                    if self.player.lives <= 0:
                        self.state = GameState.GAME_OVER
                    else:
                        self.reset_positions()
                    break

    def reset_positions(self) -> None:
        """Resets entity positions after death or round restart."""
        self.player.position = Vector2D(x=9.0, y=15.0)
        self.player.direction = Direction.NONE
        self.player.next_direction = Direction.NONE

        spawn_positions = {
            GhostType.BLINKY: Vector2D(x=9.0, y=8.0),
            GhostType.PINKY: Vector2D(x=9.0, y=10.0),
            GhostType.INKY: Vector2D(x=8.0, y=10.0),
            GhostType.CLYDE: Vector2D(x=10.0, y=10.0),
        }

        for ghost_type, ghost in self.ghosts.items():
            ghost.position = spawn_positions[ghost_type]
            ghost.direction = Direction.NONE
            ghost.next_direction = Direction.NONE
            ghost.mode = GhostMode.CHASE

    def render(self) -> None:
        if self.state == GameState.MENU:
            self.ui.draw_menu(options=self.menu_options, selected_index=self.menu_index)

        elif self.state in (GameState.PLAYING, GameState.PAUSED, GameState.CONFIRM_QUIT):
            self.ui.clear()
            self.ui.draw_hud(self.score, self.player.lives, self.time_remaining, self.current_level)
            self.ui.draw_board(self.board, True)
            self.ui.draw_grid_overlay(alpha=0)
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
