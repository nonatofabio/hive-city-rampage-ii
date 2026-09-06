import contextlib
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/pyg'))
import pygame as pg
from siege_audio import Audio


class AudioTests(unittest.TestCase):
    def setUp(self):pg.mixer.init(44100,-16,2)
    def tearDown(self):pg.mixer.quit()

    def test_only_gunfire_loads_and_no_music_api_is_used(self):
        with patch.object(pg.mixer.music,'load') as music_load, patch.object(pg.mixer.music,'play') as music_play:
            audio=Audio()
            self.assertFalse(audio.missing)
            self.assertEqual(set(audio.sounds),{'shot'})
            self.assertEqual(len(audio.sounds['shot']),4)
            audio.play('shot')
            self.assertTrue(pg.mixer.Channel(0).get_busy())
            music_load.assert_not_called();music_play.assert_not_called()
            audio.close()

    def test_rejected_events_are_silent(self):
        audio=Audio()
        for name in ('rifle','blast','hit','armor','debris','pickup','shield','dash','step','walker_step','warning','relay','victory'):
            audio.play(name)
        self.assertFalse(pg.mixer.get_busy())
        self.assertFalse(audio.last_variant)
        audio.close()

    def test_variation_mute_and_pause(self):
        audio=Audio();audio.play('shot');first=audio.last_variant['shot']
        audio.play('shot');self.assertNotEqual(first,audio.last_variant['shot'])
        audio.set_paused(True);voice=audio.next_voice;audio.play('shot')
        self.assertEqual(audio.next_voice,voice)
        audio.set_paused(False);audio.toggle_mute()
        self.assertFalse(pg.mixer.get_busy())
        audio.play('shot');self.assertEqual(audio.next_voice,voice)
        audio.close()

    def test_absent_device_and_missing_files_are_safe(self):
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            audio=Audio(directory=Path(tmp));self.assertEqual(len(audio.missing),4)
            audio.play('shot');audio.close()
        pg.mixer.quit();audio=Audio();self.assertFalse(audio.available)
        audio.play('shot');audio.set_paused(True);audio.toggle_mute();audio.close()


if __name__=='__main__':unittest.main()
