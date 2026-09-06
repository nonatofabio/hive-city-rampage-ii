#!/bin/bash
# Build the Godot sequel for macOS and Android without deleting existing artifacts.
set -euo pipefail
hyve_root="$(cd "$(dirname "$0")" && pwd)"
if [[ $# -gt 0 ]]; then
    echo 'Usage: ./build.sh (configure GODOT_BIN, JAVA_HOME and ANDROID_HOME as needed)' >&2
    exit 2
fi
exec python3 "$hyve_root/tools/build_releases.py"
