# Godot game

Open `project.godot` in Godot 4.3 or use `make run` from the repository root.
The game runs entirely in Godot; it loads only assets within this project.
See [Make commands and build setup](../BUILDING.md).

## Structure

- `scenes/main.tscn`: world layers, Y-sorted actors, HUD, touch controls, and title menu.
- `scenes/actor.tscn`: reusable layered character with shadow, legs, torso, and muzzle.
- `scenes/effect.tscn`: fire, explosion, and death animation.
- `scripts/siege.gd`: fixed-step mission, input, camera, and audio.
- `scripts/title_screen.gd`: deployment, field orders, and audio buttons.
- `scripts/pose_library.gd`: pose metadata, ground anchors, aim solver, and gait.
- `scripts/iso.gd`: projection and swept collision.
- `scripts/hud.gd`, `touch_controls.gd`: desktop and mobile interface.
- `assets/data/mission.json`: mission placements.
- `assets/data/player_registration.json`: shared torso/leg calibration.

Combat uses flat world coordinates, projected into an isometric view. Sorting uses
ground contact. Characters are pre-rendered sprites with separate aiming torsos and
authored lower-body poses. The logical viewport is 960 × 540; Android is landscape.

## Validation

`make test` checks title deployment via mouse and touch, field orders, audio,
pause/restart, 2,972 reference/combat/asset assertions, 17,112 silhouette combinations,
multitouch controls, and a 600-frame combat simulation.

`tests/baseline_reference.json` preserves 828 geometry and pose cases from the final
art handoff (`b9828a6` in the original project). It is static test data and requires
no legacy engine. Update fixtures deliberately when changing the accepted art contract.

`make capture` renders title, opening, pause, boss, effects, victory, and an action
contact sheet into ignored `artifacts/`. See [visual audit](FINAL_VISUAL_REVIEW.md)
for the baseline overlap measurements and remaining animation limitations.

## Assets

Runtime sheets, metadata, sound, and baked scenery live in `assets/`. Editable
Blender projects and audio source clips are under `../art/`; the original generation
pipeline is maintained in the predecessor repository, not required here.
Asset licenses and historical provenance accompany the files. Export presets
exclude tests and captures and include runtime JSON and font/audio notices.
