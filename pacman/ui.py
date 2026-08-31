import os

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame  # noqa: E402
from pacman.entities import GhostMode, GhostState, PlayerState  # noqa: E402

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
                 title: str = "Pac-Man 42"
                 ) -> None:
        pygame.init()
        pygame.font.init()

        self.width_cells = width_cells
        self.height_cells = height_cells
        self.cell_size = cell_size

        self.screen_width = width_cells * self.cell_size
        self.screen_height = height_cells * self.cell_size + 40  # 40px HUD header

        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption(title)

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 18, bold=True)
        self.ghost_colors = [RED, PINK, CYAN, ORANGE]

    def clear(self) -> None:
        self.screen.fill(BLACK)

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
        radius = self.cell_size // 2 - 2
        pygame.draw.circle(self.screen, YELLOW, (px, py), radius)

    def draw_ghosts(self, ghosts: list[GhostState]) -> None:
        for ghost in ghosts:
            gx = ghost.position.x * self.cell_size + self.cell_size // 2
            gy = ghost.position.y * self.cell_size + self.cell_size // 2 + 40
            radius = self.cell_size // 2 - 2

            color = self.ghost_colors[ghost.id % len(self.ghost_colors)]
            if ghost.mode == GhostMode.FRIGHTENED:
                color = FRIGHTENED_BLUE
            elif ghost.mode == GhostMode.EATEN:
                color = WHITE

            pygame.draw.circle(self.screen, color, (gx, gy), radius)

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

    def draw_menu(self) -> None:
        self.clear()
        title_surf = self.font.render("PAC-MAN 42", True, YELLOW)
        play_surf = self.font.render("Press SPACE to Play", True, WHITE)
        quit_surf = self.font.render("Press Q to Quit", True, WHITE)

        cx = self.screen_width // 2
        self.screen.blit(title_surf, title_surf.get_rect(center=(cx, 100)))
        self.screen.blit(play_surf, play_surf.get_rect(center=(cx, 180)))
        self.screen.blit(quit_surf, quit_surf.get_rect(center=(cx, 220)))

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
