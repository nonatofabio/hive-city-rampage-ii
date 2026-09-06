"""
AI and targeting system for Hive City Rampage
Aim assist and enemy behavior utilities
"""

from constants import AIM_RANGE, AIM_CONE
from utils import norm


def pick_aim_target(player, enemies, rng=AIM_RANGE, cone=AIM_CONE):
    """
    Select best enemy target within range and cone
    Prioritizes enemies in front of player with type weighting
    """
    best = None
    bestscore = -1e9
    fx, fy = player.face

    for e in enemies:
        dx, dy = e.x - player.x, e.y - player.y
        ux, uy, d = norm(dx, dy)

        if d <= rng:
            # Check if enemy is in front
            infront = ux*fx + uy*fy
            if infront >= (1-cone):
                # Weight by enemy type
                kindw = 0.0
                if e.kind == "shooter":
                    kindw = 0.25
                if e.kind == "brute":
                    kindw = 0.35

                # Score based on direction, distance, and type
                score = infront*2 - (d/rng) + kindw
                if score > bestscore:
                    bestscore = score
                    best = e

    return best