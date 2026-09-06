# Hyve City Rampage II — Godot technical notes

Playable migration of the current Ashgate mission to Godot 4 / typed GDScript.
Developed and tested with the locally installed Godot 4.3 on macOS Apple Silicon.
The game runs entirely in Godot; Python, Pygame, and Blender are offline tools only.

The sequel adds a deployment title screen and Cinzel / Rajdhani typography.

## Play

Double-click **Play Godot.command** in the worktree root. It finds the installed
Godot application and imports assets on the first launch. No Python environment is
needed. Alternatively, import `project.godot` in Godot and press **F6** with
`scenes/main.tscn` open, or **F5** to run the project.

```sh
./'Play Godot.command'
# Open the editor:
./'Play Godot.command' --editor
# Reproducible combat randomness and optional muted launch:
./'Play Godot.command' -- --seed 42 --mute
```

WASD moves; mouse aims; left click fires; Space/right click throws grenades;
Shift dashes; Escape pauses; R restarts after death/victory; M mutes;
minus/equal change gunfire volume. Losing window focus pauses gameplay.

Destroy all three relays, defeat the Cathedral-Breaker, and reach extraction.
The authored map, enemy stats, weapons, shield, pickups, kill chains, boss strike,
destructible cover, barrel chains, grenade arcs, casing bounce, and corpse fades
retain the prototype's rules. The viewport remains 960×540 and scales with the
window. Only the four approved bolter sounds play.

## Migration history and source snapshot

The migration began on `feat/ashgate-godot` in the separate `games-godot` worktree. The
first commit snapshots the original checkout's tracked, uncommitted art/motion
changes at migration start. The original checkout and its index were not modified.
Later work in the Pygame session is **not automatically synchronized** here.

The torso silhouette update from Pygame commit `fccbb04` has been synchronized:
138 cleaned upper-body sheets remove the old thigh remnants, retaining the waist
connection and hanging weapon. The same update's corrected facade projection and
ground anchors are exported into the Godot mission data.

The final Python handoff is **`b9828a6`**. Idle, fire, walk, and walk-fire now use
the same torso/leg layers, with per-view belt overlap, shared ground/socket
calibration, and nearest-contact stopping. `assets/data/player_registration.json`
holds those calibration values. Future gameplay work proceeds in Godot; Python
remains the frozen comparison reference and optional offline asset tooling.

`assets/` contains an independent copy of the runtime sheets and metadata, plus
baked scenery generated from that snapshot. It has no symlinks or references to
the original checkout. The original editable Blender rigs remain in `../art/blender`.

## Structure

- `scenes/main.tscn`: native world layers, Y-sorted objects, and canvas HUD.
- `scenes/actor.tscn`: reusable actor with shadow, lower body, torso, muzzle sprites.
- `scenes/effect.tscn`: reusable fire, explosion, and death animation with additive flash.
- `scripts/siege.gd`: fixed-step mission simulation, input, camera, bounded audio voices.
- `scripts/pose_library.gd`: Blender sheet metadata, anchors, aim solver, and gait selection.
- `scripts/iso.gd`: projection and swept segment collision.
- `scripts/hud.gd`, `world_overlay.gd`: native canvas drawing for HUD and transient overlays.
- `assets/data/mission.json`: authored entity placements separated from simulation code.

Combat uses the original flat world coordinate system. The display projects it
to isometric coordinates; node Y sorting uses ground contact. This preserves
collision radii and shot trajectories while Godot handles rendering and the loop.
The existing pre-rendered, planar Blender characters remain sprites.

## Verification

```sh
python3 tools/validate_godot.py  # from the worktree root; no pygame dependency
./'Play Godot.command' --script res://tests/capture_scenarios.gd -- --validation --mute
./'Play Godot.command' --script res://tests/capture_torso.gd -- --validation --mute
./'Play Godot.command' --script res://tests/capture_actions.gd -- --validation --mute
```

The checks compare 828 Pygame reference cases for poses, sockets, directional gait,
aim selection, movement, and all action/contact states. They also exercise cover interception, muzzle clipping,
shield/dash immunity, grenades, barrel chains, relay rewards, boss targeting,
extraction, death, pause/restart, and every runtime animation sheet.
The capture script renders opening, pause, boss, effects, and victory screenshots
into ignored `artifacts/`. A 600-frame smoke run exercises actual fixed-step play.
The torso capture creates four sheets covering all five views and all four gait
phases, both walking forward and retreating, through the real Godot sprite layers.
The action capture shows all four states in all eight visible directions. The native
seam audit checks all 17,112 combinations against imported texture alpha and the
runtime registration helpers; its five minimum overlaps exactly match Python's
report (59, 79, 79, 129, and 143 pixels; required minimum 32). Touch input tests cover
independent fingers, aiming/fire, grenade, dash, pause/resume, audio, restart, and
backgrounding. These are continuity checks, not a claim that the four-key gait is
artistically perfect. See [final visual review](FINAL_VISUAL_REVIEW.md).

## Rebuild assets or reference fixtures

Use a Python environment with pygame installed. These commands read this
worktree's Pygame snapshot and write only Godot exports or reference fixtures:

```sh
python tools/export_godot_assets.py
python tools/build_godot_fixtures.py
```

`assets/inventory.json` records hashes of exported runtime assets. Character sheets,
effect sheets, walk layers, JSON socket data, and WAVs are copied. Pygame's procedural
floor, cleaned/cropped props, shadows, and facades are baked once to PNG. This keeps
their existing appearance without keeping a Pygame runtime. Original provenance is
in `../src/pyg/assets/ASHGATE_ART.md` and `assets/audio/CREDITS.md`.

## Packaging and present limits

The macOS preset includes JSON files used by runtime loading. A portable resource
pack can be tested using the installed engine without export templates:

```sh
./'Play Godot.command' --headless --export-pack macOS artifacts/Ashgate-Siege.pck
/Applications/Godot.app/Contents/MacOS/Godot --main-pack /absolute/path/to/Ashgate-Siege.pck
```

## macOS and Android test builds

```sh
python3 tools/build_releases.py  # run from the worktree root after validation
```

This exports the universal macOS app to `../build/macos/Ashgate Siege.app`, creates
`../build/Ashgate-Siege-0.1.1-macOS.zip`, and produces the signed test APK at
`../build/android/Ashgate-Siege-0.1.1.apk`. The build manifest records artifact hashes
and source revision. The build script rejects an unsigned APK and checks both
platform signatures. macOS uses ad-hoc signing without Apple notarization; Android
uses the local debug key. These are direct-install test builds, not store submissions.

The installed toolchain is Godot 4.3 templates, Java 17, and Android SDK build-tools
34.0.0 / platform 34. `JAVA_HOME`, `ANDROID_HOME`, and `GODOT_BIN` can override local
paths. Android export also needs Java/Android paths configured in Godot's editor
settings. No signing credentials or SDKs are stored in the repository.

Android is locked to landscape, supports ARMv7 and ARM64, and has a left movement
stick, a right aim/fire stick, FRAG, DASH, and PAUSE buttons. The pause panel accepts
touch to resume/restart and to mute/unmute audio. Backgrounding clears held touches.
Use `./'Play Godot.command' -- --touch` for the mobile UI in desktop testing.

On macOS, extract the ZIP and open the app. A downloaded copy may require **Open
Anyway** in System Settings > Privacy & Security because it is not notarized.
On Android, transfer the APK, open it, and allow installation from that source if
prompted. USB installation is also supported with `adb install -r <apk path>`.

The standalone macOS app was run on Apple M1 with a rendered 240-frame smoke test
from outside the repository. Its executable contains both ARM64 and x86_64; Intel
execution has not been tested. The Android APK was installed and launched in an
ARM64 Android 14 / API 34 emulator, where touch restart, movement, firing, grenade,
and pause were exercised. Screenshots and runtime logs are in `../build/`. Physical
Android devices have not been tested. Both packages pass signature verification.

This is the playable parity milestone. The floor is a baked image, and mission
placements load from JSON; a visual TileMap level-authoring workflow is future work.
The HUD uses Godot's font rasterization and may differ slightly from Pygame.
GPU blending and pixel placement can differ slightly. Godot's random number generator
does not reproduce Python's exact enemy/loot/particle sequence for the same seed.
This port covers Ashgate Siege; the legacy `--classic` survival mode remains in Python.
Godot 4.3 was chosen for immediate local testing, not as a long-term engine version
commitment; an upgrade should get the same validation before adoption.
