"""Bake the existing Pygame art once; the Godot game has no Python dependency.

Run with a Python environment containing pygame. Source files are never changed.
Only runtime sheets referenced by the manifests are copied, not render intermediates.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'src/pyg/assets'
DEST = ROOT / 'godot/assets'
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, str(ROOT / 'src/pyg'))
import pygame as pg
from isometric_game import Renderer, Siege
from isometric_art import facade, facade_anchor, prop
from siege_effects import shadow_stamp, light_stamp
from siege_motion import BELT_OVERLAP, GROUND_SHIFT


def main():
    pg.init()
    pg.display.set_mode((1, 1))
    for sub in ('rendered/upper', 'rendered/walk', 'effects', 'baked', 'audio', 'data'):
        (DEST / sub).mkdir(parents=True, exist_ok=True)
    for sub in ('rendered', 'rendered/upper'):
        data = json.loads((SOURCE / sub / 'sprites.json').read_text())
        shutil.copy2(SOURCE / sub / 'sprites.json', DEST / sub / 'sprites.json')
        for model in data['models'].values():
            for clip in model['clips'].values():
                shutil.copy2(SOURCE / sub / clip['sheet'], DEST / sub / clip['sheet'])
    for sub, pattern in [('rendered/walk', '*.png'), ('effects', '*.png'), ('audio', '*.wav')]:
        for path in (SOURCE / sub).glob(pattern):
            shutil.copy2(path, DEST / sub / path.name)
    shutil.copy2(SOURCE / 'audio/CREDITS.md', DEST / 'audio/CREDITS.md')
    shutil.copy2(SOURCE / 'ASHGATE_ART.md', DEST / 'ART_PROVENANCE.md')
    pg.image.save(Renderer().floor, DEST / 'baked/floor.png')
    for i in range(4):
        pg.image.save(facade(i), DEST / f'baked/facade_{i}.png')
    for kind in ('crate', 'barrel', 'relay'):
        pg.image.save(prop(kind), DEST / f'baked/{kind}.png')
    for name, w, h in [('actor', 50, 16), ('boss', 110, 26), ('prop', 86, 28), ('mark', 54, 20)]:
        pg.image.save(shadow_stamp(w, h), DEST / f'baked/shadow_{name}.png')
    pg.image.save(light_stamp(160, (130, 65, 16), .55), DEST / 'baked/blast_light.png')
    game = Siege()
    def actor(a):
        return {'position': list(a.pos), 'kind': a.kind, 'hp': a.hp, 'radius': a.radius}
    mission = {'player': actor(game.player), 'cover': list(map(actor, game.cover)),
               'relays': list(map(actor, game.relays)), 'enemies': list(map(actor, game.enemies)),
               'fires': [list(p) for p in game.fires], 'extraction': [2280, 510],
               'world_size': [2400, 700],
               'facades': [{'position': [i * 220, 0], 'variant': i % 4,
                            'anchor': list(facade_anchor())} for i in range(12)]}
    (DEST / 'data/mission.json').write_text(json.dumps(mission, indent=2) + '\n')
    (DEST / 'data/player_registration.json').write_text(json.dumps(
        {'belt_overlap': BELT_OVERLAP, 'ground_shift': GROUND_SHIFT}, indent=2) + '\n')
    # A content inventory makes this an explicit, reproducible snapshot.
    inventory = {str(p.relative_to(DEST)): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in sorted(DEST.rglob('*')) if p.is_file()
                 and p.name != 'inventory.json' and not p.name.endswith('.import')}
    (DEST / 'inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')
    print(f'Exported {len(inventory)} runtime assets to {DEST}')
    pg.quit()


if __name__ == '__main__':
    main()
