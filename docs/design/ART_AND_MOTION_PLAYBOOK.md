# Game art and motion playbook

A working record from Ashgate Siege, intended for reuse in later game design. Update this file when a playtest establishes a preference or an implementation reveals a useful constraint. Separate observed feedback from assumptions; approval of one preview does not approve every asset in that style.

## Established direction

The target is a readable, chunky, illustrated isometric shooter: cobalt/gold hero, rust and bone enemies, dark gothic masonry, and warm firelight. The player preferred the original sprites to the geometric low-poly Blender reconstruction. They approved the continuous-mesh sprite walk preview, then asked for flatter colors and removal of pale outline pixels. They subsequently liked the directional aiming preview. These are the strongest style references for new work.

Use broad color clusters with a small number of deliberate shades per material. Preserve a dark silhouette and characteristic armor, weapon, and head shapes. Inspect at the actual 960×540 gameplay resolution before judging a magnified atlas. Tiny scratches and isolated highlights can become moving noise after downsampling.

## Asset generation and importing

1. Supply the accepted sprite as the identity/style reference. Specify camera, pose, palette, physical scale, padding, and the exact changes needed.
2. Save the result as a new source asset. Record the prompt, input reference, actual dimensions, import rules, and consuming files in `src/pyg/assets/ASHGATE_ART.md`.
3. Inspect the returned file. Requested dimensions and grids are not guarantees: the directional and effect sheets arrived at 1254×1254, and the death sheet needed explicitly measured row and column boundaries to preserve the boss's spires, prone boots, and long barrels.
4. Preserve real alpha when provided. A displayed checkerboard can be painted pixels rather than transparency. When a color key is necessary, reserve pure magenta and remove blended magenta edge pixels too. Avoid light matte extraction around pale armor.
5. Use the largest connected component for a single character silhouette. Preserve disconnected components for smoke, sparks, detached weapons, and effect wisps.
6. Register a fixed ground anchor and consistent physical scale across a sequence. Independently resizing every frame's bounding box causes a breathing or bouncing effect. Grounded flame bases should stay still while the plume evolves.

Original images remain in `src/pyg/assets/`; imported textures and runtime sheets are reproducible artifacts. Development tooling can require Blender or ffmpeg; playing the game does not.

## Animation choices

The accepted walk uses one connected UV mesh per sprite, Blender armatures, normalized blended skin weights, and small joint movements that protect armor shapes. Runtime detached-limb rotations exposed seams and received negative feedback. Save the editable `.blend`, packed textures, landmarks, and animation actions alongside export tools.

Use skeletal deformation for modest movement within an existing view. Author new images for changes in visible surfaces or major silhouette changes. Directional turns reveal backs, fronts, and foreshortened guns. Death poses bend bodies into silhouettes a standing drawing cannot convincingly supply by rotation or flattening.

The player currently has five source views: up, diagonal up, side, diagonal down, down. Mirroring produces eight compass directions. Front/rear views remain unmirrored as the cursor crosses the vertical axis, avoiding a sudden weapon-side swap. A four-degree margin around selection boundaries prevents direction chatter. Keep stride phase and recoil timing continuous across view changes.

Store a muzzle socket for every rendered pose. Projectiles, muzzle flashes, and the visible barrel must agree. Validate close-cover behavior so a long gun cannot shoot through cover. The continuous aiming vector remains responsible for shot direction; the sprite is an approximate directional view.

## Fire, explosions, and deaths

Fire needs an anchored base, asymmetric curling flame masses, hot cores, darker edges, smoke, and a loop that does not visibly restart. Offset different fires' animation phases. Repeated triangular flames looked too geometric in the scene.

An explosion has distinct ignition, expansion, cooling, and smoke stages. Keep the initial light flash brief; let smoke outlive the hot core. Limit particles to useful sparks and debris so they support the main drawn effect. These effects are currently visual only; the approved gunfire remains the only sound.

Death needs readable impact, buckling, falling, and a settled pose. The current authored four-pose sheets cover cultist, heavy infantry, and siege walker; runners and brutes share the appropriate scaled set. This is a first authored collapse pass, not a full directional death library. Corpse facing is captured at the lethal hit. Health, scoring, pickups, and collision resolve immediately; the visual presentation continues independently. Hold the final pose, then fade it. Bound both corpse and explosion collections and freeze their clocks when gameplay is paused or terminal.

Depth-sort active collapses and explosions by ground contact. Draw settled bodies beneath standing actors. Never let an effect overwrite HUD readability.

## Scenery and lighting

Apply the same edge and texture cleanup to props as to characters. Keep high-frequency pavement detail lower in contrast than the combatants. Contact shadows give crates and barrels weight; continuous wall shade connects facades to the ground.

Bake stable window and fire light into the map surface once. Use broad, restrained warm pools against cooler ambient stone. A temporary explosion can add local ground light and a short character tint. Bake lighting according to the authored scene; if props or emitters become movable, their lighting must become dynamic or be invalidated.

The current implementation is 2D light painting, without physical light occlusion or a normal-map system. Avoid implying full 3D lighting. Review the whole scene: a good isolated flame can still be too bright or too large in play.

## Review and evidence

For each pass, produce a short preview with complete animation cycles and a gameplay capture at native resolution. Use the same scene for lighting comparisons. Test behavioral contracts: muzzle alignment, angle boundaries, one death per kill, pause/terminal freezing, bounded lifetimes, and preserved gameplay progression. Check visual timing manually; test success cannot establish that an animation looks good.

Preserve milestone tags. Commit review artifacts, editable sources, runtime assets, and the code that consumes them together. Keep unrelated local artwork out of these checkpoints.

## Rebuild and review commands

```sh
.venv/bin/python tools/blender/prepare_sprite_textures.py
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python-exit-code 1 --python tools/blender/rig_sprites.py -- --render
.venv/bin/python tools/blender/prepare_direction_textures.py
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python-exit-code 1 --python tools/blender/rig_sprites.py -- --directions --render
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python-exit-code 1 --python tools/blender/rig_sprites.py -- --aiming --render
.venv/bin/python tools/blender/pack_sprites.py
.venv/bin/python tools/prepare_ashgate_effects.py
.venv/bin/python tools/capture_ashgate_directions.py
.venv/bin/python tools/capture_ashgate_effects.py
.venv/bin/python -m unittest discover -s tests -v
```

## Review log

- 2026-09-05: User approved the sprite walk direction and requested flatter colors and clean contours. Preserved the accepted rig during texture cleanup.
- 2026-09-05: User liked the added directional player views and requested effects, lighting, scenery, death animation, and this reusable learning record.
- 2026-09-05: Added authored fire/explosion/death sheets, cleaner scenery, cached map lighting, and local blast light. This pass awaits the user's visual review; its style and timing should not yet be treated as a new approved baseline.

### Follow-up: barrel alignment, fades, and weight

A correct muzzle origin alone does not align a gun with its bullets. Coarse body views and free mouse aiming leave visible angular errors. Export a second point along the barrel and fit weapon poses to the actual muzzle-to-target line. Solving from the ground center misses parallax; repeatedly rounding an angle can oscillate as the muzzle moves. Searching a small set of exported poses is deterministic and preserves continuous shot targeting. The current player poses use a five-degree grid; very close targets magnify the remaining angular discretization.

Keep projectile artwork compact and oriented along actual velocity. Align muzzle-flash origins with the barrel rather than centering the image there. The generated flash sheet included a barrel stub; the importer explicitly excludes it.

When a user reports black ending frames, test compositing over a light background through opacity zero. The initial headless test did not reproduce an opaque source frame. The revised fade multiplies per-pixel alpha while preserving RGB and cached frames; persistent corpse marks were removed and scorch edges softened. This addresses the ending path without claiming an unverified platform-specific alpha defect.

For heavier steps, start with modest increases in foot travel and clearance, then synchronize knee lift and body settling at contact. Larger motion alone can feel floaty. This pass increased marine foot travel from 2.5px to 3.8px and clearance to 3.4px while preserving the established cycle.

- Follow-up feedback: user liked the overall effects pass, reported bullet-angle mismatch and black ending flashes, and requested a slightly heavier marine step. The weapon/fade/heavy-stride revision awaits visual review.

### Follow-up: rigid materials, joint motion, and unobtrusive HUDs

The user accepted the aiming movement but noticed the gun bending. Soft skinning must follow material boundaries: make the whole weapon rigid, including the receiver, and put the articulation at the wrist. A broad capsule over the barrel was insufficient. Store per-view rigid outlines and arm landmarks, then validate distances between evaluated gun vertices through animation. Normalized weights and a connected mesh prove topology, not visual rigidity.

Increasing small offsets still looked like a wiggle. A subsequent IK pass with blended leg weights distorted the armor and was explicitly rejected. Fixed bone lengths alone do not preserve the sprite surface. Assign each thigh, shin, and boot panel to one bone and animate rotations at the joints. Counter-rotate the boot at the ankle. Validate distances within each panel as well as the knee angle, then review motion in every source view. Narrow connector geometry is still needed between rigid regions; keep it at the joints rather than across armor faces.

Particles need anchors too. Larger themed shell casings now originate at an exported receiver port, rotate through several views, bounce once, settle, and fade. Enlarging a line at the actor center would not fix their placement or material character.

The user requested an open health HUD and translucent map. Remove the enclosing background rather than merely making the panel a little smaller. Thin bar tracks and one-pixel text shadows preserve contrast without covering the scene. The new 132×88 auspex uses a translucent backdrop with stronger markers. A 40×56 servo-skull replaces the placeholder icon and periodically shows short, original Latin-styled devotional sayings, with quiet intervals.

Tooling lesson: Blender can return exit code zero after a Python exception. Pass `--python-exit-code 1` and validate the saved rig before accepting exports. The rigid-weapon pass exposed a legacy capsule configuration assumption; the corrected pipeline now reports such failures explicitly.

- Follow-up feedback: user requested rigid gun motion through the wrist, stronger knee flex, larger thematic casings, an unobtrusive HUD, and a servo-skull with brief High Gothic sayings. This revision awaits visual review.


## Authored lower-body walks after the shuffle rejection

The rigid-knee pass passed geometry validation but the user still saw a side shuffle in play. A rigidity test proves material preservation, not convincing locomotion. Stop iterating bone amplitudes when the base silhouette lacks contact, passing, and opposite-foot poses. The new player walk uses drawn lower-body frames behind an independently aimed upper body. Travel direction comes from displacement after collision resolution; mouse direction must not determine walking direction.

Sprite-sheet generation needs visual checking: the first atlas returned seven columns instead of eight, and later passes repeated the same supporting foot. Register poses at the belt at a common scale. For symmetric frontal/rear armor, mirror the first half-cycle for reliable opposite-foot phases. Inspect diagonal views separately; generated overlap and gait continuity still require artistic review. Four drawn keys are a starting cycle, not eight invented frames obtained by deforming the same picture.

The waist is an explicit layer boundary, with the lower belt behind the torso hem and the entire hanging gun retained on the upper layer. Keep gun sockets from that exact upper pose. Review moving gameplay plus enlarged views; a walk-in-place preview alone cannot reveal travel/aim coupling or collision-related foot sliding.


## Constrain and register independently animated body layers

The independent-leg pass produced impossible opposing poses and visible waist disconnection. Independence of control inputs does not imply unrestricted anatomical rotation. Select pelvis orientation relative to the actual torso source view, cap relative yaw (45 degrees here), and reverse the walk for retreat. Review all eight-by-eight aim/travel pairs, not only matching directions. Lateral movement currently uses constrained diagonal walking poses; dedicated strafing artwork remains an art improvement.

A shared ground anchor is insufficient for two body layers: export the animated pelvis attachment and register the lower belt to that exact point. Use one normalized phase for both layers, with contact settling and passing rise. When the torso animation changes, combat sockets must come from its new rendered metadata. Tests should check anatomical constraints, mirrored attachments, and weight-transfer phase in addition to muzzle alignment.


## Silhouette boundaries and environmental contact

Bone weights are not an extraction mask. The upper-body extraction left broad thigh remnants because hip blends and generous weapon weights retained leg pixels. Use explicit per-view torso hems, and separate render visibility polygons for hanging weapons/ammunition. Preserve deformation weights for recoil without treating every weighted pixel as part of the gun.

Painted scenery must be registered to the engine projection. The facade's masonry slope was approximately 0.60 versus the street's 0.50, compounded by a wall placement 24 world units behind the floor. A cached column projection preserves vertical pillars while matching horizontal masonry to the 2:1 world projection. Use an explicit front-face baseline anchor at the pavement edge rather than inferring it from image height. Inspect repeated segments at ground contact, not only one isolated wall.


## Inspect actual alpha continuity, not only skeleton registration

The socket-based join still showed a visible gap: the anatomical pelvis point was below the trimmed torso's visible hem. A correct skeleton coordinate is not a guaranteed visible connection. Enlarged contact sheets on a light background exposed this clearly across passing poses. Seat the belt inside the torso using per-view overlap; then recalibrate the ground anchor so fixing the seam does not make boots float. Keep those ground corrections in the geometry used by both rendering and combat sockets.

Do not mix a newly authored moving lower body with an older full-body idle sprite. The player now uses one layered set for idle, fire, walk, and walk-fire, with a nearest-contact stop pose. Review transitions as well as individual states. Cache shared lower-body poses instead of slicing/mirroring them for each aiming frame.

`tools/audit_ashgate_sprites.py` generates enlarged sheets for all eight directions, all compatible travel directions, four walk keys, and action-state comparisons. `tools/check_ashgate_seams.py` checks actual torso/belt alpha overlap across every fine aiming angle, torso animation frame, facing, and compatible lower pose. This pass checked 17,112 combinations, with minimum overlap 59 pixels at alpha >64 (required minimum 32). This confirms layer overlap within that tested set; visual continuity and natural gait still require inspection: the four-key authored cycle and reused diagonal strafe poses remain artistic limitations.
