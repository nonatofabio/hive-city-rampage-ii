import os
from pathlib import Path
import sys
import unittest

os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/pyg'))
import pygame as pg
from siege_motion import animated_sprite,muzzle_offset,aim_pose,pose_key,direction_angle,barrel_axis
from isometric_game import Siege,Actor,V,project,unproject,cursor_aim


class MotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pg.init()
        pg.display.set_mode((960,540))

    @classmethod
    def tearDownClass(cls):
        pg.quit()

    def test_rendered_and_simulated_muzzle_match(self):
        for kind in ('player','rifle','grunt'):
            for facing in (-1,1):
                for angle in (-90,-45,0,45,90):
                    args=(kind,.3,True,facing,angle,.08,2.)
                    sprite,anchor,muzzle=animated_sprite(*args)
                    expected=muzzle_offset(*args)
                    self.assertLess((muzzle-anchor-expected).length(),.001)
                    self.assertTrue(sprite.get_rect().collidepoint(muzzle))

    def test_walk_and_gun_are_independent(self):
        def pixels(stride,moving,angle=0,kick=0):
            s,_,_=animated_sprite('player',stride,moving,1,angle,kick)
            return pg.image.tostring(s,'RGBA')
        self.assertNotEqual(pixels(0,True),pixels(.25,True))
        self.assertEqual(pixels(0,False),pixels(.25,False))
        self.assertNotEqual(pixels(0,False),pixels(0,False,45))
        self.assertNotEqual(pixels(0,False),pixels(0,False,0,.105))

    def test_five_player_views_keep_walk_phase(self):
        expected={-90:'player_n',-45:'player_ne',0:'player',45:'player_se',90:'player_s'}
        images=set()
        for angle,model in expected.items():
            key=pose_key('player',.3,True,angle,.08)
            self.assertEqual(key,(model,'walk_fire_aim_'+str(angle),3))
            sprite,_,_=animated_sprite('player',.3,True,1,angle,.08)
            images.add(pg.image.tobytes(sprite,'RGBA'))
        self.assertEqual(len(images),5)

    def test_shots_start_at_each_directional_barrel(self):
        game=Siege();game.cover=[];game.relays=[]
        for degrees in range(-180,180,45):
            delta=V(300,0).rotate(degrees)
            actor=game.player
            actor.facing,actor.aim_angle=aim_pose(unproject(delta),actor.facing)
            actor.recoil=.105
            aim=actor.pos+unproject(delta)
            game.fire_weapon(actor,aim,950,24)
            shot=game.shots[-1]
            _,anchor,muzzle=animated_sprite('player',actor.stride,actor.moving,actor.facing,actor.aim_angle,actor.recoil,game.time,view=actor.aim_view)
            self.assertLess((project(shot.pos-actor.pos)-V(0,55)-(muzzle-anchor)).length(),.001)
            desired=delta-V(0,55)-(muzzle-anchor)
            self.assertAlmostEqual(project(shot.velocity).normalize().dot(desired.normalize()),1)

    def test_barrel_tracks_cursor_across_angles_and_walk_phases(self):
        game=Siege();game.cover=[];game.relays=[]
        actor=game.player;actor.moving=True
        for distance in (120,240,500):
            for degrees in range(-180,180,7):
                actor.stride=(degrees%13)/13;actor.recoil=.105
                target=actor.pos+unproject(V(distance,0).rotate(degrees))
                game.fire_weapon(actor,target,950,24)
                key=pose_key('player',actor.stride,True,actor.aim_angle,actor.recoil,game.time,view=actor.aim_view)
                axis=barrel_axis('player',key,actor.facing)
                error=abs((axis.angle_to(project(game.shots[-1].velocity))+180)%360-180)
                self.assertLess(error,4.5 if distance==120 else 3.1,(distance,degrees,error))

    def test_direction_boundaries_have_hysteresis(self):
        self.assertEqual(direction_angle(24,0),0)
        self.assertEqual(direction_angle(27,0),45)
        self.assertEqual(direction_angle(21,45),45)
        self.assertEqual(direction_angle(18,45),0)
        self.assertEqual(direction_angle(-24,0),0)
        self.assertEqual(direction_angle(-27,0),-45)
        self.assertEqual(aim_pose(V(),-1,-45),(-1,-45))

    def test_vertical_views_do_not_flip_when_crossing_center(self):
        for angle in (-90,90):
            right=animated_sprite('player',.2,True,1,angle,0)
            left=animated_sprite('player',.2,True,-1,angle,0)
            self.assertEqual(pg.image.tobytes(right[0],'RGBA'),pg.image.tobytes(left[0],'RGBA'))
            self.assertEqual(right[1:],left[1:])
        for angle in (-45,0,45):
            right=animated_sprite('player',.2,True,1,angle,0)
            left=animated_sprite('player',.2,True,-1,angle,0)
            self.assertEqual(pg.image.tobytes(pg.transform.flip(right[0],True,False),'RGBA'),pg.image.tobytes(left[0],'RGBA'))
            self.assertAlmostEqual(right[2].x+left[2].x,right[0].get_width())

    def test_stride_depends_on_distance_not_frame_rate(self):
        def travel(frames):
            game=Siege()
            game.cover=[]
            game.relays=[]
            for _ in range(frames):game.move(game.player,V(120/frames,0))
            return game.player.stride
        self.assertAlmostEqual(travel(30),travel(120))
        self.assertAlmostEqual(travel(60),120/132)

    def test_blocked_movement_does_not_animate_or_step(self):
        class Recorder:
            def __init__(self):self.events=[]
            def play(self,*args):self.events.append(args[0])
        recorder=Recorder()
        game=Siege(audio=recorder)
        game.cover=[Actor(V(365,360),'crate',65,29)]
        distance=game.move(game.player,V(8,0))
        self.assertEqual(distance,0)
        self.assertEqual(game.player.stride,0)
        self.assertNotIn('step',recorder.events)

    def test_torso_aim_resolves_tall_boss(self):
        game=Siege()
        game.enemies=[]
        boss=game.spawn(V(550,360),'boss')
        cursor=project(boss.pos)-game.camera+V(0,-180)
        self.assertEqual(cursor_aim(cursor,game),boss.pos)

    def test_cover_cannot_be_bypassed_by_long_barrel(self):
        game=Siege()
        game.enemies=[]
        game.relays=[]
        game.cover=[Actor(V(354,360),'crate',65,20)]
        game.player.facing,game.player.aim_angle=aim_pose(V(300,0))
        game.fire_weapon(game.player,V(700,360),950,24)
        self.assertEqual(game.shots[0].pos,game.player.pos)


if __name__ == '__main__':unittest.main()
