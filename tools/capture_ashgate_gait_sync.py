"""Exhaustive visual review: eight torso directions x eight travel directions."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/pyg'))
import pygame as pg
from siege_motion import animated_sprite
DIRECTIONS=[(0,1,'E'),(45,1,'SE'),(90,1,'S'),(45,-1,'SW'),(0,-1,'W'),(-45,-1,'NW'),(-90,1,'N'),(-45,1,'NE')]


def main():
    pg.init();pg.display.set_mode((1080,1240));screen=pg.Surface((1080,1240));font=pg.font.Font(None,20)
    encoder=subprocess.Popen([shutil.which('ffmpeg'),'-y','-loglevel','error','-f','rawvideo','-pixel_format','rgb24','-video_size','1080x1240','-framerate','12','-i','-','-an','-c:v','libx264','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(ROOT/'static/ashgate-gait-sync.mp4')],stdin=subprocess.PIPE)
    try:
        for i in range(72):
            screen.fill((32,36,44))
            screen.blit(font.render('ROWS: TORSO AIM / COLUMNS: TRAVEL / 64 DIRECTION COMBINATIONS',True,(224,192,125)),(12,8))
            for col,(_,_,label) in enumerate(DIRECTIONS):screen.blit(font.render(label,True,(230,211,164)),(86+col*128,35))
            for row,(view,facing,label) in enumerate(DIRECTIONS):
                screen.blit(font.render(label,True,(230,211,164)),(8,100+row*146))
                for col,(travel,side,_) in enumerate(DIRECTIONS):
                    sprite,anchor,_=animated_sprite('player',i/12,True,facing,view,0,i/12,view=view,move_angle=travel,move_facing=side)
                    ground=pg.Vector2(94+col*128,188+row*146)
                    pg.draw.line(screen,(56,64,74),ground+(-45,1),ground+(45,1))
                    screen.blit(sprite,ground-anchor)
            if i==3:pg.image.save(screen,str(ROOT/'static/ashgate-gait-sync.png'))
            encoder.stdin.write(pg.image.tobytes(screen,'RGB'))
        encoder.stdin.close()
        if encoder.wait()!=0:raise RuntimeError('ffmpeg failed')
    finally:
        if encoder.poll() is None:encoder.kill();encoder.wait()
        pg.quit()


if __name__=='__main__':main()
