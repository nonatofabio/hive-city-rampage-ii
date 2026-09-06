"""Gunfire only. The rejected music and other effects are not loaded or shipped."""
from pathlib import Path
import random
import pygame as pg

AUDIO_DIR = Path(__file__).with_name('assets')/'audio'


class Audio:
    def __init__(self, sfx_volume=.8, muted=False, directory=AUDIO_DIR):
        self.sfx_volume = max(0.,min(1.,sfx_volume))
        self.muted, self.paused = muted, False
        self.available = bool(pg.mixer.get_init())
        self.sounds, self.missing = {}, []
        self.rng = random.Random(718)
        self.last_variant = {}
        self.next_voice = 0
        if not self.available:
            return
        pg.mixer.set_num_channels(4)
        bank=[]
        for i in range(4):
            filename=f'bolter_{i}.wav'
            try:
                bank.append(pg.mixer.Sound(str(directory/filename)))
            except (pg.error,FileNotFoundError):
                self.missing.append(filename)
        self.sounds['shot']=bank
        if self.missing:
            print('Gunfire assets unavailable: '+', '.join(self.missing))

    def play(self, name, position=None, listener=None, gain=1.):
        bank=self.sounds.get(name,[])
        if not self.available or self.muted or self.paused or not bank or self.sfx_volume == 0:
            return
        choices=[i for i in range(len(bank)) if i != self.last_variant.get(name)] or [0]
        variant=self.rng.choice(choices)
        self.last_variant[name]=variant
        channel=pg.mixer.Channel(self.next_voice)
        self.next_voice=(self.next_voice+1)%4
        channel.set_volume(.72*self.sfx_volume*gain)
        channel.play(bank[variant])

    def set_paused(self, paused):
        self.paused=paused
        if self.available:
            pg.mixer.pause() if paused else pg.mixer.unpause()

    def toggle_mute(self):
        self.muted=not self.muted
        if self.available and self.muted:
            pg.mixer.stop()

    def close(self):
        if self.available and pg.mixer.get_init():
            pg.mixer.stop()
