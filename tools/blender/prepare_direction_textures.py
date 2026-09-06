"""Import the four generated yaw views; keep the accepted side texture intact."""
from pathlib import Path
import os
import sys
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
import pygame as pg
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src/pyg'))
from sprite_import import cutout
pg.display.init();pg.display.set_mode((1,1))
sheet=pg.image.load(str(ROOT/'src/pyg/assets/ashgate_player_directions.png')).convert_alpha()
w,h=sheet.get_size();cw,ch=w//2,h//2
for name,x,y in [('player_ne',0,0),('player_n',1,0),('player_se',0,1),('player_s',1,1)]:
    sprite=cutout(sheet,(x*cw,y*ch,cw,ch),magenta=True)
    pg.image.save(sprite,str(ROOT/'art/blender/textures'/f'{name}.png'))
    print(name,sprite.get_size())
pg.quit()
