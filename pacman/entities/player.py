from pacman.entities.base import BaseEntity, Vector2D


class Player(BaseEntity):
    """Player-controlled Pac-Man entity."""

    def __init__(self, position: Vector2D | None = None,
                 speed: float = 5.0, lives: int = 3) -> None:
        super().__init__(position=position, speed=speed)
        self.lives = lives

    def update(self, board: list[list[int]], dt: float) -> None:
        self.update_position(board, dt)
