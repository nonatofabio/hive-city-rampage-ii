#!/bin/bash
set -euo pipefail
ashgate_root="$(cd "$(dirname "$0")" && pwd)"
if [[ -n "${GODOT_BIN:-}" ]]; then
    ashgate_engine="$GODOT_BIN"
elif [[ -x /Applications/Godot.app/Contents/MacOS/Godot ]]; then
    ashgate_engine=/Applications/Godot.app/Contents/MacOS/Godot
elif command -v godot >/dev/null 2>&1; then
    ashgate_engine="$(command -v godot)"
elif command -v godot4 >/dev/null 2>&1; then
    ashgate_engine="$(command -v godot4)"
else
    echo 'Godot 4 is required. Install it or set GODOT_BIN to its executable.' >&2
    exit 1
fi
# Ensure a fresh worktree imports its assets and registers GDScript classes first.
if [[ ! -f "$ashgate_root/godot/.godot/global_script_class_cache.cfg" ]]; then
    "$ashgate_engine" --headless --path "$ashgate_root/godot" --editor --import
fi
exec "$ashgate_engine" --path "$ashgate_root/godot" "$@"
