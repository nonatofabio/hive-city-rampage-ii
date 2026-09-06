# Hive City Rampage II — development and release entry points.
.DEFAULT_GOAL := help
.NOTPARALLEL:

-include Makefile.local
PYTHON ?= python3
FFMPEG ?= ffmpeg
GODOT_BIN ?= $(shell command -v godot 2>/dev/null || command -v godot4 2>/dev/null || echo /Applications/Godot.app/Contents/MacOS/Godot)
GODOT_ARGS ?=
GAME_ARGS ?=
export GODOT_BIN JAVA_HOME ANDROID_HOME

.PHONY: help import run editor test build capture record import-props clean
help:
	@printf '%s\n' 'make run      Launch the game' 'make editor   Open Godot' 'make test     Validate menu, touch, combat and silhouettes' 'make build    Build and verify macOS + Android packages (macOS host)' 'make capture  Render title and review screenshots' 'make record   Record gameplay MP4 and a small GIF (requires ffmpeg)' 'make clean    Remove generated builds and Godot caches' '' 'Overrides: GODOT_BIN, JAVA_HOME, ANDROID_HOME, PYTHON' 'Example: make run GAME_ARGS="--mute --touch"'

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

import-props:
	@"$(GODOT_BIN)" --headless --path godot --script res://tools/import_props.gd

record: import
	@mkdir -p build/media
	@"$(GODOT_BIN)" --path godot --fixed-fps 30 --write-movie "$(CURDIR)/build/media/gameplay.avi" --script res://tests/record_gameplay.gd -- --validation
	@"$(FFMPEG)" -y -loglevel error -i build/media/gameplay.avi -t 14 -c:v libx264 -crf 26 -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart static/gameplay.mp4
	@"$(FFMPEG)" -y -loglevel error -ss 1 -t 8 -i static/gameplay.mp4 -filter_complex "[0:v]fps=10,scale=384:-1:flags=lanczos,split[a][b];[a]palettegen=stats_mode=diff:max_colors=64[p];[b][p]paletteuse=dither=none" -loop 0 static/gameplay.gif
	@rm -f build/media/gameplay.avi

.PHONY: record-level-two
record-level-two: import
	@mkdir -p build/media
	@"$(GODOT_BIN)" --path godot --fixed-fps 30 --write-movie "$(CURDIR)/build/media/iron-belly.avi" --script res://tests/record_level_two.gd -- --validation
	@"$(FFMPEG)" -y -loglevel error -i build/media/iron-belly.avi -t 16 -c:v libx264 -crf 26 -pix_fmt yuv420p -c:a aac -movflags +faststart static/iron-belly.mp4
	@rm -f build/media/iron-belly.avi
