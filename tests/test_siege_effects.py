import os
from pathlib import Path
import sys
import unittest
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/pyg'))
import pygame as pg
from isometric_game import Siege,V
from siege_effects import effect,death_sprite,frames,faded,BLAST_DURATION,CORPSE_DURATION


class EffectsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pg.init();pg.display.set_mode((960,540))

    @classmethod
    def tearDownClass(cls):pg.quit()

    def test_lethal_hit_records_one_facing_aware_death(self):
        game=Siege();enemy=game.enemies[0];enemy.facing=-1
        game.hit(enemy,999);score=game.score
        game.hit(enemy,999)
        self.assertEqual(len(game.deaths),1)
        self.assertEqual(game.deaths[0][1:3],[enemy.kind,-1])
        self.assertEqual(game.score,score)
        self.assertEqual(game.kills,1)
        self.assertFalse(any(kind==enemy.kind for _,kind in game.marks))
        game.update(.01)
        self.assertNotIn(enemy,game.enemies)
        self.assertEqual(len(game.deaths),1)

    def test_visual_lifetimes_and_terminal_freeze(self):
        game=Siege();game.enemies=[];game.cover=[];game.relays=[]
        game.explode(V(1800,400),damage=0)
        game.deaths=[[V(1500,400),'grunt',1,CORPSE_DURATION-.01]]
        game.blasts[0][1]=BLAST_DURATION-.01
        game.state='dead';game.update(.05)
        self.assertEqual(len(game.blasts),1)
        self.assertEqual(len(game.deaths),1)
        game.state='playing';game.update(.05)
        self.assertFalse(game.blasts)
        self.assertFalse(game.deaths)

    def test_death_drawings_change_and_hold_final_pose(self):
        for kind in ('grunt','rifle','runner','brute','boss'):
            early=death_sprite(kind,.02,1)
            fallen=death_sprite(kind,.7,1)
            late=death_sprite(kind,12,1)
            self.assertNotEqual(pg.image.tobytes(early[0],'RGBA'),pg.image.tobytes(fallen[0],'RGBA'))
            self.assertIs(fallen[0],late[0])
            self.assertEqual(early[1],fallen[1])
            mirrored=death_sprite(kind,.7,-1)[0]
            self.assertEqual(pg.image.tobytes(mirrored,'RGBA'),pg.image.tobytes(pg.transform.flip(fallen[0],True,False),'RGBA'))

    def test_last_frames_fade_to_background_without_black_or_cache_mutation(self):
        background=(116,139,162)
        for source in (death_sprite('grunt',19,1)[0],death_sprite('brute',19,-1)[0],effect('explosion',1.04)[0]):
            original=pg.image.tobytes(source,'RGBA')
            previous=float('inf')
            for opacity in (1,.5,.1,.01,0):
                image=pg.Surface(source.get_size());image.fill(background)
                image.blit(faded(source,opacity),(0,0))
                difference=sum(abs(image.get_at((x,y))[c]-background[c]) for y in range(image.get_height()) for x in range(image.get_width()) for c in range(3))
                self.assertLessEqual(difference,previous)
                previous=difference
                self.assertEqual(image.get_at((0,0))[:3],background)
            self.assertEqual(previous,0)
            self.assertEqual(pg.image.tobytes(source,'RGBA'),original)

    def test_effect_loop_and_transparent_sheet_registration(self):
        self.assertIs(effect('fire',0)[0],effect('fire',.8)[0])
        self.assertIsNot(effect('explosion',0)[0],effect('explosion',.8)[0])
        for name in ('fire','explosion','death_grunt','death_rifle','death_boss'):
            sizes={sprite.get_size() for sprite in frames(name)}
            self.assertEqual(len(sizes),1)
            for sprite in frames(name):
                self.assertEqual(sprite.get_at((0,0)).a,0)
                self.assertGreater(sprite.get_bounding_rect().width,8)


if __name__=='__main__':unittest.main()
