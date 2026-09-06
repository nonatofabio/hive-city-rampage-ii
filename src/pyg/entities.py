"""
Entity classes for Hive City Rampage
Player, enemies, projectiles, pickups, and effects
"""

import random
from constants import *


class Entity:
    """Base entity class with physics and collision"""
    def __init__(self, x, y, r=14):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.r = r  # collision radius

    def try_move(self, arena, dx, dy):
        """Try to move with collision detection"""
        nx = self.x + dx
        ny = self.y + dy
        r = self.r

        # X movement
        if not (arena.is_solid_px(nx-r, self.y-r) or arena.is_solid_px(nx+r, self.y-r) or
                arena.is_solid_px(nx-r, self.y+r) or arena.is_solid_px(nx+r, self.y+r)):
            self.x = nx
        # Y movement
        if not (arena.is_solid_px(self.x-r, ny-r) or arena.is_solid_px(self.x+r, ny-r) or
                arena.is_solid_px(self.x-r, ny+r) or arena.is_solid_px(self.x+r, ny+r)):
            self.y = ny


class Player(Entity):
    """Player character with weapons, shield, and scoring"""
    def __init__(self, x, y):
        super().__init__(x, y, r=14)
        # Health
        self.hp = 12
        self.maxhp = 12
        # Combat
        self.cd = 0  # shoot cooldown
        self.ifr = 0  # invincibility frames
        self.dmg_cd = 0  # damage cooldown
        # Movement and aim
        self.face = (1, 0)
        self.aim = (1, 0)
        self.aim_tgt = None
        self.aim_hold = 0
        self.walk_phase = 0.0
        self.shoot_flash = 0.0
        self.step_t = 0  # footstep timer for subtle movement shake
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
    """Enemy with different types and behaviors"""
    def __init__(self, x, y, kind="grunt", wave=1):
        super().__init__(x, y, r=14)
        base_sp = 1.6 + wave*0.05
        base_hp = 2 + int(wave*0.20)
        self.kind = kind
        self.hit_cd = 0
        self.dmg = 1
        self.hp = base_hp
        self.spd = base_sp
        self.shoot_cd = random.uniform(0.8, 1.6)
        # Knockback velocity (for smooth bounce)
        self.knock_vx = 0.0
        self.knock_vy = 0.0

        # Type-specific stats
        if kind == "runner":
            self.spd *= 1.25
            self.hp = max(1, self.hp-1)
        elif kind == "shooter":
            self.spd *= 0.92
            self.hp += 1
            self.shoot_cd = random.uniform(0.6, 1.2)
        elif kind == "brute":
            self.spd *= 0.78
            self.hp += 3
            self.dmg = 2


class Bullet:
    """Projectile class"""
    def __init__(self, x, y, vx, vy, life=0.8, owner="player"):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.owner = owner


class Pickup:
    """Collectible items (health, shield, grenade)"""
    def __init__(self, x, y, kind="health"):
        self.x = x
        self.y = y
        self.kind = kind  # "health", "shield", or "grenade"
        self.life = 15.0  # despawn after 15 seconds


class Explosion:
    """Explosion animation container"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.frame = 0
        self.life = 0.5  # seconds for full animation


class VFX:
    """Visual effects (smoke, shockwave)"""
    def __init__(self, x, y, kind="smoke"):
        self.x = x
        self.y = y
        self.kind = kind  # "smoke" or "shockwave"
        self.frame = 0
        self.life = 0.4 if kind == "smoke" else 0.3