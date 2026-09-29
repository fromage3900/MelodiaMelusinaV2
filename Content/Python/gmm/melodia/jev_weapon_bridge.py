"""Jev-driven Melusina Transforming WaveHarp, Real-Time Archery Combat & Overworld HUD Bridge.

Provides the end-to-end operational implementation for:
1. Melusina Weapon Stance:
   - HARP_EXPLORATION: Real-time instrument playing, 7-string plucking, musical exploration & resonance.
   - BOW_COMBAT: Real-time archery combat, aiming, variable draw tension, crystal arrow projectile release.
2. Intermittent WaveHarp Transformation:
   - Governs the transformation state machine, cooldowns, and visual asset/FX transitions between
     SM_ME_WaveHarp_Harp_R07 and SM_ME_WaveHarp_Bow_R07.
3. Jev Conductor Integration:
   - Direct live integration with typesafe_sdk using TYPESAFE_API_KEY.
   - Dynamically evaluates musical/combat telemetry (BPM, beat energy, target distance, movement, resonance, wind)
     to select authored attack montages (BOW_V1, BOW_V2, BOW_POLISHED, BOW_GAMEPLAY) and conduct arrow loose timing.
4. Overworld HUD Integration:
   - Callable switch button interface and live HUD data provider for WBP_Melodia_OverworldHUD.
"""
from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional, Tuple

# Ensure Prototypes directory is accessible for Jev conductor imports
_PROTO_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "Prototypes", "JevBowConductor")
)
if os.path.isdir(_PROTO_DIR) and _PROTO_DIR not in sys.path:
    sys.path.insert(0, _PROTO_DIR)

try:
    from jev_bow_director import (
        BowConductor,
        BowDecision,
        BowState,
        format_hud,
        ASSET_MAP,
    )
except Exception:
    BowConductor = None
    BowDecision = None
    BowState = None
    format_hud = None
    ASSET_MAP = {}


# ---------------------------------------------------------------------------
# Constants & Asset Mapping
# ---------------------------------------------------------------------------

class WeaponStance:
    HARP_EXPLORATION = "HARP_EXPLORATION"
    BOW_COMBAT = "BOW_COMBAT"


WEAPON_SOCKET_BOW_HELD = "hand_l_socket"
WEAPON_SOCKET_STRING_DRAW = "hand_r_socket"
WEAPON_SOCKET_HARP_HELD = "S_Instrument_L"
WEAPON_SOCKET_HARP_PLUCK = "S_Instrument_R"
WEAPON_SOCKET_HOLSTER = "spine_quiver_socket"

MESH_HARP = "/Game/MelodiaIntegration/Weapons/WaveHarp/SM_ME_WaveHarp_Harp_R07.SM_ME_WaveHarp_Harp_R07"
MESH_BOW = "/Game/MelodiaIntegration/Weapons/WaveHarp/SM_ME_WaveHarp_Bow_R07.SM_ME_WaveHarp_Bow_R07"
MESH_ARROW = "/Game/MelodiaIntegration/Weapons/WaveHarp/SM_WaveHarp_CrystalArrow"

VFX_TRANSFORM_BURST = "/Game/MelodiaIntegration/VFX/NS_WaveHarp_Transform"
VFX_ARROW_TRAIL = "/Game/MelodiaIntegration/VFX/NS_CrystalArrowTrail"

# 7 Diatonic Strings of the WaveHarp (Key of C / A minor)
HARP_STRINGS: List[Dict[str, Any]] = [
    {"index": 0, "note": "C4", "midi": 60, "solfege": "Do", "freq_hz": 261.63, "color": [0.2, 0.6, 1.0]},
    {"index": 1, "note": "D4", "midi": 62, "solfege": "Re", "freq_hz": 293.66, "color": [0.25, 0.7, 0.9]},
    {"index": 2, "note": "E4", "midi": 64, "solfege": "Mi", "freq_hz": 329.63, "color": [0.3, 0.8, 0.8]},
    {"index": 3, "note": "F4", "midi": 65, "solfege": "Fa", "freq_hz": 349.23, "color": [0.35, 0.9, 0.7]},
    {"index": 4, "note": "G4", "midi": 67, "solfege": "Sol", "freq_hz": 392.00, "color": [0.4, 0.95, 0.6]},
    {"index": 5, "note": "A4", "midi": 69, "solfege": "La", "freq_hz": 440.00, "color": [0.5, 0.85, 0.75]},
    {"index": 6, "note": "B4", "midi": 71, "solfege": "Si", "freq_hz": 493.88, "color": [0.6, 0.75, 0.9]},
]


# ---------------------------------------------------------------------------
# Melusina Weapon Stance Manager
# ---------------------------------------------------------------------------

class MelusinaWeaponStanceManager:
    """Manages Melusina's live weapon transformation, real-time archery combat,
    real-time harp playing, and overworld HUD presentation.
    """

    def __init__(self, conductor: Optional[Any] = None):
        self.current_stance: str = WeaponStance.HARP_EXPLORATION
        self.is_transforming: bool = False
        self.transform_start_time: float = 0.0
        self.transformation_duration: float = 0.8  # seconds for transform montage/vfx
        self.transform_cooldown: float = 1.2       # minimum seconds between transform requests
        self.last_transform_time: float = -999.0

        # Archery Combat State
        self.is_aiming: bool = False
        self.is_drawing: bool = False
        self.draw_start_time: float = 0.0
        self.max_draw_duration: float = 1.0        # seconds for 100% tension
        self.draw_tension: float = 0.0
        self.last_loose_time: float = -999.0
        self.last_loose_asset: str = ""
        self.loose_count: int = 0
        self.arrows_fired: List[Dict[str, Any]] = []

        # Real-time Harp Instrument State
        self.plucked_notes_history: List[Dict[str, Any]] = []
        self.active_resonance_score: float = 0.0

        # Jev Conductor Integration
        if conductor is not None:
            self.conductor = conductor
        elif BowConductor is not None:
            self.conductor = BowConductor()
        else:
            self.conductor = None

        self.last_decision: Optional[Any] = None
        self._subscribers: List[Callable[[Dict[str, Any]], None]] = []

    # -----------------------------------------------------------------------
    # Stance & Transformation Control (callable from HUD Switch Button)
    # -----------------------------------------------------------------------

    def toggle_weapon_mode(self, now: Optional[float] = None) -> Dict[str, Any]:
        """Toggles between HARP_EXPLORATION and BOW_COMBAT with validation and cooldown."""
        t = time.time() if now is None else now

        if self.is_transforming:
            remaining = max(0.0, self.transformation_duration - (t - self.transform_start_time))
            return {
                "ok": False,
                "error": "Transformation in progress",
                "remaining_seconds": round(remaining, 2),
                "current_stance": self.current_stance,
            }

        elapsed_since_last = t - self.last_transform_time
        if elapsed_since_last < self.transform_cooldown:
            cooldown_left = round(self.transform_cooldown - elapsed_since_last, 2)
            return {
                "ok": False,
                "error": "Transformation on cooldown",
                "cooldown_remaining": cooldown_left,
                "current_stance": self.current_stance,
            }

        # Target stance
        target_stance = (
            WeaponStance.BOW_COMBAT
            if self.current_stance == WeaponStance.HARP_EXPLORATION
            else WeaponStance.HARP_EXPLORATION
        )

        # Cancel any active combat draw
        self.is_aiming = False
        self.is_drawing = False
        self.draw_tension = 0.0

        # Begin transformation
        self.is_transforming = True
        self.transform_start_time = t
        self.last_transform_time = t
        self.current_stance = target_stance

        event = {
            "ok": True,
            "event": "WeaponTransformationStarted",
            "new_stance": target_stance,
            "duration": self.transformation_duration,
            "active_mesh": MESH_BOW if target_stance == WeaponStance.BOW_COMBAT else MESH_HARP,
            "vfx": VFX_TRANSFORM_BURST,
            "socket": WEAPON_SOCKET_BOW_HELD if target_stance == WeaponStance.BOW_COMBAT else WEAPON_SOCKET_HARP_HELD,
            "timestamp": t,
        }

        self._notify_subscribers(event)
        return event

    def complete_transformation(self, now: Optional[float] = None) -> Dict[str, Any]:
        """Finalizes transformation state when the visual montage / burst completes."""
        t = time.time() if now is None else now
        self.is_transforming = False
        event = {
            "ok": True,
            "event": "WeaponTransformationCompleted",
            "active_stance": self.current_stance,
            "timestamp": t,
        }
        self._notify_subscribers(event)
        return event

    # -----------------------------------------------------------------------
    # Real-Time Archery Combat Actions
    # -----------------------------------------------------------------------

    def start_aim(self, now: Optional[float] = None) -> Dict[str, Any]:
        """Enters over-the-shoulder bow aiming mode."""
        if self.current_stance != WeaponStance.BOW_COMBAT:
            return {"ok": False, "error": "Cannot aim: not in BOW_COMBAT stance"}
        if self.is_transforming:
            return {"ok": False, "error": "Cannot aim while transforming"}

        self.is_aiming = True
        return {
            "ok": True,
            "aiming": True,
            "camera_offset": "OverShoulder_R",
            "reticle": True,
        }

    def stop_aim(self, now: Optional[float] = None) -> Dict[str, Any]:
        """Exits over-the-shoulder bow aiming mode."""
        self.is_aiming = False
        return {"ok": True, "aiming": False, "reticle": False}

    def start_draw(self, now: Optional[float] = None) -> Dict[str, Any]:
        """Begins drawing the bowstring, building tension."""
        t = time.time() if now is None else now
        if self.current_stance != WeaponStance.BOW_COMBAT:
            return {"ok": False, "error": "Cannot draw: not in BOW_COMBAT stance"}
        if self.is_transforming:
            return {"ok": False, "error": "Cannot draw while transforming"}

        self.is_drawing = True
        self.draw_start_time = t
        self.draw_tension = 0.0
        return {
            "ok": True,
            "drawing": True,
            "draw_start_time": t,
        }

    def update_draw(self, now: Optional[float] = None) -> float:
        """Calculates current draw tension from 0.0 to 1.0."""
        if not self.is_drawing:
            self.draw_tension = 0.0
            return 0.0
        t = time.time() if now is None else now
        elapsed = t - self.draw_start_time
        self.draw_tension = min(1.0, elapsed / self.max_draw_duration)
        return self.draw_tension

    def release_arrow(
        self,
        aim_direction: Optional[tuple] = None,
        now: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Releases the drawn bowstring, launching a crystal arrow projectile."""
        t = time.time() if now is None else now
        if self.current_stance != WeaponStance.BOW_COMBAT:
            return {"ok": False, "error": "Cannot fire: not in BOW_COMBAT stance"}
        if not self.is_drawing and self.draw_tension <= 0.05:
            return {"ok": False, "error": "Cannot fire: bow is not drawn"}

        tension = self.update_draw(t) if self.is_drawing else self.draw_tension
        self.is_drawing = False

        # Scale velocity and damage by draw tension
        base_speed = 4500.0  # cm/s in UE
        max_speed = 8500.0
        speed = base_speed + (max_speed - base_speed) * tension

        base_damage = 35.0
        max_damage = 120.0
        damage = base_damage + (max_damage - base_damage) * (tension ** 1.5)

        self.last_loose_time = t
        self.loose_count += 1
        self.draw_tension = 0.0

        arrow_payload = {
            "ok": True,
            "event": "ArrowReleased",
            "index": self.loose_count,
            "tension": round(tension, 3),
            "speed_cms": round(speed, 1),
            "damage": round(damage, 1),
            "spawn_socket": WEAPON_SOCKET_STRING_DRAW,
            "projectile_mesh": MESH_ARROW,
            "vfx_trail": VFX_ARROW_TRAIL,
            "aim_direction": aim_direction or (1.0, 0.0, 0.0),
            "timestamp": t,
        }

        self.arrows_fired.append(arrow_payload)
        self._notify_subscribers(arrow_payload)
        return arrow_payload

    # -----------------------------------------------------------------------
    # Real-Time Harp Exploration & Instrument Playing Actions
    # -----------------------------------------------------------------------

    def pluck_harp_string(
        self,
        string_index: int,
        velocity: float = 1.0,
        now: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Plucks an individual WaveHarp string (0..6) for real-time music and puzzle triggers."""
        t = time.time() if now is None else now
        if self.current_stance != WeaponStance.HARP_EXPLORATION:
            return {"ok": False, "error": "Cannot pluck harp: not in HARP_EXPLORATION stance"}
        if self.is_transforming:
            return {"ok": False, "error": "Cannot pluck while transforming"}

        if not (0 <= string_index < len(HARP_STRINGS)):
            return {"ok": False, "error": f"Invalid string index {string_index}. Must be 0..6"}

        string_info = HARP_STRINGS[string_index]
        velocity = max(0.1, min(1.0, velocity))

        # Resonance calculation (combines recent harmonic rhythm)
        self.active_resonance_score = min(1.0, self.active_resonance_score * 0.9 + 0.25 * velocity)

        note_event = {
            "ok": True,
            "event": "HarpStringPlucked",
            "string_index": string_index,
            "note": string_info["note"],
            "midi_pitch": string_info["midi"],
            "freq_hz": string_info["freq_hz"],
            "solfege": string_info["solfege"],
            "velocity": round(velocity, 2),
            "resonance": round(self.active_resonance_score, 3),
            "socket": WEAPON_SOCKET_HARP_PLUCK,
            "timestamp": t,
        }

        self.plucked_notes_history.append(note_event)
        if len(self.plucked_notes_history) > 32:
            self.plucked_notes_history.pop(0)

        self._notify_subscribers(note_event)
        return note_event

    def play_harp_chord(
        self,
        string_indices: List[int],
        velocity: float = 1.0,
        now: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Plays multiple strings simultaneously to activate harmonic environmental resonances."""
        t = time.time() if now is None else now
        plucks = []
        for idx in string_indices:
            res = self.pluck_harp_string(idx, velocity=velocity, now=t)
            if res.get("ok"):
                plucks.append(res)
        return {
            "ok": True,
            "event": "HarpChordPlayed",
            "plucks": plucks,
            "chord_size": len(plucks),
            "timestamp": t,
        }

    # -----------------------------------------------------------------------
    # Jev Conductor Frame Execution
    # -----------------------------------------------------------------------

    def conduct_frame(
        self,
        telemetry: Optional[dict] = None,
        now: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Executes a single frame of Jev conduction using live telemetry.
        Selects the optimal combat attack asset or evaluates harmonic resonance.
        """
        t = time.time() if now is None else now
        telemetry = telemetry or {}

        if self.conductor is None:
            return {"ok": False, "error": "Jev conductor not available"}

        # Calculate seconds since last loose
        since_last_loose = (
            t - self.last_loose_time if self.last_loose_time > 0.0 else 999.0
        )

        # Normalize movement string ("still", "walk", "run")
        move_val = telemetry.get("movement", telemetry.get("movement_speed", "still"))
        if isinstance(move_val, (int, float)):
            if move_val > 300.0:
                movement_str = "run"
            elif move_val > 10.0:
                movement_str = "walk"
            else:
                movement_str = "still"
        else:
            movement_str = str(move_val)

        state = BowState(
            bpm_intensity=telemetry.get("bpm_intensity", 0.5),
            beat_energy=telemetry.get("beat_energy", 0.5),
            target_distance_m=telemetry.get("target_distance_m", 15.0),
            movement=movement_str,
            resonance=telemetry.get("resonance", self.active_resonance_score),
            wind_strength=telemetry.get("wind_strength", 0.0),
            seconds_since_last_loose=since_last_loose,
            current_bow=self.last_loose_asset or "IDLE_READY",
            provenance="ue-live",
        )

        decision: BowDecision = self.conductor.evaluate(state, now=t)
        self.last_decision = decision

        # In combat mode, if Jev dictates loose=True and we are drawing, fire arrow!
        arrow_fired = None
        if self.current_stance == WeaponStance.BOW_COMBAT and decision.loose and self.is_drawing:
            arrow_fired = self.release_arrow(now=t)

        self.last_loose_asset = decision.bow.choice

        return {
            "ok": True,
            "stance": self.current_stance,
            "decision": {
                "bow_choice": decision.bow.choice,
                "asset_path": ASSET_MAP.get(decision.bow.choice, "") if ASSET_MAP else "",
                "loose": decision.loose,
                "loose_probability": decision.loose_probability,
                "source": decision.source,
            },
            "arrow_fired": arrow_fired,
            "hud_text": format_hud(decision) if format_hud else "",
            "timestamp": t,
        }

    # -----------------------------------------------------------------------
    # Overworld HUD View Data Provider
    # -----------------------------------------------------------------------

    def get_hud_view_data(self, now: Optional[float] = None) -> Dict[str, Any]:
        """Produces the complete data contract required for WBP_Melodia_OverworldHUD.
        Provides button labels, reticle/stave visibility, cooldowns, and conductor telemetry.
        """
        t = time.time() if now is None else now

        elapsed_since_transform = t - self.last_transform_time
        can_switch = (not self.is_transforming) and (elapsed_since_transform >= self.transform_cooldown)
        cooldown_remaining = max(0.0, self.transform_cooldown - elapsed_since_transform)

        is_bow = (self.current_stance == WeaponStance.BOW_COMBAT)

        hud_summary = ""
        conductor_source = "none"
        if self.last_decision:
            conductor_source = self.last_decision.source
            if format_hud:
                hud_summary = format_hud(self.last_decision)

        return {
            "current_stance": self.current_stance,
            "is_bow": is_bow,
            "is_harp": not is_bow,
            "stance_label": "BOW [ARCHERY COMBAT]" if is_bow else "HARP [EXPLORATION]",
            "switch_button_label": "SWITCH TO HARP" if is_bow else "SWITCH TO BOW",
            "switch_button_enabled": can_switch,
            "cooldown_remaining": round(cooldown_remaining, 2) if not can_switch else 0.0,
            "is_transforming": self.is_transforming,
            # Archery Combat HUD elements
            "reticle_visible": is_bow,
            "is_aiming": self.is_aiming,
            "draw_tension": round(self.draw_tension, 3),
            "loose_count": self.loose_count,
            # Harp Instrument HUD elements
            "stave_visible": not is_bow,
            "active_strings_count": len(HARP_STRINGS),
            "recent_notes": [p["note"] for p in self.plucked_notes_history[-5:]],
            "resonance_level": round(self.active_resonance_score, 3),
            # Conductor Telemetry
            "conductor_choice": self.last_decision.bow.choice if self.last_decision else "NONE",
            "conductor_source": conductor_source,
            "conductor_hud_summary": hud_summary,
        }

    # -----------------------------------------------------------------------
    # Observer Pattern
    # -----------------------------------------------------------------------

    def subscribe(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Subscribes a listener (e.g. HUD widget dispatcher) to stance events."""
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def _notify_subscribers(self, event: Dict[str, Any]) -> None:
        for sub in list(self._subscribers):
            try:
                sub(event)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Global Singleton Provider
# ---------------------------------------------------------------------------

_global_stance_manager: Optional[MelusinaWeaponStanceManager] = None


def get_melusina_weapon_manager() -> MelusinaWeaponStanceManager:
    """Returns the singleton MelusinaWeaponStanceManager instance."""
    global _global_stance_manager
    if _global_stance_manager is None:
        _global_stance_manager = MelusinaWeaponStanceManager()
    return _global_stance_manager


def reset_melusina_weapon_manager() -> None:
    """Resets the singleton for clean testing."""
    global _global_stance_manager
    _global_stance_manager = None
