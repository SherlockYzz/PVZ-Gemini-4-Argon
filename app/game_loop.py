# -*- coding: utf-8 -*-
"""Main Game Application and Loop Orchestrator.
Coordinates viewport, inputs, audio, controller state, and 60 FPS presentation.
"""

import sys
import pygame
from config.tuning import FPS
from infra.pygame_viewport import Viewport
from infra.pygame_input import InputHandler
from infra.pygame_audio import PygameAudioAdapter
from infra.json_save import JsonSaveAdapter
from app.controller import GameController
from app.renderers.menu import render_menu
from app.renderers.seed_select import render_seed_select
from app.renderers.battle import render_battle
from app.renderers.hud import render_hud
from app.renderers.overlays import render_pause, render_victory, render_game_over, render_warp_overlay


class GameApp:
    def __init__(self):
        pygame.init()
        self.clock = pygame.time.Clock()
        self.viewport = Viewport()
        self.input_handler = InputHandler(self.viewport)
        self.audio = PygameAudioAdapter()
        self.storage = JsonSaveAdapter()

        # Load session progress from disk
        self.session = self.storage.load()
        self.controller = GameController(self.session, self.audio, self.storage)
        self.is_running = True

    def run(self) -> None:
        while self.is_running:
            dt = self.clock.tick(FPS) / 1000.0
            # Clamp dt to avoid physics explode on long frame hitch
            dt = min(0.08, dt)

            # 1. Poll Inputs
            events = self.input_handler.poll_events()
            menu_btns = {}
            seed_btns = {}
            overlay_btns = {}

            # 2. Advance Simulation
            self.controller.tick_battle(dt)

            # 3. Render Canvas
            canvas = self.viewport.canvas
            mouse_pos = (self.input_handler.mouse_x, self.input_handler.mouse_y)
            mode = self.controller.mode

            if mode == "menu":
                menu_btns = render_menu(canvas, self.session, mouse_pos)

            elif mode == "seed_select":
                seed_btns = render_seed_select(canvas, self.session, mouse_pos)

            elif mode == "battle":
                if self.controller.world:
                    render_battle(canvas, self.controller.world, self.session, mouse_pos)
                    render_hud(canvas, self.controller.world, self.session, mouse_pos, self.controller.hud_rects)

            elif mode == "pause":
                if self.controller.world:
                    render_battle(canvas, self.controller.world, self.session, mouse_pos)
                    render_hud(canvas, self.controller.world, self.session, mouse_pos, self.controller.hud_rects)
                overlay_btns = render_pause(canvas)

            elif mode == "victory":
                if self.controller.world:
                    render_battle(canvas, self.controller.world, self.session, mouse_pos)
                    render_hud(canvas, self.controller.world, self.session, mouse_pos, self.controller.hud_rects)
                overlay_btns = render_victory(canvas, self.controller.latest_reward)

            elif mode == "game_over":
                if self.controller.world:
                    render_battle(canvas, self.controller.world, self.session, mouse_pos)
                    render_hud(canvas, self.controller.world, self.session, mouse_pos, self.controller.hud_rects)
                overlay_btns = render_game_over(canvas)

            elif mode == "warp":
                if self.controller.world:
                    render_battle(canvas, self.controller.world, self.session, mouse_pos)
                    render_hud(canvas, self.controller.world, self.session, mouse_pos, self.controller.hud_rects)
                overlay_btns = render_warp_overlay(canvas, self.session, mouse_pos)

            # 4. Dispatch events to controller
            for ev in events:
                if ev.kind == "quit":
                    self.is_running = False
                elif ev.kind == "fullscreen":
                    self.viewport.toggle_fullscreen()
                else:
                    self.controller.handle_event(
                        ev, menu_buttons=menu_btns, seed_buttons=seed_btns, overlay_buttons=overlay_btns
                    )

            # 5. Present letterboxed canvas to window display
            self.viewport.present()

        # Shutdown & Save
        self.storage.save(self.session)
        pygame.quit()
