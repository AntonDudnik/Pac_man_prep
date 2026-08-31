from pacman.ui import PygameUI
from pacman.entities import GhostState, PlayerState, Vector2D
import os

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
os.environ["SDL_VIDEODRIVER"] = "dummy"  # Headless mode for CI/unit tests


def test_ui_headless_initialization() -> None:
    ui = PygameUI(19, 21)
    ui.clear()
    ui.draw_hud(100, 3, 90.0, 1)
    ui.draw_maze_border()

    player = PlayerState(position=Vector2D(x=9, y=10))
    ghosts = [GhostState(id=0, position=Vector2D(x=1, y=1))]

    ui.draw_player(player)
    ui.draw_ghosts(ghosts)
    ui.close()
