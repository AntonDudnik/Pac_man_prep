import os
import pygame
from typing import Dict, List, Tuple
from pacman.entities import Direction, GhostMode

# ==============================================================================
# TOP-LEVEL SPRITESHEET GEOMETRY CONSTANTS
# ==============================================================================
FONT_TILE_SIZE: int = 8
FONT_LINE_THICKNESS: int = 1
FONT_STRIDE: int = FONT_TILE_SIZE + FONT_LINE_THICKNESS  # 9px
FONT_SECTION_HEIGHT: int = (9 * FONT_STRIDE) + 1         # 82px

MIDDLE_SEPARATOR_Y: int = 1  # Divider line between top & bottom sections

ENTITY_TILE_SIZE: int = 16
ENTITY_LINE_THICKNESS: int = 1
ENTITY_STRIDE: int = ENTITY_TILE_SIZE + ENTITY_LINE_THICKNESS  # 18px

BOTTOM_SECTION_OFFSET_Y: int = FONT_SECTION_HEIGHT + MIDDLE_SEPARATOR_Y  # 84px
BOTTOM_SECTION_OFFSET_X: int = 1  # 1px border margin

PALETTE_BLOCK_WIDTH: int = 22 * FONT_STRIDE + 2
PALETTE_BLOCK_HEIGHT: int = 9 * FONT_STRIDE + 6 * ENTITY_STRIDE + 3
# ==============================================================================


class SpriteSheet:
    def __init__(
        self,
        filename: str = "assets/spritesheet.png",
        target_size: int = 24,
        tile_pixel_size: int = 8,
        default_palette: Tuple[int, int] = (2, 1),
    ) -> None:
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Spritesheet file not found: {filename}")

        self.sheet = pygame.image.load(filename).convert_alpha()
        self.sheet.set_colorkey((0, 0, 0))
        self.target_size = target_size
        self.current_palette = default_palette
        self._tile_cache: Dict[Tuple[int, int, int, int, int, str], pygame.Surface] = {}

        # Pre-cache dictionary for wall and pellet surfaces
        self.wall_sprites: Dict[str, pygame.Surface] = {}

    def set_palette(self, palette_coord: Tuple[int, int]) -> None:
        """Update active palette coordinate (col, row)."""
        self.current_palette = palette_coord

    def get_font_tile(self, col: int, row: int) -> pygame.Surface:
        """Extract an 8x8 font/maze tile using current_palette offset (top section)."""
        cache_key = (col, row, self.current_palette[0],
                     self.current_palette[1], self.target_size, "font")
        if cache_key in self._tile_cache:
            return self._tile_cache[cache_key]

        block_x = self.current_palette[0] * PALETTE_BLOCK_WIDTH
        block_y = self.current_palette[1] * PALETTE_BLOCK_HEIGHT

        # Font/Maze grid uses 1px margin + FONT_STRIDE (9px) spacing
        x = block_x + (col * FONT_STRIDE) + 1
        y = block_y + (row * FONT_STRIDE) + 1

        rect = pygame.Rect(x, y, FONT_TILE_SIZE, FONT_TILE_SIZE)
        image = pygame.Surface((FONT_TILE_SIZE, FONT_TILE_SIZE), pygame.SRCALPHA)
        image.blit(self.sheet, (0, 0), rect)

        scaled_image = pygame.transform.scale(image, (self.target_size, self.target_size))
        self._tile_cache[cache_key] = scaled_image
        return scaled_image

    def get_entity_tile(self, col: int, row: int) -> pygame.Surface:
        """Extract a 16x16 tile using current_palette state (with caching)."""
        cache_key = (col, row, self.current_palette[0],
                     self.current_palette[1], self.target_size, "entity")
        if cache_key in self._tile_cache:
            return self._tile_cache[cache_key]

        block_x = self.current_palette[0] * PALETTE_BLOCK_WIDTH
        block_y = self.current_palette[1] * PALETTE_BLOCK_HEIGHT

        x = block_x + BOTTOM_SECTION_OFFSET_X + (col * ENTITY_STRIDE)
        y = block_y + BOTTOM_SECTION_OFFSET_Y + (row * ENTITY_STRIDE)

        rect = pygame.Rect(x, y, ENTITY_TILE_SIZE, ENTITY_TILE_SIZE)
        image = pygame.Surface((ENTITY_TILE_SIZE, ENTITY_TILE_SIZE), pygame.SRCALPHA)
        image.blit(self.sheet, (0, 0), rect)

        scaled_image = pygame.transform.scale(image, (self.target_size, self.target_size))
        self._tile_cache[cache_key] = scaled_image
        return scaled_image


class AnimationManager:
    def __init__(self, spritesheet: SpriteSheet) -> None:
        self.sheet = spritesheet
        self._load_pacman_frames()
        self._load_ghost_frames()

    def _load_pacman_frames(self) -> None:
        self.sheet.set_palette((1, 3))
        closed = self.sheet.get_entity_tile(col=6, row=5)

        right_half = self.sheet.get_entity_tile(col=6, row=4)
        right_wide = self.sheet.get_entity_tile(col=6, row=3)

        down_half = self.sheet.get_entity_tile(col=7, row=4)
        down_wide = self.sheet.get_entity_tile(col=7, row=3)

        left_half = pygame.transform.flip(right_half, True, False)
        left_wide = pygame.transform.flip(right_wide, True, False)

        up_half = pygame.transform.flip(down_half, False, True)
        up_wide = pygame.transform.flip(down_wide, False, True)

        self.pacman_frames: Dict[Direction, List[pygame.Surface]] = {
            Direction.RIGHT: [closed, right_half, right_wide, right_half],
            Direction.LEFT:  [closed, left_half,  left_wide,  left_half],
            Direction.DOWN:  [closed, down_half,  down_wide,  down_half],
            Direction.UP:    [closed, up_half,    up_wide,    up_half],
            Direction.NONE:  [closed, right_half, right_wide, right_half],
        }

    def _load_ghost_frames(self) -> None:
        self.ghost_frames: Dict[int, Dict[Direction, List[pygame.Surface]]] = {}
        ghost_palettes = [(0, 0), (1, 0), (2, 0), (3, 0)]

        dir_cols = {
            Direction.RIGHT: ((0, 0), (0, 1)),
            Direction.LEFT:  ((0, 4), (0, 5)),
            Direction.UP:    ((0, 6), (0, 7)),
            Direction.DOWN:  ((0, 2), (0, 3)),
            Direction.NONE:  ((0, 0), (0, 1)),
        }

        for ghost_id in range(4):
            self.ghost_frames[ghost_id] = {}
            self.sheet.set_palette(ghost_palettes[ghost_id])

            for direction, (f1_pos, f2_pos) in dir_cols.items():
                f1 = self.sheet.get_entity_tile(col=f1_pos[1], row=f1_pos[0])
                f2 = self.sheet.get_entity_tile(col=f2_pos[1], row=f2_pos[0])
                self.ghost_frames[ghost_id][direction] = [f1, f2]

        # 2. Frightened Blue Frames (Palette 2, Row 5, Cols 0 & 1)
        self.sheet.set_palette((2, 0))
        self.frightened_frames = [
            self.sheet.get_entity_tile(col=0, row=5),
            self.sheet.get_entity_tile(col=1, row=5),
        ]
        # 3. Frightened Flashing White Frames (Palette 0, Row 5, Cols 0 & 1)
        self.sheet.set_palette((0, 0))
        self.frightened_white_frames = [
            self.sheet.get_entity_tile(col=0, row=5),
            self.sheet.get_entity_tile(col=1, row=5),
        ]

        # 4. Eaten Eyes Only (Palette 0, Row 5, Cols 2..5)
        self.sheet.set_palette((1, 1))
        self.eaten_frames: Dict[Direction, pygame.Surface] = {
            Direction.RIGHT: self.sheet.get_entity_tile(col=0, row=0),
            Direction.LEFT:  self.sheet.get_entity_tile(col=4, row=0),
            Direction.UP:    self.sheet.get_entity_tile(col=6, row=0),
            Direction.DOWN:  self.sheet.get_entity_tile(col=2, row=0),
            Direction.NONE:  self.sheet.get_entity_tile(col=0, row=0),
        }

    def get_pacman_sprite(self, direction: Direction, anim_time: float) -> pygame.Surface:
        frames = self.pacman_frames.get(direction, self.pacman_frames[Direction.NONE])
        return frames[int(anim_time / 0.08) % len(frames)]

    def get_ghost_sprite(
        self,
        ghost_id: int,
        mode: GhostMode,
        direction: Direction,
        anim_time: float,
        frightened_timer: float = 0.0,
    ) -> pygame.Surface:
        # Eaten mode: Return directional eyes
        if mode == GhostMode.EATEN:
            return self.eaten_frames.get(direction, self.eaten_frames[Direction.RIGHT])

        # Frightened mode: Flash white/blue when timer is running low (< 2.0s)
        if mode == GhostMode.FRIGHTENED:
            if frightened_timer > 0 and frightened_timer <= 2.0:
                # Flash between white and blue every 0.2s
                is_white = int(anim_time / 0.2) % 2 == 0
                frames = self.frightened_white_frames if is_white else self.frightened_frames
            else:
                frames = self.frightened_frames

            return frames[int(anim_time / 0.15) % len(frames)]

        # Normal Chase/Scatter mode
        frames = self.ghost_frames[ghost_id % 4].get(
            direction, self.ghost_frames[ghost_id % 4][Direction.RIGHT]
        )
        return frames[int(anim_time / 0.15) % len(frames)]
