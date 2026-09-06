# Baseline sprite visual audit

Reviewed and migrated source commit `b9828a6` after the earlier `fccbb04` cleanup.
This historical migration audit defines the accepted sprite baseline. The source
commits refer to the predecessor repository; current checks run through `make test`.

## Findings and resolved migration gaps

- **Waist gaps:** the exported pelvis socket alone did not ensure visible overlap.
  Imported the final per-view belt overlap and applied it to the actual lower sprite.
- **Grounding and aiming:** the adjusted contact poses require ground-anchor shifts.
  These are applied in shared geometry, so muzzle/ejection offsets and the aim solver
  move with the displayed body.
- **Idle/fire discontinuity:** the prior port still used full-body art while stationary.
  Idle and fire now use the final upper-body exports and the same authored lower-body
  poses as walking. Stopping chooses the nearest contact frame using Python-compatible
  nearest-even rounding at exact ties.
- **Facades:** the earlier corrected street slope and explicit ground anchors remain
  in the exported mission data.

## Evidence

The Python direction sheets and action-state sheet were reviewed alongside native
Godot captures. `artifacts/actions-godot.png` renders all four action states and all
eight directions through real Sprite2D layers. Opening/boss/effect/victory captures
exercise the layers in the mission.

The native alpha audit checked **17,112** frame/facing/lower-pose combinations.
Minimum belt overlaps match the Python report exactly:

| Source view | Python | Godot |
|---|---:|---:|
| Side | 59 | 59 |
| Rear diagonal | 79 | 79 |
| Rear | 79 | 79 |
| Front | 129 | 129 |
| Front diagonal | 143 | 143 |

The threshold is alpha >64, with at least 32 overlapping pixels required. The native
report is `artifacts/seams-godot.json`. All **2,972** reference/combat/asset checks
pass, including direct checks of the final Sprite2D layer offsets and every action.

## Remaining visual limitations

The authored walk still has four keys and reuses diagonal poses for some strafing
directions. Abrupt contact changes and stylized leg motion remain possible. Aggregate
alpha overlap proves the tested layers intersect; it does not prove perfect outline
continuity or natural movement at every transition. Pixel placement, fonts, and GPU
blending can differ slightly from Pygame. The map floor remains baked.

The reviewed waist gap and action-art mismatch are resolved in this migration.
Further animation refinement belongs in the Godot workflow, using this snapshot as
the baseline rather than introducing another Python gameplay revision.
