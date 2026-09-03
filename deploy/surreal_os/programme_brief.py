"""Programme Brief — architectural programme validation for Melodia Studio.

Architect's lens P0: every space has a brief (area, proportion, height, adjacency).
Validates gb_* props against programme_types.yaml so a machiai is not drawn as a nave.
"""
from __future__ import annotations
import os
from ._io import package_path

_BRIEF_CACHE: dict[str, dict] = {}
_BRIEF_FILE = "programme_types.yaml"

def _load_briefs() -> dict[str, dict]:
    if _BRIEF_CACHE:
        return _BRIEF_CACHE
    # try yaml then json fallback
    base = package_path("")
    # package_path("") is surreal_os root
    yaml_path = os.path.join(base, _BRIEF_FILE)
    json_path = os.path.join(base, "programme_types.json")
    data = None
    # yaml if available
    if os.path.exists(yaml_path):
        try:
            import yaml  # type: ignore
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except Exception:
            data = None
    if data is None and os.path.exists(json_path):
        try:
            import json
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f) or {}
        except Exception:
            data = {}
    if not isinstance(data, dict):
        data = {}
    # data shape: {programme_id: {min_area, max_area, proportion, height, ...}}
    for k, v in list(data.items()):
        if isinstance(v, dict):
            _BRIEF_CACHE[k] = v
    return _BRIEF_CACHE

def list_programmes() -> list[str]:
    return sorted(_load_briefs().keys())

def get_brief(programme_id: str) -> dict | None:
    return _load_briefs().get(programme_id)

def validate_props(props, programme_id: str) -> list[str]:
    """Check gb_* props against brief, return list of error strings (empty = OK)."""
    brief = get_brief(programme_id)
    if not brief:
        return []
    errs = []
    # area = width * depth for rect, pi*r^2 for circular
    w = float(getattr(props, "gb_width", 0) or 0)
    d = float(getattr(props, "gb_depth", 0) or 0)
    h = float(getattr(props, "gb_height", 0) or 0)
    r = float(getattr(props, "gb_room_radius", 0) or 0)
    shape = str(getattr(props, "gb_room_shape", "RECTANGLE") or "RECTANGLE")
    if shape in ("CIRCLE", "ROTUNDA", "APSIDAL"):
        area = 3.14159 * r * r if r > 0 else w * d
        prop = 1.0
    elif shape == "SUPERELLIPSE":
        area = w * d * 0.9
        prop = max(w, d) / max(1e-6, min(w, d))
    else:
        area = w * d
        prop = max(w, d) / max(1e-6, min(w, d))
    min_area = brief.get("min_area")
    max_area = brief.get("max_area")
    if isinstance(min_area, (int, float)) and area < float(min_area) - 0.01:
        errs.append(f"area {area:.1f} < brief min {min_area}")
    if isinstance(max_area, (int, float)) and area > float(max_area) + 0.01:
        errs.append(f"area {area:.1f} > brief max {max_area}")
    proportion = brief.get("proportion")
    if isinstance(proportion, str) and ":" in proportion:
        try:
            a, b = proportion.split(":")
            target = float(a) / float(b)
            if abs(prop - target) > 0.35:
                errs.append(f"proportion {prop:.2f} vs brief {proportion}")
        except: pass
    height = brief.get("height")
    if isinstance(height, (int, float)) and abs(h - float(height)) > 0.6:
        errs.append(f"height {h:.1f} vs brief {height}")
    # clearance head 2.1m
    clearance = brief.get("clearance_head")
    if isinstance(clearance, (int, float)) and h < float(clearance) - 0.01:
        errs.append(f"height {h:.1f} < clearance {clearance}")
    return errs

def brief_summary(props, programme_id: str) -> str:
    brief = get_brief(programme_id)
    if not brief:
        return "No brief"
    errs = validate_props(props, programme_id)
    w = float(getattr(props, "gb_width", 0) or 0)
    d = float(getattr(props, "gb_depth", 0) or 0)
    h = float(getattr(props, "gb_height", 0) or 0)
    r = float(getattr(props, "gb_room_radius", 0) or 0)
    shape = str(getattr(props, "gb_room_shape", "RECTANGLE"))
    if shape in ("CIRCLE", "ROTUNDA"):
        area = 3.14159 * r * r
    else:
        area = w * d
    status = "OK" if not errs else "; ".join(errs)
    label = brief.get("label", programme_id)
    return f"{label}: {area:.1f}m2 {w:.1f}x{d:.1f} h{h:.1f} — {status}"
