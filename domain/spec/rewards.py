# -*- coding: utf-8 -*-
"""Level progression and rewards.
Maps each level completion to unlocked plant blueprints and ancient artifacts.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class LevelReward:
    plants: list[str] = field(default_factory=list)
    artifact: Optional[str] = None
    artifact_name: Optional[str] = None
    artifact_desc: Optional[str] = None


# Unlock order for player's seed inventory
UNLOCK_ORDER: list[str] = [
    # 初始基础植物 (第 1 关开局可用)
    "sunflower",
    "peashooter",
    # 白天草坪阶段解锁
    "wallnut",
    "snowpea",
    "potatomine",
    "repeater",
    "threepeater",
    "squash",
    # 黑夜墓地阶段解锁
    "puffshroom",
    "sunshroom",
    "fumeshroom",
    "spikeweed",
    "hypnoshroom",
    "cherrybomb",
    "chomper",
    "iceshroom",
    "doomshroom",
    "jalapeno",
    # 泳池水面阶段解锁
    "lilypad",
    "cabbagepult",
    "kernelpult",
    "torchwood",
    "garlic",
    "cattail",
    "twinsunflower",
    "starfruit",
    "melonpult",
    "tallnut",
    # 传奇新植物与终极武器
    "agave",
    "magicshroom",
    "laserbean",
    "wintermelon",
    "gatlingpea",
    "cobcannon",
]

LEVEL_REWARDS: dict[int, LevelReward] = {
    0: LevelReward(plants=["wallnut"]),
    1: LevelReward(plants=["snowpea"]),
    2: LevelReward(plants=["potatomine"]),
    3: LevelReward(plants=["repeater"]),
    4: LevelReward(
        plants=["squash", "threepeater"],
        artifact="golden_shovel",
        artifact_name="黄金阳光铲",
        artifact_desc="神奇黄金铁铲！铲除任何植物时，100% 全额返还种植所消耗的阳光！",
    ),
    5: LevelReward(plants=["puffshroom", "sunshroom"]),
    6: LevelReward(plants=["fumeshroom", "spikeweed"]),
    7: LevelReward(
        plants=["hypnoshroom", "cherrybomb"],
        artifact="sun_vault",
        artifact_name="阳光储蓄罐",
        artifact_desc="戴夫特制存钱罐！每个关卡开局额外赠送 +100 点初始阳光储备！",
    ),
    8: LevelReward(plants=["chomper", "iceshroom"]),
    9: LevelReward(
        plants=["doomshroom", "jalapeno"],
        artifact="auto_sun_magnet",
        artifact_name="磁能阳光发生器 (自动收集阳光)",
        artifact_desc="戴夫高级黑科技！通关第10关解锁全场阳光自动吸附功能，可在右上角[自吸:开/关]随心自由切换！",
    ),
    10: LevelReward(plants=["lilypad", "cabbagepult"]),
    11: LevelReward(
        plants=["kernelpult", "torchwood"],
        artifact="golden_mower",
        artifact_name="镀金清扫车",
        artifact_desc="华丽镀金清扫车！当割草机或泳池清扫机被触发碾压时，额外爆落 200 点阳光！",
    ),
    12: LevelReward(
        plants=["garlic", "cattail", "twinsunflower"],
        artifact="belt_9",
        artifact_name="九格战术腰带",
        artifact_desc="精锐战术腰带！通关倒数第四关解锁，出战卡槽容量永久扩充至 9 格！",
    ),
    13: LevelReward(plants=["starfruit", "agave", "gatlingpea"]),
    14: LevelReward(
        plants=["melonpult", "tallnut", "magicshroom", "laserbean"],
        artifact="master_belt",
        artifact_name="十格大师腰带",
        artifact_desc="顶级战术大师腰带！通关倒数第二关解锁，出战卡槽容量永久扩充至 10 格！",
    ),
    15: LevelReward(plants=["wintermelon", "gatlingpea", "cobcannon"]),
}
