#!/bin/bash
# Run a Pico-8 game

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PICO8="$SCRIPT_DIR/pico-8/PICO-8.app/Contents/MacOS/pico8"

if [ -z "$1" ]; then
    echo "Usage: ./run.sh <game>"
    echo ""
    echo "Available games:"
    ls -1 "$SCRIPT_DIR/src/"*.p8 2>/dev/null | xargs -n1 basename | sed 's|.p8||'
    exit 1
fi

GAME="$SCRIPT_DIR/src/$1.p8"
if [ ! -f "$GAME" ]; then
    GAME="$1"  # Try as full path
fi

if [ ! -f "$GAME" ]; then
    echo "Game not found: $1"
    exit 1
fi

echo "Running: $GAME"
"$PICO8" -run "$GAME"