import os
import sys
from typing import List
from pacman.entities import GhostState, PlayerState
from pacman.spritesheet import AnimationManager, SpriteSheet

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame  # noqa: E402

# Color Constants (RGB)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (33, 33, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
PINK = (252, 181, 255)
CYAN = (0, 255, 255)
ORANGE = (253, 161, 37)
FRIGHTENED_BLUE = (33, 33, 222)


class PygameUI:
    """Encapsulated UI rendering wrapper following MLX equivalence patterns."""

    def __init__(self, width_cells: int, height_cells: int, cell_size: int = 24,
                 spritesheet_path: str = "assets/spritesheet.png", title: str = "Pac-Man 42"
                 ) -> None:
        pygame.init()
        pygame.font.init()

        self.width_cells = width_cells
        self.height_cells = height_cells
        self.cell_size = cell_size
        self.anim_time = 0.0

        self.screen_width = width_cells * self.cell_size
        self.screen_height = height_cells * self.cell_size + 40  # 40px HUD header

        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption(title)

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 18, bold=True)
        self.ghost_colors = [RED, PINK, CYAN, ORANGE]
        self.animations: AnimationManager | None = None
        try:
            sheet = SpriteSheet(spritesheet_path, target_size=cell_size)
            self.animations = AnimationManager(sheet)
        except Exception as e:
            print(
                f"[WARN] Could not load spritesheet ('{spritesheet_path}'): {e}. "
                "Falling back to shapes.",
                file=sys.stderr,
            )

    def clear(self) -> None:
        self.screen.fill(BLACK)

    def update_anim_timer(self, dt: float) -> None:
        self.anim_time += dt

    def draw_hud(self, score: int, lives: int, time_left: float, level: int) -> None:
        hud_text = f"SCORE:{score:04d}  LIVES:{lives}  TIME:{int(time_left):02d}s  LVL:{level}"
        surface = self.font.render(hud_text, True, WHITE)
        self.screen.blit(surface, (10, 10))

    def draw_maze_border(self) -> None:
        top_offset = 40
        # Draw outer bounding box for empty maze placeholder
        rect = pygame.Rect(0, top_offset, self.screen_width, self.screen_height - top_offset)
        pygame.draw.rect(self.screen, BLUE, rect, width=3)

    def draw_player(self, player: PlayerState) -> None:
        px = player.position.x * self.cell_size + self.cell_size // 2
        py = player.position.y * self.cell_size + self.cell_size // 2 + 40
        if self.animations:
            sprite = self.animations.get_pacman_sprite(
                player.direction, self.anim_time
            )
            self.screen.blit(sprite, (px, py))
        else:
            # Geometric circle fallback
            cx = px + self.cell_size // 2
            cy = py + self.cell_size // 2
            pygame.draw.circle(self.screen, YELLOW, (cx, cy), self.cell_size // 2 - 2)

    def draw_ghosts(self, ghosts: List[GhostState]) -> None:
        """Render ghosts using animation frames if available, otherwise fallback to shapes."""
        # Vertical offset to account for top HUD/score bar height
        hud_offset_y = 40

        for ghost in ghosts:
            gx = int(ghost.position.x * self.cell_size)
            gy = int(ghost.position.y * self.cell_size) + hud_offset_y

            # Try loading sprite from animation manager (checking both variable names)
            anim_mgr = getattr(self, "animations", None) or getattr(self, "anim_manager", None)

            if anim_mgr:
                anim_time = getattr(self, "anim_time", getattr(self, "anim_timer", 0.0))
                sprite = anim_mgr.get_ghost_sprite(
                    ghost_id=ghost.id,
                    mode=ghost.mode,
                    direction=ghost.direction,
                    anim_time=anim_time,
                    frightened_timer=ghost.frightened_timer,
                )
                self.screen.blit(sprite, (gx, gy))
            else:
                # Geometric fallback shape rendering
                cx = gx + self.cell_size // 2
                cy = gy + self.cell_size // 2
                color = self.ghost_colors[ghost.id % len(self.ghost_colors)]
                pygame.draw.circle(self.screen, color, (cx, cy), self.cell_size // 2 - 2)

    def draw_grid_overlay(self, alpha: int = 50) -> None:
        """Draw a semi-transparent grid overlay for visual testing and debugging."""
        # Create a transparent surface matching screen dimensions
        grid_surface = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        grid_color = (255, 255, 255, alpha)  # White with custom alpha transparency

        top_offset = 40

        # Draw vertical grid lines
        for x in range(0, self.screen_width + 1, self.cell_size):
            pygame.draw.line(grid_surface, grid_color, (x, top_offset), (x, self.screen_height))

        # Draw horizontal grid lines
        for y in range(top_offset, self.screen_height + 1, self.cell_size):
            pygame.draw.line(grid_surface, grid_color, (0, y), (self.screen_width, y))

        # Blit grid onto the main display
        self.screen.blit(grid_surface, (0, 0))

    def draw_confirm_quit(self) -> None:
        """Render a semi-transparent dialog overlay prompting quit confirmation."""
        # 1. Darken background screen
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # 70% black alpha blend
        self.screen.blit(overlay, (0, 0))

        # 2. Centered Dialog Box Dimensions
        box_w, box_h = 320, 140
        box_x = (self.screen_width - box_w) // 2
        box_y = (self.screen_height - box_h) // 2

        # Draw Dialog Border & Background
        pygame.draw.rect(self.screen, (20, 20, 40), (box_x, box_y, box_w, box_h), border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 255), (box_x, box_y,
                         box_w, box_h), width=2, border_radius=8)

        # 3. Dialog Text Prompts
        msg_surf = self.font.render("QUIT GAME?", True, (255, 255, 0))
        opts_surf = self.font.render("[Y] YES   /   [N] NO", True, (255, 255, 255))

        self.screen.blit(msg_surf, msg_surf.get_rect(center=(self.screen_width // 2, box_y + 40)))
        self.screen.blit(opts_surf, opts_surf.get_rect(center=(self.screen_width // 2, box_y + 90)))

    def draw_menu(
        self,
        options: list[str] = ["PLAY GAME", "OPTIONS", "QUIT"],
        selected_index: int = 0
    ) -> None:
        self.clear()

        cx = self.screen_width // 2

        # 1. Title Banner
        title_surf = self.font.render("PAC-MAN 42", True, (255, 255, 0))  # Yellow
        self.screen.blit(title_surf, title_surf.get_rect(center=(cx, 80)))

        # 2. Render Menu Options
        start_y = 160
        line_spacing = 40

        for idx, option_text in enumerate(options):
            y_pos = start_y + (idx * line_spacing)
            is_selected = (idx == selected_index)

            # Highlight selected item in yellow, unselected in white
            color = (255, 255, 0) if is_selected else (255, 255, 255)
            text_surf = self.font.render(option_text, True, color)
            rect = text_surf.get_rect(center=(cx, y_pos))

            self.screen.blit(text_surf, rect)

            # Draw Arcade Selection Cursor ('>' arrow or indicator block)
            if is_selected:
                cursor_surf = self.font.render(">", True, (255, 255, 0))
                cursor_rect = cursor_surf.get_rect(right=rect.left - 15, centery=rect.centery)
                self.screen.blit(cursor_surf, cursor_rect)

        # 3. Footer Control Hints
        hint_surf = self.font.render("USE UP/DOWN & ENTER TO SELECT", True, (150, 150, 150))
        self.screen.blit(hint_surf, hint_surf.get_rect(center=(cx, self.screen_height - 30)))

    def draw_pause(self) -> None:
        pause_surf = self.font.render("PAUSED - Press P to Resume", True, YELLOW)
        cx = self.screen_width // 2
        cy = self.screen_height // 2
        self.screen.blit(pause_surf, pause_surf.get_rect(center=(cx, cy)))

    def present(self) -> None:
        pygame.display.flip()
        self.clock.tick(60)

    def close(self) -> None:
        pygame.quit()
