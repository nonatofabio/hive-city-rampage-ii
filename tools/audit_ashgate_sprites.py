"""Render all torso views and locomotion keys on a light inspection background."""
import os
from pathlib import Path
import sys
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/pyg'))
import pygame as pg
from siege_motion import animated_sprite


def main():
    pg.init();pg.display.set_mode((1,1));font=pg.font.Font(None,22)
    out=ROOT/'static/sprite-audit';out.mkdir(exist_ok=True)
    directions=[(0,1,'E'),(45,1,'SE'),(90,1,'S'),(45,-1,'SW'),(0,-1,'W'),(-45,-1,'NW'),(-90,1,'N'),(-45,1,'NE')]
    for view,facing,name in directions:
        canvas=pg.Surface((1280,2000));canvas.fill((98,109,119))
        canvas.blit(font.render(f'AIM {name}: upper block travel E SE S SW; lower W NW N NE; rows keys 0 1 2 3',True,(250,231,191)),(12,8))
        for row in range(4):
            for col,(travel,side,_) in enumerate(directions):
                sprite,anchor,_=animated_sprite('player',row/4,True,facing,view,0,view=view,move_angle=travel,move_facing=side)
                point=pg.Vector2(160+(col%4)*320,242+(row+(col//4)*4)*246)
                canvas.blit(pg.transform.scale_by(sprite,2),point-anchor*2)
        pg.image.save(canvas,str(out/f'{name}.png'))
    canvas=pg.Surface((1280,2000));canvas.fill((98,109,119))
    for row,(moving,recoil,label) in enumerate(((False,0,'IDLE'),(False,.08,'FIRE'),(True,0,'WALK'),(True,.08,'WALK FIRE'))):
        canvas.blit(font.render(label,True,(250,231,191)),(12,row*246+8))
        for col,(view,facing,_) in enumerate(directions):
            sprite,anchor,_=animated_sprite('player',0,moving,facing,view,recoil,view=view)
            canvas.blit(pg.transform.scale_by(sprite,2),pg.Vector2(160+(col%4)*320,242+(row+(col//4)*4)*246)-anchor*2)
    pg.image.save(canvas,str(out/'states.png'))
    (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Ashgate sprite audit</title><style>body{background:#20242c;color:#eee;font:18px system-ui;margin:24px}a{color:#efc575}img{display:block;max-width:100%;margin:16px 0}details{margin:20px 0}</style><h1>Ashgate sprite audit</h1><p>Every travel direction and four walk keys; standing, firing, walking, and walking fire share the same body layers. Click images for full resolution.</p>'+''.join(f'<details><summary>{name}</summary><a href="{name}.png"><img loading="lazy" src="{name}.png"></a></details>' for name in ['E','SE','S','SW','W','NW','N','NE','states'])+'<p><a href="seams.json">Exhaustive alpha-overlap report</a></p>')
    pg.quit()


if __name__=='__main__':main()
