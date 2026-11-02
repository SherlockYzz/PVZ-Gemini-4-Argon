# -*- coding: utf-8 -*-
"""Batch chroma-key greenscreen cleaner for plant and item sprites."""

import sys
from pathlib import Path
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
PLANTS_DIR = BASE_DIR / "assets" / "plants"
ITEMS_DIR = BASE_DIR / "assets" / "items"


def clean_greenscreen(img: Image.Image) -> tuple[Image.Image, int]:
    img = img.convert("RGBA")
    w, h = img.size
    pixels = img.load()
    removed = 0

    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if a == 0:
                continue

            # Pure Chroma-Key green screen:
            # High G, low R, low B, with strong green dominance
            is_greenscreen = False
            if g >= 110 and r <= 60 and b <= 60 and g >= max(1, r) * 1.5 and g >= max(1, b) * 1.5:
                is_greenscreen = True
            elif g >= 95 and r <= 42 and b <= 42 and g >= max(1, r + b) * 1.3:
                is_greenscreen = True
            elif g >= 140 and r <= 70 and b <= 70 and g > (r + b) * 1.25:
                is_greenscreen = True

            if is_greenscreen:
                pixels[x, y] = (0, 0, 0, 0)
                removed += 1

    return img, removed


def process_directory(directory: Path) -> None:
    total_cleaned = 0
    cleaned_files = 0

    for png_file in directory.rglob("*.png"):
        try:
            with Image.open(png_file) as img:
                cleaned_img, count = clean_greenscreen(img)
                if count > 0:
                    cleaned_img.save(png_file, format="PNG")
                    total_cleaned += count
                    cleaned_files += 1
                    print(f"Cleaned {count:5d} px from {png_file.relative_to(BASE_DIR)}")
        except Exception as e:
            print(f"Error processing {png_file}: {e}")

    print(f"\nCompleted! Cleaned {total_cleaned} green screen pixels across {cleaned_files} files in {directory.name}.")


if __name__ == "__main__":
    print("=== Cleaning Plant Sprites Greenscreen Residues ===")
    process_directory(PLANTS_DIR)
    print("\n=== Cleaning Item Sprites Greenscreen Residues ===")
    process_directory(ITEMS_DIR)
