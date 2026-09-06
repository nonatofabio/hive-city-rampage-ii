"""Headless regression checks for the isometric mission and combat rules."""
import os
from pathlib import Path
import sys
import unittest

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src' / 'pyg'))
import pygame as pg
from isometric_game import Actor, Siege, Shot, V, Renderer, project, unproject, segment_hit


class SiegeTests(unittest.TestCase):
    def game(self):
        game = Siege(17)
        game.enemies.clear()
        game.spawn_timer = 100
        return game

    def test_projection_round_trip(self):
        for point in (V(0,0), V(320,360), V(2399,699), V(-70,110)):
            self.assertLess((unproject(project(point))-point).length(), 1e-8)

    def test_fast_projectile_sweeps_between_frames(self):
        self.assertTrue(segment_hit(V(0,0), V(100,0), V(45,0), 4))
        self.assertFalse(segment_hit(V(0,0), V(100,0), V(45,10), 4))

    def test_cover_blocks_shots_before_enemies(self):
        game = self.game()
        game.cover = [Actor(V(390,360), 'crate', 65, 25)]
        enemy = game.spawn(V(440,360), 'grunt')
        game.shots.append(Shot(V(340,360), V(2000,0), 24))
        game.update(.06)
        self.assertEqual(game.cover[0].hp, 41)
        self.assertEqual(enemy.hp, 45)
        self.assertEqual(len(game.shots), 0)

    def test_larger_hitbox_can_be_hit_before_nearer_center(self):
        game = self.game()
        game.cover = [Actor(V(430,360), 'crate', 65, 15)]
        enemy = game.spawn(V(450,360), 'boss')
        enemy.phase = 1
        enemy.target = V(game.player.pos)
        game.shots.append(Shot(V(350,360), V(2000,0), 24))
        game.update(.06)
        self.assertEqual(game.cover[0].hp, 65)
        self.assertEqual(enemy.hp, 1776)

    def test_cover_blocks_movement_then_opens_when_destroyed(self):
        game = self.game()
        cover = Actor(V(370,360), 'crate', 65, 29)
        game.cover = [cover]
        game.move(game.player, V(20,0))
        self.assertEqual(game.player.pos.x, 320)
        game.hit(cover, 100)
        game.move(game.player, V(20,0))
        self.assertEqual(game.player.pos.x, 340)

    def test_grenade_limits_and_delayed_detonation(self):
        game = self.game()
        enemy = game.spawn(V(800,360), 'brute')
        game.grenade(enemy.pos)
        game.grenade(enemy.pos)
        self.assertEqual(game.grenades, 4)
        self.assertEqual(len(game.grenade_flights), 1)
        self.assertEqual(enemy.hp, 125)
        for _ in range(40):
            game.update(1/60)
        self.assertLess(enemy.hp, 125)
        self.assertFalse(game.grenade_flights)

    def test_barrel_chain_reaction_is_finite(self):
        game = self.game()
        game.cover = [Actor(V(800,350), 'barrel',28), Actor(V(840,350), 'barrel',28)]
        game.hit(game.cover[0], 30)
        self.assertTrue(all(c.hp <= 0 for c in game.cover))

    def test_boss_unlock_death_and_extraction(self):
        game = self.game()
        for relay in game.relays:
            game.hit(relay, 200)
        game.update(1/60)
        bosses = [e for e in game.enemies if e.kind == 'boss']
        self.assertEqual(len(bosses), 1)
        game.update(1/60)
        self.assertEqual(len([e for e in game.enemies if e.kind == 'boss']), 1)
        game.hit(bosses[0], 2000)
        self.assertTrue(game.boss_defeated)
        game.player.pos = V(2280,510)
        game.update(1/60)
        self.assertEqual(game.state, 'won')

    def test_boss_attack_locks_target_and_can_be_dodged(self):
        game = self.game()
        boss = game.spawn(V(550,360), 'boss')
        boss.cooldown = 0
        game.update(1/60)
        locked = V(boss.target)
        self.assertGreater(boss.phase, 0)
        game.player.pos += V(0,200)
        for _ in range(80):
            game.update(1/60)
        self.assertEqual(boss.target, locked)
        self.assertEqual(game.player.hp, 100)
        self.assertEqual(game.shield, 60)

    def test_death_freezes_simulation_and_shield_absorbs_first(self):
        game = self.game()
        game.damage_player(70)
        self.assertEqual(game.shield, 0)
        self.assertEqual(game.player.hp, 90)
        game.hurt_timer = 0
        game.damage_player(100)
        self.assertEqual(game.state, 'dead')
        game.update(1)
        self.assertEqual(game.time, 0)

    def test_screen_relative_movement_and_dash(self):
        game = self.game()
        old = V(game.player.pos)
        game.update(.016, V(1,0), dash=True)
        delta = project(game.player.pos-old)
        self.assertGreater(delta.x, 0)
        self.assertAlmostEqual(delta.y, 0)
        self.assertGreater(game.dash_cd, 0)
        game.damage_player(50)
        self.assertEqual(game.shield, 60)

    def test_render_all_mission_states_and_assets(self):
        pg.init()
        pg.display.set_mode((960,540))
        try:
            game = self.game()
            renderer = Renderer()
            for kind in ('grunt','rifle','runner','brute','boss'):
                game.spawn(V(450,350),kind)
            for state in ('playing','won','dead'):
                game.state = state
                self.assertEqual(renderer.draw(game).get_size(), (960,540))
            renderer.draw(game, paused=True)
            from isometric_art import atlas_sprite
            for kind in ('player','grunt','rifle','runner','brute','boss','facade','crate','barrel','relay'):
                sprite = atlas_sprite(kind)
                self.assertIsNotNone(sprite)
                count = pg.mask.from_surface(sprite).count()
                self.assertGreater(count, sprite.get_width()*sprite.get_height()*.15)
                self.assertLess(count, sprite.get_width()*sprite.get_height()*.95)
        finally:
            pg.quit()


if __name__ == '__main__':
    unittest.main()
