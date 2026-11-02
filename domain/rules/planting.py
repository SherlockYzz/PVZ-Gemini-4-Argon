# -*- coding: utf-8 -*-
"""Planting validation and execution rules.
Controls grid occupancy, upgrades (Twin Sunflower, Gatling Pea, Cattail),
water/land carrier requirements, and shovel refunds.
"""

from typing import Optional
from domain.spec.plants import PLANTS, PlantSpec, PlacementRule
from domain.model.plant import Plant
from domain.model.world import World
from domain.model.session import Session


def can_plant(spec_id: str, col: int, row: int, world: World, session: Session) -> tuple[bool, str]:
    if spec_id not in PLANTS:
        return False, "未知植物卡片"

    spec = PLANTS[spec_id]

    # 1. Sun check
    if world.sun < spec.cost:
        return False, f"阳光不足 (需 {spec.cost}，现有 {world.sun})"

    # 2. Cooldown check
    cd = session.seed_cooldowns.get(spec_id, 0.0)
    if cd > 0:
        return False, f"卡片冷却中 (还需 {cd:.1f} 秒)"

    # 3. Grid boundary check
    if col < 0 or col >= world.layout.cols or row < 0 or row >= world.layout.rows:
        return False, "请在草坪格内点击种植"

    is_water_tile = world.layout.is_water_tile(col, row)
    existing_plant = world.get_plant_at(col, row)
    existing_carrier = world.get_carrier_at(col, row)

    rule = spec.placement

    # Upgrade rules with crystal-clear guidance
    if rule == PlacementRule.UPGRADE_SUN:
        if existing_plant and existing_plant.spec_id == "sunflower":
            return True, ""
        return False, "双胞向日葵是升级植物，必须种植在现有向日葵上！"

    if rule == PlacementRule.UPGRADE_REPEATER:
        if existing_plant and existing_plant.spec_id == "repeater":
            return True, ""
        return False, "加特林射手是升级植物，必须种植在现有双发射手上！"

    if rule == PlacementRule.UPGRADE_LILYPAD:
        if existing_carrier and not existing_plant:
            return True, ""
        return False, "猫尾草是升级植物，必须种植在水池的睡莲上！"

    # Carrier placement (Lilypad)
    if rule == PlacementRule.CARRIER or rule == PlacementRule.WATER_ONLY:
        if not is_water_tile:
            return False, "睡莲只能种植在水池水面上！"
        if existing_carrier:
            return False, "该水格已有睡莲！"
        return True, ""

    # Normal plants on water tiles require a carrier (Lilypad)
    if is_water_tile:
        if rule == PlacementRule.AQUATIC:
            return existing_plant is None, "该水格已有植物！"
        if not existing_carrier:
            return False, "水面必须先种植睡莲，才能放置陆地植物！"
        if existing_plant:
            return False, "该睡莲上已有植物！"
        if spec_id in ("spikeweed", "potatomine"):
            return False, "地刺与土豆地雷不能种植在水池中！"
        return True, ""

    # Normal plants on land
    if existing_plant:
        return False, "该格已有植物，请先用铁锹铲除！"

    return True, ""


def perform_plant(spec_id: str, col: int, row: int, world: World, session: Session) -> Optional[Plant]:
    allowed, _ = can_plant(spec_id, col, row, world, session)
    if not allowed:
        return None

    spec = PLANTS[spec_id]
    world.sun -= spec.cost
    session.seed_cooldowns[spec_id] = spec.cooldown

    cx, cy = world.layout.get_cell_center(col, row)

    # Handle upgrades
    if spec.placement == PlacementRule.UPGRADE_SUN:
        existing = world.get_plant_at(col, row)
        carrier = existing.carrier if existing else None
        new_plant = Plant.create(spec_id, col, row, cx, cy, carrier=carrier)
        world.plants[(col, row)] = new_plant
        return new_plant

    if spec.placement == PlacementRule.UPGRADE_REPEATER:
        existing = world.get_plant_at(col, row)
        carrier = existing.carrier if existing else None
        new_plant = Plant.create(spec_id, col, row, cx, cy, carrier=carrier)
        world.plants[(col, row)] = new_plant
        return new_plant

    if spec.placement == PlacementRule.UPGRADE_LILYPAD:
        # Cattail replaces/occupies the lilypad
        existing_carrier = world.get_carrier_at(col, row)
        new_plant = Plant.create(spec_id, col, row, cx, cy, carrier=existing_carrier)
        world.plants[(col, row)] = new_plant
        return new_plant

    if spec.placement == PlacementRule.CARRIER:
        carrier = Plant.create(spec_id, col, row, cx, cy)
        world.carriers[(col, row)] = carrier
        return carrier

    # Normal placement
    carrier = world.get_carrier_at(col, row)
    plant = Plant.create(spec_id, col, row, cx, cy, carrier=carrier)
    world.plants[(col, row)] = plant
    return plant


def shovel_plant(col: int, row: int, world: World, session: Session) -> bool:
    plant = world.get_plant_at(col, row)
    carrier = world.get_carrier_at(col, row)

    if not plant and not carrier:
        return False

    # Refund if golden shovel is unlocked
    if "golden_shovel" in session.unlocked_artifacts:
        target_spec_id = plant.spec_id if plant else carrier.spec_id
        cost = PLANTS[target_spec_id].cost
        world.sun += cost

    if plant:
        del world.plants[(col, row)]
    elif carrier:
        del world.carriers[(col, row)]

    return True
