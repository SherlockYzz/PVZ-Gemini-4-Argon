# -*- coding: utf-8 -*-
"""HUD Layout calculations.
Pure functions computing exact screen bounding boxes and hit areas for HUD elements.
"""

from dataclasses import dataclass
from typing import Optional
import pygame


@dataclass(frozen=True)
class HudRects:
    sun_counter: pygame.Rect
    card_slots: list[pygame.Rect]
    shovel_button: pygame.Rect
    speed_button: pygame.Rect
    pause_button: pygame.Rect
    skip_button: pygame.Rect
    auto_sun_toggle: pygame.Rect
    progress_bar: pygame.Rect


# Seed belt capacity is data-driven by Session.max_seed_slots (8 / 9 / 10).
MIN_HUD_SLOTS: int = 1
MAX_HUD_SLOTS: int = 10


def compute_hud_layout(max_slots: int = 8) -> HudRects:
    # Defensive clamp: a corrupted save or a future artifact must never produce
    # an empty/overlapping layout, since callers index card_slots by slot id.
    max_slots = max(MIN_HUD_SLOTS, min(MAX_HUD_SLOTS, int(max_slots)))

    sun_counter = pygame.Rect(10, 8, 118, 76)

    card_slots = []
    for i in range(max_slots):
        x = 136 + i * 70
        y = 6
        card_slots.append(pygame.Rect(x, y, 66, 80))

    shovel_x = 136 + max_slots * 70 + 12
    shovel_btn = pygame.Rect(shovel_x, 10, 62, 70)

    # Top right controls bar (speed, pause, skip warp, auto sun)
    speed_btn = pygame.Rect(920, 10, 48, 36)
    pause_btn = pygame.Rect(974, 10, 52, 36)
    skip_btn = pygame.Rect(1032, 10, 56, 36)
    auto_sun_btn = pygame.Rect(1094, 10, 96, 36)

    progress_bar = pygame.Rect(760, 722, 220, 20)

    return HudRects(
        sun_counter=sun_counter,
        card_slots=card_slots,
        shovel_button=shovel_btn,
        speed_button=speed_btn,
        pause_button=pause_btn,
        skip_button=skip_btn,
        auto_sun_toggle=auto_sun_btn,
        progress_bar=progress_bar,
    )
