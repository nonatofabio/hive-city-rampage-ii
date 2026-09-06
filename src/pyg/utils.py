"""
Utility functions for Hive City Rampage
Math helpers and common operations
"""

import math


def clamp(v, a, b):
    """Clamp value v between a and b"""
    return a if v < a else b if v > b else v


def dist2(ax, ay, bx, by):
    """Squared distance between two points (avoids sqrt for performance)"""
    dx, dy = ax - bx, ay - by
    return dx*dx + dy*dy


def norm(dx, dy):
    """Normalize a vector and return (unit_x, unit_y, magnitude)"""
    d = math.hypot(dx, dy)
    if d < 1e-6:
        return 1.0, 0.0, 1.0
    return dx/d, dy/d, d


def lerp(a, b, t):
    """Linear interpolation between a and b by factor t"""
    return a + (b - a) * t