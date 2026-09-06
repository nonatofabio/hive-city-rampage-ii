"""
Wave spawning director for Hive City Rampage
Manages enemy spawning waves and difficulty progression
"""

import random
from constants import *
from entities import Enemy
from utils import dist2


class Director:
    """Wave-based enemy spawning with state machine"""
    def __init__(self):
        self.wave = 1
        self.budget = 0.0
        self.state = "build"
        self.t = 0.0
        self.spawn_cd = 0.0
        self.intensity = 1.0

    def tick(self, dt, arena, player, enemies, camera):
        """Update director state and spawn enemies"""
        self.t += dt

        # Budget and intensity scaling
        self.intensity = min(3.0, self.intensity + dt*0.006)
        self.budget += dt * (0.8 + self.wave*0.18) * self.intensity

        # State machine transitions
        if self.state == "build" and self.t >= 5.2:
            self.state = "push"
            self.t = 0
        elif self.state == "push" and self.t >= 2.0:
            self.state = "breather"
            self.t = 0
        elif self.state == "breather" and self.t >= 1.6:
            self.state = "spike"
            self.t = 0
        elif self.state == "spike" and self.t >= 1.5:
            self.state = "build"
            self.t = 0
            self.wave += 1

        # Pressure gate - limit enemies near player
        pressure = sum(1 for e in enemies if dist2(e.x, e.y, player.x, player.y) < PRESSURE_RADIUS**2)
        if pressure >= PRESSURE_CAP:
            return

        self.spawn_cd -= dt
        if self.spawn_cd > 0:
            return

        sx, sy = arena.rand_floor_far(player.x, player.y, min_d=SAFE_SPAWN_DIST)

        kind = "grunt"
        cost = 1

        # State-specific spawning
        if self.state == "build":
            if random.random() < 0.22:
                kind = "runner"
            self.spawn_cd = 0.24

        elif self.state == "push":
            kind = "runner" if random.random() < 0.40 else "grunt"
            self.spawn_cd = 0.17
            camera.add_shake(0.8, 6)

        elif self.state == "breather":
            if random.random() < 0.18:
                kind = "grunt"
                self.spawn_cd = 0.35
            else:
                self.spawn_cd = 0.20
                return

        elif self.state == "spike":
            if random.random() < 0.55:
                kind = "shooter"
                cost = 2
            else:
                kind = "brute"
                cost = 4
            self.spawn_cd = 0.32
            camera.add_shake(1.6, 10)

        # Spawn if budget allows
        if self.budget >= cost:
            self.budget -= cost
            enemies.append(Enemy(sx, sy, kind=kind, wave=self.wave))