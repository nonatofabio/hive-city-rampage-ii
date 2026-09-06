"""
Main game loop for Hive City Rampage
Orchestrates all systems and handles game state
"""

import math
import random
import sys
import os
import pygame as pg

# Import all our modules
from constants import *
from utils import *
from assets import *
from world import Camera, Arena
from entities import *
from director import Director
from ai import pick_aim_target


# -------------------- RENDER HELPERS --------------------
def blit_center(screen, img, x, y):
    """Draw image centered at position"""
    r = img.get_rect(center=(x, y))
    screen.blit(img, r)


def draw_placeholder(screen, x, y, color, size=34):
    """Draw colored placeholder rectangle"""
    r = pg.Rect(0, 0, size, size)
    r.center = (x, y)
    pg.draw.rect(screen, color, r, border_radius=6)
    pg.draw.rect(screen, (0, 0, 0), r, 2, border_radius=6)


# -------------------- MAIN GAME --------------------
def main():
    """Main game loop"""
    from gothic_ui import GothicHUD
    pg.init()
    screen = pg.display.set_mode((W, H))
    clock = pg.time.Clock()
    pg.display.set_caption("Hive City Rampage (Pygame)")

    # Load assets
    assets = SpriteBank(os.path.join(os.path.dirname(__file__), "assets"))

    # Player animations
    assets.load_anim("marine_idle", "marine_idle.png", frames=1, fps=SPR_FPS_IDLE)
    assets.load_anim("marine_walk", "marine_walk.png", frames=2, fps=SPR_FPS_WALK)
    assets.load_anim("marine_shoot", "marine_shoot.png", frames=4, fps=12)

    # Enemy animations
    assets.load_anim("grunt_idle", "grunt_idle.png", frames=4, fps=SPR_FPS_IDLE)
    assets.load_anim("grunt_walk", "grunt_walk.png", frames=3, fps=SPR_FPS_WALK)
    assets.load_anim("runner_idle", "runner_idle.png", frames=4, fps=SPR_FPS_IDLE)
    assets.load_anim("runner_walk", "runner_walk.png", frames=3, fps=SPR_FPS_WALK)
    assets.load_anim("shooter_idle", "shooter_idle.png", frames=4, fps=SPR_FPS_IDLE)
    assets.load_anim("brute_idle", "brute_idle.png", frames=4, fps=SPR_FPS_IDLE)
    assets.load_anim("brute_walk", "brute_walk.png", frames=3, fps=SPR_FPS_WALK)

    player_bullet = load_image(os.path.join(assets.dir, "bullet_player.png"))
    enemy_bullet = load_image(os.path.join(assets.dir, "bullet_enemy.png"))

    # Load effect animations
    explosion_sheet = load_image(os.path.join(assets.dir, "explosion.png"))
    explosion_frames = []
    if explosion_sheet:
        for i in range(8):
            rect = pg.Rect(i * 64, 0, 64, 64)
            explosion_frames.append(explosion_sheet.subsurface(rect).copy())

    smoke_sheet = load_image(os.path.join(assets.dir, "smoke.png"))
    smoke_frames = []
    if smoke_sheet:
        for i in range(6):
            rect = pg.Rect(i * 32, 0, 32, 32)
            smoke_frames.append(smoke_sheet.subsurface(rect).copy())

    shockwave_sheet = load_image(os.path.join(assets.dir, "shockwave.png"))
    shockwave_frames = []
    if shockwave_sheet:
        for i in range(6):
            rect = pg.Rect(i * 96, 0, 96, 96)
            shockwave_frames.append(shockwave_sheet.subsurface(rect).copy())

    grenade_pickup_img = load_image(os.path.join(assets.dir, "pickup_grenade.png"))

    # Load terrain sprites v2 (edge-aware autotiling)
    terrain_interior = load_image(os.path.join(assets.dir, "terrain_interior.png"))
    terrain_autotile = load_image(os.path.join(assets.dir, "terrain_autotile.png"))
    terrain_corners_outer = load_image(os.path.join(assets.dir, "terrain_corners_outer.png"))
    terrain_corners_inner = load_image(os.path.join(assets.dir, "terrain_corners_inner.png"))
    terrain_floors_v2 = load_image(os.path.join(assets.dir, "terrain_floors_v2.png"))
    terrain_wall_elements = load_image(os.path.join(assets.dir, "terrain_wall_elements.png"))

    # Slice autotile sheet (16 edge configurations)
    autotile_walls = []
    if terrain_autotile:
        for i in range(10):
            rect = pg.Rect(i * 32, 0, 32, 32)
            autotile_walls.append(terrain_autotile.subsurface(rect).copy())

    # Slice outer corner tiles (NW, NE, SW, SE)
    outer_corners = []
    if terrain_corners_outer:
        for i in range(4):
            rect = pg.Rect(i * 32, 0, 32, 32)
            outer_corners.append(terrain_corners_outer.subsurface(rect).copy())

    # Slice inner corner tiles
    inner_corners = []
    if terrain_corners_inner:
        for i in range(4):
            rect = pg.Rect(i * 32, 0, 32, 32)
            inner_corners.append(terrain_corners_inner.subsurface(rect).copy())

    # Slice floor tiles
    floor_tiles = []
    if terrain_floors_v2:
        for i in range(8):
            rect = pg.Rect(i * 32, 0, 32, 32)
            floor_tiles.append(terrain_floors_v2.subsurface(rect).copy())

    # Slice wall elements
    wall_elements = []
    if terrain_wall_elements:
        for i in range(8):
            rect = pg.Rect(i * 32, 0, 32, 32)
            wall_elements.append(terrain_wall_elements.subsurface(rect).copy())

    # Fallback for old wall_tiles reference
    wall_tiles = autotile_walls if autotile_walls else []

    # Load hazard tiles
    hazard_tiles = {}
    for hazard_type in ["toxic", "electric", "heat"]:
        img = load_image(os.path.join(assets.dir, f"hazard_{hazard_type}.png"))
        if img:
            hazard_tiles[hazard_type] = img

    # Load prop sprites
    prop_images = {}
    prop_names = ['computer_n', 'computer_s', 'holotable', 'container', 'crate',
                  'barrel', 'ammo_crate', 'weapon_rack', 'column', 'generator',
                  'light_post', 'pipe_vertical', 'small_crate']
    for prop_name in prop_names:
        img = load_image(os.path.join(assets.dir, f"prop_{prop_name}.png"))
        if img:
            prop_images[prop_name] = img

    # Load animated tile sheets
    animated_tile_data = {}
    anim_configs = [
        ("flickering_light", 4, 8),
        ("steam_vent", 6, 10),
        ("electrical_panel", 8, 12)
    ]

    for anim_name, frame_count, fps in anim_configs:
        sheet = load_image(os.path.join(assets.dir, f"anim_{anim_name}.png"))
        if sheet:
            frames = []
            for i in range(frame_count):
                rect = pg.Rect(i * 32, 0, 32, 32)
                frames.append(sheet.subsurface(rect).copy())
            animated_tile_data[anim_name] = (frames, fps)

    # Load decal overlays
    decal_images = {}
    for decal_type in ["blood_pool", "shell_casing", "debris", "oil_spill", "scorch_mark", "corpse"]:
        img = load_image(os.path.join(assets.dir, f"decal_{decal_type}.png"))
        if img:
            decal_images[decal_type] = img

    # Initialize Gothic HUD
    hud = GothicHUD(W, H, assets.dir)

    # Initialize game state
    arena = Arena()
    player = Player(arena.w*TILE/2, arena.h*TILE/2)
    camera = Camera()
    director = Director()
    enemies = []
    bullets = []
    pickups = []
    explosions = []
    vfx = []

    # Create AnimatedTile instances for the arena
    animated_tile_instances = {}
    for (tx, ty), anim_type in arena.animated_tiles.items():
        if anim_type in animated_tile_data:
            frames, fps = animated_tile_data[anim_type]
            animated_tile_instances[(tx, ty)] = AnimatedTile(frames, fps)

    # Animation instances
    marine_idle = assets.anim("marine_idle")
    marine_walk = assets.anim("marine_walk")
    marine_shoot = assets.anim("marine_shoot")
    enemy_idle_anims = {
        "grunt": assets.anim("grunt_idle"),
        "runner": assets.anim("runner_idle"),
        "shooter": assets.anim("shooter_idle"),
        "brute": assets.anim("brute_idle"),
    }
    enemy_walk_anims = {
        "grunt": assets.anim("grunt_walk"),
        "runner": assets.anim("runner_walk"),
        "shooter": assets.anim("shooter_idle"),  # no walk, use idle
        "brute": assets.anim("brute_walk"),
    }

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        fps = clock.get_fps()

        # -------------------- EVENT HANDLING --------------------
        for ev in pg.event.get():
            if ev.type == pg.QUIT:
                running = False
            if ev.type == pg.KEYDOWN and ev.key == pg.K_x:
                arena = Arena()
                player = Player(arena.w*TILE/2, arena.h*TILE/2)
                enemies.clear(); bullets.clear(); pickups.clear()
                explosions.clear(); vfx.clear()
                director = Director()
                camera.shake_t = 0; camera.shake_pow = 0; camera.shake_seed = 0

                # Recreate animated tiles for new arena
                animated_tile_instances.clear()
                for (tx, ty), anim_type in arena.animated_tiles.items():
                    if anim_type in animated_tile_data:
                        frames, fps = animated_tile_data[anim_type]
                        animated_tile_instances[(tx, ty)] = AnimatedTile(frames, fps)

        keys = pg.key.get_pressed()

        # -------------------- UPDATE --------------------
        if player.hp > 0:
            # Movement input
            ax = (keys[pg.K_d] - keys[pg.K_a])
            ay = (keys[pg.K_s] - keys[pg.K_w])

            if ax or ay:
                sx = 1 if ax > 0 else -1 if ax < 0 else 0
                sy = 1 if ay > 0 else -1 if ay < 0 else 0
                if sx or sy:
                    player.face = (sx, sy)

            # Apply acceleration with diagonal compensation
            if ax and ay:
                # For diagonal movement, normalize the input to maintain consistent speed
                # sqrt(2) normalization prevents slowdown on diagonals
                diag_factor = 0.7071  # 1/sqrt(2)
                player.vx += ax * PLAYER_ACC * diag_factor * 1.4  # Extra boost for diagonals
                player.vy += ay * PLAYER_ACC * diag_factor * 1.4
            else:
                player.vx += ax * PLAYER_ACC
                player.vy += ay * PLAYER_ACC

            # Speed clamping
            sp = math.hypot(player.vx, player.vy)
            if sp > PLAYER_MAX:
                s = PLAYER_MAX / sp
                player.vx *= s
                player.vy *= s

            # Reduced turn drag for snappier controls
            if (ax and abs(player.vy) > 80) or (ay and abs(player.vx) > 80):
                player.vx *= 0.92  # less drag for quicker direction changes
                player.vy *= 0.92

            player.vx *= PLAYER_FRIC
            player.vy *= PLAYER_FRIC
            player.try_move(arena, player.vx*dt, player.vy*dt)

            moving = (abs(player.vx) + abs(player.vy)) > 60  # adjusted for higher speed
            if moving:
                player.walk_phase += dt
                # Footstep shake (matching PICO-8 prototype)
                player.step_t += 1
                if player.step_t >= 14:
                    player.step_t = 0
                    camera.add_shake(0.6, 4)  # subtle footstep shake
            else:
                player.step_t = 0

            # Aim with mouse
            mx, my = pg.mouse.get_pos()
            # Convert screen position to world position
            world_mx = mx + camera.x - camera.frame_shake_x
            world_my = my + camera.y - camera.frame_shake_y
            # Direction from player to mouse
            ux, uy, _ = norm(world_mx - player.x, world_my - player.y)
            player.aim = (ux, uy)
            # Update face direction to match aim
            player.face = (1 if ux > 0 else -1, 0)

            # Shooting (left mouse button)
            mouse_buttons = pg.mouse.get_pressed()
            player.is_shooting = False
            if player.cd > 0: player.cd -= 1
            if mouse_buttons[0] and player.cd <= 0:
                player.cd = SHOT_COOLDOWN_FR
                player.shoot_flash = 0.10
                player.is_shooting = True
                player.shield_regen_timer = 0.0  # reset regen timer when shooting
                bvx = player.aim[0] * 520
                bvy = player.aim[1] * 520
                bullets.append(Bullet(player.x, player.y, bvx, bvy, life=0.75, owner="player"))
                camera.add_shake(1.1, 8)  # halved for better feel

            # Grenade throwing (space key)
            if player.grenade_cd > 0:
                player.grenade_cd -= dt
            if keys[pg.K_SPACE] and player.grenade_cd <= 0 and player.grenades > 0:
                player.grenades -= 1
                player.grenade_cd = GRENADE_COOLDOWN

                # Create explosion at player position
                explosions.append(Explosion(player.x, player.y))
                vfx.append(VFX(player.x, player.y, "shockwave"))

                # Damage and knockback all enemies in radius
                for e in enemies[:]:
                    dx, dy = e.x - player.x, e.y - player.y
                    d2 = dx*dx + dy*dy
                    if d2 < GRENADE_RADIUS**2:
                        e.hp -= GRENADE_DAMAGE
                        # Knockback away from explosion
                        kx, ky, d = norm(dx, dy)
                        force = GRENADE_KNOCKBACK * (1 - d/GRENADE_RADIUS)
                        e.knock_vx += kx * force
                        e.knock_vy += ky * force
                        # Add smoke effect on hit enemies
                        vfx.append(VFX(e.x, e.y, "smoke"))

                # Big screen shake
                camera.add_shake(12.0, 15)

            # Shield regeneration (continuous after delay when not shooting)
            if not player.is_shooting and player.shield < player.max_shield:
                player.shield_regen_timer += dt
                if player.shield_regen_timer >= SHIELD_REGEN_DELAY:
                    player.shield = min(player.max_shield, player.shield + SHIELD_REGEN_RATE * dt)

            if player.ifr > 0: player.ifr -= 1
            if player.dmg_cd > 0: player.dmg_cd -= 1
            if player.shoot_flash > 0: player.shoot_flash -= dt

        # Director
        prev_wave = director.wave
        director.tick(dt, arena, player, enemies, camera)

        # Wave completion bonus
        if director.wave > prev_wave and player.hp > 0:
            wave_bonus = WAVE_BONUS_BASE * prev_wave
            player.points += wave_bonus

        # Bullets update
        for b in bullets[:]:
            b.x += b.vx * dt
            b.y += b.vy * dt
            b.life -= dt
            if b.life <= 0 or arena.is_solid_px(b.x, b.y):
                bullets.remove(b)
                continue

            if b.owner == "player":
                for e in enemies:
                    if dist2(b.x, b.y, e.x, e.y) < (18**2):
                        e.hp -= 1
                        camera.add_shake(0.9, 6)
                        if b in bullets: bullets.remove(b)
                        break
            else:
                # Enemy bullet hits player - damages shield first (3 per bullet)
                if player.hp > 0 and dist2(b.x, b.y, player.x, player.y) < (18**2) and player.ifr <= 0:
                    if player.shield > 0:
                        player.shield = max(0, player.shield - 3)
                    else:
                        player.hp -= 1
                    player.ifr = IFRAMES_FR
                    camera.add_shake(2.6, 10)
                    if b in bullets: bullets.remove(b)

        # Enemies update
        for e in enemies[:]:
            dx, dy = player.x - e.x, player.y - e.y
            ux, uy, d = norm(dx, dy)

            # Apply and decay knockback velocity (smooth bounce)
            if abs(e.knock_vx) > 1 or abs(e.knock_vy) > 1:
                e.try_move(arena, e.knock_vx * dt, e.knock_vy * dt)
                e.knock_vx *= 0.85  # decay
                e.knock_vy *= 0.85

            vx = ux * e.spd * 120
            vy = uy * e.spd * 120

            if e.kind == "shooter" and d < 180:
                vx *= -0.55; vy *= -0.55

            e.try_move(arena, vx*dt, vy*dt)

            # Separation from other enemies (stronger for non-runners)
            pushx = pushy = 0.0

            # Different separation rules based on enemy type
            if e.kind == "runner":
                sep_radius = 32  # Runners can get closer
                sep_force = 2.0   # Weaker separation force
            else:
                sep_radius = 56  # Other enemies need more space
                sep_force = 4.5   # Strong separation force

            for o in enemies:
                if o is e: continue
                ddx, ddy = e.x - o.x, e.y - o.y
                d2 = ddx*ddx + ddy*ddy

                # Use appropriate radius based on both enemy types
                check_radius = sep_radius if o.kind != "runner" or e.kind != "runner" else 32

                if 1 < d2 < (check_radius**2):
                    ux2, uy2, dd = norm(ddx, ddy)
                    f = (check_radius - dd) * sep_force
                    pushx += ux2 * f
                    pushy += uy2 * f

            # Separation from player (no visual overlap)
            if player.hp > 0:
                pdx, pdy = e.x - player.x, e.y - player.y
                pd2 = pdx*pdx + pdy*pdy
                player_sep_radius = 48  # Keep enemies visually separated from player
                if 1 < pd2 < (player_sep_radius**2):
                    pux, puy, pdd = norm(pdx, pdy)
                    pf = (player_sep_radius - pdd) * 3.5
                    pushx += pux * pf
                    pushy += puy * pf

            e.try_move(arena, pushx*dt, pushy*dt)

            # Melee contact damage with shield system, bounce-back, and auto-damage
            if e.hit_cd > 0: e.hit_cd -= 1
            if player.hp > 0 and dist2(e.x, e.y, player.x, player.y) < (22**2) and e.hit_cd <= 0 and player.ifr <= 0 and player.dmg_cd <= 0:
                e.hit_cd = 24  # longer cooldown for melee enemies
                player.dmg_cd = GLOBAL_DMG_CD_FR
                player.ifr = IFRAMES_FR

                # Shield absorbs melee damage (1 per hit, need 15 to deplete)
                if player.shield > 0:
                    player.shield = max(0, player.shield - 1)
                else:
                    player.hp -= e.dmg

                # Bounce player away from enemy
                kx, ky, _ = norm(player.x - e.x, player.y - e.y)
                player.try_move(arena, kx*28, ky*28)

                # BOUNCE ENEMY BACK as velocity (smooth knockback)
                e.knock_vx = -kx * 450  # velocity, will be applied over multiple frames
                e.knock_vy = -ky * 450

                # Player auto-damages melee enemy on contact (0.5 HP via accumulator)
                if not hasattr(e, 'melee_dmg_accum'):
                    e.melee_dmg_accum = 0.0
                e.melee_dmg_accum += 0.5
                if e.melee_dmg_accum >= 1.0:
                    e.hp -= 1
                    e.melee_dmg_accum -= 1.0
                camera.add_shake(3.0, 10)

                # If enemy dies from melee, regenerate HP by 1
                if e.hp <= 0:
                    player.hp = min(player.maxhp, player.hp + 1)
                    camera.add_shake(4.0, 12)
                else:
                    camera.add_shake(2.5, 8)

            # Shooter bullets
            if e.kind == "shooter":
                e.shoot_cd -= dt
                if e.shoot_cd <= 0 and d < ENEMY_SHOOT_RANGE and player.hp > 0:
                    e.shoot_cd = random.uniform(0.9, 1.5)
                    bux, buy, _ = norm(player.x - e.x, player.y - e.y)
                    bullets.append(Bullet(e.x, e.y, bux*ENEMY_BULLET_SPEED, buy*ENEMY_BULLET_SPEED,
                                          life=ENEMY_BULLET_LIFE, owner="enemy"))
                    camera.add_shake(0.8, 6)

            if e.hp <= 0:
                # Award points based on enemy type with combo multiplier
                base_points = {"grunt": POINTS_GRUNT, "runner": POINTS_RUNNER,
                               "shooter": POINTS_SHOOTER, "brute": POINTS_BRUTE}.get(e.kind, 10)
                combo_mult = 1.0 + player.combo * COMBO_MULTIPLIER
                player.points += int(base_points * combo_mult)
                player.combo += 1
                player.combo_timer = COMBO_WINDOW

                # Chance to spawn pickup
                if random.random() < PICKUP_SPAWN_CHANCE:
                    pickup_kind = "health" if random.random() < 0.5 else "shield"
                    pickups.append(Pickup(e.x, e.y, pickup_kind))
                elif random.random() < GRENADE_PICKUP_CHANCE:
                    pickups.append(Pickup(e.x, e.y, "grenade"))

                enemies.remove(e)

        # Update combo timer
        if player.combo_timer > 0:
            player.combo_timer -= dt
            if player.combo_timer <= 0:
                player.combo = 0

        # Update and collect pickups
        for p in pickups[:]:
            p.life -= dt
            if p.life <= 0:
                pickups.remove(p)
                continue
            # Check player collision
            if dist2(p.x, p.y, player.x, player.y) < PICKUP_RADIUS**2:
                if p.kind == "health":
                    player.hp = min(player.maxhp, player.hp + HEALTH_PICKUP_AMOUNT)
                elif p.kind == "shield":
                    player.shield = min(player.max_shield, player.shield + SHIELD_PICKUP_AMOUNT)
                elif p.kind == "grenade":
                    player.grenades += 1  # No max limit, let player stock up
                pickups.remove(p)

        # Update explosions
        for exp in explosions[:]:
            exp.life -= dt
            exp.frame = int((0.5 - exp.life) * 16)  # 8 frames over 0.5 seconds
            if exp.life <= 0:
                explosions.remove(exp)

        # Update VFX
        for v in vfx[:]:
            v.life -= dt
            if v.kind == "smoke":
                v.frame = int((0.4 - v.life) * 15)  # 6 frames over 0.4 seconds
            else:  # shockwave
                v.frame = int((0.3 - v.life) * 20)  # 6 frames over 0.3 seconds
            if v.life <= 0:
                vfx.remove(v)

        # Stim pack auto-revive system
        if player.hp <= 0 and player.stims_used < MAX_STIMS:
            player.stims_used += 1
            player.hp = player.maxhp
            player.shield = player.max_shield
            player.ifr = 60  # brief invincibility after revive
            camera.add_shake(8.0, 20)  # big shake on revive

        # Camera follow
        camera.update(player.x - W/2, player.y - H/2)

        # Update anims
        marine_idle.update(dt)
        marine_walk.update(dt)
        marine_shoot.update(dt)
        for a in enemy_idle_anims.values():
            a.update(dt)
        for a in enemy_walk_anims.values():
            a.update(dt)

        # Update animated tiles
        for anim_tile in animated_tile_instances.values():
            anim_tile.update(dt)

        # -------------------- DRAW --------------------
        screen.fill((12, 10, 8))  # Warm dark background

        # Draw tiles (visible window)
        camx, camy = camera.x, camera.y
        x0 = int(camx // TILE) - 2
        y0 = int(camy // TILE) - 2
        x1 = x0 + int(W // TILE) + 5
        y1 = y0 + int(H // TILE) + 5

        for ty in range(y0, y1):
            if ty < 0 or ty >= arena.h: continue
            for tx in range(x0, x1):
                if tx < 0 or tx >= arena.w: continue
                px = tx*TILE
                py = ty*TILE
                sx, sy = camera.apply_xy(px, py)
                r = pg.Rect(int(sx), int(sy), TILE, TILE)
                if arena.solid[ty][tx]:
                    # Edge-aware wall rendering
                    if (tx, ty) in arena.wall_elements and wall_elements:
                        # Draw wall element (computer, pipes, etc.)
                        elem_idx = arena.wall_elements[(tx, ty)]
                        if elem_idx < len(wall_elements):
                            screen.blit(wall_elements[elem_idx], r)
                        else:
                            pg.draw.rect(screen, (45, 45, 52), r)
                    elif arena.is_interior_wall(tx, ty):
                        # Interior wall (surrounded by walls) - dark
                        if terrain_interior:
                            screen.blit(terrain_interior, r)
                        else:
                            pg.draw.rect(screen, (12, 12, 15), r)
                    elif autotile_walls:
                        # Edge wall - use autotile based on neighbors
                        mask = arena.get_neighbor_mask(tx, ty)
                        if mask < len(autotile_walls):
                            screen.blit(autotile_walls[mask], r)
                        else:
                            pg.draw.rect(screen, (45, 45, 52), r)
                    else:
                        pg.draw.rect(screen, (45, 45, 52), r)
                else:
                    # Check for hazard tiles first
                    if (tx, ty) in arena.hazard_tiles:
                        hazard_type = arena.hazard_tiles[(tx, ty)]
                        if hazard_type in hazard_tiles:
                            screen.blit(hazard_tiles[hazard_type], r)
                        else:
                            # Fallback floor
                            if floor_tiles:
                                variant_idx = arena.floor_variants[ty][tx] % len(floor_tiles)
                                screen.blit(floor_tiles[variant_idx], r)
                            else:
                                pg.draw.rect(screen, (18, 18, 22), r)

                    # Check for animated tiles
                    elif (tx, ty) in animated_tile_instances:
                        anim_tile = animated_tile_instances[(tx, ty)]
                        frame = anim_tile.frame()
                        if frame:
                            screen.blit(frame, r)
                        else:
                            # Fallback floor
                            if floor_tiles:
                                variant_idx = arena.floor_variants[ty][tx] % len(floor_tiles)
                                screen.blit(floor_tiles[variant_idx], r)
                            else:
                                pg.draw.rect(screen, (18, 18, 22), r)

                    # Regular floor tile
                    else:
                        if floor_tiles:
                            variant_idx = arena.floor_variants[ty][tx] % len(floor_tiles)
                            screen.blit(floor_tiles[variant_idx], r)
                        else:
                            pg.draw.rect(screen, (18, 18, 22), r)

                    # Draw props on floor tiles
                    if (tx, ty) in arena.props:
                        prop_type = arena.props[(tx, ty)]
                        if prop_type in prop_images:
                            screen.blit(prop_images[prop_type], r)

                    # Draw decals on top of floor tiles
                    if (tx, ty) in arena.tile_decals:
                        decal_type = arena.tile_decals[(tx, ty)]
                        if decal_type in decal_images:
                            screen.blit(decal_images[decal_type], r, special_flags=pg.BLEND_RGBA_ADD)

        # Bullets
        for b in bullets:
            sx, sy = camera.apply_xy(b.x, b.y)
            if b.owner == "player" and player_bullet:
                blit_center(screen, player_bullet, sx, sy)
            elif b.owner == "enemy" and enemy_bullet:
                blit_center(screen, enemy_bullet, sx, sy)
            else:
                color = (255, 210, 80) if b.owner == "player" else (255, 80, 110)
                pg.draw.circle(screen, color, (int(sx), int(sy)), 4)

        # Pickups
        for p in pickups:
            sx, sy = camera.apply_xy(p.x, p.y)
            # Pulsing effect based on life remaining
            pulse = 1.0 + 0.2 * math.sin(p.life * 8)
            size = int(12 * pulse)
            if p.kind == "health":
                color = (255, 80, 80)  # red for health
                pg.draw.circle(screen, color, (int(sx), int(sy)), size)
                pg.draw.circle(screen, (255, 200, 200), (int(sx), int(sy)), size - 3)
                # Cross symbol
                pg.draw.rect(screen, color, (int(sx) - 4, int(sy) - 1, 8, 2))
                pg.draw.rect(screen, color, (int(sx) - 1, int(sy) - 4, 2, 8))
            elif p.kind == "shield":
                color = (80, 180, 255)  # blue for shield
                pg.draw.circle(screen, color, (int(sx), int(sy)), size)
                pg.draw.circle(screen, (200, 230, 255), (int(sx), int(sy)), size - 3)
            else:  # grenade
                if grenade_pickup_img:
                    blit_center(screen, grenade_pickup_img, sx, sy)
                else:
                    color = (100, 140, 100)  # green for grenade
                    pg.draw.circle(screen, color, (int(sx), int(sy)), size)
                    pg.draw.circle(screen, (150, 200, 150), (int(sx), int(sy)), size - 3)

        # Enemies
        for e in enemies:
            sx, sy = camera.apply_xy(e.x, e.y)
            img = enemy_walk_anims[e.kind].frame()
            if img:
                # Flip sprite if moving left (toward player)
                if player.x < e.x:
                    img = pg.transform.flip(img, True, False)
                blit_center(screen, img, sx, sy)
            else:
                color = (170, 90, 90)
                if e.kind == "runner": color = (200, 120, 120)
                if e.kind == "shooter": color = (150, 120, 200)
                if e.kind == "brute": color = (220, 170, 90)
                draw_placeholder(screen, sx, sy, color, size=48)

        # Player
        psx, psy = camera.apply_xy(player.x, player.y)
        moving = (abs(player.vx) + abs(player.vy)) > 60  # adjusted for higher speed
        if player.shoot_flash > 0 and marine_shoot.frame():
            pimg = marine_shoot.frame()
        else:
            pimg = marine_walk.frame() if moving else marine_idle.frame()
        if pimg:
            # Flip sprite if aiming left
            if player.aim[0] < 0:
                pimg = pg.transform.flip(pimg, True, False)
            blit_center(screen, pimg, psx, psy)
        else:
            draw_placeholder(screen, psx, psy, (90, 180, 255), size=50)

        # Render VFX (shockwaves first, under explosions)
        for v in vfx:
            sx, sy = camera.apply_xy(v.x, v.y)
            if v.kind == "shockwave":
                if shockwave_frames and 0 <= v.frame < len(shockwave_frames):
                    blit_center(screen, shockwave_frames[v.frame], sx, sy)

        # Render explosions
        for exp in explosions:
            sx, sy = camera.apply_xy(exp.x, exp.y)
            if explosion_frames and 0 <= exp.frame < len(explosion_frames):
                blit_center(screen, explosion_frames[exp.frame], sx, sy)

        # Render smoke VFX (on top)
        for v in vfx:
            sx, sy = camera.apply_xy(v.x, v.y)
            if v.kind == "smoke":
                if smoke_frames and 0 <= v.frame < len(smoke_frames):
                    blit_center(screen, smoke_frames[v.frame], sx, sy)

        # Draw Gothic HUD
        hud.draw(screen, player, director, len(enemies))

        pg.display.flip()

    pg.quit()


if __name__ == "__main__":
    if "--classic" in sys.argv:
        main()
    else:
        from isometric_game import main as siege_main
        siege_main()
