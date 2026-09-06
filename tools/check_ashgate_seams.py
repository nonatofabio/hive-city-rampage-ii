"""Check actual alpha overlap for every torso frame and compatible leg pose."""
import json
import os
from pathlib import Path
import sys
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/pyg'))
import pygame as pg
from siege_motion import upper_manifest,upper_sheet,lower_body,lower_origin,gait_pose


def main():
    pg.display.init();pg.display.set_mode((1,1))
    report={};total=0
    for model,data in upper_manifest().items():
        view={'player':0,'player_ne':-45,'player_n':-90,'player_se':45,'player_s':90}[model]
        w,h=data['cell'];minimum=100000;worst=None
        for clip,meta in data['clips'].items():
            sheet=upper_sheet(model,clip)
            for index in range(meta['count']):
                key=(model,clip,index)
                for facing in (1,-1):
                    upper=sheet.subsurface((index*w,0,w,h))
                    if facing<0 and abs(view)!=90:upper=pg.transform.flip(upper,True,False)
                    mask=pg.mask.from_surface(upper,64)
                    poses={(view,facing,0),(view,facing,2)} if not clip.startswith('walk') else {gait_pose(view,facing,travel,side,index/meta['count']) for travel in (-90,-45,0,45,90) for side in (1,-1)}
                    for leg,side,step in poses:
                        lower=lower_body(leg,side,step)
                        belt=pg.Surface(lower.get_size(),pg.SRCALPHA);belt.blit(lower,(0,12),(0,12,80,12))
                        overlap=mask.overlap_area(pg.mask.from_surface(belt,64),lower_origin(key,facing))
                        if overlap<minimum:minimum=overlap;worst=[clip,index,facing,leg,side,step]
                        total+=1
        report[model]={'minimum_belt_overlap_pixels':minimum,'worst_case':worst}
    report['checked_combinations']=total
    (ROOT/'static/sprite-audit/seams.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2));pg.quit()
    if any(v['minimum_belt_overlap_pixels']<32 for k,v in report.items() if k!='checked_combinations'):raise SystemExit('Insufficient belt overlap')


if __name__=='__main__':main()
