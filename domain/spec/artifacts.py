# -*- coding: utf-8 -*-
"""Artifact specifications and registry.
Provides passive perks and special utility upgrades unlocked through campaign victories.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ArtifactSpec:
    id: str
    name: str
    description: str
    icon_name: str = ""


ARTIFACTS: dict[str, ArtifactSpec] = {
    "golden_shovel": ArtifactSpec(
        id="golden_shovel",
        name="黄金阳光铲",
        description="神奇黄金铁铲！铲除任何植物时，100% 全额返还种植所消耗的阳光！",
    ),
    "sun_vault": ArtifactSpec(
        id="sun_vault",
        name="阳光储蓄罐",
        description="戴夫特制存钱罐！每个关卡开局额外赠送 +100 点初始阳光储备！",
    ),
    "auto_sun_magnet": ArtifactSpec(
        id="auto_sun_magnet",
        name="磁能阳光发生器",
        description="戴夫高级黑科技！解锁全场阳光自动吸附功能，可在右上角[自吸:开/关]随心自由切换！",
    ),
    "golden_mower": ArtifactSpec(
        id="golden_mower",
        name="镀金清扫车",
        description="华丽镀金清扫车！当割草机或泳池清扫机被触发碾压时，额外爆落 200 点阳光！",
    ),
    "belt_9": ArtifactSpec(
        id="belt_9",
        name="九格战术腰带",
        description="戴夫高阶腰带！出战卡槽容量永久扩充至 9 格！",
    ),
    "master_belt": ArtifactSpec(
        id="master_belt",
        name="大师战术腰带",
        description="顶级战术大师腰带！出战卡槽容量永久扩充至 10 格！",
    ),
}
