"""Global Scatter/Chase wave timer state manager."""

from dataclasses import dataclass, field
from enum import Enum, auto


class GlobalWaveMode(Enum):
    SCATTER = auto()
    CHASE = auto()


@dataclass
class WaveTimer:
    """Tracks global Arcade wave schedules (Level 1 defaults)."""

    # Typical Level 1 schedule in seconds: Scatter 7s, Chase 20s, Scatter 7s, Chase 20s...
    schedule: list[tuple[GlobalWaveMode, float]] = field(
        default_factory=lambda: [
            (GlobalWaveMode.SCATTER, 7.0),
            (GlobalWaveMode.CHASE, 20.0),
            (GlobalWaveMode.SCATTER, 7.0),
            (GlobalWaveMode.CHASE, 20.0),
            (GlobalWaveMode.SCATTER, 5.0),
            (GlobalWaveMode.CHASE, 20.0),
            (GlobalWaveMode.SCATTER, 5.0),
            (GlobalWaveMode.CHASE, float("inf")),  # Permanent Chase wave 4
        ]
    )

    current_wave_idx: int = 0
    time_in_wave: float = 0.0

    @property
    def current_mode(self) -> GlobalWaveMode:
        return self.schedule[self.current_wave_idx][0]

    def update(self, dt: float) -> bool:
        """Ticks the wave timer. Returns True if a mode transition occurred."""
        mode, duration = self.schedule[self.current_wave_idx]
        if duration == float("inf"):
            return False

        self.time_in_wave += dt
        if self.time_in_wave >= duration:
            self.time_in_wave = 0.0
            if self.current_wave_idx < len(self.schedule) - 1:
                self.current_wave_idx += 1
                return True
        return False
