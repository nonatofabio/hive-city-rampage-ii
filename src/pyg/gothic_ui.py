"""
Gothic UI System - Imperium-style HUD with TTF font rendering.

Provides High Gothic fonts, ornate panels, and grimdark UI elements.
"""

import pygame as pg
import os

# Color palette for UI
COLORS = {
    'gold': (185, 155, 95),
    'gold_light': (215, 185, 125),
    'gold_dark': (125, 95, 55),
    'bronze': (145, 115, 75),
    'crimson': (195, 55, 45),
    'crimson_dark': (145, 35, 35),
    'cyan': (65, 165, 215),
    'cyan_dark': (45, 115, 155),
    'green': (85, 175, 95),
    'green_dark': (55, 125, 65),
    'bone': (195, 185, 165),
    'parchment': (185, 165, 135),
    'iron': (95, 90, 85),
    'iron_dark': (55, 50, 48),
    'shadow': (25, 22, 20),
    'black': (15, 12, 10),
}


class GothicHUD:
    """Imperium-style heads-up display using TTF fonts."""

    def __init__(self, screen_width, screen_height, assets_path):
        self.W = screen_width
        self.H = screen_height
        self.assets_path = assets_path

        # Load TTF font
        font_path = os.path.join(assets_path, "font", "Ancient Medium.ttf")
        if os.path.exists(font_path):
            self.font_small = pg.font.Font(font_path, 16)
            self.font_medium = pg.font.Font(font_path, 20)
            self.font_large = pg.font.Font(font_path, 28)
            self.font_title = pg.font.Font(font_path, 36)
        else:
            # Fallback to system font
            self.font_small = pg.font.Font(None, 18)
            self.font_medium = pg.font.Font(None, 22)
            self.font_large = pg.font.Font(None, 30)
            self.font_title = pg.font.Font(None, 40)

        # Load UI images if available
        self._load_ui_images()

        # Panel dimensions
        self.panel_height = 76

        # Pre-render static panel
        self._build_panel()

    def _load_ui_images(self):
        """Load UI sprite images."""
        self.images = {}
        image_names = ['skulls', 'aquila', 'corners', 'grenade_icon', 'stim_icon']
        for name in image_names:
            path = os.path.join(self.assets_path, f"ui_{name}.png")
            if os.path.exists(path):
                self.images[name] = pg.image.load(path).convert_alpha()

    def _build_panel(self):
        """Build the HUD panel background."""
        self.panel = pg.Surface((self.W, self.panel_height), pg.SRCALPHA)

        # Dark metal gradient background
        for y in range(self.panel_height):
            darkness = 28 - (y // 8)
            color = (darkness, darkness - 4, darkness - 6)
            pg.draw.line(self.panel, color, (0, y), (self.W, y))

        # Bottom border - gold line
        pg.draw.line(self.panel, COLORS['gold_dark'], (0, self.panel_height - 4), (self.W, self.panel_height - 4), 2)
        pg.draw.line(self.panel, COLORS['gold'], (0, self.panel_height - 2), (self.W, self.panel_height - 2), 1)

        # Rivets along bottom
        for x in range(24, self.W - 24, 48):
            pg.draw.circle(self.panel, COLORS['gold_light'], (x, self.panel_height - 4), 3)
            pg.draw.circle(self.panel, COLORS['gold_dark'], (x, self.panel_height - 4), 3, 1)

        # Add aquila in center top if available
        if 'aquila' in self.images:
            aquila = self.images['aquila']
            ax = self.W // 2 - aquila.get_width() // 2
            self.panel.blit(aquila, (ax, 2))

    def _render_text(self, font, text, color, shadow=True):
        """Render text with optional drop shadow."""
        if shadow:
            shadow_color = (color[0] // 4, color[1] // 4, color[2] // 4)
            shadow_surf = font.render(text, True, shadow_color)
            text_surf = font.render(text, True, color)

            # Create combined surface
            w = text_surf.get_width() + 2
            h = text_surf.get_height() + 2
            combined = pg.Surface((w, h), pg.SRCALPHA)
            combined.blit(shadow_surf, (2, 2))
            combined.blit(text_surf, (0, 0))
            return combined
        else:
            return font.render(text, True, color)

    def draw_bar(self, screen, x, y, width, height, value, max_value,
                 fill_color, border_color, bg_color=None):
        """Draw an ornate progress bar."""
        if bg_color is None:
            bg_color = COLORS['shadow']

        # Background
        pg.draw.rect(screen, bg_color, (x, y, width, height))

        # Fill
        if max_value > 0:
            fill_width = int((value / max_value) * (width - 4))
            if fill_width > 0:
                pg.draw.rect(screen, fill_color, (x + 2, y + 2, fill_width, height - 4))

                # Highlight on fill
                highlight = (min(255, fill_color[0] + 40),
                             min(255, fill_color[1] + 40),
                             min(255, fill_color[2] + 40))
                pg.draw.line(screen, highlight, (x + 2, y + 2), (x + 2 + fill_width, y + 2))

        # Border
        pg.draw.rect(screen, border_color, (x, y, width, height), 2)

        # Corner rivets
        rivet_color = COLORS['gold_light']
        for rx, ry in [(x + 3, y + 3), (x + width - 4, y + 3),
                       (x + 3, y + height - 4), (x + width - 4, y + height - 4)]:
            pg.draw.circle(screen, rivet_color, (rx, ry), 2)

    def draw(self, screen, player, director, enemy_count):
        """Draw the complete HUD."""
        # Draw panel background
        screen.blit(self.panel, (0, 0))

        # === LEFT SECTION: Health & Shield ===
        bar_x = 24
        bar_width = 180

        # HP label and bar
        hp_label = self._render_text(self.font_small, "Vitae", COLORS['gold_light'])
        screen.blit(hp_label, (bar_x, 4))

        hp_pct = max(0, player.hp) / player.maxhp if player.maxhp > 0 else 0
        hp_color = COLORS['crimson'] if hp_pct > 0.25 else (255, 60, 60)
        self.draw_bar(screen, bar_x, 20, bar_width, 16,
                      max(0, player.hp), player.maxhp,
                      hp_color, COLORS['gold_dark'])

        # HP value text
        hp_text = self._render_text(self.font_small, f"{int(player.hp)}/{player.maxhp}", COLORS['bone'])
        screen.blit(hp_text, (bar_x + bar_width + 8, 20))

        # Shield label and bar
        shield_label = self._render_text(self.font_small, "Aegis", COLORS['cyan'])
        screen.blit(shield_label, (bar_x, 38))

        shield_color = COLORS['cyan'] if player.shield > 0 else COLORS['iron_dark']
        self.draw_bar(screen, bar_x, 52, bar_width, 12,
                      max(0, player.shield), player.max_shield,
                      shield_color, COLORS['cyan_dark'])

        # === CENTER SECTION: Wave Info ===
        center_x = self.W // 2

        # Wave number
        wave_text = self._render_text(self.font_large, f"Wave {director.wave}", COLORS['gold_light'])
        screen.blit(wave_text, (center_x - wave_text.get_width() // 2, 18))

        # Enemy count
        enemy_text = self._render_text(self.font_small, f"Hostiles: {enemy_count}", COLORS['crimson'])
        screen.blit(enemy_text, (center_x - enemy_text.get_width() // 2, 48))

        # === RIGHT SECTION: Score & Items ===
        right_x = self.W - 24

        # Score (right-aligned)
        score_str = f"{player.points:,}".replace(",", ".")
        score_text = self._render_text(self.font_large, score_str, COLORS['gold_light'])
        screen.blit(score_text, (right_x - score_text.get_width(), 4))

        # Skull icon next to score
        if 'skulls' in self.images:
            skull = self.images['skulls'].subsurface((0, 0, 16, 16))
            screen.blit(skull, (right_x - score_text.get_width() - 20, 8))

        # Combo (if active)
        if player.combo > 0:
            combo_color = COLORS['gold'] if player.combo < 5 else COLORS['crimson']
            combo_text = self._render_text(self.font_medium, f"x{player.combo + 1} FURY!", combo_color)
            screen.blit(combo_text, (right_x - combo_text.get_width(), 28))

        # Grenades
        grenade_color = COLORS['green'] if player.grenades > 0 else COLORS['iron_dark']
        if 'grenade_icon' in self.images:
            screen.blit(self.images['grenade_icon'], (right_x - 100, 50))
        grenade_text = self._render_text(self.font_small, str(player.grenades), grenade_color)
        screen.blit(grenade_text, (right_x - 80, 52))

        # Stims
        stims_left = 3 - player.stims_used
        stim_color = COLORS['green'] if stims_left > 1 else COLORS['crimson']
        if 'stim_icon' in self.images:
            screen.blit(self.images['stim_icon'], (right_x - 50, 50))
        stim_text = self._render_text(self.font_small, str(stims_left), stim_color)
        screen.blit(stim_text, (right_x - 30, 52))

        # === GAME OVER ===
        if player.hp <= 0:
            self._draw_game_over(screen, player.points)

    def _draw_game_over(self, screen, final_score):
        """Draw game over overlay."""
        # Darken screen
        overlay = pg.Surface((self.W, self.H - self.panel_height), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, self.panel_height))

        center_y = self.H // 2 + 20

        # Game over text
        go_text = self._render_text(self.font_title, "THE EMPEROR PROTECTS", COLORS['gold_light'])
        screen.blit(go_text, (self.W // 2 - go_text.get_width() // 2, center_y - 50))

        # Score
        score_text = self._render_text(self.font_large, f"FINAL TALLY: {final_score}", COLORS['bone'])
        screen.blit(score_text, (self.W // 2 - score_text.get_width() // 2, center_y))

        # Restart prompt
        restart_text = self._render_text(self.font_medium, "PRESS X TO SERVE AGAIN", COLORS['gold'])
        screen.blit(restart_text, (self.W // 2 - restart_text.get_width() // 2, center_y + 50))
