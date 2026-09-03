# addon_utils - Blender-side helpers for Melodia Studio family
# Copyright (c) 2026 fromage3900 - MIT
# Only import from here inside Blender (bpy may be absent offline).

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure melodia_utils is importable (parent is Script Directory)
_HERE = Path(__file__).resolve().parent
_ADDONS_ROOT = _HERE.parent
if str(_ADDONS_ROOT) not in sys.path:
    sys.path.insert(0, str(_ADDONS_ROOT))

try:
    import melodia_utils as mu  # type: ignore
except Exception:
    mu = None  # type: ignore


# ------------------------------------------------------------------ design tokens (live site, Melodia luxury editorial x HoYoverse celestial)
# Tokens from melodia-design-system/tokens.json + wix/melodia-tokens.css
# Used for bespoke header copy; not applied as direct UI tint (Blender theme is user-controlled)
MELODIA_GOLD = "#C9A86A"
MELODIA_PLUM = "#241B2E"
MELODIA_IVORY = "#FCFBF8"
MELODIA_ASTRAL = "#141A30"
MELODIA_IRIS = "#6E5AA6"
MELODIA_SAKURA = "#E7C9CE"

# ------------------------------------------------------------------ icons

_ICON_CACHE = None
_ICONS_LOADED = False


def _load_icons():
    global _ICON_CACHE, _ICONS_LOADED
    if _ICONS_LOADED:
        return _ICON_CACHE
    _ICONS_LOADED = True
    try:
        import bpy.utils.previews as previews  # type: ignore
        pcoll = previews.new()
        # Primary: melodia_icons folder (bespoke)
        icons_dir = _ADDONS_ROOT / "melodia_icons"
        if icons_dir.is_dir():
            for png in icons_dir.glob("*.png"):
                key = png.stem
                try:
                    pcoll.load(key, str(png), 'IMAGE')
                except Exception:
                    pass
        # Chrome: gold-ivory with pink/rose-gold header, rules, preset cards, pillar dots
        try:
            chrome_dir = _HERE / "melodia_chrome"
            # fallback to sibling melodia_chrome package path
            if not chrome_dir.is_dir():
                chrome_dir = _ADDONS_ROOT / "melodia_chrome"
            if chrome_dir.is_dir():
                for png in chrome_dir.glob("*.png"):
                    key = png.stem
                    if key in pcoll:
                        continue
                    try:
                        pcoll.load(key, str(png), 'IMAGE')
                    except Exception:
                        pass
        except Exception:
            pass
        # Secondary: reuse generated T_Melodia textures as icon backplates where useful
        # (lightweight, only load small subset to avoid polluting cache)
        try:
            from pathlib import Path as _P
            gen_root = _P(r"C:\EnvironmentPortfolio\generated\assets\melodia-game-ui")
            if gen_root.is_dir():
                for name in ["T_Melodia_FiligreeDivider.png", "T_Melodia_FiligreeCornerBaroque.png"]:
                    fp = gen_root / name
                    if fp.exists():
                        key = fp.stem.lower()
                        if key not in pcoll:
                            try:
                                pcoll.load(key, str(fp), 'IMAGE')
                            except Exception:
                                pass
        except Exception:
            pass
        _ICON_CACHE = pcoll
        return pcoll
    except Exception:
        return None


def icon_kwargs(key: str, fallback: str = 'NONE') -> dict:
    """Usage: layout.operator(..., **icon_kwargs('starlight', 'SHADERFX'))"""
    pcoll = _load_icons()
    if pcoll is not None and key in pcoll:
        return {"icon_value": pcoll[key].icon_id}
    return {"icon": fallback}


def get_icon_id(key: str) -> int:
    """Return preview icon_id or 0."""
    pcoll = _load_icons()
    if pcoll is not None and key in pcoll:
        return pcoll[key].icon_id
    return 0


def unload_icons():
    global _ICON_CACHE, _ICONS_LOADED
    if _ICON_CACHE is not None:
        try:
            import bpy.utils.previews as previews  # type: ignore
            previews.remove(_ICON_CACHE)
        except Exception:
            pass
    _ICON_CACHE = None
    _ICONS_LOADED = False


# ------------------------------------------------------------------ bespoke header helpers - make panels feel like Melodia, not Blender

def draw_melodia_header(layout, title: str, subtitle: str = "", icon_key: str = "starlight"):
    """Branded header that lifts the panel out of stock Blender.

    Renders: [star icon]  MELODIA  -  Title  (kicker + headline hierarchy)
    Uses icon_value when custom PNG is available, ASCII fallback otherwise
    to avoid unicode bake issues.
    """
    try:
        import bpy  # type: ignore
    except Exception:
        layout.label(text=f"{title}")
        return
    header = layout.box()
    row = header.row()
    # Star mark + wordmark - use custom icon, ASCII star fallback (no emoji)
    icon_id = get_icon_id(icon_key)
    if icon_id:
        row.label(text="", icon_value=icon_id)
    else:
        row.label(text="*")
    # Cinzel wordmark + Syne title simulation: uppercase
    row.label(text=f"MELODIA  -  {title.upper()}")
    if subtitle:
        header.label(text=subtitle, icon='INFO')
    # Gold rule simulation - thin divider with centered marker (ASCII to avoid bake issues)
    sep = header.row()
    sep.alignment = 'CENTER'
    sep.label(text="-- * --")


def draw_gold_rule(layout):
    row = layout.row()
    row.alignment = 'CENTER'
    row.label(text="-- * --")


def draw_kicker(layout, text: str, icon: str = 'NONE'):
    """Mono kicker (Azeret Mono 0.22em uppercase gold) proxy."""
    row = layout.row()
    # Uppercase + spaced mimics 0.22em tracking
    spaced = "  ".join(text.upper())
    if icon != 'NONE':
        row.label(text=spaced, icon=icon)
    else:
        row.label(text=spaced)


# ------------------------------------------------------------------ cleanup

def cleanup_objects_with_prefix(prefixes: tuple[str, ...] = ("Terrain", "Showroom_Terrain", "MS_", "SR_")) -> int:
    """Remove old terrain/camera/light objects that clutter the scene on re-generate."""
    try:
        import bpy  # type: ignore
    except Exception:
        return 0
    removed = 0
    for obj in list(bpy.data.objects):
        if any(obj.name.startswith(p) for p in prefixes):
            # Don't delete if user renamed and is using it elsewhere - only our generated prefixes
            try:
                bpy.data.objects.remove(obj, do_unlink=True)
                removed += 1
            except Exception:
                pass
    # Also purge orphan meshes/materials that were tied to those objects
    # (gentle - only if user has no users)
    return removed


def cleanup_meshes_by_name(name_substr: str = "Terrain") -> int:
    try:
        import bpy  # type: ignore
    except Exception:
        return 0
    removed = 0
    for mesh in list(bpy.data.meshes):
        if name_substr in mesh.name and mesh.users == 0:
            try:
                bpy.data.meshes.remove(mesh)
                removed += 1
            except Exception:
                pass
    return removed


# ------------------------------------------------------------------ folders & health

def open_folder(path: str | Path) -> str:
    """Open OS file browser; returns path string for report."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    try:
        import bpy  # type: ignore
        # Blender's path is more reliable cross-platform
        import subprocess, platform
        s = str(p.resolve())
        system = platform.system()
        if system == "Windows":
            os.startfile(s)  # type: ignore[attr-defined]
        elif system == "Darwin":
            subprocess.Popen(["open", s])
        else:
            subprocess.Popen(["xdg-open", s])
    except Exception:
        pass
    return str(p)


def health_report_text() -> str:
    if mu is None:
        return "melodia_utils not importable"
    import json
    h = mu.health_check()
    lines = [
        f"Repo: {h['repo_root']}",
        f"MIDI: {h['midi_count']} files - {'OK' if h['midi_ok'] and h['has_default_midi'] else 'MISSING'}",
        f"Voxel: {'OK' if h['voxel_ok'] else 'MISSING'} {h['voxel_dir']}",
        f"Presets: {'on disk' if h['presets_exists'] else 'defaults (not yet exported)'}",
    ]
    if h["issues"]:
        lines.append("Issues:")
        for iss in h["issues"]:
            lines.append(f"  * {iss}")
    else:
        lines.append("Health: OK - C: authority")
    return "\n".join(lines)


def repo_root_path() -> Path:
    if mu is not None:
        return mu.repo_root()
    # fallback - this file -> BS_GodFile
    return _HERE.parent.parent.parent.resolve() if (_HERE.parent.parent / "Content").exists() else Path(r"C:\EnvironmentPortfolio\BS_GodFile")
