import os
from pathlib import Path
import sys
import unittest
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/pyg'))
import pygame as pg
from isometric_game import Siege,V,project
from siege_hud import auspex,status_hud,servo_saying
from siege_motion import ejection_offset
from siege_effects import casing_sprite


class HUDAndCasingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pg.init();pg.display.set_mode((960,540));cls.font=pg.font.Font(None,17)

    @classmethod
    def tearDownClass(cls):pg.quit()

    def test_status_has_no_enclosing_background_and_map_is_translucent(self):
        game=Siege();game.time=1
        screen=pg.Surface((960,540));screen.fill((92,117,139))
        status_hud(screen,game,self.font,self.font)
        self.assertEqual(screen.get_at((250,100))[:3],(92,117,139))
        panel=auspex(game,self.font)
        self.assertLess(panel.get_at((4,82)).a,128)
        self.assertGreater(panel.get_at((4,82)).a,0)
        self.assertEqual(panel.get_size(),(132,88))

    def test_servo_sayings_cycle_and_have_quiet_intervals(self):
        first,alpha=servo_saying(1)
        self.assertGreater(alpha,0)
        self.assertEqual(servo_saying(4)[1],0)
        self.assertNotEqual(first,servo_saying(7.5)[0])

    def test_casing_origin_matches_the_rendered_receiver(self):
        game=Siege();game.cover=[];game.relays=[]
        actor=game.player;actor.recoil=.105;game.aim=actor.pos+V(250,100)
        game.aim_weapon(actor,game.aim);game.eject_casing(actor)
        position,velocity,age,height,vz=game.casings[-1]
        port=ejection_offset('player',actor.stride,actor.moving,actor.facing,actor.aim_angle,actor.recoil,game.time,actor.aim_view)
        self.assertLess((project(position-actor.pos)-V(0,height)-port).length(),.001)
        self.assertGreater(vz,0)
        self.assertGreater(casing_sprite(0,False).get_width(),8)

    def test_casing_bounces_then_settles_and_expires(self):
        game=Siege();game.enemies=[];game.cover=[];game.relays=[];game.spawn_timer=100
        game.casings=[[V(1300,400),V(30,0),0.,2.,-150.]]
        game.update(.03)
        self.assertGreater(game.casings[0][4],0)
        for _ in range(100):game.update(.02)
        self.assertEqual(game.casings[0][3:],[0.,0.])
        game.casings[0][2]=7.99;game.update(.02)
        self.assertFalse(game.casings)


if __name__=='__main__':unittest.main()
