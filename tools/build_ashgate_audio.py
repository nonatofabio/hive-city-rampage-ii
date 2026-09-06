"""Rebuild the original Ashgate weapon/foley mixes from bundled CC0 samples.

No downloads, NumPy, DAW, or Blender required. Sources and licenses live in
src/pyg/assets/audio. Output is deterministic mono 44.1 kHz PCM WAV.
"""
from array import array
from functools import lru_cache
import math
import os
from pathlib import Path
import random
import wave

os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame as pg

ROOT = Path(__file__).resolve().parents[1]/'src/pyg/assets/audio'
RATE = 44100


@lru_cache(maxsize=32)
def source(name):
    return array('h', pg.mixer.Sound(str(ROOT/'source'/f'{name}.ogg')).get_raw())


def layer(output, name, gain=1., pitch=1., delay=0., decay=None):
    data = source(name)
    start = int(delay*RATE)
    for i in range(start,len(output)):
        t = i-start
        index = t*pitch
        j = int(index)
        if j+1 >= len(data):
            break
        sample = data[j]+(data[j+1]-data[j])*(index-j)
        envelope = math.exp(-t/RATE/decay) if decay else 1.
        output[i] += sample/32768*gain*envelope


def save(name, output):
    # Soft limiting plus fixed headroom avoids clipping when voices overlap.
    peak = max(abs(x) for x in output) or 1
    scale = .78/max(1.,peak)
    samples = array('h')
    for i,value in enumerate(output):
        edge = min(1.,i/100,(len(output)-i-1)/450)
        samples.append(round(max(-.95,min(.95,value*scale))*edge*32767))
    with wave.open(str(ROOT/f'{name}.wav'),'wb') as f:
        f.setparams((1,2,RATE,0,'NONE','not compressed'))
        f.writeframes(samples.tobytes())


def build():
    pg.mixer.init(RATE,-16,1)
    try:
        for variant in range(4):
            rng = random.Random(601+variant)
            pitch = .90+variant*.055
            output = [0.] * int(RATE*.24)
            layer(output, 'explosionCrunch_000', 1.5, pitch*1.25, decay=.055)
            layer(output, 'impactMetal_heavy_000', .65, pitch*.85, .008, .065)
            layer(output, 'impactMetal_light_001', .8, pitch*1.3, .075, .035)
            # A short sub-pressure thump gives the bolter a ballistic chest hit.
            for i in range(len(output)):
                t = i/RATE
                output[i] += .48*math.sin(math.tau*(95*t-100*t*t))*math.exp(-t/ .041)
                output[i] += rng.uniform(-.20,.20)*math.exp(-t/.016)
            save(f'bolter_{variant}', output)
    finally:
        pg.mixer.quit()
    print('Built four bolter mixes from bundled CC0 sources.')


if __name__ == '__main__':
    build()
