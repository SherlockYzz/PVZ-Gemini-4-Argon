# -*- coding: utf-8 -*-
"""Projectile kinematics, trajectories, homing physics, and impact resolution.
Includes parabolic lobbing, Cattail homing, Torchwood igniting, and butter splat stuns.
"""

import math
import random
from domain.model.world import World
from domain.model.projectile import Projectile
from domain.model.particle import CombatParticle, FloatingText
from domain.rules.damage import apply_damage
from domain.spec.math_util import lerp


def update_projectiles(world: World, dt: float) -> None:
    for proj in world.projectiles:
        if not proj.alive:
            continue

        if proj.is_lobbed:
            _update_lobbed_projectile(proj, world, dt)
        elif proj.homing:
            _update_homing_projectile(proj, world, dt)
        else:
            _update_straight_projectile(proj, world, dt)


def _update_straight_projectile(proj: Projectile, world: World, dt: float) -> None:
    step = proj.vx * dt
    proj.x += step
    proj.y += proj.vy * dt
    proj.range_traveled += step

    if proj.range_traveled >= proj.max_range or proj.x > 1250 or proj.x < -50:
        proj.alive = False
        return

    # Torchwood enhancement: turn pea into flaming pea
    if proj.bullet_type == "pea":
        col, row = world.layout.pos_to_cell(proj.x, proj.y)
        if col is not None and row is not None:
            plant = world.get_plant_at(col, row)
            if plant and plant.spec_id == "torchwood":
                proj.bullet_type = "firepea"
                proj.damage = 40.0

    # Collision with zombies in the same row
    zombies = world.get_zombies_in_row(proj.row)
    for z in zombies:
        if not z.is_alive or z.hypnotized or z.id in proj.hit_zombie_ids:
            continue
        # Snorkel underwater evasion against straight low bullets
        if z.submerged and proj.bullet_type in ("pea", "snowpea", "firepea", "shroom"):
            continue

        # Check collision threshold
        if abs(proj.x - z.x) < 28:
            proj.hit_zombie_ids.add(z.id)
            
            slow_sec = 4.0 if proj.bullet_type == "snowpea" else 0.0
            if proj.bullet_type == "firepea":
                z.slow_timer = 0.0  # Fire melts ice!

            # Card special perk: 25% chance of bonus effect
            if proj.bullet_type == "card" and random.random() < 0.25:
                if random.random() < 0.5:
                    z.hypnotize()
                else:
                    world.sun += 25
                    world.floating_texts.append(FloatingText("+25", z.x, z.y - 20, (255, 235, 60)))

            apply_damage(z, proj.damage, slow_duration=slow_sec)

            # Hit visual particle
            color = (140, 220, 255) if proj.bullet_type == "snowpea" else (255, 120, 40) if proj.bullet_type == "firepea" else (180, 240, 100)
            world.particles.append(
                CombatParticle(kind="splat", x=proj.x, y=proj.y, vx=random.uniform(-40, 40), vy=random.uniform(-40, 40), color=color, size=6.0, lifetime=0.2)
            )

            if not proj.piercing:
                proj.alive = False
                break


def _update_lobbed_projectile(proj: Projectile, world: World, dt: float) -> None:
    proj.flight_t += dt / max(0.01, proj.flight_duration)
    t = min(1.0, proj.flight_t)

    # Parabolic trajectory
    proj.x = lerp(proj.start_x, proj.target_x, t)
    arc_y = 4.0 * proj.arc_height * t * (1.0 - t)
    proj.y = lerp(proj.start_y, proj.target_y, t) - arc_y

    if t >= 1.0:
        # Explode / Impact at target
        proj.alive = False
        _detonate_lobbed_impact(proj, world)


def _detonate_lobbed_impact(proj: Projectile, world: World) -> None:
    tx, ty = proj.target_x, proj.target_y
    bullet_type = proj.bullet_type

    # Heavy Cob Cannon detonation
    if bullet_type == "cob":
        world.shake.trigger(magnitude=14.0, duration=0.4)
        for z in world.zombies:
            if z.is_alive and not z.hypnotized:
                dist = math.hypot(z.x - tx, z.y - ty)
                if dist < 170.0:
                    apply_damage(z, 1800.0, is_ash=True)
        return

    # Normal catapult impacts (cabbage, kernel, butter, melon, wintermelon)
    # Catapults can hit submerged snorkel zombies directly!
    target_row = proj.row
    zombies_in_row = world.get_zombies_in_row(target_row)

    # Find primary target closest to landing spot
    primary_zombie = None
    min_dist = 9999.0
    for z in zombies_in_row:
        if z.is_alive and not z.hypnotized:
            d = abs(z.x - tx)
            if d < min_dist and d < 55.0:
                min_dist = d
                primary_zombie = z

    butter_duration = 4.0 if bullet_type == "butter" else 0.0
    slow_duration = 5.0 if bullet_type == "wintermelon" else 0.0

    if primary_zombie:
        apply_damage(
            primary_zombie,
            proj.damage,
            butter_duration=butter_duration,
            slow_duration=slow_duration,
        )
        if butter_duration > 0:
            world.floating_texts.append(FloatingText("黄油定身!", primary_zombie.x, primary_zombie.y - 30, (255, 230, 80)))

    # Splash damage for melon and wintermelon
    if bullet_type in ("melon", "wintermelon"):
        splash_dmg = 26.0
        for z in world.zombies:
            if z.is_alive and not z.hypnotized and z != primary_zombie:
                dist = math.hypot(z.x - tx, z.y - ty)
                if dist < 110.0:
                    apply_damage(z, splash_dmg, slow_duration=slow_duration)


def _update_homing_projectile(proj: Projectile, world: World, dt: float) -> None:
    # Find nearest alive enemy zombie
    best_target = None
    min_dist = 999999.0

    for z in world.zombies:
        if z.is_alive and not z.hypnotized:
            dist = math.hypot(z.x - proj.x, z.y - proj.y)
            if dist < min_dist:
                min_dist = dist
                best_target = z

    if best_target:
        dx = best_target.x - proj.x
        dy = best_target.y - proj.y
        dist = max(1.0, math.hypot(dx, dy))
        desired_vx = (dx / dist) * 350.0
        desired_vy = (dy / dist) * 350.0
        proj.vx = lerp(proj.vx, desired_vx, dt * 7.0)
        proj.vy = lerp(proj.vy, desired_vy, dt * 7.0)

    proj.x += proj.vx * dt
    proj.y += proj.vy * dt

    if proj.x > 1250 or proj.x < -50 or proj.y < -50 or proj.y > 800:
        proj.alive = False
        return

    # Check collision with any target
    for z in world.zombies:
        if z.is_alive and not z.hypnotized:
            if math.hypot(z.x - proj.x, z.y - proj.y) < 26.0:
                apply_damage(z, proj.damage)
                proj.alive = False
                world.particles.append(
                    CombatParticle(kind="splat", x=proj.x, y=proj.y, vx=0, vy=0, color=(240, 140, 180), size=5.0, lifetime=0.15)
                )
                break
