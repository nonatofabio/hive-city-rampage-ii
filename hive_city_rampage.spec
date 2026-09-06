# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Hive City Rampage
Packages the game with all assets for distribution
"""

import sys
from pathlib import Path

block_cipher = None

# Define paths
src_path = Path('src/pyg')
assets_path = src_path / 'assets'

# Collect all game modules
game_modules = [
    str(src_path / 'hive_city_rampage.py'),
    str(src_path / 'constants.py'),
    str(src_path / 'utils.py'),
    str(src_path / 'assets.py'),
    str(src_path / 'world.py'),
    str(src_path / 'entities.py'),
    str(src_path / 'director.py'),
    str(src_path / 'ai.py'),
]

# Collect all asset files (sprites, animations, etc.)
asset_files = []
if assets_path.exists():
    for asset in assets_path.rglob('*'):
        if asset.is_file() and asset.suffix.lower() in {'.png', '.json', '.ttf', '.ogg', '.wav', '.txt'}:
            destination = Path('assets') / asset.parent.relative_to(assets_path)
            asset_files.append((str(asset), str(destination)))

a = Analysis(
    game_modules,
    pathex=[str(src_path)],
    binaries=[],
    datas=asset_files,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='HiveCityRampage',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False for windowed app (no console)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you create one: 'assets/icon.ico'
)

# macOS app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='HiveCityRampage.app',
        icon=None,  # Add icon path here: 'assets/icon.icns'
        bundle_identifier='com.hivecityrampage.game',
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSHighResolutionCapable': 'True',
        },
    )
