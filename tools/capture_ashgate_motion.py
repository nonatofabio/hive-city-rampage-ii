"""Render a six-second, silent animation review using the live sprite rig.

Requires ffmpeg on PATH; it is a developer tool, not a game dependency.
"""
import argparse
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys

os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/pyg'))
import pygame as pg
from siege_motion import animated_sprite


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=Path('static/ashgate-motion.mp4'))
    args=parser.parse_args()
    ffmpeg=shutil.which('ffmpeg')
    if not ffmpeg:
        parser.error('ffmpeg is required to encode the preview')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    pg.init()
    pg.display.set_mode((960,540))
    surface=pg.Surface((960,540))
    font=pg.font.Font(None,24)
    encoder=subprocess.Popen([ffmpeg,'-y','-loglevel','error','-f','rawvideo','-pixel_format','rgb24','-video_size','960x540','-framerate','30','-i','-','-an','-c:v','libx264','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(args.output)],stdin=subprocess.PIPE)
    try:
        for i in range(180):
            t=i/30
            surface.fill((30,32,37))
            surface.blit(font.render('ASHGATE // WALK, WEAPON RECOIL & SIEGE-WALKER WINDUP',True,(210,178,106)),(35,25))
            for j,(kind,label) in enumerate([('player','ARMORED STRIDE'),('rifle','INDEPENDENT GUN'),('boss','HYDRAULIC WINDUP')]):
                x=160+j*320
                pg.draw.line(surface,(75,72,66),(x-125,415),(x+125,415),2)
                moving= j==0 or j==2 and t%3<1.5
                recoil=max(0,.105-t%.30) if j==1 else 0
                angle=math.sin(t*1.8)*60 if j==1 else 0
                windup=(1.25-(t%3-1.5)) if j==2 and 1.5<t%3<2.75 else 0
                sprite,anchor,muzzle=animated_sprite(kind,t*(1.7 if j==0 else .55),moving,1,angle,recoil,t,windup)
                scale=2 if j<2 else 1.2
                sprite=pg.transform.scale(sprite,(round(sprite.get_width()*scale),round(sprite.get_height()*scale)))
                foot=pg.Vector2(x,414)
                surface.blit(sprite,foot-anchor*scale)
                if recoil>.065:
                    tip=foot+(muzzle-anchor)*scale
                    pg.draw.circle(surface,(255,217,103),tip,7)
                surface.blit(font.render(label,True,(190,190,184)),(x-105,455))
            surface.blit(font.render('Blender weighted sprite rig | cleaned textures | bolter gunfire in-game',True,(133,144,156)),(35,500))
            encoder.stdin.write(pg.image.tostring(surface,'RGB'))
        encoder.stdin.close()
        if encoder.wait()!=0:
            raise RuntimeError('ffmpeg failed')
    finally:
        if encoder.poll() is None:
            encoder.kill()
            encoder.wait()
        pg.quit()
    print(args.output)


if __name__=='__main__':main()
