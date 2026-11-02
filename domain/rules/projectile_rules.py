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
    proj.range_traveled += abs(step)

    if proj.range_traveled >= proj.max_range or proj.x > 1250 or proj.x < -50:
        proj.alive = False
        return

    # Torchwood enhancement: turn peas into flaming firepeas
    if proj.bullet_type in ("pea", "snowpea"):
        for plant in world.get_plants_in_row(proj.row):
            if plant.spec_id == "torchwood" and abs(proj.x - plant.x) < 34:
                if proj.bullet_type == "snowpea":
                    # Frozen pea extinguished to normal pea
                    proj.bullet_type = "pea"
                else:
                    # Normal pea ignited into fiery flamepea with double damage!
                    proj.bullet_type = "firepea"
                    proj.damage = max(proj.damage * 2.0, 40.0)
                    world.particles.append(
                        CombatParticle(
                            kind="flame",
                            x=proj.x,
                            y=proj.y,
                            vx=random.uniform(15, 35),
                            vy=random.uniform(-15, 15),
                            color=(255, 160, 30),
                            size=8.0,
                            lifetime=0.25,
                        )
                    )
                break

    # Fiery trailing sparks for firepeas
    if proj.bullet_type == "firepea" and random.random() < 0.4:
        world.particles.append(
            CombatParticle(
                kind="spark",
                x=proj.x - 6,
                y=proj.y + random.uniform(-4, 4),
                vx=random.uniform(-30, -5),
                vy=random.uniform(-8, 8),
                color=(255, 140, 20),
                size=4.0,
                lifetime=0.15,
            )
        )

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

            # Magic-shroom Magic Card: authentic charm & trick spell
            actual_damage = proj.damage
            if proj.bullet_type in ("magic_card", "card"):
                # 35% chance to charm/hypnotize zombie!
                if z.spec_id not in ("gargantuar",) and random.random() < 0.35:
                    z.hypnotize()
                    world.floating_texts.append(FloatingText("魔术戏法·反戈魅惑!", z.x, z.y - 30, (230, 130, 255)))
                    for _ in range(8):
                        world.particles.append(
                            CombatParticle(
                                kind="magic",
                                x=z.x + random.uniform(-15, 15),
                                y=z.y - random.uniform(20, 50),
                                vx=random.uniform(-40, 40),
                                vy=random.uniform(-40, 10),
                                color=(235, 120, 255),
                                size=random.uniform(5.0, 8.0),
                                lifetime=0.3,
                            )
                        )
                else:
                    if random.random() < 0.5:
                        world.sun += 25
                        world.floating_texts.append(FloatingText("+25 阳光!", z.x, z.y - 25, (255, 235, 60)))
                    else:
                        actual_damage += 20.0
                        world.floating_texts.append(FloatingText("暴击扑克!", z.x, z.y - 25, (255, 130, 190)))

            apply_damage(z, actual_damage, slow_duration=slow_sec)

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
    if bullet_type in ("cob", "cob_missile"):
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
    # 1. Target candidate selection: prioritize flying balloons, then frontmost zombie
    best_target = None
    if proj.target_zombie_id is not None:
        for z in world.zombies:
            if z.id == proj.target_zombie_id and z.is_alive and not z.hypnotized:
                best_target = z
                break

    if not best_target:
        candidates = [z for z in world.zombies if z.is_alive and not z.hypnotized]
        if candidates:
            flying = [z for z in candidates if z.flying]
            if flying:
                best_target = min(flying, key=lambda z: z.x)
            else:
                best_target = min(candidates, key=lambda z: math.hypot(z.x - proj.x, (z.y - 45) - proj.y))
            if best_target:
                proj.target_zombie_id = best_target.id

    # 2. Homing steering toward target torso / balloon
    if best_target:
        target_y = best_target.y - (110 if best_target.flying else 50)
        dx = best_target.x - proj.x
        dy = target_y - proj.y
        dist = math.hypot(dx, dy)
        speed = 420.0
        if dist > 0:
            desired_vx = (dx / dist) * speed
            desired_vy = (dy / dist) * speed
        else:
            desired_vx, desired_vy = speed, 0.0

        # High-responsiveness navigation: never orbits!
        steer = min(1.0, dt * 18.0)
        proj.vx = lerp(proj.vx, desired_vx, steer)
        proj.vy = lerp(proj.vy, desired_vy, steer)

    proj.x += proj.vx * dt
    proj.y += proj.vy * dt

    if proj.x > 1250 or proj.x < -50 or proj.y < -50 or proj.y > 800:
        proj.alive = False
        return

    # 3. Collision resolution against all enemy zombies (torso, balloon, body)
    for z in world.zombies:
        if not z.is_alive or z.hypnotized:
            continue

        body_top = z.y - (145 if z.flying else 95)
        body_bottom = z.y + 15
        is_hit = False
        if abs(proj.x - z.x) <= 32 and (body_top <= proj.y <= body_bottom):
            is_hit = True
        elif math.hypot(proj.x - z.x, proj.y - (z.y - (100 if z.flying else 45))) < 36.0:
            is_hit = True

        if is_hit:
            # Cattail pops balloon zombies!
            if z.flying:
                z.balloon_popped = True
                z.shield_hp = 0.0
                world.floating_texts.append(FloatingText("气球刺破!", z.x, z.y - 65, (255, 200, 80)))

            apply_damage(z, proj.damage)
            proj.alive = False
            world.particles.append(
                CombatParticle(kind="splat", x=proj.x, y=proj.y, vx=random.uniform(-20, 20), vy=random.uniform(-20, 20), color=(240, 140, 180), size=6.0, lifetime=0.18)
            )
            break
