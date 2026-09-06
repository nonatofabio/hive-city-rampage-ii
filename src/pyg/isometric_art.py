"""Deterministic, cached pixel art for the Ashgate isometric battlefield.

Art is drawn at native resolution; no reference image is used as a backdrop.
"""
import math
import random
from functools import lru_cache
from pathlib import Path
import pygame as pg
from sprite_import import cutout

INK = (18, 20, 25)
STONE = (73, 69, 68)
GOLD = (194, 143, 62)


@lru_cache(maxsize=2)
def atlas(clean=False):
    root = Path(__file__).with_name('assets')
    path = root / ('ashgate_atlas_clean.png' if clean and (root/'ashgate_atlas_clean.png').exists() else 'ashgate_atlas_cutout.png')
    return pg.image.load(str(path)).convert_alpha() if path.exists() else None


@lru_cache(maxsize=24)
def atlas_sprite(kind):
    """Slice independently packed objects and key the generator's pale matte.

    Largest connected silhouettes discard neighboring spire/foot fragments at
    cell boundaries. This import step leaves the source PNG untouched.
    """
    clean = (Path(__file__).with_name('assets')/'ashgate_atlas_clean.png').exists()
    sheet = atlas(clean)
    if sheet is None:
        return None
    regions = {
        'player': ((60, 50, 340, 394), (88, 100)),
        'grunt': ((450, 70, 320, 352), (82, 90)),
        'rifle': ((800, 85, 290, 365), (82, 94)),
        'runner': ((450, 70, 320, 352), (70, 78)),
        'brute': ((800, 85, 290, 365), (98, 112)),
        'boss': ((1130, 0, 406, 530), (200, 238)),
        'facade': ((10, 428, 394, 592), (258, 397)),
        'crate': ((450, 610, 330, 342), (103, 94)),
        'barrel': ((870, 600, 215, 362), (43, 64)),
        'relay': ((1210, 468, 240, 540), (70, 151)),
    }
    rect, size = regions[kind]
    sprite = cutout(sheet,rect,magenta=clean)
    return pg.transform.scale(sprite, size)


def poly(s, color, pts, outline=True):
    pg.draw.polygon(s, color, pts)
    if outline:
        pg.draw.lines(s, INK, True, pts, 1)


def skull(s, x, y, scale=1):
    r = scale
    pg.draw.rect(s, (183, 174, 148), (x-5*r, y-6*r, 10*r, 9*r), border_radius=3*r)
    pg.draw.rect(s, (139, 131, 112), (x-3*r, y+2*r, 6*r, 4*r))
    for dx in (-3, 2):
        pg.draw.rect(s, INK, (x+dx*r, y-2*r, 3*r, 3*r))
    pg.draw.line(s, INK, (x, y+1*r), (x-r, y+3*r), r)
    for dx in (-2, 0, 2):
        pg.draw.line(s, INK, (x+dx*r, y+4*r), (x+dx*r, y+6*r))


@lru_cache(maxsize=128)
def soldier(kind, facing=1, step=0):
    """Foot-anchored infantry and multi-part armored siege walker."""
    textured = atlas_sprite(kind)
    if textured is not None:
        # A subtle stepping offset preserves the silhouette without distorting it.
        s = pg.Surface((textured.get_width(), textured.get_height()+4), pg.SRCALPHA)
        s.blit(textured, (0, abs(step)*2))
        return pg.transform.flip(s, facing < 0, False)
    boss = kind == 'boss'
    s = pg.Surface((160, 180) if boss else (64, 80), pg.SRCALPHA)
    if boss:
        # Oversized spiked pauldrons, piston legs, armored fists and skull maw.
        for x in (42, 99):
            pg.draw.rect(s, INK, (x, 107, 27, 60))
            pg.draw.rect(s, (78, 86, 89), (x+3, 107, 21, 43))
            pg.draw.rect(s, (148, 155, 149), (x+5, 111, 5, 35))
            poly(s, (54, 63, 70), [(x-7, 150), (x+22, 149), (x+28, 167), (x-10, 167)])
        poly(s, (65, 77, 88), [(40, 55), (116, 55), (123, 116), (96, 141), (56, 131), (33, 100)])
        for x in (8, 104):
            poly(s, (91, 105, 114), [(x, 57), (x+10, 29), (x+36, 32), (x+46, 61), (x+40, 88), (x+3, 83)])
            pg.draw.lines(s, (182, 185, 177), False, [(x+3, 57), (x+13, 34), (x+34, 37)], 3)
            for k in range(3):
                poly(s, (205, 199, 174), [(x+7+k*12, 37), (x+6+k*12, 16-k%2*9), (x+15+k*12, 35)])
            pg.draw.rect(s, (53, 59, 64), (x+8, 88, 29, 43))
            for k in range(3):
                pg.draw.line(s, (170, 172, 155), (x+10+k*10, 121), (x+3+k*11, 145), 4)
            poly(s, (156, 48, 35), [(x+17, 43), (x+29, 49), (x+20, 61), (x+34, 72), (x+13, 68)])
        skull(s, 79, 74, 4)
        pg.draw.rect(s, (33, 16, 17), (68, 81, 23, 26))
        for x in (69, 85):
            poly(s, (233, 206, 140), [(x, 83), (x+5, 83), (x+2, 96)])
        pg.draw.rect(s, (252, 70, 25), (66, 62, 9, 4))
        pg.draw.rect(s, (252, 70, 25), (84, 62, 9, 4))
    else:
        blue = kind == 'player'
        col = (31, 106, 175) if blue else {'rifle': (144, 92, 50), 'runner': (97, 112, 71), 'brute': (112, 115, 118)}.get(kind, (126, 79, 49))
        light = tuple(min(255, c+39) for c in col)
        # Backpack, greaves, separate shoulder armor and gold edging.
        pg.draw.rect(s, INK, (12, 24, 18, 30), border_radius=4)
        pg.draw.rect(s, col, (13, 23, 12, 24), border_radius=3)
        for x, off in ((22, step*2), (36, -step*2)):
            pg.draw.rect(s, INK, (x-2, 51+off, 14, 23), border_radius=3)
            pg.draw.rect(s, col, (x, 52+off, 10, 16))
            pg.draw.rect(s, light, (x+1, 54+off, 3, 10))
            pg.draw.rect(s, col, (x-3, 67+off, 15, 6))
        poly(s, col, [(21, 28), (42, 26), (48, 46), (40, 58), (22, 54), (18, 38)])
        pg.draw.line(s, light, (23, 30), (24, 48), 3)
        pg.draw.rect(s, (40, 37, 33), (22, 50, 23, 5))
        for x in (23, 37):
            pg.draw.rect(s, GOLD, (x, 50, 5, 6))
        pg.draw.rect(s, INK, (28, 9, 18, 22), border_radius=6)
        pg.draw.rect(s, col if blue else (196, 180, 139), (29, 10, 16, 19), border_radius=5)
        pg.draw.rect(s, light if blue else (220, 199, 154), (31, 11, 5, 10))
        pg.draw.rect(s, (248, 84, 34) if blue else INK, (38, 17, 8, 4))
        pg.draw.rect(s, (42, 47, 51), (37, 23, 10, 6))
        pg.draw.rect(s, GOLD if blue else INK, (16, 26, 20, 20), border_radius=6)
        pg.draw.rect(s, col, (18, 27, 16, 16), border_radius=5)
        pg.draw.line(s, light, (20, 29), (29, 29), 2)
        if blue:
            skull(s, 25, 35)
        pg.draw.rect(s, INK, (34, 38, 28, 10))
        pg.draw.rect(s, (89, 91, 84), (36, 39, 25, 5))
        pg.draw.rect(s, (161, 158, 139), (49, 39, 11, 2))
        pg.draw.rect(s, (41, 42, 43), (46, 44, 7, 10))
        pg.draw.rect(s, col, (29, 40, 13, 9), border_radius=3)
    return pg.transform.flip(s, facing < 0, False)


@lru_cache(maxsize=64)
def facade(variant):
    textured = atlas_sprite('facade')
    if textured is not None:
        # The painted wall's horizontal masonry runs at 0.60 px/px. Project
        # those rows to the same 0.50 slope as the street, preserving verticals.
        result=pg.Surface((textured.get_width(),textured.get_height()+26),pg.SRCALPHA)
        for x in range(textured.get_width()):
            result.blit(textured,(x,26+round(x*.5)-round(x*.6)),(x,0,1,textured.get_height()))
        return result
    rng = random.Random(variant)
    s = pg.Surface((258, 340), pg.SRCALPHA)
    # Receding roof and front wall share the street's 2:1 projection.
    poly(s, (48, 44, 44), [(8, 31), (228, 141), (248, 126), (29, 16)])
    poly(s, (66, 59, 57), [(8, 31), (228, 141), (228, 325), (8, 215)])
    poly(s, (35, 36, 40), [(228, 141), (248, 126), (248, 309), (228, 325)])
    for row in range(12):
        for col in range(11):
            x = 10+col*20
            y = 35+x*.5+row*14
            c = rng.randint(-9, 9)
            poly(s, (72+c, 64+c, 60+c), [(x, y), (x+18, y+9), (x+18, y+21), (x, y+12)])
    for x in (22, 94, 166):
        y = 50+x//2
        # Tall pointed, glowing lancet windows.
        poly(s, (25, 24, 29), [(x, y+23), (x+19, y), (x+38, y+42), (x+38, y+98), (x, y+79)])
        poly(s, (187, 85, 24), [(x+6, y+26), (x+19, y+9), (x+31, y+40), (x+31, y+86), (x+6, y+74)])
        for j in range(5):
            pg.draw.line(s, (251, 178, 53), (x+10+j%2*8, y+32+j*9), (x+14+j%2*8, y+43+j*9), 3)
        pg.draw.line(s, INK, (x+19, y+10), (x+19, y+82), 4)
        pg.draw.line(s, INK, (x+4, y+48), (x+32, y+62), 4)
        poly(s, (104, 97, 85), [(x-4, y+23), (x+19, y-7), (x+42, y+40), (x+38, y+43), (x+19, y), (x, y+26)])
        skull(s, x+17, y+116, 2)
    for x in (9, 79, 151, 220):
        y = 36+x//2
        poly(s, (111, 102, 88), [(x, y), (x+7, y+3), (x+7, y+179), (x, y+176)])
        poly(s, (44, 43, 44), [(x+7, y+3), (x+13, y), (x+13, y+174), (x+7, y+179)])
    for h in (158, 178):
        poly(s, (118, 106, 89), [(4, h+32), (229, h+145), (234, h+139), (10, h+26)])
    return s


def facade_anchor():
    # Painted front-face baseline: y=260+0.60*x before reprojection/padding.
    return (0,286) if atlas_sprite('facade') is not None else (8,215)


@lru_cache(maxsize=48)
def prop(kind, variant=0):
    s = pg.Surface((116, 104), pg.SRCALPHA)
    textured = atlas_sprite(kind)
    if textured is not None:
        # Props share a ground anchor, including the taller signal tower.
        s = pg.Surface((116, max(104, textured.get_height()+16)), pg.SRCALPHA)
        s.blit(textured, ((116-textured.get_width())//2, s.get_height()-16-textured.get_height()))
        return s
    if kind == 'relay':
        poly(s, (49, 56, 62), [(28, 75), (57, 60), (90, 76), (59, 94)])
        pg.draw.rect(s, INK, (43, 15, 32, 64))
        pg.draw.rect(s, (106, 111, 105), (46, 17, 26, 60))
        pg.draw.rect(s, (48, 23, 23), (50, 22, 18, 28))
        for y in range(24, 49, 6):
            pg.draw.rect(s, (246, 83, 37), (52, y, 14, 3))
        skull(s, 59, 61)
        for x in (34, 79):
            pg.draw.line(s, (147, 133, 103), (x, 78), (x, 22), 4)
            poly(s, (214, 182, 113), [(x-4, 23), (x, 11), (x+4, 23)])
    elif kind == 'barrel':
        pg.draw.ellipse(s, INK, (41, 40, 33, 47))
        pg.draw.rect(s, (126, 54, 32), (42, 43, 31, 34))
        pg.draw.ellipse(s, (186, 104, 48), (42, 38, 31, 12))
        for y in (48, 69):
            pg.draw.line(s, (56, 53, 45), (42, y), (73, y), 4)
        skull(s, 58, 59)
    else:
        c = (57, 90, 115) if variant % 2 else (121, 79, 51)
        poly(s, c, [(18, 43), (61, 64), (61, 94), (18, 73)])
        poly(s, tuple(max(0,v-22) for v in c), [(61, 64), (99, 45), (99, 75), (61, 94)])
        poly(s, tuple(v+30 for v in c), [(18, 43), (56, 24), (99, 45), (61, 64)])
        for x in (24, 48):
            pg.draw.line(s, (165, 135, 84), (x, 47+(x-24)//2), (x, 73+(x-24)//2), 4)
        for x in range(64, 98, 9):
            pg.draw.line(s, GOLD if x%2 else INK, (x, 68-(x-64)//2), (x, 84-(x-64)//2), 4)
    return s
