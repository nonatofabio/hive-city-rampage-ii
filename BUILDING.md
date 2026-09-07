# Build and run with Make

Run `make help` for the available targets. Commands are run from the repository
root, or from elsewhere with `make -C /path/to/hive-city-rampage-ii <target>`.

## Toolchain

Use Godot **4.3** and its matching export templates for reproducible previews.
Running, testing, and capturing need Godot, Make, and Python 3 with its standard library.
`make build` additionally requires a macOS host, Java 17, Android SDK platform 34,
build-tools 34.0.0, and Godot's Android debug signing key.

Copy `Makefile.local.example` to ignored `Makefile.local` and adjust its paths:

```make
GODOT_BIN := /Applications/Godot.app/Contents/MacOS/Godot
JAVA_HOME := /path/to/jdk-17/Contents/Home
ANDROID_HOME := /path/to/Android/sdk
```

`GODOT_BIN` otherwise resolves `godot` or `godot4` on PATH, then the standard macOS
application path. Environment variables and command-line Make variables are also
supported. No SDK paths, signing keys, or Python virtual environments are committed.
Configure the Java SDK, Android SDK, and debug keystore in Godot's editor export
settings before the first Android build. Install matching export templates through Godot.

## Commands

| Command | Result |
| --- | --- |
| `make run` | Import assets, then launch the title screen |
| `make editor` | Import assets, then open the Godot editor |
| `make test` | Import and run all native regression checks |
| `make build` | Import, export all three platforms, verify signatures, ZIP, hash |
| `make capture` | Render review screenshots into `godot/artifacts/` |
| `make record` | Record 14-second MP4 with audio and 8-second GIF; requires ffmpeg |
| `make import-props` | Repack the generated prop atlas into runtime sprites |
| `make clean` | Remove `build/`, `godot/artifacts/`, and `godot/.godot/` |

Pass engine flags with `GODOT_ARGS` and game flags with `GAME_ARGS`:

```sh
make run GAME_ARGS="--mute --touch"
make run GODOT_ARGS="--headless" GAME_ARGS="--smoke-test 600 --mute"
```

Godot import/test script errors are checked in addition to process exit codes.
The helpers in `tools/` use Python's standard library; no packages are installed.
Capture targets need a rendering display. Tests run headlessly.

## Artifacts

`godot/export_presets.cfg` defines the version and platform export settings.
Outputs under `build/` include a universal macOS `.app` and ZIP, an Android APK,
a native Linux x86-64 executable and Steam Deck tarball,
logs, and `manifest.json` containing SHA-256 hashes and the source commit.
The builder preserves existing artifacts and fails on import/export/signature errors.

The app uses ad-hoc signing and the APK uses a local debug key. The Android package
is `com.nonatofabio.hivecityrampageii`; macOS is not notarized. These are preview
packages, not store submissions. `make build` does not publish a release.

`make record` drives real mission input at 60 simulation steps per second, recorded
at 30 FPS with Godot Movie Maker. It applies no scripted damage or invulnerability.
The MP4 is 960 × 540; the lightweight GIF is 384 × 216 at 10 FPS. Outputs are in
`static/`; the temporary AVI is removed after successful conversion.

Use `make run GAME_ARGS="--level 2"` to select Iron Belly, and
`make record-level-two` to record its 16-second gameplay movie.

See [Steam Deck / Linux](STEAM-DECK.md) for the native Linux export and installation.
