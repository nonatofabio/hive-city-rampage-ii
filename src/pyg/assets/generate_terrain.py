#!/usr/bin/env python3
"""
Generate grim dark terrain sprites for Hive City Rampage
Creates 32x32 pixel tiles with industrial/gothic aesthetic
"""

import pygame as pg
import random
import math

def create_wall_tile():
    """Create a grim dark industrial wall tile"""
    tile = pg.Surface((32, 32), pg.SRCALPHA)

    # Base dark metal color
    base_color = (35, 35, 40)
    tile.fill(base_color)

    # Add metal panel lines
    panel_color = (25, 25, 30)
    pg.draw.line(tile, panel_color, (0, 8), (32, 8), 2)
    pg.draw.line(tile, panel_color, (0, 24), (32, 24), 2)
    pg.draw.line(tile, panel_color, (10, 0), (10, 32), 1)
    pg.draw.line(tile, panel_color, (22, 0), (22, 32), 1)

    # Add rivets
    rivet_color = (45, 45, 50)
    rivet_shadow = (20, 20, 25)
    for x in [4, 16, 28]:
        for y in [4, 16, 28]:
            pg.draw.circle(tile, rivet_shadow, (x+1, y+1), 2)
            pg.draw.circle(tile, rivet_color, (x, y), 2)
            pg.draw.circle(tile, (55, 55, 60), (x-1, y-1), 1)

    # Add rust and wear
    rust_color = (60, 40, 30)
    wear_color = (50, 50, 55)
    for _ in range(20):
        x = random.randint(0, 31)
        y = random.randint(0, 31)
        if random.random() > 0.5:
            tile.set_at((x, y), rust_color)
        else:
            tile.set_at((x, y), wear_color)

    # Add edge highlight (top-left light source)
    highlight = (48, 48, 53)
    pg.draw.line(tile, highlight, (0, 0), (31, 0), 1)
    pg.draw.line(tile, highlight, (0, 0), (0, 31), 1)

    # Add shadow (bottom-right)
    shadow = (15, 15, 20)
    pg.draw.line(tile, shadow, (31, 1), (31, 31), 1)
    pg.draw.line(tile, shadow, (1, 31), (31, 31), 1)

    return tile

def create_floor_tile():
    """Create a grim dark industrial floor tile"""
    tile = pg.Surface((32, 32), pg.SRCALPHA)

    # Base floor color (darker than walls)
    base_color = (20, 20, 24)
    tile.fill(base_color)

    # Add metal grating pattern
    grate_color = (15, 15, 18)
    grate_light = (25, 25, 29)

    # Horizontal grates
    for y in range(0, 32, 4):
        pg.draw.line(tile, grate_color, (0, y), (32, y), 1)
        if y > 0:
            pg.draw.line(tile, grate_light, (0, y-1), (32, y-1), 1)

    # Vertical grates (less prominent)
    for x in range(0, 32, 8):
        pg.draw.line(tile, grate_color, (x, 0), (x, 32), 1)

    # Add oil stains and grime
    stain_color = (10, 8, 12)
    for _ in range(3):
        x = random.randint(4, 28)
        y = random.randint(4, 28)
        radius = random.randint(3, 6)
        # Create irregular stain shape
        for angle in range(0, 360, 30):
            rad = math.radians(angle)
            rx = int(x + math.cos(rad) * radius * random.uniform(0.7, 1.3))
            ry = int(y + math.sin(rad) * radius * random.uniform(0.7, 1.3))
            if 0 <= rx < 32 and 0 <= ry < 32:
                pg.draw.circle(tile, stain_color, (rx, ry), 2)

    # Add scattered debris/scratches
    scratch_color = (30, 30, 35)
    for _ in range(8):
        x1 = random.randint(0, 31)
        y1 = random.randint(0, 31)
        x2 = x1 + random.randint(-4, 4)
        y2 = y1 + random.randint(-4, 4)
        x2 = max(0, min(31, x2))
        y2 = max(0, min(31, y2))
        pg.draw.line(tile, scratch_color, (x1, y1), (x2, y2), 1)

    # Add subtle highlight spots (worn metal showing through)
    for _ in range(5):
        x = random.randint(2, 29)
        y = random.randint(2, 29)
        tile.set_at((x, y), (35, 35, 40))

    return tile

def create_wall_variants(base_tile, count=4):
    """Create variations of the wall tile"""
    variants = []
    for i in range(count):
        variant = base_tile.copy()

        # Add random damage/bullet holes
        if random.random() > 0.5:
            x = random.randint(4, 28)
            y = random.randint(4, 28)
            pg.draw.circle(variant, (15, 15, 20), (x, y), 3)
            pg.draw.circle(variant, (10, 10, 15), (x, y), 2)

        # Add occasional warning stripes
        if random.random() > 0.7:
            stripe_color = (60, 50, 20)
            for offset in range(0, 32, 8):
                pg.draw.line(variant, stripe_color, (offset, 30), (offset+4, 26), 2)

        # Add Aquila or skull decoration occasionally
        if random.random() > 0.85:
            decor_color = (55, 50, 45)
            # Simple skull shape
            cx, cy = 16, 10
            pg.draw.circle(variant, decor_color, (cx, cy), 4)
            pg.draw.circle(variant, (20, 20, 25), (cx-2, cy), 1)
            pg.draw.circle(variant, (20, 20, 25), (cx+2, cy), 1)

        variants.append(variant)

    return variants

def create_floor_variants(base_tile, count=4):
    """Create variations of the floor tile"""
    variants = []
    for i in range(count):
        variant = base_tile.copy()

        # Add blood splatter occasionally
        if random.random() > 0.8:
            blood_color = (40, 10, 10)
            x = random.randint(8, 24)
            y = random.randint(8, 24)
            for _ in range(5):
                sx = x + random.randint(-4, 4)
                sy = y + random.randint(-4, 4)
                if 0 <= sx < 32 and 0 <= sy < 32:
                    pg.draw.circle(variant, blood_color, (sx, sy), random.randint(1, 2))

        # Add drainage grate occasionally
        if random.random() > 0.85:
            grate_x = random.choice([8, 24])
            grate_y = random.choice([8, 24])
            pg.draw.rect(variant, (10, 10, 12), (grate_x-4, grate_y-4, 8, 8))
            for offset in range(-3, 4, 2):
                pg.draw.line(variant, (5, 5, 8),
                           (grate_x-3, grate_y+offset),
                           (grate_x+3, grate_y+offset), 1)

        variants.append(variant)

    return variants

def main():
    pg.init()

    # Generate base tiles
    print("Generating grim dark terrain tiles...")

    wall_base = create_wall_tile()
    floor_base = create_floor_tile()

    # Save basic tiles
    pg.image.save(wall_base, "terrain_wall.png")
    pg.image.save(floor_base, "terrain_floor.png")
    print("✓ Created terrain_wall.png (32x32)")
    print("✓ Created terrain_floor.png (32x32)")

    # Create variant sprite sheets (optional)
    wall_variants = create_wall_variants(wall_base, 8)
    floor_variants = create_floor_variants(floor_base, 8)

    # Create sprite sheets for variants
    wall_sheet = pg.Surface((32 * 8, 32), pg.SRCALPHA)
    floor_sheet = pg.Surface((32 * 8, 32), pg.SRCALPHA)

    for i, variant in enumerate(wall_variants):
        wall_sheet.blit(variant, (i * 32, 0))

    for i, variant in enumerate(floor_variants):
        floor_sheet.blit(variant, (i * 32, 0))

    pg.image.save(wall_sheet, "terrain_walls_sheet.png")
    pg.image.save(floor_sheet, "terrain_floors_sheet.png")
    print("✓ Created terrain_walls_sheet.png (256x32) - 8 variants")
    print("✓ Created terrain_floors_sheet.png (256x32) - 8 variants")

    print("\nTerrain sprites generated successfully!")
    print("The game will use terrain_wall.png and terrain_floor.png")
    print("Variant sheets are available for more variety if needed")

if __name__ == "__main__":
    main()