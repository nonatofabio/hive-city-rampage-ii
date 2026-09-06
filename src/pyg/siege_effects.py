"""Authored effect/death frames and cached light stamps for the siege renderer."""
from functools import lru_cache
from pathlib import Path
import pygame as pg

DIRECTORY=Path(__file__).with_name('assets')/'effects'
BLAST_DURATION=1.05
DEATH_DURATION=.85
CORPSE_DURATION=20.


@lru_cache(maxsize=12)
def frames(name):
    sheet=pg.image.load(str(DIRECTORY/(name+'.png'))).convert_alpha()
    count=8 if name in ('fire','explosion') else 4
    w=sheet.get_width()//count
    return tuple(sheet.subsurface((i*w,0,w,sheet.get_height())) for i in range(count))


def effect(name,age,variant=0):
    sequence=frames(name)
    index=int(age*10+variant*3)%8 if name=='fire' else min(7,int(max(0,age)/BLAST_DURATION*8))
    sprite=sequence[index]
    return sprite,pg.Vector2(sprite.get_width()/2,sprite.get_height()*.94)


@lru_cache(maxsize=32)
def death_frame(kind,index,facing):
    model={'runner':'grunt','brute':'rifle'}.get(kind,kind)
    sprite=frames('death_'+model)[index]
    scale={'runner':.86,'brute':1.18}.get(kind,1.)
    if scale!=1:sprite=pg.transform.scale_by(sprite,scale)
    if facing<0:sprite=pg.transform.flip(sprite,True,False)
    return sprite,pg.Vector2(sprite.get_width()/2,sprite.get_height()*.88)


def death_sprite(kind,age,facing):
    # Hit recoil is quick; the fall takes longer and ends in a held corpse pose.
    index=0 if age<.10 else 1 if age<.28 else 2 if age<.52 else 3
    return death_frame(kind,index,facing)


@lru_cache(maxsize=24)
def light_stamp(radius,color=(50,22,5),aspect=.5):
    """Black-backed additive light with a smooth falloff; baked once for scenery."""
    height=max(2,round(radius*2*aspect))
    stamp=pg.Surface((radius*2,height))
    stamp.fill((0,0,0))
    for step in range(32,0,-1):
        ratio=step/32
        intensity=(1-ratio)**2
        shade=tuple(round(c*intensity) for c in color)
        w=max(1,round(radius*2*ratio));h=max(1,round(height*ratio))
        pg.draw.ellipse(stamp,shade,((radius*2-w)//2,(height-h)//2,w,h))
    return stamp


def add_light(surface,center,radius,color=(50,22,5),aspect=.5):
    stamp=light_stamp(radius,color,aspect)
    surface.blit(stamp,(round(center[0]-stamp.get_width()/2),round(center[1]-stamp.get_height()/2)),special_flags=pg.BLEND_RGB_ADD)


@lru_cache(maxsize=8)
def shadow_stamp(width,height):
    stamp=pg.Surface((width,height),pg.SRCALPHA)
    for step in range(20,0,-1):
        ratio=step/20
        w=max(1,round(width*ratio));h=max(1,round(height*ratio))
        pg.draw.ellipse(stamp,(8,10,16,round(95*(1-ratio)**.6)),((width-w)//2,(height-h)//2,w,h))
    return stamp


def faded(sprite,opacity):
    """Fade per-pixel alpha only; never darken RGB or disable alpha at zero."""
    result=sprite.copy()
    result.fill((255,255,255,round(255*max(0,min(1,opacity)))),special_flags=pg.BLEND_RGBA_MULT)
    return result


@lru_cache(maxsize=12)
def weapon_texture(name):
    return pg.image.load(str(DIRECTORY/(name+'.png'))).convert_alpha()


@lru_cache(maxsize=720)
def weapon_frame(name,angle):
    sprite=weapon_texture(name)
    anchor=pg.Vector2(0,sprite.get_height()*.477) if name.startswith('muzzle') else pg.Vector2(sprite.get_width()-1,sprite.get_height()/2)
    center=pg.Vector2(sprite.get_width()/2,sprite.get_height()/2)
    rotated=pg.transform.rotate(sprite,-angle)
    anchor=(anchor-center).rotate(angle)+pg.Vector2(rotated.get_width()/2,rotated.get_height()/2)
    return rotated,anchor


def weapon_effect(name,direction):
    import math
    angle=round(math.degrees(math.atan2(direction.y,direction.x))/2)*2
    return weapon_frame(name,angle)


@lru_cache(maxsize=108)
def casing_frame(index,angle):
    return pg.transform.rotate(weapon_texture('casing_'+str(index)),-angle)


def casing_sprite(age,grounded,seed=0):
    index=0 if grounded else int(age*17)%3
    angle=(int(seed)%18)*10 if grounded else int(age*72)%36*10
    sprite=casing_frame(index,angle)
    return faded(sprite,(8-age)/2) if age>6 else sprite
