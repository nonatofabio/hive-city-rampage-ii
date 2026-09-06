#!/usr/bin/env python3
"""Generate explosion and smoke effect animations for Hive City Rampage"""

from PIL import Image, ImageDraw
import random
import math

def generate_explosion_animation():
    """Create a 8-frame explosion animation (64x64 per frame)"""
    frame_size = 64
    frame_count = 8
    width = frame_size * frame_count
    height = frame_size

    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))

    for frame in range(frame_count):
        # Calculate animation progress
        t = frame / (frame_count - 1)

        # Create a frame
        frame_img = Image.new('RGBA', (frame_size, frame_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(frame_img)
        center = frame_size // 2

        if frame < 2:
            # Initial bright flash
            flash_radius = int(20 + frame * 8)
            # Bright white core
            draw.ellipse([center-flash_radius, center-flash_radius,
                         center+flash_radius, center+flash_radius],
                        fill=(255, 255, 200, 255))
            # Yellow outer
            flash_radius2 = flash_radius + 4
            draw.ellipse([center-flash_radius2, center-flash_radius2,
                         center+flash_radius2, center+flash_radius2],
                        fill=(255, 200, 100, 180))

        elif frame < 5:
            # Expanding fireball
            base_radius = 12 + (frame - 2) * 10

            # Multiple fireballs for chunky explosion
            for i in range(12):
                angle = (i / 12) * math.pi * 2 + frame * 0.3
                offset = 8 + (frame - 2) * 3
                fx = center + int(math.cos(angle) * offset)
                fy = center + int(math.sin(angle) * offset)
                r = random.randint(8, 12)

                # Orange/red fireball
                color = (255, random.randint(100, 180), random.randint(0, 50), 200)
                draw.ellipse([fx-r, fy-r, fx+r, fy+r], fill=color)

            # Central explosion
            for ring in range(3):
                r = base_radius - ring * 4
                alpha = 220 - ring * 60
                color = (255, 180 - ring*30, 50 - ring*20, alpha)
                draw.ellipse([center-r, center-r, center+r, center+r], fill=color)

        else:
            # Dissipating smoke
            smoke_particles = 15
            for i in range(smoke_particles):
                angle = (i / smoke_particles) * math.pi * 2
                dist = 20 + (frame - 5) * 8
                px = center + int(math.cos(angle) * dist)
                py = center + int(math.sin(angle) * dist)
                r = random.randint(4, 8)
                alpha = max(0, 180 - (frame - 5) * 50)
                gray = random.randint(40, 80)
                draw.ellipse([px-r, py-r, px+r, py+r],
                           fill=(gray, gray, gray, alpha))

        # Paste frame into strip
        img.paste(frame_img, (frame * frame_size, 0))

    img.save('explosion.png')
    print(f"Generated explosion.png: {width}x{height} ({frame_count} frames)")

def generate_smoke_animation():
    """Create a 6-frame smoke puff animation (32x32 per frame)"""
    frame_size = 32
    frame_count = 6
    width = frame_size * frame_count
    height = frame_size

    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))

    for frame in range(frame_count):
        t = frame / (frame_count - 1)

        frame_img = Image.new('RGBA', (frame_size, frame_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(frame_img)
        center = frame_size // 2

        # Multiple smoke puffs
        puff_count = 8
        for i in range(puff_count):
            angle = (i / puff_count) * math.pi * 2 + frame * 0.2
            # Smoke expands outward
            dist = 3 + t * 10
            px = center + int(math.cos(angle) * dist)
            py = center + int(math.sin(angle) * dist) - t * 5  # Rise up

            # Size varies
            r = random.randint(3, 6) + int(t * 3)
            # Fade out
            alpha = int(200 * (1 - t))
            # Gray color
            gray = random.randint(60, 100)

            draw.ellipse([px-r, py-r, px+r, py+r],
                        fill=(gray, gray, gray, alpha))

        # Central smoke
        central_r = 8 - int(t * 6)
        if central_r > 0:
            alpha = int(150 * (1 - t))
            draw.ellipse([center-central_r, center-central_r,
                         center+central_r, center+central_r],
                        fill=(80, 80, 80, alpha))

        img.paste(frame_img, (frame * frame_size, 0))

    img.save('smoke.png')
    print(f"Generated smoke.png: {width}x{height} ({frame_count} frames)")

def generate_shockwave_animation():
    """Create a 6-frame expanding shockwave ring (96x96 per frame)"""
    frame_size = 96
    frame_count = 6
    width = frame_size * frame_count
    height = frame_size

    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))

    for frame in range(frame_count):
        t = frame / (frame_count - 1)

        frame_img = Image.new('RGBA', (frame_size, frame_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(frame_img)
        center = frame_size // 2

        # Expanding ring
        radius = int(10 + t * 35)
        thickness = max(1, int(4 * (1 - t * 0.5)))
        alpha = int(200 * (1 - t))

        # Draw ring
        for i in range(thickness):
            r = radius + i
            # Color shifts from white to blue as it expands
            blue_shift = int(t * 100)
            color = (200 - blue_shift, 220 - blue_shift//2, 255, alpha)
            draw.ellipse([center-r, center-r, center+r, center+r],
                        outline=color, width=1)

        # Inner distortion effect (first few frames)
        if frame < 3:
            distort_r = int(radius * 0.7)
            distort_alpha = int(100 * (1 - frame/3))
            draw.ellipse([center-distort_r, center-distort_r,
                         center+distort_r, center+distort_r],
                        fill=(180, 200, 255, distort_alpha))

        img.paste(frame_img, (frame * frame_size, 0))

    img.save('shockwave.png')
    print(f"Generated shockwave.png: {width}x{height} ({frame_count} frames)")

def generate_grenade_icon():
    """Create a simple grenade pickup sprite (32x32)"""
    size = 32
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Grenade body (oval)
    body_rect = [10, 8, 22, 24]
    draw.ellipse(body_rect, fill=(60, 80, 60), outline=(40, 60, 40), width=1)

    # Highlight
    draw.ellipse([12, 10, 18, 16], fill=(80, 100, 80))

    # Pin and lever
    draw.rectangle([14, 5, 18, 8], fill=(120, 120, 120))
    draw.rectangle([13, 4, 19, 6], fill=(140, 140, 140))

    # Pattern on body
    draw.line([12, 14, 20, 14], fill=(40, 60, 40), width=1)
    draw.line([12, 18, 20, 18], fill=(40, 60, 40), width=1)

    img.save('pickup_grenade.png')
    print("Generated pickup_grenade.png: 32x32")

if __name__ == "__main__":
    print("Generating effect animations...")
    generate_explosion_animation()
    generate_smoke_animation()
    generate_shockwave_animation()
    generate_grenade_icon()
    print("Done!")