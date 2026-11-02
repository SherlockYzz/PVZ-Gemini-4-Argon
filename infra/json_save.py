# -*- coding: utf-8 -*-
"""JSON persistence adapter.
Implements SavePort with atomic writes to guarantee file integrity.
"""

import json
import os
from pathlib import Path
from typing import Any, Optional
from config.tuning import SAVE_FILE
from domain.model.session import Session


class JsonSaveAdapter:
    def __init__(self, file_path: Path = SAVE_FILE):
        self.file_path = file_path

    def load(self) -> Session:
        if not self.file_path.exists():
            return Session()

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            def _safe_int(val: Any, default: int = 0, min_v: Optional[int] = None, max_v: Optional[int] = None) -> int:
                try:
                    res = int(val)
                except (ValueError, TypeError):
                    res = default
                if min_v is not None:
                    res = max(min_v, res)
                if max_v is not None:
                    res = min(max_v, res)
                return res

            def _safe_float(val: Any, default: float = 1.0, min_v: float = 0.5, max_v: float = 3.0) -> float:
                try:
                    res = float(val)
                except (ValueError, TypeError):
                    res = default
                return max(min_v, min(max_v, res))

            raw_cur = data.get("current_level", 0)
            raw_high = data.get("highest_level", data.get("level", 0))

            session = Session(
                current_level_idx=_safe_int(raw_cur, 0, 0, 15),
                highest_level=_safe_int(raw_high, 0, 0, 15),
                unlocked_plants=set(data.get("unlocked_plants", ["sunflower", "peashooter"])),
                unlocked_artifacts=set(data.get("unlocked_artifacts", [])),
                endless_best_wave=_safe_int(data.get("endless_record", 0), 0, 0),
                auto_sun_enabled=bool(data.get("auto_sun_enabled", True)),
                speed_multiplier=_safe_float(data.get("speed_multiplier", 1.0)),
                sound_enabled=bool(data.get("sound_enabled", True)),
                music_enabled=bool(data.get("music_enabled", True)),
                is_fullscreen=bool(data.get("is_fullscreen", False)),
            )
            # Ensure basic plants are unlocked
            session.unlocked_plants.add("sunflower")
            session.unlocked_plants.add("peashooter")
            return session
        except Exception as e:
            print(f"Warning: Failed to load save file, fallback to default. Error: {e}")
            return Session()

    def save(self, session: Session) -> bool:
        data: dict[str, Any] = {
            "current_level": session.current_level_idx,
            "highest_level": session.highest_level,
            "level": session.highest_level,
            "unlocked_plants": sorted(list(session.unlocked_plants)),
            "unlocked_artifacts": sorted(list(session.unlocked_artifacts)),
            "endless_record": session.endless_best_wave,
            "auto_sun_enabled": session.auto_sun_enabled,
            "speed_multiplier": session.speed_multiplier,
            "sound_enabled": session.sound_enabled,
            "music_enabled": session.music_enabled,
            "is_fullscreen": session.is_fullscreen,
        }

        try:
            # Atomic write via temporary file
            temp_path = self.file_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(temp_path, self.file_path)
            return True
        except Exception as e:
            print(f"Error: Failed to save progress. Error: {e}")
            return False
