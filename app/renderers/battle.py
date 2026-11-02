# -*- coding: utf-8 -*-
"""Battlefield Renderer.
Draws lawn maps, cell highlights, mowers, carriers, plants, zombies, projectiles,
suns, combat particles, screen shake, and floating damage numbers.
"""

import math
import random
import pygame
from typing import Optional
from domain.model.world import World
from domain.model.session import Session
from domain.spec.levels import LEVELS
from domain.spec.field_layout import FieldLayout, LAND_LAYOUT, POOL_LAYOUT
from infra.sprites import get_sprites
from infra.pygame_fonts import get_font


_BACKGROUND_CACHE: dict[str, pygame.Surface] = {}
_GRID_OVERLAY_CACHE: dict[str, pygame.Surface] = {}


def _lerp_color(c1: tuple[int, int, int], c2: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


def _draw_house_edge(surface: pygame.Surface, layout: FieldLayout) -> None:
    grid_x = layout.origin_x
    grid_y = layout.origin_y
    total_h = layout.rows * layout.cell_h + 28
    pygame.draw.rect(surface, (78, 59, 44), (0, grid_y - 14, grid_x, total_h))
    pygame.draw.rect(surface, (114, 88, 64), (0, grid_y - 14, grid_x - 12, total_h))
    for row in range(layout.rows):
        y = grid_y + row * layout.cell_h
        pygame.draw.rect(surface, (91, 70, 52), (grid_x - 18, y + 8, 12, layout.cell_h - 16), border_radius=3)
        pygame.draw.line(surface, (54, 40, 30), (0, y), (grid_x, y), 2)


def _draw_right_garden(surface: pygame.Surface, theme: str, layout: FieldLayout) -> None:
    fence_color = (196, 189, 162) if "night" not in theme else (120, 130, 125)
    shadow = (42, 68, 48)
    grid_right = layout.grid_right
    grid_y = layout.origin_y
    grid_bottom = grid_y + layout.rows * layout.cell_h
    for x in range(grid_right + 8, 1200 + 20, 26):
        pygame.draw.polygon(
            surface, shadow,
            [(x - 2, grid_y - 8), (x + 10, grid_y - 18), (x + 22, grid_y - 8), (x + 22, grid_bottom + 8), (x - 2, grid_bottom + 8)],
        )
        pygame.draw.polygon(
            surface, fence_color,
            [(x, grid_y - 10), (x + 10, grid_y - 20), (x + 20, grid_y - 10), (x + 20, grid_bottom + 6), (x, grid_bottom + 6)],
        )
    pygame.draw.line(surface, fence_color, (grid_right + 2, grid_y + 50), (1200, grid_y + 50), 6)
    pygame.draw.line(surface, fence_color, (grid_right + 2, grid_bottom - 60), (1200, grid_bottom - 60), 6)


def get_grid_overlay(layout: FieldLayout, is_pool: bool) -> pygame.Surface:
    """Pre-baked 1200x760 transparent grid overlay to avoid creating 54 surfaces per frame."""
    key = f"{is_pool}_{layout.origin_x}_{layout.cell_w}_{layout.cell_h}"
    if key in _GRID_OVERLAY_CACHE:
        return _GRID_OVERLAY_CACHE[key]

    overlay = pygame.Surface((1200, 760), pygame.SRCALPHA)
    for c in range(layout.cols):
        for r in range(layout.rows):
            cx, cy, cw, ch = layout.get_cell_rect(c, r)
            border_c = (120, 220, 255, 45) if (is_pool and r in layout.pool_rows) else (35, 75, 35, 40)
            pygame.draw.rect(overlay, border_c, (cx, cy, cw, ch), 1)

    _GRID_OVERLAY_CACHE[key] = overlay
    return overlay


def get_procedural_background(theme: str, layout: Optional[FieldLayout] = None, is_pool: bool = False) -> pygame.Surface:
    if layout is None:
        layout = POOL_LAYOUT if (is_pool or "pool" in theme) else LAND_LAYOUT
    key = f"{theme}_{layout.is_pool}_{layout.origin_x}_{layout.cell_w}_{layout.cell_h}"
    if key in _BACKGROUND_CACHE:
        return _BACKGROUND_CACHE[key]

    width, height = 1200, 760
    surface = pygame.Surface((width, height))
    grid_x = layout.origin_x
    grid_y = layout.origin_y
    cols = layout.cols
    rows = layout.rows
    cell_w = layout.cell_w
    cell_h = layout.cell_h
    grid_bottom = grid_y + rows * cell_h
    grid_right = layout.grid_right
    is_pool = layout.is_pool

    palettes = {
        "day": ((108, 185, 224), (205, 237, 244), (112, 188, 77), (95, 168, 65)),
        "dusk": ((219, 125, 78), (252, 203, 137), (142, 171, 72), (119, 149, 58)),
        "night": ((18, 32, 44), (43, 67, 85), (63, 122, 69), (48, 102, 57)),
        "pool_day": ((108, 185, 224), (205, 237, 244), (112, 188, 77), (95, 168, 65)),
        "pool_night": ((18, 32, 44), (43, 67, 85), (63, 122, 69), (48, 102, 57)),
    }
    sky_top, sky_bottom, grass_light, grass_dark = palettes.get(theme, palettes["day"])

    # 1. Base dark lawn
    surface.fill(grass_dark)

    # 2. Gradient Sky
    for y in range(0, grid_y):
        ratio = y / grid_y
        col = _lerp_color(sky_top, sky_bottom, ratio)
        pygame.draw.line(surface, col, (0, y), (width, y))

    # 3. Sky Ornaments (Sun, Dusk Sunset, Stars & Crescent Moon)
    if "night" in theme:
        rng = random.Random(42)
        for _ in range(70):
            sx = rng.randint(0, width)
            sy = rng.randint(0, grid_bottom)
            pygame.draw.circle(surface, (245, 247, 218), (sx, sy), 1.5 if rng.random() > 0.5 else 1.0)
        pygame.draw.circle(surface, (255, 252, 214), (1040, 68), 28)
        pygame.draw.circle(surface, sky_top, (1054, 62), 26)
    elif theme == "dusk":
        pygame.draw.circle(surface, (255, 172, 85), (960, 95), 38)
        pygame.draw.circle(surface, (255, 232, 148), (960, 95), 32)
    else:
        # Daytime glowing sun
        pygame.draw.circle(surface, (255, 240, 130), (1080, 58), 34)
        pygame.draw.circle(surface, (255, 215, 0), (1080, 58), 24)
        pygame.draw.circle(surface, (255, 248, 180), (1080, 58), 16)

    # 4. Lawn Checkerboard Grid & Pool Tiles (Pixel-perfect alignment with layout)
    for c in range(cols):
        for r in range(rows):
            cx, cy, cw, ch = layout.get_cell_rect(c, r)
            cell_rect = pygame.Rect(cx, cy, cw, ch)
            if is_pool and r in layout.pool_rows:
                water_c = (52, 148, 204) if (c + r) % 2 == 0 else (42, 128, 182)
                pygame.draw.rect(surface, water_c, cell_rect)
                pygame.draw.rect(surface, (80, 180, 230), cell_rect, 1)
            else:
                base = grass_light if (c + r) % 2 == 0 else grass_dark
                pygame.draw.rect(surface, base, cell_rect)
                pygame.draw.rect(surface, _lerp_color(base, (22, 50, 28), 0.16), cell_rect, 1)

    # 5. Grid Lines
    for r in range(rows + 1):
        y = grid_y + r * cell_h
        pygame.draw.line(surface, (45, 96, 48), (grid_x - 10, y), (grid_right + 10, y), 2)
    for c in range(cols + 1):
        x = grid_x + c * cell_w
        pygame.draw.line(surface, (45, 96, 48), (x, grid_y), (x, grid_bottom), 1)

    # 6. House Edge & Right Garden Fence
    _draw_house_edge(surface, layout)
    _draw_right_garden(surface, theme, layout)

    _BACKGROUND_CACHE[key] = surface
    return surface


def render_battle(
    surface: pygame.Surface,
    world: World,
    session: Session,
    mouse_pos: tuple[float, float],
) -> None:
    sprites = get_sprites()
    font_small = get_font(14, bold=True)
    font_bold = get_font(18, bold=True)

    level_idx = session.current_level_idx
    level_spec = LEVELS[level_idx] if 0 <= level_idx < len(LEVELS) else LEVELS[0]
    theme = level_spec.theme

    # 1. Screen Shake impulse
    ox, oy = world.shake.update(0.0)

    # 2. Lawn / Pool Map Background
    map_surf = sprites.get_map(theme)
    if map_surf:
        surface.blit(map_surf, (ox, oy))
        # Subtle pre-baked cell boundary guide overlay
        grid_overlay = get_grid_overlay(world.layout, level_spec.is_pool)
        surface.blit(grid_overlay, (ox, oy))
    else:
        # Full procedural lawn with checkerboard grid, sky, house and fence
        bg = get_procedural_background(theme, world.layout)
        surface.blit(bg, (ox, oy))

    # 3. Cell Hover Highlight (Guaranteed Pixel-Perfect Alignment)
    mx, my = mouse_pos
    col, row = world.layout.pos_to_cell(mx, my)
    if col is not None and row is not None:
        if session.active_seed_idx is not None or session.active_shovel:
            cx, cy, cw, ch = world.layout.get_cell_rect(col, row)
            highlight_color = (255, 235, 60, 90) if session.active_seed_idx is not None else (255, 100, 80, 90)
            hs = pygame.Surface((cw, ch), pygame.SRCALPHA)
            hs.fill(highlight_color)
            surface.blit(hs, (cx + ox, cy + oy))
            pygame.draw.rect(surface, (255, 240, 100), (cx + ox, cy + oy, cw, ch), 2)

    # 4. Lawnmowers and Pool Cleaners
    for m in world.mowers:
        if m.active:
            m_surf = sprites.get_mower(is_pool=m.is_pool)
            if m_surf:
                surface.blit(m_surf, (m.x - 32 + ox, m.y - 26 + oy))
            else:
                pygame.draw.rect(surface, (200, 50, 40), (m.x - 25 + ox, m.y - 20 + oy, 50, 40), border_radius=6)

    # 5. Carriers (Lilypads)
    for (c, r), carrier in world.carriers.items():
        if carrier.is_alive:
            sprites.render_plant(
                surface, "lilypad", (carrier.x + ox, carrier.y + oy),
                scale=carrier.scale, time_val=world.game_time, hp_ratio=1.0, age=carrier.age, plant=carrier
            )

    # 6. Plants
    for (c, r), plant in world.plants.items():
        if not plant.is_alive:
            continue

        sprites.render_plant(
            surface, plant.spec_id, (plant.x + ox, plant.y + oy),
            scale=plant.scale, time_val=world.game_time,
            hp_ratio=plant.hp / plant.max_hp, age=plant.age, plant=plant
        )

        # Health bar if damaged
        if plant.hp < plant.max_hp:
            bar_w = 46
            bar_h = 6
            bx = plant.x - bar_w // 2 + ox
            by = plant.y - 48 + oy
            ratio = max(0.0, plant.hp / plant.max_hp)
            pygame.draw.rect(surface, (30, 30, 30), (bx, by, bar_w, bar_h))
            pygame.draw.rect(surface, (60, 220, 60), (bx, by, int(bar_w * ratio), bar_h))

    # 7. Zombies (Sorted by Row and X for Proper Depth Layering)
    sorted_zombies = sorted(world.zombies, key=lambda z: (z.row, -z.x))
    for z in sorted_zombies:
        if not z.is_alive:
            continue

        # Hypno glowing halo
        if z.hypnotized:
            pygame.draw.circle(surface, (200, 100, 255), (int(z.x + ox), int(z.y - 30 + oy)), 38, 3)

        sprites.render_zombie(surface, z, time_val=world.game_time, ground_y=z.y + oy)

        # Butter pat on head when butter-stunned!
        if z.butter_timer > 0:
            bx = z.x - 14 + ox
            by = z.y - 74 + oy
            pygame.draw.rect(surface, (255, 230, 80), (bx, by, 28, 14), border_radius=3)
            pygame.draw.rect(surface, (200, 170, 40), (bx, by, 28, 14), 2, border_radius=3)

    # 8. Projectiles
    for p in world.projectiles:
        if not p.alive:
            continue

        if p.bullet_type == "butter":
            # Yellow butter chunk
            pygame.draw.rect(surface, (255, 235, 90), (p.x - 10 + ox, p.y - 8 + oy, 20, 16), border_radius=3)
            pygame.draw.rect(surface, (210, 180, 50), (p.x - 10 + ox, p.y - 8 + oy, 20, 16), 1, border_radius=3)
        elif p.bullet_type in ("melon", "wintermelon"):
            col = (140, 230, 255) if p.bullet_type == "wintermelon" else (70, 170, 60)
            pygame.draw.circle(surface, col, (int(p.x + ox), int(p.y + oy)), 15)
            pygame.draw.circle(surface, (30, 80, 25), (int(p.x + ox), int(p.y + oy)), 15, 2)
        elif p.bullet_type == "spike":
            # Cattail needle
            pygame.draw.line(surface, (220, 100, 140), (p.x - 8 + ox, p.y + oy), (p.x + 8 + ox, p.y + oy), 3)
        else:
            is_fire = p.bullet_type in ("firepea", "fire_pea")
            is_freeze = p.bullet_type in ("snowpea", "pea_ice")

            # Fire pea flame glow aura
            if is_fire:
                glow_surf = pygame.Surface((36, 36), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (255, 120, 20, 65), (18, 18), 16)
                pygame.draw.circle(glow_surf, (255, 200, 50, 110), (18, 18), 10)
                surface.blit(glow_surf, (p.x - 18 + ox, p.y - 18 + oy))

            b_surf = sprites.get_bullet(p.bullet_type, is_freeze=is_freeze, size=24)
            if b_surf:
                surface.blit(b_surf, (p.x - b_surf.get_width() // 2 + ox, p.y - b_surf.get_height() // 2 + oy))
            else:
                col = (120, 220, 255) if is_freeze else (255, 120, 30) if is_fire else (140, 230, 60)
                pygame.draw.circle(surface, col, (int(p.x + ox), int(p.y + oy)), 8)

    # 9. Suns
    for s in world.suns:
        if s.state == "collected":
            continue
        sun_surf = sprites.get_sun(world.game_time + s.id, radius=s.radius)
        if sun_surf:
            surface.blit(sun_surf, (s.x - s.radius + ox, s.y - s.radius + oy))
        else:
            pygame.draw.circle(surface, (255, 235, 60), (int(s.x + ox), int(s.y + oy)), int(s.radius))

    # 10. Combat Particles & Floating Texts
    for pt in world.particles:
        if pt.alive:
            if pt.kind == "slash":
                sx, sy = int(pt.x + ox), int(pt.y + oy)
                pygame.draw.line(surface, pt.color, (sx - 8, sy + 8), (sx + 8, sy - 8), 3)
            else:
                pygame.draw.circle(surface, pt.color, (int(pt.x + ox), int(pt.y + oy)), int(pt.size))

    for ft in world.floating_texts:
        if ft.alive:
            txt_surf = font_bold.render(ft.text, True, ft.color)
            txt_surf.set_alpha(ft.alpha)
            # High-visibility dark badge for warning messages
            if ft.text.startswith("⚠") or "必须" in ft.text or "阳光" in ft.text or "冷却" in ft.text:
                tw, th = txt_surf.get_size()
                bg_rect = pygame.Rect(int(ft.x + ox - 8), int(ft.y + oy - 4), tw + 16, th + 8)
                badge_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
                badge_surf.fill((20, 15, 15, int(195 * (ft.alpha / 255.0))))
                surface.blit(badge_surf, bg_rect.topleft)
                pygame.draw.rect(surface, (255, 100, 80, int(220 * (ft.alpha / 255.0))), bg_rect, 1, border_radius=4)
            surface.blit(txt_surf, (ft.x + ox, ft.y + oy))
