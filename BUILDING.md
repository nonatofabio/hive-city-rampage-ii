# Building Hyve City Rampage II

Use Godot 4.3 and its matching export templates. The game itself needs no Python runtime.

1. Set `GODOT_BIN` to the Godot executable.
2. Install Java 17 and Android SDK build-tools 34.0.0; set `JAVA_HOME` and `ANDROID_HOME`.
3. Import and validate: `python3 tools/validate_godot.py`.
4. Build: `python3 tools/build_releases.py`.

Outputs are in `build/`: a universal macOS application and ZIP, an Android APK,
export/signature logs, and `manifest.json` with SHA-256 hashes and the source commit.
The macOS app uses ad-hoc signing; Android uses the local debug key.
The APK package is `com.nonatofabio.hyvecityrampageii` and installs alongside the old Ashgate test app.

Release binaries are built and tested locally, then attached to a GitHub prerelease.
The original Python build workflow is archived in `docs/legacy/` and does not run
on sequel release tags. `build.sh` and the PyInstaller specification are legacy Python tooling.
