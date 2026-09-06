"""Shared, portable Godot resolution for the Make helpers (standard library only)."""
import os
from pathlib import Path
import shutil


def godot_binary():
    engine = os.environ.get('GODOT_BIN') or shutil.which('godot') or shutil.which('godot4')
    if not engine and Path('/Applications/Godot.app/Contents/MacOS/Godot').is_file():
        engine = '/Applications/Godot.app/Contents/MacOS/Godot'
    if not engine or not shutil.which(engine):
        raise SystemExit('Install Godot 4.3 or set GODOT_BIN in Makefile.local.')
    return engine
