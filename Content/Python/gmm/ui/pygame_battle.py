"""PyGame Battle GUI — Melodia rhythm battle with Figma design system integration.

Features:
  - Figma design assets: grade pops, highway, hitline, filigree, iri overlay, grain, sheen, note glyph
  - Rhythm highway with scrolling note lanes (4 lanes: D/F/J/K)
  - SPACE/key rhythm detection synced to BPM
  - Animated HP/SP/ULT bars with easing
  - Command buttons (Basic, Skill, Ultimate, Defend, Flee)
  - Grade popups using Figma assets
  - Battle log panel with filigree corners
  - Enemy sprite with Figma enemy glow

Usage:
    from gmm.ui.pygame_battle import PyGameBattleGUI
    gui = PyGameBattleGUI()
    gui.run()

Or via CLI:
    python -m gmm.main --gui
"""

from __future__ import annotations

import math
import random
import sys
import time
from dataclasses import dataclass
from typing import Optional

import pygame

from gmm.game.battle_manager import (
    MelodiaBattleManager,
    PHASE_NONE,
    PHASE_AWAITING,
    PHASE_RHYTHM,
    PHASE_ENEMY,
    PHASE_VICTORY,
    PHASE_DEFEAT,
    PHASE_FLED,
)
from gmm.game.config import GAME_CFG
from gmm.game.data_registry import MelodiaDataRegistry
from gmm.game.player_state import MelodiaPlayerState
from gmm.game.audio_engine import AudioEngine
from gmm.melodia.enemies import list_enemies
from gmm.melodia.skills import list_skills
from gmm.ui.figma_assets import get_asset_loader, preload_figma_assets


# =============================================================================
# Colors & Constants (from Figma design tokens)
# =============================================================================

VOID = (13, 18, 36)
SURFACE = (18, 24, 42)
SURFACE_LIGHT = (26, 32, 58)
GOLD = (255, 230, 102)
CYAN = (102, 217, 255)
PEARL = (240, 220, 240)
MAGENTA = (255, 110, 178)
TEXT_PRIMARY = (236, 235, 244)
TEXT_SECONDARY = (169, 167, 192)
TEXT_MUTED = (110, 96, 128)
HP_COLOR = (102, 217, 255)
SP_COLOR = (255, 230, 102)
ULT_COLOR = (255, 110, 178)
RED = (255, 68, 102)
GREEN = (68, 255, 136)
ORANGE = (255, 180, 68)
IRIS = (155, 143, 197)
BORDER = (255, 255, 255, 30)
BORDER_GOLD = (201, 168, 106, 76)

GRADE_COLORS = {
    "perfect": GOLD,
    "great": CYAN,
    "good": PEARL,
    "miss": MAGENTA,
}
GRADE_LABELS = {
    "perfect": "PERFECT",
    "great": "GREAT",
    "good": "GOOD",
    "miss": "MISS",
}

COMMANDS = [
    ("basic_attack", "Basic", (100, 100, 100)),
    ("skill", "Skill", CYAN),
    ("ultimate", "Ultimate", MAGENTA),
    ("defend", "Defend", GREEN),
    ("flee", "Flee", ORANGE),
]

ELEMENT_COLORS = {
    "Forte": (255, 100, 100),
    "Stone": (180, 150, 80),
    "Umbral": (120, 80, 160),
    "Arcane": (100, 180, 220),
    "Radiant": (255, 220, 100),
    "Gale": (100, 200, 140),
    "Tide": (80, 160, 240),
    "Neutral": (180, 180, 180),
}

WINDOW_W = 1024
WINDOW_H = 640
FPS = 60

# Rhythm timing (matching MelodiaRhythmClock)
BEAT_TOLERANCE_PERFECT = 40.0   # ms
BEAT_TOLERANCE_GREAT = 80.0
BEAT_TOLERANCE_GOOD = 140.0

# Lane keys and positions
LANE_KEYS = ("D", "F", "J", "K")
LANE_COLORS = [GOLD, CYAN, MAGENTA, PEARL]
LANE_COUNT = 4
HIGHWAY_TOP = 160
HIGHWAY_HEIGHT = 280
HITLINE_Y = HIGHWAY_TOP + HIGHWAY_HEIGHT - 20
NOTE_SPEED = 400.0  # pixels per second
NOTE_SPAWN_Y = HIGHWAY_TOP - 40


# =============================================================================
# Helper Classes
# =============================================================================

@dataclass
class AnimBar:
    """Animated bar with smooth value interpolation."""
    x: int
    y: int
    w: int
    h: int
    color: tuple
    bg_color: tuple = (30, 30, 50)
    border_color: tuple = (60, 60, 90)
    value: float = 0.0
    target: float = 0.0
    speed: float = 8.0

    def update(self, dt: float):
        if abs(self.value - self.target) > 0.001:
            self.value += (self.target - self.value) * min(1.0, self.speed * dt)

    def set_target(self, ratio: float):
        self.target = max(0.0, min(1.0, ratio))

    def draw(self, surf: pygame.Surface, label: str = "", font: Optional[pygame.font.Font] = None):
        pygame.draw.rect(surf, self.bg_color, (self.x, self.y, self.w, self.h), border_radius=4)
        fill_w = int(self.w * self.value)
        if fill_w > 0:
            pygame.draw.rect(surf, self.color, (self.x, self.y, fill_w, self.h), border_radius=4)
        pygame.draw.rect(surf, self.border_color, (self.x, self.y, self.w, self.h), 2, border_radius=4)
        if label and font:
            txt = font.render(label, True, TEXT_SECONDARY)
            surf.blit(txt, (self.x, self.y - 18))


@dataclass
class GradePopup:
    """Floating grade text with animation using Figma grade assets."""
    x: float
    y: float
    grade: str
    damage: float
    spawn_time: float
    grade_surface: Optional[pygame.Surface] = None
    duration: float = 1.5
    vy: float = -60.0
    scale: float = 1.0
    scale_vel: float = 0.0

    def update(self, dt: float):
        self.y += self.vy * dt
        self.vy *= 0.98
        # Pop-in scale animation
        self.scale_vel += (1.0 - self.scale) * 15.0 * dt
        self.scale_vel *= 0.85
        self.scale += self.scale_vel * dt

    def is_alive(self, now: float) -> bool:
        return now - self.spawn_time < self.duration

    def draw(self, surf: pygame.Surface, font: pygame.font.Font, now: float):
        age = now - self.spawn_time
        alpha = int(255 * max(0.0, 1.0 - age / self.duration))

        if self.grade_surface:
            # Use Figma grade asset
            scaled = pygame.transform.rotozoom(self.grade_surface, 0, self.scale)
            scaled.set_alpha(alpha)
            rect = scaled.get_rect(center=(int(self.x), int(self.y)))
            surf.blit(scaled, rect)
        else:
            # Fallback text
            color = GRADE_COLORS.get(self.grade, TEXT_PRIMARY)
            color = (*color, alpha)
            label = GRADE_LABELS.get(self.grade, self.grade.upper())
            txt = font.render(label, True, color[:3])
            txt.set_alpha(alpha)
            rect = txt.get_rect(center=(int(self.x), int(self.y)))
            surf.blit(txt, rect)

        # Damage number
        if self.damage > 0:
            dmg_font = pygame.font.SysFont("consolas", 18, bold=True)
            dmg_txt = dmg_font.render(f"{self.damage:.0f}", True, (*GOLD, alpha))
            dmg_rect = dmg_txt.get_rect(center=(int(self.x), int(self.y + 32 * self.scale)))
            surf.blit(dmg_txt, dmg_rect)


class EnemySprite:
    """Enemy sprite using Figma enemy glow asset."""
    def __init__(self, element: str, size: int = 160):
        self.element = element
        self.size = size
        self.color = ELEMENT_COLORS.get(element, (180, 180, 180))
        self.anim_time = 0.0
        self.breath_phase = random.random() * math.pi * 2
        self._load_assets()

    def _load_assets(self):
        loader = get_asset_loader()
        self.glow = loader.get("enemy-glow")
        self.base_surface = self._generate_base()

    def _generate_base(self) -> pygame.Surface:
        """Generate procedural base shape."""
        s = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        cx, cy = self.size // 2, self.size // 2
        r = self.size // 2 - 8

        if self.element == "Forte":
            points = []
            for i in range(8):
                angle = i * math.pi / 4
                r_outer = r if i % 2 == 0 else r * 0.55
                points.append((cx + r_outer * math.cos(angle), cy + r_outer * math.sin(angle)))
            pygame.draw.polygon(s, self.color, points)
        elif self.element == "Stone":
            points = [(cx + r * math.cos(i * math.pi / 3), cy + r * math.sin(i * math.pi / 3)) for i in range(6)]
            pygame.draw.polygon(s, self.color, points)
        elif self.element == "Umbral":
            points = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
            pygame.draw.polygon(s, self.color, points)
        elif self.element == "Arcane":
            points = []
            for i in range(10):
                angle = i * math.pi / 5 - math.pi / 2
                r_outer = r if i % 2 == 0 else r * 0.35
                points.append((cx + r_outer * math.cos(angle), cy + r_outer * math.sin(angle)))
            pygame.draw.polygon(s, self.color, points)
        elif self.element == "Radiant":
            pygame.draw.circle(s, self.color, (cx, cy), r)
            for i in range(8):
                angle = i * math.pi / 4
                x1 = cx + (r * 0.5) * math.cos(angle)
                y1 = cy + (r * 0.5) * math.sin(angle)
                x2 = cx + (r * 1.4) * math.cos(angle)
                y2 = cy + (r * 1.4) * math.sin(angle)
                pygame.draw.line(s, (255, 255, 200), (x1, y1), (x2, y2), 3)
        elif self.element == "Gale":
            for i in range(3):
                angle = i * 2 * math.pi / 3 + self.breath_phase
                pts = []
                for t in range(20):
                    t_norm = t / 19.0
                    ra = r * t_norm
                    aa = angle + t_norm * 4
                    pts.append((cx + ra * math.cos(aa), cy + ra * math.sin(aa)))
                if len(pts) > 1:
                    pygame.draw.lines(s, self.color, False, pts, 3)
        elif self.element == "Tide":
            pts = []
            for i in range(40):
                x = i * self.size / 39
                y = cy + math.sin(i * 0.5 + self.breath_phase) * (r * 0.5)
                pts.append((x, y))
            pygame.draw.lines(s, self.color, False, pts, 4)
        else:
            pygame.draw.circle(s, self.color, (cx, cy), r)

        pygame.draw.circle(s, (255, 255, 255, 60), (cx, cy), r // 3)
        return s

    def update(self, dt: float, broken: bool = False):
        self.anim_time += dt
        self.breath_phase += dt * 2.0

    def draw(self, surf: pygame.Surface, x: int, y: int, broken: bool = False):
        scale = 1.0 + math.sin(self.breath_phase) * 0.03
        if broken:
            scale *= 0.9

        # Draw glow behind
        if self.glow:
            glow_scaled = pygame.transform.rotozoom(self.glow, 0, scale * 1.5)
            glow_rect = glow_scaled.get_rect(center=(x, y))
            surf.blit(glow_scaled, glow_rect)

        # Draw base
        base_scaled = pygame.transform.rotozoom(self.base_surface, 0, scale)
        if broken:
            base_scaled.fill((100, 100, 100, 180), special_flags=pygame.BLEND_RGBA_MULT)
        rect = base_scaled.get_rect(center=(x, y))
        surf.blit(base_scaled, rect)


class RhythmNote:
    """Scrolling note on the highway."""
    def __init__(self, lane: int, spawn_time: float, hit_time: float, note_type: str = "tap"):
        self.lane = lane
        self.spawn_time = spawn_time
        self.hit_time = hit_time
        self.note_type = note_type  # "tap", "hold", "slide"
        self.hit = False
        self.missed = False
        self.grade: Optional[str] = None
        self.x = 0
        self.y = 0

    def update(self, current_time: float):
        if self.hit or self.missed:
            return
        time_to_hit = self.hit_time - current_time
        if time_to_hit <= -0.2:  # 200ms grace after hit
            self.missed = True
        # Y position based on time
        self.y = HITLINE_Y - (time_to_hit * NOTE_SPEED)

    def draw(self, surf: pygame.Surface, note_head: Optional[pygame.Surface], lane_x: int):
        if self.hit or self.missed:
            return
        color = LANE_COLORS[self.lane]
        if self.note_type == "hold":
            pygame.draw.rect(surf, color, (lane_x - 20, int(self.y) - 10, 40, 20), border_radius=5)
            pygame.draw.rect(surf, (*color, 200), (lane_x - 18, int(self.y) - 8, 36, 16), 2, border_radius=5)
        else:
            if note_head:
                rect = note_head.get_rect(center=(lane_x, int(self.y)))
                surf.blit(note_head, rect)
            else:
                pygame.draw.circle(surf, color, (lane_x, int(self.y)), 18)
                pygame.draw.circle(surf, (*color, 200), (lane_x, int(self.y)), 18, 2)


class RhythmHighway:
    """4-lane rhythm highway with Figma assets."""
    def __init__(self, bpm: float):
        self.bpm = bpm
        self.beat_interval = 60.0 / bpm
        self.notes: list[RhythmNote] = []
        self.lane_rects: list[pygame.Rect] = []
        self.lane_centers: list[int] = []
        self.hitline_flash = 0.0
        self.grade_flash: Optional[tuple[str, float]] = None
        self._build_lanes()
        self._load_assets()

    def _load_assets(self):
        loader = get_asset_loader()
        assets = loader.get_rhythm_assets()
        self.highway_bg = assets.get("highway_bg")
        self.hitline = assets.get("hitline")
        self.note_head = assets.get("note_head")
        self.staff_tile = assets.get("staff_tile")
        self.sheen_sweep = assets.get("sheen_sweep")

    def _build_lanes(self):
        # Highway area
        hx = (WINDOW_W - 500) // 2
        lane_w = 500 // LANE_COUNT
        for i in range(LANE_COUNT):
            lx = hx + i * lane_w + lane_w // 2
            self.lane_centers.append(lx)
            self.lane_rects.append(pygame.Rect(hx + i * lane_w, HIGHWAY_TOP, lane_w, HIGHWAY_HEIGHT))

    def set_bpm(self, bpm: float):
        self.bpm = bpm
        self.beat_interval = 60.0 / bpm

    def spawn_note(self, lane: int, hit_time: float, note_type: str = "tap"):
        self.notes.append(RhythmNote(lane, time.time(), hit_time, note_type))

    def generate_pattern(self, current_time: float, measures: int = 4):
        """Generate a rhythmic pattern for the next N measures."""
        beat_time = current_time
        for m in range(measures):
            for beat in range(4):
                beat_time += self.beat_interval
                # 70% chance of note per beat, distributed across lanes
                if random.random() < 0.7:
                    lane = random.randrange(LANE_COUNT)
                    self.spawn_note(lane, beat_time)

    def update(self, current_time: float):
        self.hitline_flash = max(0.0, self.hitline_flash - 3.0 * (1/60))
        for note in self.notes:
            note.update(current_time)
        # Cleanup old missed notes
        self.notes = [n for n in self.notes if not (n.missed and n.hit_time < current_time - 0.5)]

    def check_hit(self, lane: int, current_time: float) -> Optional[str]:
        """Check if a note in the given lane was hit. Returns grade or None."""
        best_note = None
        best_error = float('inf')
        for note in self.notes:
            if note.lane != lane or note.hit or note.missed:
                continue
            error = abs(note.hit_time - current_time) * 1000  # ms
            if error < best_error:
                best_error = error
                best_note = note

        if best_note and best_error <= BEAT_TOLERANCE_GOOD:
            best_note.hit = True
            self.hitline_flash = 1.0
            if best_error <= BEAT_TOLERANCE_PERFECT:
                best_note.grade = "perfect"
            elif best_error <= BEAT_TOLERANCE_GREAT:
                best_note.grade = "great"
            else:
                best_note.grade = "good"
            self.grade_flash = (best_note.grade, current_time)
            return best_note.grade
        return None

    def draw(self, surf: pygame.Surface, current_time: float):
        # Highway background
        if self.highway_bg:
            # Tile the background
            for y in range(HIGHWAY_TOP, HIGHWAY_TOP + HIGHWAY_HEIGHT, self.highway_bg.get_height()):
                for x in range(self.lane_rects[0].left, self.lane_rects[-1].right, self.highway_bg.get_width()):
                    surf.blit(self.highway_bg, (x, y))
        else:
            # Fallback
            for rect in self.lane_rects:
                pygame.draw.rect(surf, (20, 25, 45), rect)
                pygame.draw.rect(surf, (40, 50, 80), rect, 1)

        # Staff lines (tiling)
        if self.staff_tile:
            for i, lx in enumerate(self.lane_centers):
                for y in range(HIGHWAY_TOP, HIGHWAY_TOP + HIGHWAY_HEIGHT, self.staff_tile.get_height()):
                    surf.blit(self.staff_tile, (lx - self.staff_tile.get_width() // 2, y))

        # Lane dividers
        for i in range(1, LANE_COUNT):
            x = self.lane_rects[i].left
            pygame.draw.line(surf, BORDER, (x, HIGHWAY_TOP), (x, HIGHWAY_TOP + HIGHWAY_HEIGHT), 1)

        # Notes
        for note in self.notes:
            if not note.hit and not note.missed:
                note.draw(surf, self.note_head, self.lane_centers[note.lane])

        # Hitline
        hitline_y = HITLINE_Y
        if self.hitline:
            hl_w = self.hitline.get_width()
            for i, lx in enumerate(self.lane_centers):
                rect = self.hitline.get_rect(center=(lx, hitline_y))
                if self.hitline_flash > 0:
                    flash_surf = self.hitline.copy()
                    flash_surf.fill((*GOLD, int(255 * self.hitline_flash)), special_flags=pygame.BLEND_RGBA_MULT)
                    surf.blit(flash_surf, rect)
                else:
                    surf.blit(self.hitline, rect)
        else:
            # Fallback hitline
            color = (*GOLD, int(255 * self.hitline_flash)) if self.hitline_flash > 0 else GOLD
            pygame.draw.line(surf, color, (self.lane_rects[0].left, hitline_y), (self.lane_rects[-1].right, hitline_y), 3)

        # Lane key labels
        font = pygame.font.SysFont("segoeui", 12, bold=True)
        for i, (lx, key) in enumerate(zip(self.lane_centers, LANE_KEYS)):
            txt = font.render(key, True, (*LANE_COLORS[i], 180))
            surf.blit(txt, (lx - txt.get_width() // 2, HIGHWAY_TOP + HIGHWAY_HEIGHT + 4))

        # Sheen sweep (on beat)
        if self.sheen_sweep and self.hitline_flash > 0:
            sweep = pygame.transform.scale(self.sheen_sweep, (self.lane_rects[-1].right - self.lane_rects[0].left, HIGHWAY_HEIGHT))
            sweep.set_alpha(int(100 * self.hitline_flash))
            surf.blit(sweep, (self.lane_rects[0].left, HIGHWAY_TOP))

        # Grade flash
        if self.grade_flash:
            grade, flash_time = self.grade_flash
            age = current_time - flash_time
            if age < 0.5:
                alpha = int(255 * (1.0 - age / 0.5))
                color = GRADE_COLORS.get(grade, TEXT_PRIMARY)
                txt = pygame.font.SysFont("segoeui", 24, bold=True).render(GRADE_LABELS.get(grade, grade), True, (*color, alpha))
                rect = txt.get_rect(center=(WINDOW_W // 2, HIGHWAY_TOP - 30))
                surf.blit(txt, rect)
            else:
                self.grade_flash = None


class FiligreePanel:
    """UI panel with Figma filigree corners and dividers."""
    def __init__(self):
        loader = get_asset_loader()
        self.corner = loader.get("filigree-corner")
        self.divider = loader.get("filigree-divider")
        self.iri_overlay = loader.get("iri-overlay")
        self.grain = loader.get("grain")

    def draw_panel(self, surf: pygame.Surface, rect: pygame.Rect, border_color: tuple = BORDER_GOLD):
        # Background
        pygame.draw.rect(surf, SURFACE, rect, border_radius=8)
        # Iri overlay
        if self.iri_overlay:
            iri_scaled = pygame.transform.scale(self.iri_overlay, rect.size)
            iri_scaled.set_alpha(30)
            surf.blit(iri_scaled, rect)
        # Grain
        if self.grain:
            grain_scaled = pygame.transform.scale(self.grain, rect.size)
            grain_scaled.set_alpha(15)
            surf.blit(grain_scaled, rect)
        # Border
        pygame.draw.rect(surf, border_color, rect, 2, border_radius=8)
        # Filigree corners
        if self.corner:
            cw, ch = self.corner.get_size()
            corners = [
                (rect.left, rect.top),
                (rect.right - cw, rect.top),
                (rect.left, rect.bottom - ch),
                (rect.right - cw, rect.bottom - ch),
            ]
            for cx, cy in corners:
                surf.blit(self.corner, (cx, cy))

    def draw_divider(self, surf: pygame.Surface, x1: int, y1: int, x2: int, y2: int):
        if self.divider:
            length = int(math.hypot(x2 - x1, y2 - y1))
            angle = math.atan2(y2 - y1, x2 - x1)
            scaled = pygame.transform.scale(self.divider, (length, self.divider.get_height()))
            rotated = pygame.transform.rotate(scaled, -math.degrees(angle))
            rect = rotated.get_rect(center=((x1 + x2) // 2, (y1 + y2) // 2))
            surf.blit(rotated, rect)
        else:
            pygame.draw.line(surf, BORDER_GOLD, (x1, y1), (x2, y2), 1)


# =============================================================================
# Main GUI Class
# =============================================================================

class PyGameBattleGUI:
    """Main PyGame battle interface with Figma design integration."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("GMM Rhythm Battle")
        self.screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        self.clock = pygame.time.Clock()
        self.running = True

        # Fonts (matching Figma: Inter for UI, Fraunces for display, IBM Plex Mono for data)
        self.font_display = pygame.font.SysFont("fraunces", 32, bold=True)
        self.font_large = pygame.font.SysFont("inter", 22, bold=True)
        self.font_medium = pygame.font.SysFont("inter", 16)
        self.font_small = pygame.font.SysFont("inter", 12)
        self.font_mono = pygame.font.SysFont("ibmplexmono", 12)
        self.font_grade = pygame.font.SysFont("fraunces", 36, bold=True)

        # Load Figma assets
        preload_figma_assets()
        self.asset_loader = get_asset_loader()
        self.grade_assets = self.asset_loader.get_grade_assets()
        self.filigree = FiligreePanel()

        # Game systems
        self.registry = MelodiaDataRegistry()
        self.player = MelodiaPlayerState()
        self.audio = AudioEngine()
        self.battle = MelodiaBattleManager(registry=self.registry, player=self.player, audio=self.audio)

        # UI State
        self.enemy_sprite: Optional[EnemySprite] = None
        self.highway: Optional[RhythmHighway] = None
        self.grade_popups: list[GradePopup] = []
        self.battle_log: list[tuple[str, tuple]] = []
        self.enemy_list = list_enemies()
        self.skill_list = list_skills()
        self.enemy_index = 0
        self.show_skill_menu = False
        self.selected_skill = 0

        # Animated bars
        self.player_hp_bar = AnimBar(40, 80, 280, 20, HP_COLOR)
        self.player_sp_bar = AnimBar(40, 110, 280, 14, SP_COLOR)
        self.player_ult_bar = AnimBar(40, 134, 280, 14, ULT_COLOR)
        self.enemy_hp_bar = AnimBar(WINDOW_W - 360, 80, 320, 20, HP_COLOR)
        self.enemy_tough_bar = AnimBar(WINDOW_W - 360, 110, 320, 10, CYAN)

        # Rhythm
        self.awaiting_rhythm = False

        # Combat log
        self.log_rect = pygame.Rect(40, WINDOW_H - 160, WINDOW_W - 80, 120)

        # Command buttons
        self.cmd_rects: list[pygame.Rect] = []
        self._build_command_buttons()

        self._log("Welcome to GMM Rhythm Battle!", GOLD)
        self._log("Press D/F/J/K on the beat during Rhythm phase.", CYAN)
        self._log("UP/DOWN to select enemy, ENTER to start.", TEXT_SECONDARY)

    def _build_command_buttons(self):
        btn_w = 160
        btn_h = 48
        spacing = 10
        start_x = (WINDOW_W - (btn_w * 5 + spacing * 4)) // 2
        y = WINDOW_H - 190
        for i, (cmd_id, label, color) in enumerate(COMMANDS):
            x = start_x + i * (btn_w + spacing)
            self.cmd_rects.append(pygame.Rect(x, y, btn_w, btn_h))

    def _log(self, msg: str, color: tuple = TEXT_SECONDARY):
        self.battle_log.append((f"> {msg}", color))
        if len(self.battle_log) > 25:
            self.battle_log.pop(0)

    def _spawn_enemy(self, enemy_id: str):
        result = self.battle.start_encounter(enemy_id)
        if result.get("ok"):
            enemy = self.battle.enemy
            self.enemy_sprite = EnemySprite(enemy.element, 180)
            self.highway = RhythmHighway(enemy.bpm)
            # Pre-generate first 2 measures
            self.highway.generate_pattern(time.time(), measures=2)
            self._log(f"Encounter: {enemy.display_name} ({enemy.element}, {enemy.bpm} BPM)", GREEN)
            self._update_bars()
        else:
            self._log(f"Failed: {result.get('error')}", RED)

    def _update_bars(self):
        if self.battle.enemy:
            p = self.battle
            hp_r = p.battle_hp / p.player.max_hp if p.player.max_hp else 0
            sp_r = p.battle_sp / GAME_CFG.shared_sp_max if GAME_CFG.shared_sp_max else 0
            ult_r = p.battle_ult / GAME_CFG.ult_max if GAME_CFG.ult_max else 0
            self.player_hp_bar.set_target(hp_r)
            self.player_sp_bar.set_target(sp_r)
            self.player_ult_bar.set_target(ult_r)

            e_hp_r = p.enemy_hp / p.enemy.max_hp if p.enemy.max_hp else 0
            e_tough_r = p.enemy_toughness / p.enemy.toughness if p.enemy.toughness else 0
            self.enemy_hp_bar.set_target(e_hp_r)
            self.enemy_tough_bar.set_target(e_tough_r)

    def _issue_command(self, cmd: str):
        if cmd == "skill" and self.show_skill_menu:
            skill_id = self.skill_list[self.selected_skill].skill_id
            result = self.battle.player_command(cmd, skill_id)
        else:
            result = self.battle.player_command(cmd)

        if result.get("ok"):
            self._log(f"Command: {COMMANDS[[c[0] for c in COMMANDS].index(cmd)][1]}", CYAN)
            if self.battle.phase == PHASE_RHYTHM:
                self.awaiting_rhythm = True
                self._log("Rhythm phase! Press D/F/J/K on beat.", GOLD)
                if self.highway and self.battle.enemy:
                    self.highway.set_bpm(self.battle.enemy.bpm)
                    # Generate more notes
                    self.highway.generate_pattern(time.time(), measures=2)
        else:
            self._log(f"Failed: {result.get('error')}", RED)

    def _resolve_rhythm_input(self, lane: int):
        if not self.awaiting_rhythm or not self.highway:
            return
        current_time = time.time()
        grade = self.highway.check_hit(lane, current_time)
        if grade:
            self.awaiting_rhythm = False
            # Grade popup with Figma asset
            dmg = 0  # Will be filled by battle result
            popup = GradePopup(
                x=WINDOW_W // 2 + random.uniform(-40, 40),
                y=HIGHWAY_TOP - 20,
                grade=grade,
                damage=dmg,
                spawn_time=current_time,
                grade_surface=self.grade_assets.get(grade),
            )
            self.grade_popups.append(popup)

    def _process_rhythm_result(self):
        """Called after rhythm phase resolves to get actual damage from battle manager."""
        # The battle manager was already called via resolve_rhythm in the CLI version
        # Here we simulate by checking if we're transitioning from rhythm phase
        pass

    def _check_auto_resolve(self):
        """Check if rhythm phase should auto-resolve (for demo)."""
        pass

    def _enemy_turn(self):
        result = self.battle.enemy_turn()
        if result.get("ok"):
            dmg = result.get("damage", 0)
            self._log(f"Enemy attacks for {dmg:.0f} damage!", RED)
            self._update_bars()
            if self.battle.phase == PHASE_DEFEAT:
                self._log("DEFEAT!", RED)
                self.audio.play_defeat()
            else:
                self._log("Your turn.", CYAN)
        else:
            self._log(f"Enemy turn failed: {result.get('error')}", RED)

    def _next_enemy(self, delta: int):
        self.enemy_index = (self.enemy_index + delta) % len(self.enemy_list)
        self._spawn_enemy(self.enemy_list[self.enemy_index]["enemy_id"])

    def _handle_keydown(self, event: pygame.event.Event):
        if event.key == pygame.K_ESCAPE:
            self.running = False
        elif event.key == pygame.K_UP:
            if self.battle.phase == PHASE_NONE:
                self._next_enemy(-1)
        elif event.key == pygame.K_DOWN:
            if self.battle.phase == PHASE_NONE:
                self._next_enemy(1)
        elif event.key == pygame.K_RETURN:
            if self.battle.phase == PHASE_NONE:
                self._spawn_enemy(self.enemy_list[self.enemy_index]["enemy_id"])
            elif self.battle.phase == PHASE_AWAITING:
                self._issue_command("basic_attack")
        elif event.key == pygame.K_SPACE:
            if self.battle.phase == PHASE_RHYTHM and self.awaiting_rhythm:
                # SPACE hits center lane (lane 1 = F)
                self._resolve_rhythm_input(1)
        elif event.key == pygame.K_d:
            if self.battle.phase == PHASE_RHYTHM and self.awaiting_rhythm:
                self._resolve_rhythm_input(0)
        elif event.key == pygame.K_f:
            if self.battle.phase == PHASE_RHYTHM and self.awaiting_rhythm:
                self._resolve_rhythm_input(1)
        elif event.key == pygame.K_j:
            if self.battle.phase == PHASE_RHYTHM and self.awaiting_rhythm:
                self._resolve_rhythm_input(2)
        elif event.key == pygame.K_k:
            if self.battle.phase == PHASE_RHYTHM and self.awaiting_rhythm:
                self._resolve_rhythm_input(3)
        elif event.key == pygame.K_TAB:
            if self.battle.phase == PHASE_AWAITING:
                self.show_skill_menu = not getattr(self, 'show_skill_menu', False)
                self.selected_skill = 0
        elif event.key == pygame.K_LEFT:
            if getattr(self, 'show_skill_menu', False):
                self.selected_skill = (self.selected_skill - 1) % len(self.skill_list)
        elif event.key == pygame.K_RIGHT:
            if getattr(self, 'show_skill_menu', False):
                self.selected_skill = (self.selected_skill + 1) % len(self.skill_list)
        elif event.key == pygame.K_s:
            if self.battle.phase == PHASE_AWAITING:
                self._issue_command("skill")
        elif event.key == pygame.K_u:
            if self.battle.phase == PHASE_AWAITING:
                self._issue_command("ultimate")
        elif event.key == pygame.K_d:
            if self.battle.phase == PHASE_AWAITING:
                self._issue_command("defend")
        elif event.key == pygame.K_f:
            if self.battle.phase == PHASE_AWAITING:
                self._issue_command("flee")
        elif event.key == pygame.K_e:
            if self.battle.phase == PHASE_ENEMY:
                self._enemy_turn()
        elif event.key == pygame.K_r:
            if self.battle.phase in (PHASE_VICTORY, PHASE_DEFEAT, PHASE_FLED):
                self.battle.end_encounter()
                self.enemy_sprite = None
                self.highway = None
                self.grade_popups.clear()
                self._log("Encounter ended. Select new enemy.", GREEN)

    def _handle_mouse(self, pos: tuple, clicked: bool):
        for i, rect in enumerate(self.cmd_rects):
            if rect.collidepoint(pos):
                if clicked:
                    cmd_id = COMMANDS[i][0]
                    if cmd_id == "skill":
                        self.show_skill_menu = not getattr(self, 'show_skill_menu', False)
                    else:
                        self._issue_command(cmd_id)
                return

    def update(self, dt: float):
        # Animate bars
        self.player_hp_bar.update(dt)
        self.player_sp_bar.update(dt)
        self.player_ult_bar.update(dt)
        self.enemy_hp_bar.update(dt)
        self.enemy_tough_bar.update(dt)

        if self.enemy_sprite:
            self.enemy_sprite.update(dt, self.battle.enemy_broken if self.battle.enemy else False)

        if self.highway:
            self.highway.update(time.time())

        # Update grade popups
        now = time.time()
        self.grade_popups = [p for p in self.grade_popups if p.is_alive(now)]
        for p in self.grade_popups:
            p.update(dt)

        # Auto enemy turn
        if self.battle.phase == PHASE_ENEMY:
            self._enemy_turn()

    def draw(self):
        self.screen.fill(VOID)

        # Enemy panel (right)
        self._draw_enemy_panel()

        # Player panel (left)
        self._draw_player_panel()

        # Center: Rhythm highway during rhythm phase
        if self.battle.phase == PHASE_RHYTHM and self.highway:
            self.highway.draw(self.screen, time.time())
            # Prompt
            prompt = self.font_display.render("HIT D/F/J/K ON THE BEAT", True, GOLD)
            prompt_rect = prompt.get_rect(center=(WINDOW_W // 2, HIGHWAY_TOP - 40))
            # Gold hairline
            pygame.draw.line(self.screen, BORDER_GOLD, (prompt_rect.left - 20, prompt_rect.bottom + 8), (prompt_rect.right + 20, prompt_rect.bottom + 8), 2)
            self.screen.blit(prompt, prompt_rect)

        # Grade popups
        for p in self.grade_popups:
            p.draw(self.screen, self.font_grade, time.time())

        # Battle log
        self._draw_log()

        # Command buttons
        self._draw_commands()

        # Skill menu overlay
        if getattr(self, 'show_skill_menu', False):
            self._draw_skill_menu()

        # Phase indicator
        self._draw_phase_indicator()

        pygame.display.flip()

    def _draw_player_panel(self):
        x, y = 40, 40
        # Panel rect
        panel_rect = pygame.Rect(x - 10, y - 10, 340, 220)
        self.filigree.draw_panel(self.screen, panel_rect, BORDER_GOLD)

        # Name/Level
        name_txt = self.font_display.render(f"Grandmaster Lv.{self.player.level}", True, CYAN)
        self.screen.blit(name_txt, (x, y))

        # Bars
        self.player_hp_bar.draw(self.screen, "HP", self.font_small)
        self.player_sp_bar.draw(self.screen, "SP", self.font_small)
        self.player_ult_bar.draw(self.screen, "ULT", self.font_small)

        # Stats
        stats_y = 180
        equipped = self.player.get_equipped_stats()
        stats = [
            f"ATK  {equipped['min_attack']:.0f}-{equipped['max_attack']:.0f}",
            f"DEF  {equipped['defense']:.0f}",
            f"SPD  {self.player.speed:.0f}",
            f"Gold {self.player.gold}",
        ]
        for i, s in enumerate(stats):
            txt = self.font_mono.render(s, True, TEXT_SECONDARY)
            self.screen.blit(txt, (x, stats_y + i * 20))

        # XP bar
        xp_ratio = self.player.xp / self.player.xp_to_next if self.player.xp_to_next > 0 else 0
        xp_bar = AnimBar(x, stats_y + 95, 280, 8, GOLD)
        xp_bar.value = xp_ratio
        xp_bar.target = xp_ratio
        xp_bar.draw(self.screen, f"XP: {self.player.xp}/{self.player.xp_to_next}", self.font_small)

    def _draw_enemy_panel(self):
        if not self.battle.enemy:
            return

        x = WINDOW_W - 370
        y = 40
        panel_rect = pygame.Rect(x - 10, y - 10, 350, 320)
        self.filigree.draw_panel(self.screen, panel_rect, BORDER_GOLD)

        # Name
        name_txt = self.font_display.render(self.battle.enemy.display_name, True, MAGENTA)
        self.screen.blit(name_txt, (x, y))

        # Element badge
        elem_color = ELEMENT_COLORS.get(self.battle.enemy.element, TEXT_SECONDARY)
        elem_txt = self.font_medium.render(self.battle.enemy.element, True, elem_color)
        self.screen.blit(elem_txt, (x, y + 36))

        # BPM
        bpm_txt = self.font_mono.render(f"BPM: {self.battle.enemy.bpm}", True, TEXT_SECONDARY)
        self.screen.blit(bpm_txt, (x + 100, y + 36))

        # Enemy sprite
        if self.enemy_sprite:
            self.enemy_sprite.draw(self.screen, WINDOW_W // 2 + 140, 200, self.battle.enemy_broken)

        # Bars
        self.enemy_hp_bar.draw(self.screen, "HP", self.font_small)
        self.enemy_tough_bar.draw(self.screen, "TOUGHNESS", self.font_small)

        # Break indicator
        if self.battle.enemy_broken:
            break_txt = self.font_large.render("BROKEN", True, RED)
            self.screen.blit(break_txt, (x, y + 160))

        # Level
        lvl_txt = self.font_mono.render(f"Level 1  •  {self.battle.enemy.max_hp:.0f} HP", True, TEXT_MUTED)
        self.screen.blit(lvl_txt, (x, y + 200))

    def _draw_log(self):
        # Panel
        log_panel = pygame.Rect(self.log_rect.x - 10, self.log_rect.y - 10, self.log_rect.w + 20, self.log_rect.h + 20)
        self.filigree.draw_panel(self.screen, log_panel)

        # Log entries (bottom-up)
        y = self.log_rect.bottom - 10
        for msg, color in reversed(self.battle_log):
            txt = self.font_mono.render(msg, True, color)
            y -= txt.get_height() + 2
            if y < self.log_rect.top:
                break
            self.screen.blit(txt, (self.log_rect.left + 10, y))

    def _draw_commands(self):
        for i, (cmd_id, label, color) in enumerate(COMMANDS):
            rect = self.cmd_rects[i]
            enabled = self.battle.phase == PHASE_AWAITING

            if cmd_id == "ultimate":
                enabled = enabled and self.battle.battle_ult >= GAME_CFG.ult_max
            if cmd_id == "skill":
                enabled = enabled and len(self.skill_list) > 0

            bg = color if enabled else (50, 50, 70)
            fg = VOID if enabled else TEXT_MUTED

            pygame.draw.rect(self.screen, bg, rect, border_radius=6)
            pygame.draw.rect(self.screen, (80, 80, 120), rect, 2, border_radius=6)

            txt = self.font_medium.render(label, True, fg)
            txt_rect = txt.get_rect(center=rect.center)
            self.screen.blit(txt, txt_rect)

            # Hotkey hint
            hotkey_map = {"basic_attack": "ENTER", "skill": "S / TAB", "ultimate": "U", "defend": "D", "flee": "F"}
            hk = self.font_small.render(hotkey_map.get(cmd_id, ""), True, (*fg, 180))
            self.screen.blit(hk, (rect.right - hk.get_width() - 8, rect.bottom - 20))

    def _draw_skill_menu(self):
        if not self.skill_list:
            return

        menu_w = 440
        menu_h = min(340, len(self.skill_list) * 38 + 60)
        menu_x = (WINDOW_W - menu_w) // 2
        menu_y = (WINDOW_H - menu_h) // 2

        # Panel
        panel_rect = pygame.Rect(menu_x, menu_y, menu_w, menu_h)
        self.filigree.draw_panel(self.screen, panel_rect, GOLD)

        title = self.font_display.render("Select Skill", True, GOLD)
        self.screen.blit(title, (menu_x + 20, menu_y + 15))

        for i, skill in enumerate(self.skill_list):
            y = menu_y + 55 + i * 38
            if y > menu_y + menu_h - 35:
                break

            selected = i == self.selected_skill
            bg = SURFACE_LIGHT if selected else SURFACE
            pygame.draw.rect(self.screen, bg, (menu_x + 15, y, menu_w - 30, 32), border_radius=4)
            if selected:
                pygame.draw.rect(self.screen, CYAN, (menu_x + 15, y, menu_w - 30, 32), 2, border_radius=4)

            color = ELEMENT_COLORS.get(skill.element, TEXT_PRIMARY)
            name_txt = self.font_medium.render(skill.display_name, True, color)
            self.screen.blit(name_txt, (menu_x + 25, y + 4))

            info_txt = self.font_small.render(f"DMG:{skill.base_damage} SP:{skill.sp_cost} {skill.element}", True, TEXT_SECONDARY)
            self.screen.blit(info_txt, (menu_x + 200, y + 6))

        hint = self.font_small.render("LEFT/RIGHT to select, ENTER to confirm, TAB to close", True, TEXT_MUTED)
        self.screen.blit(hint, (menu_x + 20, menu_y + menu_h - 28))

    def _draw_phase_indicator(self):
        phase_colors = {
            PHASE_NONE: TEXT_MUTED,
            PHASE_AWAITING: CYAN,
            PHASE_RHYTHM: GOLD,
            PHASE_ENEMY: MAGENTA,
            PHASE_VICTORY: GREEN,
            PHASE_DEFEAT: RED,
            PHASE_FLED: ORANGE,
        }
        phase_labels = {
            PHASE_NONE: "SELECT ENEMY  ↑/↓  ENTER to start",
            PHASE_AWAITING: "YOUR TURN  —  ENTER: Basic  S: Skill  U: Ultimate  D: Defend  F: Flee",
            PHASE_RHYTHM: "RHYTHM PHASE  —  D/F/J/K on beat",
            PHASE_ENEMY: "ENEMY TURN  —  E to process",
            PHASE_VICTORY: "VICTORY!  R to continue",
            PHASE_DEFEAT: "DEFEAT  R to continue",
            PHASE_FLED: "FLED  R to continue",
        }
        color = phase_colors.get(self.battle.phase, TEXT_PRIMARY)
        label = phase_labels.get(self.battle.phase, self.battle.phase)
        txt = self.font_large.render(label, True, color)
        rect = txt.get_rect(center=(WINDOW_W // 2, 28))
        # Gold hairline
        pygame.draw.line(self.screen, BORDER_GOLD, (rect.left - 20, rect.top - 6), (rect.right + 20, rect.top - 6), 2)
        bg_rect = rect.inflate(20, 10)
        pygame.draw.rect(self.screen, SURFACE, bg_rect, border_radius=6)
        pygame.draw.rect(self.screen, color, bg_rect, 2, border_radius=6)
        self.screen.blit(txt, rect)

    def run(self):
        last_time = time.time()
        while self.running:
            now = time.time()
            dt = min(now - last_time, 1.0 / 30.0)
            last_time = now

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    self._handle_keydown(event)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._handle_mouse(event.pos, True)
                elif event.type == pygame.MOUSEMOTION:
                    self._handle_mouse(event.pos, False)

            self.update(dt)
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()


def launch_pygame_battle():
    """Entry point for PyGame battle GUI."""
    gui = PyGameBattleGUI()
    gui.run()


if __name__ == "__main__":
    launch_pygame_battle()