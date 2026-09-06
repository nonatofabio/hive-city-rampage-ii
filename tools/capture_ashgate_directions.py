"""Capture the actual runtime view selection, walking and muzzle sockets."""
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/pyg'))
import pygame as pg
from siege_motion import animated_sprite
from siege_effects import weapon_effect
from isometric_game import Siege,unproject


def main():
    pg.init();pg.display.set_mode((1000,650))
    canvas=pg.Surface((1000,650));font=pg.font.Font(None,25)
    out=ROOT/'static/ashgate-directions.mp4'
    ffmpeg=shutil.which('ffmpeg')
    if not ffmpeg:raise RuntimeError('ffmpeg required for preview encoding')
    encoder=subprocess.Popen([ffmpeg,'-y','-loglevel','error','-f','rawvideo','-pixel_format','rgb24','-video_size','1000x650','-framerate','30','-i','-','-an','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(out)],stdin=subprocess.PIPE)
    game=Siege();actor=game.player
    try:
        for i in range(300):
            t=i/30;canvas.fill((31,33,39))
            canvas.blit(font.render('FIVE SOURCE VIEWS // MIRRORED LEFT & RIGHT',True,(226,188,106)),(28,20))
            for j,(a,label) in enumerate([(-90,'UP'),(-45,'SIDE UP'),(0,'SIDE'),(45,'SIDE DOWN'),(90,'DOWN')]):
                sprite,anchor,muzzle=animated_sprite('player',t*1.7,i>=150,1,a,0,t)
                foot=pg.Vector2(100+200*j,258)
                canvas.blit(pg.transform.scale_by(sprite,1.8),foot-anchor*1.8)
                # Gold markers are the same muzzle sockets used by live shots.
                pg.draw.circle(canvas,(235,188,80),foot+(muzzle-anchor)*1.8,3)
                canvas.blit(font.render(label,True,(185,190,202)),(55+200*j,280))
            phase=t/5*math.tau
            delta=pg.Vector2(math.cos(phase),math.sin(phase))*150
            recoil=max(0,.105-t%.3)
            game.time=t;actor.stride=t*1.7;actor.moving=i>=150;actor.recoil=recoil
            game.aim_weapon(actor,actor.pos+unproject(delta/2))
            sprite,anchor,muzzle=animated_sprite('player',actor.stride,actor.moving,actor.facing,actor.aim_angle,recoil,t,view=actor.aim_view)
            foot=pg.Vector2(500,574);scale=2
            pg.draw.ellipse(canvas,(20,22,26),(453,565,94,20))
            canvas.blit(pg.transform.scale_by(sprite,scale),foot-anchor*scale)
            tip=foot+(muzzle-anchor)*scale
            target=foot-pg.Vector2(0,55*scale)+delta
            pg.draw.circle(canvas,(132,173,196),target,9,1)
            if recoil>.065:
                flash,origin=weapon_effect('muzzle_'+str(i%2),target-tip)
                canvas.blit(pg.transform.scale_by(flash,scale),tip-origin*scale)
            canvas.blit(font.render('Mouse orbit + recoil / '+('walking' if i>=150 else 'standing'),True,(180,187,198)),(28,610))
            if i==0:pg.image.save(canvas,str(ROOT/'static/ashgate-directions.png'))
            encoder.stdin.write(pg.image.tobytes(canvas,'RGB'))
        encoder.stdin.close()
        if encoder.wait()!=0:raise RuntimeError('ffmpeg failed')
    finally:
        if encoder.poll() is None:encoder.kill();encoder.wait()
        pg.quit()
    print(out)


if __name__=='__main__':main()
