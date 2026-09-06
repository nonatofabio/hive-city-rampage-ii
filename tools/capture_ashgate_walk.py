"""Review authored walks in five views and independent movement/aim in gameplay."""
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/pyg'))
import pygame as pg
from isometric_game import Siege,Renderer,V,project,unproject
from siege_motion import animated_sprite


def main():
    pg.init();pg.display.set_mode((960,780));screen=pg.Surface((960,780));font=pg.font.Font(None,21)
    game=Siege();game.cover=[];game.relays=[];game.enemies=[];game.spawn_timer=100
    game.player.pos=V(1000,330);game.camera=project(game.player.pos)-V(480,285);game.message_timer=0
    renderer=Renderer()
    encoder=subprocess.Popen([shutil.which('ffmpeg'),'-y','-loglevel','error','-f','rawvideo','-pixel_format','rgb24','-video_size','960x780','-framerate','30','-i','-','-an','-c:v','libx264','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(ROOT/'static/ashgate-walk.mp4')],stdin=subprocess.PIPE)
    try:
        for i in range(360):
            t=i/30;screen.fill((32,36,44))
            screen.blit(font.render('WALK / STOP / FIRE // SHARED BODY LAYERS',True,(221,188,116)),(18,10))
            for j,view in enumerate((0,-45,-90,45,90)):
                stride=(int(t//4)*3+min(t%4,3))*1.15
                sprite,anchor,_=animated_sprite('player',stride,t%4<3,1,view,.08 if t%4>3.3 else 0,t,view=view,move_angle=view)
                screen.blit(pg.transform.scale_by(sprite,1.7),V(96+j*192,211)-anchor*1.7)
            movement=V(math.cos(t*math.tau/6),math.sin(t*math.tau/6)) if t%4<3 else V()
            game.update(1/30,movement,game.player.pos+unproject(V(300,55)),shooting=t%3<1)
            renderer.draw(game);screen.blit(renderer.surface,(0,240))
            if i==77:pg.image.save(screen,str(ROOT/'static/ashgate-walk.png'))
            encoder.stdin.write(pg.image.tobytes(screen,'RGB'))
        encoder.stdin.close()
        if encoder.wait()!=0:raise RuntimeError('ffmpeg failed')
    finally:
        if encoder.poll() is None:encoder.kill();encoder.wait()
        pg.quit()


if __name__=='__main__':main()
