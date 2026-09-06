"""Run Godot import, reference/combat checks, and a ten-second simulation.

Requires Python's standard library and Godot, but does not import pygame.
Godot 4.3 can return zero after script errors, so check output as well as status.
"""
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    engine = os.environ.get('GODOT_BIN') or shutil.which('godot') or shutil.which('godot4')
    if not engine and Path('/Applications/Godot.app/Contents/MacOS/Godot').exists():
        engine = '/Applications/Godot.app/Contents/MacOS/Godot'
    if not engine:
        raise SystemExit('Install Godot 4 or set GODOT_BIN.')
    tasks = [
        (['--editor', '--import'], None),
        (['--script', 'res://tests/test_title.gd', '--', '--validation', '--touch', '--mute'], 'TITLE PASS:'),
        (['--script', 'res://tests/run_tests.gd', '--', '--validation', '--mute'], 'TEST PASS:'),
        (['--script', 'res://tests/audit_seams.gd'], 'SEAM PASS:'),
        (['--script', 'res://tests/test_touch.gd', '--', '--validation', '--touch', '--mute'], 'TOUCH PASS:'),
        (['--', '--smoke-test', '600', '--mute'], 'SMOKE PASS'),
    ]
    for args, marker in tasks:
        result = subprocess.run([engine, '--headless', '--path', str(ROOT/'godot'), *args],
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
        print(result.stdout, end='')
        if result.returncode or 'ERROR:' in result.stdout or (marker and marker not in result.stdout):
            raise SystemExit(1)
    print('VALIDATION PASS')


if __name__ == '__main__':
    main()
