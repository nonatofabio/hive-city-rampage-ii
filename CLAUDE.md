# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a game development repository containing both PICO-8 and Pygame games. The repository includes a PICO-8 fantasy console environment for macOS and Python/Pygame projects with a virtual environment setup.

## Development Commands

### Running PICO-8 Games
```bash
# Run a PICO-8 game by name (looks in src/p8/ directory)
./run.sh game_name

# Run a PICO-8 game by full path
./run.sh /path/to/game.p8

# List available PICO-8 games
./run.sh
```

### Running Pygame Games
```bash
# Run the main Pygame game
cd src/pyg
../../.venv/bin/python hive_city_rampage.py

# Generate sprites (run from assets directory)
cd src/pyg/assets
../../../.venv/bin/python generate_terrain.py
../../../.venv/bin/python generate_advanced_terrain.py
../../../.venv/bin/python generate_terrain_v2.py
../../../.venv/bin/python generate_enemies.py
../../../.venv/bin/python generate_props.py
../../../.venv/bin/python convert_sprites.py
```

### Virtual Environment
- Python virtual environment located at `.venv/`
- Contains pygame 2.6.1 and other dependencies
- Use `../../.venv/bin/python` when running from `src/pyg/`

## Code Architecture

### Repository Structure
```
games/
├── src/
│   ├── p8/           # PICO-8 games (.p8 cartridge files)
│   └── pyg/          # Pygame projects
│       ├── assets/   # Sprite sheets, terrain tiles, generation scripts
│       └── *.py      # Game implementation files
├── pico-8/           # PICO-8 application bundle
└── .venv/            # Python virtual environment
```

### Pygame Game Architecture (Hive City Rampage)

#### Module Structure
The game is organized into modular components:
- **hive_city_rampage.py**: Main game loop, rendering, and input handling (~800 lines)
- **constants.py**: All gameplay constants and configuration values
- **utils.py**: Math utilities (clamp, dist2, norm, lerp)
- **assets.py**: Sprite loading system with `SpriteBank` and `Anim` classes
- **world.py**: `Camera` (with shake) and `Arena` (procedural generation) classes
- **entities.py**: `Entity` base class, `Player`, `Enemy`, `Bullet`, `Pickup`, `Explosion`, `VFX`
- **director.py**: Wave-based enemy spawning with state machine
- **ai.py**: Target prioritization and aim assist

#### Core Systems
- **Tile-based world**: 32x32 pixel tiles, procedural arena generation
- **Entity system**: Base Entity class with collision detection, inherited by Player and Enemy
- **Animation system**: `Anim` class for sprite animation, `AnimatedTile` for terrain animations
- **Camera system**: Smooth follow with screen shake effects
- **Director system**: Wave-based enemy spawning with intensity scaling

#### Sprite Management
- **SpriteBank**: Centralized asset loading with `load_anim(key, filename, frames=N, fps=N)`
- **Animation strips**: Horizontal sprite sheets, frame width auto-calculated from image width / frame count
- **Variable frame sizes**: Different sprites can have different frame dimensions (e.g., marine_walk 44x48, marine_shoot 49x48)
- **Fallback rendering**: Colored placeholders when sprites are missing

#### Terrain System
- **Variant tiles**: 8 variations per tile type for visual diversity
- **Hazard tiles**: Toxic, electric, heat zones with unique visuals
- **Animated tiles**: Flickering lights, steam vents, electrical panels
- **Decal overlays**: Blood, debris, shell casings, scorch marks
- **Metadata**: JSON configuration for tile types and animations

#### Game Constants
- Display: 960x540 window, 60 FPS
- World: 120x90 tiles (3840x2880 pixels)
- Movement: WASD with acceleration-based physics
- Combat: Mouse aiming, left-click shooting, space for grenades

### PICO-8 Game Architecture

#### Cartridge Structure
- `.p8` files contain: `__lua__`, `__gfx__`, `__map__`, `__sfx__`, `__music__`
- Core loop: `_init()`, `_update()` or `_update60()`, `_draw()`
- State machine pattern: menu → play → gameover

#### PICO-8 Constraints
- Resolution: 128x128 pixels
- Sprites: 8x8 pixels (128x128 sprite sheet)
- Map: 128x32 tiles
- Token limit: 8192
- Cartridge size: 32KB

## Asset Generation

### Asset Generation Scripts
- `generate_terrain.py`: Basic wall/floor tiles with grim dark aesthetic
- `generate_advanced_terrain.py`: Corner tiles, hazards, animations, decals
- `generate_terrain_v2.py`: Autotiling system (16-state edge configurations)
- `generate_enemies.py`: Genestealer-style enemy sprites
- `generate_props.py`: Environmental objects (crates, barrels, computers, etc.)
- `generate_effects.py`: Explosion, smoke, shockwave animations and grenade pickup
- `convert_sprites.py`: Convert single-frame sprites to animation strips

### Sprite Organization
```
assets/
├── marine_idle.png       # Player idle (1 frame)
├── marine_walk.png       # Player walk (2 frames)
├── marine_shoot.png      # Player shoot (4 frames)
├── *_idle.png            # Enemy idle animations (4 frames)
├── *_walk.png            # Enemy walk animations (3 frames)
├── explosion.png         # Explosion animation (8 frames)
├── smoke.png             # Smoke effect (6 frames)
├── shockwave.png         # Shockwave effect (6 frames)
├── grenade_pickup.png    # Grenade pickup item
├── terrain_*.png         # Static tile variants
├── anim_*.png            # Animated tile sheets
├── decal_*.png           # Overlay graphics
├── hazard_*.png          # Special floor tiles
├── prop_*.png            # Environmental props
└── terrain_metadata.json # Tile configuration
```

## Key Implementation Details

### Collision Detection
- Pixel-based solid checking against tile map
- Separate X/Y movement for sliding along walls
- Entity radius-based collision with corners

### Enemy AI
- Direct pursuit with speed variations by type
- Separation forces to prevent clustering (32px for runners, 56px for others)
- Shooter enemies retreat at close range
- Contact damage with cooldowns and invincibility frames
- Sprite mirroring based on player position

### Wave System (Director)
- States: build → push → breather → spike
- Intensity scaling over time
- Budget-based spawning with pressure limits
- Safe spawn distance enforcement

### Player Controls
- **Movement**: WASD keys with acceleration-based physics
- **Aiming**: Mouse cursor for precise targeting
- **Shooting**: Left-click for primary weapon
- **Grenades**: Space bar for area-of-effect explosions (240px radius)
- **Shield**: Regenerates at 2/sec, pickups provide instant boost
- **Stim Packs**: Auto-revive on death (3 uses total)