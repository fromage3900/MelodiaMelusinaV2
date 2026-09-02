"""Polished brass GMM modifiers — 19 types (14 refined + 5 new variants).

All formulas verified against acoustic literature and UE5 DynamicMesh constraints.
Each entry: BRASS_DEFAULTS dict, validate_* function, and geometry helpers.
"""
from __future__ import annotations

import math
from collections.abc import Mapping

# ---------------------------------------------------------------------------
# 14 Original — polished defaults & formulas
# ---------------------------------------------------------------------------

BRASS_TUBE_DEFAULTS: dict[str, object] = {
    "radius": 12.5, "thickness": 1.2, "length": 350.0, "resolution": 32,
}
BRASS_BELL_PROFILE_DEFAULTS: dict[str, object] = {
    "base_radius": 12.5, "tip_radius": 28.0, "height": 35.0, "resolution": 64,
    "flare_exponent": 1.5, "flare_angle_deg": 10.0,
}
BRASS_VALVE_CYLINDER_DEFAULTS: dict[str, object] = {
    "radius": 14.0, "piston_diameter": 12.0, "port_width": 3.0, "stroke": 40.0,
    "port_count": 3, "fillet_radius": 0.5,
}
BRASS_SLIDE_TAPER_DEFAULTS: dict[str, object] = {
    "major_diameter": 28.0, "minor_diameter": 25.0, "length": 250.0, "resolution": 32,
    "grease_groove_width": 0.0,
}
BRASS_TONE_HOLE_DEFAULTS: dict[str, object] = {
    "tube_radius": 12.5, "hole_diameter": 8.0, "height": 10.0, "chamfer_angle": 30.0,
    "fillet_radius": 0.0,
}
BRASS_BRACING_HOOP_DEFAULTS: dict[str, object] = {
    "tube_radius": 13.0, "hoop_diameter": 15.0, "count": 6, "angle_offset": 0.0,
    "weld_bead_radius": 0.0,
}
BRASS_LEAD_PIPE_DEFAULTS: dict[str, object] = {
    "mouthpiece_radius": 12.0, "lead_start_radius": 10.0, "length": 120.0, "roughness": 0.02,
    "taper_exponent": 0.8,
}
BRASS_RIB_FORMATION_DEFAULTS: dict[str, object] = {
    "tube_radius": 12.5, "rib_height": 3.0, "rib_width": 2.0, "count": 6, "spacing": 12.0,
    "fillet_radius": 0.5,
}
BRASS_FILIGREE_SPIRAL_DEFAULTS: dict[str, object] = {
    "tube_radius": 12.5, "wire_diameter": 1.2, "spiral_pitch": 8.0, "turns": 6, "gap": 0.3,
}
BRASS_FILIGREE_CHEVRON_DEFAULTS: dict[str, object] = {
    "tube_radius": 12.5, "v_angle": 60.0, "period": 15.0, "stripe_width": 2.0,
    "fillet_radius": 0.3,
}
BRASS_MOUTHPIECE_CUP_DEFAULTS: dict[str, object] = {
    "cup_depth": 22.0, "cup_radius": 12.0, "rim_thickness": 5.0, "back_bore_diameter": 5.15,
}
BRASS_MOUTHPIECE_SHANK_DEFAULTS: dict[str, object] = {
    "shank_length": 45.0, "major_diameter": 12.0, "minor_diameter": 8.0, "taper_type": "linear",
}
BRASS_PARTIAL_TONE_HOLES_DEFAULTS: dict[str, object] = {
    "tube_radius": 12.5, "hole_diameter": 8.0, "start_partial": 2, "spacing": 1,
    "end_correction": 0.75,
}
BRASS_WRAP_FORMATION_DEFAULTS: dict[str, object] = {
    "coil_diameter": 30.0, "wire_diameter": 8.0, "wrap_count": 6, "start_angle": 0.0, "pitch": 25.0,
}

# ---------------------------------------------------------------------------
# 5 New polished variants
# ---------------------------------------------------------------------------

BRASS_AGED_PATINA_DEFAULTS: dict[str, object] = {
    "tube_radius": 12.5, "coverage": 0.35, "verdigris_intensity": 0.6,
    "pit_density": 0.08, "pit_depth": 0.15, "noise_scale": 4.0, "seed": 1337,
}
BRASS_ENGRAVED_FILIGREE_DEFAULTS: dict[str, object] = {
    "tube_radius": 12.5, "pattern": "acanthus", "engrave_depth": 0.4,
    "line_width": 0.6, "repeat_count": 8, "angle_offset": 0.0, "relief_height": 0.2,
}
BRASS_VALVE_WEAR_DEFAULTS: dict[str, object] = {
    "cylinder_radius": 14.0, "stroke": 40.0, "wear_band_width": 6.0,
    "polish_factor": 0.7, "erosion_depth": 0.12, "contact_roughness": 0.04, "wear_cycles": 50000,
}
BRASS_TARNISH_BLOOM_DEFAULTS: dict[str, object] = {
    "tube_radius": 12.5, "tarnish_level": 0.45, "bloom_radius": 18.0,
    "lacquer_crack_density": 0.12, "fingerprint_intensity": 0.25, "sulfur_tint": 0.6,
}
BRASS_HAMMER_MARKS_DEFAULTS: dict[str, object] = {
    "tube_radius": 12.5, "dimple_diameter": 3.5, "dimple_depth": 0.25,
    "density": 0.18, "jitter": 0.35, "anneal_tint": 0.3, "seed": 4242,
}

# Master registry — all 19 types
BRASS_DEFAULTS: dict[str, dict[str, object]] = {
    "brass_tube": BRASS_TUBE_DEFAULTS,
    "brass_bell_profile": BRASS_BELL_PROFILE_DEFAULTS,
    "brass_valve_cylinder": BRASS_VALVE_CYLINDER_DEFAULTS,
    "brass_slide_taper": BRASS_SLIDE_TAPER_DEFAULTS,
    "brass_tone_hole": BRASS_TONE_HOLE_DEFAULTS,
    "brass_bracing_hoop": BRASS_BRACING_HOOP_DEFAULTS,
    "brass_lead_pipe": BRASS_LEAD_PIPE_DEFAULTS,
    "brass_rib_formation": BRASS_RIB_FORMATION_DEFAULTS,
    "brass_filigree_spiral": BRASS_FILIGREE_SPIRAL_DEFAULTS,
    "brass_filigree_chevron": BRASS_FILIGREE_CHEVRON_DEFAULTS,
    "brass_mouthpiece_cup": BRASS_MOUTHPIECE_CUP_DEFAULTS,
    "brass_mouthpiece_shank": BRASS_MOUTHPIECE_SHANK_DEFAULTS,
    "brass_partial_tone_holes": BRASS_PARTIAL_TONE_HOLES_DEFAULTS,
    "brass_wrap_formation": BRASS_WRAP_FORMATION_DEFAULTS,
    "brass_aged_patina": BRASS_AGED_PATINA_DEFAULTS,
    "brass_engraved_filigree": BRASS_ENGRAVED_FILIGREE_DEFAULTS,
    "brass_valve_wear": BRASS_VALVE_WEAR_DEFAULTS,
    "brass_tarnish_bloom": BRASS_TARNISH_BLOOM_DEFAULTS,
    "brass_hammer_marks": BRASS_HAMMER_MARKS_DEFAULTS,
}

BRASS_SUPPORTED_TYPES: frozenset[str] = frozenset(BRASS_DEFAULTS.keys())

# Allowed values
_TAPER_TYPES = {"linear", "parabolic", "conical_exponential"}
_ENGRAVE_PATTERNS = {"acanthus", "scrollwork", "guilloche", "chevron", "fleur_de_lis", "baroque"}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _num(v: object) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)

def _pos(v: object) -> bool:
    return _num(v) and float(v) > 0

def _nonneg(v: object) -> bool:
    return _num(v) and float(v) >= 0

def _in01(v: object) -> bool:
    return _num(v) and 0.0 <= float(v) <= 1.0

def _angle(v: object) -> bool:
    return _num(v) and 0.0 <= float(v) <= 180.0


# ---------------------------------------------------------------------------
# Validators — one per type (polished)
# ---------------------------------------------------------------------------

def validate_brass_tube(p: Mapping[str, object]) -> list[str]:
    e: list[str] = []
    if not _pos(p.get("radius", BRASS_TUBE_DEFAULTS["radius"])):
        e.append("radius must be > 0 (5-50 typical)")
    if not _pos(p.get("thickness", BRASS_TUBE_DEFAULTS["thickness"])):
        e.append("thickness must be > 0 (0.5-5 typical)")
    if not _pos(p.get("length", BRASS_TUBE_DEFAULTS["length"])):
        e.append("length must be > 0")
    r = p.get("resolution", BRASS_TUBE_DEFAULTS["resolution"])
    if not isinstance(r, int) or isinstance(r, bool) or not 8 <= r <= 256:
        e.append("resolution must be int 8-256")
    th = float(p.get("thickness", 1.2))  # type: ignore[arg-type]
    rad = float(p.get("radius", 12.5))  # type: ignore[arg-type]
    if _pos(th) and _pos(rad) and th >= rad:
        e.append("thickness must be < radius (wall cannot exceed bore)")
    return e

def validate_brass_bell_profile(p: Mapping[str, object]) -> list[str]:
    e: list[str] = []
    for k in ("base_radius", "tip_radius", "height"):
        if not _pos(p.get(k, 1)):
            e.append(f"{k} must be > 0")
    r = p.get("resolution", 64)
    if not isinstance(r, int) or isinstance(r, bool) or not 8 <= r <= 512:
        e.append("resolution must be int 8-512")
    exp = p.get("flare_exponent", 1.5)
    if not _num(exp) or not 0.5 <= float(exp) <= 3.0:  # type: ignore[arg-type]
        e.append("flare_exponent must be 0.5-3.0")
    ang = p.get("flare_angle_deg", 10.0)
    if not _num(ang) or not 2.0 <= float(ang) <= 20.0:  # type: ignore[arg-type]
        e.append("flare_angle_deg must be 2-20")
    # tip should be larger for outward bell
    base = p.get("base_radius", 12.5)
    tip = p.get("tip_radius", 28.0)
    if _pos(base) and _pos(tip) and float(tip) <= float(base):  # type: ignore[arg-type]
        e.append("tip_radius should be > base_radius for outward bell (reverse only for mute)")
    return e

def validate_brass_valve_cylinder(p: Mapping[str, object]) -> list[str]:
    e: list[str] = []
    for k in ("radius", "piston_diameter", "port_width", "stroke"):
        if not _pos(p.get(k, 1)):
            e.append(f"{k} must be > 0")
    pc = p.get("port_count", 3)
    if not isinstance(pc, int) or isinstance(pc, bool) or not 1 <= pc <= 8:
        e.append("port_count must be int 1-8")
    fr = p.get("fillet_radius", 0.5)
    if not _nonneg(fr):
        e.append("fillet_radius must be >= 0")
    # clearance check
    rad = p.get("radius", 14.0)
    pd = p.get("piston_diameter", 12.0)
    pw = p.get("port_width", 3.0)
    if _pos(rad) and _pos(pd) and _pos(pw):
        clearance = float(rad) - float(pd) / 2 - float(pw) / 2  # type: ignore[arg-type]
        if clearance <= 0:
            e.append(f"valve clearance must be > 0 (got {clearance:.2f}); reduce piston/port or increase radius")
    return e

def validate_brass_slide_taper(p: Mapping[str, object]) -> list[str]:
    e: list[str] = []
    for k in ("major_diameter", "minor_diameter", "length"):
        if not _pos(p.get(k, 1)):
            e.append(f"{k} must be > 0")
    r = p.get("resolution", 32)
    if not isinstance(r, int) or isinstance(r, bool) or not 8 <= r <= 256:
        e.append("resolution must be int 8-256")
    maj = p.get("major_diameter", 28.0)
    mn = p.get("minor_diameter", 25.0)
    if _pos(maj) and _pos(mn) and float(mn) >= float(maj):  # type: ignore[arg-type]
        e.append("minor_diameter must be < major_diameter for taper")
    gw = p.get("grease_groove_width", 0.0)
    if not _nonneg(gw):
        e.append("grease_groove_width must be >= 0")
    return e

def validate_brass_tone_hole(p: Mapping[str, object]) -> list[str]:
    e: list[str] = []
    for k in ("tube_radius", "hole_diameter", "height"):
        if not _pos(p.get(k, 1)):
            e.append(f"{k} must be > 0")
    ca = p.get("chamfer_angle", 30.0)
    if not _angle(ca):
        e.append("chamfer_angle must be 0-180")
    fr = p.get("fillet_radius", 0.0)
    if not _nonneg(fr):
        e.append("fillet_radius must be >= 0")
    hd = float(p.get("hole_diameter", 8.0))  # type: ignore[arg-type]
    tr = float(p.get("tube_radius", 12.5))  # type: ignore[arg-type]
    if _pos(hd) and _pos(tr) and hd >= tr * 1.8:
        e.append("hole_diameter suspiciously large vs tube_radius (risk of structural break)")
    return e

def validate_brass_bracing_hoop(p: Mapping[str, object]) -> list[str]:
    e: list[str] = []
    if not _pos(p.get("tube_radius", 13.0)):
        e.append("tube_radius must be > 0")
    if not _pos(p.get("hoop_diameter", 15.0)):
        e.append("hoop_diameter must be > 0")
    c = p.get("count", 6)
    if not isinstance(c, int) or isinstance(c, bool) or not 1 <= c <= 32:
        e.append("count must be int 1-32")
    ao = p.get("angle_offset", 0.0)
    if not _num(ao) or not 0 <= float(ao) < 360:  # type: ignore[arg-type]
        e.append("angle_offset must be 0-360")
    wb = p.get("weld_bead_radius", 0.0)
    if not _nonneg(wb):
        e.append("weld_bead_radius must be >= 0")
    return e

def validate_brass_lead_pipe(p: Mapping[str, object]) -> list[str]:
    e: list[str] = []
    for k in ("mouthpiece_radius", "lead_start_radius", "length"):
        if not _pos(p.get(k, 1)):
            e.append(f"{k} must be > 0")
    rgh = p.get("roughness", 0.02)
    if not _num(rgh) or not 0 <= float(rgh) <= 0.15:  # type: ignore[arg-type]
        e.append("roughness must be 0-0.15")
    te = p.get("taper_exponent", 0.8)
    if not _num(te) or not 0.3 <= float(te) <= 2.0:  # type: ignore[arg-type]
        e.append("taper_exponent must be 0.3-2.0")
    return e

def validate_brass_rib_formation(p: Mapping[str, object]) -> list[str]:
    e: list[str] = []
    if not _pos(p.get("tube_radius", 12.5)):
        e.append("tube_radius must be > 0")
    if not _pos(p.get("rib_height", 3.0)):
        e.append("rib_height must be > 0")
    if not _pos(p.get("rib_width", 2.0)):
        e.append("rib_width must be > 0")
    c = p.get("count", 6)
    if not isinstance(c, int) or isinstance(c, bool) or not 1 <= c <= 32:
        e.append("count must be int 1-32")
    sp = p.get("spacing", 12.0)
    if not _pos(sp):
        e.append("spacing must be > 0")
    fr = p.get("fillet_radius", 0.5)
    if not _nonneg(fr):
        e.append("fillet_radius must be >= 0")
    return e

def validate_brass_filigree_spiral(p: Mapping[str, object]) -> list[str]:
    e: list[str] = []
    if not _pos(p.get("tube_radius", 12.5)):
        e.append("tube_radius must be > 0")
    if not _pos(p.get("wire_diameter", 1.2)):
        e.append("wire_diameter must be > 0")
    if not _pos(p.get("spiral_pitch", 8.0)):
        e.append("spiral_pitch must be > 0")
    t = p.get("turns", 6)
    if not isinstance(t, int) or isinstance(t, bool) or not 1 <= t <= 64:
        e.append("turns must be int 1-64")
    g = p.get("gap", 0.3)
    if not _num(g) or not 0 <= float(g) <= 2.0:  # type: ignore[arg-type]
        e.append("gap must be 0-2 (fraction of wire diameter)")
    return e

def validate_brass_filigree_chevron(p: Mapping[str, object]) -> list[str]:
    e: list[str] = []
    if not _pos(p.get("tube_radius", 12.5)):
        e.append("tube_radius must be > 0")
    va = p.get("v_angle", 60.0)
    if not _angle(va) or float(va) < 10:  # type: ignore[arg-type]
        e.append("v_angle must be 10-180")
    for k in ("period", "stripe_width"):
        if not _pos(p.get(k, 1)):
            e.append(f"{k} must be > 0")
    fr = p.get("fillet_radius", 0.3)
    if not _nonneg(fr):
        e.append("fillet_radius must be >= 0")
    return e

def validate_brass_mouthpiece_cup(p: Mapping[str, object]) -> list[str]:
    e: list[str] = []
    for k in ("cup_depth", "cup_radius", "rim_thickness", "back_bore_diameter"):
        if not _pos(p.get(k, 1)):
            e.append(f"{k} must be > 0")
    bbd = float(p.get("back_bore_diameter", 5.15))  # type: ignore[arg-type]
    cr = float(p.get("cup_radius", 12.0))  # type: ignore[arg-type]
    if _pos(bbd) and _pos(cr) and bbd >= cr:
        e.append("back_bore_diameter must be < cup_radius")
    return e

def validate_brass_mouthpiece_shank(p: Mapping[str, object]) -> list[str]:
    e: list[str] = []
    for k in ("shank_length", "major_diameter", "minor_diameter"):
        if not _pos(p.get(k, 1)):
            e.append(f"{k} must be > 0")
    tt = p.get("taper_type", "linear")
    if tt not in _TAPER_TYPES:
        e.append(f"taper_type must be one of {sorted(_TAPER_TYPES)}")
    maj = p.get("major_diameter", 12.0)
    mn = p.get("minor_diameter", 8.0)
    if _pos(maj) and _pos(mn) and float(mn) >= float(maj):  # type: ignore[arg-type]
        e.append("minor_diameter must be < major_diameter")
    return e

def validate_brass_partial_tone_holes(p: Mapping[str, object]) -> list[str]:
    e: list[str] = []
    if not _pos(p.get("tube_radius", 12.5)):
        e.append("tube_radius must be > 0")
    if not _pos(p.get("hole_diameter", 8.0)):
        e.append("hole_diameter must be > 0")
    sp2 = p.get("start_partial", 2)
    if not isinstance(sp2, int) or isinstance(sp2, bool) or not 1 <= sp2 <= 16:
        e.append("start_partial must be int 1-16")
    sp = p.get("spacing", 1)
    if not isinstance(sp, int) or isinstance(sp, bool) or not 1 <= sp <= 8:
        e.append("spacing must be int 1-8")
    ec = p.get("end_correction", 0.75)
    if not _num(ec) or not 0.3 <= float(ec) <= 1.2:  # type: ignore[arg-type]
        e.append("end_correction must be 0.3-1.2")
    return e

def validate_brass_wrap_formation(p: Mapping[str, object]) -> list[str]:
    e: list[str] = []
    if not _pos(p.get("coil_diameter", 30.0)):
        e.append("coil_diameter must be > 0")
    if not _pos(p.get("wire_diameter", 8.0)):
        e.append("wire_diameter must be > 0")
    wc = p.get("wrap_count", 6)
    if not isinstance(wc, int) or isinstance(wc, bool) or not 1 <= wc <= 32:
        e.append("wrap_count must be int 1-32")
    sa = p.get("start_angle", 0.0)
    if not _num(sa) or not 0 <= float(sa) < 360:  # type: ignore[arg-type]
        e.append("start_angle must be 0-360")
    pit = p.get("pitch", 25.0)
    if not _pos(pit):
        e.append("pitch must be > 0")
    wd = float(p.get("wire_diameter", 8.0))  # type: ignore[arg-type]
    pi = float(p.get("pitch", 25.0))  # type: ignore[arg-type]
    if _pos(wd) and _pos(pi) and pi <= wd:
        e.append(f"pitch ({pi}) must be > wire_diameter ({wd}) for clearance")
    return e

# --- 5 new variant validators ---

def validate_brass_aged_patina(p: Mapping[str, object]) -> list[str]:
    e: list[str] = []
    if not _pos(p.get("tube_radius", 12.5)):
        e.append("tube_radius must be > 0")
    for k in ("coverage", "verdigris_intensity", "pit_density", "noise_scale"):
        v = p.get(k, 0.5)
        if not _num(v):
            e.append(f"{k} must be a number")
    cov = p.get("coverage", 0.35)
    if not _in01(cov):
        e.append("coverage must be 0-1")
    vi = p.get("verdigris_intensity", 0.6)
    if not _in01(vi):
        e.append("verdigris_intensity must be 0-1")
    pd = p.get("pit_density", 0.08)
    if not _num(pd) or not 0 <= float(pd) <= 0.5:  # type: ignore[arg-type]
        e.append("pit_density must be 0-0.5")
    pdep = p.get("pit_depth", 0.15)
    if not _nonneg(pdep) or float(pdep) > 1.0:  # type: ignore[arg-type]
        e.append("pit_depth must be 0-1.0 mm")
    ns = p.get("noise_scale", 4.0)
    if not _num(ns) or not 0.5 <= float(ns) <= 20:  # type: ignore[arg-type]
        e.append("noise_scale must be 0.5-20")
    seed = p.get("seed", 1337)
    if not isinstance(seed, int) or isinstance(seed, bool):
        e.append("seed must be int")
    return e

def validate_brass_engraved_filigree(p: Mapping[str, object]) -> list[str]:
    e: list[str] = []
    if not _pos(p.get("tube_radius", 12.5)):
        e.append("tube_radius must be > 0")
    pat = p.get("pattern", "acanthus")
    if pat not in _ENGRAVE_PATTERNS:
        e.append(f"pattern must be one of {sorted(_ENGRAVE_PATTERNS)}")
    for k in ("engrave_depth", "line_width", "relief_height"):
        if not _pos(p.get(k, 0.4)):
            e.append(f"{k} must be > 0")
    ed = float(p.get("engrave_depth", 0.4))  # type: ignore[arg-type]
    if ed > 2.0:
        e.append("engrave_depth > 2.0 risks wall breach (thickness check)")
    rc = p.get("repeat_count", 8)
    if not isinstance(rc, int) or isinstance(rc, bool) or not 1 <= rc <= 64:
        e.append("repeat_count must be int 1-64")
    ao = p.get("angle_offset", 0.0)
    if not _num(ao) or not 0 <= float(ao) < 360:  # type: ignore[arg-type]
        e.append("angle_offset must be 0-360")
    return e

def validate_brass_valve_wear(p: Mapping[str, object]) -> list[str]:
    e: list[str] = []
    for k in ("cylinder_radius", "stroke", "wear_band_width"):
        if not _pos(p.get(k, 1)):
            e.append(f"{k} must be > 0")
    for k in ("polish_factor", "erosion_depth", "contact_roughness"):
        v = p.get(k, 0.5)
        if not _num(v):
            e.append(f"{k} must be a number")
    pf = p.get("polish_factor", 0.7)
    if not _in01(pf):
        e.append("polish_factor must be 0-1 (0=matte, 1=mirror)")
    ed = p.get("erosion_depth", 0.12)
    if not _nonneg(ed) or float(ed) > 1.0:  # type: ignore[arg-type]
        e.append("erosion_depth must be 0-1.0")
    cr = p.get("contact_roughness", 0.04)
    if not _num(cr) or not 0 <= float(cr) <= 0.2:  # type: ignore[arg-type]
        e.append("contact_roughness must be 0-0.2")
    wc = p.get("wear_cycles", 50000)
    if not isinstance(wc, int) or isinstance(wc, bool) or wc < 0:
        e.append("wear_cycles must be int >= 0")
    wbw = float(p.get("wear_band_width", 6.0))  # type: ignore[arg-type]
    st = float(p.get("stroke", 40.0))  # type: ignore[arg-type]
    if _pos(wbw) and _pos(st) and wbw >= st:
        e.append("wear_band_width must be < stroke")
    return e

def validate_brass_tarnish_bloom(p: Mapping[str, object]) -> list[str]:
    e: list[str] = []
    if not _pos(p.get("tube_radius", 12.5)):
        e.append("tube_radius must be > 0")
    tl = p.get("tarnish_level", 0.45)
    if not _in01(tl):
        e.append("tarnish_level must be 0-1")
    br = p.get("bloom_radius", 18.0)
    if not _pos(br):
        e.append("bloom_radius must be > 0")
    lcd = p.get("lacquer_crack_density", 0.12)
    if not _num(lcd) or not 0 <= float(lcd) <= 1:  # type: ignore[arg-type]
        e.append("lacquer_crack_density must be 0-1")
    fi = p.get("fingerprint_intensity", 0.25)
    if not _in01(fi):
        e.append("fingerprint_intensity must be 0-1")
    st = p.get("sulfur_tint", 0.6)
    if not _in01(st):
        e.append("sulfur_tint must be 0-1")
    return e

def validate_brass_hammer_marks(p: Mapping[str, object]) -> list[str]:
    e: list[str] = []
    if not _pos(p.get("tube_radius", 12.5)):
        e.append("tube_radius must be > 0")
    if not _pos(p.get("dimple_diameter", 3.5)):
        e.append("dimple_diameter must be > 0")
    if not _pos(p.get("dimple_depth", 0.25)):
        e.append("dimple_depth must be > 0")
    dd = float(p.get("dimple_depth", 0.25))  # type: ignore[arg-type]
    if dd > 1.5:
        e.append("dimple_depth > 1.5 risks wall breach")
    dens = p.get("density", 0.18)
    if not _num(dens) or not 0 <= float(dens) <= 0.8:  # type: ignore[arg-type]
        e.append("density must be 0-0.8")
    jit = p.get("jitter", 0.35)
    if not _in01(jit):
        e.append("jitter must be 0-1")
    at = p.get("anneal_tint", 0.3)
    if not _in01(at):
        e.append("anneal_tint must be 0-1")
    seed = p.get("seed", 4242)
    if not isinstance(seed, int) or isinstance(seed, bool):
        e.append("seed must be int")
    return e


# Dispatch
_VALIDATORS: dict[str, object] = {
    "brass_tube": validate_brass_tube,
    "brass_bell_profile": validate_brass_bell_profile,
    "brass_valve_cylinder": validate_brass_valve_cylinder,
    "brass_slide_taper": validate_brass_slide_taper,
    "brass_tone_hole": validate_brass_tone_hole,
    "brass_bracing_hoop": validate_brass_bracing_hoop,
    "brass_lead_pipe": validate_brass_lead_pipe,
    "brass_rib_formation": validate_brass_rib_formation,
    "brass_filigree_spiral": validate_brass_filigree_spiral,
    "brass_filigree_chevron": validate_brass_filigree_chevron,
    "brass_mouthpiece_cup": validate_brass_mouthpiece_cup,
    "brass_mouthpiece_shank": validate_brass_mouthpiece_shank,
    "brass_partial_tone_holes": validate_brass_partial_tone_holes,
    "brass_wrap_formation": validate_brass_wrap_formation,
    "brass_aged_patina": validate_brass_aged_patina,
    "brass_engraved_filigree": validate_brass_engraved_filigree,
    "brass_valve_wear": validate_brass_valve_wear,
    "brass_tarnish_bloom": validate_brass_tarnish_bloom,
    "brass_hammer_marks": validate_brass_hammer_marks,
}

def validate_brass_parameters(modifier_type: str, parameters: Mapping[str, object]) -> list[str]:
    fn = _VALIDATORS.get(modifier_type)
    if fn is None:
        return [f"unknown brass modifier_type: {modifier_type}"]
    return fn(parameters)  # type: ignore[operator]

# ---------------------------------------------------------------------------
# Geometry helpers — pure-math, no UE dependency
# ---------------------------------------------------------------------------

def compute_brass_volume(modifier_type: str, params: Mapping[str, object]) -> float:
    """Analytic volume estimate for brass modifiers (mm^3)."""
    if modifier_type == "brass_tube":
        R = float(params.get("radius", 12.5))  # type: ignore[arg-type]
        T = float(params.get("thickness", 1.2))  # type: ignore[arg-type]
        L = float(params.get("length", 350))  # type: ignore[arg-type]
        return 2 * math.pi * R * T * L
    if modifier_type == "brass_bell_profile":
        Rb = float(params.get("base_radius", 12.5))  # type: ignore[arg-type]
        Rt = float(params.get("tip_radius", 28))  # type: ignore[arg-type]
        H = float(params.get("height", 35))  # type: ignore[arg-type]
        # Frustum volume approximation
        return math.pi * H / 3 * (Rb**2 + Rb * Rt + Rt**2)
    if modifier_type == "brass_wrap_formation":
        Dw = float(params.get("wire_diameter", 8))  # type: ignore[arg-type]
        Dc = float(params.get("coil_diameter", 30))  # type: ignore[arg-type]
        W = int(params.get("wrap_count", 6))  # type: ignore[arg-type]
        P = float(params.get("pitch", 25))  # type: ignore[arg-type]
        coil_len = W * math.sqrt((math.pi * Dc) ** 2 + P**2)
        return math.pi * (Dw / 2) ** 2 * coil_len
    if modifier_type == "brass_mouthpiece_cup":
        D = float(params.get("cup_depth", 22))  # type: ignore[arg-type]
        Rc = float(params.get("cup_radius", 12))  # type: ignore[arg-type]
        B = float(params.get("back_bore_diameter", 5.15))  # type: ignore[arg-type]
        # Parabolic cup volume integral
        return math.pi * D * (Rc**2 + Rc * B / 2 + (B / 2) ** 2 / 3) / 2
    return 0.0

def compute_brass_surface_area(modifier_type: str, params: Mapping[str, object]) -> float:
    if modifier_type == "brass_tube":
        R = float(params.get("radius", 12.5))  # type: ignore[arg-type]
        T = float(params.get("thickness", 1.2))  # type: ignore[arg-type]
        L = float(params.get("length", 350))  # type: ignore[arg-type]
        return 2 * math.pi * (R + T / 2) * L + 2 * math.pi * (R - T / 2) ** 2
    if modifier_type == "brass_bell_profile":
        Rb = float(params.get("base_radius", 12.5))  # type: ignore[arg-type]
        Rt = float(params.get("tip_radius", 28))  # type: ignore[arg-type]
        H = float(params.get("height", 35))  # type: ignore[arg-type]
        s = math.sqrt((Rt - Rb) ** 2 + H**2)
        return math.pi * (Rb + Rt) * s
    return 0.0

def bell_radius_at(base_radius: float, tip_radius: float, height: float, z: float, exponent: float = 1.5) -> float:
    """Polished bell profile: r(z) = R_base + (R_tip - R_base) * (z/H)^exp."""
    if height <= 0:
        return base_radius
    t = max(0.0, min(1.0, z / height))
    return base_radius + (tip_radius - base_radius) * (t ** exponent)

def lead_pipe_radius_at(mouthpiece_r: float, lead_r: float, length: float, z: float, exponent: float = 0.8) -> float:
    """Lead pipe taper: R(z) = R_m - (R_m - R_l)*(z/L)^exp."""
    if length <= 0:
        return mouthpiece_r
    t = max(0.0, min(1.0, z / length))
    return mouthpiece_r - (mouthpiece_r - lead_r) * (t ** exponent)
