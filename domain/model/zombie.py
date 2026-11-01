# -*- coding: utf-8 -*-
"""Zombie entity model.
Encapsulates state, armor/shield health, status effects (freeze, slow, butter, hypno),
and special actions (pole vault, dive, rage).
"""

from dataclasses import dataclass
from typing import Optional, Any
from domain.spec.zombies import ZombieSpec, ZOMBIES


_ZOMBIE_ID_COUNTER = 0


def next_zombie_id() -> int:
    global _ZOMBIE_ID_COUNTER
    _ZOMBIE_ID_COUNTER += 1
    return _ZOMBIE_ID_COUNTER


@dataclass
class Zombie:
    id: int
    spec_id: str
    name: str
    row: int
    x: float
    y: float
    hp: float
    max_hp: float
    shield_hp: float
    shield_max_hp: float
    shield_type: Optional[str]
    speed: float
    base_speed: float
    damage: float
    is_water: bool = False

    # Status & CC effects
    freeze_timer: float = 0.0          # Absolute freeze (Ice-shroom)
    slow_timer: float = 0.0            # 50% chill slow (Snow Pea, Ice Melon)
    butter_timer: float = 0.0          # Butter stun (Kernel-pult)
    hypnotized: bool = False           # Defected to player side!
    flash_timer: float = 0.0           # Hit flash feedback

    # Behaviors & State
    eating: bool = False
    target_plant: Optional[Any] = None
    eat_timer: float = 0.0
    walk_dir: int = -1                 # -1 moves left (toward house), +1 moves right (hypnotized / digger)

    # Special archetypes
    has_vaulted: bool = False
    vaulting: bool = False
    vault_progress: float = 0.0
    submerged: bool = False            # Snorkel underwater evasion
    underground: bool = False          # Digger tunnel status
    is_enraged: bool = False           # Newspaper rage mode

    score: int = 10
    total_lifetime: float = 0.0

    @classmethod
    def create(cls, spec_id: str, row: int, x: float, y: float) -> "Zombie":
        spec = ZOMBIES[spec_id]
        body_hp = spec.max_hp
        shield_hp = spec.shield_hp
        # Total HP is body + shield
        total_hp = body_hp + shield_hp

        # Submerged initially for snorkels entering water
        submerged = spec.can_dive

        return cls(
            id=next_zombie_id(),
            spec_id=spec_id,
            name=spec.name,
            row=row,
            x=x,
            y=y,
            hp=body_hp,
            max_hp=body_hp,
            shield_hp=shield_hp,
            shield_max_hp=shield_hp,
            shield_type=spec.shield_type,
            speed=spec.speed,
            base_speed=spec.speed,
            damage=spec.damage,
            is_water=spec.is_water,
            submerged=submerged,
            score=spec.score,
        )

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    @property
    def dead(self) -> bool:
        return self.hp <= 0

    @property
    def ztype(self) -> str:
        return self.spec_id

    @property
    def has_newspaper(self) -> bool:
        return self.spec_id == "newspaper" and self.shield_hp > 0

    @property
    def newspaper_hp(self) -> float:
        return self.shield_hp if self.spec_id == "newspaper" else 0.0

    @property
    def flying(self) -> bool:
        return self.spec_id == "balloon" and not getattr(self, "balloon_popped", False)

    @property
    def total_current_hp(self) -> float:
        return self.hp + max(0.0, self.shield_hp)

    @property
    def total_max_hp(self) -> float:
        return self.max_hp + self.shield_max_hp

    @property
    def health_ratio(self) -> float:
        """Returns 0.0 - 1.0 hp percentage for the health bar.
        Always based on full total so the bar never abruptly disappears!
        """
        if self.total_max_hp <= 0:
            return 0.0
        return max(0.0, min(1.0, self.total_current_hp / self.total_max_hp))

    @property
    def effective_speed(self) -> float:
        """Calculates current movement speed factoring in CC and rage."""
        if self.freeze_timer > 0 or self.butter_timer > 0:
            return 0.0

        current = self.base_speed
        if self.is_enraged:
            current = self.base_speed * 2.6

        if self.slow_timer > 0:
            current *= 0.5

        return current

    def apply_damage(self, amount: float, bypass_shield: bool = False) -> tuple[float, bool]:
        """Applies damage respecting shield absorption.
        Returns (absorbed_damage, is_dead).
        """
        self.flash_timer = 0.12  # Trigger visual white flash

        actual_dealt = amount
        if self.shield_hp > 0 and not bypass_shield:
            if self.shield_hp >= amount:
                self.shield_hp -= amount
                return amount, False
            else:
                absorbed = self.shield_hp
                leftover = amount - absorbed
                self.shield_hp = 0.0
                # Newspaper shield breaks -> trigger rage!
                if self.spec_id == "newspaper" and not self.is_enraged:
                    self.is_enraged = True
                self.hp -= leftover
                is_dead = self.hp <= 0
                if is_dead:
                    self.hp = 0
                return amount, is_dead

        # Direct body damage
        self.hp -= amount
        is_dead = self.hp <= 0
        if is_dead:
            self.hp = 0
        return amount, is_dead

    def apply_freeze(self, duration: float) -> None:
        self.freeze_timer = max(self.freeze_timer, duration)

    def apply_slow(self, duration: float) -> None:
        self.slow_timer = max(self.slow_timer, duration)

    def apply_butter(self, duration: float) -> None:
        """Kernel-pult butter stun: completely stops movement and chewing."""
        self.butter_timer = max(self.butter_timer, duration)
        self.eating = False

    def hypnotize(self) -> None:
        """Defects zombie to player side."""
        self.hypnotized = True
        self.walk_dir = 1  # Turn around and walk right!
        self.eating = False
        self.target_plant = None
