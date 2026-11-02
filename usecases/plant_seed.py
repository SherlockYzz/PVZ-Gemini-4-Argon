# -*- coding: utf-8 -*-
"""Plant seed use case."""

from typing import Optional
from domain.model.world import World
from domain.model.session import Session
from domain.model.plant import Plant
from domain.rules.planting import can_plant, perform_plant, shovel_plant


def execute_plant_action(col: int, row: int, world: World, session: Session) -> tuple[Optional[Plant], str]:
    """Plants the currently selected seed card at (col, row). Returns (plant, reason_if_failed)."""
    if session.active_seed_idx is None:
        return None, ""

    if session.active_seed_idx >= len(session.selected_seeds):
        return None, ""

    spec_id = session.selected_seeds[session.active_seed_idx]
    allowed, reason = can_plant(spec_id, col, row, world, session)
    if not allowed:
        return None, reason

    plant = perform_plant(spec_id, col, row, world, session)
    if plant:
        # Deselect after successful placement
        session.active_seed_idx = None
        return plant, ""
    return None, reason


def execute_shovel_action(col: int, row: int, world: World, session: Session) -> bool:
    """Removes a plant using the shovel."""
    if not session.active_shovel:
        return False
    success = shovel_plant(col, row, world, session)
    if success:
        session.active_shovel = False
    return success
