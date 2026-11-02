# -*- coding: utf-8 -*-
"""Plant specifications and behavior recipes for all 34 authentic plants.
Declarative design: adding a new plant only requires defining a PlantSpec recipe here,
without touching core combat loops.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class PlacementRule(Enum):
    LAND_ONLY = auto()       # Land only (e.g. standard plants, spikeweed)
    WATER_ONLY = auto()      # Water surface only (Lilypad)
    AQUATIC = auto()         # Can be planted directly on water or land
    CARRIER = auto()         # Water carrier platform that holds other plants (Lilypad)
    UPGRADE_SUN = auto()     # Upgrade from Sunflower (TwinSunflower)
    UPGRADE_REPEATER = auto()# Upgrade from Repeater (GatlingPea)
    UPGRADE_LILYPAD = auto() # Upgrade from Lilypad (Cattail)
    UPGRADE_SPIKEWEED = auto()# Upgrade from Spikeweed (Spikerock)


class BehaviorKind(Enum):
    PRODUCER = auto()        # Periodic sun generator (Sunflower, SunShroom, TwinSunflower)
    SHOOTER = auto()         # Horizontal bullet shooter (Peashooter, SnowPea, Repeater, GatlingPea)
    LOBBER = auto()          # Lobbed catapult (CabbagePult, KernelPult, MelonPult, WinterMelon, CobCannon)
    MELEE = auto()           # Close combat / Devour (Chomper, Agave)
    EXPLODER = auto()        # Instant / timed detonator (CherryBomb, Jalapeno, PotatoMine, DoomShroom, Squash)
    DEFENDER = auto()        # High HP barricade or diversion (Wallnut, Tallnut, Garlic)
    AURA = auto()            # Lane / area continuous attack (Spikeweed, Fumeshroom, LaserBean)
    HOMING = auto()          # Homing guidance spikes (Cattail)
    SPECIAL = auto()         # Unique mechanics (Torchwood, IceShroom, HypnoShroom, MagicShroom, Starfruit)


@dataclass(frozen=True)
class BehaviorSpec:
    kind: BehaviorKind
    interval: float = 1.4
    first_interval: Optional[float] = None
    damage: float = 20.0
    bullet_type: str = "pea"
    freeze: bool = False
    burst_count: int = 1
    rows_spread: int = 0
    area_radius: float = 0.0
    produce_sun: int = 25
    delay: float = 0.0
    butter_chance: float = 0.0
    butter_damage: float = 55.0


@dataclass(frozen=True)
class PlantSpec:
    id: str
    name: str
    cost: int
    cooldown: float
    max_hp: float
    placement: PlacementRule
    behavior: BehaviorSpec
    tip: str
    upgrade_from: Optional[str] = None


PLANTS: dict[str, PlantSpec] = {
    # 1. 基础日间与草坪系列
    "sunflower": PlantSpec(
        id="sunflower", name="向日葵", cost=50, cooldown=7.5, max_hp=300,
        placement=PlacementRule.LAND_ONLY,
        behavior=BehaviorSpec(kind=BehaviorKind.PRODUCER, interval=7.0, first_interval=4.1, produce_sun=25),
        tip="向日葵：提供维持草坪防御的重要阳光产出！",
    ),
    "peashooter": PlantSpec(
        id="peashooter", name="豌豆射手", cost=100, cooldown=7.5, max_hp=300,
        placement=PlacementRule.LAND_ONLY,
        behavior=BehaviorSpec(kind=BehaviorKind.SHOOTER, interval=1.4, damage=20.0, bullet_type="pea"),
        tip="豌豆射手：经典防线基石，向前方僵尸稳定射出豌豆！",
    ),
    "wallnut": PlantSpec(
        id="wallnut", name="坚果墙", cost=50, cooldown=20.0, max_hp=4000,
        placement=PlacementRule.LAND_ONLY,
        behavior=BehaviorSpec(kind=BehaviorKind.DEFENDER),
        tip="坚果墙：坚不可摧的生命屏障，阻挡僵尸长久推进！",
    ),
    "snowpea": PlantSpec(
        id="snowpea", name="寒冰射手", cost=175, cooldown=7.5, max_hp=300,
        placement=PlacementRule.LAND_ONLY,
        behavior=BehaviorSpec(kind=BehaviorKind.SHOOTER, interval=1.4, damage=20.0, bullet_type="snowpea", freeze=True),
        tip="寒冰射手：发射冰冻豌豆，击中僵尸造成伤害并持续减速！",
    ),
    "potatomine": PlantSpec(
        id="potatomine", name="土豆地雷", cost=25, cooldown=20.0, max_hp=300,
        placement=PlacementRule.LAND_ONLY,
        behavior=BehaviorSpec(kind=BehaviorKind.EXPLODER, delay=12.0, damage=1800.0, area_radius=82.0),
        tip="土豆地雷：需要时间破土成熟，僵尸靠近时瞬间爆炸！",
    ),
    "repeater": PlantSpec(
        id="repeater", name="双发射手", cost=200, cooldown=7.5, max_hp=300,
        placement=PlacementRule.LAND_ONLY,
        behavior=BehaviorSpec(kind=BehaviorKind.SHOOTER, interval=1.4, damage=20.0, burst_count=2, bullet_type="pea"),
        tip="双发射手：每次连续吐出两颗豌豆，压制力倍增！",
    ),
    "threepeater": PlantSpec(
        id="threepeater", name="三线射手", cost=300, cooldown=7.5, max_hp=300,
        placement=PlacementRule.LAND_ONLY,
        behavior=BehaviorSpec(kind=BehaviorKind.SHOOTER, interval=1.45, damage=20.0, rows_spread=1, bullet_type="pea"),
        tip="三线射手：一次向当前行及相邻上下三路同时发射豌豆！",
    ),
    "squash": PlantSpec(
        id="squash", name="窝瓜", cost=50, cooldown=20.0, max_hp=300,
        placement=PlacementRule.LAND_ONLY,
        behavior=BehaviorSpec(kind=BehaviorKind.EXPLODER, damage=1800.0, area_radius=85.0),
        tip="窝瓜：发现临近僵尸会跃起重重将其砸扁！",
    ),
    "cherrybomb": PlantSpec(
        id="cherrybomb", name="樱桃炸弹", cost=150, cooldown=25.0, max_hp=300,
        placement=PlacementRule.LAND_ONLY,
        behavior=BehaviorSpec(kind=BehaviorKind.EXPLODER, delay=1.2, damage=1800.0, area_radius=165.0),
        tip="樱桃炸弹：引燃后产生 3x3 超大范围强力爆炸！",
    ),
    "chomper": PlantSpec(
        id="chomper", name="大嘴花", cost=150, cooldown=7.5, max_hp=300,
        placement=PlacementRule.LAND_ONLY,
        behavior=BehaviorSpec(kind=BehaviorKind.MELEE, interval=2.0, damage=1800.0),
        tip="大嘴花：口吞靠近的整只僵尸，吞下后需长时间咀嚼消化！",
    ),

    # 2. 夜间专属蘑菇家族与阵地杀器
    "puffshroom": PlantSpec(
        id="puffshroom", name="小喷菇", cost=0, cooldown=7.5, max_hp=300,
        placement=PlacementRule.LAND_ONLY,
        behavior=BehaviorSpec(kind=BehaviorKind.SHOOTER, interval=1.4, damage=20.0, bullet_type="mushroom"),
        tip="小喷菇：0 阳光即可快速部署，喷吐中近程孢子！",
    ),
    "sunshroom": PlantSpec(
        id="sunshroom", name="阳光菇", cost=25, cooldown=7.5, max_hp=300,
        placement=PlacementRule.LAND_ONLY,
        behavior=BehaviorSpec(kind=BehaviorKind.PRODUCER, interval=7.0, first_interval=3.5, produce_sun=15),
        tip="阳光菇：初期产出小阳光，长大后产出正常大阳光！",
    ),
    "fumeshroom": PlantSpec(
        id="fumeshroom", name="大喷菇", cost=75, cooldown=7.5, max_hp=300,
        placement=PlacementRule.LAND_ONLY,
        behavior=BehaviorSpec(kind=BehaviorKind.AURA, interval=1.4, damage=20.0, bullet_type="fume"),
        tip="大喷菇：喷射穿透整条直线的紫色气雾，无视护甲！",
    ),
    "spikeweed": PlantSpec(
        id="spikeweed", name="地刺", cost=100, cooldown=7.5, max_hp=450,
        placement=PlacementRule.LAND_ONLY,
        behavior=BehaviorSpec(kind=BehaviorKind.AURA, interval=0.45, damage=22.0),
        tip="地刺：扎破轮胎，对踩过的僵尸造成持续足底伤害！",
    ),
    "hypnoshroom": PlantSpec(
        id="hypnoshroom", name="魅惑菇", cost=75, cooldown=15.0, max_hp=300,
        placement=PlacementRule.LAND_ONLY,
        behavior=BehaviorSpec(kind=BehaviorKind.SPECIAL),
        tip="魅惑菇：让啃食它的僵尸彻底倒戈，反身咬死同伴！",
    ),
    "iceshroom": PlantSpec(
        id="iceshroom", name="寒冰菇", cost=75, cooldown=25.0, max_hp=300,
        placement=PlacementRule.LAND_ONLY,
        behavior=BehaviorSpec(kind=BehaviorKind.SPECIAL),
        tip="寒冰菇：冻结全屏所有僵尸数秒，并造成全场极度冰寒！",
    ),
    "doomshroom": PlantSpec(
        id="doomshroom", name="毁灭菇", cost=125, cooldown=25.0, max_hp=300,
        placement=PlacementRule.LAND_ONLY,
        behavior=BehaviorSpec(kind=BehaviorKind.EXPLODER, delay=1.2, damage=1800.0, area_radius=280.0),
        tip="毁灭菇：引发毁天灭地的超级大爆炸，并在原地留下弹坑！",
    ),
    "jalapeno": PlantSpec(
        id="jalapeno", name="火爆辣椒", cost=125, cooldown=25.0, max_hp=300,
        placement=PlacementRule.LAND_ONLY,
        behavior=BehaviorSpec(kind=BehaviorKind.EXPLODER, delay=0.8, damage=1800.0),
        tip="火爆辣椒：瞬间焚烧整条横行上的所有僵尸与冰道！",
    ),

    # 3. 泳池水面与两栖战力
    "lilypad": PlantSpec(
        id="lilypad", name="睡莲", cost=25, cooldown=5.0, max_hp=300,
        placement=PlacementRule.CARRIER,
        behavior=BehaviorSpec(kind=BehaviorKind.DEFENDER),
        tip="睡莲：水面关键支撑！只有铺上睡莲才能在水上种植植物！",
    ),
    "cabbagepult": PlantSpec(
        id="cabbagepult", name="卷心菜投手", cost=100, cooldown=7.5, max_hp=300,
        placement=PlacementRule.LAND_ONLY,
        behavior=BehaviorSpec(kind=BehaviorKind.LOBBER, interval=2.85, damage=40.0, bullet_type="cabbage"),
        tip="卷心菜投手：投出弧线卷心菜，跨越护具直击本体！",
    ),
    "kernelpult": PlantSpec(
        id="kernelpult", name="玉米投手", cost=100, cooldown=7.5, max_hp=300,
        placement=PlacementRule.LAND_ONLY,
        behavior=BehaviorSpec(
            kind=BehaviorKind.LOBBER, interval=2.35, damage=28.0,
            bullet_type="kernel", butter_chance=0.30, butter_damage=55.0
        ),
        tip="玉米投手：投掷玉米粒或黄油块；黄油命中强制定身僵尸 4.5 秒！",
    ),
    "melonpult": PlantSpec(
        id="melonpult", name="西瓜投手", cost=300, cooldown=7.5, max_hp=300,
        placement=PlacementRule.LAND_ONLY,
        behavior=BehaviorSpec(kind=BehaviorKind.LOBBER, interval=2.9, damage=80.0, bullet_type="melon", area_radius=80.0),
        tip="西瓜投手：投掷重磅西瓜，对落点及周围大片僵尸造成溅射伤害！",
    ),
    "wintermelon": PlantSpec(
        id="wintermelon", name="冰西瓜投手", cost=500, cooldown=15.0, max_hp=300,
        placement=PlacementRule.LAND_ONLY,
        behavior=BehaviorSpec(kind=BehaviorKind.LOBBER, interval=2.9, damage=80.0, bullet_type="winter_melon", freeze=True, area_radius=80.0),
        tip="冰西瓜投手：投掷冰冻西瓜，群体高额爆发并大范围冰冻减速！",
    ),
    "torchwood": PlantSpec(
        id="torchwood", name="火炬树桩", cost=175, cooldown=7.5, max_hp=300,
        placement=PlacementRule.LAND_ONLY,
        behavior=BehaviorSpec(kind=BehaviorKind.SPECIAL),
        tip="火炬树桩：穿透其火焰的豌豆将升级为强力火球，伤害翻倍！",
    ),
    "tallnut": PlantSpec(
        id="tallnut", name="高坚果", cost=125, cooldown=20.0, max_hp=8000,
        placement=PlacementRule.LAND_ONLY,
        behavior=BehaviorSpec(kind=BehaviorKind.DEFENDER),
        tip="高坚果：高耸伟岸的坚果重盾，彻底杜绝跳跃僵尸跨越！",
    ),
    "garlic": PlantSpec(
        id="garlic", name="大蒜", cost=50, cooldown=7.5, max_hp=400,
        placement=PlacementRule.LAND_ONLY,
        behavior=BehaviorSpec(kind=BehaviorKind.SPECIAL),
        tip="大蒜：咬它的僵尸会满口苦涩痛苦改道变道！",
    ),
    "starfruit": PlantSpec(
        id="starfruit", name="杨桃", cost=125, cooldown=7.5, max_hp=300,
        placement=PlacementRule.LAND_ONLY,
        behavior=BehaviorSpec(kind=BehaviorKind.SPECIAL),
        tip="杨桃：五角星形全向射手，向五个方向同时发射锋利金星！",
    ),

    # 4. 紫卡进阶升级植物与终极武器
    "twinsunflower": PlantSpec(
        id="twinsunflower", name="双子向日葵", cost=125, cooldown=15.0, max_hp=300,
        placement=PlacementRule.UPGRADE_SUN,
        behavior=BehaviorSpec(kind=BehaviorKind.PRODUCER, interval=7.0, first_interval=3.5, produce_sun=50),
        tip="双子向日葵：种在向日葵上，一次产出双倍阳光！",
        upgrade_from="sunflower",
    ),
    "gatlingpea": PlantSpec(
        id="gatlingpea", name="机枪射手", cost=250, cooldown=15.0, max_hp=300,
        placement=PlacementRule.UPGRADE_REPEATER,
        behavior=BehaviorSpec(kind=BehaviorKind.SHOOTER, interval=1.4, damage=20.0, burst_count=4, bullet_type="pea"),
        tip="机枪射手：种在双发射手上，狂暴连射 4 颗豌豆火力全开！",
        upgrade_from="repeater",
    ),
    "cattail": PlantSpec(
        id="cattail", name="猫尾草", cost=225, cooldown=15.0, max_hp=300,
        placement=PlacementRule.UPGRADE_LILYPAD,
        behavior=BehaviorSpec(kind=BehaviorKind.HOMING, interval=1.4, damage=20.0, burst_count=2, bullet_type="cattail_spike"),
        tip="猫尾草：种在睡莲上，全场智能追踪发射飞刺，气球杀手！",
        upgrade_from="lilypad",
    ),
    "spikerock": PlantSpec(
        id="spikerock", name="地刺王", cost=125, cooldown=25.0, max_hp=900,
        placement=PlacementRule.UPGRADE_SPIKEWEED,
        behavior=BehaviorSpec(kind=BehaviorKind.AURA, interval=1.0, damage=60.0),
        tip="地刺王：种在地刺上，造成双倍高额穿刺伤害，且能抗住巨人和车轮多次碾压！",
        upgrade_from="spikeweed",
    ),
    "splitpea": PlantSpec(
        id="splitpea", name="双向射手", cost=125, cooldown=7.5, max_hp=300,
        placement=PlacementRule.LAND_ONLY,
        behavior=BehaviorSpec(kind=BehaviorKind.SHOOTER, interval=1.4, damage=20.0, bullet_type="pea"),
        tip="双向射手：前后双向索敌，向前发射单发豌豆，向后猛烈连射双发豌豆！",
    ),
    "cobcannon": PlantSpec(
        id="cobcannon", name="玉米加农炮", cost=500, cooldown=30.0, max_hp=1200,
        placement=PlacementRule.LAND_ONLY,
        behavior=BehaviorSpec(kind=BehaviorKind.LOBBER, interval=15.0, damage=1800.0, bullet_type="cob_missile", area_radius=150.0),
        tip="玉米加农炮：终极重炮，发射毁天灭地的追踪毁灭爆破弹！",
    ),

    # 5. 特色神级植物
    "magicshroom": PlantSpec(
        id="magicshroom", name="魔术菇", cost=175, cooldown=10.0, max_hp=300,
        placement=PlacementRule.LAND_ONLY,
        behavior=BehaviorSpec(kind=BehaviorKind.SHOOTER, interval=1.3, damage=35.0, bullet_type="magic_card"),
        tip="魔术菇：抛出魔法扑克牌，击中僵尸有概率触发随机戏法与魅惑！",
    ),
    "agave": PlantSpec(
        id="agave", name="龙舌兰", cost=150, cooldown=10.0, max_hp=600,
        placement=PlacementRule.LAND_ONLY,
        behavior=BehaviorSpec(kind=BehaviorKind.MELEE, interval=1.0, damage=120.0),
        tip="龙舌兰：蓄力剑气横扫前方僵尸，对残血敌人具有斩杀破甲效果！",
    ),
    "laserbean": PlantSpec(
        id="laserbean", name="激光豆", cost=200, cooldown=10.0, max_hp=300,
        placement=PlacementRule.LAND_ONLY,
        behavior=BehaviorSpec(kind=BehaviorKind.AURA, interval=1.8, damage=85.0),
        tip="激光豆：双目射出贯通全屏整行的超强激光束，无视护甲穿透灼烧！",
    ),
}
