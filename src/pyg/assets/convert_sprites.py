#!/usr/bin/env python3
"""
Convert single-frame sprites to 4-frame animation strips.
Creates subtle idle animation (bobbing/breathing effect).
"""

import pygame as pg
import math
import os

# Target frame size (matching marine sprites: 136/4 = 34 width, 48 height)
FRAME_W = 34
FRAME_H = 48
NUM_FRAMES = 4


def create_animation_strip(source_img, name):
    """
    Take a single-frame sprite and create a 4-frame animation strip
    with subtle idle animation (vertical bobbing).
    """
    src_w, src_h = source_img.get_size()

    # Calculate scale to fit in frame (with some padding)
    max_w = FRAME_W - 4  # leave 2px padding on each side
    max_h = FRAME_H - 6  # leave 3px padding top/bottom

    scale_w = max_w / src_w
    scale_h = max_h / src_h
    scale = min(scale_w, scale_h)

    new_w = int(src_w * scale)
    new_h = int(src_h * scale)

    # Scale the source sprite
    scaled = pg.transform.smoothscale(source_img, (new_w, new_h))

    # Create the animation strip
    strip = pg.Surface((FRAME_W * NUM_FRAMES, FRAME_H), pg.SRCALPHA)

    for frame in range(NUM_FRAMES):
        # Calculate bob offset (subtle up/down motion)
        bob = int(math.sin(frame * math.pi / 2) * 2)  # -2 to +2 pixels

        # Calculate horizontal position (centered in frame)
        x = frame * FRAME_W + (FRAME_W - new_w) // 2
        # Vertical position (bottom-aligned with bob)
        y = FRAME_H - new_h - 2 + bob

        strip.blit(scaled, (x, y))

    return strip


def main():
    pg.init()
    pg.display.set_mode((100, 100))  # Required for convert_alpha()

    print("Converting single-frame sprites to animation strips...")
    print(f"Target frame size: {FRAME_W}x{FRAME_H}, {NUM_FRAMES} frames")
    print("-" * 50)

    # Sprites to convert (single-frame -> animation strip)
    sprites_to_convert = [
        ('grunt_idle.png', 'grunt_idle_strip.png'),
        ('runner_idle.png', 'runner_idle_strip.png'),
        ('brute_idle.png', 'brute_idle_strip.png'),
    ]

    for src_name, dst_name in sprites_to_convert:
        if not os.path.exists(src_name):
            print(f"[SKIP] {src_name} not found")
            continue

        # Check if it's already a strip (width > height * 2)
        src_img = pg.image.load(src_name).convert_alpha()
        src_w, src_h = src_img.get_size()

        if src_w > src_h * 2:
            print(f"[SKIP] {src_name} already appears to be an animation strip ({src_w}x{src_h})")
            continue

        print(f"[CONVERT] {src_name} ({src_w}x{src_h}) -> {dst_name}")

        strip = create_animation_strip(src_img, src_name)
        strip_w, strip_h = strip.get_size()

        # Save the new strip (overwrite the original)
        pg.image.save(strip, src_name)
        print(f"  Saved {src_name} ({strip_w}x{strip_h})")

    print("-" * 50)
    print("Conversion complete!")
    print(f"\nNote: Update game SPR constant to {FRAME_W} or adjust frame slicing")


if __name__ == "__main__":
    main()
