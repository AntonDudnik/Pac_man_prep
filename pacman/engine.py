from enum import Enum, auto
import os

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame  # noqa: E402

from pacman.config import GameConfig  # noqa: E402
from pacman.entities import Direction, GhostMode, GhostState, PlayerState, Vector2D  # noqa: E402
from pacman.ui import PygameUI  # noqa: E402


class GameState(Enum):
    MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    VICTORY = auto()


class GameEngine:
    def __init__(self, config: GameConfig) -> None:
        self.config = config
        self.state = GameState.MENU
        self.ui = PygameUI(config.width, config.height, config.cell_size)

        self.current_level = 1
        self.score = 0
        self.lives = config.lives
        self.time_remaining = float(config.level_max_time)

        # Entities
        self.player = PlayerState(
            position=Vector2D(x=config.width // 2, y=config.height // 2),
            lives=config.lives,
            speed=config.player_speed,
        )
        self.ghosts = [
            GhostState(id=0, position=Vector2D(x=1, y=1), speed=config.ghost_speed),
            GhostState(id=1, position=Vector2D(x=config.width - 2, y=1), speed=config.ghost_speed),
            GhostState(id=2, position=Vector2D(x=1, y=config.height - 2), speed=config.ghost_speed),
            GhostState(id=3, position=Vector2D(x=config.width - 2, y=config.height - 2),
                       speed=config.ghost_speed),
        ]

        # Cheats
        self.cheat_invincible = False
        self.cheat_freeze_ghosts = False
        self.cheat_speed_boost: bool = False

    def handle_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if self.state == GameState.MENU:
                    if event.key == pygame.K_SPACE:
                        self.state = GameState.PLAYING
                    elif event.key == pygame.K_q:
                        return False

                elif self.state == GameState.PLAYING:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        self.player.direction = Direction.UP
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.player.direction = Direction.DOWN
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        self.player.direction = Direction.LEFT
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        self.player.direction = Direction.RIGHT
                    elif event.key == pygame.K_p:
                        self.state = GameState.PAUSED
                    # Cheats
                    elif event.key == pygame.K_i:
                        self.cheat_invincible = not self.cheat_invincible
                        print(f"[CHEAT] Invincible: {self.cheat_invincible}")
                    elif event.key == pygame.K_f:
                        self.cheat_freeze_ghosts = not self.cheat_freeze_ghosts
                        print(f"[CHEAT] Freeze: {self.cheat_freeze_ghosts}")
                    elif event.key == pygame.K_b:
                        self.cheat_speed_boost = not self.cheat_speed_boost
                        print(f"[CHEAT] Speed Boost: {self.cheat_speed_boost}")

                elif self.state == GameState.PAUSED:
                    if event.key == pygame.K_p:
                        self.state = GameState.PLAYING

        return True

    def update(self, dt: float) -> None:
        if self.state != GameState.PLAYING:
            return

        self.time_remaining -= dt
        if self.time_remaining <= 0:
            self.state = GameState.GAME_OVER

        # Apply speed multiplier (e.g., speed boost cheat)
        effective_speed = self.player.speed * (2.0 if self.cheat_speed_boost else 1.0)
        distance = effective_speed * dt

        # Move player continuously
        new_pos = self.player.position.move_continuous(self.player.direction, distance)

        # Clamp bounds placeholder
        px = max(1.0, min(float(self.config.width - 2), new_pos.x))
        py = max(1.0, min(float(self.config.height - 2), new_pos.y))
        self.player.position = Vector2D(x=px, y=py)

        # Move ghosts if not frozen by cheat
        if not self.cheat_freeze_ghosts:
            for ghost in self.ghosts:
                # Frightened ghosts move slower
                ghost_speed = ghost.speed * (0.5 if ghost.mode == GhostMode.FRIGHTENED else 1.0)
                g_dist = ghost_speed * dt
                ghost.position = ghost.position.move_continuous(ghost.direction, g_dist)

    def render(self) -> None:
        if self.state == GameState.MENU:
            self.ui.draw_menu()
        elif self.state in (GameState.PLAYING, GameState.PAUSED):
            self.ui.clear()
            self.ui.draw_hud(self.score, self.player.lives, self.time_remaining, self.current_level)
            self.ui.draw_maze_border()
            self.ui.draw_grid_overlay(alpha=20)
            self.ui.draw_player(self.player)
            self.ui.draw_ghosts(self.ghosts)
            if self.state == GameState.PAUSED:
                self.ui.draw_pause()

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
