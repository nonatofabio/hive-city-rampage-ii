"""Pack complete Blender-rendered poses. No limb cropping or image rotations."""
from pathlib import Path
import json
import os
import sys
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
import pygame as pg
ROOT=Path(__file__).resolve().parents[2]
DIRECTORY=ROOT/'src/pyg/assets/rendered'
if '--upper-body' in sys.argv:DIRECTORY=DIRECTORY/'upper'
pg.display.init();pg.display.set_mode((1,1))
# Keep already-packed models when rebuilding only the additional directions.
manifest_path=DIRECTORY/'sprites.json'
manifest=json.loads(manifest_path.read_text()) if manifest_path.exists() else {'version':1,'models':{}}
manifest['sources']=['art/blender/ashgate_sprite_rigs.blend','art/blender/ashgate_direction_rigs.blend','art/blender/ashgate_aim_rigs.blend']
if '--upper-body' in sys.argv:manifest['sources']=['art/blender/ashgate_upper_rigs.blend']
for path in sorted(DIRECTORY.glob('*_frames.json')):
    model=path.stem.removesuffix('_frames')
    source=json.loads(path.read_text());w,h=source['cell']
    entry={'cell':[w,h],'anchor':source['anchor'],'size':source.get('size',[w-48,h-48]),'aim_angles':source.get('aim_angles'),'clips':{}}
    for name,clip in source['clips'].items():
        sheet=pg.Surface((w*clip['count'],h),pg.SRCALPHA)
        for i,frame in enumerate(clip['frames']):
            image=pg.image.load(str(DIRECTORY/frame['file'])).convert_alpha()
            if image.get_size()!=(w,h):raise ValueError('Unexpected frame dimensions')
            sheet.blit(image,(i*w,0))
        filename=f'{model}_{name}_poses.png' if '_aim_' in name else f'{model}_{name}.png'
        pg.image.save(sheet,str(DIRECTORY/filename))
        entry['clips'][name]={'sheet':filename,'count':clip['count'],'muzzles':[f['muzzle'] for f in clip['frames']],'barrels':[f.get('barrel',f['muzzle']) for f in clip['frames']],'ejections':[f.get('ejection',f['muzzle']) for f in clip['frames']]}
        if all('waist' in f for f in clip['frames']):entry['clips'][name]['waists']=[f['waist'] for f in clip['frames']]
    manifest['models'][model]=entry
(DIRECTORY/'sprites.json').write_text(json.dumps(manifest,indent=2)+'\n')
pg.quit()
print('Packed '+', '.join(manifest['models']))
