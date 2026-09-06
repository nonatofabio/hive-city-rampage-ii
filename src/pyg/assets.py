"""
Asset loading and animation system for Hive City Rampage
Handles sprites, animations, and image loading
"""

import os
import random
import pygame as pg


def load_image(path):
    """Load an image with error handling"""
    try:
        return pg.image.load(path).convert_alpha()
    except Exception:
        return None


def slice_strip(img, frame_w, frame_h):
    """Slice a sprite sheet into frames"""
    if img is None:
        return []
    frames = []
    w, h = img.get_size()
    cols = w // frame_w
    rows = h // frame_h
    for y in range(rows):
        for x in range(cols):
            r = pg.Rect(x*frame_w, y*frame_h, frame_w, frame_h)
            frames.append(img.subsurface(r).copy())
    return frames


class Anim:
    """Animation controller for sprites"""
    def __init__(self, frames, fps=10):
        self.frames = frames
        self.fps = fps
        self.t = 0.0

    def update(self, dt):
        """Update animation timer"""
        self.t += dt

    def frame(self):
        """Get current frame"""
        if not self.frames:
            return None
        i = int(self.t * self.fps) % len(self.frames)
        return self.frames[i]


class AnimatedTile:
    """Animation controller for tiles with random start offset"""
    def __init__(self, frames, fps=10):
        self.frames = frames
        self.fps = fps
        self.t = random.random() * len(frames) / fps  # Random start time

    def update(self, dt):
        """Update animation timer"""
        self.t += dt

    def frame(self):
        """Get current frame"""
        if not self.frames:
            return None
        i = int(self.t * self.fps) % len(self.frames)
        return self.frames[i]


class SpriteBank:
    """Centralized sprite asset management"""
    def __init__(self, assets_dir="assets"):
        self.dir = assets_dir
        self.img = {}

    def get(self, key):
        """Get stored image data"""
        return self.img.get(key)

    def load_anim(self, key, filename, frames=4, fps=10):
        """Load animation strip. Frames are auto-sized from image width."""
        path = os.path.join(self.dir, filename)
        img = load_image(path)
        if img:
            w, h = img.get_size()
            frame_w = w // frames
            frame_list = slice_strip(img, frame_w, h)
        else:
            frame_list = []
        self.img[key] = (img, frame_list, fps)

    def anim(self, key):
        """Create animation instance from loaded data"""
        pack = self.img.get(key)
        if not pack:
            return Anim([], 10)
        _, frames, fps = pack
        return Anim(frames, fps)