"""Render reproducible effects, death-pose, and baked-lighting review artifacts."""
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
from siege_effects import effect,death_sprite,BLAST_DURATION,add_light
from siege_motion import animated_sprite
from isometric_game import Siege,Renderer,V,project


def main():
    pg.init();pg.display.set_mode((1100,680))
    canvas=pg.Surface((1100,680));font=pg.font.Font(None,25)
    ffmpeg=shutil.which('ffmpeg')
    if not ffmpeg:raise RuntimeError('ffmpeg is required for this preview tool')
    out=ROOT/'static/ashgate-effects.mp4'
    encoder=subprocess.Popen([ffmpeg,'-y','-loglevel','error','-f','rawvideo','-pixel_format','rgb24','-video_size','1100x680','-framerate','30','-i','-','-an','-c:v','libx264','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(out)],stdin=subprocess.PIPE)
    try:
        for i in range(240):
            t=i/30;canvas.fill((28,31,38))
            canvas.blit(font.render('ASHGATE // FIRE, BLAST & ENEMY DEATH POSES',True,(224,184,104)),(28,20))
            add_light(canvas,(210,265),150,(88,33,5),.4)
            sprite,anchor=effect('fire',t)
            canvas.blit(pg.transform.scale_by(sprite,1.65),V(210,265)-anchor*1.65)
            age=t%2
            if age<BLAST_DURATION:
                add_light(canvas,(760,265),190,(round(140*max(0,1-age/.35)),round(65*max(0,1-age/.35)),5),.4)
                sprite,anchor=effect('explosion',age)
                canvas.blit(sprite,V(760,265)-anchor)
            canvas.blit(font.render('LOOPING FIRE',True,(192,197,207)),(128,295))
            canvas.blit(font.render('IGNITION / EXPANSION / SMOKE',True,(192,197,207)),(605,295))
            for j,kind in enumerate(('grunt','rifle','boss')):
                foot=V(190+j*355,610);phase=t%2.5
                scale=1.7 if kind!='boss' else .95
                pg.draw.ellipse(canvas,(17,19,24),(foot.x-70,foot.y-9,140,20))
                if phase<.5:
                    sprite,anchor,_=animated_sprite(kind,0,False,1,0,0,t)
                else:sprite,anchor=death_sprite(kind,phase-.5,1)
                canvas.blit(pg.transform.scale_by(sprite,scale),foot-anchor*scale)
                canvas.blit(font.render(kind.upper()+' / COLLAPSE',True,(192,197,207)),(foot.x-100,640))
            if i==22:pg.image.save(canvas,str(ROOT/'static/ashgate-effects.png'))
            encoder.stdin.write(pg.image.tobytes(canvas,'RGB'))
        encoder.stdin.close()
        if encoder.wait()!=0:raise RuntimeError('ffmpeg failed')
    finally:
        if encoder.poll() is None:encoder.kill();encoder.wait()
    game=Siege(seed=42);game.enemies=[];game.player.pos=V(730,320)
    game.camera=project(game.player.pos)-V(385,285);game.time=.3;game.message_timer=0
    renderer=Renderer();renderer.draw(game)
    pg.image.save(renderer.surface,str(ROOT/'static/ashgate-scenery.png'))
    lit=renderer.surface.copy();renderer.floor=renderer.build_floor(baked=False);renderer.draw(game)
    comparison=pg.Surface((960,590));comparison.blit(renderer.surface,(0,0),pg.Rect(0,0,480,540));comparison.blit(lit,(480,0),pg.Rect(480,0,480,540))
    pg.draw.line(comparison,(220,184,108),(480,0),(480,540),2)
    comparison.blit(font.render('BASE PAVEMENT',True,(220,184,108)),(24,557))
    comparison.blit(font.render('BAKED WINDOW + FIRE LIGHT',True,(220,184,108)),(500,557))
    pg.image.save(comparison,str(ROOT/'static/ashgate-lighting.png'))
    pg.quit();print(out)


if __name__=='__main__':main()
