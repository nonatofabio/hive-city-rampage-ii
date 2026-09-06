"""Import the atlas's color key into real alpha without pale matte fringes."""
import pygame as pg


def cutout(sheet,rect,magenta=False):
    sprite=sheet.subsurface(rect).copy().convert_alpha()
    if magenta:
        # A color-key import, not a recolor: character colors remain untouched.
        # Include blended magenta edge pixels rather than preserving a pink halo.
        for y in range(sprite.get_height()):
            for x in range(sprite.get_width()):
                r,g,b,a=sprite.get_at((x,y))
                if r>65 and b>65 and r>g+45 and b>g+45:
                    sprite.set_at((x,y),(0,0,0,0))
        mask=pg.mask.from_surface(sprite)
    else:
        mask=pg.mask.from_threshold(sprite,(242,242,242,255),(34,34,34,255));mask.invert()
    silhouette=mask.connected_component()
    alpha=silhouette.to_surface(setcolor=(255,255,255,255),unsetcolor=(0,0,0,0))
    sprite.blit(alpha,(0,0),special_flags=pg.BLEND_RGBA_MULT)
    return sprite.subsurface(sprite.get_bounding_rect()).copy()
