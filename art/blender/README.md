# Original sprite rigs

The artwork uses a cleaned version of the original sprite atlas: flatter material colors and dark contours replace surface noise and pale matte fringes. The accepted walk rig is preserved.

`ashgate_sprite_rigs.blend` contains an editable armature and one connected UV mesh per character. Skin weights blend across hips, knees, feet, torso, arms, and weapon. This is genuine Blender skeletal deformation of the original 2D artwork, not a collection of detached image fragments. Textures are packed into the Blender file.

Open the file in Blender, select a character's collection and armature, and choose its named action in the Action Editor. Walk cycles have a repeated first key at the cycle boundary. The source meshes remain planar: this preserves the drawing and does not invent rear views that the source art does not contain.

Rebuild from the cleaned character atlas (with original art as a fallback):

```sh
.venv/bin/python tools/blender/prepare_sprite_textures.py
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python tools/blender/rig_sprites.py -- --render
.venv/bin/python tools/blender/pack_sprites.py
```

`--preview` exports only the player's animation to `art/blender/preview/`. Production poses go to `src/pyg/assets/rendered/`. The game reads complete pose sheets and exported muzzle coordinates; Blender is not a runtime dependency.

The armature's weapon bone applies a short recoil translation and pitch. Weighted vertices near the shoulder transition into the torso instead of opening a seam. Walking uses small alternating leg advances, foot clearance, knee flexion, and torso counter-motion. The deliberately limited deformation protects the original armor shapes.

## Directional player views

`ashgate_direction_rigs.blend` contains four additional continuous meshes and armatures for up, diagonal up, diagonal down, and down. The accepted side pose stays in the original rig file. Each view has its own joint landmarks, ground anchor, and muzzle in `directions.json`, and exports idle, walk, fire, and walk/fire clips. The front and rear views are kept stable when the cursor crosses the vertical axis; the three other views mirror left/right.

```sh
.venv/bin/python tools/blender/prepare_direction_textures.py
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python tools/blender/rig_sprites.py -- --directions --render
.venv/bin/python tools/blender/pack_sprites.py
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python tools/blender/validate_sprite_rigs.py -- --directions
.venv/bin/python tools/capture_ashgate_directions.py
```

The player chooses the nearest of five angles (-90, -45, 0, 45, 90 degrees from screen-right), with four degrees of hysteresis at boundaries. Walking phase continues across view changes. These five sources produce eight visible compass directions. Enemy art continues to use its existing side views and elevation variants.

## Fine weapon aim and heavier marine stride

`ashgate_aim_rigs.blend` contains the five player rigs with gun poses sampled every five degrees within each view. A second exported point behind the muzzle defines the drawn barrel axis. The runtime searches the pose geometry for the closest muzzle-to-cursor alignment while shots continue to hit the continuous mouse target. Mirroring transforms both sockets. Nearby targets can select an adjacent body view when needed.

The marine walk now uses 3.8px foot travel, 3.4px clearance, increased knee lift, and 1.4px torso settling. Enemy stride amplitude is unchanged.

Run this after rebuilding the base and directional rigs, before packing:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python tools/blender/rig_sprites.py -- --aiming --render
.venv/bin/python tools/blender/pack_sprites.py
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python tools/blender/validate_sprite_rigs.py -- --aiming
.venv/bin/python tools/capture_ashgate_weapons.py
```

`--models player_n,player_s` limits rendering during an iteration while saving all five editable rigs. Packed aiming sheets end in `_poses.png` so they remain distinct from ignored numbered frame intermediates.

## Rigid weapons, wrist attachment, and knee flex

`weapon_rig.json` records each view's rigid weapon outline, elbow/wrist points, and ejection port. Vertices inside the weapon outline use 100% weapon-bone weight, including the receiver and magazine. Blending happens outside that outline and across the arm. The weapon pivots at the wrist; the forearm follows, and the weapon inherits no arm scale. Validation measures distances across the evaluated gun mesh through aiming to catch deformation that normalized weights alone cannot detect.

The latest player rig replaces soft leg skinning with rigid thigh, shin, and boot regions. Forward kinematics rotates the hip by up to 15 degrees and the knee by up to 43 degrees during the return, preserving segment lengths. Boots counter-rotate at the ankle. The rotation axis follows the source view; body settling is 2.2px. Only the hip connector blends into the torso. Validation measures panel vertex distances through the animation, in addition to knee articulation.

Exports also contain the animated ejection-port position. Use `--python-exit-code 1` before `--python` in automated Blender commands so script errors fail the build rather than returning success.


## Player walking now uses authored lower-body poses

The rigid-leg experiment is retained in history, but moving players now use drawn lower-body frames. `--aiming --upper-body --render` saves `ashgate_upper_rigs.blend` and renders torso-only sheets beneath `assets/rendered/upper`; `pack_sprites.py --upper-body` packs these separately. Offline face removal retains the complete hanging weapon. The runtime combines those aiming torsos with the authored walk atlas imported by `tools/prepare_ashgate_walk.py`. No additional leg deformation is applied to the drawn frames.


Upper-layer silhouette extraction now uses the per-view `torso_hem` and optional `upper_weapon` polygons in `weapon_rig.json`. These are visibility boundaries, separate from animation weights. The waist hem retains the central pelvis connection while removing the original thigh plates.

The upper-body render now includes idle and stationary fire, so all player action states share the same layered artwork. The per-view runtime belt-overlap and ground calibration are reviewed in `static/sprite-audit`.
