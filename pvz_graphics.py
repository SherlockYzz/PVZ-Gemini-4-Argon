# -*- coding: utf-8 -*-
"""PVZ 原版高清素材管理与极致性能平滑渲染引擎
包含植物、僵尸、卡牌、阳光、子弹与推车的正版纹理加载、动画帧流转、冰冻色调滤镜与受击反馈。
通过双层缓存与预缩放机制彻底杜绝主线程掉帧与内存泄漏。
"""

from __future__ import annotations

import math
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pygame

ASSETS_DIR = Path(__file__).parent / "assets"

# 贴图原始帧与结构缓存
_PLANT_FRAMES: Dict[str, Dict[str, List[pygame.Surface]]] = {}
_ZOMBIE_FRAMES: Dict[str, Dict[str, List[pygame.Surface]]] = {}
_CARD_SURFACES: Dict[str, pygame.Surface] = {}
_ITEM_SURFACES: Dict[str, pygame.Surface] = {}
_MAP_SURFACES: Dict[str, pygame.Surface] = {}
_SUN_FRAMES: List[pygame.Surface] = []

# 运行时几何尺寸与特效缓存 (彻底消除每帧分配与双线性插值 CPU 瓶颈)
_SCALED_CACHE: Dict[Tuple[int, int, int], pygame.Surface] = {}
_FROZEN_CACHE: Dict[int, pygame.Surface] = {}
_ALPHA_CACHE: Dict[Tuple[int, int], pygame.Surface] = {}
_SUN_SCALED_CACHE: Dict[Tuple[int, int], pygame.Surface] = {}


def _load_png(path: Path) -> Optional[pygame.Surface]:
    if not path.exists():
        return None
    try:
        surf = pygame.image.load(str(path))
        try:
            return surf.convert_alpha()
        except Exception:
            return surf
    except Exception:
        return None


def init_graphics() -> None:
    """预加载核心贴图，预先建立索引"""
    if not ASSETS_DIR.exists():
        return

    # 1. 卡牌 (10种植物原版卡牌)
    cards_dir = ASSETS_DIR / "cards"
    if cards_dir.exists():
        for card_file in cards_dir.glob("card_*.png"):
            plant_name = card_file.stem.replace("card_", "")
            surf = _load_png(card_file)
            if surf:
                _CARD_SURFACES[plant_name] = surf

    # 2. 物品 (推车、铲子、子弹)
    items_dir = ASSETS_DIR / "items"
    if items_dir.exists():
        for item_file in items_dir.glob("*.png"):
            surf = _load_png(item_file)
            if surf:
                _ITEM_SURFACES[item_file.stem] = surf

        # 阳光帧 (sun_0 .. sun_21)
        sun_dir = items_dir / "sun"
        if sun_dir.exists():
            frames = []
            for i in range(30):
                f = sun_dir / f"sun_{i}.png"
                if f.exists():
                    s = _load_png(f)
                    if s:
                        frames.append(s)
            if frames:
                _SUN_FRAMES.clear()
                _SUN_FRAMES.extend(frames)

    # 3. 植物序列帧
    plants_dir = ASSETS_DIR / "plants"
    if plants_dir.exists():
        for p_type_dir in plants_dir.iterdir():
            if not p_type_dir.is_dir():
                continue
            p_type = p_type_dir.name
            _PLANT_FRAMES[p_type] = {}
            for png_file in p_type_dir.glob("*.png"):
                parts = png_file.stem.rsplit("_", 1)
                action = parts[0]
                surf = _load_png(png_file)
                if surf:
                    _PLANT_FRAMES[p_type].setdefault(action, []).append(
                        (int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0, surf)
                    )
            for action in _PLANT_FRAMES[p_type]:
                _PLANT_FRAMES[p_type][action].sort(key=lambda x: x[0])
                _PLANT_FRAMES[p_type][action] = [s for _, s in _PLANT_FRAMES[p_type][action]]

    # 4. 僵尸序列帧
    zombies_dir = ASSETS_DIR / "zombies"
    if zombies_dir.exists():
        for z_type_dir in zombies_dir.iterdir():
            if not z_type_dir.is_dir():
                continue
            z_type = z_type_dir.name
            _ZOMBIE_FRAMES[z_type] = {}
            for png_file in z_type_dir.glob("*.png"):
                parts = png_file.stem.rsplit("_", 1)
                action = parts[0]
                surf = _load_png(png_file)
                if surf:
                    _ZOMBIE_FRAMES[z_type].setdefault(action, []).append(
                        (int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0, surf)
                    )
            for action in _ZOMBIE_FRAMES[z_type]:
                _ZOMBIE_FRAMES[z_type][action].sort(key=lambda x: x[0])
                _ZOMBIE_FRAMES[z_type][action] = [s for _, s in _ZOMBIE_FRAMES[z_type][action]]


def _get_scaled(surf: pygame.Surface, target_w: int, target_h: int) -> pygame.Surface:
    """带高速内存缓存的平滑缩放，同一尺寸绝不重复插值"""
    key = (id(surf), target_w, target_h)
    cached = _SCALED_CACHE.get(key)
    if cached is None:
        try:
            if surf.get_bitsize() not in (24, 32):
                surf = surf.convert_alpha()
            cached = pygame.transform.smoothscale(surf, (target_w, target_h))
        except Exception:
            cached = pygame.transform.scale(surf, (target_w, target_h))
        _SCALED_CACHE[key] = cached
    return cached


def _get_frozen(surf: pygame.Surface) -> pygame.Surface:
    """带缓存的冰冻冷蓝滤镜"""
    key = id(surf)
    cached = _FROZEN_CACHE.get(key)
    if cached is None:
        cached = surf.copy()
        tint = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        tint.fill((125, 205, 245, 255))
        cached.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        _FROZEN_CACHE[key] = cached
    return cached


def _get_alpha_surf(surf: pygame.Surface, alpha: int) -> pygame.Surface:
    """带缓存的透明衰减"""
    if alpha >= 255:
        return surf
    key = (id(surf), alpha)
    cached = _ALPHA_CACHE.get(key)
    if cached is None:
        cached = surf.copy()
        cached.set_alpha(alpha)
        _ALPHA_CACHE[key] = cached
    return cached


def get_card_surface(plant_type: str, target_size: Optional[Tuple[int, int]] = None) -> Optional[pygame.Surface]:
    surf = _CARD_SURFACES.get(plant_type)
    if surf is None:
        aliases = {
            "repeater": "repeaterpea",
            "threepeater": "threepeashooter",
        }
        alias = aliases.get(plant_type)
        if alias:
            surf = _CARD_SURFACES.get(alias)
    if surf is None:
        return None
    if target_size and surf.get_size() != target_size:
        return _get_scaled(surf, target_size[0], target_size[1])
    return surf


def get_sun_frame(time_value: float, radius: float = 24.0) -> Optional[pygame.Surface]:
    if not _SUN_FRAMES:
        return None
    fps = 12.0
    idx = int(time_value * fps) % len(_SUN_FRAMES)
    surf = _SUN_FRAMES[idx]
    size = int(radius * 2.3)
    key = (idx, size)
    cached = _SUN_SCALED_CACHE.get(key)
    if cached is None:
        cached = pygame.transform.smoothscale(surf, (size, size))
        _SUN_SCALED_CACHE[key] = cached
    return cached


def get_mower_surface(target_size: Tuple[int, int] = (64, 52), is_pool: bool = False) -> Optional[pygame.Surface]:
    key = "pool_cleaner" if is_pool else "car"
    surf = _ITEM_SURFACES.get(key) or _ITEM_SURFACES.get("car")
    if surf:
        return _get_scaled(surf, target_size[0], target_size[1])
    return None


def get_bullet_surface(freeze: bool = False, size: int = 24, bullet_type: str = "pea") -> Optional[pygame.Surface]:
    type_map = {
        "mushroom": ("bullet_mushroom", size, size),
        "shroom": ("bullet_mushroom", size, size),
        "fume": ("bullet_mushroom", int(size * 1.3), int(size * 1.3)),
        "fire_pea": ("fire_pea", int(size * 1.35), int(size * 1.35)),
        "firepea": ("fire_pea", int(size * 1.35), int(size * 1.35)),
        "cabbage": ("cabbage", int(size * 1.25), int(size * 1.25)),
        "kernel": ("kernel", int(size * 0.95), int(size * 1.15)),
        "butter": ("butter", int(size * 1.4), int(size * 1.0)),
        "melon": ("melon", int(size * 1.5), int(size * 1.3)),
        "winter_melon": ("winter_melon", int(size * 1.5), int(size * 1.3)),
        "wintermelon": ("winter_melon", int(size * 1.5), int(size * 1.3)),
        "spike": ("cattail_spike", int(size * 1.3), int(size * 0.8)),
        "cob_missile": ("kernel", int(size * 2.2), int(size * 1.6)),
        "cob": ("kernel", int(size * 2.2), int(size * 1.6)),
        "cattail_spike": ("cattail_spike", int(size * 1.3), int(size * 0.8)),
        "magic_card": ("magic_card", int(size * 0.9), int(size * 1.25)),
        "card": ("magic_card", int(size * 0.9), int(size * 1.25)),
        "pea_ice": ("pea_ice", size, size),
        "snowpea": ("pea_ice", size, size),
        "pea": ("pea_normal", size, size),
        "pea_normal": ("pea_normal", size, size),
    }
    if bullet_type in type_map:
        key, w, h = type_map[bullet_type]
    elif freeze or bullet_type in ("snowpea", "pea_ice"):
        key, w, h = "pea_ice", size, size
    else:
        key, w, h = "pea_normal", size, size
    surf = _ITEM_SURFACES.get(key)
    if surf:
        return _get_scaled(surf, w, h)
    return None


def get_map_surface(theme: str, target_size: Tuple[int, int] = (1200, 760)) -> Optional[pygame.Surface]:
    if theme in _MAP_SURFACES:
        return _MAP_SURFACES[theme]
    path = ASSETS_DIR / "maps" / f"{theme}.png"
    if path.exists():
        surf = _load_png(path)
        if surf:
            scaled = _get_scaled(surf, target_size[0], target_size[1])
            _MAP_SURFACES[theme] = scaled
            return scaled
    return None


def render_plant_sprite(
    surface: pygame.Surface,
    plant_type: str,
    center: Tuple[float, float],
    scale: float,
    time_value: float,
    hp_ratio: float = 1.0,
    age: float = 10.0,
    plant: any = None,
) -> bool:
    """使用原版贴图与动作序列帧渲染植物。返回 True 表示成功绘制。"""
    actions = _PLANT_FRAMES.get(plant_type)
    if not actions:
        if plant_type == 'tallnut':
            actions = _PLANT_FRAMES.get('wallnut')
        elif plant_type == 'gatlingpea':
            actions = _PLANT_FRAMES.get('repeater')
    if not actions:
        return False

    action_key = "idle"
    fps = 9.0

    if plant_type in ("wallnut", "tallnut"):
        if hp_ratio <= 0.33 and "cracked2" in actions:
            action_key = "cracked2"
        elif hp_ratio <= 0.66 and "cracked1" in actions:
            action_key = "cracked1"
    elif plant_type == "potatomine":
        if age < 6.0 and "init" in actions:
            action_key = "init"
        elif "armed" in actions:
            action_key = "armed"
            fps = 12.0
    elif plant_type == "chomper":
        swallow = plant.swallow_timer if plant else 0.0
        if swallow > 0 and "digest" in actions:
            action_key = "digest"
            fps = 6.0
        elif plant and getattr(plant, "eating", False) and "attack" in actions:
            action_key = "attack"
            fps = 10.0
    elif plant_type == "squash":
        if plant and getattr(plant, "squash_state", "") == "jump" and "attack" in actions:
            action_key = "attack"
            fps = 14.0
        elif plant and getattr(plant, "target_zombie", None) and "aim" in actions:
            action_key = "aim"
    elif plant_type == "garlic":
        if hp_ratio <= 0.65 and "bite" in actions:
            action_key = "bite"
    elif plant_type == "cattail":
        if plant and getattr(plant, "attacking", False) and "attack" in actions:
            action_key = "attack"
            fps = 12.0
    elif plant_type == "fumeshroom":
        if plant and getattr(plant, "shooting", 0) > 0 and "attack" in actions:
            action_key = "attack"
            fps = 10.0
    elif plant_type == "laserbean":
        if plant and getattr(plant, "shooting", 0) > 0 and "attack" in actions:
            action_key = "attack"
            fps = 14.0

    frames = actions.get(action_key) or actions.get("idle") or (list(actions.values())[0] if actions else None)
    if not frames:
        return False

    idx = int(time_value * fps) % len(frames)
    frame = frames[idx]

    # 原版尺寸映射与微缩放适配
    base_w, base_h = frame.get_size()
    target_h = int(88 * scale)
    target_w = None
    y_offset = 2 * scale
    if plant_type == "spikeweed":
        target_h = int(46 * scale)
        y_offset = 22 * scale
    elif plant_type == "lilypad":
        target_h = int(72 * scale)
        target_w = int(112 * scale)
        y_offset = 22 * scale
    elif plant_type == "puffshroom":
        target_h = int(58 * scale)
        y_offset = 12 * scale
    elif plant_type == "sunshroom":
        target_h = int(62 * scale)
        y_offset = 10 * scale
    elif plant_type == "iceshroom":
        target_h = int(68 * scale)
        y_offset = 8 * scale
    elif plant_type == "garlic":
        target_h = int(68 * scale)
        y_offset = 12 * scale
    elif plant_type == "cattail":
        target_h = int(84 * scale)
        y_offset = 4 * scale
    elif plant_type == "tallnut":
        target_h = int(126 * scale)
        y_offset = -18 * scale
    elif plant_type == "gatlingpea":
        target_h = int(90 * scale)
        y_offset = 0 * scale
    elif plant_type == "torchwood":
        target_h = int(92 * scale)
        y_offset = -2 * scale
    elif plant_type == "squash":
        target_h = int(92 * scale)
        y_offset = 4 * scale
    elif plant_type in ("cabbagepult", "kernelpult"):
        target_h = int(88 * scale)
        y_offset = 4 * scale
    elif plant_type in ("melonpult", "wintermelon"):
        target_h = int(98 * scale)
        y_offset = -2 * scale
    elif plant_type == "threepeater":
        target_h = int(96 * scale)
    elif plant_type == "fumeshroom":
        target_h = int(82 * scale)
        y_offset = 4 * scale
    elif plant_type == "hypnoshroom":
        target_h = int(76 * scale)
        y_offset = 6 * scale
    elif plant_type == "laserbean":
        target_h = int(84 * scale)
        y_offset = 2 * scale
    elif plant_type == "magicshroom":
        target_h = int(82 * scale)
        y_offset = 4 * scale
    elif plant_type == "agave":
        target_h = int(90 * scale)
        y_offset = 0 * scale
    elif plant_type == "cobcannon":
        target_h = int(105 * scale)
        target_w = int(160 * scale)
        y_offset = -6 * scale
    elif plant_type == "doomshroom":
        target_h = int(86 * scale)
        y_offset = 4 * scale
    elif plant_type == "twinsunflower":
        target_h = int(88 * scale)
        target_w = int(114 * scale)
        y_offset = 0 * scale
    elif plant_type == "starfruit":
        target_h = int(82 * scale)
        y_offset = 2 * scale
    elif plant_type == "splitpea":
        target_h = int(88 * scale)
        y_offset = 2 * scale
    elif plant_type == "spikerock":
        target_h = int(54 * scale)
        y_offset = 18 * scale
    if target_w is None:
        ratio = target_h / max(1, base_h)
        target_w = int(base_w * ratio)

    # 查缓存，0 次每帧重复生成
    scaled_frame = _get_scaled(frame, target_w, target_h)

    # 绘制真实原版软阴影
    cx, cy = center
    shadow_w = int(target_w * 0.70)
    shadow_h = int(14 * scale)
    shadow = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (20, 38, 24, 85), shadow.get_rect())
    surface.blit(shadow, (cx - shadow_w // 2, cy + target_h // 2 - 10 * scale + (12 * scale if plant_type == "spikeweed" else 0)))

    # 贴图居中贴在植物网格中下部
    rect = scaled_frame.get_rect(center=(cx, cy + y_offset))
    surface.blit(scaled_frame, rect)
    return True


def render_zombie_sprite(
    surface: pygame.Surface,
    zombie: any,
    time_value: float,
    ground_y: float,
    alpha: int = 255,
    dy_offset: float = 0.0,
) -> bool:
    """使用原版贴图与动作序列帧渲染僵尸。返回 True 表示成功绘制。"""
    ztype = getattr(zombie, "ztype", "basic")
    type_map = {
        "basic": "basic",
        "cone": "cone",
        "bucket": "bucket",
        "runner": "runner",
        "newspaper": "newspaper",
        "pole": "pole",
        "ducky": "ducky",
        "snorkel": "snorkel",
        "dolphin": "dolphin",
    }
    dir_name = type_map.get(ztype, "basic")
    actions = _ZOMBIE_FRAMES.get(dir_name) or _ZOMBIE_FRAMES.get("basic")
    if not actions:
        return False

    is_eating = getattr(zombie, "eating", 0) > 0
    enraged = getattr(zombie, "enraged", False)
    vault_state = getattr(zombie, "vault_state", "")

    action_key = "walk"
    fps = 9.0

    if dir_name == "pole":
        if vault_state == "jumping":
            action_key = "jump"
            fps = 12.0
        elif is_eating:
            action_key = "attack" if "attack" in actions else "walk"
        else:
            action_key = "walk"
            fps = 13.0 if getattr(zombie, "has_pole", True) else 9.0
    elif dir_name == "newspaper":
        if enraged:
            action_key = "enraged_attack" if is_eating and "enraged_attack" in actions else "enraged_walk"
            fps = 14.0
        else:
            action_key = "attack" if is_eating and "attack" in actions else "walk"
            fps = 8.0
    elif dir_name == "ducky":
        if is_eating and "attack" in actions:
            action_key = "attack"
            fps = 11.0
        else:
            action_key = "walk"
            fps = 9.0
    elif dir_name == "snorkel":
        submerged = getattr(zombie, "submerged", True)
        if is_eating and "attack" in actions:
            action_key = "attack"
            fps = 11.0
        elif submerged and "swim" in actions:
            action_key = "swim"
            fps = 8.0
        else:
            action_key = "walk"
            fps = 9.0
    elif dir_name == "dolphin":
        if vault_state == "jumping" and "jump" in actions:
            action_key = "jump"
            fps = 12.0
        elif is_eating and "attack" in actions:
            action_key = "attack"
            fps = 11.0
        else:
            action_key = "walk"
            fps = 12.0
    else:
        if is_eating and "attack" in actions:
            action_key = "attack"
            fps = 11.0
        else:
            action_key = "walk"
            fps = 9.0

    frames = actions.get(action_key) or actions.get("walk")
    if not frames:
        return False

    phase = getattr(zombie, "phase", 0.0)
    idx = int((time_value * fps) + phase * 2.0) % len(frames)
    frame = frames[idx]

    # 冰冻减速色调滤镜 (缓存处理)
    if getattr(zombie, "slow_timer", 0.0) > 0:
        frame = _get_frozen(frame)

    # 魅惑僵尸水平翻转（调头向右冲锋）
    is_hypno = getattr(zombie, "hypnotized", False)
    if is_hypno:
        frame = pygame.transform.flip(frame, True, False)

    # 尺寸缩放适配 (原版僵尸高约 118 像素)
    bw, bh = frame.get_size()
    target_h = 118
    target_w = int(bw * (target_h / max(1, bh)))
    scaled = _get_scaled(frame, target_w, target_h)

    # 死亡透明淡出支持
    if alpha < 255:
        scaled = _get_alpha_surf(scaled, alpha)

    # 撑杆跳跃与海豚飞跃的物理高度补偿
    vault_y = 0.0
    if ztype in ("pole", "dolphin") and vault_state == "jumping":
        prog = min(1.0, max(0.0, getattr(zombie, "vault_progress", 0.0)))
        vault_y = -math.sin(prog * math.pi) * (65.0 if ztype == "pole" else 75.0)

    # 潜水僵尸潜水时的深度偏移
    if ztype == "snorkel" and getattr(zombie, "submerged", True) and not is_eating:
        dy_offset += 26.0

    # 真实地表柔和阴影或水面水波 (活着时绘制)
    is_in_water = getattr(zombie, "is_in_water", False)
    if alpha >= 200:
        if is_in_water:
            ripple_w = int(52 + math.sin(time_value * 5.0 + phase) * 4)
            ripple = pygame.Surface((ripple_w, 12), pygame.SRCALPHA)
            pygame.draw.ellipse(ripple, (170, 225, 255, 110), ripple.get_rect(), width=2)
            surface.blit(ripple, (int(zombie.x - ripple_w // 2), int(ground_y - 6)))
        else:
            shadow_w = 58
            shadow = pygame.Surface((shadow_w, 14), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow, (20, 36, 24, 90), shadow.get_rect())
            surface.blit(shadow, (zombie.x - shadow_w // 2, ground_y - 5))

    # 新增精英僵尸体型与外观重构
    scale_mult = 1.0
    if ztype == "gargantuar":
        scale_mult = 1.65 # 巨人僵尸身形极其威猛伟岸
    elif ztype == "imp":
        scale_mult = 0.55 # 小鬼僵尸小巧敏捷

    if scale_mult != 1.0:
        gw = int(target_w * scale_mult)
        gh = int(target_h * scale_mult)
        scaled = _get_scaled(scaled, gw, gh)
        target_w, target_h = gw, gh

    # 气球僵尸浮空高度与气球
    balloon_y = 0.0
    if ztype == "balloon" and getattr(zombie, "flying", True):
        balloon_y = -36.0 + math.sin(time_value * 3.5 + phase) * 5.0

    # 矿工僵尸遁地偏移
    if ztype == "digger" and getattr(zombie, "digging", False):
        dy_offset += 32.0

    # 贴图定位：底部贴齐地平线
    draw_x = int(zombie.x - target_w * 0.45)
    draw_y = int(ground_y - target_h + 8 + vault_y + balloon_y + dy_offset)

    # 矿工遁地只显示翻滚泥土
    if ztype == "digger" and getattr(zombie, "digging", False):
        # 翻滚泥土特效
        for di in range(4):
            dx = zombie.x - 18 + di * 12 + math.sin(time_value * 12 + di) * 4
            dy = ground_y - 8 + math.cos(time_value * 10 + di) * 3
            pygame.draw.circle(surface, (139, 90, 43), (int(dx), int(dy)), 6)
            pygame.draw.circle(surface, (185, 122, 60), (int(dx - 2), int(dy - 2)), 3)
    else:
        surface.blit(scaled, (draw_x, draw_y))
        if is_hypno and alpha >= 180:
            glow_surf = pygame.Surface((target_w, target_h), pygame.SRCALPHA)
            glow_a = int(55 + 25 * math.sin(time_value * 7.0))
            pygame.draw.ellipse(glow_surf, (255, 120, 240, glow_a), glow_surf.get_rect())
            surface.blit(glow_surf, (draw_x, draw_y), special_flags=pygame.BLEND_RGBA_ADD)

    # 巨人僵尸特写：巨锤与背上的小鬼
    if ztype == "gargantuar":
        # 巨型重锤/电线杆
        pole_x = int(zombie.x - 22)
        pole_y = int(ground_y - 120 + vault_y)
        pygame.draw.line(surface, (70, 75, 80), (pole_x + 15, pole_y - 20), (pole_x - 15, ground_y - 4), 10)
        # 铁牌/水泥块锤头
        pygame.draw.rect(surface, (120, 125, 130), (pole_x - 30, ground_y - 28, 30, 24), border_radius=4)
        pygame.draw.rect(surface, (230, 80, 70), (pole_x - 26, ground_y - 24, 22, 16), border_radius=2)
        # 背上的小鬼 (若尚未抛出)
        if getattr(zombie, "has_imp", True):
            imp_x = int(zombie.x + 28)
            imp_y = int(ground_y - 115 + math.sin(time_value * 4) * 3)
            pygame.draw.circle(surface, (153, 177, 143), (imp_x, imp_y), 12)
            pygame.draw.circle(surface, (25, 35, 25), (imp_x - 3, imp_y - 2), 3)
            pygame.draw.circle(surface, (255, 255, 255), (imp_x - 4, imp_y - 3), 1)
            pygame.draw.circle(surface, (25, 35, 25), (imp_x + 3, imp_y - 2), 3)
            pygame.draw.rect(surface, (65, 80, 95), (imp_x - 8, imp_y + 10, 16, 12), border_radius=3)

    # 气球僵尸：头顶摇曳的彩色气球与细线
    if ztype == "balloon" and getattr(zombie, "flying", True):
        bx = int(zombie.x + 2)
        by = int(draw_y - 28 + balloon_y)
        # 绑线
        pygame.draw.line(surface, (220, 220, 220), (int(zombie.x), int(draw_y + 15)), (bx, by + 20), 2)
        # 气球
        pygame.draw.ellipse(surface, (240, 50, 60), (bx - 18, by - 22, 36, 44))
        pygame.draw.ellipse(surface, (255, 200, 60), (bx - 8, by - 22, 16, 44)) # 金色条纹
        pygame.draw.ellipse(surface, (255, 255, 255, 180), (bx - 12, by - 16, 8, 14)) # 高光

    # 玩偶匣小丑僵尸：八音盒与发条火星
    if ztype == "jackbox":
        box_x = int(zombie.x - 14)
        box_y = int(ground_y - 48)
        pygame.draw.rect(surface, (215, 45, 55), (box_x, box_y, 22, 20), border_radius=4)
        pygame.draw.rect(surface, (255, 215, 60), (box_x + 2, box_y + 2, 18, 16), 2, border_radius=3)
        # 旋转发条
        crank_a = time_value * 18.0
        cx_tip = box_x - 6 + math.cos(crank_a) * 6
        cy_tip = box_y + 10 + math.sin(crank_a) * 6
        pygame.draw.line(surface, (210, 180, 70), (box_x, box_y + 10), (int(cx_tip), int(cy_tip)), 2)

    # 矿工僵尸：矿工安全帽与探照灯
    if ztype == "digger" and not getattr(zombie, "digging", False):
        cap_x = int(zombie.x - 14)
        cap_y = int(draw_y - 6)
        pygame.draw.ellipse(surface, (225, 180, 50), (cap_x, cap_y, 30, 16))
        # 探照灯
        pygame.draw.circle(surface, (255, 255, 180), (cap_x + 6, cap_y + 8), 5)
        # 探照灯照射光束
        cone_surf = pygame.Surface((80, 40), pygame.SRCALPHA)
        pygame.draw.polygon(cone_surf, (255, 255, 200, 45), [(0, 20), (80, 0), (80, 40)])
        surface.blit(cone_surf, (cap_x + 10, cap_y - 12))

    # 黄油糊脸特写 (被玉米黄油击中时，鲜黄醒目)
    butter_t = getattr(zombie, "butter_timer", 0.0)
    if butter_t > 0:
        butter_surf = _ITEM_SURFACES.get("butter")
        if butter_surf:
            b_scaled = _get_scaled(butter_surf, 38, 26)
            surface.blit(b_scaled, (int(zombie.x - 19), int(ground_y - 82 + vault_y)))

    # 血条绘制 (权威统一生命值：身体HP + 护盾/帽子HP，受伤即亮条，血量平滑递减)
    total_curr = getattr(zombie, "total_current_hp", None)
    total_max = getattr(zombie, "total_max_hp", None)
    if total_curr is None or total_max is None or total_max <= 0:
        b_hp = getattr(zombie, "hp", 0.0)
        s_hp = getattr(zombie, "shield_hp", 0.0)
        mb_hp = getattr(zombie, "max_hp", 200.0)
        ms_hp = getattr(zombie, "shield_max_hp", 0.0)
        total_curr = b_hp + s_hp
        total_max = mb_hp + ms_hp

    damaged = total_curr < (total_max - 0.5)
    ratio = max(0.0, min(1.0, total_curr / max(1.0, total_max)))

    if not getattr(zombie, "dead", False) and damaged and alpha >= 100:
        if ztype == "gargantuar":
            bar_y = int(ground_y - 142 + vault_y)
            bar_w = 64
        elif ztype == "imp":
            bar_y = int(ground_y - 48)
            bar_w = 34
        elif ztype == "balloon" and getattr(zombie, "flying", True):
            bar_y = int(ground_y - 118 + balloon_y)
            bar_w = 48
        else:
            bar_y = int(ground_y - 94 + vault_y)
            bar_w = 48

        bar = pygame.Rect(int(zombie.x - bar_w // 2), bar_y, bar_w, 6)
        pygame.draw.rect(surface, (45, 30, 30), bar, border_radius=3)
        fill = bar.inflate(-2, -2)
        fill.width = int(fill.width * ratio)
        col = (97, 198, 92) if ratio > 0.55 else (241, 186, 58) if ratio > 0.25 else (226, 73, 59)
        if fill.width > 0:
            pygame.draw.rect(surface, col, fill, border_radius=2)

    return True
