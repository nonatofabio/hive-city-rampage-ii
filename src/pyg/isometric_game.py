"""Ashgate siege: an isometric arcade campaign for Hive City Rampage.

Run hive_city_rampage.py; use --classic for the original survival arena.
Simulation uses flat world coordinates; projection is rendering-only.
"""
import argparse
from dataclasses import dataclass
import math
from pathlib import Path
import random

import pygame as pg
from isometric_art import facade, facade_anchor, prop, poly, INK, GOLD
from siege_audio import Audio
from siege_hud import status_hud
from siege_motion import animated_sprite, muzzle_offset, aim_pose, direction_angle, solve_weapon_aim, ejection_offset, SIZES
from siege_effects import effect, death_sprite, add_light, shadow_stamp, faded, weapon_effect, casing_sprite, BLAST_DURATION, DEATH_DURATION, CORPSE_DURATION

WIDTH, HEIGHT = 960, 540
LENGTH, DEPTH = 2400, 700
V = pg.Vector2
FIRE_POSITIONS=((170,55),(550,40),(930,65),(1470,35),(1870,60),(2260,45),(780,640),(1640,645))


def project(p):
    return V(p.x-p.y, (p.x+p.y)*.5)


def unproject(p):
    return V(p.x*.5+p.y, p.y-p.x*.5)


def unit(p):
    return p.normalize() if p.length_squared() > .001 else V(1, 0)


def segment_hit(a, b, center, radius):
    return segment_entry(a, b, center, radius) is not None


def segment_entry(a, b, center, radius):
    """Return first contact along a swept shot, including overlapping starts."""
    delta = b-a
    offset = a-center
    c = offset.length_squared()-radius*radius
    if c <= 0:
        return 0.
    length2 = delta.length_squared()
    if not length2:
        return None
    dot = offset.dot(delta)
    discriminant = dot*dot-length2*c
    if discriminant < 0:
        return None
    t = (-dot-math.sqrt(discriminant))/length2
    return t if 0 <= t <= 1 else None


@dataclass
class Actor:
    pos: V
    kind: str
    hp: float
    radius: float = 16
    cooldown: float = 0
    flash: float = 0
    phase: float = 0
    target: object = None
    moving: bool = False
    stride: float = 0.
    move_angle: float = 0.
    move_facing: int = 1.
    recoil: float = 0.
    facing: int = 1
    aim_angle: float = 0.
    aim_view: float = 0.


@dataclass
class Shot:
    pos: V
    velocity: V
    damage: float
    enemy: bool = False
    life: float = 1.1


class Siege:
    def __init__(self, seed=7, audio=None):
        self.rng = random.Random(seed)
        self.audio = audio
        self.player = Actor(V(320, 360), 'player', 100)
        self.shield = 60.
        self.hurt_timer = 0
        self.grenades = 5
        self.grenade_cd = 0
        self.dash_cd = 0
        self.dash_time = 0
        self.dash_direction = V(1, 0)
        self.enemies = []
        self.shots = []
        self.particles = []
        self.marks = []
        self.blasts = []
        self.deaths = []
        self.pickups = []
        self.grenade_flights = []
        self.casings = []
        self.cover = []
        self.relays = [Actor(V(x, y), 'relay', 170, 27) for x, y in ((650, 165), (1300, 510), (1930, 210))]
        self.fires = [V(x, y) for x, y in FIRE_POSITIONS]
        for x, y, kind in [(470, 530, 'crate'), (760, 340, 'crate'), (1050, 170, 'crate'), (1110, 200, 'crate'), (1550, 440, 'crate'), (1810, 500, 'crate'), (2100, 390, 'crate'), (560, 210, 'barrel'), (1200, 440, 'barrel'), (1740, 270, 'barrel')]:
            self.cover.append(Actor(V(x, y), kind, 65 if kind == 'crate' else 28, 29))
        self.time = 0.
        self.spawn_timer = 2.
        self.score = 0
        self.kills = 0
        self.combo = 0
        self.combo_timer = 0
        self.boss_spawned = False
        self.boss_defeated = False
        self.state = 'playing'
        self.camera = project(self.player.pos)-V(WIDTH*.38, HEIGHT*.48)
        self.shake = 0.
        self.message = 'ASHGATE // BREAK THE SIGNAL'
        self.message_timer = 4.
        self.aim = self.player.pos+V(200, 0)
        for i in range(14):
            self.spawn(V(590+i*38, 250+i%4*78), 'rifle' if i%3 == 0 else 'grunt')

    def sound(self, name, position=None, gain=1.):
        if self.audio:
            self.audio.play(name, position, self.player.pos, gain)

    @property
    def relays_down(self):
        return sum(r.hp <= 0 for r in self.relays)

    def spawn(self, pos, kind):
        hp = {'grunt': 45, 'rifle': 35, 'runner': 24, 'brute': 125, 'boss': 1800}[kind]
        enemy = Actor(V(pos), kind, hp, 52 if kind == 'boss' else 18, self.rng.uniform(.5, 2))
        enemy.stride = self.rng.random()
        self.enemies.append(enemy)
        return enemy

    def move(self, actor, delta):
        start = V(actor.pos)
        for axis in (0, 1):
            old = actor.pos[axis]
            actor.pos[axis] += delta[axis]
            actor.pos.x = max(35, min(LENGTH-35, actor.pos.x))
            actor.pos.y = max(85, min(DEPTH-55, actor.pos.y))
            if any(c.hp > 0 and (actor.pos-c.pos).length_squared() < (actor.radius+c.radius)**2 for c in self.cover+self.relays):
                actor.pos[axis] = old
        displacement=actor.pos-start
        distance = displacement.length()
        if actor.kind=='player' and distance>.001:
            travel=project(displacement)
            actor.move_facing=1 if travel.x>=0 else -1
            actor.move_angle=direction_angle(math.degrees(math.atan2(travel.y,abs(travel.x))))
        stride_length = 108 if actor.kind == 'boss' else 132 if actor.kind == 'player' else 64
        actor.stride += distance/stride_length
        return distance

    def burst(self, pos, count=15, color=(255, 161, 52), force=140):
        for _ in range(count):
            angle = self.rng.random()*math.tau
            velocity = V(math.cos(angle), math.sin(angle))*self.rng.uniform(20, force)
            self.particles.append([V(pos), velocity, self.rng.uniform(.18, .65), color, self.rng.randint(1, 4)])

    def damage_player(self, amount):
        if self.hurt_timer > 0 or self.dash_time > 0:
            return
        absorbed = min(self.shield, amount)
        self.shield -= absorbed
        self.player.hp -= amount-absorbed
        self.hurt_timer = .35
        self.player.flash = .15
        self.shake = 5
        if self.player.hp <= 0:
            self.state = 'dead'

    def hit(self, target, damage):
        if target.hp <= 0:
            return
        target.hp -= damage
        target.flash = .10
        self.burst(target.pos, 5, (218, 158, 88), 90)
        if target.hp > 0:
            return
        if target.kind in ('crate','barrel','relay'):
            self.marks.append((V(target.pos), target.kind))
        self.marks = self.marks[-180:]
        if target.kind == 'barrel':
            self.explode(target.pos, 155, 140)
        elif target.kind == 'relay':
            self.explode(target.pos, 120, 85)
            self.score += 750
            self.grenades = min(9, self.grenades+2)
            self.shield = min(60, self.shield+25)
            self.message = f'SIGNAL RELAY {self.relays_down}/3 SILENCED // +2 FRAGS'
            self.message_timer = 3.
        elif target in self.enemies:
            self.deaths.append([V(target.pos),target.kind,target.facing,0.])
            self.deaths=self.deaths[-64:]
            self.combo = self.combo+1 if self.combo_timer > 0 else 1
            self.combo_timer = 2.4
            self.score += (5000 if target.kind == 'boss' else 100)*min(5, self.combo)
            self.kills += 1
            if target.kind == 'boss':
                self.boss_defeated = True
                self.message = 'SIEGE WALKER DESTROYED // REACH EXTRACTION'
                self.message_timer = 5
                self.explode(target.pos, 210, 200)
            elif self.rng.random() < .25:
                self.pickups.append([V(target.pos), self.rng.choice(['health', 'shield', 'frag'])])

    def explode(self, pos, radius=160, damage=140):
        self.blasts.append([V(pos),0.,radius])
        self.blasts=self.blasts[-32:]
        self.burst(pos, 24, (255, 177, 66), 240)
        self.shake = 10
        for target in list(self.enemies)+self.cover+self.relays:
            distance = (target.pos-pos).length()
            if target.hp > 0 and distance < radius+target.radius:
                self.hit(target, damage*max(.3, 1-distance/(radius+target.radius)))
        if (self.player.pos-pos).length() < radius*.55:
            self.damage_player(18)
        self.marks.append((V(pos), 'scorch'))
        self.marks=self.marks[-180:]

    def grenade(self, aim):
        if self.grenades <= 0 or self.grenade_cd > 0 or self.state != 'playing':
            return
        delta = aim-self.player.pos
        if delta.length() > 430:
            delta.scale_to_length(430)
        self.grenade_flights.append([V(self.player.pos), self.player.pos+delta, 0.])
        self.grenades -= 1
        self.grenade_cd = .8

    def aim_weapon(self,actor,target):
        if actor.kind!='player':return
        actor.facing,raw=aim_pose(target-actor.pos,actor.facing)
        actor.aim_view=direction_angle(raw,actor.aim_view)
        actor.aim_view,actor.aim_angle=solve_weapon_aim(actor.stride,actor.moving,actor.facing,actor.aim_view,actor.recoil,self.time,project(target-actor.pos)-V(0,55))

    def fire_weapon(self, actor, aim, speed, damage, enemy=False):
        self.aim_weapon(actor,aim)
        offset = muzzle_offset(actor.kind,actor.stride,actor.moving,actor.facing,actor.aim_angle,actor.recoil,self.time,actor.aim_view if actor.kind=='player' else None)
        start = actor.pos+unproject(offset+V(0,55))
        # A barrel reaching through nearby cover must not bypass that cover.
        if any(c.hp > 0 and segment_hit(actor.pos,start,c.pos,c.radius) for c in self.cover+self.relays):
            start = V(actor.pos)
        self.shots.append(Shot(start,unit(aim-start)*speed,damage,enemy,2. if enemy else 1.1))

    def eject_casing(self,actor):
        port=ejection_offset(actor.kind,actor.stride,actor.moving,actor.facing,actor.aim_angle,actor.recoil,self.time,actor.aim_view)
        direction=unit(project(self.aim-actor.pos)-V(0,55)-port)
        normal=V(-direction.y,direction.x)
        position=actor.pos+unproject(port+V(0,55))
        self.casings.append([position,unproject(normal*75+direction*15),0.,55.,100.])

    def update(self, dt, movement=V(), aim=None, shooting=False, dash=False):
        if self.state != 'playing':
            return
        self.time += dt
        self.aim = V(aim) if aim is not None else self.aim
        for name in ('hurt_timer', 'grenade_cd', 'dash_cd', 'dash_time', 'combo_timer', 'message_timer'):
            setattr(self, name, max(0, getattr(self, name)-dt))
        self.player.flash = max(0, self.player.flash-dt)
        self.player.recoil = max(0., self.player.recoil-dt)
        self.player.cooldown = max(0, self.player.cooldown-dt)
        if self.hurt_timer == 0:
            self.shield = min(60, self.shield+dt*3)
        traveled = 0.
        if movement.length_squared():
            direction = unit(unproject(unit(movement)))
            if dash and self.dash_cd <= 0:
                self.dash_direction = direction
                self.dash_time = .16
                self.dash_cd = 2.2
            traveled += self.move(self.player, direction*180*dt)
        if self.dash_time > 0:
            traveled += self.move(self.player, self.dash_direction*500*dt)
        self.player.moving = traveled > .001
        self.aim_weapon(self.player,self.aim)
        if shooting and self.player.cooldown <= 0:
            self.player.cooldown = .105
            self.player.recoil = .105
            self.fire_weapon(self.player, self.aim, 950, 24)
            self.eject_casing(self.player)
            self.shake = max(self.shake, 1.5)
            self.sound('shot')
        self.spawn_timer -= dt
        if self.spawn_timer <= 0 and len(self.enemies) < 32 and not self.boss_defeated:
            self.spawn_timer = max(.65, 2.2-self.relays_down*.35-self.time/180)
            x = max(160, min(LENGTH-120, self.player.pos.x+self.rng.choice([-1, 1])*self.rng.uniform(470, 620)))
            self.spawn(V(x, self.rng.uniform(100, 620)), self.rng.choice(['grunt', 'grunt', 'rifle', 'runner', 'brute']))
        if self.relays_down == 3 and not self.boss_spawned:
            self.boss_spawned = True
            self.spawn(V(2180, 370), 'boss')
            self.message = 'WARNING // SIEGE WALKER INBOUND'
            self.message_timer = 5
        for e in self.enemies:
            if e.hp <= 0:
                continue
            e.flash = max(0, e.flash-dt)
            e.recoil = max(0.,e.recoil-dt)
            e.cooldown -= dt
            delta = self.player.pos-e.pos
            e.facing, e.aim_angle = aim_pose(delta,e.facing)
            distance = delta.length()
            direction = unit(delta)
            speed = {'grunt': 72, 'rifle': 58, 'runner': 132, 'brute': 48, 'boss': 38}[e.kind]
            if e.kind == 'boss' and e.phase > 0:
                e.moving = False
                e.phase -= dt
                if e.phase <= 0:
                    self.burst(e.target, 70, (255, 92, 30), 260)
                    self.shake = 12
                    if (self.player.pos-e.target).length() < 115:
                        self.damage_player(48)
                    for c in self.cover:
                        if (c.pos-e.target).length() < 115:
                            self.hit(c, 100)
                    e.cooldown = 2.8
                continue
            if e.kind == 'boss' and e.cooldown <= 0:
                e.target = V(self.player.pos)
                e.phase = 1.25
                continue
            if e.kind == 'rifle' and distance < 440 and e.cooldown <= 0:
                e.recoil = .16
                self.fire_weapon(e, self.player.pos, 300, 13, True)
                e.cooldown = self.rng.uniform(1.4, 2.2)
            velocity = direction*speed if distance > (230 if e.kind == 'rifle' else e.radius+14) else V()
            if e.kind == 'rifle' and distance < 150:
                velocity = -direction*speed
            # Local steering around cover and separation prevent solid infantry piles.
            for c in self.cover+self.relays:
                away = e.pos-c.pos
                d = away.length()
                if c.hp > 0 and 0 < d < c.radius+e.radius+60:
                    tangent = V(-away.y, away.x)
                    if tangent.dot(delta) < 0:
                        tangent = -tangent
                    velocity += unit(tangent)*90 + unit(away)*35
            for other in self.enemies:
                apart = e.pos-other.pos
                d2 = apart.length_squared()
                if other is not e and 0 < d2 < (e.radius+other.radius+8)**2:
                    velocity += unit(apart)*55
            traveled = self.move(e, velocity*dt)
            e.moving = traveled > .001
            if distance < e.radius+20 and e.cooldown <= 0:
                self.damage_player(24 if e.kind == 'brute' else 12)
                e.cooldown = .8
        for shot in self.shots:
            old = V(shot.pos)
            shot.pos += shot.velocity*dt
            shot.life -= dt
            targets = ([self.player] if shot.enemy else self.enemies+self.relays)+self.cover
            # Resolve the nearest intersection, so cover shields the actors behind it.
            contacts = [(segment_entry(old, shot.pos, t.pos, t.radius), t) for t in targets if t.hp > 0]
            contacts = [(fraction, t) for fraction, t in contacts if fraction is not None]
            if contacts:
                _, target = min(contacts, key=lambda contact: contact[0])
                if target is self.player:
                    self.damage_player(shot.damage)
                else:
                    self.hit(target, shot.damage)
                shot.life = 0
        self.shots = [b for b in self.shots if b.life > 0]
        self.enemies = [e for e in self.enemies if e.hp > 0]
        for g in self.grenade_flights:
            g[2] += dt
            if g[2] >= .65:
                self.explode(g[1])
        self.grenade_flights = [g for g in self.grenade_flights if g[2] < .65]
        for casing in self.casings:
            casing[0]+=casing[1]*dt; casing[2]+=dt
            old_height=casing[3]
            casing[3]=max(0.,casing[3]+casing[4]*dt)
            casing[4]-=340*dt
            if old_height>0 and casing[3]==0 and casing[4]<-100:
                casing[4]=-casing[4]*.28; casing[1]*=.6
            elif casing[3]==0 and casing[4]<=0:
                casing[4]=0.;casing[1]*=max(0.,1-dt*14)
        self.casings = [c for c in self.casings if c[2] < 8][-100:]
        for blast in self.blasts:blast[1]+=dt
        self.blasts=[b for b in self.blasts if b[1]<BLAST_DURATION]
        for death in self.deaths:death[3]+=dt
        self.deaths=[d for d in self.deaths if d[3]<CORPSE_DURATION]
        for p in self.particles:
            p[0] += p[1]*dt
            p[1] *= max(0, 1-dt*3)
            p[2] -= dt
        self.particles = [p for p in self.particles if p[2] > 0][-700:]
        for pickup in self.pickups[:]:
            if (pickup[0]-self.player.pos).length() < 36:
                if pickup[1] == 'health':
                    self.player.hp = min(100, self.player.hp+28)
                elif pickup[1] == 'shield':
                    self.shield = min(60, self.shield+30)
                else:
                    self.grenades = min(9, self.grenades+1)
                self.pickups.remove(pickup)
        if self.boss_defeated and (self.player.pos-V(2280, 510)).length() < 80 and self.state == 'playing':
            self.state = 'won'
        target = project(self.player.pos)-V(WIDTH*.38, HEIGHT*.48)
        self.camera += (target-self.camera)*(1-math.exp(-dt*7))
        self.shake *= math.exp(-dt*15)


class Renderer:
    def __init__(self):
        self.surface = pg.Surface((WIDTH, HEIGHT))
        self.font = pg.font.Font(None, 22)
        self.small = pg.font.Font(None, 17)
        self.title = pg.font.Font(None, 46)
        self.floor = self.build_floor()
        self.offset = V()

    def text(self, text, pos, color=(210, 204, 181), font=None):
        self.surface.blit((font or self.font).render(text, True, color), pos)

    def point(self, p, z=0):
        q = project(p)-self.offset
        return round(q.x), round(q.y-z)

    def diamond(self, p, radius, color, width=1):
        radius /= math.sqrt(2)
        pts = [self.point(p+V(-radius, -radius)), self.point(p+V(radius, -radius)), self.point(p+V(radius, radius)), self.point(p+V(-radius, radius))]
        pg.draw.polygon(self.surface, color, pts, width)

    def danger_ring(self, p, radius, color, width=2):
        points = [self.point(p+V(math.cos(i*math.tau/40),math.sin(i*math.tau/40))*radius) for i in range(40)]
        pg.draw.lines(self.surface, color, True, points, width)

    def build_floor(self, baked=True):
        s = pg.Surface((LENGTH+DEPTH+100, (LENGTH+DEPTH)//2+160), pg.SRCALPHA)
        rng = random.Random(103)
        def p(x, y):
            return x-y+DEPTH, (x+y)*.5
        for x in range(0, LENGTH, 48):
            for y in range(0, DEPTH, 48):
                shade = rng.randint(57, 73)
                points = [p(x, y), p(x+48, y), p(x+48, y+48), p(x, y+48)]
                poly(s, (shade+3, shade, shade+1), points, False)
                pg.draw.lines(s, (48, 46, 46), True, points, 1)
                for _ in range(40):
                    px, py = p(x+rng.randrange(46), y+rng.randrange(46))
                    fleck = rng.choice([-12, -7, 7, 13])
                    pg.draw.line(s, (shade+fleck, shade+fleck-2, shade+fleck-3), (px, py), (px+rng.randint(1,3), py), 1)
                if rng.random() < .19:
                    a = V(p(x+12, y+6))
                    pg.draw.lines(s, (38, 37, 39), False, [a, a+V(8, 10), a+V(4, 15), a+V(16, 22)])
        texture_path = Path(__file__).with_name('assets') / 'ashgate_pavement.png'
        if texture_path.exists():
            texture = pg.image.load(str(texture_path)).convert_alpha()
            tw, th = texture.get_width()//4, texture.get_height()//4
            tiles = []
            for ty in range(4):
                for tx in range(4):
                    tile = pg.transform.scale(texture.subsurface((tx*tw,ty*th,tw,th)), (100,100))
                    tile = pg.transform.scale(pg.transform.rotate(tile,45), (202,102))
                    tiles.append(tile)
            for x in range(0,LENGTH,100):
                for y in range(0,DEPTH,100):
                    px, py = p(x,y)
                    s.blit(tiles[(x//100%4)+(y//100%4)*4], (px-101,py-1))
        # Raised promenade edge and stone coping.
        for x in range(0, LENGTH, 48):
            a, b = V(p(x, 700)), V(p(x+48, 700))
            poly(s, (44, 43, 46), [a, b, b+V(0, 100), a+V(0, 100)])
            pg.draw.line(s, (111, 103, 88), a, b, 7)
            pg.draw.line(s, (70, 64, 60), a+V(4, 10), a+V(4, 95), 5)
        # Roadside rubble, gratings and brass lane dashes.
        for _ in range(650):
            x, y = rng.randrange(LENGTH), rng.choice([rng.randrange(90), rng.randrange(610, 690)])
            px, py = p(x, y)
            poly(s, rng.choice([(95, 87, 74), (48, 46, 45), (112, 100, 83)]), [(px, py), (px+7, py-4), (px+12, py+1), (px+4, py+5)])
        for x in range(0, LENGTH, 110):
            pg.draw.line(s, (135, 113, 65), p(x, 590), p(x+40, 590), 2)
            for k in range(5):
                pg.draw.line(s, (30, 32, 35), p(x+k*4, 100), p(x+k*4, 138), 2)
        if baked:
            # Baked map lighting: lower stone contrast, cool ambient, warm emitters.
            veil=pg.Surface(s.get_size(),pg.SRCALPHA)
            veil.fill((22,26,35,45));s.blit(veil,(0,0))
            for x in range(0,LENGTH,220):
                for dx in (45,100,155):
                    add_light(s,p(x+dx,95),115,(42,22,7),.65)
            for x,y in FIRE_POSITIONS:
                px,py=p(x,y)
                s.blit(shadow_stamp(100,36),(px-50,py-12))
                add_light(s,(px,py),145,(78,30,5),.48)
            # Continuous cool wall shade anchors the facades to the promenade.
            shade=pg.Surface(s.get_size(),pg.SRCALPHA)
            pg.draw.polygon(shade,(9,13,24,55),[p(0,0),p(LENGTH,0),p(LENGTH,65),p(0,65)])
            s.blit(shade,(0,0))
        return s

    def panel(self, rect):
        pg.draw.rect(self.surface, (20, 23, 27), rect)
        pg.draw.rect(self.surface, (117, 110, 94), rect, 2)
        pg.draw.rect(self.surface, (47, 48, 48), pg.Rect(rect).inflate(-8, -8), 1)
        x, y, w, h = rect
        for px, py in ((x+4,y+4), (x+w-5,y+4), (x+4,y+h-5), (x+w-5,y+h-5)):
            pg.draw.circle(self.surface, GOLD, (px, py), 1)

    def fire(self, pos, time, index):
        x,y=self.point(pos)
        if not -100<x<WIDTH+100 or not -150<y<HEIGHT+120:return
        sprite,anchor=effect('fire',time,index)
        self.surface.blit(sprite,V(x,y)-anchor)

    def death(self, item):
        pos,kind,facing,age=item
        x,y=self.point(pos)
        if not -280<x<WIDTH+280 or not -100<y<HEIGHT+300:return
        sprite,anchor=death_sprite(kind,age,facing)
        if age>CORPSE_DURATION-2:
            sprite=faded(sprite,(CORPSE_DURATION-age)/2)
        self.surface.blit(sprite,V(x,y)-anchor)

    def blast(self, item):
        pos,age,radius=item
        x,y=self.point(pos)
        if not -240<x<WIDTH+240 or not -240<y<HEIGHT+240:return
        sprite,anchor=effect('explosion',age)
        scale=max(.7,min(1.5,radius/160))
        sprite=pg.transform.scale_by(sprite,scale)
        if age>.78:
            sprite=faded(sprite,(BLAST_DURATION-age)/.27)
        self.surface.blit(sprite,V(x,y)-anchor*scale)

    def actor(self, actor, game):
        x, y = self.point(actor.pos)
        if not -180 < x < WIDTH+180 or not -120 < y < HEIGHT+220:
            return
        if actor.kind in ('crate', 'barrel', 'relay'):
            self.surface.blit(shadow_stamp(86,28),(x-43,y-8))
            sprite = prop(actor.kind, int(actor.pos.x)%3)
            self.surface.blit(sprite, (x-58, y-sprite.get_height()+16))
            if actor.kind == 'relay':
                self.text('SIGNAL RELAY', (x-39,y-sprite.get_height()+2), (246, 142, 70), self.small)
        else:
            boss = actor.kind == 'boss'
            sprite, anchor, muzzle = animated_sprite(actor.kind,actor.stride,actor.moving,actor.facing,actor.aim_angle,actor.recoil,game.time,actor.phase if boss else 0.,actor.aim_view if actor.kind=='player' else None,move_angle=actor.move_angle,move_facing=actor.move_facing)
            illumination=max((max(0,1-age/.28)*max(0,1-(actor.pos-pos).length()/220) for pos,age,radius in game.blasts),default=0)
            if illumination>0:
                sprite=sprite.copy();sprite.fill((round(65*illumination),round(32*illumination),round(8*illumination),0),special_flags=pg.BLEND_RGBA_ADD)
            if actor.flash > 0:
                sprite = sprite.copy()
                sprite.fill((100, 85, 65, 0), special_flags=pg.BLEND_RGBA_ADD)
            boss = actor.kind == 'boss'
            self.surface.blit(shadow_stamp(110 if boss else 50,26 if boss else 16),(x-(55 if boss else 25),y-6))
            self.surface.blit(sprite, (round(x-anchor.x),round(y-anchor.y)))
            if actor.kind == 'player':
                self.diamond(actor.pos, 22, (85, 165, 205))
            if actor.recoil > .065 and actor.kind in ('player','rifle'):
                tip=V(x,y)+muzzle-anchor
                direction=unit(project((game.aim if actor.kind=='player' else game.player.pos)-actor.pos)-V(0,55)-(muzzle-anchor))
                flash,origin=weapon_effect('muzzle_'+str(int(game.time*24)%2),direction)
                self.surface.blit(flash,tip-origin)
            if actor.kind != 'player' and actor.hp < {'grunt':45, 'rifle':35, 'runner':24, 'brute':125, 'boss':1800}[actor.kind]:
                maxhp = {'grunt':45, 'rifle':35, 'runner':24, 'brute':125, 'boss':1800}[actor.kind]
                pg.draw.rect(self.surface, INK, (x-19, y-SIZES[actor.kind][1], 38, 4))
                pg.draw.rect(self.surface, (174, 59, 40), (x-19, y-SIZES[actor.kind][1], max(0, 38*actor.hp/maxhp), 3))

    def draw(self, game, paused=False):
        s = self.surface
        s.fill((26, 26, 31))
        self.offset = game.camera+V(math.sin(game.time*83), math.cos(game.time*71))*game.shake
        s.blit(self.floor, (-DEPTH-self.offset.x, -self.offset.y))
        for pos, kind in game.marks:
            x, y = self.point(pos)
            s.blit(shadow_stamp(54,20),(x-27,y-8))
        for death in game.deaths:
            if death[3]>=DEATH_DURATION:self.death(death)
        for pos,age,radius in game.blasts:
            intensity=max(0,1-age/.35)
            if intensity>0:
                add_light(s,self.point(pos),round(radius),(round(130*intensity),round(65*intensity),round(16*intensity)),.55)
        for relay in game.relays:
            if relay.hp > 0:
                self.diamond(relay.pos, 45, (144, 77, 43))
        for e in game.enemies:
            if e.kind == 'boss' and e.phase > 0:
                self.danger_ring(e.target, 115, (255, 65, 33), 3)
                self.danger_ring(e.target, max(1,115*(1-e.phase/1.25)), (255, 164, 60), 2)
                x,y = self.point(e.target)
                self.text('INCOMING', (x-34,y-12), (255, 156, 80), self.small)
        for pos, kind in game.pickups:
            x, y = self.point(pos, 8+math.sin(game.time*4)*3)
            color = {'health':(105,209,105), 'shield':(70,168,242), 'frag':(227,167,68)}[kind]
            self.diamond(pos, 13, color)
            pg.draw.rect(s, color, (x-5, y-8, 10, 12))
            pg.draw.line(s, INK, (x-3,y-2), (x+3,y-2), 2)
            pg.draw.line(s, INK, (x,y-5), (x,y+1), 2)
        if game.boss_defeated:
            self.diamond(V(2280,510), 80, (94, 214, 182), 3)
            x,y = self.point(V(2280,510))
            self.text('EXTRACTION', (x-42,y-20), (130, 240, 202))
        # Sort all tall objects by their ground contact, including architecture/fire.
        queue = []
        for i in range(12):
            pos = V(i*220, 0)
            queue.append((pos.x+pos.y, 'building', (pos,i)))
        for a in game.cover+game.relays+game.enemies+[game.player]:
            if a.hp > 0:
                queue.append((a.pos.x+a.pos.y, 'actor', a))
        for death in game.deaths:
            if death[3]<DEATH_DURATION:queue.append((sum(death[0]),'death',death))
        for blast in game.blasts:queue.append((sum(blast[0])+1,'blast',blast))
        for i, pos in enumerate(game.fires):
            queue.append((pos.x+pos.y, 'fire', (pos,i)))
        for _, kind, item in sorted(queue, key=lambda item:item[0]):
            if kind == 'actor':
                self.actor(item, game)
            elif kind == 'death':
                self.death(item)
            elif kind == 'blast':
                self.blast(item)
            elif kind == 'building':
                pos, i = item
                x,y = self.point(pos)
                if -270 < x < WIDTH+50 and -350 < y < HEIGHT+350:
                    building = facade(i%4)
                    anchor=facade_anchor()
                    s.blit(building, (x-anchor[0],y-anchor[1]))
            else:
                self.fire(item[0], game.time, item[1])
        for pos,velocity,age,height,vz in game.casings:
            x,y=self.point(pos,height)
            case=casing_sprite(age,height<=0 and vz<=0,pos.x+pos.y)
            s.blit(case,(x-case.get_width()/2,y-case.get_height()/2))
        for b in game.shots:
            bolt,origin=weapon_effect('enemy_bolt' if b.enemy else 'bolt',project(b.velocity))
            s.blit(bolt,V(self.point(b.pos,55))-origin)
        for start, end, t in game.grenade_flights:
            q = start.lerp(end, min(1,t/.65))
            self.danger_ring(end, 160, (159, 141, 78), 1)
            pg.draw.circle(s, (133, 174, 72), self.point(q, math.sin(t/.65*math.pi)*100+12), 5)
        for pos, vel, life, color, size in game.particles:
            pg.draw.rect(s, color, (*self.point(pos, 15+life*22), size, size))
        self.hud(game)
        if paused or game.state != 'playing':
            overlay = pg.Surface((WIDTH,HEIGHT), pg.SRCALPHA)
            overlay.fill((8, 11, 17, 205))
            s.blit(overlay, (0,0))
            self.panel((260,175,440,185))
            title = 'PAUSED' if paused else 'ASHGATE LIBERATED' if game.state == 'won' else 'YOU HAVE FALLEN'
            self.text(title, (290,207), GOLD, self.title)
            self.text(f'{game.score:07d} POINTS   /   {game.kills} KILLS   /   {int(game.time)} SECONDS', (290,265))
            self.text('ESC TO RESUME' if paused else 'R TO DEPLOY AGAIN  /  ESC TO QUIT', (290,310), (147,164,176))
            if game.audio:
                self.panel((260,373,440,58))
                status = 'NO AUDIO DEVICE' if not game.audio.available else 'MUTED' if game.audio.muted else 'ON'
                self.text(f'AUDIO {status} [M]', (280,383), GOLD, self.small)
                self.text(f'GUNFIRE {game.audio.sfx_volume:.0%}  [- / =]', (280,405), font=self.small)
        return s

    def hud(self, game):
        s = self.surface
        status_hud(s,game,self.font,self.small)
        self.panel((16,477,928,47))
        self.text(f'FRAG {game.grenades:02d}  [SPACE / RMB]', (30,489), GOLD)
        self.text('DASH '+('READY' if game.dash_cd <= 0 else f'{game.dash_cd:.1f}s')+' [SHIFT]', (249,489))
        objective = f'RELAYS {game.relays_down}/3' if not game.boss_spawned else 'REACH EXTRACTION' if game.boss_defeated else 'DESTROY THE WALKER'
        self.text(objective, (483,489), (230,151,80))
        self.text('WASD MOVE  /  LMB FIRE  /  ESC', (723,491), (137,144,149), self.small)
        if game.message_timer > 0:
            text = self.small.render(game.message, True, (235,194,112))
            rect = text.get_rect(center=(WIDTH//2,145))
            pg.draw.rect(s, (24,25,28), rect.inflate(24,14))
            s.blit(text,rect)
        boss = next((e for e in game.enemies if e.kind == 'boss'), None)
        if boss:
            self.text('CATHEDRAL-BREAKER', (348,24), (225,151,107), self.small)
            pg.draw.rect(s, INK, (322,44,322,10))
            pg.draw.rect(s, (176,54,38), (323,45,int(320*boss.hp/1800),8))
        if game.combo_timer > 0 and game.combo > 1:
            self.text(f'{game.combo} KILL CHAIN  x{min(5,game.combo)}', (18,98), (249,184,80))
        # An on-screen compass guides the player to the next objective.
        target = next((r.pos for r in game.relays if r.hp > 0), V(2280,510) if game.boss_defeated else (boss.pos if boss else None))
        if target is not None:
            q = V(self.point(target))
            if not pg.Rect(70,160,820,280).collidepoint(q):
                q.x = max(65,min(895,q.x))
                q.y = max(172,min(440,q.y))
                pg.draw.circle(s, GOLD, q, 12, 2)
                self.text('!', (q.x-3,q.y-7), GOLD)
        if game.state == 'playing':
            x,y = self.point(game.aim, 55)
            pg.draw.circle(s, (235,207,149), (x,y), 7, 1)
            for dx,dy in ((-12,0),(8,0),(0,-12),(0,8)):
                pg.draw.line(s, (235,207,149), (x+dx,y+dy), (x+dx+(4 if dy==0 else 0), y+dy+(4 if dx==0 else 0)))


def cursor_aim(cursor, game):
    # Clicking a visible torso (especially the towering boss) resolves to its
    # ground hitbox instead of requiring the player to aim at the creature's feet.
    for actor in sorted(game.enemies+game.relays,key=lambda a:a.pos.x+a.pos.y,reverse=True):
        if actor.hp <= 0:
            continue
        foot=project(actor.pos)-game.camera
        height=150 if actor.kind=='relay' else SIZES[actor.kind][1]
        width=actor.radius*2
        if pg.Rect(foot.x-width/2,foot.y-height,width,height).collidepoint(cursor):
            return V(actor.pos)
    return unproject(cursor+game.camera+V(0,55))


def main(argv=None):
    parser = argparse.ArgumentParser(description='Hive City Rampage: Ashgate Siege')
    parser.add_argument('--seed', type=int, default=7)
    parser.add_argument('--smoke-test', type=int, metavar='FRAMES', default=0, help='Run deterministic automated input for N frames and exit')
    parser.add_argument('--screenshot', type=Path, help='Save the last rendered frame')
    parser.add_argument('--mute', action='store_true')
    parser.add_argument('--sfx-volume', type=float, default=.8)
    args = parser.parse_args(argv)
    pg.mixer.pre_init(44100, -16, 2, 512)
    pg.init()
    window = pg.display.set_mode((1280,720), pg.RESIZABLE)
    pg.display.set_caption('HIVE CITY RAMPAGE // ASHGATE SIEGE')
    clock = pg.time.Clock()
    renderer = Renderer()
    game = Siege(args.seed, Audio(args.sfx_volume, args.mute))
    running, paused, frames = True, False, 0
    pg.mouse.set_visible(False)
    try:
        while running:
            dt = 1/60 if args.smoke_test else min(clock.tick(60)/1000, .04)
            ww, wh = window.get_size()
            scale = min(ww/WIDTH, wh/HEIGHT)
            origin = V((ww-WIDTH*scale)/2,(wh-HEIGHT*scale)/2)
            cursor = (V(pg.mouse.get_pos())-origin)/scale
            # Projectiles travel at chest height; map the cursor onto that plane.
            aim = cursor_aim(cursor, game)
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:
                        if game.state != 'playing':
                            running = False
                        else:
                            paused = not paused
                            game.audio.set_paused(paused)
                            pg.mouse.set_visible(paused)
                    elif event.key == pg.K_m:
                        game.audio.toggle_mute()
                    elif event.key in (pg.K_MINUS, pg.K_EQUALS):
                        game.audio.sfx_volume = max(0., min(1., game.audio.sfx_volume+(.05 if event.key == pg.K_EQUALS else -.05)))
                    elif event.key == pg.K_r and game.state != 'playing':
                        game = Siege(args.seed, game.audio)
                    elif event.key == pg.K_SPACE and not paused:
                        game.grenade(aim)
                elif event.type == pg.MOUSEBUTTONDOWN and event.button == 3 and not paused:
                    game.grenade(aim)
            keys = pg.key.get_pressed()
            movement = V(int(keys[pg.K_d])-int(keys[pg.K_a]), int(keys[pg.K_s])-int(keys[pg.K_w]))
            shooting = pg.mouse.get_pressed()[0]
            if args.smoke_test:
                movement = V(.3, math.sin(frames*.025)*.3)
                aim = next((e.pos for e in game.enemies), game.relays[0].pos)
                shooting = True
                if frames == 90:
                    game.grenade(aim)
            if not paused:
                game.update(dt, movement, aim, shooting, keys[pg.K_LSHIFT] or keys[pg.K_RSHIFT])
            surface = renderer.draw(game, paused)
            window.fill((9,11,15))
            window.blit(pg.transform.scale(surface, (round(WIDTH*scale),round(HEIGHT*scale))), origin)
            pg.display.flip()
            frames += 1
            if args.smoke_test and frames >= args.smoke_test:
                running = False
        if args.screenshot:
            args.screenshot.parent.mkdir(parents=True, exist_ok=True)
            pg.image.save(renderer.surface, str(args.screenshot))
        if args.smoke_test:
            print(f'Smoke test: {frames} frames, {game.kills} kills, {len(game.enemies)} enemies, state={game.state}')
    finally:
        game.audio.close()
        pg.mouse.set_visible(True)
        pg.quit()


if __name__ == '__main__':
    main()
