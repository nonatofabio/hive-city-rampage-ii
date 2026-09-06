# Building Hyve City Rampage II

Use Godot 4.3 and its matching export templates. The game itself needs no Python runtime.

1. Set `GODOT_BIN` to the Godot executable.
2. Install Java 17 and Android SDK build-tools 34.0.0; set `JAVA_HOME` and `ANDROID_HOME`.
3. Import and validate: `python3 tools/validate_godot.py`.
4. Build: `./build.sh` (or `python3 tools/build_releases.py`).
5. Run from source: `./run.sh`. Use `./run.sh --editor` to open the editor.

Both shell scripts work from any working directory. The launcher accepts Godot
arguments, including `./run.sh -- --mute`. The builder imports fresh assets before
exporting and preserves existing build artifacts. `GODOT_BIN` overrides engine
selection; on this development Mac, the cached Godot 4.3 used for the preview is
preferred over the newer application in `/Applications`.

Outputs are in `build/`: a universal macOS application and ZIP, an Android APK,
export/signature logs, and `manifest.json` with SHA-256 hashes and the source commit.
The macOS app uses ad-hoc signing; Android uses the local debug key.
The APK package is `com.nonatofabio.hyvecityrampageii` and installs alongside the old Ashgate test app.

Release binaries are built and tested locally, then attached to a GitHub prerelease.
The original Python build workflow is archived in `docs/legacy/` and does not run
on sequel release tags. The PyInstaller specification remains as legacy Python tooling.
