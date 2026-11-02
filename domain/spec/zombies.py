# -*- coding: utf-8 -*-
"""Zombie specifications.
Declarative design: speeds, health, armor breakdown, water capability, and special mechanics.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ZombieSpec:
    id: str
    name: str
    max_hp: float
    speed: float
    damage: float
    is_water: bool = False
    shield_hp: float = 0.0
    shield_type: Optional[str] = None  # "cone", "bucket", "paper", "door", "football_helmet"
    can_vault: bool = False
    can_dive: bool = False
    can_dig: bool = False
    score: int = 10
    tip: str = ""


ZOMBIES: dict[str, ZombieSpec] = {
    "basic": ZombieSpec(
        id="basic", name="普通僵尸", max_hp=200, speed=18.0, damage=28,
        score=10, tip="普通僵尸：最基础的庭院入侵者，本体生命值 200 点（10 发普通豌豆）。",
    ),
    "flag": ZombieSpec(
        id="flag", name="旗帜领队僵尸", max_hp=200, speed=22.0, damage=28,
        score=15, tip="旗帜僵尸：预示着一大波尸潮的到来，生命值 200 点，移速稍快。",
    ),
    "cone": ZombieSpec(
        id="cone", name="路障僵尸", max_hp=200, speed=17.0, damage=30,
        shield_hp=370, shield_type="cone", score=25,
        tip="路障僵尸：头戴坚硬路障（370 护盾 + 200 本体 = 570 总血量），防御力是普通僵尸近 3 倍！",
    ),
    "bucket": ZombieSpec(
        id="bucket", name="铁桶僵尸", max_hp=200, speed=15.0, damage=34,
        shield_hp=1100, shield_type="bucket", score=50,
        tip="铁桶僵尸：厚重铁桶护体（1100 护盾 + 200 本体 = 1300 总血量），是普通僵尸 6.5 倍，极具抗击打压迫感！",
    ),
    "runner": ZombieSpec(
        id="runner", name="奔跑僵尸", max_hp=180, speed=32.0, damage=24,
        score=20, tip="奔跑僵尸：身形敏捷突进极快，生命值 180 点。",
    ),
    "pole": ZombieSpec(
        id="pole", name="撑杆僵尸", max_hp=500, speed=32.0, damage=28,
        can_vault=True, score=35,
        tip="撑杆僵尸：手握撑杆能飞跃第一道防线，生命值高达 500 点（是普通僵尸 2.5 倍）！",
    ),
    "newspaper": ZombieSpec(
        id="newspaper", name="读报僵尸", max_hp=200, speed=14.0, damage=28,
        shield_hp=150, shield_type="paper", score=30,
        tip="读报僵尸：报纸提供 150 点额外护盾，一旦报纸破碎立即陷入暴怒狂奔！",
    ),
    "ducky": ZombieSpec(
        id="ducky", name="鸭子救生圈僵尸", max_hp=200, speed=18.0, damage=28,
        is_water=True, score=20,
        tip="鸭子僵尸：套着救生圈在水面游弋，生命值 200 点。",
    ),
    "snorkel": ZombieSpec(
        id="snorkel", name="潜水僵尸", max_hp=200, speed=20.0, damage=30,
        is_water=True, can_dive=True, score=40,
        tip="潜水僵尸：潜伏在水下避开普通平射子弹，生命值 200 点。",
    ),
    "dolphin": ZombieSpec(
        id="dolphin", name="海豚骑士僵尸", max_hp=500, speed=36.0, damage=30,
        is_water=True, can_vault=True, score=45,
        tip="海豚骑士：在水面疾速冲刺并飞跃防线，生命值高达 500 点！",
    ),
    "gargantuar": ZombieSpec(
        id="gargantuar", name="巨人僵尸", max_hp=3000, speed=11.0, damage=1500,
        score=150, tip="巨人僵尸：经典 3000 点超强血量巨兽，力拔山河秒杀植物，残血投掷小鬼！",
    ),
    "imp": ZombieSpec(
        id="imp", name="小鬼僵尸", max_hp=100, speed=38.0, damage=25,
        score=15, tip="小鬼僵尸：生命值 100 点，体型娇小速度飞快，直插阵地后排。",
    ),
    "balloon": ZombieSpec(
        id="balloon", name="气球僵尸", max_hp=200, speed=17.0, damage=28,
        shield_hp=20, shield_type="balloon", score=30,
        tip="气球僵尸：低空飞行避开地面攻击，气球被破后坠地成为普通僵尸。",
    ),
    "jackbox": ZombieSpec(
        id="jackbox", name="小丑僵尸", max_hp=500, speed=28.0, damage=30,
        score=40, tip="小丑僵尸：生命值 500 点，手摇惊魂魔盒随机大范围自爆！",
    ),
    "digger": ZombieSpec(
        id="digger", name="矿工僵尸", max_hp=200, speed=22.0, damage=30,
        shield_hp=100, shield_type="helmet", can_dig=True, score=45,
        tip="矿工僵尸：遁地钻行直达最左侧反向包抄，头戴安全帽（100 护盾 + 200 本体）。",
    ),
}
