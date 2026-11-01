# -*- coding: utf-8 -*-
"""Unit tests for Skip Level mechanics, Retroactive Reward Grants, and Visual Rendering."""

import unittest
import os
import pygame

# Run pygame in headless mode
os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()

from domain.model.session import Session
from domain.model.world import World
from domain.model.zombie import Zombie
from domain.spec.levels import LEVELS
from domain.spec.rewards import LEVEL_REWARDS, UNLOCK_ORDER
from usecases.skip_level import skip_to_level
from app.renderers.battle import render_battle, get_procedural_background
from app.renderers.overlays import render_warp_overlay
from app.controller import GameController
from infra.pygame_input import InputEvent
from infra.pygame_audio import PygameAudioAdapter
from infra.json_save import JsonSaveAdapter


class TestSkipAndVisuals(unittest.TestCase):
    def setUp(self):
        self.canvas = pygame.Surface((1200, 760))

    def test_procedural_lawn_checkerboard(self):
        """Test procedural lawn generator produces checkerboard pattern and distinct cell pixels."""
        for theme in ["day", "dusk", "night"]:
            bg = get_procedural_background(theme, is_pool=False)
            self.assertEqual(bg.get_size(), (1200, 760))

            # Inspect two adjacent grass cells to verify checkerboard color alternation
            # Cell (0, 0) vs Cell (1, 0)
            col0_color = bg.get_at((240 + 40, 120 + 50))
            col1_color = bg.get_at((240 + 82 + 40, 120 + 50))
            self.assertNotEqual(col0_color[:3], col1_color[:3], f"Theme {theme} cells should have checkerboard alternation")

    def test_zombie_single_health_bar_properties(self):
        """Test zombie model compatibility properties for single health bar rendering."""
        z = Zombie.create("basic", row=1, x=600.0, y=200.0)
        self.assertEqual(z.ztype, "basic")
        self.assertFalse(z.dead)
        self.assertFalse(z.has_newspaper)
        self.assertEqual(z.newspaper_hp, 0.0)

        # Apply damage
        z.apply_damage(50.0)
        self.assertLess(z.health_ratio, 1.0)
        self.assertGreater(z.health_ratio, 0.0)

        # Newspaper zombie check
        np_z = Zombie.create("newspaper", row=2, x=600.0, y=300.0)
        self.assertTrue(np_z.has_newspaper)
        self.assertGreater(np_z.newspaper_hp, 0.0)

        # Test rendering battle frame with damaged zombies does not crash
        session = Session(current_level_idx=0)
        world = World()
        world.zombies = [z, np_z]
        world.rebuild_spatial_index()
        render_battle(self.canvas, world, session, (400.0, 300.0))

    def test_skip_to_level_rewards_retroactive(self):
        """Test jumping to level 5 grants all prior rewards and golden shovel."""
        session = Session(current_level_idx=0)
        world = skip_to_level(5, session)

        # Unlocked plants should contain rewards from level 0, 1, 2, 3, 4
        self.assertIn("wallnut", session.unlocked_plants)
        self.assertIn("snowpea", session.unlocked_plants)
        self.assertIn("potatomine", session.unlocked_plants)
        self.assertIn("repeater", session.unlocked_plants)
        self.assertIn("squash", session.unlocked_plants)
        self.assertIn("threepeater", session.unlocked_plants)

        # Level 4 reward is golden shovel
        self.assertIn("golden_shovel", session.unlocked_artifacts)

        # Check notification floating text
        self.assertTrue(any("时空穿梭" in ft.text for ft in world.floating_texts))

    def test_skip_to_pool_guarantees_lilypad(self):
        """Test jumping to a pool level guarantees Lilypad carrier in unlocked plants and deck."""
        session = Session(current_level_idx=0)
        world = skip_to_level(10, session)  # Level 11 is pool_day

        self.assertIn("lilypad", session.unlocked_plants)
        self.assertIn("lilypad", session.selected_seeds)

    def test_skip_to_endless_grand_slam(self):
        """Test jumping to level 15 (endless) grants all 34 plants and master belt."""
        session = Session(current_level_idx=0)
        world = skip_to_level(15, session)

        # All 34 plants unlocked
        self.assertEqual(len(session.unlocked_plants), len(UNLOCK_ORDER))
        for p in UNLOCK_ORDER:
            self.assertIn(p, session.unlocked_plants)

        # Master belt artifact unlocked and 10 seed slots available
        self.assertIn("master_belt", session.unlocked_artifacts)
        self.assertEqual(session.max_seed_slots, 10)
        self.assertEqual(len(session.selected_seeds), 10)

    def test_controller_warp_portal_interaction(self):
        """Test controller warp portal hotkeys, overlay rendering, and card clicking."""
        session = Session(current_level_idx=0)
        audio = PygameAudioAdapter()
        storage = JsonSaveAdapter()
        ctrl = GameController(session, audio, storage)

        # Start a battle
        ctrl.mode = "battle"
        ctrl.world = skip_to_level(0, session)

        # 1. Hotkey 'toggle_warp' ([L]) opens warp portal
        ctrl.handle_event(InputEvent(kind="key", key_name="toggle_warp"))
        self.assertEqual(ctrl.mode, "warp")

        # 2. Render warp overlay and verify all 16 buttons exist
        buttons = render_warp_overlay(self.canvas, session, (500, 300))
        self.assertIn("warp_0", buttons)
        self.assertIn("warp_15", buttons)
        self.assertIn("warp_next", buttons)
        self.assertIn("warp_close", buttons)

        # 3. Click level 12 in warp overlay
        lvl12_rect = buttons["warp_12"]
        ctrl.handle_event(
            InputEvent(kind="click", x=float(lvl12_rect.centerx), y=float(lvl12_rect.centery)),
            overlay_buttons=buttons,
        )
        self.assertEqual(ctrl.mode, "battle")
        self.assertEqual(ctrl.session.current_level_idx, 12)
        # Verify retroactive rewards up to level 12
        self.assertIn("golden_mower", ctrl.session.unlocked_artifacts)

        # 4. Hotkey 'skip_next' ([Tab]/[N]) jumps directly to level 13
        ctrl.handle_event(InputEvent(kind="key", key_name="skip_next"))
        self.assertEqual(ctrl.session.current_level_idx, 13)


if __name__ == "__main__":
    unittest.main()
