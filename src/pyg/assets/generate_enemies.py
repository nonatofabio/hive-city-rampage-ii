#!/usr/bin/env python3
"""
Generate enemy sprites for Hive City Rampage.
Creates 4-frame idle animations for each enemy type in the genestealer style.
"""

import pygame as pg
import math
import random

# Sprite dimensions
SPR = 48
FRAMES = 4

# Genestealer color palette (purple/magenta alien creatures)
COLORS = {
    # Carapace (outer shell)
    'carapace': (95, 45, 115),
    'carapace_light': (135, 65, 155),
    'carapace_dark': (55, 25, 75),
    'carapace_highlight': (175, 95, 195),

    # Flesh (inner body)
    'flesh': (145, 95, 115),
    'flesh_light': (175, 125, 145),
    'flesh_dark': (95, 55, 75),

    # Claws and teeth
    'claw': (215, 195, 175),
    'claw_dark': (165, 145, 125),
    'claw_tip': (245, 235, 225),

    # Eyes (menacing yellow/green)
    'eye': (195, 215, 45),
    'eye_glow': (235, 255, 95),
    'eye_dark': (125, 145, 25),

    # Brute armor plates
    'armor': (75, 65, 85),
    'armor_light': (105, 95, 115),
    'armor_edge': (135, 125, 145),

    # Shooter bio-weapon
    'bio_gun': (115, 75, 95),
    'bio_gun_dark': (75, 45, 65),
    'bio_glow': (165, 215, 95),

    # Runner stripes
    'stripe': (175, 85, 195),
}


def draw_genestealer_body(surf, cx, cy, scale=1.0, bob=0, lean=0):
    """Draw the main hunched genestealer body."""
    s = scale

    # Torso (hunched forward)
    torso_pts = [
        (cx - 8*s + lean, cy - 4*s + bob),
        (cx + 6*s + lean, cy - 8*s + bob),
        (cx + 10*s + lean, cy + 2*s + bob),
        (cx + 4*s + lean, cy + 10*s + bob),
        (cx - 10*s + lean, cy + 8*s + bob),
    ]
    pg.draw.polygon(surf, COLORS['carapace'], torso_pts)
    pg.draw.polygon(surf, COLORS['carapace_dark'], torso_pts, 2)

    # Carapace ridge highlight
    ridge_pts = [
        (cx - 4*s + lean, cy - 2*s + bob),
        (cx + 4*s + lean, cy - 6*s + bob),
        (cx + 6*s + lean, cy - 4*s + bob),
        (cx - 2*s + lean, cy + bob),
    ]
    pg.draw.polygon(surf, COLORS['carapace_light'], ridge_pts)

    return torso_pts


def draw_genestealer_head(surf, cx, cy, scale=1.0, bob=0, lean=0, frame=0):
    """Draw the elongated alien head."""
    s = scale
    hx = cx + 8*s + lean
    hy = cy - 10*s + bob

    # Elongated skull
    head_pts = [
        (hx - 4*s, hy + 2*s),
        (hx + 2*s, hy - 6*s),
        (hx + 10*s, hy - 4*s),
        (hx + 12*s, hy + 2*s),
        (hx + 6*s, hy + 6*s),
        (hx - 2*s, hy + 4*s),
    ]
    pg.draw.polygon(surf, COLORS['carapace'], head_pts)
    pg.draw.polygon(surf, COLORS['carapace_dark'], head_pts, 1)

    # Head crest
    crest_pts = [
        (hx + 2*s, hy - 4*s),
        (hx + 6*s, hy - 8*s),
        (hx + 10*s, hy - 6*s),
        (hx + 8*s, hy - 2*s),
    ]
    pg.draw.polygon(surf, COLORS['carapace_light'], crest_pts)

    # Eyes (pulsing)
    eye_bright = 1.0 + 0.2 * math.sin(frame * math.pi / 2)
    eye_color = tuple(min(255, int(c * eye_bright)) for c in COLORS['eye'])
    pg.draw.ellipse(surf, COLORS['eye_dark'], (hx + 1*s, hy - 1*s, 4*s, 3*s))
    pg.draw.ellipse(surf, eye_color, (hx + 2*s, hy, 3*s, 2*s))

    # Teeth/mandibles
    for i in range(3):
        tx = hx + 8*s + i*2*s
        ty = hy + 4*s
        pg.draw.line(surf, COLORS['claw'], (tx, ty), (tx + s, ty + 3*s), max(1, int(s)))


def draw_genestealer_arms(surf, cx, cy, scale=1.0, bob=0, lean=0, frame=0):
    """Draw the four arms with claws (genestealers have 4 arms)."""
    s = scale

    # Animation: arms move slightly
    arm_offset = math.sin(frame * math.pi / 2) * 2

    # Upper arms (larger, forward-reaching)
    for side in [-1, 1]:
        # Upper arm
        ax = cx + 6*s + lean
        ay = cy - 2*s + bob + side * 4*s

        # Arm segment
        pg.draw.line(surf, COLORS['carapace'],
                    (ax, ay),
                    (ax + 10*s + arm_offset, ay + side * 2*s),
                    max(3, int(4*s)))
        pg.draw.line(surf, COLORS['carapace_light'],
                    (ax, ay),
                    (ax + 10*s + arm_offset, ay + side * 2*s),
                    max(1, int(2*s)))

        # Claw
        claw_x = ax + 10*s + arm_offset
        claw_y = ay + side * 2*s
        for ci in range(3):
            angle = (side * 20 + ci * 15 - 15) * math.pi / 180
            claw_len = 6*s
            claw_ex = claw_x + math.cos(angle) * claw_len
            claw_ey = claw_y + math.sin(angle) * claw_len
            pg.draw.line(surf, COLORS['claw'], (claw_x, claw_y), (claw_ex, claw_ey), max(2, int(2*s)))
            pg.draw.circle(surf, COLORS['claw_tip'], (int(claw_ex), int(claw_ey)), max(1, int(s)))

    # Lower arms (smaller)
    for side in [-1, 1]:
        ax = cx + 2*s + lean
        ay = cy + 4*s + bob + side * 3*s

        pg.draw.line(surf, COLORS['flesh'],
                    (ax, ay),
                    (ax + 6*s - arm_offset, ay + side * 4*s),
                    max(2, int(3*s)))

        # Smaller claws
        claw_x = ax + 6*s - arm_offset
        claw_y = ay + side * 4*s
        for ci in range(2):
            angle = (side * 30 + ci * 20 - 10) * math.pi / 180
            pg.draw.line(surf, COLORS['claw_dark'],
                        (claw_x, claw_y),
                        (claw_x + math.cos(angle) * 4*s, claw_y + math.sin(angle) * 4*s),
                        max(1, int(1.5*s)))


def draw_genestealer_legs(surf, cx, cy, scale=1.0, bob=0, lean=0, frame=0):
    """Draw the digitigrade legs."""
    s = scale
    leg_phase = frame * math.pi / 2

    for side in [-1, 1]:
        lx = cx - 4*s + lean
        ly = cy + 8*s + bob

        # Thigh
        leg_bob = math.sin(leg_phase + side * math.pi/4) * 2
        knee_x = lx + side * 4*s
        knee_y = ly + 6*s + leg_bob
        pg.draw.line(surf, COLORS['carapace'], (lx, ly), (knee_x, knee_y), max(3, int(4*s)))

        # Lower leg
        foot_x = knee_x + side * 2*s
        foot_y = knee_y + 8*s - leg_bob
        pg.draw.line(surf, COLORS['carapace'], (knee_x, knee_y), (foot_x, foot_y), max(2, int(3*s)))

        # Foot claws
        for ci in range(3):
            angle = (90 + side * 20 + ci * 15 - 15) * math.pi / 180
            pg.draw.line(surf, COLORS['claw_dark'],
                        (foot_x, foot_y),
                        (foot_x + math.cos(angle) * 4*s, foot_y + math.sin(angle) * 4*s),
                        max(1, int(1.5*s)))


def create_grunt(frame):
    """Standard genestealer - balanced stats."""
    surf = pg.Surface((SPR, SPR), pg.SRCALPHA)

    cx, cy = SPR // 2 - 4, SPR // 2 + 2
    bob = math.sin(frame * math.pi / 2) * 1.5
    lean = math.cos(frame * math.pi / 2) * 1

    draw_genestealer_legs(surf, cx, cy, 1.0, bob, lean, frame)
    draw_genestealer_body(surf, cx, cy, 1.0, bob, lean)
    draw_genestealer_arms(surf, cx, cy, 1.0, bob, lean, frame)
    draw_genestealer_head(surf, cx, cy, 1.0, bob, lean, frame)

    return surf


def create_runner(frame):
    """Fast runner variant - leaner, with speed stripes."""
    surf = pg.Surface((SPR, SPR), pg.SRCALPHA)

    cx, cy = SPR // 2 - 2, SPR // 2 + 4
    # More aggressive bobbing for runner
    bob = math.sin(frame * math.pi / 2) * 2.5
    lean = math.cos(frame * math.pi / 2) * 2 + 3  # Leaning more forward

    # Leaner build (scale 0.85)
    draw_genestealer_legs(surf, cx, cy, 0.9, bob, lean, frame)
    draw_genestealer_body(surf, cx, cy, 0.85, bob, lean)

    # Add speed stripes on carapace
    s = 0.85
    for i in range(3):
        stripe_y = cy - 2 + i * 4 + bob
        pg.draw.line(surf, COLORS['stripe'],
                    (cx - 6*s + lean, stripe_y),
                    (cx + 8*s + lean, stripe_y - 2),
                    2)

    draw_genestealer_arms(surf, cx, cy, 0.85, bob, lean, frame)
    draw_genestealer_head(surf, cx, cy, 0.85, bob, lean, frame)

    # Extra crest spines for speed look
    hx = cx + 8*0.85 + lean
    hy = cy - 10*0.85 + bob
    for i in range(3):
        spine_angle = (-45 - i * 15) * math.pi / 180
        pg.draw.line(surf, COLORS['carapace_highlight'],
                    (hx + 4 + i*2, hy - 4),
                    (hx + 4 + i*2 + math.cos(spine_angle)*6, hy - 4 + math.sin(spine_angle)*6),
                    2)

    return surf


def create_shooter(frame):
    """Ranged variant with bio-weapon arm."""
    surf = pg.Surface((SPR, SPR), pg.SRCALPHA)

    cx, cy = SPR // 2 - 4, SPR // 2 + 2
    bob = math.sin(frame * math.pi / 2) * 1.2
    lean = math.cos(frame * math.pi / 2) * 0.8

    draw_genestealer_legs(surf, cx, cy, 1.0, bob, lean, frame)
    draw_genestealer_body(surf, cx, cy, 1.0, bob, lean)

    # Modified arms - one is a bio-cannon
    s = 1.0
    arm_offset = math.sin(frame * math.pi / 2) * 2

    # Normal upper arm (top)
    ax = cx + 6*s + lean
    ay = cy - 6*s + bob
    pg.draw.line(surf, COLORS['carapace'], (ax, ay), (ax + 10*s + arm_offset, ay - 2*s), max(3, int(4*s)))
    claw_x = ax + 10*s + arm_offset
    claw_y = ay - 2*s
    for ci in range(3):
        angle = (-20 + ci * 15 - 15) * math.pi / 180
        pg.draw.line(surf, COLORS['claw'], (claw_x, claw_y),
                    (claw_x + math.cos(angle) * 5*s, claw_y + math.sin(angle) * 5*s), 2)

    # Bio-cannon arm (bottom) - replaces lower arm
    ax = cx + 6*s + lean
    ay = cy + 2*s + bob
    # Arm
    pg.draw.line(surf, COLORS['carapace'], (ax, ay), (ax + 8*s, ay + 4*s), max(3, int(4*s)))
    # Cannon body
    cannon_x = ax + 8*s
    cannon_y = ay + 4*s
    pg.draw.ellipse(surf, COLORS['bio_gun_dark'], (cannon_x - 2, cannon_y - 3, 14, 8))
    pg.draw.ellipse(surf, COLORS['bio_gun'], (cannon_x, cannon_y - 2, 12, 6))
    # Barrel
    pg.draw.rect(surf, COLORS['bio_gun_dark'], (cannon_x + 8, cannon_y - 2, 8, 6))
    pg.draw.rect(surf, COLORS['bio_gun'], (cannon_x + 9, cannon_y - 1, 7, 4))
    # Glowing tip (pulsing)
    glow_intensity = 0.7 + 0.3 * math.sin(frame * math.pi / 2)
    glow_color = tuple(int(c * glow_intensity) for c in COLORS['bio_glow'])
    pg.draw.circle(surf, glow_color, (cannon_x + 16, cannon_y + 1), 3)

    # Lower arms (smaller, only one side visible)
    ax = cx + 2*s + lean
    ay = cy + 4*s + bob - 3*s
    pg.draw.line(surf, COLORS['flesh'], (ax, ay), (ax + 6*s - arm_offset, ay - 4*s), max(2, int(3*s)))

    draw_genestealer_head(surf, cx, cy, 1.0, bob, lean, frame)

    return surf


def create_brute(frame):
    """Heavy brute variant - larger with armor plates."""
    surf = pg.Surface((SPR, SPR), pg.SRCALPHA)

    cx, cy = SPR // 2 - 2, SPR // 2
    # Slower, heavier movement
    bob = math.sin(frame * math.pi / 2) * 1.0
    lean = math.cos(frame * math.pi / 2) * 0.5

    # Larger scale
    s = 1.15

    draw_genestealer_legs(surf, cx, cy, s, bob, lean, frame)
    draw_genestealer_body(surf, cx, cy, s, bob, lean)

    # Armor plates on body
    armor_pts = [
        (cx - 6*s + lean, cy - 2*s + bob),
        (cx + 4*s + lean, cy - 6*s + bob),
        (cx + 8*s + lean, cy + bob),
        (cx + 2*s + lean, cy + 6*s + bob),
        (cx - 8*s + lean, cy + 4*s + bob),
    ]
    pg.draw.polygon(surf, COLORS['armor'], armor_pts)
    pg.draw.polygon(surf, COLORS['armor_light'], armor_pts, 2)
    # Armor edge highlights
    pg.draw.line(surf, COLORS['armor_edge'], armor_pts[0], armor_pts[1], 2)
    pg.draw.line(surf, COLORS['armor_edge'], armor_pts[1], armor_pts[2], 2)

    # Shoulder armor
    for side in [-1, 1]:
        shoulder_x = cx + lean + side * 2*s
        shoulder_y = cy - 4*s + bob + side * 6*s
        pg.draw.circle(surf, COLORS['armor'], (int(shoulder_x), int(shoulder_y)), int(5*s))
        pg.draw.circle(surf, COLORS['armor_light'], (int(shoulder_x), int(shoulder_y)), int(5*s), 2)
        # Spikes on shoulders
        for spike in range(2):
            spike_angle = (side * 45 + spike * 30) * math.pi / 180
            pg.draw.line(surf, COLORS['armor_edge'],
                        (shoulder_x, shoulder_y),
                        (shoulder_x + math.cos(spike_angle) * 6*s, shoulder_y + math.sin(spike_angle) * 6*s),
                        2)

    draw_genestealer_arms(surf, cx, cy, s, bob, lean, frame)
    draw_genestealer_head(surf, cx, cy, s, bob, lean, frame)

    # Extra head crest/horn for intimidation
    hx = cx + 8*s + lean
    hy = cy - 10*s + bob
    horn_pts = [
        (hx + 4*s, hy - 6*s),
        (hx + 8*s, hy - 12*s),
        (hx + 10*s, hy - 8*s),
        (hx + 8*s, hy - 4*s),
    ]
    pg.draw.polygon(surf, COLORS['carapace_dark'], horn_pts)
    pg.draw.polygon(surf, COLORS['carapace'], horn_pts, 1)

    return surf


def main():
    pg.init()
    random.seed(42)

    print("Generating enemy sprites...")
    print("-" * 40)

    enemies = {
        'grunt': create_grunt,
        'runner': create_runner,
        'shooter': create_shooter,
        'brute': create_brute,
    }

    for name, create_func in enemies.items():
        # Create 4-frame animation strip
        strip = pg.Surface((SPR * FRAMES, SPR), pg.SRCALPHA)

        for frame in range(FRAMES):
            sprite = create_func(frame)
            strip.blit(sprite, (frame * SPR, 0))

        filename = f"{name}_idle.png"
        pg.image.save(strip, filename)
        print(f"Created {filename} ({FRAMES} frames, {SPR}x{SPR} each)")

    print("-" * 40)
    print("Enemy sprite generation complete!")


if __name__ == "__main__":
    main()
