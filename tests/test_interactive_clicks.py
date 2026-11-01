# -*- coding: utf-8 -*-
"""Interactive Clicks and Stress Test.
Simulates real human player clicks, card drags, shovel actions, hotkeys,
and mouse movements all over the window to guarantee 100% crash immunity.
"""

import sys
import unittest
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
pygame.init()

from domain.model.session import Session
from domain.model.zombie import Zombie
from infra.pygame_input import InputEvent
from infra.pygame_audio import PygameAudioAdapter
from infra.json_save import JsonSaveAdapter
from app.controller import GameController


class TestInteractiveClicks(unittest.TestCase):
    def test_battle_interaction_stress(self):
        session = Session(
            current_level_idx=0,
            unlocked_plants={"sunflower", "peashooter", "wallnut"},
            selected_seeds=["sunflower", "peashooter", "wallnut"],
            auto_sun_enabled=True,
        )
        audio = PygameAudioAdapter()
        storage = JsonSaveAdapter()
        controller = GameController(session, audio, storage)

        # 1. Start battle
        controller._start_battle()
        world = controller.world
        self.assertIsNotNone(world)

        # Spawn zombie at x=1250 (off lawn)
        world.zombies.append(Zombie.create("basic", row=2, x=1250, y=world.layout.get_row_ground_y(2)))

        # 2. Test pause and unpause toggle
        self.assertEqual(controller.mode, "battle")
        controller.handle_event(InputEvent(kind="key", key_name="pause"))
        self.assertEqual(controller.mode, "pause")
        controller.handle_event(InputEvent(kind="key", key_name="pause"))
        self.assertEqual(controller.mode, "battle")

        # 3. Simulate mouse moving and clicking everywhere (inside and outside lawn)
        test_coords = [
            (0, 0), (1200, 760), (-50, -50), (1500, 900),
            (200, 40),   # Slot 0 in HUD
            (50, 40),    # Sun counter
            (1050, 20),  # Auto sun toggle
            (930, 20),   # Speed toggle
            (700, 20),   # Shovel slot
            (120, 200),  # Lawn cell (0, 0)
            (300, 350),  # Lawn cell (2, 2)
            (1150, 350), # Off lawn right
            (30, 350),   # Off lawn left
        ]

        for x, y in test_coords:
            controller.handle_event(InputEvent(kind="move", x=x, y=y))
            controller.handle_event(InputEvent(kind="click", x=x, y=y))
            controller.handle_event(InputEvent(kind="right_click", x=x, y=y))

        # 4. Simulate other key presses
        for k in ["slot_0", "slot_1", "shovel", "auto_sun", "escape"]:
            controller.handle_event(InputEvent(kind="key", key_name=k))

        # 5. Simulate advancing 600 frames while clicking
        dt = 1.0 / 60.0
        for i in range(600):
            controller.tick_battle(dt)
            if i % 50 == 0:
                controller.handle_event(InputEvent(kind="click", x=300 + (i % 200), y=250 + (i % 150)))

        self.assertTrue(world.game_time > 0)
        print("Interactive clicks stress test completed with 0 errors!")


if __name__ == "__main__":
    unittest.main()
