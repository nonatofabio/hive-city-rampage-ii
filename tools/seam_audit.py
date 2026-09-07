"""Standalone Python replication of hive-city-rampage-ii's audit_seams.gd.

Reimplements the 17,112-combination torso/leg seam check without Godot, so we
can (a) confirm the published number and (b) inject sprite drift and watch it fail.
"""
import json, math, sys
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent) / "godot"
VIEWS = {-90: "player_n", -45: "player_ne", 0: "player", 45: "player_se", 90: "player_s"}
ALPHA = 64  # matches BitMap threshold 64/255

reg = json.loads((ROOT / "assets/data/player_registration.json").read_text())
models = json.loads((ROOT / "assets/rendered/sprites.json").read_text())["models"]
upper = json.loads((ROOT / "assets/rendered/upper/sprites.json").read_text())["models"]
for m in models:
    for c in models[m]["clips"].values():
        c["path"] = "assets/rendered/" + c["sheet"]
for m in upper:
    for c in upper[m]["clips"].values():
        c["path"] = "assets/rendered/upper/" + c["sheet"]
    models[m]["clips"].update(upper[m]["clips"])

_imgcache = {}
def img(rel):
    if rel not in _imgcache:
        _imgcache[rel] = np.array(Image.open(ROOT / rel).convert("RGBA"))
    return _imgcache[rel]

def round_even(v):
    lo = math.floor(v); frac = v - lo
    if frac == 0.5:
        return lo if lo % 2 == 0 else lo + 1
    return math.floor(v + 0.5) if frac > 0.5 else lo

def direction_angle(angle, previous=999):
    if previous in VIEWS and abs(angle - previous) <= 26.5:
        return previous
    best, bestd = 0, 1e9
    for view in VIEWS:
        d = abs(angle - view)
        if d < bestd:
            bestd, best = d, view
    return best

def wrapf(v, lo, hi):
    return lo + math.fmod(math.fmod(v - lo, hi - lo) + (hi - lo), hi - lo)

def gait_pose(body_view, facing, move_view, move_facing, phase):
    body = float(body_view) if facing >= 0 else wrapf(180.0 - body_view, -180.0, 180.0)
    travel = float(move_view) if move_facing >= 0 else wrapf(180.0 - move_view, -180.0, 180.0)
    delta = wrapf(travel - body, -180.0, 180.0)
    backward = abs(delta) > 90.0
    if backward:
        delta = math.fmod(delta + 360.0, 360.0)
        if delta < 0: delta += 360.0
        delta -= 180.0
    pelvis = math.radians(body + max(-45.0, min(45.0, delta)))
    leg_facing = 1 if math.cos(pelvis) >= -0.000001 else -1
    leg_view = direction_angle(math.degrees(math.atan2(math.sin(pelvis), abs(math.cos(pelvis)))))
    step = int(phase * 4.0) % 4
    z = (-step) % 4 if backward else step
    return (leg_view, leg_facing, z)

def geometry_waist(model, clip, index, facing):
    data = models[model]
    cell = np.array(data["cell"], dtype=float)
    size = np.round(cell)            # player factor == 1
    flipped = facing < 0 and model not in ("player_n", "player_s")
    c = data["clips"][clip]
    if "waists" not in c:
        return None
    pt = np.array(c["waists"][index], dtype=float)   # scale == 1
    if flipped:
        pt[0] = size[0] - pt[0]
    return pt

def lower_origin(model, clip, index, facing, gait=None):
    w = geometry_waist(model, clip, index, facing)
    if w is None:
        return None
    leg = [40,12]
    if gait is not None:
        vertical=abs(gait[0])==90
        frame=gait[2]%2 if vertical else gait[2]
        leg=list(reg['leg_waists'][str(gait[0])][frame])
        if (gait[2]>=2 if vertical else gait[1]<0): leg[0]=80-leg[0]
    return np.array([round_even(w[0]-leg[0]),
                     round_even(w[1]) - leg[1] - int(reg["belt_overlap"][model])],dtype=int)

_belts = {}
def belt_points(gait):
    if gait in _belts:
        return _belts[gait]
    vertical = abs(gait[0]) == 90
    step = gait[2] % 2 if vertical else gait[2]
    flip = gait[2] >= 2 if vertical else gait[1] < 0
    src = img("assets/rendered/walk/%d.png" % gait[0])
    pts = []
    for y in range(12, 24):
        for x in range(80):
            sx = step * 80 + (79 - x if flip else x)
            if src[y, sx, 3] > ALPHA:
                pts.append((x, y))
    _belts[gait] = np.array(pts, dtype=int) if pts else np.zeros((0, 2), int)
    return _belts[gait]

def run():
    total = 0; failures = 0; report = {}
    for view, model in VIEWS.items():
        data = models[model]
        minimum = 100000; worst = None
        cw, ch = int(data["cell"][0]), int(data["cell"][1])
        for clip_name, clip in data["clips"].items():
            if "/upper/" not in clip["path"]:
                continue
            sheet = img(clip["path"])
            for index in range(int(clip["count"])):
                for facing in (1, -1):
                    up = sheet[0:ch, index*cw:(index+1)*cw]
                    if facing < 0 and abs(view) != 90:
                        up = up[:, ::-1]
                    mask = up[:, :, 3] > ALPHA
                    origin = lower_origin(model, clip_name, index, facing)
                    if origin is None:
                        continue
                    gaits = {}
                    if clip_name.startswith("walk"):
                        for travel in VIEWS:
                            for side in (1, -1):
                                gaits[gait_pose(view, facing, travel, side,
                                                index / float(clip["count"]))] = True
                    else:
                        gaits[(view, facing, 0)] = True
                        gaits[(view, facing, 2)] = True
                    for gait in gaits:
                        origin = lower_origin(model,clip_name,index,facing,gait)
                        bp = belt_points(gait)
                        if len(bp):
                            p = bp + origin
                            ok = ((p[:,0] >= 0) & (p[:,0] < mask.shape[1]) &
                                  (p[:,1] >= 0) & (p[:,1] < mask.shape[0]))
                            q = p[ok]
                            overlap = int(mask[q[:,1], q[:,0]].sum()) if len(q) else 0
                        else:
                            overlap = 0
                        if overlap < minimum:
                            minimum = overlap
                            worst = [clip_name, index, facing, *gait]
                        if overlap < 32:
                            failures += 1
                        total += 1
        report[model] = {"minimum_belt_overlap_pixels": minimum, "worst_case": worst}
        print("SEAM %s minimum=%d" % (model, minimum))
    print()
    print("checked_combinations =", total)
    print("failures (<32px overlap) =", failures)
    if failures > 0 or total != 17112:
        print("SEAM FAIL: %d inadequate overlaps, %d combinations" % (failures, total))
        return 1
    print("SEAM PASS: %d combinations; all overlaps >=32 pixels at alpha >64" % total)
    return 0

if __name__ == "__main__":
    sys.exit(run())
