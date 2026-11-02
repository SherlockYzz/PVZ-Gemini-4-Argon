# -*- coding: utf-8 -*-
"""Combat loop orchestrator.
Coordinates plant behaviors, zombie AI, mowers, and hypno-brawls.
"""

import math
import random
from domain.model.world import World
from domain.model.session import Session
from domain.model.plant import Plant
from domain.model.zombie import Zombie
from domain.model.projectile import Projectile
from domain.model.sun import Sun
from domain.model.particle import CombatParticle, FloatingText
from domain.spec.plants import BehaviorKind, PlacementRule
from domain.rules.damage import apply_damage


def update_combat(world: World, session: Session, dt: float) -> None:
    # 1. Update plants
    _update_plants(world, dt)

    # 2. Update zombies & hypno brawls
    _update_zombies(world, dt)

    # 3. Update mowers
    _update_mowers(world, session, dt)


def _update_plants(world: World, dt: float) -> None:
    for (col, row), plant in list(world.plants.items()):
        if not plant.is_alive:
            continue

        plant.age += dt
        b_spec = plant.spec.behavior

        # Visual scale bounce back to 1.0
        if plant.scale > 1.0:
            plant.scale = max(1.0, plant.scale - dt * 2.0)

        # State machines for specials
        if plant.spec_id == "potatomine":
            if plant.state == "priming":
                plant.state_timer -= dt
                if plant.state_timer <= 0:
                    plant.state = "idle"  # Primed and ready!
            elif plant.state == "idle":
                # Check for zombie contact
                zombies = world.get_zombies_in_row(row)
                for z in zombies:
                    if z.is_alive and not z.hypnotized and abs(z.x - plant.x) < 32:
                        # Boom!
                        apply_damage(z, 1800.0, is_ash=True)
                        plant.hp = 0
                        world.shake.trigger(magnitude=8.0, duration=0.2)
                        world.particles.append(
                            CombatParticle(kind="ash", x=plant.x, y=plant.y, vx=0, vy=0, color=(120, 80, 50), size=14, lifetime=0.3)
                        )
                        break
            continue

        if plant.spec_id in ("cherrybomb", "jalapeno", "doomshroom"):
            plant.state_timer += dt
            if plant.state_timer >= 1.0:
                _detonate_explosive_plant(plant, world)
                plant.hp = 0
            continue

        if plant.spec_id == "chomper":
            if plant.state == "chewing":
                plant.state_timer -= dt
                if plant.state_timer <= 0:
                    plant.state = "idle"
            elif plant.state == "idle":
                zombies = world.get_zombies_in_row(row)
                for z in zombies:
                    if z.is_alive and not z.hypnotized and 0 <= (z.x - plant.x) < 85:
                        # Devour!
                        apply_damage(z, 2000.0, is_ash=True)
                        plant.state = "chewing"
                        plant.state_timer = 24.0
                        world.floating_texts.append(FloatingText("嚼嚼嚼!", plant.x, plant.y - 30, (140, 240, 100)))
                        break
            continue

        if plant.spec_id == "squash":
            if plant.state == "idle":
                # Check nearby zombies within adjacent tiles
                target = None
                for z in world.get_zombies_in_row(row):
                    if z.is_alive and not z.hypnotized and abs(z.x - plant.x) < 95:
                        target = z
                        break
                if target:
                    plant.state = "squash_jump"
                    plant.state_timer = 0.4
                    plant.target_x = target.x
            elif plant.state == "squash_jump":
                plant.state_timer -= dt
                if plant.state_timer <= 0:
                    # Smash!
                    world.shake.trigger(magnitude=7.0, duration=0.2)
                    for z in world.get_zombies_in_row(row):
                        if z.is_alive and not z.hypnotized and abs(z.x - plant.target_x) < 65:
                            apply_damage(z, 1800.0, is_ash=True)
                    plant.hp = 0
            continue

        # Multi-shot burst salvos (Repeater x2, Gatling x4)
        if plant.burst_remaining > 0:
            plant.sub_timer -= dt
            if plant.sub_timer <= 0:
                plant.burst_remaining -= 1
                plant.sub_timer = 0.15
                target_r = getattr(plant, "burst_target_row", plant.row)
                _fire_burst_bullet(plant, target_r, b_spec, world)

        # Periodic action updates (Shooters, Lobbers, Producers)
        plant.timer -= dt
        if plant.timer <= 0:
            kind = b_spec.kind

            if kind == BehaviorKind.PRODUCER:
                plant.timer = b_spec.interval
                plant.scale = 1.25  # Pop animation!
                # Spawn sun
                yield_val = 25
                if plant.spec_id == "sunshroom":
                    yield_val = 15 if plant.age < 35.0 else 25
                elif plant.spec_id == "twinsunflower":
                    yield_val = 50

                pop_x = plant.x + random.uniform(-18, 18)
                pop_y = plant.y + random.uniform(5, 25)
                world.suns.append(Sun.create_from_plant(plant.x, plant.y - 10, pop_x, pop_y, value=yield_val))

            elif kind == BehaviorKind.SHOOTER:
                # Check target presence across monitored rows
                rows_to_check = [row]
                if b_spec.rows_spread > 0:
                    rows_to_check = [r for r in (row - 1, row, row + 1) if 0 <= r < world.layout.rows]

                has_target = any(
                    any(z.is_alive and not z.hypnotized and z.x > plant.x - 20 for z in world.get_zombies_in_row(r))
                    for r in rows_to_check
                )

                if has_target:
                    plant.timer = b_spec.interval
                    for r in rows_to_check:
                        _fire_shooter(plant, r, b_spec, world)

            elif kind == BehaviorKind.LOBBER:
                # Catapults check row
                enemy_zombies = [z for z in world.get_zombies_in_row(row) if z.is_alive and not z.hypnotized and z.x > plant.x - 40]
                if enemy_zombies:
                    plant.timer = b_spec.interval
                    lead_zombie = min(enemy_zombies, key=lambda z: z.x)
                    _fire_lobber(plant, lead_zombie, b_spec, world)

            elif kind == BehaviorKind.HOMING:
                # Cattail fires homing spike prioritizing flying balloon zombies and closest threats
                enemy_zombies = [z for z in world.zombies if z.is_alive and not z.hypnotized and z.x > 30]
                if enemy_zombies:
                    plant.timer = b_spec.interval
                    balloons = [z for z in enemy_zombies if z.flying]
                    target = min(balloons, key=lambda z: z.x) if balloons else min(enemy_zombies, key=lambda z: z.x)
                    world.projectiles.append(
                        Projectile.create_homing("spike", row, plant.x + 16, plant.y - 12, damage=30.0, target_zombie_id=target.id)
                    )


def _fire_shooter(plant: Plant, target_row: int, b_spec, world: World) -> None:
    bullet_type = b_spec.bullet_type
    damage = b_spec.damage
    row_center_y = world.layout.get_row_center_y(target_row)
    world.projectiles.append(
        Projectile.create_straight(
            bullet_type=bullet_type,
            row=target_row,
            x=plant.x + 24,
            y=row_center_y - 8,
            damage=damage,
            piercing=(bullet_type in ("fume", "laser")),
            max_range=320.0 if plant.spec_id == "puffshroom" else 2000.0,
        )
    )
    # Repeater / Gatling rapid fire salvos
    if b_spec.burst_count > 1 and plant.burst_remaining == 0:
        plant.burst_remaining = b_spec.burst_count - 1
        plant.sub_timer = 0.15
        plant.burst_target_row = target_row


def _fire_burst_bullet(plant: Plant, target_row: int, b_spec, world: World) -> None:
    bullet_type = b_spec.bullet_type
    damage = b_spec.damage
    row_center_y = world.layout.get_row_center_y(target_row)
    world.projectiles.append(
        Projectile.create_straight(
            bullet_type=bullet_type,
            row=target_row,
            x=plant.x + 24,
            y=row_center_y - 8,
            damage=damage,
            piercing=(bullet_type in ("fume", "laser")),
            max_range=320.0 if plant.spec_id == "puffshroom" else 2000.0,
        )
    )


def _fire_lobber(plant: Plant, target_zombie: Zombie, b_spec, world: World) -> None:
    bullet_type = b_spec.bullet_type
    dmg = b_spec.damage

    # Kernel-pult butter chance
    if plant.spec_id == "kernelpult" and random.random() < b_spec.butter_chance:
        bullet_type = "butter"
        dmg = b_spec.butter_damage

    world.projectiles.append(
        Projectile.create_lobbed(
            bullet_type=bullet_type,
            row=plant.row,
            start_x=plant.x,
            start_y=plant.y - 20,
            target_x=target_zombie.x,
            target_y=target_zombie.y - 15,
            damage=dmg,
        )
    )


def _detonate_explosive_plant(plant: Plant, world: World) -> None:
    px, py = plant.x, plant.y
    world.shake.trigger(magnitude=12.0, duration=0.35)

    if plant.spec_id == "jalapeno":
        # Whole lane incinerated!
        for z in world.get_zombies_in_row(plant.row):
            apply_damage(z, 1800.0, is_ash=True)
    elif plant.spec_id == "cherrybomb":
        # 3x3 blast radius
        for z in world.zombies:
            if z.is_alive and not z.hypnotized:
                if math.hypot(z.x - px, z.y - py) < 180.0:
                    apply_damage(z, 1800.0, is_ash=True)
    elif plant.spec_id == "doomshroom":
        # 5x5 nuclear blast
        for z in world.zombies:
            if z.is_alive and not z.hypnotized:
                if math.hypot(z.x - px, z.y - py) < 320.0:
                    apply_damage(z, 3000.0, is_ash=True)


def _update_zombies(world: World, dt: float) -> None:
    for z in world.zombies:
        if not z.is_alive:
            continue

        z.total_lifetime += dt
        if z.flash_timer > 0:
            z.flash_timer = max(0.0, z.flash_timer - dt)
        if z.freeze_timer > 0:
            z.freeze_timer = max(0.0, z.freeze_timer - dt)
        if z.slow_timer > 0:
            z.slow_timer = max(0.0, z.slow_timer - dt)
        if z.butter_timer > 0:
            z.butter_timer = max(0.0, z.butter_timer - dt)

        # Frozen / Buttered zombies cannot move or chew
        if z.freeze_timer > 0 or z.butter_timer > 0:
            continue

        # Hypnotized vs Enemy Zombie Brawls (Interactive Fighting!)
        if z.hypnotized:
            # Hypnotized zombie moves right towards incoming zombies
            step = z.effective_speed * dt
            z.x += step

            # Look for normal enemy zombies in the same lane to attack!
            enemy_in_front = None
            for other in world.get_zombies_in_row(z.row):
                if other.is_alive and not other.hypnotized and 0 <= (other.x - z.x) < 35:
                    enemy_in_front = other
                    break

            if enemy_in_front:
                # Mutual chewing combat!
                z.x -= step  # Halt
                enemy_in_front.apply_damage(z.damage * dt)
                z.apply_damage(enemy_in_front.damage * dt)
            continue

        # Normal enemy zombie logic
        # 1. Check if meeting a hypnotized friendly zombie
        hypno_target = None
        for other in world.get_zombies_in_row(z.row):
            if other.is_alive and other.hypnotized and 0 <= (z.x - other.x) < 35:
                hypno_target = other
                break

        if hypno_target:
            # Engage in combat with the hypnotized zombie!
            hypno_target.apply_damage(z.damage * dt)
            z.apply_damage(hypno_target.damage * dt)
            continue

        # 2. Check plant encounters
        target_plant = None
        col, _ = world.layout.pos_to_cell(z.x - 12, world.layout.get_row_center_y(z.row))
        if col is not None:
            target_plant = world.get_plant_at(col, z.row)

        if target_plant and target_plant.is_alive:
            # Special: Hypno-shroom effect when eaten!
            if target_plant.spec_id == "hypnoshroom":
                target_plant.hp = 0
                z.hypnotize()
                world.floating_texts.append(FloatingText("被魅惑了!", z.x, z.y - 25, (220, 120, 255)))
                continue

            # Special: Garlic diversion!
            if target_plant.spec_id == "garlic":
                target_plant.take_damage(z.damage * dt)
                # Divert zombie row up or down
                options = []
                if z.row > 0:
                    options.append(z.row - 1)
                if z.row < world.layout.rows - 1:
                    options.append(z.row + 1)
                if options:
                    new_r = random.choice(options)
                    z.row = new_r
                    z.y = world.layout.get_row_ground_y(new_r)
                world.floating_texts.append(FloatingText("嫌弃变道!", z.x, z.y - 25, (200, 240, 120)))
                continue

            # Special: Pole Vault / Dolphin leap over first plant (unless Tallnut!)
            if (z.spec_id in ("pole", "dolphin")) and not z.has_vaulted:
                if target_plant.spec_id != "tallnut":
                    z.has_vaulted = True
                    z.x -= world.layout.cell_w * 1.15  # Leap over!
                    world.floating_texts.append(FloatingText("完美飞跃!", z.x, z.y - 25, (255, 200, 50)))
                    continue

            # Spikeweed cannot be eaten; instead, spikeweed damages the zombie
            if target_plant.spec_id == "spikeweed":
                apply_damage(z, 30.0 * dt, bypass_shield=True)
                # Zombie continues walking over spikeweed!
                z.x -= z.effective_speed * dt
                continue

            # Normal chewing
            z.eating = True
            plant_died = target_plant.take_damage(z.damage * dt)
            if plant_died:
                z.eating = False
        else:
            # No plant in contact, keep walking
            z.eating = False
            z.x -= z.effective_speed * dt


def _update_mowers(world: World, session: Session, dt: float) -> None:
    for mower in world.mowers:
        if not mower.active:
            continue

        if not mower.triggered:
            # Check if any enemy zombie crossed the mower line
            for z in world.get_zombies_in_row(mower.row):
                if z.is_alive and not z.hypnotized and z.x <= world.layout.grid_x + 12:
                    mower.trigger()
                    break

        if mower.triggered:
            mower.update(dt)
            # Crush all zombies in row
            for z in world.get_zombies_in_row(mower.row):
                if z.is_alive and abs(z.x - mower.x) < 40:
                    apply_damage(z, 9999.0, is_ash=True)

            # Golden mower perk bonus
            if not mower.active and "golden_mower" in session.unlocked_artifacts:
                world.sun += 200
                world.floating_texts.append(FloatingText("+200 黄金割草!", mower.x, mower.y, (255, 215, 0)))
