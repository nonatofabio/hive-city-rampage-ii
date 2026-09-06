#!/usr/bin/env python3
"""
Generate advanced grim dark terrain sprites including:
- Corner tiles
- Damaged/destroyed sections
- Hazard areas
- Animated tiles (lights, steam vents)
- Decal overlays
"""

import pygame as pg
import random
import math
import json

def create_corner_tiles():
    """Create corner wall tiles for better transitions"""
    corners = {}

    # Define corner types
    corner_types = [
        ("corner_outer_tl", 0, 0, False, False),   # Top-left outer
        ("corner_outer_tr", 1, 0, True, False),    # Top-right outer
        ("corner_outer_bl", 0, 1, False, True),    # Bottom-left outer
        ("corner_outer_br", 1, 1, True, True),     # Bottom-right outer
        ("corner_inner_tl", 2, 0, False, False),   # Top-left inner
        ("corner_inner_tr", 3, 0, True, False),    # Top-right inner
        ("corner_inner_bl", 2, 1, False, True),    # Bottom-left inner
        ("corner_inner_br", 3, 1, True, True),     # Bottom-right inner
    ]

    for name, style, variant, flip_h, flip_v in corner_types:
        tile = pg.Surface((32, 32), pg.SRCALPHA)
        base_color = (35, 35, 40)
        tile.fill(base_color)

        if style in [0, 1]:  # Outer corners
            # Draw L-shaped wall
            if style == 0:  # Top-left
                pg.draw.rect(tile, (25, 25, 30), (0, 0, 32, 16))
                pg.draw.rect(tile, (25, 25, 30), (0, 0, 16, 32))
            else:  # Other corners use flipping

                pg.draw.rect(tile, (25, 25, 30), (0, 0, 32, 16))
                pg.draw.rect(tile, (25, 25, 30), (16, 0, 16, 32))

        else:  # Inner corners
            # Fill most of tile, leave corner empty
            pg.draw.rect(tile, (25, 25, 30), (0, 0, 32, 32))
            if style == 2:  # Top-left inner
                pg.draw.rect(tile, (18, 18, 22), (0, 0, 16, 16))
            else:  # Top-right inner
                pg.draw.rect(tile, (18, 18, 22), (16, 0, 16, 16))

        # Add details
        add_wall_details(tile)

        if flip_h:
            tile = pg.transform.flip(tile, True, False)
        if flip_v:
            tile = pg.transform.flip(tile, False, True)

        corners[name] = tile

    return corners

def add_wall_details(tile):
    """Add rivets and wear to wall tiles"""
    # Add some rivets
    rivet_color = (45, 45, 50)
    for _ in range(3):
        x = random.randint(4, 28)
        y = random.randint(4, 28)
        if tile.get_at((x, y))[3] > 0:  # Only on solid parts
            pg.draw.circle(tile, rivet_color, (x, y), 2)
            pg.draw.circle(tile, (55, 55, 60), (x-1, y-1), 1)

def create_damaged_tiles():
    """Create heavily damaged wall sections"""
    damaged = []

    for i in range(4):
        tile = pg.Surface((32, 32), pg.SRCALPHA)

        # Start with wall base
        base_color = (35, 35, 40)
        tile.fill(base_color)

        # Create large damage holes
        hole_count = random.randint(1, 3)
        for _ in range(hole_count):
            x = random.randint(8, 24)
            y = random.randint(8, 24)
            radius = random.randint(4, 8)

            # Create irregular hole shape
            for angle in range(0, 360, 20):
                rad = math.radians(angle)
                rx = int(x + math.cos(rad) * radius * random.uniform(0.6, 1.2))
                ry = int(y + math.sin(rad) * radius * random.uniform(0.6, 1.2))
                if 0 <= rx < 32 and 0 <= ry < 32:
                    pg.draw.circle(tile, (18, 18, 22), (rx, ry), 3)

            # Add cracks radiating from hole
            for _ in range(4):
                angle = random.random() * math.pi * 2
                length = random.randint(6, 12)
                end_x = int(x + math.cos(angle) * length)
                end_y = int(y + math.sin(angle) * length)
                end_x = max(0, min(31, end_x))
                end_y = max(0, min(31, end_y))
                pg.draw.line(tile, (15, 15, 20), (x, y), (end_x, end_y), 1)

        # Add scorch marks
        for _ in range(5):
            x = random.randint(2, 29)
            y = random.randint(2, 29)
            pg.draw.circle(tile, (20, 15, 10), (x, y), random.randint(2, 4))

        damaged.append(tile)

    return damaged

def create_hazard_tiles():
    """Create hazard floor tiles (toxic waste, electric panels, etc.)"""
    hazards = {}

    # Toxic waste tile
    toxic = pg.Surface((32, 32), pg.SRCALPHA)
    toxic.fill((20, 20, 24))  # Base floor

    # Add toxic pools
    toxic_green = (40, 60, 20)
    toxic_bright = (50, 80, 25)
    for _ in range(3):
        x = random.randint(4, 28)
        y = random.randint(4, 28)
        radius = random.randint(3, 6)
        pg.draw.circle(toxic, toxic_green, (x, y), radius)
        pg.draw.circle(toxic, toxic_bright, (x-1, y-1), radius-1)

    # Add warning stripes
    stripe_color = (60, 50, 20)
    for i in range(0, 32, 8):
        pg.draw.line(toxic, stripe_color, (i, 0), (i+4, 4), 2)
        pg.draw.line(toxic, stripe_color, (i, 28), (i+4, 32), 2)

    hazards["toxic"] = toxic

    # Electric hazard tile
    electric = pg.Surface((32, 32), pg.SRCALPHA)
    electric.fill((25, 22, 28))  # Slightly different base

    # Add electrical panel
    panel_color = (40, 35, 45)
    pg.draw.rect(electric, panel_color, (8, 8, 16, 16))
    pg.draw.rect(electric, (15, 15, 20), (8, 8, 16, 16), 2)

    # Add spark effects (will be animated in-game)
    spark_points = [(12, 12), (20, 12), (12, 20), (20, 20)]
    for px, py in spark_points:
        pg.draw.circle(electric, (80, 80, 120), (px, py), 2)
        pg.draw.circle(electric, (100, 100, 150), (px, py), 1)

    # Warning markers
    for corner in [(2, 2), (30, 2), (2, 30), (30, 30)]:
        pg.draw.circle(electric, (80, 60, 20), corner, 2)

    hazards["electric"] = electric

    # Fire/heat hazard tile
    heat = pg.Surface((32, 32), pg.SRCALPHA)
    heat.fill((25, 20, 18))  # Warm base

    # Add grate with glow beneath
    for y in range(8, 24, 2):
        pg.draw.line(heat, (15, 12, 10), (8, y), (24, y), 1)
        pg.draw.line(heat, (60, 30, 20), (8, y+1), (24, y+1), 1)  # Glow

    # Heat distortion marks
    for _ in range(8):
        x = random.randint(8, 24)
        y = random.randint(8, 24)
        heat.set_at((x, y), (40, 20, 15))

    hazards["heat"] = heat

    return hazards

def create_animated_tile_frames():
    """Create frames for animated tiles"""
    animations = {}

    # Flickering light frames (4 frames)
    light_frames = []
    for brightness in [0.3, 0.6, 1.0, 0.7]:
        frame = pg.Surface((32, 32), pg.SRCALPHA)
        frame.fill((20, 20, 24))  # Base floor

        # Add light fixture
        fixture_color = (40, 40, 45)
        pg.draw.rect(frame, fixture_color, (12, 12, 8, 8))

        # Add light glow
        glow_radius = int(12 * brightness)
        glow_alpha = int(100 * brightness)
        if glow_radius > 0:
            for r in range(glow_radius, 0, -2):
                alpha = glow_alpha * (r / glow_radius)
                color = (180, 170, 140, int(alpha))
                pg.draw.circle(frame, color[:3], (16, 16), r)

        light_frames.append(frame)

    animations["flickering_light"] = light_frames

    # Steam vent frames (6 frames)
    steam_frames = []
    for i in range(6):
        frame = pg.Surface((32, 32), pg.SRCALPHA)
        frame.fill((20, 20, 24))  # Base floor

        # Add vent grate
        vent_color = (30, 30, 35)
        pg.draw.rect(frame, vent_color, (10, 10, 12, 12))
        for offset in range(11, 21, 2):
            pg.draw.line(frame, (15, 15, 18), (offset, 10), (offset, 22), 1)

        # Add animated steam particles
        steam_color = (60, 60, 65, 80)
        for j in range(3):
            phase = (i + j * 2) % 6
            y_offset = 10 - phase * 2
            x_wobble = int(math.sin(phase * 0.5) * 3)
            if y_offset > 0:
                for py in range(max(0, y_offset), min(y_offset + 8, 32)):
                    alpha = 80 - (py - y_offset) * 10
                    if alpha > 0 and 0 <= 16 + x_wobble < 32:
                        frame.set_at((16 + x_wobble, py),
                                   (60, 60, 65, min(80, alpha)))

        steam_frames.append(frame)

    animations["steam_vent"] = steam_frames

    # Sparking electrical panel (8 frames)
    spark_frames = []
    for i in range(8):
        frame = pg.Surface((32, 32), pg.SRCALPHA)
        frame.fill((25, 22, 28))

        # Base electrical panel
        panel_color = (40, 35, 45)
        pg.draw.rect(frame, panel_color, (8, 8, 16, 16))
        pg.draw.rect(frame, (15, 15, 20), (8, 8, 16, 16), 2)

        # Random sparks
        if i % 3 == 0:  # Spark on some frames
            spark_count = random.randint(2, 5)
            for _ in range(spark_count):
                x = random.randint(10, 22)
                y = random.randint(10, 22)
                spark_color = random.choice([
                    (150, 150, 200),
                    (120, 120, 180),
                    (200, 200, 255)
                ])
                pg.draw.circle(frame, spark_color, (x, y), 1)

                # Spark lines
                for _ in range(2):
                    angle = random.random() * math.pi * 2
                    length = random.randint(3, 6)
                    end_x = int(x + math.cos(angle) * length)
                    end_y = int(y + math.sin(angle) * length)
                    pg.draw.line(frame, spark_color, (x, y), (end_x, end_y), 1)

        spark_frames.append(frame)

    animations["electrical_panel"] = spark_frames

    return animations

def create_decal_overlays():
    """Create decal overlays (blood, shell casings, debris, etc.)"""
    decals = {}

    # Blood pool
    blood = pg.Surface((32, 32), pg.SRCALPHA)
    blood_color = (60, 10, 10, 180)
    # Irregular blood pool
    cx, cy = 16, 16
    for angle in range(0, 360, 15):
        rad = math.radians(angle)
        radius = random.randint(4, 10)
        for r in range(radius):
            x = int(cx + math.cos(rad) * r)
            y = int(cy + math.sin(rad) * r)
            if 0 <= x < 32 and 0 <= y < 32:
                alpha = 180 - r * 10
                blood.set_at((x, y), (60, 10, 10, alpha))

    # Add splatter
    for _ in range(5):
        x = cx + random.randint(-8, 8)
        y = cy + random.randint(-8, 8)
        if 0 <= x < 32 and 0 <= y < 32:
            pg.draw.circle(blood, blood_color[:3], (x, y), random.randint(1, 2))

    decals["blood_pool"] = blood

    # Shell casings
    casings = pg.Surface((32, 32), pg.SRCALPHA)
    casing_color = (120, 100, 60)
    for _ in range(random.randint(2, 4)):
        x = random.randint(4, 28)
        y = random.randint(4, 28)
        angle = random.random() * math.pi * 2

        # Draw casing as small rotated rectangle
        points = []
        for dx, dy in [(-3, -1), (3, -1), (3, 1), (-3, 1)]:
            rx = x + dx * math.cos(angle) - dy * math.sin(angle)
            ry = y + dx * math.sin(angle) + dy * math.cos(angle)
            points.append((rx, ry))

        pg.draw.polygon(casings, casing_color, points)
        # Highlight
        pg.draw.line(casings, (140, 120, 70), points[0], points[1], 1)

    decals["shell_casing"] = casings

    # Debris pile
    debris = pg.Surface((32, 32), pg.SRCALPHA)
    debris_colors = [(40, 38, 35), (35, 32, 30), (45, 40, 38)]
    for _ in range(8):
        x = random.randint(6, 26)
        y = random.randint(6, 26)
        size = random.randint(2, 4)
        color = random.choice(debris_colors)

        # Irregular debris shapes
        points = []
        for i in range(random.randint(3, 5)):
            angle = (i / 5) * math.pi * 2
            r = size * random.uniform(0.7, 1.3)
            px = int(x + math.cos(angle) * r)
            py = int(y + math.sin(angle) * r)
            points.append((px, py))

        if len(points) >= 3:
            pg.draw.polygon(debris, color, points)

    decals["debris"] = debris

    # Oil spill
    oil = pg.Surface((32, 32), pg.SRCALPHA)
    oil_color = (10, 8, 12, 160)
    # Create oil puddle
    cx, cy = 16, 16
    for angle in range(0, 360, 10):
        rad = math.radians(angle)
        radius = random.randint(6, 12)
        for r in range(radius):
            x = int(cx + math.cos(rad) * r * random.uniform(0.8, 1.2))
            y = int(cy + math.sin(rad) * r * random.uniform(0.8, 1.2))
            if 0 <= x < 32 and 0 <= y < 32:
                alpha = 160 - r * 8
                # Rainbow sheen effect
                if random.random() > 0.9:
                    oil.set_at((x, y), (20, 15, 25, alpha))
                else:
                    oil.set_at((x, y), (10, 8, 12, alpha))

    decals["oil_spill"] = oil

    # Scorch marks
    scorch = pg.Surface((32, 32), pg.SRCALPHA)
    scorch_color = (20, 15, 10, 140)
    cx, cy = random.randint(8, 24), random.randint(8, 24)

    # Blast pattern
    for angle in range(0, 360, 5):
        rad = math.radians(angle)
        length = random.randint(4, 10)
        for d in range(length):
            x = int(cx + math.cos(rad) * d)
            y = int(cy + math.sin(rad) * d)
            if 0 <= x < 32 and 0 <= y < 32:
                alpha = 140 - d * 10
                scorch.set_at((x, y), (20, 15, 10, alpha))

    decals["scorch_mark"] = scorch

    # Corpse outline (simplified)
    corpse = pg.Surface((32, 32), pg.SRCALPHA)
    # Simple body shape
    pg.draw.ellipse(corpse, (25, 20, 18, 120), (10, 8, 12, 18))  # Torso
    pg.draw.circle(corpse, (25, 20, 18, 120), (16, 6), 3)  # Head
    # Arms
    pg.draw.line(corpse, (25, 20, 18, 100), (12, 12), (6, 18), 2)
    pg.draw.line(corpse, (25, 20, 18, 100), (20, 12), (26, 18), 2)
    # Legs
    pg.draw.line(corpse, (25, 20, 18, 100), (14, 24), (12, 30), 2)
    pg.draw.line(corpse, (25, 20, 18, 100), (18, 24), (20, 30), 2)

    decals["corpse"] = corpse

    return decals

def save_tiles(tiles_dict, prefix):
    """Save individual tiles from a dictionary"""
    for name, tile in tiles_dict.items():
        filename = f"{prefix}_{name}.png"
        pg.image.save(tile, filename)
        print(f"✓ Created {filename}")

def save_animation_sheet(frames_dict, prefix):
    """Save animation frames as sprite sheets"""
    for name, frames in frames_dict.items():
        if frames:
            sheet_width = len(frames) * 32
            sheet = pg.Surface((sheet_width, 32), pg.SRCALPHA)
            for i, frame in enumerate(frames):
                sheet.blit(frame, (i * 32, 0))

            filename = f"{prefix}_{name}.png"
            pg.image.save(sheet, filename)
            print(f"✓ Created {filename} ({len(frames)} frames)")

def save_metadata(corners, hazards, animations, decals):
    """Save metadata about the tiles for game loading"""
    metadata = {
        "corners": list(corners.keys()),
        "hazards": list(hazards.keys()),
        "animations": {
            name: len(frames) for name, frames in animations.items()
        },
        "decals": list(decals.keys()),
        "tile_size": 32
    }

    with open("terrain_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    print("✓ Created terrain_metadata.json")

def main():
    pg.init()

    print("Generating advanced grim dark terrain tiles...")
    print("-" * 40)

    # Generate all tile types
    corners = create_corner_tiles()
    damaged = create_damaged_tiles()
    hazards = create_hazard_tiles()
    animations = create_animated_tile_frames()
    decals = create_decal_overlays()

    # Save corner tiles
    save_tiles(corners, "corner")

    # Save damaged tiles as a sheet
    if damaged:
        sheet = pg.Surface((len(damaged) * 32, 32), pg.SRCALPHA)
        for i, tile in enumerate(damaged):
            sheet.blit(tile, (i * 32, 0))
        pg.image.save(sheet, "terrain_damaged.png")
        print(f"✓ Created terrain_damaged.png ({len(damaged)} variants)")

    # Save hazard tiles
    save_tiles(hazards, "hazard")

    # Save animation sheets
    save_animation_sheet(animations, "anim")

    # Save decal overlays
    save_tiles(decals, "decal")

    # Save metadata
    save_metadata(corners, hazards, animations, decals)

    print("-" * 40)
    print("Advanced terrain generation complete!")
    print("\nGenerated:")
    print(f"  - {len(corners)} corner tiles")
    print(f"  - {len(damaged)} damaged wall variants")
    print(f"  - {len(hazards)} hazard floor types")
    print(f"  - {len(animations)} animated tile types")
    print(f"  - {len(decals)} decal overlays")

if __name__ == "__main__":
    main()