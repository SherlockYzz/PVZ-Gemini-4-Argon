# -*- coding: utf-8 -*-
"""HUD Renderer.
Renders the top card conveyor bar, sun economy counter, shovel,
auto-sun magnet toggle, and wave progress bar.
"""

import pygame
from typing import Optional
from config.tuning import C_GOLD, C_SUN, C_DARK, C_GREEN, C_RED, C_CREAM
from domain.model.world import World
from domain.model.session import Session
from domain.spec.plants import PLANTS
from infra.pygame_fonts import get_font
from infra.sprites import get_sprites
from app.hud_layout import compute_hud_layout, HudRects


def render_hud(
    surface: pygame.Surface,
    world: World,
    session: Session,
    mouse_pos: tuple[float, float],
    layout_rects: Optional[HudRects] = None,
) -> None:
    if layout_rects is None or len(layout_rects.card_slots) != session.max_seed_slots:
        layout_rects = compute_hud_layout(session.max_seed_slots)

    sprites = get_sprites()
    font_bold = get_font(20, bold=True)
    font_small = get_font(14, bold=True)
    font_tiny = get_font(12, bold=True)

    # 1. Top HUD wooden background strip
    bg_bar = pygame.Rect(0, 0, 1200, 92)
    pygame.draw.rect(surface, (45, 30, 20), bg_bar)
    pygame.draw.line(surface, (100, 70, 45), (0, 92), (1200, 92), 3)

    # 2. Sun Counter
    sc_rect = layout_rects.sun_counter
    pygame.draw.rect(surface, (70, 48, 32), sc_rect, border_radius=8)
    pygame.draw.rect(surface, (180, 140, 70), sc_rect, 2, border_radius=8)

    # Sun Icon
    sun_icon = sprites.get_sun(world.game_time, radius=18)
    if sun_icon:
        surface.blit(sun_icon, (sc_rect.x + 8, sc_rect.y + 12))
    else:
        pygame.draw.circle(surface, C_SUN, (sc_rect.x + 28, sc_rect.y + 38), 18)

    # Sun number text
    sun_text = font_bold.render(str(world.sun), True, C_SUN)
    surface.blit(sun_text, (sc_rect.x + 54, sc_rect.y + 24))

    # 3. Card Slots (defensive bounds to completely eliminate IndexError)
    num_slots = min(session.max_seed_slots, len(layout_rects.card_slots))
    for i in range(num_slots):
        rect = layout_rects.card_slots[i]
        # Slot frame
        pygame.draw.rect(surface, (32, 22, 16), rect, border_radius=6)
        pygame.draw.rect(surface, (90, 65, 45), rect, 2, border_radius=6)

        if i < len(session.selected_seeds):
            spec_id = session.selected_seeds[i]
            spec = PLANTS.get(spec_id)
            if not spec:
                continue

            card_surf = sprites.get_card(spec_id, (rect.width - 4, rect.height - 4))
            if card_surf:
                surface.blit(card_surf, (rect.x + 2, rect.y + 2))
            else:
                # Fallback block
                pygame.draw.rect(surface, (60, 100, 50), (rect.x + 2, rect.y + 2, rect.width - 4, rect.height - 4), border_radius=4)
                name_lbl = font_tiny.render(spec.name[:2], True, C_CREAM)
                surface.blit(name_lbl, (rect.x + 6, rect.y + 8))

            # Cooldown shadow mask
            cd = session.seed_cooldowns.get(spec_id, 0.0)
            if cd > 0:
                cd_ratio = min(1.0, max(0.0, cd / spec.cooldown)) if spec.cooldown > 0 else 0.0
                mask_h = int(rect.height * cd_ratio)
                cd_rect = pygame.Rect(rect.x, rect.bottom - mask_h, rect.width, mask_h)
                s = pygame.Surface((rect.width, mask_h), pygame.SRCALPHA)
                s.fill((0, 0, 0, 160))
                surface.blit(s, (rect.x, rect.bottom - mask_h))

            # Sun cost shortage darkening
            if world.sun < spec.cost and cd <= 0:
                s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                s.fill((0, 0, 0, 90))
                surface.blit(s, rect)

            # Selected highlight
            if session.active_seed_idx == i:
                pygame.draw.rect(surface, (255, 235, 60), rect, 3, border_radius=6)

            # Cost label in bottom-right
            cost_lbl = font_tiny.render(str(spec.cost), True, C_SUN)
            surface.blit(cost_lbl, (rect.right - cost_lbl.get_width() - 4, rect.bottom - 16))

            # Key shortcut hint (1..9, 0 for 10th slot)
            hint_str = "0" if i == 9 else str(i + 1)
            key_hint = font_tiny.render(hint_str, True, (190, 190, 190))
            surface.blit(key_hint, (rect.x + 4, rect.y + 3))

    # 4. Shovel Button
    sh_rect = layout_rects.shovel_button
    sh_bg = (140, 110, 40) if "golden_shovel" in session.unlocked_artifacts else (60, 45, 30)
    pygame.draw.rect(surface, sh_bg, sh_rect, border_radius=6)
    sh_border = (255, 220, 50) if session.active_shovel else (120, 90, 50)
    pygame.draw.rect(surface, sh_border, sh_rect, 3 if session.active_shovel else 2, border_radius=6)

    sh_lbl = font_bold.render("铲子", True, (255, 240, 200))
    surface.blit(sh_lbl, (sh_rect.x + (sh_rect.width - sh_lbl.get_width()) // 2, sh_rect.y + 12))
    sh_key = font_tiny.render("[S]", True, (220, 220, 160))
    surface.blit(sh_key, (sh_rect.x + (sh_rect.width - sh_key.get_width()) // 2, sh_rect.y + 40))

    # 5. Buttons (Speed, Pause, Skip, Auto-Sun)
    # Speed Toggle
    spd_rect = layout_rects.speed_button
    spd_text = "2X" if session.speed_multiplier > 1.0 else "1X"
    pygame.draw.rect(surface, (50, 75, 40) if session.speed_multiplier > 1.0 else (55, 45, 35), spd_rect, border_radius=6)
    pygame.draw.rect(surface, (140, 180, 100), spd_rect, 2, border_radius=6)
    s_lbl = font_small.render(spd_text, True, C_CREAM)
    surface.blit(s_lbl, (spd_rect.x + (spd_rect.width - s_lbl.get_width()) // 2, spd_rect.y + 8))

    # Pause Button
    p_rect = layout_rects.pause_button
    pygame.draw.rect(surface, (55, 45, 35), p_rect, border_radius=6)
    pygame.draw.rect(surface, (140, 110, 80), p_rect, 2, border_radius=6)
    p_lbl = font_small.render("暂停", True, C_CREAM)
    surface.blit(p_lbl, (p_rect.x + (p_rect.width - p_lbl.get_width()) // 2, p_rect.y + 8))

    # Skip / Warp Button (Golden highlighted portal trigger)
    sk_rect = layout_rects.skip_button
    pygame.draw.rect(surface, (75, 52, 28), sk_rect, border_radius=6)
    pygame.draw.rect(surface, (255, 215, 60), sk_rect, 2, border_radius=6)
    sk_lbl = font_small.render("跳关", True, (255, 235, 110))
    surface.blit(sk_lbl, (sk_rect.x + (sk_rect.width - sk_lbl.get_width()) // 2, sk_rect.y + 8))

    # Auto-Sun Magnet Toggle
    if session.has_auto_sun:
        as_rect = layout_rects.auto_sun_toggle
        is_on = session.auto_sun_enabled
        as_bg = (35, 85, 45) if is_on else (65, 45, 40)
        pygame.draw.rect(surface, as_bg, as_rect, border_radius=6)
        border_col = (100, 220, 120) if is_on else (160, 100, 90)
        pygame.draw.rect(surface, border_col, as_rect, 2, border_radius=6)

        label = "自吸:开 [A]" if is_on else "自吸:关 [A]"
        as_lbl = font_small.render(label, True, (240, 255, 230) if is_on else (220, 180, 170))
        surface.blit(as_lbl, (as_rect.x + (as_rect.width - as_lbl.get_width()) // 2, as_rect.y + 8))

    # 6. Wave Progress Bar
    pb_rect = layout_rects.progress_bar
    pygame.draw.rect(surface, (40, 30, 25), pb_rect, border_radius=6)
    pygame.draw.rect(surface, (120, 90, 60), pb_rect, 2, border_radius=6)

    wave_ratio = world.wave_state.progress_ratio
    fill_w = int((pb_rect.width - 4) * wave_ratio)
    if fill_w > 0:
        fill_rect = pygame.Rect(pb_rect.right - 2 - fill_w, pb_rect.y + 2, fill_w, pb_rect.height - 4)
        pygame.draw.rect(surface, (80, 180, 70), fill_rect, border_radius=4)

    # Flag icon at beginning of progress bar
    flag_x = pb_rect.x + 12
    pygame.draw.line(surface, (200, 200, 200), (flag_x, pb_rect.y - 10), (flag_x, pb_rect.bottom), 2)
    pygame.draw.polygon(surface, C_RED, [(flag_x, pb_rect.y - 10), (flag_x - 12, pb_rect.y - 4), (flag_x, pb_rect.y + 2)])

    # 7. Dragging Seed / Shovel Cursor Follower
    mx, my = mouse_pos
    if session.active_shovel:
        # Draw floating shovel icon under cursor
        sh_lbl = font_bold.render("铲", True, (255, 230, 80))
        surface.blit(sh_lbl, (mx + 10, my - 20))
    elif session.active_seed_idx is not None and session.active_seed_idx < len(session.selected_seeds):
        spec_id = session.selected_seeds[session.active_seed_idx]
        cursor_card = sprites.get_card(spec_id, (54, 68))
        if cursor_card:
            surface.blit(cursor_card, (mx - 27, my - 34))
