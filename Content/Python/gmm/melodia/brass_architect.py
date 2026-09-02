"""High-level brass architect — builds complete instrument stacks from brass_modifiers."""
from __future__ import annotations

import json
import pathlib

from gmm.geometry.modifiers import GeometryModifier, ModifierStack
from gmm.geometry.brass_modifiers import BRASS_DEFAULTS

_PRESET_DIR = pathlib.Path(__file__).parent / "brass_presets"


def _add(stack: ModifierStack, mid: str, mtype: str, params: dict[str, object]) -> None:
    defaults = BRASS_DEFAULTS.get(mtype, {})
    merged = {**defaults, **params}
    stack.add(GeometryModifier(modifier_id=mid, modifier_type=mtype, parameters=merged))


def build_trumpet_bb(key: str = "C", ensemble: str = "vintage") -> ModifierStack:
    """Bb trumpet: tube + bell + 3 valves + mouthpiece."""
    stack = ModifierStack(target="SM_BrassTrumpet")
    _add(stack, "body_tube", "brass_tube", {"radius": 12.5, "thickness": 1.2, "length": 350.0, "resolution": 32})
    _add(stack, "bell_mouth", "brass_bell_profile", {"base_radius": 12.5, "tip_radius": 28.0, "height": 35.0, "resolution": 64, "flare_exponent": 1.5, "flare_angle_deg": 10.0})
    for i in range(1, 4):
        _add(stack, f"valve_{i}_cylinder", "brass_valve_cylinder", {"radius": 14.0, "piston_diameter": 12.0, "port_width": 3.0, "stroke": 40.0, "port_count": 3, "fillet_radius": 0.5})
    _add(stack, "mouthpiece_cup", "brass_mouthpiece_cup", {"cup_depth": 22.0, "cup_radius": 12.0, "rim_thickness": 5.0, "back_bore_diameter": 5.15})
    _add(stack, "mouthpiece_shank", "brass_mouthpiece_shank", {"shank_length": 45.0, "major_diameter": 12.0, "minor_diameter": 8.0, "taper_type": "linear"})
    return stack


def build_trombone_bb(key: str = "Bb", ensemble: str = "modern") -> ModifierStack:
    stack = ModifierStack(target="SM_BrassTrombone")
    _add(stack, "main_tube", "brass_tube", {"radius": 13.0, "thickness": 1.5, "length": 380.0, "resolution": 32})
    _add(stack, "bell_mouth", "brass_bell_profile", {"base_radius": 13.0, "tip_radius": 32.0, "height": 40.0, "resolution": 64, "flare_exponent": 1.5, "flare_angle_deg": 10.0})
    for i in range(1, 4):
        _add(stack, f"slide_{i}_taper", "brass_slide_taper", {"major_diameter": 28.0, "minor_diameter": 25.0, "length": 250.0, "resolution": 32, "grease_groove_width": 1.0})
    _add(stack, "bracing_hoop_1", "brass_bracing_hoop", {"tube_radius": 13.0, "hoop_diameter": 15.0, "count": 6, "angle_offset": 0.0, "weld_bead_radius": 1.0})
    _add(stack, "mouthpiece_cup", "brass_mouthpiece_cup", {"cup_depth": 25.0, "cup_radius": 13.0, "rim_thickness": 6.0, "back_bore_diameter": 5.5})
    _add(stack, "mouthpiece_shank", "brass_mouthpiece_shank", {"shank_length": 50.0, "major_diameter": 13.0, "minor_diameter": 9.0, "taper_type": "parabolic"})
    return stack


def build_french_horn_f(key: str = "F", ensemble: str = "double") -> ModifierStack:
    stack = ModifierStack(target="SM_BrassFrenchHorn")
    _add(stack, "main_tube", "brass_tube", {"radius": 8.0, "thickness": 1.0, "length": 420.0, "resolution": 32})
    _add(stack, "bell_mouth", "brass_bell_profile", {"base_radius": 8.0, "tip_radius": 18.0, "height": 45.0, "resolution": 64, "flare_exponent": 1.5, "flare_angle_deg": 10.0})
    for i in range(1, 4):
        _add(stack, f"rotary_{i}_cylinder", "brass_valve_cylinder", {"radius": 10.0, "piston_diameter": 8.5, "port_width": 2.5, "stroke": 50.0, "port_count": 3, "fillet_radius": 0.4})
    _add(stack, "bracing_hoop_1", "brass_bracing_hoop", {"tube_radius": 8.0, "hoop_diameter": 12.0, "count": 8, "angle_offset": 22.5, "weld_bead_radius": 0.8})
    _add(stack, "mouthpiece_cup", "brass_mouthpiece_cup", {"cup_depth": 20.0, "cup_radius": 9.0, "rim_thickness": 4.0, "back_bore_diameter": 4.75})
    return stack


def build_tuba_cc(key: str = "C", valve_config: str = "4") -> ModifierStack:
    n_valves = int(valve_config) if valve_config.isdigit() else 4
    stack = ModifierStack(target="SM_BrassTuba")
    _add(stack, "main_tube", "brass_tube", {"radius": 16.0, "thickness": 2.0, "length": 500.0, "resolution": 48})
    _add(stack, "bell_mouth", "brass_bell_profile", {"base_radius": 16.0, "tip_radius": 40.0, "height": 50.0, "resolution": 64, "flare_exponent": 1.5, "flare_angle_deg": 10.0})
    for i in range(1, n_valves + 1):
        _add(stack, f"valve_{i}_cylinder", "brass_valve_cylinder", {"radius": 18.0, "piston_diameter": 15.0, "port_width": 4.0, "stroke": 60.0, "port_count": 3, "fillet_radius": 0.6})
    _add(stack, "wrap_formation", "brass_wrap_formation", {"coil_diameter": 30.0, "wire_diameter": 8.0, "wrap_count": 6, "start_angle": 0.0, "pitch": 25.0})
    _add(stack, "bracing_hoop_1", "brass_bracing_hoop", {"tube_radius": 16.0, "hoop_diameter": 20.0, "count": 8, "angle_offset": 0.0, "weld_bead_radius": 1.5})
    _add(stack, "mouthpiece_cup", "brass_mouthpiece_cup", {"cup_depth": 30.0, "cup_radius": 16.0, "rim_thickness": 7.0, "back_bore_diameter": 6.5})
    return stack


def load_preset(filename: str) -> ModifierStack:
    """Load a JSON preset file into a ModifierStack."""
    path = _PRESET_DIR / filename
    if not path.exists():
        # Try plugins dir
        alt = pathlib.Path("Plugins/ProceduralModelingToolkit/Content/Presets") / filename
        if alt.exists():
            path = alt
        else:
            raise FileNotFoundError(f"preset not found: {filename} (searched {_PRESET_DIR} and {alt})")
    data = json.loads(path.read_text(encoding="utf-8"))
    target = data.get("ue_binding", f"SM_{data.get('instrument_type', 'Brass')}")
    stack = ModifierStack(target=target)
    for entry in data.get("modifier_stacks", []):
        stack.add(GeometryModifier(
            modifier_id=entry["id"],
            modifier_type=entry["type"],
            enabled=entry.get("enabled", True),
            scope=entry.get("scope", "editor"),
            backend=entry.get("backend", "auto"),
            parameters=dict(entry.get("parameters", {})),
        ))
    return stack


def list_presets() -> list[str]:
    if not _PRESET_DIR.exists():
        return []
    return sorted(p.name for p in _PRESET_DIR.glob("*.json"))
