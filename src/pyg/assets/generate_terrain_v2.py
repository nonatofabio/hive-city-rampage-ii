#!/usr/bin/env python3
"""
Generate grim dark terrain sprites with:
- Edge-aware wall tiles (interior vs edges)
- Smooth rounded corners using 8-neighbor detection
- Higher contrast colors
- Wall elements (computers, pipes, panels)
- Autotile sheet for runtime neighbor-based selection
"""

import pygame as pg
import random
import math

# Vibrant color palette inspired by classic grimdark pixel art
COLORS = {
    # Interior (surrounded by walls) - deep dark with hint of brown
    'interior': (18, 15, 12),
    'interior_detail': (28, 24, 20),

    # Wall edges - warmer stone/metal tones
    'wall_base': (58, 52, 48),
    'wall_dark': (42, 38, 35),
    'wall_light': (75, 68, 62),
    'wall_highlight': (95, 88, 78),

    # Metal details - blue-gray tint
    'metal': (62, 65, 72),
    'metal_light': (85, 90, 100),
    'metal_dark': (40, 42, 48),
    'rivet': (72, 75, 82),
    'rivet_light': (105, 110, 120),

    # Floor - warmer dark tones
    'floor_base': (28, 24, 22),
    'floor_dark': (18, 15, 14),
    'floor_light': (42, 38, 35),
    'floor_grate': (22, 18, 16),

    # Accent colors - more saturated
    'rust': (120, 65, 35),
    'rust_dark': (85, 45, 25),
    'grime': (35, 28, 22),
    'warning': (185, 145, 45),
    'blood': (140, 25, 25),

    # Tech/glow - vibrant
    'tech_green': (65, 185, 85),
    'tech_blue': (65, 95, 165),
    'tech_red': (165, 55, 45),
    'glow': (185, 165, 95),

    # New warm accent colors
    'amber': (195, 145, 55),
    'amber_dark': (145, 95, 35),
    'window_glow': (215, 165, 75),
}

def create_interior_tile():
    """Create dark interior tile (wall surrounded by walls)"""
    tile = pg.Surface((32, 32), pg.SRCALPHA)
    tile.fill(COLORS['interior'])

    # Subtle texture
    for _ in range(15):
        x, y = random.randint(0, 31), random.randint(0, 31)
        tile.set_at((x, y), COLORS['interior_detail'])

    return tile


def create_edge_wall_tile(edge_mask):
    """
    Create wall edge tile based on which sides touch floor.
    edge_mask bits: N=1, E=2, S=4, W=8
    """
    tile = pg.Surface((32, 32), pg.SRCALPHA)
    tile.fill(COLORS['wall_base'])

    n = edge_mask & 1
    e = edge_mask & 2
    s = edge_mask & 4
    w = edge_mask & 8

    # Add panel lines
    pg.draw.line(tile, COLORS['wall_dark'], (0, 10), (32, 10), 2)
    pg.draw.line(tile, COLORS['wall_dark'], (0, 22), (32, 22), 2)
    pg.draw.line(tile, COLORS['wall_dark'], (16, 0), (16, 32), 1)

    # Add rivets
    for rx, ry in [(6, 6), (26, 6), (6, 26), (26, 26), (16, 16)]:
        pg.draw.circle(tile, COLORS['metal_dark'], (rx+1, ry+1), 2)
        pg.draw.circle(tile, COLORS['rivet'], (rx, ry), 2)
        pg.draw.circle(tile, COLORS['rivet_light'], (rx-1, ry-1), 1)

    # Edge highlights/shadows based on which sides are exposed
    if n:  # North edge (floor above)
        pg.draw.line(tile, COLORS['wall_highlight'], (0, 0), (31, 0), 2)
        pg.draw.line(tile, COLORS['wall_light'], (0, 2), (31, 2), 1)
    if s:  # South edge (floor below)
        pg.draw.line(tile, COLORS['metal_dark'], (0, 30), (31, 30), 2)
        pg.draw.line(tile, COLORS['wall_dark'], (0, 31), (31, 31), 1)
    if w:  # West edge (floor left)
        pg.draw.line(tile, COLORS['wall_highlight'], (0, 0), (0, 31), 2)
        pg.draw.line(tile, COLORS['wall_light'], (2, 0), (2, 31), 1)
    if e:  # East edge (floor right)
        pg.draw.line(tile, COLORS['metal_dark'], (30, 0), (30, 31), 2)
        pg.draw.line(tile, COLORS['wall_dark'], (31, 0), (31, 31), 1)

    # Add wear
    for _ in range(12):
        x, y = random.randint(2, 29), random.randint(2, 29)
        c = random.choice([COLORS['rust'], COLORS['grime'], COLORS['wall_light']])
        tile.set_at((x, y), c)

    return tile


def create_corner_tile(corner_type, rounded=True):
    """
    Create corner tiles for smooth transitions.
    corner_type: 'outer_nw', 'outer_ne', 'outer_sw', 'outer_se',
                 'inner_nw', 'inner_ne', 'inner_sw', 'inner_se'
    """
    tile = pg.Surface((32, 32), pg.SRCALPHA)

    is_outer = 'outer' in corner_type

    if is_outer:
        # Outer corner: wall wraps around floor
        tile.fill(COLORS['wall_base'])

        # Cut out the floor corner
        floor_rect = None
        if 'nw' in corner_type:
            floor_rect = (0, 0, 16, 16)
            if rounded:
                pg.draw.circle(tile, COLORS['floor_base'], (16, 16), 16)
            else:
                pg.draw.rect(tile, COLORS['floor_base'], floor_rect)
        elif 'ne' in corner_type:
            floor_rect = (16, 0, 16, 16)
            if rounded:
                pg.draw.circle(tile, COLORS['floor_base'], (16, 16), 16)
            else:
                pg.draw.rect(tile, COLORS['floor_base'], floor_rect)
        elif 'sw' in corner_type:
            floor_rect = (0, 16, 16, 16)
            if rounded:
                pg.draw.circle(tile, COLORS['floor_base'], (16, 16), 16)
            else:
                pg.draw.rect(tile, COLORS['floor_base'], floor_rect)
        elif 'se' in corner_type:
            floor_rect = (16, 16, 16, 16)
            if rounded:
                pg.draw.circle(tile, COLORS['floor_base'], (16, 16), 16)
            else:
                pg.draw.rect(tile, COLORS['floor_base'], floor_rect)

        # Add edge highlight on the curved edge
        if rounded:
            # Draw arc highlight
            for angle in range(0, 91, 5):
                rad = math.radians(angle)
                if 'nw' in corner_type:
                    x = int(16 + math.cos(rad + math.pi) * 15)
                    y = int(16 + math.sin(rad + math.pi) * 15)
                elif 'ne' in corner_type:
                    x = int(16 + math.cos(-rad - math.pi/2) * 15)
                    y = int(16 + math.sin(-rad - math.pi/2) * 15)
                elif 'sw' in corner_type:
                    x = int(16 + math.cos(rad + math.pi/2) * 15)
                    y = int(16 + math.sin(rad + math.pi/2) * 15)
                elif 'se' in corner_type:
                    x = int(16 + math.cos(-rad) * 15)
                    y = int(16 + math.sin(-rad) * 15)
                if 0 <= x < 32 and 0 <= y < 32:
                    tile.set_at((x, y), COLORS['wall_highlight'])
    else:
        # Inner corner: floor wraps into wall corner
        tile.fill(COLORS['floor_base'])

        # Add wall corner
        if 'nw' in corner_type:
            if rounded:
                pg.draw.circle(tile, COLORS['wall_base'], (0, 0), 14)
            else:
                pg.draw.rect(tile, COLORS['wall_base'], (0, 0, 14, 14))
        elif 'ne' in corner_type:
            if rounded:
                pg.draw.circle(tile, COLORS['wall_base'], (32, 0), 14)
            else:
                pg.draw.rect(tile, COLORS['wall_base'], (18, 0, 14, 14))
        elif 'sw' in corner_type:
            if rounded:
                pg.draw.circle(tile, COLORS['wall_base'], (0, 32), 14)
            else:
                pg.draw.rect(tile, COLORS['wall_base'], (0, 18, 14, 14))
        elif 'se' in corner_type:
            if rounded:
                pg.draw.circle(tile, COLORS['wall_base'], (32, 32), 14)
            else:
                pg.draw.rect(tile, COLORS['wall_base'], (18, 18, 14, 14))

        # Add floor grate pattern to visible floor area
        add_floor_grate(tile)

    return tile


def add_floor_grate(tile):
    """Add floor grating pattern"""
    for y in range(0, 32, 4):
        for x in range(0, 32):
            px = tile.get_at((x, y))
            if px[:3] == COLORS['floor_base']:
                tile.set_at((x, y), COLORS['floor_grate'])
    for x in range(0, 32, 8):
        for y in range(0, 32):
            px = tile.get_at((x, y))
            if px[:3] == COLORS['floor_base']:
                tile.set_at((x, y), COLORS['floor_grate'])


def create_floor_tile(variant=0):
    """Create floor tile with high contrast grating"""
    tile = pg.Surface((32, 32), pg.SRCALPHA)
    tile.fill(COLORS['floor_base'])

    # Metal grating pattern
    for y in range(0, 32, 4):
        pg.draw.line(tile, COLORS['floor_grate'], (0, y), (32, y), 1)
        if y > 0:
            pg.draw.line(tile, COLORS['floor_light'], (0, y+1), (32, y+1), 1)

    for x in range(0, 32, 8):
        pg.draw.line(tile, COLORS['floor_grate'], (x, 0), (x, 32), 1)

    # Add detail based on variant
    if variant % 3 == 1:
        # Oil stains
        for _ in range(2):
            x, y = random.randint(4, 28), random.randint(4, 28)
            for dx in range(-3, 4):
                for dy in range(-3, 4):
                    if dx*dx + dy*dy < 10 and 0 <= x+dx < 32 and 0 <= y+dy < 32:
                        tile.set_at((x+dx, y+dy), COLORS['grime'])

    if variant % 3 == 2:
        # Scratches
        for _ in range(4):
            x1, y1 = random.randint(0, 31), random.randint(0, 31)
            x2 = x1 + random.randint(-6, 6)
            y2 = y1 + random.randint(-6, 6)
            pg.draw.line(tile, COLORS['floor_light'], (x1, y1),
                        (max(0,min(31,x2)), max(0,min(31,y2))), 1)

    # Random wear
    for _ in range(8):
        x, y = random.randint(0, 31), random.randint(0, 31)
        tile.set_at((x, y), random.choice([COLORS['floor_light'], COLORS['floor_dark']]))

    return tile


def create_wall_element(element_type):
    """Create wall decoration elements"""
    tile = pg.Surface((32, 32), pg.SRCALPHA)
    tile.fill(COLORS['wall_base'])

    # Base wall texture
    pg.draw.line(tile, COLORS['wall_dark'], (0, 10), (32, 10), 1)
    pg.draw.line(tile, COLORS['wall_dark'], (0, 22), (32, 22), 1)

    if element_type == 'computer':
        # Computer terminal
        pg.draw.rect(tile, COLORS['metal_dark'], (6, 6, 20, 20))
        pg.draw.rect(tile, COLORS['metal'], (6, 6, 20, 20), 2)
        # Screen
        pg.draw.rect(tile, (8, 15, 12), (8, 8, 16, 12))
        # Screen content (scanlines)
        for y in range(9, 19, 2):
            pg.draw.line(tile, COLORS['tech_green'], (9, y), (22, y), 1)
        # Buttons
        pg.draw.circle(tile, COLORS['tech_red'], (11, 23), 2)
        pg.draw.circle(tile, COLORS['tech_green'], (16, 23), 2)
        pg.draw.circle(tile, COLORS['tech_blue'], (21, 23), 2)

    elif element_type == 'pipes_h':
        # Horizontal pipes
        for py in [8, 16, 24]:
            pg.draw.rect(tile, COLORS['metal_dark'], (0, py-2, 32, 4))
            pg.draw.line(tile, COLORS['metal_light'], (0, py-2), (32, py-2), 1)
            pg.draw.line(tile, COLORS['metal_dark'], (0, py+1), (32, py+1), 1)
        # Joints
        for px in [8, 24]:
            pg.draw.circle(tile, COLORS['metal'], (px, 16), 4)
            pg.draw.circle(tile, COLORS['rivet'], (px, 16), 2)

    elif element_type == 'pipes_v':
        # Vertical pipes
        for px in [8, 16, 24]:
            pg.draw.rect(tile, COLORS['metal_dark'], (px-2, 0, 4, 32))
            pg.draw.line(tile, COLORS['metal_light'], (px-2, 0), (px-2, 32), 1)
            pg.draw.line(tile, COLORS['metal_dark'], (px+1, 0), (px+1, 32), 1)
        # Valve
        pg.draw.circle(tile, COLORS['rust'], (16, 16), 5)
        pg.draw.circle(tile, COLORS['metal'], (16, 16), 3)

    elif element_type == 'vent':
        # Ventilation grate
        pg.draw.rect(tile, COLORS['metal_dark'], (4, 4, 24, 24))
        pg.draw.rect(tile, COLORS['metal'], (4, 4, 24, 24), 2)
        # Slats
        for y in range(7, 26, 3):
            pg.draw.line(tile, (5, 5, 8), (6, y), (26, y), 2)
            pg.draw.line(tile, COLORS['metal_dark'], (6, y+1), (26, y+1), 1)
        # Corner rivets
        for rx, ry in [(6, 6), (26, 6), (6, 26), (26, 26)]:
            pg.draw.circle(tile, COLORS['rivet'], (rx, ry), 2)

    elif element_type == 'panel':
        # Control panel
        pg.draw.rect(tile, COLORS['metal'], (4, 4, 24, 24))
        pg.draw.rect(tile, COLORS['metal_dark'], (4, 4, 24, 24), 2)
        # Buttons and lights
        for i, color in enumerate([COLORS['tech_red'], COLORS['tech_green'],
                                   COLORS['warning'], COLORS['tech_blue']]):
            x = 8 + (i % 2) * 10
            y = 8 + (i // 2) * 10
            pg.draw.rect(tile, color, (x, y, 6, 6))
            pg.draw.rect(tile, COLORS['metal_dark'], (x, y, 6, 6), 1)
        # Label plate
        pg.draw.rect(tile, COLORS['metal_light'], (8, 22, 16, 4))

    elif element_type == 'skull':
        # Imperial skull decoration
        # Skull
        pg.draw.circle(tile, COLORS['metal_light'], (16, 12), 7)
        pg.draw.circle(tile, COLORS['metal_light'], (16, 16), 5)
        # Eye sockets
        pg.draw.circle(tile, COLORS['interior'], (13, 11), 2)
        pg.draw.circle(tile, COLORS['interior'], (19, 11), 2)
        # Nose
        pg.draw.polygon(tile, COLORS['interior'], [(16, 13), (14, 16), (18, 16)])
        # Teeth
        for tx in range(13, 20, 2):
            pg.draw.rect(tile, COLORS['metal_light'], (tx, 18, 1, 3))
        # Wings/laurels
        pg.draw.arc(tile, COLORS['metal'], (2, 8, 10, 16), 0.5, 2.5, 2)
        pg.draw.arc(tile, COLORS['metal'], (20, 8, 10, 16), 0.6, 2.6, 2)

    elif element_type == 'warning':
        # Warning stripes
        for i in range(0, 32, 8):
            pg.draw.polygon(tile, COLORS['warning'],
                          [(i, 32), (i+8, 32), (i+12, 24), (i+4, 24)])
            pg.draw.polygon(tile, COLORS['interior'],
                          [(i+4, 32), (i+8, 32), (i+8, 28), (i+4, 28)])
        # Hazard symbol
        pg.draw.polygon(tile, COLORS['warning'], [(16, 4), (8, 18), (24, 18)])
        pg.draw.polygon(tile, COLORS['interior'], [(16, 8), (11, 16), (21, 16)])
        pg.draw.circle(tile, COLORS['warning'], (16, 13), 2)

    elif element_type == 'aquila':
        # Double-headed eagle
        # Body
        pg.draw.ellipse(tile, COLORS['metal'], (10, 12, 12, 10))
        # Heads
        pg.draw.circle(tile, COLORS['metal'], (8, 10), 4)
        pg.draw.circle(tile, COLORS['metal'], (24, 10), 4)
        # Beaks
        pg.draw.polygon(tile, COLORS['warning'], [(4, 10), (8, 8), (8, 12)])
        pg.draw.polygon(tile, COLORS['warning'], [(28, 10), (24, 8), (24, 12)])
        # Wings
        pg.draw.polygon(tile, COLORS['metal_light'],
                       [(6, 14), (2, 24), (12, 18)])
        pg.draw.polygon(tile, COLORS['metal_light'],
                       [(26, 14), (30, 24), (20, 18)])

    return tile


def create_autotile_sheet():
    """
    Create a complete autotile sheet using 4-bit neighbor mask.
    Index = N*1 + E*2 + S*4 + W*8
    16 tiles total for cardinal directions.
    """
    sheet = pg.Surface((32 * 16, 32), pg.SRCALPHA)

    for mask in range(16):
        tile = create_edge_wall_tile(mask)
        sheet.blit(tile, (mask * 32, 0))

    return sheet


def create_8bit_corner_sheet():
    """
    Create corner tiles for diagonal neighbors.
    Used when cardinal neighbors are walls but diagonal is floor.
    """
    sheet = pg.Surface((32 * 4, 32), pg.SRCALPHA)

    corners = ['outer_nw', 'outer_ne', 'outer_sw', 'outer_se']
    for i, corner in enumerate(corners):
        tile = create_corner_tile(corner, rounded=True)
        sheet.blit(tile, (i * 32, 0))

    return sheet


def create_inner_corner_sheet():
    """Inner corners for when floor wraps into wall"""
    sheet = pg.Surface((32 * 4, 32), pg.SRCALPHA)

    corners = ['inner_nw', 'inner_ne', 'inner_sw', 'inner_se']
    for i, corner in enumerate(corners):
        tile = create_corner_tile(corner, rounded=True)
        sheet.blit(tile, (i * 32, 0))

    return sheet


def main():
    pg.init()
    random.seed(42)  # Consistent generation

    print("Generating improved grim dark terrain v2...")
    print("-" * 50)

    # Interior tile (surrounded by walls)
    interior = create_interior_tile()
    pg.image.save(interior, "terrain_interior.png")
    print("Created terrain_interior.png (dark interior)")

    # Autotile sheet (16 edge configurations)
    autotile = create_autotile_sheet()
    pg.image.save(autotile, "terrain_autotile.png")
    print("Created terrain_autotile.png (16 edge configs)")

    # Outer corner sheet (rounded)
    outer_corners = create_8bit_corner_sheet()
    pg.image.save(outer_corners, "terrain_corners_outer.png")
    print("Created terrain_corners_outer.png (4 rounded outer corners)")

    # Inner corner sheet (rounded)
    inner_corners = create_inner_corner_sheet()
    pg.image.save(inner_corners, "terrain_corners_inner.png")
    print("Created terrain_corners_inner.png (4 rounded inner corners)")

    # Floor variants
    floor_sheet = pg.Surface((32 * 8, 32), pg.SRCALPHA)
    for i in range(8):
        floor = create_floor_tile(variant=i)
        floor_sheet.blit(floor, (i * 32, 0))
    pg.image.save(floor_sheet, "terrain_floors_v2.png")
    print("Created terrain_floors_v2.png (8 floor variants)")

    # Wall elements
    elements = ['computer', 'pipes_h', 'pipes_v', 'vent', 'panel', 'skull', 'warning', 'aquila']
    elements_sheet = pg.Surface((32 * len(elements), 32), pg.SRCALPHA)
    for i, elem in enumerate(elements):
        tile = create_wall_element(elem)
        elements_sheet.blit(tile, (i * 32, 0))
    pg.image.save(elements_sheet, "terrain_wall_elements.png")
    print(f"Created terrain_wall_elements.png ({len(elements)} elements)")

    print("-" * 50)
    print("Terrain v2 generation complete!")
    print("\nFiles created:")
    print("  - terrain_interior.png     : Dark tile for wall interiors")
    print("  - terrain_autotile.png     : 16 edge configurations (4-bit)")
    print("  - terrain_corners_outer.png: 4 rounded outer corners")
    print("  - terrain_corners_inner.png: 4 rounded inner corners")
    print("  - terrain_floors_v2.png    : 8 floor variants")
    print("  - terrain_wall_elements.png: Decorative wall elements")


if __name__ == "__main__":
    main()
