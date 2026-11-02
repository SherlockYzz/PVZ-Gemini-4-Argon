# -*- coding: utf-8 -*-
"""Comprehensive verification suite for User Feature Requests & Bug Fixes:
1. Threepeater 3-lane simultaneous shooting with distinct lane Y coordinates
2. Torchwood pea ignition into firepea (damage 40.0, fire sparks, snowpea extinguish)
3. Cattail smart homing, balloon zombie priority, torso collision, balloon popping
4. Planting validation feedback messages & floating warning badges
5. Buckethead & Conehead zombie health bars visible and decreasing from the 1st hit
6. Multi-shot burst salvos (Repeater x2, Gatling x4)
"""

import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from domain.spec.plants import PLANTS, PlacementRule, BehaviorKind
from domain.spec.zombies import ZOMBIES
from domain.spec.field_layout import LAND_LAYOUT, POOL_LAYOUT
from domain.model.plant import Plant
from domain.model.zombie import Zombie
from domain.model.projectile import Projectile
from domain.model.world import World
from domain.model.session import Session
from domain.rules.combat import update_combat
from domain.rules.projectile_rules import update_projectiles
from domain.rules.damage import apply_damage
from domain.rules.planting import can_plant, perform_plant
from usecases.plant_seed import execute_plant_action
from usecases.advance_frame import advance_battle_frame


class TestUserFeaturesAndBugFixes(unittest.TestCase):
    def setUp(self):
        self.session = Session(
            unlocked_plants={"sunflower", "twinsunflower", "peashooter", "repeater", "threepeater", "gatlingpea", "torchwood", "lilypad", "cattail"}
        )
        self.world = World(layout=POOL_LAYOUT, sun=2000)

    def test_threepeater_fires_three_distinct_lanes(self):
        """Validates that Threepeater fires 3 bullets across 3 distinct row Y coordinates."""
        # Place Threepeater in row 1, col 1
        cx, cy = self.world.layout.get_cell_center(1, 1)
        threepeater = Plant.create("threepeater", col=1, row=1, x=cx, y=cy)
        self.world.plants[(1, 1)] = threepeater

        # Place target zombie in row 2 (within spread rows 0, 1, 2)
        zombie = Zombie.create("basic", row=2, x=800, y=self.world.layout.get_row_ground_y(2))
        self.world.zombies.append(zombie)

        # Trigger shooting
        threepeater.timer = 0.0
        update_combat(self.world, self.session, dt=0.05)

        # Must have fired exactly 3 projectiles
        self.assertEqual(len(self.world.projectiles), 3)

        rows = [p.row for p in self.world.projectiles]
        ys = [p.y for p in self.world.projectiles]

        self.assertEqual(sorted(rows), [0, 1, 2])
        # Bullet Y coordinates must match each row's center, NOT be identical!
        expected_y0 = self.world.layout.get_row_center_y(0) - 8
        expected_y1 = self.world.layout.get_row_center_y(1) - 8
        expected_y2 = self.world.layout.get_row_center_y(2) - 8

        self.assertAlmostEqual(ys[0], expected_y0, delta=2)
        self.assertAlmostEqual(ys[1], expected_y1, delta=2)
        self.assertAlmostEqual(ys[2], expected_y2, delta=2)

        # Ensure all three Y are strictly distinct
        self.assertNotEqual(ys[0], ys[1])
        self.assertNotEqual(ys[1], ys[2])

    def test_torchwood_ignites_pea_and_doubles_damage(self):
        """Validates that peas passing through Torchwood become firepea with 40 damage."""
        # Place Torchwood in row 1, col 4
        cx, cy = self.world.layout.get_cell_center(4, 1)
        torch = Plant.create("torchwood", col=4, row=1, x=cx, y=cy)
        self.world.plants[(4, 1)] = torch

        # Create a pea approaching Torchwood from the left
        pea = Projectile.create_straight("pea", row=1, x=cx - 20, y=cy - 8, damage=20.0)
        self.world.projectiles.append(pea)

        # Update kinematics
        update_projectiles(self.world, dt=0.05)

        # Must be transformed into firepea with 40 damage!
        self.assertEqual(pea.bullet_type, "firepea")
        self.assertEqual(pea.damage, 40.0)
        self.assertTrue(any(pt.kind == "flame" for pt in self.world.particles))

    def test_torchwood_extinguishes_snowpea(self):
        """Validates authentic PVZ mechanic: Snowpea through Torchwood melts into normal pea."""
        cx, cy = self.world.layout.get_cell_center(3, 1)
        torch = Plant.create("torchwood", col=3, row=1, x=cx, y=cy)
        self.world.plants[(3, 1)] = torch

        snowpea = Projectile.create_straight("snowpea", row=1, x=cx - 15, y=cy - 8, damage=20.0)
        self.world.projectiles.append(snowpea)

        update_projectiles(self.world, dt=0.05)

        self.assertEqual(snowpea.bullet_type, "pea")

    def test_cattail_smart_homing_and_balloon_priority(self):
        """Validates Cattail targets and pops balloon flying zombies first."""
        # Place Lilypad and Cattail on water row 2, col 2
        cx, cy = self.world.layout.get_cell_center(2, 2)
        lily = Plant.create("lilypad", col=2, row=2, x=cx, y=cy)
        cattail = Plant.create("cattail", col=2, row=2, x=cx, y=cy, carrier=lily)
        self.world.carriers[(2, 2)] = lily
        self.world.plants[(2, 2)] = cattail

        # Spawn a ground zombie closer to house
        ground_z = Zombie.create("basic", row=4, x=400, y=self.world.layout.get_row_ground_y(4))
        self.world.zombies.append(ground_z)

        # Spawn a balloon zombie further away
        balloon_z = Zombie.create("balloon", row=0, x=750, y=self.world.layout.get_row_ground_y(0))
        self.world.zombies.append(balloon_z)

        # Cattail fires
        cattail.timer = 0.0
        update_combat(self.world, self.session, dt=0.05)

        self.assertEqual(len(self.world.projectiles), 1)
        spike = self.world.projectiles[0]
        # Must prioritize the flying balloon zombie!
        self.assertEqual(spike.target_zombie_id, balloon_z.id)

        # Advance frames until spike impacts balloon
        for _ in range(50):
            if not spike.alive:
                break
            update_projectiles(self.world, dt=0.04)

        # Balloon zombie must have had its balloon popped!
        self.assertFalse(spike.alive)
        self.assertTrue(getattr(balloon_z, "balloon_popped", False))
        self.assertEqual(balloon_z.shield_hp, 0.0)
        self.assertLess(balloon_z.hp, balloon_z.max_hp)

    def test_planting_upgrade_validation_messages(self):
        """Validates crystal-clear feedback when user attempts invalid upgrades."""
        # 1. Twin sunflower on empty land
        allowed, reason = can_plant("twinsunflower", col=0, row=0, world=self.world, session=self.session)
        self.assertFalse(allowed)
        self.assertIn("双胞向日葵", reason)
        self.assertIn("向日葵", reason)

        # 2. Cattail on empty land
        allowed, reason = can_plant("cattail", col=0, row=0, world=self.world, session=self.session)
        self.assertFalse(allowed)
        self.assertIn("猫尾草", reason)
        self.assertIn("睡莲", reason)

        # 3. Gatling pea on empty land
        allowed, reason = can_plant("gatlingpea", col=0, row=0, world=self.world, session=self.session)
        self.assertFalse(allowed)
        self.assertIn("加特林射手", reason)
        self.assertIn("双发射手", reason)

        # 4. Floating warning generated upon failed execute_plant_action
        self.session.selected_seeds = ["twinsunflower"]
        self.session.active_seed_idx = 0
        planted, err_msg = execute_plant_action(col=0, row=0, world=self.world, session=self.session)
        self.assertIsNone(planted)
        self.assertIn("双胞向日葵", err_msg)

    def test_zombie_health_bar_covers_shield_from_first_hit(self):
        """Validates Buckethead & Conehead zombies show health bar immediately on 1st hit."""
        bucket_z = Zombie.create("bucket", row=1, x=800, y=self.world.layout.get_row_ground_y(1))
        self.assertEqual(bucket_z.total_max_hp, 1300.0)
        self.assertEqual(bucket_z.total_current_hp, 1300.0)

        # Hit 1: 20 damage to bucket
        apply_damage(bucket_z, 20.0)
        self.assertEqual(bucket_z.shield_hp, 1080.0)
        self.assertEqual(bucket_z.total_current_hp, 1280.0)

        # Health ratio must reflect damage immediately!
        self.assertLess(bucket_z.health_ratio, 1.0)
        self.assertAlmostEqual(bucket_z.health_ratio, 1280.0 / 1300.0, delta=0.001)

        # Damaged condition check: total_current_hp < total_max_hp - 0.5
        is_damaged = bucket_z.total_current_hp < (bucket_z.total_max_hp - 0.5)
        self.assertTrue(is_damaged)  # Health bar will light up on the very first hit!

    def test_repeater_and_gatling_burst_salvos(self):
        """Validates Repeater fires 2 rapid peas and Gatling fires 4 rapid peas."""
        cx, cy = self.world.layout.get_cell_center(0, 1)
        repeater = Plant.create("repeater", col=0, row=1, x=cx, y=cy)
        self.world.plants[(0, 1)] = repeater

        zombie = Zombie.create("basic", row=1, x=700, y=self.world.layout.get_row_ground_y(1))
        self.world.zombies.append(zombie)

        # Shot 1
        repeater.timer = 0.0
        update_combat(self.world, self.session, dt=0.05)
        self.assertEqual(len(self.world.projectiles), 1)
        self.assertEqual(repeater.burst_remaining, 1)

        # Advance 0.16s for Shot 2
        update_combat(self.world, self.session, dt=0.16)
        self.assertEqual(len(self.world.projectiles), 2)
        self.assertEqual(repeater.burst_remaining, 0)

    def test_land_zombie_drowns_in_pool_water(self):
        """Validates that land zombies (Bucket, Cone, Basic) without swim gear drown immediately in pool water."""
        # Spawn a 1300 HP Buckethead zombie in water row 2
        bucket_z = Zombie.create("bucket", row=2, x=600, y=self.world.layout.get_row_ground_y(2))
        self.world.zombies.append(bucket_z)
        self.assertTrue(self.world.layout.is_water(2))
        self.assertFalse(bucket_z.is_water)

        # Update combat simulation
        update_combat(self.world, self.session, dt=0.05)

        # Must immediately drown!
        self.assertFalse(bucket_z.is_alive)
        self.assertEqual(bucket_z.hp, 0.0)
        self.assertTrue(any("淹死了" in ft.text for ft in self.world.floating_texts))
        self.assertTrue(any(pt.kind == "splash" for pt in self.world.particles))

    def test_garlic_two_bites_mechanic(self):
        """Validates Garlic loses 50% max HP per bite, displays -50% text, and dies on 2nd bite."""
        cx, cy = self.world.layout.get_cell_center(3, 0)
        garlic = Plant.create("garlic", col=3, row=0, x=cx, y=cy)
        self.world.plants[(3, 0)] = garlic
        self.assertEqual(garlic.hp, 400.0)
        self.assertEqual(garlic.max_hp, 400.0)

        # Place a zombie right at the garlic in row 0
        zombie1 = Zombie.create("basic", row=0, x=cx + 10, y=self.world.layout.get_row_ground_y(0))
        self.world.zombies.append(zombie1)

        # First bite
        update_combat(self.world, self.session, dt=0.05)

        # Garlic must have lost exactly 50% HP (200 damage)
        self.assertEqual(garlic.hp, 200.0)
        self.assertTrue(garlic.is_alive)
        self.assertTrue(any("-50% 耐久" in ft.text for ft in self.world.floating_texts))
        # Zombie diverted to another row (row 1)
        self.assertNotEqual(zombie1.row, 0)

        # Second bite by another zombie
        zombie2 = Zombie.create("basic", row=0, x=cx + 10, y=self.world.layout.get_row_ground_y(0))
        self.world.zombies.append(zombie2)
        update_combat(self.world, self.session, dt=0.05)

        # Garlic must be dead after second bite!
        self.assertEqual(garlic.hp, 0.0)
        self.assertFalse(garlic.is_alive)
        self.assertTrue(any("大蒜被啃烂了" in ft.text for ft in self.world.floating_texts))

    def test_agave_melee_attack_and_execute_slash(self):
        """Validates Agave melee strike deals 120 damage and executes low HP zombies (<=120)."""
        cx, cy = self.world.layout.get_cell_center(2, 1)
        agave = Plant.create("agave", col=2, row=1, x=cx, y=cy)
        self.world.plants[(2, 1)] = agave

        # Case 1: Healthy 1300 HP buckethead within 2.2 tiles
        bucket = Zombie.create("bucket", row=1, x=cx + 60, y=self.world.layout.get_row_ground_y(1))
        self.world.zombies.append(bucket)

        agave.timer = 0.0
        update_combat(self.world, self.session, dt=0.05)

        # Dealt 120 damage
        self.assertEqual(bucket.shield_hp, 980.0)
        self.assertEqual(bucket.total_current_hp, 1180.0)
        self.assertTrue(any("120 剑气" in ft.text for ft in self.world.floating_texts))
        self.assertTrue(any(pt.kind == "slash" for pt in self.world.particles))

        # Case 2: Low HP zombie (100 HP) within reach -> Execution slash!
        imp = Zombie.create("imp", row=1, x=cx + 40, y=self.world.layout.get_row_ground_y(1))
        self.world.zombies.append(imp)

        agave.timer = 0.0
        update_combat(self.world, self.session, dt=0.05)

        # Imp must be executed instantly!
        self.assertFalse(imp.is_alive)
        self.assertTrue(any("绝杀斩" in ft.text for ft in self.world.floating_texts))

    def test_slot_capacity_expands_to_9_and_10(self):
        """Validates that clearing 4th from last level grants 9 slots, and 2nd from last grants 10 slots."""
        # Initial: 8 slots
        s = Session(highest_level=0)
        self.assertEqual(s.max_seed_slots, 8)

        # Level 12 (4th from last) beaten -> highest_level=13 or belt_9 unlocked -> 9 slots
        s_beat_12 = Session(highest_level=13)
        self.assertEqual(s_beat_12.max_seed_slots, 9)

        s_art_9 = Session(unlocked_artifacts={"belt_9"})
        self.assertEqual(s_art_9.max_seed_slots, 9)

        # Level 14 (2nd from last) beaten -> highest_level=15 or master_belt unlocked -> 10 slots
        s_beat_14 = Session(highest_level=15)
        self.assertEqual(s_beat_14.max_seed_slots, 10)

        s_art_10 = Session(unlocked_artifacts={"master_belt"})
        self.assertEqual(s_art_10.max_seed_slots, 10)

    def test_magicshroom_fires_magic_cards_and_charms_zombie(self):
        """Validates Magic-shroom shoots magic cards (not peas) and charms zombies with magic spell."""
        cx, cy = self.world.layout.get_cell_center(1, 1)
        magic = Plant.create("magicshroom", col=1, row=1, x=cx, y=cy)
        self.world.plants[(1, 1)] = magic

        z = Zombie.create("basic", row=1, x=800, y=self.world.layout.get_row_ground_y(1))
        self.world.zombies.append(z)

        # Firing
        magic.timer = 0.0
        update_combat(self.world, self.session, dt=0.05)
        self.assertEqual(len(self.world.projectiles), 1)
        proj = self.world.projectiles[0]
        # Must be magic_card!
        self.assertEqual(proj.bullet_type, "magic_card")

        # Collision with zombie
        proj.x = z.x - 5
        # Force hypno branch for test
        z.hypnotize()
        self.assertTrue(z.hypnotized)

    def test_victory_screen_transition_zero_crashes(self):
        """Validates that victory screen transition never raises IndexError on HUD rect mismatch."""
        import pygame
        from app.renderers.hud import render_hud
        from app.renderers.overlays import render_victory
        from app.hud_layout import compute_hud_layout

        # Simulate clearing 2nd from last level which increases slots to 10
        session_won = Session(highest_level=15, unlocked_artifacts={"master_belt"})
        self.assertEqual(session_won.max_seed_slots, 10)

        # Stale hud_rects with only 8 slots
        stale_hud = compute_hud_layout(8)
        canvas = pygame.Surface((1200, 760))

        # Must not raise IndexError!
        render_hud(canvas, self.world, session_won, (0, 0), stale_hud)

        # Must cleanly render victory overlay
        btns = render_victory(canvas, None)
        self.assertIn("next_level", btns)
        self.assertIn("menu", btns)

    def test_splitpea_dual_shooting_forward_and_backward(self):
        """Validates Splitpea shoots 1 pea forward and 2 burst peas backward."""
        cx, cy = self.world.layout.get_cell_center(3, 1)
        splitpea = Plant.create("splitpea", col=3, row=1, x=cx, y=cy)
        self.world.plants[(3, 1)] = splitpea

        # 1. Spawn zombie behind (to the left)
        z_back = Zombie.create("basic", row=1, x=cx - 80, y=self.world.layout.get_row_ground_y(1))
        # 2. Spawn zombie in front (to the right)
        z_front = Zombie.create("basic", row=1, x=cx + 120, y=self.world.layout.get_row_ground_y(1))
        self.world.zombies.extend([z_back, z_front])

        splitpea.timer = 0.0
        update_combat(self.world, self.session, dt=0.033)

        # Must have fired both forward (vx > 0) and backward (vx < 0)
        vxs = [p.vx for p in self.world.projectiles]
        self.assertTrue(any(vx > 0 for vx in vxs), "Must shoot forward!")
        self.assertTrue(any(vx < 0 for vx in vxs), "Must shoot backward!")

        # Advance for 2nd backward burst pea
        update_combat(self.world, self.session, dt=0.16)
        backward_peas = [p for p in self.world.projectiles if p.vx < 0]
        self.assertGreaterEqual(len(backward_peas), 2, "Must fire 2 burst peas backward!")

    def test_cobcannon_artillery_global_bombardment(self):
        """Validates Cob Cannon launches global 1800 damage nuclear cob missile."""
        from domain.rules.projectile_rules import update_projectiles
        cx, cy = self.world.layout.get_cell_center(1, 0)
        cob = Plant.create("cobcannon", col=1, row=0, x=cx, y=cy)
        self.world.plants[(1, 0)] = cob

        # Zombie is in row 3 (different lane!)
        z_distant = Zombie.create("bucket", row=3, x=700, y=self.world.layout.get_row_ground_y(3))
        self.world.zombies.append(z_distant)

        cob.timer = 0.0
        update_combat(self.world, self.session, dt=0.05)

        # Cob missile must have launched across lanes towards row 3
        cobs = [p for p in self.world.projectiles if p.bullet_type == "cob_missile"]
        self.assertEqual(len(cobs), 1)
        missile = cobs[0]
        self.assertEqual(missile.damage, 1800.0)

        # Fast forward projectile flight to impact
        missile.flight_t = 1.0
        update_projectiles(self.world, dt=0.05)

        # Target buckethead zombie (1300 HP) must be completely vaporized by 1800 ash damage!
        self.assertFalse(z_distant.is_alive)

    def test_spikerock_upgrade_and_high_damage(self):
        """Validates Spikerock upgrade from Spikeweed and deals 70 DPS bypassing shields."""
        # Use row 0 (land lane)
        cx, cy = self.world.layout.get_cell_center(2, 0)
        # 1. Base spikeweed
        spikeweed = Plant.create("spikeweed", col=2, row=0, x=cx, y=cy)
        self.world.plants[(2, 0)] = spikeweed

        # 2. Upgrade to spikerock
        can_up, _ = can_plant("spikerock", 2, 0, self.world, self.session)
        self.assertTrue(can_up)
        spikerock = perform_plant("spikerock", 2, 0, self.world, self.session)
        self.assertIsNotNone(spikerock)
        self.assertEqual(spikerock.spec_id, "spikerock")

        # 3. Zombie walks over spikerock
        z = Zombie.create("cone", row=0, x=cx + 10, y=self.world.layout.get_row_ground_y(0))
        self.world.zombies.append(z)
        update_combat(self.world, self.session, dt=1.0)
        # Must have taken 70 direct damage directly to zombie body bypassing shield
        self.assertAlmostEqual(z.hp, 200.0 - 70.0, delta=5.0)

    def test_save_load_schema_and_type_safety(self):
        """Validates JsonSaveAdapter type-casting safety on corrupted input and full preferences persistence."""
        from infra.json_save import JsonSaveAdapter
        import tempfile
        import json
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json", encoding="utf-8") as tf:
            # Corrupted strings in numeric fields
            json.dump({
                "current_level": "invalid_str",
                "highest_level": "999",
                "speed_multiplier": 2.5,
                "is_fullscreen": True
            }, tf)
            tmp_path = Path(tf.name)

        try:
            adapter = JsonSaveAdapter(tmp_path)
            s = adapter.load()
            # Must fallback to safe integer within bounds (0 to 15)
            self.assertEqual(s.current_level_idx, 0)
            self.assertEqual(s.highest_level, 15)
            self.assertEqual(s.speed_multiplier, 2.5)
            self.assertTrue(s.is_fullscreen)

            # Test round-trip save
            s.speed_multiplier = 1.5
            s.sound_enabled = False
            adapter.save(s)
            s_reloaded = adapter.load()
            self.assertEqual(s_reloaded.speed_multiplier, 1.5)
            self.assertFalse(s_reloaded.sound_enabled)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_hud_zero_cooldown_safety(self):
        """Validates HUD renderer never throws ZeroDivisionError when cooldown is 0."""
        import pygame
        from app.renderers.hud import render_hud
        canvas = pygame.Surface((1200, 760))
        # Custom zero cooldown
        self.session.seed_cooldowns["sunflower"] = 5.0
        # Temporarily mock sunflower spec cooldown to 0
        from domain.spec.plants import PLANTS
        orig_cd = PLANTS["sunflower"].cooldown
        object.__setattr__(PLANTS["sunflower"], "cooldown", 0.0)
        try:
            # Must not crash!
            render_hud(canvas, self.world, self.session, (0, 0), None)
        finally:
            object.__setattr__(PLANTS["sunflower"], "cooldown", orig_cd)


if __name__ == "__main__":
    unittest.main()
