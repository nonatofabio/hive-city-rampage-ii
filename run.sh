#!/bin/bash
# Launch Hyve City Rampage II; pass Godot options through unchanged.
set -euo pipefail
hyve_root="$(cd "$(dirname "$0")" && pwd)"
exec "$hyve_root/Play Godot.command" "$@"
