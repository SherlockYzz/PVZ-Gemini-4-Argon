# -*- coding: utf-8 -*-
"""Game Controller and State Machine.
Directs semantic events to use cases and manages screen mode transitions.
"""

from typing import Optional
import pygame

from domain.model.session import Session
from domain.model.world import World
from domain.model.particle import FloatingText
from domain.spec.levels import LEVELS
from domain.spec.rewards import LevelReward, UNLOCK_ORDER
from domain.spec.plants import PLANTS
from infra.pygame_input import InputEvent
from infra.pygame_audio import PygameAudioAdapter
from infra.json_save import JsonSaveAdapter
from usecases.start_level import start_level
from usecases.skip_level import skip_to_level
from usecases.plant_seed import execute_plant_action, execute_shovel_action
from usecases.collect_sun import execute_collect_sun
from usecases.advance_frame import advance_battle_frame
from usecases.toggle_setting import toggle_auto_sun, toggle_game_speed
from app.hud_layout import compute_hud_layout, HudRects


class GameController:
    def __init__(self, session: Session, audio: PygameAudioAdapter, storage: JsonSaveAdapter):
        self.session = session
        self.audio = audio
        self.storage = storage

        self.mode = "menu"  # "menu", "seed_select", "battle", "pause", "victory", "game_over", "warp"
        self.world: Optional[World] = None
        self.latest_reward: Optional[LevelReward] = None

        # HUD geometry depends on the live belt capacity, which grows mid-session
        # when a belt artifact is unlocked (8 -> 9 -> 10 slots). Caching it once in
        # __init__ made the renderer index a stale, shorter card_slots list and crash
        # with IndexError. Cache it but invalidate whenever the capacity changes.
        self._hud_rects_cache: Optional[HudRects] = None
        self._hud_rects_slot_count: int = -1

        # Play title music
        self.audio.play_music("menu")

    @property
    def hud_rects(self) -> HudRects:
        """HUD hit-boxes, kept in sync with the live seed belt capacity.

        Session.max_seed_slots changes at runtime (belt artifacts / retroactive
        skip rewards), so this must never be a frozen value computed at boot.
        """
        slot_count = self.session.max_seed_slots
        if self._hud_rects_cache is None or self._hud_rects_slot_count != slot_count:
            self._hud_rects_cache = compute_hud_layout(slot_count)
            self._hud_rects_slot_count = slot_count
        return self._hud_rects_cache

    def handle_event(self, event: InputEvent, menu_buttons: dict = None, seed_buttons: dict = None, overlay_buttons: dict = None) -> None:
        if event.kind == "fullscreen":
            return

        if self.mode == "menu":
            self._handle_menu_event(event, menu_buttons)
        elif self.mode == "seed_select":
            self._handle_seed_select_event(event, seed_buttons)
        elif self.mode == "battle":
            self._handle_battle_event(event)
        elif self.mode == "warp":
            self._handle_warp_event(event, overlay_buttons)
        elif self.mode in ("pause", "victory", "game_over"):
            self._handle_overlay_event(event, overlay_buttons)

    def _handle_menu_event(self, event: InputEvent, buttons: dict) -> None:
        if event.kind == "click" and buttons:
            mx, my = event.x, event.y
            for name, rect in buttons.items():
                if rect.collidepoint(mx, my):
                    self.audio.play_sound("click")
                    if name.startswith("level_"):
                        idx = int(name.split("_")[1])
                        self.session.current_level_idx = idx
                    elif name == "start":
                        self._enter_seed_select()
                    elif name == "endless":
                        self.session.current_level_idx = 15  # Level 16 is endless
                        self._enter_seed_select()

    def _enter_seed_select(self) -> None:
        self.mode = "seed_select"
        self.audio.play_music("seeds")
        # Ensure default seed selection if empty
        if not self.session.selected_seeds:
            self._smart_recommend_seeds()

    def _smart_recommend_seeds(self) -> None:
        """Smart deck recommendation based on level theme and unlocked plants."""
        lvl_idx = self.session.current_level_idx
        lvl_spec = LEVELS[lvl_idx] if lvl_idx < len(LEVELS) else LEVELS[0]
        unlocked = [p for p in UNLOCK_ORDER if p in self.session.unlocked_plants]

        selected = []
        # Night vs Day sun economy
        if lvl_spec.theme in ("night", "pool_night"):
            if "sunshroom" in unlocked:
                selected.append("sunshroom")
            if "puffshroom" in unlocked:
                selected.append("puffshroom")
        else:
            if "sunflower" in unlocked:
                selected.append("sunflower")

        # Pool requires Lilypad
        if lvl_spec.is_pool and "lilypad" in unlocked:
            selected.append("lilypad")

        # Core defense and attack
        for core in ["wallnut", "repeater", "threepeater", "kernelpult", "cattail", "squash", "cherrybomb", "peashooter"]:
            if core in unlocked and core not in selected and len(selected) < self.session.max_seed_slots:
                selected.append(core)

        # Fill remaining slots
        for p in unlocked:
            if p not in selected and len(selected) < self.session.max_seed_slots:
                selected.append(p)

        self.session.selected_seeds = selected

    def _handle_seed_select_event(self, event: InputEvent, buttons: dict) -> None:
        if event.kind == "click" and buttons:
            mx, my = event.x, event.y
            for name, rect in buttons.items():
                if rect.collidepoint(mx, my):
                    self.audio.play_sound("click")
                    if name.startswith("catalog_"):
                        p_id = name.split("_", 1)[1]
                        if p_id in self.session.selected_seeds:
                            self.session.selected_seeds.remove(p_id)
                        elif len(self.session.selected_seeds) < self.session.max_seed_slots:
                            self.session.selected_seeds.append(p_id)
                    elif name.startswith("tray_"):
                        idx = int(name.split("_")[1])
                        if idx < len(self.session.selected_seeds):
                            self.session.selected_seeds.pop(idx)
                    elif name == "auto_fill":
                        self._smart_recommend_seeds()
                    elif name == "start_battle":
                        if self.session.selected_seeds:
                            self._start_battle()
                    elif name == "back":
                        self.mode = "menu"
                        self.audio.play_music("menu")

    def _sync_music_for_level(self) -> None:
        lvl_spec = LEVELS[self.session.current_level_idx]
        music_track = "endless" if lvl_spec.is_endless else "night" if "night" in lvl_spec.theme else "day"
        self.audio.play_music(music_track)

    def _start_battle(self) -> None:
        self._hud_rects = compute_hud_layout(self.session.max_seed_slots)
        self.world = start_level(self.session.current_level_idx, self.session)
        self.mode = "battle"
        self._sync_music_for_level()

    def _handle_battle_event(self, event: InputEvent) -> None:
        if not self.world:
            return

        # 1. Hotkeys
        if event.kind == "key":
            if event.key_name == "escape":
                self.session.active_seed_idx = None
                self.session.active_shovel = False
            elif event.key_name == "shovel":
                self.session.active_shovel = not self.session.active_shovel
                self.session.active_seed_idx = None
                self.audio.play_sound("click")
            elif event.key_name == "auto_sun":
                toggle_auto_sun(self.session)
                self.audio.play_sound("click")
            elif event.key_name == "pause":
                self.mode = "pause"
            elif event.key_name == "toggle_warp":
                self.mode = "warp"
                self.audio.play_sound("click")
            elif event.key_name == "skip_next":
                target = (self.session.current_level_idx + 1) % len(LEVELS)
                self.world = skip_to_level(target, self.session)
                self.storage.save(self.session)
                self.audio.play_sound("win")
                self._sync_music_for_level()
            elif event.key_name == "skip_prev":
                target = (self.session.current_level_idx - 1) % len(LEVELS)
                self.world = skip_to_level(target, self.session)
                self.storage.save(self.session)
                self.audio.play_sound("win")
                self._sync_music_for_level()
            elif event.seed_slot is not None:
                if event.seed_slot < len(self.session.selected_seeds):
                    self.session.active_seed_idx = event.seed_slot
                    self.session.active_shovel = False
                    self.audio.play_sound("click")
            return

        # 2. Right click cancels selection
        if event.kind == "right_click":
            self.session.active_seed_idx = None
            self.session.active_shovel = False
            return

        # 3. Mouse hover over suns
        if event.kind == "move":
            execute_collect_sun(event.x, event.y, self.world)
            return

        # 4. Mouse click
        if event.kind == "click":
            mx, my = event.x, event.y

            # Check HUD buttons first
            if self.hud_rects.shovel_button.collidepoint(mx, my):
                self.session.active_shovel = not self.session.active_shovel
                self.session.active_seed_idx = None
                self.audio.play_sound("click")
                return

            if self.hud_rects.speed_button.collidepoint(mx, my):
                toggle_game_speed(self.session)
                self.audio.play_sound("click")
                return

            if self.hud_rects.pause_button.collidepoint(mx, my):
                self.mode = "pause"
                self.audio.play_sound("click")
                return

            if self.hud_rects.skip_button.collidepoint(mx, my):
                self.mode = "warp"
                self.audio.play_sound("click")
                return

            if self.session.has_auto_sun and self.hud_rects.auto_sun_toggle.collidepoint(mx, my):
                toggle_auto_sun(self.session)
                self.audio.play_sound("click")
                return

            # Check card slots (switching or selecting card)
            for i, slot_rect in enumerate(self.hud_rects.card_slots):
                if slot_rect.collidepoint(mx, my):
                    if i < len(self.session.selected_seeds):
                        if self.session.active_seed_idx == i:
                            self.session.active_seed_idx = None
                        else:
                            self.session.active_seed_idx = i
                            self.session.active_shovel = False
                        self.audio.play_sound("click")
                    return

            # Priority 1: Lawn Placement / Shoveling when holding card or shovel
            if self.session.active_shovel:
                col, row = self.world.layout.pos_to_cell(mx, my)
                if col is not None and row is not None:
                    shoveled = execute_shovel_action(col, row, self.world, self.session)
                    if shoveled:
                        self.audio.play_sound("plant")
                    return

            if self.session.active_seed_idx is not None:
                col, row = self.world.layout.pos_to_cell(mx, my)
                if col is not None and row is not None:
                    planted, reason = execute_plant_action(col, row, self.world, self.session)
                    if planted:
                        self.audio.play_sound("plant")
                    else:
                        self.audio.play_sound("click")
                        cx, cy = self.world.layout.get_cell_center(col, row)
                        self.world.floating_texts.append(
                            FloatingText(
                                text=f"⚠ {reason}",
                                x=max(120, min(800, cx - 70)),
                                y=max(70, cy - 25),
                                color=(255, 90, 80),
                                lifetime=2.0,
                                vy=-14.0,
                            )
                        )
                    return
                else:
                    # Clicked off-lawn while holding seed card
                    self.world.floating_texts.append(
                        FloatingText("⚠ 请点击草坪格种植植物", max(120, min(800, mx - 70)), max(65, my - 20), (255, 100, 100), lifetime=1.5, vy=-12.0)
                    )
                    return

            # Priority 2: Sun collection (when not holding a card/shovel)
            collected = execute_collect_sun(mx, my, self.world)
            if collected:
                self.audio.play_sound("collect")
                return

    def _handle_warp_event(self, event: InputEvent, buttons: dict) -> None:
        if event.kind == "key":
            if event.key_name in ("escape", "toggle_warp"):
                self.mode = "battle"
                self.audio.play_sound("click")
                return
            elif event.key_name == "skip_next":
                target = (self.session.current_level_idx + 1) % len(LEVELS)
                self.world = skip_to_level(target, self.session)
                self.storage.save(self.session)
                self.mode = "battle"
                self.audio.play_sound("win")
                self._sync_music_for_level()
                return
            elif event.key_name == "skip_prev":
                target = (self.session.current_level_idx - 1) % len(LEVELS)
                self.world = skip_to_level(target, self.session)
                self.storage.save(self.session)
                self.mode = "battle"
                self.audio.play_sound("win")
                self._sync_music_for_level()
                return
            return

        if event.kind != "click" or not buttons:
            return

        mx, my = event.x, event.y
        for name, rect in buttons.items():
            if rect.collidepoint(mx, my):
                if name == "warp_close":
                    self.mode = "battle"
                    self.audio.play_sound("click")
                    return
                elif name == "warp_next":
                    target = (self.session.current_level_idx + 1) % len(LEVELS)
                    self.world = skip_to_level(target, self.session)
                    self.storage.save(self.session)
                    self.mode = "battle"
                    self.audio.play_sound("win")
                    self._sync_music_for_level()
                    return
                elif name.startswith("warp_"):
                    idx = int(name.split("_")[1])
                    self.world = skip_to_level(idx, self.session)
                    self.storage.save(self.session)
                    self.mode = "battle"
                    self.audio.play_sound("win")
                    self._sync_music_for_level()
                    return

    def _handle_overlay_event(self, event: InputEvent, buttons: dict) -> None:
        if event.kind == "key":
            if self.mode == "pause" and event.key_name in ("pause", "escape"):
                self.mode = "battle"
                self.audio.play_sound("click")
            return

        if event.kind != "click" or not buttons:
            return

        mx, my = event.x, event.y
        for name, rect in buttons.items():
            if rect.collidepoint(mx, my):
                self.audio.play_sound("click")
                if name == "resume":
                    self.mode = "battle"
                elif name == "restart" or name == "retry":
                    self._start_battle()
                elif name == "next_level":
                    self.session.current_level_idx = min(15, self.session.current_level_idx + 1)
                    self._enter_seed_select()
                elif name == "menu":
                    self.storage.save(self.session)
                    self.mode = "menu"
                    self.audio.play_music("menu")

    def tick_battle(self, dt: float) -> None:
        """Ticks the simulation when in battle mode."""
        if self.mode != "battle" or not self.world:
            return

        reward = advance_battle_frame(self.world, self.session, dt)

        if self.world.is_victory:
            self.mode = "victory"
            self.latest_reward = reward
            self._hud_rects = compute_hud_layout(self.session.max_seed_slots)
            self.audio.play_sound("win")
            self.storage.save(self.session)
        elif self.world.is_game_over:
            self.mode = "game_over"
            self.audio.play_sound("lose")
