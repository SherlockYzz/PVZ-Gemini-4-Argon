# -*- coding: utf-8 -*-
"""Modal and overlay renderers (Pause, Victory Award, and Game Over)."""

import pygame
from typing import Optional
from domain.model.session import Session
from domain.spec.rewards import LevelReward
from domain.spec.plants import PLANTS
from domain.spec.levels import LEVELS
from infra.pygame_fonts import get_font
from infra.sprites import get_sprites


def render_pause(surface: pygame.Surface) -> dict[str, pygame.Rect]:
    # Dim overlay
    dim = pygame.Surface((1200, 760), pygame.SRCALPHA)
    dim.fill((0, 0, 0, 160))
    surface.blit(dim, (0, 0))

    box = pygame.Rect(420, 200, 360, 340)
    pygame.draw.rect(surface, (45, 34, 25), box, border_radius=12)
    pygame.draw.rect(surface, (160, 120, 60), box, 3, border_radius=12)

    font_large = get_font(32, bold=True)
    font_mid = get_font(20, bold=True)

    t_lbl = font_large.render("游戏暂停", True, (255, 230, 90))
    surface.blit(t_lbl, (box.x + (box.width - t_lbl.get_width()) // 2, box.y + 30))

    buttons: dict[str, pygame.Rect] = {}

    resume_btn = pygame.Rect(box.x + 60, box.y + 100, 240, 50)
    buttons["resume"] = resume_btn
    pygame.draw.rect(surface, (60, 130, 50), resume_btn, border_radius=8)
    pygame.draw.rect(surface, (140, 220, 100), resume_btn, 2, border_radius=8)
    r_lbl = font_mid.render("继续游戏", True, (255, 255, 255))
    surface.blit(r_lbl, (resume_btn.x + (resume_btn.width - r_lbl.get_width()) // 2, resume_btn.y + 12))

    restart_btn = pygame.Rect(box.x + 60, box.y + 165, 240, 50)
    buttons["restart"] = restart_btn
    pygame.draw.rect(surface, (120, 80, 40), restart_btn, border_radius=8)
    pygame.draw.rect(surface, (220, 160, 90), restart_btn, 2, border_radius=8)
    rs_lbl = font_mid.render("重新开始", True, (255, 255, 255))
    surface.blit(rs_lbl, (restart_btn.x + (restart_btn.width - rs_lbl.get_width()) // 2, restart_btn.y + 12))

    menu_btn = pygame.Rect(box.x + 60, box.y + 230, 240, 50)
    buttons["menu"] = menu_btn
    pygame.draw.rect(surface, (110, 50, 45), menu_btn, border_radius=8)
    pygame.draw.rect(surface, (220, 120, 100), menu_btn, 2, border_radius=8)
    m_lbl = font_mid.render("返回主菜单", True, (255, 255, 255))
    surface.blit(m_lbl, (menu_btn.x + (menu_btn.width - m_lbl.get_width()) // 2, menu_btn.y + 12))

    return buttons


def render_victory(surface: pygame.Surface, reward: Optional[LevelReward]) -> dict[str, pygame.Rect]:
    dim = pygame.Surface((1200, 760), pygame.SRCALPHA)
    dim.fill((0, 0, 0, 185))
    surface.blit(dim, (0, 0))

    box_w = 660
    box_h = 510
    box = pygame.Rect((1200 - box_w) // 2, 110, box_w, box_h)
    pygame.draw.rect(surface, (34, 48, 28), box, border_radius=16)
    pygame.draw.rect(surface, (255, 215, 60), box, 4, border_radius=16)

    font_huge = get_font(36, bold=True)
    font_mid = get_font(18, bold=True)
    font_small = get_font(14)
    font_tiny = get_font(12, bold=True)
    sprites = get_sprites()

    # Title badge
    t_lbl = font_huge.render("★ 关 卡 大 捷 ★", True, (255, 235, 70))
    surface.blit(t_lbl, (box.x + (box.width - t_lbl.get_width()) // 2, box.y + 22))

    has_plants = bool(reward and reward.plants)
    has_artifact = bool(reward and reward.artifact)

    if has_plants:
        plants = reward.plants
        p_title = font_mid.render(f"恭喜解锁新植物图鉴 ({len(plants)} 株)：", True, (210, 255, 170))
        surface.blit(p_title, (box.x + 40, box.y + 78))

        # Horizontal card row
        n_p = len(plants)
        card_w, card_h = 56, 72
        slot_gap = 18
        row_w = n_p * card_w + (n_p - 1) * slot_gap
        row_start_x = box.x + (box.width - row_w) // 2
        cards_y = box.y + 112

        for pi, p_id in enumerate(plants):
            cx = row_start_x + pi * (card_w + slot_gap)
            spec = PLANTS.get(p_id)
            c_surf = sprites.get_card(p_id, (card_w, card_h))
            if c_surf:
                surface.blit(c_surf, (cx, cards_y))
            else:
                pygame.draw.rect(surface, (60, 110, 50), (cx, cards_y, card_w, card_h), border_radius=6)

            pygame.draw.rect(surface, (255, 225, 80), (cx, cards_y, card_w, card_h), 2, border_radius=6)
            name_str = spec.name if spec else p_id
            name_lbl = font_tiny.render(name_str, True, (255, 240, 160))
            surface.blit(name_lbl, (cx + (card_w - name_lbl.get_width()) // 2, cards_y + card_h + 6))

    # Show reward artifact
    art_y = box.y + 245 if has_plants else box.y + 110
    if has_artifact:
        art_box = pygame.Rect(box.x + 35, art_y, box.width - 70, 95)
        pygame.draw.rect(surface, (55, 42, 20), art_box, border_radius=10)
        pygame.draw.rect(surface, (255, 215, 60), art_box, 2, border_radius=10)

        a_title = font_mid.render(f"★ 荣获传世神器：【{reward.artifact_name}】★", True, (255, 225, 70))
        surface.blit(a_title, (art_box.x + (art_box.width - a_title.get_width()) // 2, art_box.y + 14))

        desc_txt = font_small.render(reward.artifact_desc[:44], True, (255, 235, 180))
        surface.blit(desc_txt, (art_box.x + (art_box.width - desc_txt.get_width()) // 2, art_box.y + 46))

    if not has_plants and not has_artifact:
        congrats_y = box.y + 170
        cg_lbl1 = font_mid.render("草坪与泳池在你的英明指挥下固若金汤！", True, (220, 255, 200))
        surface.blit(cg_lbl1, (box.x + (box.width - cg_lbl1.get_width()) // 2, congrats_y))
        cg_lbl2 = font_small.render("击溃尸潮侵袭，向着更深远的庭院荣耀进发吧！", True, (180, 220, 190))
        surface.blit(cg_lbl2, (box.x + (box.width - cg_lbl2.get_width()) // 2, congrats_y + 40))

    buttons: dict[str, pygame.Rect] = {}
    btn_y = box.bottom - 78
    next_btn = pygame.Rect(box.x + 80, btn_y, 220, 50)
    buttons["next_level"] = next_btn
    pygame.draw.rect(surface, (50, 140, 55), next_btn, border_radius=10)
    pygame.draw.rect(surface, (160, 250, 130), next_btn, 2, border_radius=10)
    nxt_lbl = font_mid.render("进入下一关 >>", True, (255, 255, 255))
    surface.blit(nxt_lbl, (next_btn.x + (next_btn.width - nxt_lbl.get_width()) // 2, next_btn.y + 14))

    menu_btn = pygame.Rect(box.right - 300, btn_y, 220, 50)
    buttons["menu"] = menu_btn
    pygame.draw.rect(surface, (120, 55, 45), menu_btn, border_radius=10)
    pygame.draw.rect(surface, (230, 140, 120), menu_btn, 2, border_radius=10)
    m_lbl = font_mid.render("返回主菜单", True, (255, 255, 255))
    surface.blit(m_lbl, (menu_btn.x + (menu_btn.width - m_lbl.get_width()) // 2, menu_btn.y + 14))

    return buttons


def render_game_over(surface: pygame.Surface) -> dict[str, pygame.Rect]:
    dim = pygame.Surface((1200, 760), pygame.SRCALPHA)
    dim.fill((0, 0, 0, 200))
    surface.blit(dim, (0, 0))

    box = pygame.Rect(380, 220, 440, 300)
    pygame.draw.rect(surface, (50, 25, 25), box, border_radius=12)
    pygame.draw.rect(surface, (220, 60, 50), box, 3, border_radius=12)

    font_huge = get_font(36, bold=True)
    font_mid = get_font(20, bold=True)

    t_lbl = font_huge.render("僵尸吃掉了你的脑子！", True, (255, 90, 80))
    surface.blit(t_lbl, (box.x + (box.width - t_lbl.get_width()) // 2, box.y + 40))

    buttons: dict[str, pygame.Rect] = {}
    retry_btn = pygame.Rect(box.x + 50, box.y + 150, 160, 50)
    buttons["retry"] = retry_btn
    pygame.draw.rect(surface, (120, 60, 40), retry_btn, border_radius=8)
    pygame.draw.rect(surface, (240, 140, 90), retry_btn, 2, border_radius=8)
    rt_lbl = font_mid.render("重新再战", True, (255, 255, 255))
    surface.blit(rt_lbl, (retry_btn.x + (retry_btn.width - rt_lbl.get_width()) // 2, retry_btn.y + 12))

    menu_btn = pygame.Rect(box.right - 210, box.y + 150, 160, 50)
    buttons["menu"] = menu_btn
    pygame.draw.rect(surface, (70, 70, 70), menu_btn, border_radius=8)
    pygame.draw.rect(surface, (160, 160, 160), menu_btn, 2, border_radius=8)
    m_lbl = font_mid.render("返回主菜单", True, (255, 255, 255))
    surface.blit(m_lbl, (menu_btn.x + (menu_btn.width - m_lbl.get_width()) // 2, menu_btn.y + 12))

    return buttons


def render_warp_overlay(surface: pygame.Surface, session: Session, mouse_pos: tuple[float, float]) -> dict[str, pygame.Rect]:
    """Renders the Time-Warp Portal overlay for instant jumping across all 16 levels."""
    dim = pygame.Surface((1200, 760), pygame.SRCALPHA)
    dim.fill((17, 28, 23, 175))
    surface.blit(dim, (0, 0))

    box = pygame.Rect(140, 45, 920, 655)
    # Vintage parchment window
    pygame.draw.rect(surface, (246, 238, 212), box, border_radius=16)
    pygame.draw.rect(surface, (68, 52, 28), box, 4, border_radius=16)

    font_title = get_font(22, bold=True)
    font_desc = get_font(13)
    font_card_title = get_font(13, bold=True)
    font_tiny = get_font(11, bold=True)
    font_btn = get_font(15, bold=True)

    # Title & Help Hint
    t_lbl = font_title.render("【时空穿梭 · 任意跳关传送门】", True, (62, 42, 18))
    surface.blit(t_lbl, (box.x + (box.width - t_lbl.get_width()) // 2, box.y + 14))

    desc_lbl = font_desc.render("点击任意关卡秒速直达并自动补齐所有战利品！快捷键：[Tab]/[N] 下一关 | [P] 上一关 | [L]/[Esc] 关闭", True, (115, 90, 55))
    surface.blit(desc_lbl, (box.x + (box.width - desc_lbl.get_width()) // 2, box.y + 44))

    pygame.draw.line(surface, (185, 160, 120), (box.x + 20, box.y + 68), (box.right - 20, box.y + 68), 2)

    buttons: dict[str, pygame.Rect] = {}
    card_w = 205
    card_h = 76
    gap_x = 16
    gap_y = 10
    wx0 = box.x + (box.width - (4 * card_w + 3 * gap_x)) // 2
    wy0 = box.y + 78
    mx, my = mouse_pos

    for i in range(len(LEVELS)):
        col = i % 4
        row = i // 4
        wrect = pygame.Rect(wx0 + col * (card_w + gap_x), wy0 + row * (card_h + gap_y), card_w, card_h)
        buttons[f"warp_{i}"] = wrect
        hover = wrect.collidepoint(mx, my)
        is_cur = (i == session.current_level_idx)

        theme = LEVELS[i].theme
        if "pool" in theme:
            bg_c = (235, 250, 255) if hover else (220, 242, 255)
            bd_c = (255, 195, 45) if is_cur else (45, 120, 180)
        elif theme == "night":
            bg_c = (240, 235, 255) if hover else (225, 220, 240)
            bd_c = (255, 195, 45) if is_cur else (110, 85, 160)
        else:
            bg_c = (255, 252, 235) if hover else (240, 245, 220)
            bd_c = (255, 195, 45) if is_cur else (80, 135, 60)

        pygame.draw.rect(surface, bg_c, wrect, border_radius=8)
        border_thickness = 3 if is_cur or hover else 1
        pygame.draw.rect(surface, bd_c, wrect, border_thickness, border_radius=8)

        # Card Content
        lvl_num_lbl = font_card_title.render(f"第 {i + 1:02d} 关", True, (160, 80, 20) if is_cur else (60, 45, 30))
        surface.blit(lvl_num_lbl, (wrect.x + 8, wrect.y + 6))

        tag_text = "[当前关卡]" if is_cur else ("[泳池水面]" if "pool" in theme else ("[暗夜墓地]" if "night" in theme else "[白天草坪]"))
        tag_col = (200, 120, 20) if is_cur else ((30, 100, 160) if "pool" in theme else (80, 110, 70))
        tag_lbl = font_tiny.render(tag_text, True, tag_col)
        surface.blit(tag_lbl, (wrect.right - tag_lbl.get_width() - 8, wrect.y + 8))

        # Level name
        name_lbl = font_desc.render(LEVELS[i].name[:12], True, (40, 30, 20))
        surface.blit(name_lbl, (wrect.x + 8, wrect.y + 28))

        # Zombie count info
        wave_str = f"难度: {LEVELS[i].zombie_count} 只僵尸"
        w_lbl = font_tiny.render(wave_str, True, (110, 95, 75))
        surface.blit(w_lbl, (wrect.x + 8, wrect.y + 52))

    # Bottom action buttons
    next_btn = pygame.Rect(box.centerx - 190, box.bottom - 54, 170, 42)
    buttons["warp_next"] = next_btn
    pygame.draw.rect(surface, (50, 145, 65), next_btn, border_radius=8)
    pygame.draw.rect(surface, (255, 220, 90), next_btn, 2, border_radius=8)
    n_lbl = font_btn.render("下一关 >> [Tab]", True, (255, 255, 255))
    surface.blit(n_lbl, (next_btn.x + (next_btn.width - n_lbl.get_width()) // 2, next_btn.y + 10))

    close_btn = pygame.Rect(box.centerx + 20, box.bottom - 54, 170, 42)
    buttons["warp_close"] = close_btn
    pygame.draw.rect(surface, (140, 60, 50), close_btn, border_radius=8)
    pygame.draw.rect(surface, (240, 180, 160), close_btn, 2, border_radius=8)
    c_lbl = font_btn.render("返回战斗 [Esc]", True, (255, 255, 255))
    surface.blit(c_lbl, (close_btn.x + (close_btn.width - c_lbl.get_width()) // 2, close_btn.y + 10))

    return buttons
