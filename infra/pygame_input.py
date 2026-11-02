# -*- coding: utf-8 -*-
"""Input handler and semantic event translator.
Converts raw Pygame hardware events into clean high-level game actions.
"""

from dataclasses import dataclass
from typing import Optional, Literal
import pygame
from infra.pygame_viewport import Viewport


@dataclass
class InputEvent:
    kind: Literal["click", "right_click", "move", "key", "fullscreen", "quit"]
    x: float = 0.0
    y: float = 0.0
    key_name: str = ""
    seed_slot: Optional[int] = None


class InputHandler:
    def __init__(self, viewport: Viewport):
        self.viewport = viewport
        self.mouse_x = 0.0
        self.mouse_y = 0.0

    def poll_events(self) -> list[InputEvent]:
        events: list[InputEvent] = []

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                events.append(InputEvent(kind="quit"))

            elif e.type == pygame.VIDEORESIZE:
                self.viewport.handle_resize(e.w, e.h)

            elif e.type == pygame.KEYDOWN:
                # F11 or Alt+Enter toggles fullscreen
                if e.key == pygame.K_F11 or (e.key == pygame.K_RETURN and (e.mod & pygame.KMOD_ALT)):
                    events.append(InputEvent(kind="fullscreen"))
                elif pygame.K_1 <= e.key <= pygame.K_9:
                    slot = e.key - pygame.K_1
                    events.append(InputEvent(kind="key", key_name=f"slot_{slot}", seed_slot=slot))
                elif e.key == pygame.K_0:
                    events.append(InputEvent(kind="key", key_name="slot_9", seed_slot=9))
                elif e.key == pygame.K_s:
                    events.append(InputEvent(kind="key", key_name="shovel"))
                elif e.key == pygame.K_a:
                    events.append(InputEvent(kind="key", key_name="auto_sun"))
                elif e.key in (pygame.K_SPACE, pygame.K_p):
                    events.append(InputEvent(kind="key", key_name="pause"))
                elif e.key == pygame.K_ESCAPE:
                    events.append(InputEvent(kind="key", key_name="escape"))
                elif e.key in (pygame.K_TAB, pygame.K_n, pygame.K_RIGHTBRACKET):
                    events.append(InputEvent(kind="key", key_name="skip_next"))
                elif e.key in (pygame.K_LEFTBRACKET, pygame.K_PAGEUP):
                    events.append(InputEvent(kind="key", key_name="skip_prev"))
                elif e.key == pygame.K_l:
                    events.append(InputEvent(kind="key", key_name="toggle_warp"))

            elif e.type == pygame.MOUSEMOTION:
                lx, ly = self.viewport.window_to_logical(e.pos[0], e.pos[1])
                self.mouse_x, self.mouse_y = lx, ly
                events.append(InputEvent(kind="move", x=lx, y=ly))

            elif e.type == pygame.MOUSEBUTTONDOWN:
                lx, ly = self.viewport.window_to_logical(e.pos[0], e.pos[1])
                if e.button == 1:
                    events.append(InputEvent(kind="click", x=lx, y=ly))
                elif e.button == 3:
                    events.append(InputEvent(kind="right_click", x=lx, y=ly))

        return events
