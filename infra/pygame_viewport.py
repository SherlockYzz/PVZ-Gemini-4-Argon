# -*- coding: utf-8 -*-
"""Pygame Viewport and Letterbox Manager.
Handles resolution scaling, seamless F11 fullscreen toggling, letterboxing,
and exact inverse mouse coordinate mapping.
"""

import pygame
from config.tuning import WIDTH, HEIGHT


class Viewport:
    def __init__(self, caption: str = "植物大战僵尸 · 十关与无尽增强重构版"):
        pygame.display.set_caption(caption)
        self.logical_width = WIDTH
        self.logical_height = HEIGHT

        self.is_fullscreen = False
        self.window_surface = pygame.display.set_mode((self.logical_width, self.logical_height), pygame.RESIZABLE)
        self.canvas = pygame.Surface((self.logical_width, self.logical_height))

        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.update_dimensions()

    def update_dimensions(self) -> None:
        win_w, win_h = self.window_surface.get_size()
        scale_x = win_w / self.logical_width
        scale_y = win_h / self.logical_height
        self.scale = min(scale_x, scale_y)

        scaled_w = int(self.logical_width * self.scale)
        scaled_h = int(self.logical_height * self.scale)

        self.offset_x = (win_w - scaled_w) // 2
        self.offset_y = (win_h - scaled_h) // 2

    def toggle_fullscreen(self) -> bool:
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            self.window_surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.window_surface = pygame.display.set_mode((self.logical_width, self.logical_height), pygame.RESIZABLE)

        self.update_dimensions()
        return self.is_fullscreen

    def handle_resize(self, width: int, height: int) -> None:
        if not self.is_fullscreen:
            self.window_surface = pygame.display.set_mode((width, height), pygame.RESIZABLE)
            self.update_dimensions()

    def window_to_logical(self, wx: int, wy: int) -> tuple[float, float]:
        """Converts raw window coordinates to canvas 1200x760 logical coordinates."""
        if self.scale <= 0:
            return 0.0, 0.0
        lx = (wx - self.offset_x) / self.scale
        ly = (wy - self.offset_y) / self.scale
        return lx, ly

    def present(self) -> None:
        """Presents canvas onto the display window with ultra-low latency letterbox handling."""
        win_w, win_h = self.window_surface.get_size()
        scaled_w = int(self.logical_width * self.scale)
        scaled_h = int(self.logical_height * self.scale)

        # 1:1 Pixel Mapping Fast-Path: Zero-scaling, Zero-fill overhead
        if scaled_w == self.logical_width and scaled_h == self.logical_height and self.offset_x == 0 and self.offset_y == 0:
            self.window_surface.blit(self.canvas, (0, 0))
        else:
            scaled_canvas = pygame.transform.scale(self.canvas, (scaled_w, scaled_h))
            if self.offset_x > 0 or self.offset_y > 0:
                self.window_surface.fill((0, 0, 0))
            self.window_surface.blit(scaled_canvas, (self.offset_x, self.offset_y))

        pygame.display.flip()
