from pacman.config import GameConfig
from pacman.entities.base import BaseEntity


class Player(BaseEntity):
    """Player-controlled Pac-Man entity."""

    def __init__(self, config: GameConfig) -> None:
        super().__init__(config=config)
        self.speed = config.player_speed
        self.position = config.player_init_position
        self.lives = config.lives

    def update(self, board: list[list[int]], dt: float) -> None:
        self.update_position(board, dt)
