#!/bin/bash
set -euo pipefail
hyve_root="$(cd "$(dirname "$0")" && pwd)"
if [[ -n "${GODOT_BIN:-}" ]]; then
    hyve_engine="$GODOT_BIN"
elif [[ -x "$HOME/Library/Caches/ashgate-build/godot-4.3/Godot.app/Contents/MacOS/Godot" ]]; then
    hyve_engine="$HOME/Library/Caches/ashgate-build/godot-4.3/Godot.app/Contents/MacOS/Godot"
elif [[ -x /Applications/Godot.app/Contents/MacOS/Godot ]]; then
    hyve_engine=/Applications/Godot.app/Contents/MacOS/Godot
elif command -v godot >/dev/null 2>&1; then
    hyve_engine="$(command -v godot)"
elif command -v godot4 >/dev/null 2>&1; then
    hyve_engine="$(command -v godot4)"
else
    echo 'Godot 4 is required. Install it or set GODOT_BIN to its executable.' >&2
    exit 1
fi
# Ensure a fresh worktree imports its assets and registers GDScript classes first.
if [[ ! -f "$hyve_root/godot/.godot/global_script_class_cache.cfg" ]]; then
    "$hyve_engine" --headless --path "$hyve_root/godot" --editor --import
fi
exec "$hyve_engine" --path "$hyve_root/godot" "$@"
