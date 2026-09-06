"""Register drawn lower-body walk poses at their belts, preserving pose scale."""
import os
from pathlib import Path
from statistics import median
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
import pygame as pg
ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'src/pyg/assets'


def main():
    pg.display.init();pg.display.set_mode((1,1))
    source=pg.image.load(str(ASSETS/'ashgate_walk_atlas_final.png')).convert_alpha()
    # Chroma-key authored magenta, including antialiased pink edge pixels.
    for y in range(source.get_height()):
        for x in range(source.get_width()):
            r,g,b,a=source.get_at((x,y))
            if r>80 and b>65 and r>g+40 and b>g+40:
                source.set_at((x,y),(0,0,0,0))
    boxes=pg.mask.from_surface(source,32).get_bounding_rects()
    boxes=[r for r in boxes if r.width>45 and r.height>80]
    if len(boxes)!=20:raise ValueError(f'Expected 20 isolated walking poses, found {len(boxes)}')
    boxes.sort(key=lambda r:r.centery)
    out=ASSETS/'rendered/walk';out.mkdir(parents=True,exist_ok=True)
    for row,view in enumerate((0,-45,-90,45,90)):
        cells=sorted(boxes[row*4:row*4+4],key=lambda r:r.centerx)
        scale=44/median(r.height for r in cells)
        # Source paintings have taller proportions: match the game's squat armor.
        scale_x=scale*(1.35 if view==0 else 1.65 if abs(view)==90 else 1.5)
        sheet=pg.Surface((320,64),pg.SRCALPHA)
        for i,box in enumerate(cells):
            pose=source.subsurface(box).copy()
            belt=pose.subsurface((0,0,pose.get_width(),max(1,round(box.height*.075)))).get_bounding_rect(min_alpha=32)
            belt_x=belt.centerx
            image=pg.transform.smoothscale(pose,(round(box.width*scale_x),round(box.height*scale)))
            sheet.blit(image,(i*80+40-round(belt_x*scale_x),12))
        pg.image.save(sheet,str(out/f'{view}.png'))
    pg.quit()


if __name__=='__main__':main()
