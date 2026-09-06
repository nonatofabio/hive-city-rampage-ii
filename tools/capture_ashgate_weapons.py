"""Review actual aiming/shot geometry, heavy stride, and transparent final fades."""
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/pyg'))
import pygame as pg
from isometric_game import Siege,V,project,unproject
from siege_motion import animated_sprite
from siege_effects import weapon_effect,death_sprite,effect,faded


def main():
    pg.init();pg.display.set_mode((1100,760));screen=pg.Surface((1100,760));font=pg.font.Font(None,25)
    encoder=subprocess.Popen([shutil.which('ffmpeg'),'-y','-loglevel','error','-f','rawvideo','-pixel_format','rgb24','-video_size','1100x760','-framerate','30','-i','-','-an','-c:v','libx264','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(ROOT/'static/ashgate-weapons.mp4')],stdin=subprocess.PIPE)
    game=Siege();game.cover=[];game.relays=[];a=game.player;scale=2.4;foot=V(550,442);last=-1
    try:
        for i in range(300):
            t=i/30;game.time=t;a.moving=True;a.stride=t*1.65
            target=foot-V(0,55*scale)+V(math.cos(t*math.tau/5)*355,math.sin(t*math.tau/5)*170)
            aim=a.pos+unproject((target-foot)/scale+V(0,55))
            a.recoil=max(0,.105-(t-last));game.aim_weapon(a,aim)
            if t-last>=.105:
                a.recoil=.105;game.fire_weapon(a,aim,950,24);last=t
            screen.fill((32,36,44));screen.blit(font.render('HEAVY STRIDE // BARREL AIM // SPRITE PROJECTILES',True,(221,188,116)),(24,20))
            pg.draw.ellipse(screen,(22,25,31),(500,431,100,25))
            sprite,anchor,muzzle=animated_sprite('player',a.stride,True,a.facing,a.aim_angle,a.recoil,t,view=a.aim_view)
            screen.blit(pg.transform.scale_by(sprite,scale),foot-anchor*scale)
            tip=foot+(muzzle-anchor)*scale
            pg.draw.circle(screen,(127,173,194),target,9,1)
            if a.recoil>.065:
                image,origin=weapon_effect('muzzle_'+str(i%2),target-tip)
                screen.blit(pg.transform.scale_by(image,scale),tip-origin*scale)
            for shot in game.shots:
                point=foot+(project(shot.pos-a.pos)-V(0,55))*scale
                image,origin=weapon_effect('bolt',project(shot.velocity))
                screen.blit(pg.transform.scale_by(image,scale),point-origin*scale)
                shot.pos+=shot.velocity/30;shot.life-=1/30
            game.shots=[b for b in game.shots if b.life>.85]
            screen.blit(font.render('Final-frame fade checks on a light background',True,(205,211,221)),(24,510))
            phase=(t%2.5)/2.5
            for j,name in enumerate(('grunt','rifle','boss','explosion')):
                panel=pg.Rect(20+j*270,555,250,160);pg.draw.rect(screen,(113,134,150),panel)
                image,origin=effect('explosion',1.04) if name=='explosion' else death_sprite(name,19,1)
                image=faded(image,1-phase)
                factor=.5 if name in ('boss','explosion') else 1
                image=pg.transform.scale_by(image,factor)
                screen.blit(image,V(panel.centerx,panel.bottom-8)-origin*factor)
                screen.blit(font.render(name.upper(),True,(205,211,221)),(panel.x,panel.bottom+10))
            if i==41:pg.image.save(screen,str(ROOT/'static/ashgate-weapons.png'))
            encoder.stdin.write(pg.image.tobytes(screen,'RGB'))
        encoder.stdin.close()
        if encoder.wait()!=0:raise RuntimeError('ffmpeg failed')
    finally:
        if encoder.poll() is None:encoder.kill();encoder.wait()
        pg.quit()


if __name__=='__main__':main()
