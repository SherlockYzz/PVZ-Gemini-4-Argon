# -*- coding: utf-8 -*-
"""World state entity container.
Encapsulates all mutable battle elements (plants, zombies, projectiles, suns, mowers)
with high-performance row-level spatial indexing.
"""

from dataclasses import dataclass, field
from typing import Optional
from domain.spec.field_layout import FieldLayout, LAND_LAYOUT
from domain.model.plant import Plant
from domain.model.zombie import Zombie
from domain.model.projectile import Projectile
from domain.model.sun import Sun
from domain.model.mower import Mower
from domain.model.particle import CombatParticle, FloatingText, ScreenShake
from domain.model.wave import WaveState


@dataclass
class World:
    layout: FieldLayout = LAND_LAYOUT
    plants: dict[tuple[int, int], Plant] = field(default_factory=dict)
    carriers: dict[tuple[int, int], Plant] = field(default_factory=dict)
    zombies: list[Zombie] = field(default_factory=list)
    projectiles: list[Projectile] = field(default_factory=list)
    suns: list[Sun] = field(default_factory=list)
    mowers: list[Mower] = field(default_factory=list)
    particles: list[CombatParticle] = field(default_factory=list)
    floating_texts: list[FloatingText] = field(default_factory=list)
    shake: ScreenShake = field(default_factory=ScreenShake)
    wave_state: WaveState = field(default_factory=lambda: WaveState(level_id=0, total_zombies=10))

    sun: int = 150
    natural_sun_timer: float = 6.0
    game_time: float = 0.0
    is_game_over: bool = False
    is_victory: bool = False

    # Row-level spatial cache (rebuilt each frame for O(1) lane queries)
    _zombies_by_row: dict[int, list[Zombie]] = field(default_factory=dict, init=False)
    _plants_by_row: dict[int, list[Plant]] = field(default_factory=dict, init=False)

    def rebuild_spatial_index(self) -> None:
        """High-performance lane grouping: eliminates O(N*M) full-lawn collision checks."""
        self._zombies_by_row = {r: [] for r in range(self.layout.rows)}
        for z in self.zombies:
            if z.is_alive and 0 <= z.row < self.layout.rows:
                self._zombies_by_row[z.row].append(z)

        self._plants_by_row = {r: [] for r in range(self.layout.rows)}
        for p in self.plants.values():
            if p.is_alive and 0 <= p.row < self.layout.rows:
                self._plants_by_row[p.row].append(p)

    def get_zombies_in_row(self, row: int) -> list[Zombie]:
        if not self._zombies_by_row:
            return [z for z in self.zombies if z.row == row and z.is_alive]
        return self._zombies_by_row.get(row, [])

    def get_plants_in_row(self, row: int) -> list[Plant]:
        if not self._plants_by_row:
            return [p for p in self.plants.values() if p.row == row and p.is_alive]
        return self._plants_by_row.get(row, [])

    def get_plant_at(self, col: int, row: int) -> Optional[Plant]:
        return self.plants.get((col, row))

    def get_carrier_at(self, col: int, row: int) -> Optional[Plant]:
        return self.carriers.get((col, row))

    def remove_dead_entities(self) -> None:
        """Prunes dead plants, zombies, expired projectiles, and collected suns."""
        self.plants = {k: p for k, p in self.plants.items() if p.is_alive}
        self.carriers = {k: c for k, c in self.carriers.items() if c.is_alive}
        self.zombies = [z for z in self.zombies if z.is_alive]
        self.projectiles = [p for p in self.projectiles if p.alive]
        self.suns = [s for s in self.suns if s.age < s.lifetime and s.state != "collected"]
        self.particles = [pt for pt in self.particles if pt.alive]
        self.floating_texts = [ft for ft in self.floating_texts if ft.alive]
