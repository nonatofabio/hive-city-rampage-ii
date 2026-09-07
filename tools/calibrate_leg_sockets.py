"""Measure each leg frame's pelvis center from its upper belt band.
Pixel-center coordinates preserve mirror symmetry. Does not rewrite sprite pixels.
"""
import json
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'godot/assets/data/player_registration.json'
r=json.loads(p.read_text()); r['leg_waists']={}
for view in [-90,-45,0,45,90]:
 a=np.array(Image.open(ROOT/f'godot/assets/rendered/walk/{view}.png'))
 sockets=[]
 for frame in range(4):
  mask=a[12:17,frame*80:(frame+1)*80,3]>64
  _,xs=np.where(mask)
  sockets.append([round(float(xs.mean()+.5),3),12])
 r['leg_waists'][str(view)]=sockets
p.write_text(json.dumps(r,indent=2)+'\n')
print('Measured 20 leg-frame pelvis sockets')
