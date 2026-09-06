"""
Constants for Hive City Rampage
All gameplay configuration in one place for easy tuning
"""

# -------------------- DISPLAY --------------------
W, H = 960, 540
FPS = 60
TILE = 32
WORLD_W, WORLD_H = 120, 90  # in tiles

# -------------------- ANIMATION --------------------
SPR_FPS_IDLE = 6
SPR_FPS_WALK = 10

# -------------------- PLAYER MOVEMENT --------------------
PLAYER_ACC = 25.0
PLAYER_MAX = 450.0
PLAYER_FRIC = 0.82
PLAYER_TURN_DRAG = 0.78
SHOT_COOLDOWN_FR = 6

# -------------------- AIM ASSIST --------------------
AIM_RANGE = 10 * TILE
AIM_CONE = 0.45
AIM_SMOOTH = 0.16
AIM_HOLD_FR = 10

# -------------------- SPAWNING & FAIRNESS --------------------
SAFE_SPAWN_DIST = 8 * TILE
PRESSURE_RADIUS = 3 * TILE
PRESSURE_CAP = 4
GLOBAL_DMG_CD_FR = 12
IFRAMES_FR = 18

# -------------------- ENEMY COMBAT --------------------
ENEMY_BULLET_SPEED = 250.0
ENEMY_BULLET_LIFE = 1.2
ENEMY_SHOOT_RANGE = 9 * TILE

# -------------------- SHIELD & HEALTH --------------------
SHIELD_REGEN_DELAY = 1.2  # seconds after shooting before regen starts
SHIELD_REGEN_RATE = 2.0   # shield points per second

# -------------------- PICKUPS --------------------
PICKUP_RADIUS = 24
PICKUP_SPAWN_CHANCE = 0.25  # chance per enemy kill
HEALTH_PICKUP_AMOUNT = 3
SHIELD_PICKUP_AMOUNT = 5

# -------------------- GRENADES --------------------
GRENADE_COOLDOWN = 3.0  # seconds between grenades
GRENADE_RADIUS = 240  # explosion radius
GRENADE_DAMAGE = 4  # damage to enemies
GRENADE_KNOCKBACK = 800  # knockback force
MAX_GRENADES = 5  # starting grenades
GRENADE_PICKUP_CHANCE = 0.08  # chance to drop grenade pickup

# -------------------- SCORING --------------------
POINTS_GRUNT = 10
POINTS_RUNNER = 15
POINTS_SHOOTER = 25
POINTS_BRUTE = 50
COMBO_WINDOW = 1.5  # seconds to chain kills
COMBO_MULTIPLIER = 0.5  # bonus per combo level (1.0, 1.5, 2.0, ...)
WAVE_BONUS_BASE = 100  # base points per wave completed

# -------------------- STIM PACKS --------------------
MAX_STIMS = 3