"""Render every audited runtime torso/leg combination into labelled contact sheets.
Uses the same atlas sockets, mirroring, gait enumeration and offsets as seam_audit.
Outputs a browsable gallery and machine-readable pose index under godot/artifacts.
"""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
import seam_audit as audit

OUT = audit.ROOT / 'artifacts/player-combinations'
OUT.mkdir(parents=True, exist_ok=True)
W,H,COLS,ROWS = 120,152,12,12

def combinations():
 for view,model in audit.VIEWS.items():
  data=audit.models[model]; cw,ch=map(int,data['cell'])
  for name,clip in data['clips'].items():
   if '/upper/' not in clip['path']: continue
   sheet=audit.img(clip['path'])
   for index in range(int(clip['count'])):
    for facing in [1,-1]:
     upper=sheet[:ch,index*cw:(index+1)*cw]
     if facing<0 and abs(view)!=90: upper=upper[:,::-1]
     gaits=set()
     if name.startswith('walk'):
      for travel in audit.VIEWS:
       for side in [1,-1]:
        gaits.add(audit.gait_pose(view,facing,travel,side,index/clip['count']))
     else: gaits.update([(view,facing,0),(view,facing,2)])
     for gait in sorted(gaits):
      yield model,name,index,facing,gait,upper

def compose(model,name,index,facing,gait,upper):
 origin=audit.lower_origin(model,name,index,facing,gait)
 vertical=abs(gait[0])==90
 step=gait[2]%2 if vertical else gait[2]
 flip=gait[2]>=2 if vertical else gait[1]<0
 lower=audit.img(f'assets/rendered/walk/{gait[0]}.png')[:,step*80:(step+1)*80]
 if flip: lower=lower[:,::-1]
 canvas=Image.new('RGBA',(W,H),(25,28,33,255))
 anchor=np.array(audit.models[model]['anchor'],float)
 anchor[1]+=audit.reg['ground_shift'][model]
 if facing<0 and model not in ['player_n','player_s']: anchor[0]=upper.shape[1]-anchor[0]
 base=np.array([W//2,122])-np.rint(anchor).astype(int)
 canvas.alpha_composite(Image.fromarray(lower),tuple(map(int,base+origin)))
 canvas.alpha_composite(Image.fromarray(upper),tuple(map(int,base)))
 d=ImageDraw.Draw(canvas)
 d.line([(0,123),(W,123)],fill=(60,70,78),width=1)
 points=audit.belt_points(gait)+origin
 valid=(points[:,0]>=0)&(points[:,0]<upper.shape[1])&(points[:,1]>=0)&(points[:,1]<upper.shape[0])
 q=points[valid]; overlap=int((upper[q[:,1],q[:,0],3]>64).sum())
 d.text((3,2),model.replace('player','P'),fill='white')
 d.text((3,13),name.replace('_aim_','@').replace('walk_fire','wf')+f'/{index}',fill='white')
 d.text((3,128),f'F{facing} L{gait} O{overlap}',fill='white')
 return canvas,overlap

def main():
 records=[]; worst=[]; page=None; pages=[]
 for n,args in enumerate(combinations()):
  if n%(COLS*ROWS)==0:
   if page is not None: page.save(OUT/pages[-1])
   page=Image.new('RGB',(W*COLS,H*ROWS),(25,28,33)); pages.append(f'page-{len(pages):03d}.png')
  frame,overlap=compose(*args)
  slot=n%(COLS*ROWS); page.paste(frame,((slot%COLS)*W,(slot//COLS)*H))
  records.append({'model':args[0],'clip':args[1],'frame':args[2],'facing':args[3],'gait':args[4],'overlap':overlap,'page':pages[-1],'slot':slot})
  worst.append((overlap,n,frame))
  if len(worst)>96: worst=sorted(worst,key=lambda x:x[:2])[:48]
 if page is not None: page.save(OUT/pages[-1])
 worst=sorted(worst,key=lambda x:x[:2])[:48]
 preview=Image.new('RGB',(W*8,H*6),(25,28,33))
 for i,(_,_,frame) in enumerate(worst): preview.paste(frame,((i%8)*W,(i//8)*H))
 preview.resize((W*16,H*12),Image.Resampling.NEAREST).save(OUT/'lowest-overlap.png')
 (OUT/'index.json').write_text(json.dumps(records))
 (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Player pose audit</title><style>body{background:#191c21;color:white;font:16px sans-serif}img{max-width:100%;image-rendering:pixelated}</style><h1>'+str(len(records))+' player combinations</h1>'+''.join(f'<h2>{p}</h2><img loading="lazy" src="{p}">' for p in pages))
 print(f'RENDER PASS: {len(records)} combinations in {len(pages)} pages: {OUT}')
if __name__=='__main__': main()
