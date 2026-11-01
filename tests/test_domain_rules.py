# -*- coding: utf-8 -*-
"""Comprehensive Domain Rules & Combat Invariant Tests.
Validates all 34 plants, 15 zombies, 16 levels, damage authority, and grid geometry.
Built on standard unittest for zero-dependency execution.
"""

import sys
import unittest
from pathlib import Path

# Ensure root package resolution
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from domain.spec.plants import PLANTS, PlacementRule, BehaviorKind
from domain.spec.zombies import ZOMBIES
from domain.spec.levels import LEVELS
from domain.spec.field_layout import LAND_LAYOUT, POOL_LAYOUT
from domain.spec.rewards import LEVEL_REWARDS, UNLOCK_ORDER
from domain.model.plant import Plant
from domain.model.zombie import Zombie
from domain.model.world import World
from domain.model.session import Session
from domain.rules.damage import apply_damage
from domain.rules.planting import can_plant, perform_plant, shovel_plant
from domain.rules.economy import collect_sun_at
from domain.model.sun import Sun


class TestDomainRules(unittest.TestCase):
    def test_plants_integrity(self):
        self.assertGreaterEqual(len(PLANTS), 34)
        self.assertEqual(PLANTS["twinsunflower"].cost, 125)  # Authentic 125 sun fix
        self.assertEqual(PLANTS["sunflower"].cost, 50)
        self.assertEqual(PLANTS["threepeater"].cost, 300)
        self.assertGreater(PLANTS["kernelpult"].behavior.butter_chance, 0.0)

    def test_zombies_integrity(self):
        self.assertGreaterEqual(len(ZOMBIES), 15)
        self.assertIn("newspaper", ZOMBIES)
        self.assertGreater(ZOMBIES["newspaper"].shield_hp, 0)
        self.assertTrue(ZOMBIES["ducky"].is_water)
        self.assertTrue(ZOMBIES["snorkel"].can_dive)

    def test_levels_and_layouts(self):
        self.assertEqual(len(LEVELS), 16)
        self.assertFalse(LEVELS[0].is_pool)
        self.assertTrue(LEVELS[10].is_pool)
        self.assertTrue(LEVELS[15].is_endless)

        # POOL_LAYOUT exact geometry check
        self.assertEqual(POOL_LAYOUT.rows, 6)
        self.assertEqual(POOL_LAYOUT.pool_rows, frozenset({2, 3}))
        self.assertTrue(POOL_LAYOUT.is_water_tile(0, 2))
        self.assertFalse(POOL_LAYOUT.is_water_tile(0, 1))

    def test_damage_authority_and_shields(self):
        z = Zombie.create("newspaper", row=1, x=500, y=200)
        self.assertGreater(z.shield_hp, 0)
        initial_shield = z.shield_hp
        initial_body = z.hp

        # Hit 1: absorbed by newspaper shield
        dealt, is_dead = apply_damage(z, 40.0)
        self.assertEqual(dealt, 40.0)
        self.assertFalse(is_dead)
        self.assertEqual(z.shield_hp, initial_shield - 40.0)
        self.assertEqual(z.hp, initial_body)

        # Hit 2: destroy shield and overflow to body -> enrage!
        dealt, is_dead = apply_damage(z, initial_shield)
        self.assertFalse(is_dead)
        self.assertEqual(z.shield_hp, 0)
        self.assertTrue(z.is_enraged)  # Newspaper enraged!
        self.assertGreater(z.health_ratio, 0.0)  # Health bar remains clearly visible!

        # Butter stun
        apply_damage(z, 20.0, butter_duration=4.0)
        self.assertEqual(z.butter_timer, 4.0)
        self.assertEqual(z.effective_speed, 0.0)

    def test_planting_upgrades_and_carriers(self):
        session = Session(unlocked_plants={"sunflower", "twinsunflower", "lilypad", "peashooter"})
        world = World(layout=POOL_LAYOUT, sun=500)

        # 1. Planting Lilypad on water row 2
        can_pad, _ = can_plant("lilypad", col=3, row=2, world=world, session=session)
        self.assertTrue(can_pad)
        pad = perform_plant("lilypad", col=3, row=2, world=world, session=session)
        self.assertIsNotNone(pad)
        self.assertIsNotNone(world.get_carrier_at(3, 2))

        # 2. Planting Sunflower on Lilypad carrier
        can_sun, _ = can_plant("sunflower", col=3, row=2, world=world, session=session)
        self.assertTrue(can_sun)
        sun = perform_plant("sunflower", col=3, row=2, world=world, session=session)
        self.assertIsNotNone(sun)
        self.assertEqual(sun.carrier, pad)

        # 3. Upgrade Sunflower to Twin Sunflower (125 sun)
        can_twin, _ = can_plant("twinsunflower", col=3, row=2, world=world, session=session)
        self.assertTrue(can_twin)
        twin = perform_plant("twinsunflower", col=3, row=2, world=world, session=session)
        self.assertIsNotNone(twin)
        self.assertEqual(twin.spec_id, "twinsunflower")
        self.assertEqual(world.get_plant_at(3, 2).spec_id, "twinsunflower")

    def test_golden_shovel_refund(self):
        session = Session(unlocked_artifacts={"golden_shovel"})
        world = World(sun=100)
        plant = perform_plant("peashooter", col=0, row=0, world=world, session=session)
        self.assertEqual(world.sun, 0)  # 100 - 100

        # Shovel refund
        success = shovel_plant(0, 0, world, session)
        self.assertTrue(success)
        self.assertEqual(world.sun, 100)  # 100% full refund!
        self.assertIsNone(world.get_plant_at(0, 0))

    def test_pos_to_cell_out_of_bounds_safety(self):
        """Validates that out-of-bounds coordinates never crash tuple unpacking."""
        layout = LAND_LAYOUT
        # Test out-of-bounds unpacking safety
        col, row = layout.pos_to_cell(-100, -100)
        self.assertIsNone(col)
        self.assertIsNone(row)

        col, row = layout.pos_to_cell(1300, 300)
        self.assertIsNone(col)
        self.assertIsNone(row)

        col, row = layout.pos_to_cell(500, 20)  # In top HUD
        self.assertIsNone(col)
        self.assertIsNone(row)

        # In-bounds unpacking
        cx, cy = layout.center(3, 2)
        col, row = layout.pos_to_cell(cx, cy)
        self.assertEqual(col, 3)
        self.assertEqual(row, 2)


if __name__ == "__main__":
    unittest.main()
