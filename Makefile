# Hyve City Rampage II — development and release entry points.
.DEFAULT_GOAL := help
.NOTPARALLEL:

-include Makefile.local
PYTHON ?= python3
GODOT_BIN ?= $(shell command -v godot 2>/dev/null || command -v godot4 2>/dev/null || echo /Applications/Godot.app/Contents/MacOS/Godot)
GODOT_ARGS ?=
GAME_ARGS ?=
export GODOT_BIN JAVA_HOME ANDROID_HOME

.PHONY: help import run editor test build capture clean
help:
	@printf '%s\n' 'make run      Launch the game' 'make editor   Open Godot' 'make test     Validate menu, touch, combat and silhouettes' 'make build    Build and verify macOS + Android packages (macOS host)' 'make capture  Render title and review screenshots' 'make clean    Remove generated builds and Godot caches' '' 'Overrides: GODOT_BIN, JAVA_HOME, ANDROID_HOME, PYTHON' 'Example: make run GAME_ARGS="--mute --touch"'

import:
	@"$(PYTHON)" tools/validate_godot.py --import-only

run: import
	@"$(GODOT_BIN)" --path godot $(GODOT_ARGS) -- $(GAME_ARGS)

editor: import
	@"$(GODOT_BIN)" --path godot --editor $(GODOT_ARGS)

test:
	@"$(PYTHON)" tools/validate_godot.py

build:
	@"$(PYTHON)" tools/build_releases.py

capture: import
	@mkdir -p godot/artifacts
	@"$(GODOT_BIN)" --path godot --script res://tests/test_title.gd -- --validation --touch --mute
	@"$(GODOT_BIN)" --path godot --script res://tests/capture_scenarios.gd -- --validation --mute
	@"$(GODOT_BIN)" --path godot --script res://tests/capture_actions.gd -- --validation --mute

clean:
	rm -rf -- build godot/artifacts godot/.godot
