# Standalone seam audit

`seam_audit.py` reimplements `godot/tests/audit_seams.gd` in plain Python so the
sprite registration numbers can be reproduced without installing Godot.

```sh
python3 tools/seam_audit.py          # from the repo root
```

Requires PIL and numpy. It checks the same 17,112 combinations of view, clip,
frame, facing and gait: belt pixels from the leg sprite are offset by the waist
socket and counted against opaque torso pixels. Fewer than 32 overlapping
pixels fails the pose.

```
SEAM PASS: 17112 combinations; all overlaps >=32 pixels at alpha >64
```

## What the check does and does not cover

`seam_drift_test.py` corrupts copies of the atlases and re-runs the audit, which
maps the boundary of what the seam check detects:

```sh
python3 tools/seam_drift_test.py
```

Measured with the historical overlap-only audit:

- character 4% smaller — FAIL, 352 combinations
- character 8% smaller — FAIL, 6728 combinations
- alpha edge eroded 2px — FAIL, 3036 combinations
- torso shifted 3px or 6px down in the cell — PASS

Scale drift is caught at 4% and above, and passes below 3%. Whole-sprite
vertical translation is not caught at any magnitude tested: shifting the torso
down moves the waist socket with it, so the minimum overlap rises from 59 to
249 while the sprite itself gets worse.

The seam audit answers whether two parts still meet. It does not answer whether
the assembled pair sits correctly inside its cell; that needs a separate check
anchored to the cell rather than to the neighbouring sprite.

## Current alignment and complete gallery

`calibrate_leg_sockets.py` measures the pelvis center of each of the 20 leg
frames from its top belt pixels. Runtime placement uses these per-frame sockets,
including the mirrored pixel-center coordinate, instead of assuming x=40 for
every frame. Body and leg origins share a whole-pixel placement to avoid uneven
sampling at the join. The legacy socket-only baseline remains in the tests.

The Godot audit now checks both overlap and independently measured waist-center
error (at most 0.51 source pixels) for every combination. This catches lateral
misregistration that overlap alone would miss.

```sh
python3 tools/calibrate_leg_sockets.py
python3 tools/render_player_combinations.py
```

Both tools require numpy and Pillow. The second renders all 17,112 unique audited
combinations into 119 labelled contact sheets, with `index.html`, `index.json`,
and a sheet of the lowest-overlap poses under `godot/artifacts/player-combinations/`.
The image index identifies the body clip, frame, facing and leg gait of each cell.
This is complete enumeration of supported poses; full artistic judgment of each
pose is still distinct from the numeric registration checks.
