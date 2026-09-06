"""
World generation and camera system for Hive City Rampage
Handles level generation, camera viewport, and collision detection
"""

import math
import random
from constants import TILE, WORLD_W, WORLD_H, SAFE_SPAWN_DIST
from utils import dist2


class Camera:
    """Camera with smooth follow and screen shake effects"""
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
        """Add screen shake effect"""
        self.shake_pow = min(18.0, self.shake_pow + pow_)
        self.shake_t = max(self.shake_t, t)
        self.shake_seed += 1

    def update(self, target_x, target_y):
        """Update camera position with smooth follow"""
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
        """Convert world coordinates to screen coordinates"""
        return x - self.x + self.frame_shake_x, y - self.y + self.frame_shake_y


class Arena:
    """Procedural level generation with rooms, hallways, and props"""
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
        """Carve a floor tile at position"""
        if 0 <= tx < self.w and 0 <= ty < self.h:
            self.solid[ty][tx] = 0

    def _rebuild_floor(self):
        """Rebuild list of floor tiles"""
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
        """Check if pixel coordinates are solid"""
        tx, ty = int(px // TILE), int(py // TILE)
        if tx < 0 or ty < 0 or tx >= self.w or ty >= self.h:
            return True
        return self.solid[ty][tx] == 1

    def rand_floor_far(self, px, py, min_d=SAFE_SPAWN_DIST):
        """Find a random floor tile far from given position"""
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