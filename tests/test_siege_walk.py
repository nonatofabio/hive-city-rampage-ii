import os
from pathlib import Path
import sys
import unittest
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/pyg'))
import pygame as pg
from isometric_game import Siege,V,unproject
from siege_motion import animated_sprite,muzzle_offset,gait_pose,signed_direction,pose_key,waist_socket,upper_manifest,upper_sheet,lower_body,lower_origin


class WalkingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):pg.init();pg.display.set_mode((960,540))
    @classmethod
    def tearDownClass(cls):pg.quit()

    def test_all_eight_by_eight_directions_limit_torso_twist(self):
        directions=[(0,1),(45,1),(90,1),(45,-1),(0,-1),(-45,-1),(-90,1),(-45,1)]
        for body,facing in directions:
            for travel,move_facing in directions:
                for phase in (0,.25,.5,.75):
                    view,side,step=gait_pose(body,facing,travel,move_facing,phase)
                    twist=(signed_direction(view,side)-signed_direction(body,facing)+180)%360-180
                    self.assertLessEqual(abs(twist),45.0001,(body,facing,travel,move_facing))
                    self.assertIn(step,range(4))

    def test_opposite_travel_keeps_body_facing_and_reverses_steps(self):
        for phase in (0,.25,.5,.75):
            # Walking north while firing south must never select north-facing legs.
            view,side,step=gait_pose(90,1,-90,1,phase)
            self.assertEqual(view,90)
            self.assertEqual(step,(-int(phase*4))%4)
            view,side,step=gait_pose(0,1,0,-1,phase)
            self.assertEqual((view,side),(0,1))

    def test_pelvis_attachment_is_animated_and_mirrors_with_torso(self):
        sockets=[]
        for phase in (0,.25,.5,.75):
            key=pose_key('player',phase,True,0,0)
            right=waist_socket(key,1);left=waist_socket(key,-1)
            image,_,_=animated_sprite('player',phase,True,1,0,0)
            self.assertAlmostEqual(right.x+left.x,image.get_width())
            self.assertAlmostEqual(right.y,left.y)
            sockets.append(right.y)
        self.assertGreater(max(sockets)-min(sockets),.5)
        self.assertGreater(sockets[0],sockets[1])  # Screen Y: contact settles below passing.
        self.assertAlmostEqual(sockets[0],sockets[2])

    def test_every_action_uses_the_same_registered_lower_body(self):
        # Contact poses must remain on the ground across stopping and firing.
        for view in (-90,-45,0,45,90):
            for moving,recoil in ((False,0),(False,.08),(True,0),(True,.08)):
                key=pose_key('player',0,moving,view,recoil,view=view)
                self.assertIn(key[1],upper_manifest()[key[0]]['clips'])
                image,anchor,_=animated_sprite('player',0,moving,1,view,recoil,view=view)
                self.assertLess(abs(image.get_bounding_rect(min_alpha=64).bottom-anchor.y),4)
                w,h=upper_manifest()[key[0]]['cell']
                upper=upper_sheet(key[0],key[1]).subsurface((key[2]*w,0,w,h))
                lower=lower_body(view,1,0)
                belt=pg.Surface(lower.get_size(),pg.SRCALPHA);belt.blit(lower,(0,12),(0,12,80,12))
                overlap=pg.mask.from_surface(upper,64).overlap_area(pg.mask.from_surface(belt,64),lower_origin(key,1))
                self.assertGreaterEqual(overlap,32,(view,moving,recoil))

    def test_travel_direction_is_independent_of_aim(self):
        game=Siege();game.cover=[];game.relays=[];a=game.player;a.pos=V(1200,350)
        for movement,expected in [(V(0,-10),-90),(V(10,10),45),(V(-10,0),0)]:
            game.move(a,unproject(movement))
            self.assertEqual(a.move_angle,expected)
            before=(a.move_angle,a.move_facing)
            game.aim_weapon(a,a.pos+unproject(V(300,0)))
            self.assertEqual((a.move_angle,a.move_facing),before)

    def test_blocked_motion_does_not_advance_cycle(self):
        game=Siege();game.cover=[];game.relays=[];a=game.player;a.pos=V(35,85)
        before=a.stride
        self.assertEqual(game.move(a,V(-10,-10)),0)
        self.assertEqual(a.stride,before)

    def test_walk_direction_changes_legs_without_moving_muzzle(self):
        args=('player',.3,True,1,0,.08)
        right,anchor,muzzle=animated_sprite(*args,move_angle=0)
        up,other_anchor,other_muzzle=animated_sprite(*args,move_angle=-90)
        self.assertEqual(anchor,other_anchor);self.assertEqual(muzzle,other_muzzle)
        self.assertEqual(muzzle-anchor,muzzle_offset(*args))
        self.assertNotEqual(pg.image.tobytes(right,'RGBA'),pg.image.tobytes(up,'RGBA'))
        # The head and shoulders must be byte-identical when only travel changes.
        self.assertEqual(pg.image.tobytes(right.subsurface((0,0,right.get_width(),50)),'RGBA'),pg.image.tobytes(up.subsurface((0,0,up.get_width(),50)),'RGBA'))


if __name__=='__main__':unittest.main()
