# -*- coding: utf-8 -*-
"""Session and Progress model.
Tracks career progress, unlocked plants/artifacts, seed selections, and options.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Session:
    current_level_idx: int = 0
    highest_level: int = 0
    unlocked_plants: set[str] = field(default_factory=lambda: {"sunflower", "peashooter"})
    unlocked_artifacts: set[str] = field(default_factory=set)
    endless_best_wave: int = 0

    # User preferences
    auto_sun_enabled: bool = True
    speed_multiplier: float = 1.0
    sound_enabled: bool = True
    music_enabled: bool = True
    is_fullscreen: bool = False

    # In-match ephemeral selection state
    selected_seeds: list[str] = field(default_factory=list)
    seed_cooldowns: dict[str, float] = field(default_factory=dict)
    active_seed_idx: Optional[int] = None
    active_shovel: bool = False
    game_mode: str = "menu"
    cob_targeting_col_row: Optional[tuple[int, int]] = None

    @property
    def max_seed_slots(self) -> int:
        # 倒数第二关打通后 (Level 14 completed -> highest_level >= 15 or master_belt unlocked) 变成 10 格
        if "master_belt" in self.unlocked_artifacts or self.highest_level >= 15:
            return 10
        # 倒数第四关打通后 (Level 12 completed -> highest_level >= 13 or belt_9 unlocked) 变成 9 格
        if "belt_9" in self.unlocked_artifacts or self.highest_level >= 13:
            return 9
        return 8

    @property
    def has_auto_sun(self) -> bool:
        """True if the player has unlocked the magnet artifact."""
        return "auto_sun_magnet" in self.unlocked_artifacts or self.highest_level >= 10
