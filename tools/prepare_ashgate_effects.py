"""Import authored VFX/death atlases into registered runtime pose sheets.

Retain real alpha (including detached smoke and sparks); key magenta only when
it is present. Never normalize individual pose sizes during an animation.
"""
from pathlib import Path
import os
import pygame as pg
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'src/pyg/assets'
OUT=ASSETS/'effects'


def alpha_import(sprite):
    for y in range(sprite.get_height()):
        for x in range(sprite.get_width()):
            r,g,b,a=sprite.get_at((x,y))
            if r>65 and b>65 and r>g+45 and b>g+45:
                sprite.set_at((x,y),(0,0,0,0))
    return sprite


def cell(sheet,x,y,cols,rows):
    w,h=sheet.get_size()
    left,top=round(x*w/cols),round(y*h/rows)
    right,bottom=round((x+1)*w/cols),round((y+1)*h/rows)
    return alpha_import(sheet.subsurface((left,top,right-left,bottom-top)).copy())


def main():
    pg.display.init();pg.display.set_mode((1,1));OUT.mkdir(exist_ok=True)
    source=pg.image.load(str(ASSETS/'ashgate_vfx_atlas.png')).convert_alpha()
    for name,row,size in [('fire',0,128),('explosion',2,208)]:
        packed=pg.Surface((size*8,size),pg.SRCALPHA)
        for i in range(8):
            sprite=pg.transform.scale(cell(source,i%4,row+i//4,4,4),(size,size))
            # Stabilize the grounded base while leaving plume size free to evolve.
            dy=round(size*.94)-sprite.get_bounding_rect(min_alpha=12).bottom
            packed.blit(sprite,(i*size,dy))
        pg.image.save(packed,str(OUT/(name+'.png')))
    death_path=ASSETS/'ashgate_deaths_atlas.png'
    if death_path.exists():
        source=pg.image.load(str(death_path)).convert_alpha()
        for row,(name,w,h) in enumerate([('grunt',128,132),('rifle',128,116),('boss',260,280)]):
            packed=pg.Surface((w*4,h),pg.SRCALPHA)
            for i in range(4):
                # The generated rows have uneven gutters; keep the boss spires intact.
                edges=[0,440,800,1254]
                top=round(edges[row]*source.get_height()/1254)
                bottom=round(edges[row+1]*source.get_height()/1254)
                strip=source.subsurface((0,top,source.get_width(),bottom-top))
                # Measured column gutters preserve the prone boots and gun barrels.
                columns=[0,305,588,902,1254]
                left=round(columns[i]*source.get_width()/1254)
                right=round(columns[i+1]*source.get_width()/1254)
                crop=alpha_import(strip.subsurface((left,0,right-left,strip.get_height())).copy())
                scale=h/strip.get_height()
                sprite=pg.transform.scale(crop,(round(crop.get_width()*scale),h))
                dx=round(w/2-((i+.5)*source.get_width()/4-left)*scale)
                dy=round(h*.88)-sprite.get_bounding_rect(min_alpha=12).bottom
                packed.blit(sprite,(i*w+dx,dy))
            pg.image.save(packed,str(OUT/('death_'+name+'.png')))
    weapons=ASSETS/'ashgate_weapon_fx.png'
    if weapons.exists():
        source=pg.image.load(str(weapons)).convert_alpha()
        for i,name in enumerate(('bolt','enemy_bolt')):
            sprite=cell(source,i,0,2,2)
            sprite=sprite.subsurface(sprite.get_bounding_rect()).copy()
            sprite=pg.transform.smoothscale(sprite,(20,6) if i==0 else (16,5))
            pg.image.save(sprite,str(OUT/(name+'.png')))
        for i in range(2):
            sprite=cell(source,i,1,2,2)
            # The source flash includes a barrel stub; only import the flame.
            left=round(sprite.get_width()*.20)
            sprite=sprite.subsurface((left,0,sprite.get_width()-left,sprite.get_height())).copy()
            sprite=pg.transform.smoothscale(sprite,(36,42))
            pg.image.save(sprite,str(OUT/('muzzle_'+str(i)+'.png')))
    servo=ASSETS/'ashgate_servo_casings.png'
    if servo.exists():
        source=pg.image.load(str(servo)).convert_alpha()
        for name,x,y,size in [('servo_skull',0,0,(40,56)),('casing_0',1,0,(12,6)),('casing_1',0,1,(12,12)),('casing_2',1,1,(8,7))]:
            sprite=cell(source,x,y,2,2)
            sprite=sprite.subsurface(sprite.get_bounding_rect()).copy()
            pg.image.save(pg.transform.smoothscale(sprite,size),str(OUT/(name+'.png')))
    pg.quit()


if __name__=='__main__':main()
