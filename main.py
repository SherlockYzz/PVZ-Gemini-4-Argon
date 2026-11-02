# -*- coding: utf-8 -*-
"""Plants vs Zombies: Remastered & Modular Architecture.
Entry point: parses CLI arguments, builds composition root, and launches the game loop.
"""

import sys
import argparse
from pathlib import Path

# Ensure root package resolution
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.game_loop import GameApp
from domain.spec.levels import LEVELS
from usecases.skip_level import skip_to_level


def main() -> None:
    parser = argparse.ArgumentParser(description="植物大战僵尸 · 全新重构架构版")
    parser.add_argument("--level", type=int, default=None, help=f"Directly jump to level index (0-{len(LEVELS) - 1})")
    parser.add_argument("--fullscreen", action="store_true", help="Start directly in fullscreen mode")
    parser.add_argument("--mute", action="store_true", help="Mute all audio tracks and sounds")
    args = parser.parse_args()

    app = GameApp()

    if args.level is not None:
        target_idx = max(0, min(len(LEVELS) - 1, args.level))
        app.controller.world = skip_to_level(target_idx, app.session)
        app.controller._enter_seed_select()

    if args.fullscreen:
        app.viewport.toggle_fullscreen()

    if args.mute:
        app.audio.enabled = False

    app.run()


if __name__ == "__main__":
    main()
