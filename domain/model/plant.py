# -*- coding: utf-8 -*-
"""Plant entity model.
Represents an instantiated plant on the lawn or pool grid.
"""

from dataclasses import dataclass, field
from typing import Optional
from domain.spec.plants import PlantSpec, PLANTS, BehaviorKind


@dataclass
class Plant:
    spec_id: str
    col: int
    row: int
    x: float
    y: float
    hp: float
    max_hp: float
    carrier: Optional["Plant"] = None  # e.g., Lilypad underneath this plant
    is_carrier: bool = False           # True if this plant can support another on water

    # Behavior timers
    timer: float = 0.0                 # Action countdown (shoot / produce sun / attack)
    sub_timer: float = 0.0             # Secondary timer (e.g. Gatling / Repeater burst gaps)
    burst_remaining: int = 0           # Remaining shots in current salvo
    burst_target_row: int = 0          # Target row for burst salvos
    state: str = "idle"                # "idle", "attack", "chewing", "priming", "exploded", "squash_jump"
    state_timer: float = 0.0           # State duration / animation progress

    # Targeting & Special fields
    target_x: float = 0.0              # Lobbed target x (e.g. Cob Cannon / Squash)
    target_y: float = 0.0              # Lobbed target y
    target_zombie_id: Optional[int] = None
    age: float = 0.0                   # How long this plant has lived
    scale: float = 1.0                 # Visual pop scale (juice!)
    is_sleeping: bool = False          # Nocturnal sleep during daytime if unawakened

    @classmethod
    def create(cls, spec_id: str, col: int, row: int, x: float, y: float, carrier: Optional["Plant"] = None) -> "Plant":
        spec = PLANTS[spec_id]
        b_spec = spec.behavior
        # Initial action timer: respect first_interval if defined, else full interval
        init_timer = b_spec.first_interval if b_spec.first_interval is not None else b_spec.interval

        is_carrier = (spec_id == "lilypad")
        plant = cls(
            spec_id=spec_id,
            col=col,
            row=row,
            x=x,
            y=y,
            hp=spec.max_hp,
            max_hp=spec.max_hp,
            carrier=carrier,
            is_carrier=is_carrier,
            timer=init_timer,
            state="priming" if spec_id == "potatomine" else "idle",
            state_timer=14.0 if spec_id == "potatomine" else 0.0,
        )
        return plant

    @property
    def spec(self) -> PlantSpec:
        return PLANTS[self.spec_id]

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, amount: float) -> bool:
        """Deals damage to plant. Returns True if plant died."""
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            return True
        return False

    def heal(self, amount: float) -> None:
        self.hp = min(self.max_hp, self.hp + amount)
