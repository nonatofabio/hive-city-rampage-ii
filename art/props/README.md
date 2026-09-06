# Wreckage and permanent cover

Generated with the built-in image generation tool on 2026-09-06, using the game's
crate, barrel, and relay sprites as visual references. No external game assets were downloaded.

`atlas.png` is the final color-key source. The initial generation painted a checkerboard;
a second image edit replaced that background with magenta. `make import-props` keys
magenta, splits and trims the six cells, and scales them into transparent runtime PNGs
in `godot/assets/props/`. This uses Godot's image operations, not a Python image dependency.

The runtime pieces are crate/barrel/relay wrecks, sandbags, a concrete barricade, and
a steel tank trap. Wrecks stay for the mission; intact permanent cover remains solid.

## Generation prompt

Create ONE production sprite atlas on transparent background, exactly 3 columns by 2 rows of equal square cells, each object isolated entirely inside its cell with wide transparent gutters, NO labels or text. Match attached gothic isometric pixel-art props, same 2:1 isometric ground projection, top-left lighting, chunky hand-painted pixel clusters, dark outlines, brass/steel/cobalt palette. TOP LEFT: destroyed blue-and-brass supply crate from reference 1, crumpled split-open shell, bent blue armored lid fallen sideways, brass corners twisted, scattered scraps, low recognizable wreck. TOP MIDDLE: ruptured red explosive barrel from reference 2, peeled jagged metal rim, blackened crushed cylinder collapsed sideways, detached hoop and metal pieces, NO active fire or smoke. TOP RIGHT: ruined signal relay from reference 3, snapped spire lying diagonally over a scorched broken mechanical base, bent brass supports, shattered red energy tubes, severed cables, low rubble pile, NO active glow. BOTTOM LEFT: intact tactical sandbag barricade, compact oblong stack of tan/olive canvas bags three courses tall aligned along isometric northeast axis, sandbag seams and sagging weight, no insignia. BOTTOM MIDDLE: intact heavy concrete roadblock, low chunky trapezoidal gothic industrial barrier aligned along same isometric axis, worn grey concrete, two small steel braces and tiny faded black/yellow hazard stripes. BOTTOM RIGHT: intact squat dark steel tank trap, crossed heavy I-beams, scratched steel and rivets, isometric. All six sprites same coherent art style as references, not photorealistic, strong readable silhouette at 120px width. Ground-contact shadows compact translucent, preserve true transparency with no checkerboard. Each sprite centered in its cell, debris stays in that cell. No border, grid lines, decorations outside objects. Output 1536x1024 if possible.

## Background correction prompt

Precise game sprite atlas background correction. Keep all SIX objects, their pixels, positions and sizes, the 3x2 grid, and the 1536x1024 canvas exactly as in reference. Replace the entire baked white/grey checkerboard background with perfectly flat pure magenta RGB(255,0,255) #FF00FF for color-key sprite import. Remove soft ground shadows so objects end in crisp outlines against magenta. Do NOT change or recolor the objects, including the dark inner cavities of the wrecked crate/barrel. No checkerboard, gradients or texture in the magenta background. No text.
