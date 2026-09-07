"""Run Godot import, reference/combat checks, and a ten-second simulation.

Requires Python's standard library and Godot, but does not import pygame.
Godot 4.3 can return zero after script errors, so check output as well as status.
"""
import argparse
from pathlib import Path
from toolchain import godot_binary
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    engine = godot_binary()
    tasks = [
        (['--editor', '--import'], None),
        (['--script', 'res://tests/test_title.gd', '--', '--validation', '--touch', '--mute'], 'TITLE PASS:'),
        (['--script', 'res://tests/test_controller.gd', '--', '--validation', '--touch', '--mute'], 'CONTROLLER PASS:'),
        (['--script', 'res://tests/test_cover.gd', '--', '--validation', '--mute'], 'COVER PASS:'),
        (['--script', 'res://tests/test_level_two.gd', '--', '--validation', '--mute'], 'LEVEL TWO PASS:'),
        (['--script', 'res://tests/run_tests.gd', '--', '--validation', '--mute'], 'TEST PASS:'),
        (['--script', 'res://tests/audit_seams.gd'], 'SEAM PASS:'),
        (['--script', 'res://tests/test_touch.gd', '--', '--validation', '--touch', '--mute'], 'TOUCH PASS:'),
        (['--', '--smoke-test', '600', '--mute'], 'SMOKE PASS'),
    ]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--import-only', action='store_true')
    options = parser.parse_args()
    if options.import_only:
        tasks = tasks[:1]
    for args, marker in tasks:
        result = subprocess.run([engine, '--headless', '--path', str(ROOT/'godot'), *args],
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
        print(result.stdout, end='')
        if result.returncode or 'ERROR:' in result.stdout or (marker and marker not in result.stdout):
            raise SystemExit(1)
    print('IMPORT PASS' if options.import_only else 'VALIDATION PASS')


if __name__ == '__main__':
    main()
