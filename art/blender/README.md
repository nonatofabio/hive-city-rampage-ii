# Editable Blender sources

These source projects and textures belong to the assets used in Hive City Rampage II.
Open the `.blend` files directly in Blender for inspection or editing. They are not
loaded at runtime and are not needed to build the game.

- `ashgate_sprite_rigs.blend`: base character meshes and armatures.
- `ashgate_direction_rigs.blend`: additional authored player directions.
- `ashgate_aim_rigs.blend`: weapon aiming poses and sockets.
- `ashgate_upper_rigs.blend`: torso-only poses used by the layered player.
- `directions.json`, `weapon_rig.json`: direction landmarks and rigid weapon masks.
- `textures/`: source sprite textures.

Packed runtime exports are in `godot/assets/rendered/` and their metadata in
`godot/assets/data/`. Preserve the registered scale, ground, waist, and weapon
sockets when replacing them, then run `make test` and `make capture` at the root.

The original rendering/packing pipeline is preserved in
[Hive City Rampage](https://github.com/nonatofabio/hive-city-rampage/tree/feat/ashgate-audio-motion/tools/blender)
at the final art handoff `b9828a6`. That pipeline is not part of the sequel's build.
