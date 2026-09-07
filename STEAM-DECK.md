# Steam Deck / Linux

Use the native Linux x86-64 package. It embeds the game data into the executable
and runs directly on SteamOS; leave forced Proton compatibility disabled.

1. In Desktop Mode, download `Hive-City-Rampage-II-0.4.0-Linux-SteamDeck.tar.gz`
   from the GitHub release and extract it into a permanent folder such as
   `/home/deck/Games/` (not a temporary download preview).
2. In Steam, choose **Add a Game → Add a Non-Steam Game → Browse** and select
   `Hive-City-Rampage-II.x86_64` in the extracted folder. If it is filtered out,
   select all file types. The archive preserves the executable permission;
   if your file manager strips it, enable **Is executable** in Properties.
3. Return to Gaming Mode and launch it from **Library → Non-Steam**.
4. Set its Steam Input template to **Gamepad**: left stick/D-pad moves, right
   stick moves the cursor, R2 fires, L2 throws a grenade, L3 dashes, and Start
   pauses. Holding fire near an enemy uses the chainsword.
5. Use the title menu's **Options** for cursor speed, Wide/Normal/Close view,
   and sound level. While paused, Y opens Options.

Keep the default 1280×800 display mode; the 16:9 game view is letterboxed while
menus remain readable. For trackpad aiming, you can optionally map the right
trackpad to Mouse, but start with the Gamepad template for the built-in sticks.

## Build from source

Install Godot 4.3 with its matching Linux export templates. From the repository:

```sh
mkdir -p build/linux
godot --headless --editor --path godot --import
godot --headless --path godot --export-release Linux "$(pwd)/build/linux/Hive-City-Rampage-II.x86_64"
```

Godot resolves the export destination relative to the project directory; use an
absolute output path if desired. On the configured macOS build host, `make build`
exports and packages Linux alongside Android and macOS and hashes all three.

The Linux build can be smoke-tested without a display:

```sh
./Hive-City-Rampage-II.x86_64 --headless -- --smoke-test 600 --mute
```

This is a manually installed preview, not a Steam Store or Deck Verified release.
