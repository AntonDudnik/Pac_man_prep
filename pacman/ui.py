import os
import sys
from typing import Dict, List, Union

from pacman.spritesheet import AnimationManager, SpriteSheet
from pacman.entities import GhostType, CellType, Player, Ghost

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame  # noqa: E402

# Board & UI Constants
HUD_HEIGHT: int = 40
WALL_THICKNESS: int = 1

# Color Constants (RGB)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (33, 33, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
PINK = (252, 181, 255)
CYAN = (0, 255, 255)
ORANGE = (253, 161, 37)

# Debug Colors (Semi-transparent / distinct)
GHOST_HOUSE_COLOR = (70, 0, 120)  # Purple
GATE_COLOR = (255, 184, 255)       # Pink Gate Line
OBSTACLE_42_COLOR = (40, 40, 40)   # Dark Gray for solid '42' blocks (value 15)
PELLET_COLOR = (255, 183, 174)


class PygameUI:
    """Encapsulated UI rendering wrapper following MLX equivalence patterns."""

    def __init__(
        self,
        width_cells: int,
        height_cells: int,
        cell_size: int,
        spritesheet_path: str = "assets/spritesheet.png",
        title: str = "Pac-Man 42",
    ) -> None:
        pygame.init()
        pygame.font.init()

        self.width_cells = width_cells
        self.height_cells = height_cells
        self.cell_size = cell_size
        self.anim_time = 0.0

        # Add WALL_THICKNESS buffer so outer right & bottom wall edges are fully visible
        self.screen_width = width_cells * self.cell_size + WALL_THICKNESS
        self.screen_height = height_cells * self.cell_size + HUD_HEIGHT + WALL_THICKNESS

        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption(title)

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 18, bold=True)
        self.ghost_colors = [RED, PINK, CYAN, ORANGE]
        self.animations: AnimationManager | None = None
        try:
            sheet = SpriteSheet(spritesheet_path, target_size=cell_size - WALL_THICKNESS - 2)
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
        hud_text = (
            f"SCORE:{score:04d}  LIVES:{lives}  TIME:{int(time_left):02d}s  LVL:{level}"
        )
        surface = self.font.render(hud_text, True, WHITE)
        self.screen.blit(surface, (10, 10))

    def draw_board(self, board: list[list[int]], debug: bool = True) -> None:
        cs = self.cell_size

        for y, row in enumerate(board):
            for x, cell in enumerate(row):
                left = x * cs
                top = y * cs + HUD_HEIGHT
                right = left + cs
                bottom = top + cs
                cx, cy = left + cs // 2, top + cs // 2

                # --- DEBUG VISUAL OVERLAYS ---
                if debug:
                    # Highlight Ghost Box interior tiles
                    if cell & CellType.GHOST_HOUSE:  # GHOST_HOUSE
                        pygame.draw.rect(self.screen, GHOST_HOUSE_COLOR, (left, top, cs, cs))

                    # Highlight Ghost Gate door tile
                    if cell & CellType.GATE:  # GATE
                        pygame.draw.rect(self.screen, GATE_COLOR, (left, top, cs, cs))

                    # Highlight solid '42' maze generator obstacles (raw code 15)
                    if (cell & 15) == 15:
                        pygame.draw.rect(self.screen, OBSTACLE_42_COLOR, (left, top, cs, cs))

                # 1. Render Pellets
                if cell & CellType.DOT:  # DOT
                    if self.animations and hasattr(self.animations.sheet, "wall_sprites"):
                        sprite = self.animations.sheet.wall_sprites.get("dot")
                        if sprite:
                            self.screen.blit(sprite, (left, top))
                        else:
                            pygame.draw.circle(self.screen, PELLET_COLOR, (cx, cy), 3)
                    else:
                        pygame.draw.circle(self.screen, PELLET_COLOR, (cx, cy), 3)
                elif cell & CellType.SUPER_DOT:  # SUPER_DOT
                    if self.animations and hasattr(self.animations.sheet, "wall_sprites"):
                        sprite = self.animations.sheet.wall_sprites.get("super_dot")
                        if sprite:
                            self.screen.blit(sprite, (left, top))
                        else:
                            pygame.draw.circle(self.screen, PELLET_COLOR, (cx, cy), 7)
                    else:
                        pygame.draw.circle(self.screen, PELLET_COLOR, (cx, cy), 7)

                # 2. Render Wall Lines using top-level constant
                if cell & CellType.NORTH:  # NORTH
                    pygame.draw.line(self.screen, BLUE, (left, top), (right, top), WALL_THICKNESS)
                if cell & CellType.EAST:  # EAST
                    pygame.draw.line(self.screen, BLUE, (right, top),
                                     (right, bottom), WALL_THICKNESS)
                if cell & CellType.SOUTH:  # SOUTH
                    pygame.draw.line(self.screen, BLUE, (left, bottom),
                                     (right, bottom), WALL_THICKNESS)
                if cell & CellType.WEST:  # WEST
                    pygame.draw.line(self.screen, BLUE, (left, top), (left, bottom), WALL_THICKNESS)

    def draw_player(self, player: Player) -> None:
        px = int(player.position.x * self.cell_size + WALL_THICKNESS // 2 + 2)
        py = int(player.position.y * self.cell_size + WALL_THICKNESS // 2 + 2) + HUD_HEIGHT

        if self.animations:
            sprite = self.animations.get_pacman_sprite(player.direction, self.anim_time)
            self.screen.blit(sprite, (px, py))
        else:
            cx = px + self.cell_size // 2
            cy = py + self.cell_size // 2
            pygame.draw.circle(self.screen, YELLOW, (cx, cy), self.cell_size // 2 - 2)

    def draw_ghosts(self, ghosts: Union[Dict[GhostType, Ghost], List[Ghost]]) -> None:
        ghost_list = ghosts.values() if isinstance(ghosts, dict) else ghosts

        for ghost in ghost_list:
            gx = int(ghost.position.x * self.cell_size + WALL_THICKNESS // 2 + 2)
            gy = int(ghost.position.y * self.cell_size + WALL_THICKNESS // 2 + 2) + HUD_HEIGHT

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
                cx = gx + self.cell_size // 2
                cy = gy + self.cell_size // 2
                color = self.ghost_colors[ghost.id % len(self.ghost_colors)]
                pygame.draw.circle(self.screen, color, (cx, cy), self.cell_size // 2 - 2)

    def draw_grid_overlay(self, alpha: int = 50) -> None:
        grid_surface = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        grid_color = (255, 255, 255, alpha)
        top_offset = 40

        for x in range(0, self.screen_width + 1, self.cell_size):
            pygame.draw.line(grid_surface, grid_color, (x, top_offset), (x, self.screen_height))

        for y in range(top_offset, self.screen_height + 1, self.cell_size):
            pygame.draw.line(grid_surface, grid_color, (0, y), (self.screen_width, y))

        self.screen.blit(grid_surface, (0, 0))

    def draw_confirm_quit(self) -> None:
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        box_w, box_h = 320, 140
        box_x = (self.screen_width - box_w) // 2
        box_y = (self.screen_height - box_h) // 2

        pygame.draw.rect(self.screen, (20, 20, 40), (box_x, box_y, box_w, box_h), border_radius=8)
        pygame.draw.rect(
            self.screen, (255, 255, 255), (box_x, box_y, box_w, box_h), width=2, border_radius=8,
        )

        msg_surf = self.font.render("QUIT GAME?", True, (255, 255, 0))
        opts_surf = self.font.render("[Y] YES   /   [N] NO", True, (255, 255, 255))

        self.screen.blit(
            msg_surf, msg_surf.get_rect(center=(self.screen_width // 2, box_y + 40))
        )
        self.screen.blit(
            opts_surf, opts_surf.get_rect(center=(self.screen_width // 2, box_y + 90))
        )

    def draw_menu(
        self,
        options: list[str] = ["PLAY GAME", "OPTIONS", "QUIT"],
        selected_index: int = 0,
    ) -> None:
        self.clear()
        cx = self.screen_width // 2

        title_surf = self.font.render("PAC-MAN 42", True, (255, 255, 0))
        self.screen.blit(title_surf, title_surf.get_rect(center=(cx, 80)))

        start_y = 160
        line_spacing = 40

        for idx, option_text in enumerate(options):
            y_pos = start_y + (idx * line_spacing)
            is_selected = idx == selected_index

            color = (255, 255, 0) if is_selected else (255, 255, 255)
            text_surf = self.font.render(option_text, True, color)
            rect = text_surf.get_rect(center=(cx, y_pos))

            self.screen.blit(text_surf, rect)

            if is_selected:
                cursor_surf = self.font.render(">", True, (255, 255, 0))
                cursor_rect = cursor_surf.get_rect(
                    right=rect.left - 15, centery=rect.centery
                )
                self.screen.blit(cursor_surf, cursor_rect)

        hint_surf = self.font.render(
            "USE UP/DOWN & ENTER TO SELECT", True, (150, 150, 150)
        )
        self.screen.blit(
            hint_surf,
            hint_surf.get_rect(center=(cx, self.screen_height - 30)),
        )

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
