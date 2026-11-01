# -*- coding: utf-8 -*-
"""Headless Rendering Dry-Run Test.
Validates that every single UI view and overlay renders onto a Pygame surface without errors,
even with extreme out-of-bounds mouse coordinates.
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
from domain.spec.rewards import LEVEL_REWARDS
from usecases.start_level import start_level
from usecases.plant_seed import execute_plant_action
from app.renderers.menu import render_menu
from app.renderers.seed_select import render_seed_select
from app.renderers.battle import render_battle
from app.renderers.hud import render_hud
from app.renderers.overlays import render_pause, render_victory, render_game_over


class TestRenderDryRun(unittest.TestCase):
    def setUp(self):
        self.canvas = pygame.Surface((1200, 760))
        self.session = Session(
            current_level_idx=10,
            unlocked_plants={"sunflower", "peashooter", "lilypad", "kernelpult", "cattail"},
            selected_seeds=["sunflower", "peashooter", "lilypad", "kernelpult", "cattail"],
            unlocked_artifacts={"auto_sun_magnet"},
        )

    def test_render_all_screens_and_out_of_bounds_mouse(self):
        world = start_level(10, self.session)
        # Add some entities to test drawing
        self.session.active_seed_idx = 2
        execute_plant_action(col=3, row=2, world=world, session=self.session)  # Lilypad
        self.session.active_seed_idx = 4
        execute_plant_action(col=3, row=2, world=world, session=self.session)  # Cattail

        # Test extreme mouse positions
        mouse_positions = [
            (0, 0),
            (1200, 760),
            (600, 30),     # Top HUD (outside lawn grid)
            (30, 400),     # Left of lawn
            (1150, 400),   # Right of lawn (zombie side)
            (600, 740),    # Bottom edge
            (-100, -100),  # Negative out of bounds
            (3000, 3000),  # Way beyond screen
            (500, 300),    # Inside lawn grid
        ]

        for mpos in mouse_positions:
            # 1. Main menu
            render_menu(self.canvas, self.session, mpos)
            # 2. Seed select
            render_seed_select(self.canvas, self.session, mpos)
            # 3. Battle & HUD
            render_battle(self.canvas, world, self.session, mpos)
            render_hud(self.canvas, world, self.session, mpos)
            # 4. Overlays
            render_pause(self.canvas)
            render_victory(self.canvas, LEVEL_REWARDS[9])
            render_game_over(self.canvas)


if __name__ == "__main__":
    unittest.main()
