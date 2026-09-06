"""Record reference results from the preserved Pygame implementation.

This is an offline oracle, not a second implementation of the Godot algorithms.
"""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src/pyg'))
import siege_motion as motion
from isometric_game import Siege, V, project, segment_entry


def main():
    poses = []
    for kind in ('player', 'grunt', 'rifle', 'runner', 'brute', 'boss'):
        for moving in (False, True):
            for facing in (-1, 1):
                for angle in (-90, -45, 0, 45, 90):
                    stride, recoil, time = .413, .082, 1.23
                    if kind == 'boss':
                        recoil = 0.0
                    key = motion.pose_key(kind, stride, moving, angle, recoil, time)
                    size, anchor, muzzle = motion.coordinates(kind, key, facing)
                    port = motion.ejection_offset(kind, stride, moving, facing, angle, recoil, time)
                    poses.append(dict(kind=kind, moving=moving, facing=facing, angle=angle,
                                      stride=stride, recoil=recoil, time=time, key=key,
                                      size=list(size), anchor=list(anchor), muzzle=list(muzzle), port=list(port)))
    gaits = []
    for body in (-90,-45,0,45,90):
        for facing in (-1,1):
            for move in (-90,-45,0,45,90):
                for move_facing in (-1,1):
                    for phase in (.0,.26,.51,.76):
                        args = [body,facing,move,move_facing,phase]
                        gaits.append({'args':args,'result':list(motion.gait_pose(*args))})
    aims = []
    for facing in (-1,1):
        for moving in (False,True):
            for view in (-90,-45,0,45,90):
                for target in ((180,-75),(12,-30),(380,80)):
                    point = V(target[0]*facing,target[1])
                    result = motion.solve_weapon_aim(.413,moving,facing,view,.082,1.23,point)
                    aims.append(dict(facing=facing,moving=moving,view=view,target=list(point),result=list(result)))
    movement = []
    for delta in ((1,0),(0,1),(-1,0),(0,-1),(1,1),(-1,-1),(50,100),(300,0)):
        game = Siege()
        distance = game.move(game.player,V(delta))
        movement.append(dict(delta=delta,pos=list(game.player.pos),distance=distance,stride=game.player.stride))
    layers = []
    for view in (-90,-45,0,45,90):
        for facing in (-1,1):
            for moving,recoil in ((False,0),(False,.08),(True,0),(True,.08)):
                for stride in (0,.25,.5,.75,1.25,1.75):
                    key=motion.pose_key('player',stride,moving,view,recoil,view=view)
                    gait=motion.gait_pose(view,facing,-view,-facing,key[2]/motion.manifest()[key[0]]['clips'][key[1]]['count']) if moving else (view,facing,(round(stride*2)*2)%4)
                    layers.append(dict(view=view,facing=facing,moving=moving,recoil=recoil,stride=stride,
                                       gait=list(gait),origin=list(motion.lower_origin(key,facing))))
    path = ROOT / 'godot/tests/pygame_reference.json'
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(dict(poses=poses,gaits=gaits,aims=aims,movement=movement,layers=layers),indent=2)+'\n')
    print(f'Wrote {len(poses)+len(gaits)+len(aims)+len(movement)+len(layers)} Pygame reference cases')


if __name__ == '__main__':
    main()
