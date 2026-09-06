import math, random, sys, os
import pygame as pg

# -------------------- CONFIG --------------------
W, H = 960, 540
FPS = 60
TILE = 32
WORLD_W, WORLD_H = 120, 90  # in tiles

# sprite animation
SPR_FPS_IDLE = 6
SPR_FPS_WALK = 10

# gameplay feel (tuned to match PICO-8 prototype feel)
PLAYER_ACC = 25.0
PLAYER_MAX = 450.0
PLAYER_FRIC = 0.82
PLAYER_TURN_DRAG = 0.78
SHOT_COOLDOWN_FR = 6

AIM_RANGE = 10 * TILE
AIM_CONE = 0.45
AIM_SMOOTH = 0.16
AIM_HOLD_FR = 10

# fairness
SAFE_SPAWN_DIST = 8 * TILE
PRESSURE_RADIUS = 3 * TILE
PRESSURE_CAP = 4
GLOBAL_DMG_CD_FR = 12
IFRAMES_FR = 18

# enemy bullets
ENEMY_BULLET_SPEED = 250.0
ENEMY_BULLET_LIFE = 1.2
ENEMY_SHOOT_RANGE = 9 * TILE

# shield regen (reduced to favor pickups)
SHIELD_REGEN_DELAY = 1.2  # seconds after shooting before regen starts
SHIELD_REGEN_RATE = 2.0   # shield points per second (was 5)

# pickups (increased drop rate)
PICKUP_RADIUS = 24
PICKUP_SPAWN_CHANCE = 0.25  # chance per enemy kill (was 0.15)
HEALTH_PICKUP_AMOUNT = 3
SHIELD_PICKUP_AMOUNT = 5

# grenades
GRENADE_COOLDOWN = 3.0  # seconds between grenades
GRENADE_RADIUS = 240  # explosion radius (doubled for massive blast)
GRENADE_DAMAGE = 4  # damage to enemies
GRENADE_KNOCKBACK = 800  # knockback force
MAX_GRENADES = 5  # starting grenades
GRENADE_PICKUP_CHANCE = 0.08  # chance to drop grenade pickup

# points
POINTS_GRUNT = 10
POINTS_RUNNER = 15
POINTS_SHOOTER = 25
POINTS_BRUTE = 50
COMBO_WINDOW = 1.5  # seconds to chain kills
COMBO_MULTIPLIER = 0.5  # bonus per combo level (1.0, 1.5, 2.0, ...)
WAVE_BONUS_BASE = 100  # base points per wave completed

# stim packs
MAX_STIMS = 3

# -------------------- HELPERS --------------------
def clamp(v, a, b): return a if v < a else b if v > b else v
def dist2(ax, ay, bx, by):
    dx, dy = ax - bx, ay - by
    return dx*dx + dy*dy

def norm(dx, dy):
    d = math.hypot(dx, dy)
    if d < 1e-6: return 1.0, 0.0, 1.0
    return dx/d, dy/d, d

def lerp(a, b, t): return a + (b - a) * t

# -------------------- ASSETS --------------------
def load_image(path):
    try:
        return pg.image.load(path).convert_alpha()
    except Exception:
        return None

def slice_strip(img, frame_w, frame_h):
    if img is None:
        return []
    frames = []
    w, h = img.get_size()
    cols = w // frame_w
    rows = h // frame_h
    for y in range(rows):
        for x in range(cols):
            r = pg.Rect(x*frame_w, y*frame_h, frame_w, frame_h)
            frames.append(img.subsurface(r).copy())
    return frames

class Anim:
    def __init__(self, frames, fps=10):
        self.frames = frames
        self.fps = fps
        self.t = 0.0

    def update(self, dt):
        self.t += dt

    def frame(self):
        if not self.frames:
            return None
        i = int(self.t * self.fps) % len(self.frames)
        return self.frames[i]

class AnimatedTile:
    def __init__(self, frames, fps=10):
        self.frames = frames
        self.fps = fps
        self.t = random.random() * len(frames) / fps  # Random start time

    def update(self, dt):
        self.t += dt

    def frame(self):
        if not self.frames:
            return None
        i = int(self.t * self.fps) % len(self.frames)
        return self.frames[i]

class SpriteBank:
    def __init__(self, assets_dir="assets"):
        self.dir = assets_dir
        self.img = {}

    def get(self, key):
        return self.img.get(key)

    def load_anim(self, key, filename, frames=4, fps=10):
        """Load animation strip. Frames are auto-sized from image width."""
        path = os.path.join(self.dir, filename)
        img = load_image(path)
        if img:
            w, h = img.get_size()
            frame_w = w // frames
            frame_list = slice_strip(img, frame_w, h)
        else:
            frame_list = []
        self.img[key] = (img, frame_list, fps)

    def anim(self, key):
        pack = self.img.get(key)
        if not pack:
            return Anim([], 10)
        _, frames, fps = pack
        return Anim(frames, fps)

# -------------------- WORLD --------------------
class Camera:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.shake_t = 0
        self.shake_pow = 0.0
        self.shake_seed = 0
        # Per-frame shake offset (computed once in update, used by all apply_xy calls)
        self.frame_shake_x = 0.0
        self.frame_shake_y = 0.0

    def add_shake(self, pow_, t):
        self.shake_pow = min(18.0, self.shake_pow + pow_)
        self.shake_t = max(self.shake_t, t)
        self.shake_seed += 1

    def update(self, target_x, target_y):
        self.x += (target_x - self.x) * 0.12
        self.y += (target_y - self.y) * 0.12

        # Compute shake once per frame (matching PICO-8 style with sinusoidal component)
        if self.shake_t > 0:
            self.shake_t -= 1
            self.shake_pow *= 0.90
            t = self.shake_seed * 0.1
            self.frame_shake_x = (random.random() - 0.5) * 2 * self.shake_pow + math.sin(t * 12) * self.shake_pow * 0.35
            self.frame_shake_y = (random.random() - 0.5) * 2 * self.shake_pow + math.cos(t * 10) * self.shake_pow * 0.35
        else:
            self.shake_pow = 0.0
            self.frame_shake_x = 0.0
            self.frame_shake_y = 0.0

    def apply_xy(self, x, y):
        return x - self.x + self.frame_shake_x, y - self.y + self.frame_shake_y

class Arena:
    def __init__(self, seed=None):
        random.seed(seed)
        self.w = WORLD_W
        self.h = WORLD_H
        self.solid = [[1] * self.w for _ in range(self.h)]
        self.floor = []
        self.wall_variants = [[0] * self.w for _ in range(self.h)]
        self.floor_variants = [[0] * self.w for _ in range(self.h)]
        self.tile_decals = {}  # (tx,ty): decal_type
        self.animated_tiles = {}  # (tx,ty): AnimatedTile instance
        self.hazard_tiles = {}  # (tx,ty): hazard_type
        self.wall_elements = {}  # (tx,ty): element_index (0-7)
        self.props = {}  # (tx,ty): prop_type string
        self.rooms = []  # List of (x,y,w,h) room rectangles
        self._gen()
        self._assign_variants()

    def get_neighbor_mask(self, tx, ty):
        """Get 4-bit mask for cardinal neighbors (1=floor touching)
        N=1, E=2, S=4, W=8"""
        mask = 0
        if ty > 0 and self.solid[ty-1][tx] == 0: mask |= 1  # N
        if tx < self.w-1 and self.solid[ty][tx+1] == 0: mask |= 2  # E
        if ty < self.h-1 and self.solid[ty+1][tx] == 0: mask |= 4  # S
        if tx > 0 and self.solid[ty][tx-1] == 0: mask |= 8  # W
        return mask

    def get_diagonal_mask(self, tx, ty):
        """Get which diagonal corners have floor (for rounded corners)
        NW=1, NE=2, SW=4, SE=8"""
        mask = 0
        if tx > 0 and ty > 0 and self.solid[ty-1][tx-1] == 0: mask |= 1  # NW
        if tx < self.w-1 and ty > 0 and self.solid[ty-1][tx+1] == 0: mask |= 2  # NE
        if tx > 0 and ty < self.h-1 and self.solid[ty+1][tx-1] == 0: mask |= 4  # SW
        if tx < self.w-1 and ty < self.h-1 and self.solid[ty+1][tx+1] == 0: mask |= 8  # SE
        return mask

    def is_interior_wall(self, tx, ty):
        """Check if wall is completely surrounded by walls (no floor neighbors)"""
        if not self.solid[ty][tx]: return False
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0: continue
                nx, ny = tx + dx, ty + dy
                if 0 <= nx < self.w and 0 <= ny < self.h:
                    if self.solid[ny][nx] == 0:
                        return False
        return True

    def carve(self, tx, ty):
        if 0 <= tx < self.w and 0 <= ty < self.h:
            self.solid[ty][tx] = 0

    def _rebuild_floor(self):
        self.floor.clear()
        for ty in range(1, self.h-1):
            for tx in range(1, self.w-1):
                if self.solid[ty][tx] == 0:
                    self.floor.append((tx, ty))

    def _gen(self):
        """Generate spaceship/hive city layout with hallways and rooms"""
        cx, cy = self.w//2, self.h//2

        # Parameters for layout
        hall_width = 3  # corridor width
        room_spacing_x = 16  # distance between vertical corridors
        room_spacing_y = 12  # distance between horizontal corridors

        # Create main grid of hallways
        # Horizontal corridors
        for gy in range(3, self.h - 3, room_spacing_y):
            # Add some variation to corridor positions
            y_offset = random.randint(-1, 1)
            corridor_y = gy + y_offset
            if corridor_y < 3 or corridor_y > self.h - 4:
                continue
            # Carve horizontal corridor
            for tx in range(3, self.w - 3):
                for w in range(hall_width):
                    self.carve(tx, corridor_y + w)

        # Vertical corridors
        for gx in range(4, self.w - 4, room_spacing_x):
            x_offset = random.randint(-1, 1)
            corridor_x = gx + x_offset
            if corridor_x < 3 or corridor_x > self.w - 5:
                continue
            # Carve vertical corridor
            for ty in range(3, self.h - 3):
                for w in range(hall_width):
                    self.carve(corridor_x + w, ty)

        # Create rooms at some intersections and along corridors
        self.rooms = []  # Store room positions for prop placement
        for gy in range(3, self.h - 8, room_spacing_y):
            for gx in range(4, self.w - 10, room_spacing_x):
                if random.random() < 0.7:  # 70% chance for a room
                    room_w = random.randint(6, 10)
                    room_h = random.randint(5, 8)
                    rx = gx + random.randint(-2, 2)
                    ry = gy + random.randint(-1, 1)
                    # Carve room
                    for ty in range(ry, min(ry + room_h, self.h - 2)):
                        for tx in range(rx, min(rx + room_w, self.w - 2)):
                            if tx > 1 and ty > 1:
                                self.carve(tx, ty)
                    self.rooms.append((rx, ry, room_w, room_h))

        # Create central command room (larger)
        for oy in range(-5, 6):
            for ox in range(-6, 7):
                self.carve(cx + ox, cy + oy)
        self.rooms.append((cx - 6, cy - 5, 13, 11))

        # Add some connecting corridors to ensure connectivity
        # Connect rooms that might be isolated
        for _ in range(15):
            if len(self.rooms) < 2:
                break
            r1 = random.choice(self.rooms)
            r2 = random.choice(self.rooms)
            x1, y1 = r1[0] + r1[2]//2, r1[1] + r1[3]//2
            x2, y2 = r2[0] + r2[2]//2, r2[1] + r2[3]//2
            # L-shaped corridor
            for tx in range(min(x1, x2), max(x1, x2) + 1):
                for w in range(hall_width):
                    if 1 < y1 + w < self.h - 1:
                        self.carve(tx, y1 + w)
            for ty in range(min(y1, y2), max(y1, y2) + 1):
                for w in range(hall_width):
                    if 1 < x2 + w < self.w - 1:
                        self.carve(x2 + w, ty)

        self._rebuild_floor()
        self._place_props()

    def _place_props(self):
        """Place interior props in rooms: computers, columns, containers, ammo"""
        cx, cy = self.w//2, self.h//2

        for rx, ry, rw, rh in self.rooms:
            # Skip very small rooms
            if rw < 5 or rh < 4:
                continue

            # Determine room type based on position/size
            is_central = abs(rx + rw//2 - cx) < 8 and abs(ry + rh//2 - cy) < 6
            room_type = random.choice(['command', 'storage', 'armory', 'machinery']) if not is_central else 'command'

            if room_type == 'command':
                # Computer stations along walls
                # Top wall computers
                for x in range(rx + 2, rx + rw - 2, 3):
                    if self.solid[ry][x] == 0 and ry > 0 and self.solid[ry-1][x] == 1:
                        self.props[(x, ry)] = 'computer_n'
                # Bottom wall computers
                for x in range(rx + 2, rx + rw - 2, 3):
                    if ry + rh - 1 < self.h and self.solid[ry + rh - 1][x] == 0:
                        if ry + rh < self.h and self.solid[ry + rh][x] == 1:
                            self.props[(x, ry + rh - 1)] = 'computer_s'
                # Central holotable in larger rooms
                if rw >= 8 and rh >= 6:
                    hx, hy = rx + rw//2, ry + rh//2
                    if self.solid[hy][hx] == 0:
                        self.props[(hx, hy)] = 'holotable'

            elif room_type == 'storage':
                # Storage containers in grid pattern
                for y in range(ry + 1, ry + rh - 1, 2):
                    for x in range(rx + 1, rx + rw - 1, 3):
                        if self.solid[y][x] == 0 and random.random() < 0.6:
                            self.props[(x, y)] = random.choice(['container', 'crate', 'barrel'])

            elif room_type == 'armory':
                # Ammo crates and weapon racks
                for x in range(rx + 1, rx + rw - 1, 2):
                    if self.solid[ry + 1][x] == 0 and random.random() < 0.7:
                        self.props[(x, ry + 1)] = 'ammo_crate'
                for x in range(rx + 1, rx + rw - 1, 2):
                    if ry + rh - 2 < self.h and self.solid[ry + rh - 2][x] == 0 and random.random() < 0.5:
                        self.props[(x, ry + rh - 2)] = 'weapon_rack'

            elif room_type == 'machinery':
                # Columns and pipes
                # Corner columns
                corners = [(rx + 1, ry + 1), (rx + rw - 2, ry + 1),
                          (rx + 1, ry + rh - 2), (rx + rw - 2, ry + rh - 2)]
                for px, py in corners:
                    if 0 <= py < self.h and 0 <= px < self.w and self.solid[py][px] == 0:
                        self.props[(px, py)] = 'column'
                # Central machinery
                if rw >= 6 and rh >= 5:
                    mx, my = rx + rw//2, ry + rh//2
                    if self.solid[my][mx] == 0:
                        self.props[(mx, my)] = 'generator'

        # Add some props in corridors (less dense)
        for tx, ty in self.floor:
            if (tx, ty) in self.props:
                continue
            # Check if this is a corridor (narrow area)
            neighbors_floor = sum(1 for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]
                                 if 0 <= tx+dx < self.w and 0 <= ty+dy < self.h
                                 and self.solid[ty+dy][tx+dx] == 0)
            if neighbors_floor <= 2 and random.random() < 0.02:
                # Corridor props
                self.props[(tx, ty)] = random.choice(['light_post', 'pipe_vertical', 'small_crate'])

    def _assign_variants(self):
        """Randomly assign tile variants, place decals, and wall elements"""
        for ty in range(self.h):
            for tx in range(self.w):
                # Assign random variants (0-7 for 8 variants)
                self.wall_variants[ty][tx] = random.randint(0, 7)
                self.floor_variants[ty][tx] = random.randint(0, 7)

                if self.solid[ty][tx] == 1:  # Wall tiles
                    # Place wall elements on edge walls (not interior)
                    if not self.is_interior_wall(tx, ty) and random.random() < 0.08:
                        # 0=computer, 1=pipes_h, 2=pipes_v, 3=vent, 4=panel, 5=skull, 6=warning, 7=aquila
                        self.wall_elements[(tx, ty)] = random.randint(0, 7)

                if self.solid[ty][tx] == 0:  # Floor tiles
                    # Occasionally place decals on floor tiles
                    if random.random() < 0.05:
                        decal_types = ["shell_casing", "debris", "blood_pool", "oil_spill", "scorch_mark"]
                        self.tile_decals[(tx, ty)] = random.choice(decal_types)

                    # Occasionally place hazard tiles
                    if random.random() < 0.02:
                        hazard_types = ["toxic", "electric", "heat"]
                        self.hazard_tiles[(tx, ty)] = random.choice(hazard_types)

                    # Occasionally place animated tiles
                    if random.random() < 0.03:
                        anim_types = ["flickering_light", "steam_vent", "electrical_panel"]
                        self.animated_tiles[(tx, ty)] = random.choice(anim_types)

    def is_solid_px(self, px, py):
        tx, ty = int(px // TILE), int(py // TILE)
        if tx < 0 or ty < 0 or tx >= self.w or ty >= self.h:
            return True
        return self.solid[ty][tx] == 1

    def rand_floor_far(self, px, py, min_d=SAFE_SPAWN_DIST):
        min_d2 = min_d * min_d
        best = None
        bestd = -1
        for _ in range(140):
            tx, ty = random.choice(self.floor)
            fx, fy = tx*TILE + TILE/2, ty*TILE + TILE/2
            d = dist2(fx, fy, px, py)
            if d >= min_d2:
                return fx, fy
            if d > bestd:
                bestd = d
                best = (fx, fy)
        return best if best else (px, py)

# -------------------- ENTITIES --------------------
class Entity:
    def __init__(self, x, y, r=14):
        self.x=x; self.y=y
        self.vx=0.0; self.vy=0.0
        self.r=r

    def try_move(self, arena: Arena, dx, dy):
        nx = self.x + dx
        ny = self.y + dy
        r = self.r

        # X
        if not (arena.is_solid_px(nx-r, self.y-r) or arena.is_solid_px(nx+r, self.y-r) or
                arena.is_solid_px(nx-r, self.y+r) or arena.is_solid_px(nx+r, self.y+r)):
            self.x = nx
        # Y
        if not (arena.is_solid_px(self.x-r, ny-r) or arena.is_solid_px(self.x+r, ny-r) or
                arena.is_solid_px(self.x-r, ny+r) or arena.is_solid_px(self.x+r, ny+r)):
            self.y = ny

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, r=14)
        self.hp=12; self.maxhp=12
        self.cd=0
        self.ifr=0
        self.dmg_cd=0
        self.face=(1,0)
        self.aim=(1,0)
        self.aim_tgt=None
        self.aim_hold=0
        self.walk_phase=0.0
        self.shoot_flash=0.0
        self.step_t=0  # footstep timer for subtle movement shake
        # Shield system
        self.shield = 15
        self.max_shield = 15
        self.shield_regen_timer = 0.0
        self.is_shooting = False  # track if player shot this frame
        # Points and combo system
        self.points = 0
        self.combo = 0
        self.combo_timer = 0.0
        # Stim packs (auto-revive)
        self.stims_used = 0
        # Grenades
        self.grenades = MAX_GRENADES
        self.grenade_cd = 0.0

class Enemy(Entity):
    def __init__(self, x, y, kind="grunt", wave=1):
        super().__init__(x, y, r=14)
        base_sp = 1.6 + wave*0.05
        base_hp = 2 + int(wave*0.20)
        self.kind=kind
        self.hit_cd=0
        self.dmg=1
        self.hp=base_hp
        self.spd=base_sp
        self.shoot_cd = random.uniform(0.8, 1.6)
        # Knockback velocity (for smooth bounce)
        self.knock_vx = 0.0
        self.knock_vy = 0.0

        if kind=="runner":
            self.spd*=1.25; self.hp=max(1,self.hp-1)
        elif kind=="shooter":
            self.spd*=0.92; self.hp+=1
            self.shoot_cd = random.uniform(0.6, 1.2)
        elif kind=="brute":
            self.spd*=0.78; self.hp+=3; self.dmg=2

class Bullet:
    def __init__(self, x, y, vx, vy, life=0.8, owner="player"):
        self.x=x; self.y=y
        self.vx=vx; self.vy=vy
        self.life=life
        self.owner=owner

class Pickup:
    def __init__(self, x, y, kind="health"):
        self.x = x
        self.y = y
        self.kind = kind  # "health", "shield", or "grenade"
        self.life = 15.0  # despawn after 15 seconds

class Explosion:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.frame = 0
        self.life = 0.5  # seconds for full animation

class VFX:
    def __init__(self, x, y, kind="smoke"):
        self.x = x
        self.y = y
        self.kind = kind  # "smoke" or "shockwave"
        self.frame = 0
        self.life = 0.4 if kind == "smoke" else 0.3

# -------------------- DIRECTOR --------------------
class Director:
    def __init__(self):
        self.wave=1
        self.budget=0.0
        self.state="build"
        self.t=0.0
        self.spawn_cd=0.0
        self.intensity=1.0

    def tick(self, dt, arena, player, enemies, camera):
        self.t += dt

        # budget + intensity
        self.intensity = min(3.0, self.intensity + dt*0.006)
        self.budget += dt * (0.8 + self.wave*0.18) * self.intensity

        # state machine
        if self.state=="build" and self.t>=5.2:
            self.state="push"; self.t=0
        elif self.state=="push" and self.t>=2.0:
            self.state="breather"; self.t=0
        elif self.state=="breather" and self.t>=1.6:
            self.state="spike"; self.t=0
        elif self.state=="spike" and self.t>=1.5:
            self.state="build"; self.t=0; self.wave += 1

        # pressure gate
        pressure = sum(1 for e in enemies if dist2(e.x,e.y,player.x,player.y) < PRESSURE_RADIUS**2)
        if pressure >= PRESSURE_CAP:
            return

        self.spawn_cd -= dt
        if self.spawn_cd > 0:
            return

        sx, sy = arena.rand_floor_far(player.x, player.y, min_d=SAFE_SPAWN_DIST)

        kind="grunt"
        cost=1

        if self.state=="build":
            if random.random() < 0.22: kind="runner"
            self.spawn_cd = 0.24

        elif self.state=="push":
            kind = "runner" if random.random() < 0.40 else "grunt"
            self.spawn_cd = 0.17
            camera.add_shake(0.8, 6)

        elif self.state=="breather":
            if random.random() < 0.18:
                kind="grunt"
                self.spawn_cd=0.35
            else:
                self.spawn_cd=0.20
                return

        elif self.state=="spike":
            if random.random() < 0.55:
                kind="shooter"; cost=2
            else:
                kind="brute"; cost=4
            self.spawn_cd=0.32
            camera.add_shake(1.6, 10)

        if self.budget >= cost:
            self.budget -= cost
            enemies.append(Enemy(sx, sy, kind=kind, wave=self.wave))

# -------------------- AIM ASSIST --------------------
def pick_aim_target(player, enemies, rng=AIM_RANGE, cone=AIM_CONE):
    best=None
    bestscore=-1e9
    fx, fy = player.face
    for e in enemies:
        dx, dy = e.x-player.x, e.y-player.y
        ux, uy, d = norm(dx, dy)
        if d <= rng:
            infront = ux*fx + uy*fy
            if infront >= (1-cone):
                kindw = 0.0
                if e.kind=="shooter": kindw=0.25
                if e.kind=="brute": kindw=0.35
                score = infront*2 - (d/rng) + kindw
                if score > bestscore:
                    bestscore=score
                    best=e
    return best

# -------------------- RENDER HELPERS --------------------
def blit_center(screen, img, x, y):
    r = img.get_rect(center=(x, y))
    screen.blit(img, r)

def draw_placeholder(screen, x, y, color, size=34):
    r = pg.Rect(0,0,size,size); r.center=(x,y)
    pg.draw.rect(screen, color, r, border_radius=6)
    pg.draw.rect(screen, (0,0,0), r, 2, border_radius=6)

# -------------------- MAIN --------------------
def main():
    pg.init()
    screen = pg.display.set_mode((W,H))
    clock = pg.time.Clock()
    pg.display.set_caption("Hive City Rampage (Pygame)")

    font = pg.font.Font(None, 26)

    assets = SpriteBank(os.path.join(os.path.dirname(__file__), "assets"))
    # These can be missing; game will fallback to placeholders
    assets.load_anim("marine_idle", "marine_idle.png", frames=1, fps=SPR_FPS_IDLE)
    assets.load_anim("marine_walk", "marine_walk.png", frames=2, fps=SPR_FPS_WALK)
    assets.load_anim("marine_shoot", "marine_shoot.png", frames=4, fps=12)

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
        for i in range(16):
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

    # Slice wall elements (computer, pipes_h, pipes_v, vent, panel, skull, warning, aquila)
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

    arena = Arena()
    player = Player(arena.w*TILE/2, arena.h*TILE/2)
    camera = Camera()
    director = Director()
    enemies=[]
    bullets=[]
    pickups=[]
    explosions=[]
    vfx=[]

    # Create AnimatedTile instances for the arena
    animated_tile_instances = {}
    for (tx, ty), anim_type in arena.animated_tiles.items():
        if anim_type in animated_tile_data:
            frames, fps = animated_tile_data[anim_type]
            animated_tile_instances[(tx, ty)] = AnimatedTile(frames, fps)

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

    running=True
    while running:
        dt = clock.tick(FPS) / 1000.0
        fps = clock.get_fps()

        for ev in pg.event.get():
            if ev.type == pg.QUIT:
                running=False
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

        # ---------------- UPDATE ----------------
        if player.hp > 0:
            ax = (keys[pg.K_d]-keys[pg.K_a])
            ay = (keys[pg.K_s]-keys[pg.K_w])

            if ax or ay:
                sx = 1 if ax>0 else -1 if ax<0 else 0
                sy = 1 if ay>0 else -1 if ay<0 else 0
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

            moving = (abs(player.vx)+abs(player.vy)) > 60  # adjusted for higher speed
            if moving:
                player.walk_phase += dt
                # Footstep shake (matching PICO-8 prototype)
                player.step_t += 1
                if player.step_t >= 14:
                    player.step_t = 0
                    camera.add_shake(0.6, 4)  # subtle footstep shake
            else:
                player.step_t = 0

            # aim with mouse
            mx, my = pg.mouse.get_pos()
            # Convert screen position to world position
            world_mx = mx + camera.x - camera.frame_shake_x
            world_my = my + camera.y - camera.frame_shake_y
            # Direction from player to mouse
            ux, uy, _ = norm(world_mx - player.x, world_my - player.y)
            player.aim = (ux, uy)
            # Update face direction to match aim
            player.face = (1 if ux > 0 else -1, 0)

            # shooting (left mouse button)
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

        # director
        prev_wave = director.wave
        director.tick(dt, arena, player, enemies, camera)

        # Wave completion bonus
        if director.wave > prev_wave and player.hp > 0:
            wave_bonus = WAVE_BONUS_BASE * prev_wave
            player.points += wave_bonus

        # bullets update
        for b in bullets[:]:
            b.x += b.vx * dt
            b.y += b.vy * dt
            b.life -= dt
            if b.life <= 0 or arena.is_solid_px(b.x, b.y):
                bullets.remove(b); continue

            if b.owner == "player":
                for e in enemies:
                    if dist2(b.x, b.y, e.x, e.y) < (18**2):
                        e.hp -= 1
                        camera.add_shake(0.9, 6)
                        if b in bullets: bullets.remove(b)
                        break
            else:
                # enemy bullet hits player - damages shield first (3 per bullet)
                if player.hp > 0 and dist2(b.x, b.y, player.x, player.y) < (18**2) and player.ifr <= 0:
                    if player.shield > 0:
                        player.shield = max(0, player.shield - 3)
                    else:
                        player.hp -= 1
                    player.ifr = IFRAMES_FR
                    camera.add_shake(2.6, 10)
                    if b in bullets: bullets.remove(b)

        # enemies update
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

            # separation from other enemies (stronger for non-runners)
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

            # melee contact damage with shield system, bounce-back, and auto-damage
            if e.hit_cd > 0: e.hit_cd -= 1
            if player.hp > 0 and dist2(e.x,e.y,player.x,player.y) < (22**2) and e.hit_cd<=0 and player.ifr<=0 and player.dmg_cd<=0:
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

            # shooter bullets
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

        # camera follow
        camera.update(player.x - W/2, player.y - H/2)

        # update anims
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

        # ---------------- DRAW ----------------
        screen.fill((12, 10, 8))  # Warm dark background

        # draw tiles (visible window)
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
                            pg.draw.rect(screen, (45,45,52), r)
                    elif arena.is_interior_wall(tx, ty):
                        # Interior wall (surrounded by walls) - dark
                        if terrain_interior:
                            screen.blit(terrain_interior, r)
                        else:
                            pg.draw.rect(screen, (12,12,15), r)
                    elif autotile_walls:
                        # Edge wall - use autotile based on neighbors
                        mask = arena.get_neighbor_mask(tx, ty)
                        if mask < len(autotile_walls):
                            screen.blit(autotile_walls[mask], r)
                        else:
                            pg.draw.rect(screen, (45,45,52), r)
                    else:
                        pg.draw.rect(screen, (45,45,52), r)
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
                                pg.draw.rect(screen, (18,18,22), r)

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
                                pg.draw.rect(screen, (18,18,22), r)

                    # Regular floor tile
                    else:
                        if floor_tiles:
                            variant_idx = arena.floor_variants[ty][tx] % len(floor_tiles)
                            screen.blit(floor_tiles[variant_idx], r)
                        else:
                            pg.draw.rect(screen, (18,18,22), r)

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

        # bullets
        for b in bullets:
            sx, sy = camera.apply_xy(b.x, b.y)
            if b.owner == "player" and player_bullet:
                blit_center(screen, player_bullet, sx, sy)
            elif b.owner == "enemy" and enemy_bullet:
                blit_center(screen, enemy_bullet, sx, sy)
            else:
                color = (255,210,80) if b.owner=="player" else (255,80,110)
                pg.draw.circle(screen, color, (int(sx), int(sy)), 4)

        # pickups
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

        # enemies
        for e in enemies:
            sx, sy = camera.apply_xy(e.x, e.y)
            img = enemy_walk_anims[e.kind].frame()
            if img:
                # Flip sprite if moving left (toward player)
                if player.x < e.x:
                    img = pg.transform.flip(img, True, False)
                blit_center(screen, img, sx, sy)
            else:
                color = (170,90,90)
                if e.kind=="runner": color=(200,120,120)
                if e.kind=="shooter": color=(150,120,200)
                if e.kind=="brute": color=(220,170,90)
                draw_placeholder(screen, sx, sy, color, size=48)

        # player
        psx, psy = camera.apply_xy(player.x, player.y)
        moving = (abs(player.vx)+abs(player.vy)) > 60  # adjusted for higher speed
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
            draw_placeholder(screen, psx, psy, (90,180,255), size=50)

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

        # UI - warm dark panel
        ui = pg.Rect(0,0,W,74)
        pg.draw.rect(screen, (28, 24, 22), ui)
        pg.draw.line(screen, (65, 55, 45), (0, 73), (W, 73), 2)

        # HP bar - bright red/orange
        hpw = int((max(0, player.hp)/player.maxhp) * 200)
        pg.draw.rect(screen, (195, 55, 45), (24,10,hpw,16))
        pg.draw.rect(screen, (145, 125, 95), (24,10,200,16), 2)

        # Shield bar (below HP) - bright cyan/blue
        shw = int((max(0, player.shield)/player.max_shield) * 200)
        shield_color = (65, 165, 215) if player.shield > 0 else (45, 42, 38)
        pg.draw.rect(screen, shield_color, (24,30,shw,12))
        pg.draw.rect(screen, (95, 125, 145), (24,30,200,12), 2)

        # Labels - warm amber text
        screen.blit(font.render("HP", True, (215, 185, 125)), (232, 10))
        screen.blit(font.render("SHIELD", True, (145, 175, 195)), (232, 28))

        # Points display (right side)
        points_text = f"SCORE: {player.points}"
        screen.blit(font.render(points_text, True, (255, 220, 100)), (W - 180, 10))

        # Combo display (shows when active)
        if player.combo > 0:
            combo_color = (255, 180, 80) if player.combo < 5 else (255, 100, 100)
            combo_text = f"x{player.combo + 1} COMBO!"
            screen.blit(font.render(combo_text, True, combo_color), (W - 180, 30))

        # Grenades remaining (below combo)
        grenade_text = f"GRENADES: {player.grenades}"
        grenade_color = (150, 200, 150) if player.grenades > 0 else (100, 100, 100)
        screen.blit(font.render(grenade_text, True, grenade_color), (W - 200, 48))

        # Stim packs remaining (bottom right of UI)
        stims_left = MAX_STIMS - player.stims_used
        stim_text = f"STIMS: {stims_left}"
        stim_color = (100, 255, 100) if stims_left > 1 else (255, 100, 100)
        screen.blit(font.render(stim_text, True, stim_color), (W - 90, 48))

        info = f"WAVE {director.wave}   E:{len(enemies)}   {director.state}"
        screen.blit(font.render(info, True, (195, 175, 145)), (330, 50))

        if player.hp <= 0:
            msg = font.render(f"GAME OVER - FINAL SCORE: {player.points} - press X to restart", True, (255,220,220))
            screen.blit(msg, (W//2 - msg.get_width()//2, 78))

        pg.display.flip()

    pg.quit()

if __name__ == "__main__":
    main()
