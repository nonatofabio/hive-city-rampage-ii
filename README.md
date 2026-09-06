# Hyve City Rampage II

A gothic isometric shooter by **nonatofabio**, built in **Godot 4**.
Deploy into the burning streets of Ashgate, destroy three signal relays,
bring down the siege walker, and fight your way to extraction.

![Hyve City Rampage II title screen](static/hyve-title.png)

## Play

Download a macOS or Android test build from [Releases](https://github.com/nonatofabio/hyve-city-rampage-ii/releases).
macOS builds are locally signed and not notarized. Android test APKs use a debug signing key.

From source, open `godot/project.godot` in Godot 4.3 or later, or double-click
**Play Godot.command** on macOS. No Python installation is needed to play.
Choose **Deploy to Ashgate** on the opening screen. **Field Orders** explains the mission and controls.

| Action | Desktop | Android |
| --- | --- | --- |
| Move | WASD | Left stick |
| Aim / fire | Mouse / left click | Right stick |
| Grenade | Space / right click | FRAG |
| Dash | Shift | DASH |
| Pause | Escape | PAUSE |

## Development

```sh
python3 tools/validate_godot.py
python3 tools/build_releases.py
```

Validation covers menu input, touch controls, combat, mission completion, and the
original sprite registration and silhouette audits. Exporting requires matching
Godot export templates, Java 17, and an Android SDK. See [technical notes](godot/README.md).

## Origins and credits

Sequel to [Hive City Rampage](https://github.com/nonatofabio/hive-city-rampage).
The original top-down Pygame game credits Claude; its README/screenshots commit
`3f5f993` names Claude Opus 4.5, while the gameplay commits do not specify a model.
The native Godot implementation and sequel menu were developed with Codex (GPT-6),
under Fabio Nonato’s direction.

The final Pygame art handoff is `b9828a6`; its source and Blender tools are retained
for asset editing and comparison. See the [legacy documentation](README_LEGACY.md).
Ashgate Siege is the first mission of Hyve City Rampage II.

Typography: Cinzel by Natanael Gama and Rajdhani by Indian Type Foundry.
Their SIL Open Font License notices ship in `godot/assets/fonts/`.
[Audio credits](src/pyg/assets/audio/CREDITS.md) retain source attribution.
