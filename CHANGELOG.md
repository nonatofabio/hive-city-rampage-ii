# Changelog

## Post-Alpha 1 — complete player sprite continuity audit

- Corrected the visible waist gap with per-view belt overlap and recalibrated ground anchors.
- Unified idle, firing, walking, and walking-fire around the same torso/lower-body artwork; stopping settles onto the nearest contact pose.
- Added enlarged direction/phase review sheets, action-state comparisons, and an exhaustive alpha-overlap audit covering 17,112 combinations.
- Updated the gameplay preview to demonstrate repeated walking, stopping, and firing.

## Post-Alpha 1 — clean torso hem and wall alignment

- Removed old thigh remnants from aiming torsos with explicit per-view waist boundaries and separate weapon visibility masks.
- Reprojected painted facade rows to the street's 2:1 slope and anchored wall bases at the pavement edge.

## Post-Alpha 1 — torso and gait synchronization

- Constrained pelvis facing to within 45 degrees of the torso and reversed the walking sequence when retreating.
- Attached the drawn belt to an exported animated pelvis socket, replacing the fixed screen offset.
- Synchronized torso settling with contact/passing poses and sourced combat sockets from the exact torso animation.
- Added exhaustive direction-pair tests and a 64-case visual review grid.

## Post-Alpha 1 — authored lower-body walking

- Replaced the player's procedural leg animation during walking with drawn contact and passing poses.
- Legs follow actual travel direction independently of the mouse-aimed torso; collision-blocked movement does not advance the walk.
- Slower, distance-driven cadence and belt registration preserve the bulky silhouette.
- Retained barrel, muzzle, and ejection geometry; added independent-movement regression tests and a gameplay walk preview.

## Post-Alpha 1 — wrist rig, knee flex, brass casings, and servo HUD

- Rigid weapon weights and wrist/forearm articulation keep the whole gun intact while aiming.
- Rigid thigh, shin, and boot sections rotate at the hip, knee, and ankle without soft armor bending.
- Larger brass casings eject from an animated receiver socket, tumble, bounce, and settle.
- Background-free vitals, a smaller translucent auspex, and a servo-skull with brief devotional sayings.
- Added gun-rigidity/knee validation, casing/HUD regression checks, previews, and reusable design notes.

## Post-Alpha 1 — aligned weapons, sprite bolts, and heavier steps

- Finer player weapon poses selected from barrel-axis geometry and the actual muzzle-to-cursor line.
- Authored projectile sprites and muzzle flashes replace line tracers and polygon bursts.
- Stronger marine foot travel, knee lift, and torso settling.
- Per-pixel final fades preserve cached artwork; removed persistent corpse marks and softened scorch edges.
- Added alignment/fade regression coverage and recorded the findings in the design playbook.

## Post-Alpha 1 — effects, deaths, and scene lighting

- Authored eight-frame fire loops and expanding explosions that cool into smoke.
- Hit, buckle, fall, and settled death poses for infantry and the siege walker, with facing-aware corpses and bounded visual lifetimes.
- Cleaned scenery surfaces, grounded prop shadows, baked window/fire lighting, and brief local blast illumination.
- Reproducible effects and scenery previews, lifecycle regression tests, and a reusable art/motion playbook with observed feedback and known limits.

## Post-Alpha 1 — directional player aiming

- Added front, rear, and diagonal player artwork, retaining the cleaned side view.
- Rendered four new Blender rigs with walking and recoil for eight compass directions through mirroring.
- Mouse-driven view selection preserves walk phase and avoids flickering at angular boundaries.
- Per-view muzzle sockets align shots and flashes; added directional regression checks and a mouse-orbit preview.

## Post-Alpha 1 — sprite cleanup and Blender animation

- Retained only the approved bolter gunfire; removed music and other effects.
- Replaced runtime cut-and-rotate animation with complete poses rendered from continuous 2D meshes and blended Blender armatures.
- Cleaned character textures with flatter color areas and dark contours, removing pale matte fringes while preserving the accepted walk cycle.
- Added editable Blender sources, pose export tools, and a skin-weight/topology validation report.

## Post-Alpha 1 — sound and motion polish

- Layered bolter variants, impact and armor sounds, spatial footsteps, explosions, and combat cues using documented CC0 sources.
- Dedicated voice pools, stereo positioning, distance falloff, music ducking, pause/mute, and separate mix controls.
- Optional streamed dark ambient loop; music starts off following playtest feedback, effects remain enabled.
- Distance-driven articulated walking, independently aimed/recoiling guns, visible shell ejection, matching muzzle/projectile geometry, and siege-walker windup.
- Torso targeting for tall enemies, blocked-movement footstep prevention, and close-cover muzzle protection.
- Reproducible audio mixes and motion preview; 22 regression tests.

## 0.2.0-alpha.1 — Ashgate Alpha 1

First playable isometric Ashgate Siege checkpoint. Preserves the original top-down mode with `--classic`.

- Gothic street art, depth-sorted soldiers and scenery, combat effects, and tactical HUD.
- Destructible cover, explosive barrels, grenades, dash, pickups, and kill chains.
- Three signal relays, Cathedral-Breaker boss, extraction, victory, and restart.
- Initial synthesized sound effects; placeholder stepping motion.
- Twelve regression tests and deterministic headless gameplay capture.

The tag records the playable baseline before the sound-design and motion polish pass.
