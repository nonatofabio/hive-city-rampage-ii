"""Import existing sprite silhouettes for Blender without altering source art."""
from pathlib import Path
import os
import sys
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
import pygame as pg
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'art/blender/textures'
sys.path.insert(0,str(ROOT/'src/pyg'))
from sprite_import import cutout
REGIONS={'player':(60,50,340,394),'grunt':(450,70,320,352),'rifle':(800,85,290,365),'boss':(1130,0,406,530)}
pg.display.init();pg.display.set_mode((1,1))
clean=ROOT/'src/pyg/assets/ashgate_atlas_clean.png'
sheet=pg.image.load(str(clean if clean.exists() else ROOT/'src/pyg/assets/ashgate_atlas_cutout.png')).convert_alpha()
OUT.mkdir(parents=True,exist_ok=True)
for name,rect in REGIONS.items():
 sprite=cutout(sheet,rect,magenta=clean.exists())
 pg.image.save(sprite,str(OUT/(name+'.png')))
pg.quit()
