#!/usr/bin/env python3
"""
Generate interior prop sprites for Hive City Rampage:
- Computer stations with green displays
- Storage containers and crates
- Ammo crates and weapon racks
- Columns and pillars
- Generators and machinery
- Holotables
"""

import pygame as pg
import random
import math

# Vibrant color palette inspired by classic grimdark pixel art
COLORS = {
    'metal': (62, 65, 72),
    'metal_light': (95, 100, 115),
    'metal_dark': (40, 42, 48),
    'metal_darker': (28, 28, 35),

    # Vibrant green CRT screens
    'screen_bg': (8, 22, 12),
    'screen_green': (65, 215, 95),
    'screen_green_dim': (35, 125, 55),
    'screen_glow': (95, 255, 125),

    # Warmer, richer browns
    'crate_brown': (95, 65, 42),
    'crate_dark': (62, 42, 28),
    'crate_light': (125, 95, 65),

    # Rich blues (like space marine armor)
    'container_blue': (55, 75, 125),
    'container_dark': (35, 48, 85),

    # More saturated red
    'barrel_red': (145, 55, 35),
    'barrel_dark': (95, 35, 25),

    # Military olive green
    'ammo_green': (75, 95, 55),
    'ammo_dark': (48, 65, 35),

    # Brighter gold/amber
    'gold': (195, 165, 65),
    'gold_dark': (145, 115, 45),

    # Vibrant warning colors
    'warning': (215, 175, 45),
    'danger': (195, 65, 45),

    # Warmer stone
    'column_stone': (85, 78, 68),
    'column_dark': (55, 50, 45),
    'column_light': (115, 105, 95),

    # Glows
    'glow_blue': (95, 145, 215),
    'glow_orange': (215, 155, 65),
    'glow_amber': (235, 185, 85),
}


def create_computer_station(facing='n'):
    """Computer terminal with green CRT display"""
    tile = pg.Surface((32, 32), pg.SRCALPHA)

    # Base/desk
    if facing == 'n':
        pg.draw.rect(tile, COLORS['metal_dark'], (4, 18, 24, 14))
        pg.draw.rect(tile, COLORS['metal'], (4, 18, 24, 14), 1)
        # Monitor
        pg.draw.rect(tile, COLORS['metal_darker'], (6, 4, 20, 16))
        pg.draw.rect(tile, COLORS['metal'], (6, 4, 20, 16), 2)
        # Screen
        pg.draw.rect(tile, COLORS['screen_bg'], (8, 6, 16, 11))
        # Scanlines and text
        for y in range(7, 16, 2):
            width = random.randint(6, 14)
            pg.draw.line(tile, COLORS['screen_green_dim'], (9, y), (9 + width, y), 1)
        # Cursor blink
        pg.draw.rect(tile, COLORS['screen_green'], (20, 14, 2, 2))
        # Screen glow effect
        pg.draw.rect(tile, COLORS['screen_glow'], (10, 8, 8, 1))
        # Keyboard
        pg.draw.rect(tile, COLORS['metal_light'], (8, 22, 16, 6))
        for kx in range(9, 23, 2):
            for ky in range(23, 27, 2):
                pg.draw.rect(tile, COLORS['metal_dark'], (kx, ky, 1, 1))
    else:  # facing south
        pg.draw.rect(tile, COLORS['metal_dark'], (4, 0, 24, 14))
        pg.draw.rect(tile, COLORS['metal'], (4, 0, 24, 14), 1)
        # Monitor (back visible)
        pg.draw.rect(tile, COLORS['metal_darker'], (6, 12, 20, 16))
        pg.draw.rect(tile, COLORS['metal'], (6, 12, 20, 16), 2)
        # Vents on back
        for y in range(15, 26, 3):
            pg.draw.line(tile, COLORS['metal_dark'], (9, y), (23, y), 1)

    return tile


def create_holotable():
    """Central holographic display table"""
    tile = pg.Surface((32, 32), pg.SRCALPHA)

    # Circular base
    pg.draw.circle(tile, COLORS['metal_dark'], (16, 16), 14)
    pg.draw.circle(tile, COLORS['metal'], (16, 16), 14, 2)
    pg.draw.circle(tile, COLORS['metal_light'], (16, 16), 10)

    # Holographic projection (green glow)
    for r in range(8, 2, -1):
        alpha = 60 + (8 - r) * 20
        glow = pg.Surface((r*2, r*2), pg.SRCALPHA)
        pg.draw.circle(glow, (*COLORS['screen_green'], alpha), (r, r), r)
        tile.blit(glow, (16-r, 16-r))

    # Center emitter
    pg.draw.circle(tile, COLORS['screen_glow'], (16, 16), 3)
    pg.draw.circle(tile, (255, 255, 255), (16, 16), 1)

    # Control nodes around edge
    for angle in range(0, 360, 60):
        rad = math.radians(angle)
        x = int(16 + math.cos(rad) * 11)
        y = int(16 + math.sin(rad) * 11)
        pg.draw.circle(tile, COLORS['screen_green_dim'], (x, y), 2)

    return tile


def create_container():
    """Large storage container"""
    tile = pg.Surface((32, 32), pg.SRCALPHA)

    # Main body
    pg.draw.rect(tile, COLORS['container_dark'], (2, 4, 28, 24))
    pg.draw.rect(tile, COLORS['container_blue'], (2, 4, 28, 24), 2)

    # Top highlight
    pg.draw.rect(tile, COLORS['metal_light'], (2, 4, 28, 3))

    # Ribbing
    for x in [8, 16, 24]:
        pg.draw.line(tile, COLORS['container_dark'], (x, 4), (x, 28), 2)

    # Labels/markings
    pg.draw.rect(tile, COLORS['warning'], (10, 14, 12, 6))
    pg.draw.rect(tile, COLORS['metal_dark'], (10, 14, 12, 6), 1)

    # Lock
    pg.draw.circle(tile, COLORS['metal'], (26, 16), 3)
    pg.draw.circle(tile, COLORS['metal_dark'], (26, 16), 2)

    return tile


def create_crate():
    """Wooden/metal crate"""
    tile = pg.Surface((32, 32), pg.SRCALPHA)

    # Main body
    pg.draw.rect(tile, COLORS['crate_brown'], (4, 6, 24, 20))

    # Planks
    for y in [6, 13, 20]:
        pg.draw.rect(tile, COLORS['crate_dark'], (4, y, 24, 2))
    for x in [4, 15, 26]:
        pg.draw.line(tile, COLORS['crate_dark'], (x, 6), (x, 26), 2)

    # Metal corners
    for corner in [(4, 6), (26, 6), (4, 24), (26, 24)]:
        pg.draw.rect(tile, COLORS['metal'], (corner[0]-1, corner[1]-1, 4, 4))
        pg.draw.circle(tile, COLORS['metal_light'], corner, 1)

    # Top highlight
    pg.draw.line(tile, COLORS['crate_light'], (5, 7), (27, 7), 1)

    return tile


def create_barrel():
    """Industrial barrel"""
    tile = pg.Surface((32, 32), pg.SRCALPHA)

    # Main body (oval)
    pg.draw.ellipse(tile, COLORS['barrel_red'], (6, 4, 20, 24))
    pg.draw.ellipse(tile, COLORS['barrel_dark'], (6, 4, 20, 24), 2)

    # Metal bands
    for y in [8, 16, 22]:
        pg.draw.ellipse(tile, COLORS['metal'], (7, y-1, 18, 4), 2)

    # Hazard symbol
    pg.draw.polygon(tile, COLORS['warning'], [(16, 10), (12, 17), (20, 17)])
    pg.draw.polygon(tile, COLORS['barrel_dark'], [(16, 12), (14, 16), (18, 16)])

    # Lid
    pg.draw.ellipse(tile, COLORS['metal_light'], (9, 3, 14, 5))

    return tile


def create_ammo_crate():
    """Military ammo crate"""
    tile = pg.Surface((32, 32), pg.SRCALPHA)

    # Main body
    pg.draw.rect(tile, COLORS['ammo_green'], (3, 8, 26, 18))
    pg.draw.rect(tile, COLORS['ammo_dark'], (3, 8, 26, 18), 2)

    # Lid
    pg.draw.rect(tile, COLORS['ammo_green'], (2, 6, 28, 4))
    pg.draw.rect(tile, COLORS['metal'], (2, 6, 28, 4), 1)

    # Handle
    pg.draw.rect(tile, COLORS['metal'], (12, 4, 8, 3))
    pg.draw.rect(tile, COLORS['metal_dark'], (14, 5, 4, 2))

    # Markings
    pg.draw.rect(tile, COLORS['warning'], (6, 12, 8, 10))
    # Aquila symbol simplified
    pg.draw.polygon(tile, COLORS['gold'], [(10, 14), (7, 19), (13, 19)])

    # Latches
    for x in [6, 24]:
        pg.draw.rect(tile, COLORS['metal'], (x-1, 8, 3, 4))

    return tile


def create_weapon_rack():
    """Wall-mounted weapon rack"""
    tile = pg.Surface((32, 32), pg.SRCALPHA)

    # Back panel
    pg.draw.rect(tile, COLORS['metal_dark'], (2, 2, 28, 28))
    pg.draw.rect(tile, COLORS['metal'], (2, 2, 28, 28), 2)

    # Weapon slots (simplified weapons)
    for i, y in enumerate([7, 15, 23]):
        # Slot
        pg.draw.rect(tile, COLORS['metal_darker'], (4, y-1, 24, 4))
        # Weapon silhouette
        if i < 2:  # Rifles
            pg.draw.rect(tile, COLORS['metal_light'], (6, y, 18, 2))
            pg.draw.rect(tile, COLORS['metal'], (22, y-1, 4, 4))
        else:  # Pistol
            pg.draw.rect(tile, COLORS['metal_light'], (10, y, 10, 2))
            pg.draw.rect(tile, COLORS['metal'], (8, y, 4, 3))

    # Imperial eagle at top
    pg.draw.polygon(tile, COLORS['gold'], [(16, 3), (12, 5), (20, 5)])

    return tile


def create_column():
    """Structural column/pillar"""
    tile = pg.Surface((32, 32), pg.SRCALPHA)

    # Main pillar
    pg.draw.rect(tile, COLORS['column_stone'], (8, 2, 16, 28))

    # Base
    pg.draw.rect(tile, COLORS['column_dark'], (6, 26, 20, 6))
    pg.draw.rect(tile, COLORS['column_light'], (6, 26, 20, 2))

    # Capital (top)
    pg.draw.rect(tile, COLORS['column_dark'], (6, 0, 20, 6))
    pg.draw.rect(tile, COLORS['column_light'], (6, 4, 20, 2))

    # Fluting (vertical grooves)
    for x in [10, 14, 18, 22]:
        pg.draw.line(tile, COLORS['column_dark'], (x, 6), (x, 26), 1)
        pg.draw.line(tile, COLORS['column_light'], (x+1, 6), (x+1, 26), 1)

    # Skull decoration
    pg.draw.circle(tile, COLORS['column_light'], (16, 14), 4)
    pg.draw.circle(tile, COLORS['column_dark'], (14, 13), 1)
    pg.draw.circle(tile, COLORS['column_dark'], (18, 13), 1)

    return tile


def create_generator():
    """Power generator/machinery"""
    tile = pg.Surface((32, 32), pg.SRCALPHA)

    # Main body
    pg.draw.rect(tile, COLORS['metal_dark'], (4, 4, 24, 24))
    pg.draw.rect(tile, COLORS['metal'], (4, 4, 24, 24), 2)

    # Cooling fins
    for y in range(6, 26, 4):
        pg.draw.rect(tile, COLORS['metal_darker'], (2, y, 4, 2))
        pg.draw.rect(tile, COLORS['metal_darker'], (26, y, 4, 2))

    # Power core (glowing)
    pg.draw.circle(tile, COLORS['glow_orange'], (16, 16), 8)
    pg.draw.circle(tile, COLORS['warning'], (16, 16), 6)
    pg.draw.circle(tile, (255, 200, 100), (16, 16), 3)

    # Control panel
    pg.draw.rect(tile, COLORS['metal'], (8, 24, 16, 4))
    pg.draw.circle(tile, COLORS['screen_green'], (12, 26), 2)
    pg.draw.circle(tile, COLORS['danger'], (20, 26), 2)

    # Pipes
    pg.draw.rect(tile, COLORS['metal'], (2, 14, 4, 4))
    pg.draw.rect(tile, COLORS['metal'], (26, 14, 4, 4))

    return tile


def create_light_post():
    """Corridor light post"""
    tile = pg.Surface((32, 32), pg.SRCALPHA)

    # Post
    pg.draw.rect(tile, COLORS['metal_dark'], (14, 8, 4, 20))
    pg.draw.rect(tile, COLORS['metal'], (14, 8, 4, 20), 1)

    # Light fixture
    pg.draw.rect(tile, COLORS['metal'], (10, 4, 12, 6))

    # Light glow
    for r in range(8, 3, -1):
        alpha = 40 + (8 - r) * 15
        glow = pg.Surface((r*2, r*2), pg.SRCALPHA)
        pg.draw.circle(glow, (*COLORS['glow_blue'], alpha), (r, r), r)
        tile.blit(glow, (16-r, 8-r))

    pg.draw.rect(tile, (200, 220, 255), (12, 6, 8, 2))

    # Base
    pg.draw.rect(tile, COLORS['metal'], (12, 26, 8, 4))

    return tile


def create_pipe_vertical():
    """Vertical pipe section"""
    tile = pg.Surface((32, 32), pg.SRCALPHA)

    # Main pipe
    pg.draw.rect(tile, COLORS['metal_dark'], (12, 0, 8, 32))
    pg.draw.line(tile, COLORS['metal_light'], (12, 0), (12, 32), 1)
    pg.draw.line(tile, COLORS['metal_darker'], (19, 0), (19, 32), 1)

    # Joints
    for y in [8, 24]:
        pg.draw.rect(tile, COLORS['metal'], (10, y-2, 12, 4))
        pg.draw.ellipse(tile, COLORS['metal_light'], (11, y-1, 10, 2))

    # Valve
    pg.draw.circle(tile, COLORS['danger'], (16, 16), 4)
    pg.draw.circle(tile, COLORS['metal'], (16, 16), 2)
    pg.draw.line(tile, COLORS['metal_light'], (12, 16), (20, 16), 2)

    return tile


def create_small_crate():
    """Small supply crate"""
    tile = pg.Surface((32, 32), pg.SRCALPHA)

    # Main body
    pg.draw.rect(tile, COLORS['crate_brown'], (8, 12, 16, 14))
    pg.draw.rect(tile, COLORS['crate_dark'], (8, 12, 16, 14), 1)

    # Lid
    pg.draw.rect(tile, COLORS['crate_light'], (7, 10, 18, 4))
    pg.draw.rect(tile, COLORS['crate_dark'], (7, 10, 18, 4), 1)

    # Straps
    pg.draw.line(tile, COLORS['metal'], (12, 10), (12, 26), 2)
    pg.draw.line(tile, COLORS['metal'], (20, 10), (20, 26), 2)

    return tile


def main():
    pg.init()
    random.seed(42)

    print("Generating prop sprites...")
    print("-" * 40)

    props = {
        'computer_n': create_computer_station('n'),
        'computer_s': create_computer_station('s'),
        'holotable': create_holotable(),
        'container': create_container(),
        'crate': create_crate(),
        'barrel': create_barrel(),
        'ammo_crate': create_ammo_crate(),
        'weapon_rack': create_weapon_rack(),
        'column': create_column(),
        'generator': create_generator(),
        'light_post': create_light_post(),
        'pipe_vertical': create_pipe_vertical(),
        'small_crate': create_small_crate(),
    }

    # Save individual props
    for name, surf in props.items():
        filename = f"prop_{name}.png"
        pg.image.save(surf, filename)
        print(f"Created {filename}")

    # Create sprite sheet
    sheet_width = len(props) * 32
    sheet = pg.Surface((sheet_width, 32), pg.SRCALPHA)
    prop_order = list(props.keys())
    for i, name in enumerate(prop_order):
        sheet.blit(props[name], (i * 32, 0))

    pg.image.save(sheet, "props_sheet.png")
    print(f"\nCreated props_sheet.png ({len(props)} props)")

    # Save prop order for loading
    print("\nProp order in sheet:")
    for i, name in enumerate(prop_order):
        print(f"  {i}: {name}")

    print("-" * 40)
    print("Prop generation complete!")


if __name__ == "__main__":
    main()
