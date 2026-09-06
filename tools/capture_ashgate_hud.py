"""Capture the compact servo-skull HUD, wrist aiming, knee flex, and brass ejection."""
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


def main():
    pg.init();pg.display.set_mode((960,540))
    game=Siege();game.enemies=[];game.spawn_timer=100;game.player.pos=V(850,330)
    game.camera=project(game.player.pos)-V(385,285);game.message_timer=0
    renderer=Renderer()
    encoder=subprocess.Popen([shutil.which('ffmpeg'),'-y','-loglevel','error','-f','rawvideo','-pixel_format','rgb24','-video_size','960x540','-framerate','30','-i','-','-an','-c:v','libx264','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(ROOT/'static/ashgate-servo-hud.mp4')],stdin=subprocess.PIPE)
    try:
        for i in range(270):
            t=i/30;game.hurt_timer=.5
            aim=game.player.pos+unproject(V(math.cos(t*.7)*240,math.sin(t*.7)*150))
            game.update(1/30,V(math.cos(t*.8)*.6,math.sin(t*.8)*.3),aim,shooting=t%2<1.5)
            renderer.draw(game)
            if i==48:pg.image.save(renderer.surface,str(ROOT/'static/ashgate-servo-hud.png'))
            encoder.stdin.write(pg.image.tobytes(renderer.surface,'RGB'))
        encoder.stdin.close()
        if encoder.wait()!=0:raise RuntimeError('ffmpeg failed')
    finally:
        if encoder.poll() is None:encoder.kill();encoder.wait()
        pg.quit()


if __name__=='__main__':main()
