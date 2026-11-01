# -*- coding: utf-8 -*-
"""Skip level use case.
Allows instant level skipping while guaranteeing that all previous level rewards
(plant blueprints, ancient artifacts, pool carriers) are automatically granted!
"""

from typing import Optional
from domain.model.world import World
from domain.model.session import Session
from domain.model.particle import FloatingText
from domain.spec.levels import LEVELS
from domain.spec.rewards import LEVEL_REWARDS, UNLOCK_ORDER
from usecases.start_level import start_level


def skip_to_level(target_level_idx: int, session: Session) -> World:
    """Instant level skip with full retroactive reward grants.

    1. Bounds-checks the target level index (0 to 15).
    2. Retroactively unlocks all plant cards & artifacts from levels 0 to (target_level_idx - 1).
    3. Guarantees 34 full plants + master belt if jumping to endless mode.
    4. Guarantees Lilypad carrier if jumping to pool mode.
    5. Intelligently refreshes seed deck to match new level requirements.
    6. Starts the level and spawns a celebratory floating notification banner.
    """
    target_level_idx = max(0, min(len(LEVELS) - 1, target_level_idx))
    level_spec = LEVELS[target_level_idx]

    # 1. Retroactively grant all prior level rewards
    for prev_idx in range(target_level_idx):
        reward = LEVEL_REWARDS.get(prev_idx)
        if reward:
            for p in reward.plants:
                if p not in session.unlocked_plants:
                    session.unlocked_plants.add(p)
            if reward.artifact and reward.artifact not in session.unlocked_artifacts:
                session.unlocked_artifacts.add(reward.artifact)

    # 2. Endless Mode Grand Slam
    if target_level_idx >= 15:
        session.unlocked_plants.update(UNLOCK_ORDER)
        session.unlocked_artifacts.add("master_belt")

    # 3. Water lane carrier guarantee
    if level_spec.is_pool and "lilypad" not in session.unlocked_plants:
        session.unlocked_plants.add("lilypad")

    # 4. Advance highest level career record
    session.highest_level = max(session.highest_level, target_level_idx)
    session.current_level_idx = target_level_idx

    # 5. Smart update selected seed deck for the target level
    unlocked_list = [p for p in UNLOCK_ORDER if p in session.unlocked_plants]
    max_slots = session.max_seed_slots

    current_deck = [p for p in session.selected_seeds if p in session.unlocked_plants]
    if level_spec.is_pool and "lilypad" not in current_deck:
        current_deck.insert(0, "lilypad")

    # If deck is too small, intelligently fill it
    if len(current_deck) < max_slots:
        # Theme considerations
        sun_producer = "sunshroom" if "night" in level_spec.theme else "sunflower"
        if sun_producer in unlocked_list and sun_producer not in current_deck:
            current_deck.insert(0, sun_producer)

        for staple in ["wallnut", "repeater", "threepeater", "kernelpult", "cattail", "squash", "cherrybomb"]:
            if staple in unlocked_list and staple not in current_deck and len(current_deck) < max_slots:
                current_deck.append(staple)

        for p in unlocked_list:
            if p not in current_deck and len(current_deck) < max_slots:
                current_deck.append(p)

    session.selected_seeds = current_deck[:max_slots]

    # 6. Initialize the new battlefield
    world = start_level(target_level_idx, session)

    # 7. Add celebratory jump banner
    msg = f"【时空穿梭】跃迁至：第 {target_level_idx + 1:02d} 关 · {level_spec.name}"
    world.floating_texts.append(
        FloatingText(
            text=msg,
            x=320,
            y=120,
            color=(255, 220, 50),
            lifetime=2.5,
            vy=-18.0,
        )
    )

    return world
