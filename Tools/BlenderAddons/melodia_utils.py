# melodia_utils - shared pure-Python for all Melodia Blender addons
# Copyright (c) 2026 fromage3900 / Melodia Project - MIT
# C: main authority. No G: drive fallback.

from __future__ import annotations

import os
import sys
from pathlib import Path


# ------------------------------------------------------------------ C main

# Canonical C: authority. Environment variable may override for CI/tests,
# but the on-disk default is C:\EnvironmentPortfolio\BS_GodFile.
_CANONICAL_C_ROOT = Path(r"C:\EnvironmentPortfolio\BS_GodFile")

# Sentinel that proves we found the repo (Content/Melodia exists).
_SENTINEL = Path("Content") / "MelodiaIntegration" / "MIDI"


def _is_c_authority_path(path: str | Path) -> bool:
    """Return True only for paths resolved on the canonical C: authority."""
    try:
        return Path(path).expanduser().resolve().drive.lower() == "c:"
    except (OSError, RuntimeError, ValueError):
        text = str(path).lower()
        return text.startswith("c:\\") or text.startswith("c:/")


def repo_root() -> Path:
    """Resolve BS_GodFile root - C: is authority.

    Order:
      1. $MELODIA_PROJECT_ROOT if it points at a valid repo
      2. Canonical C: path if it exists
      3. Walk up from this file until sentinel is found
    Never returns a G: path.
    """
    # 1) explicit env
    env = os.environ.get("MELODIA_PROJECT_ROOT") or os.environ.get("MELODIA_PROJECT_ROOT_C")
    if env:
        p = Path(env).expanduser().resolve()
        # An override must not redirect Blender to a second worktree.
        if _is_c_authority_path(p) and ((p / _SENTINEL).is_dir() or (p / _SENTINEL).exists()):
            return p
        if _is_c_authority_path(p) and p.is_dir():
            # accept if it looks like BS_GodFile even without MIDI yet
            if (p / "Tools" / "BlenderAddons").is_dir():
                return p

    # 2) canonical C
    if _CANONICAL_C_ROOT.is_dir() and (_CANONICAL_C_ROOT / "Tools" / "BlenderAddons").is_dir():
        return _CANONICAL_C_ROOT.resolve()

    # 3) walk up from this file
    here = Path(__file__).resolve()
    for parent in [here.parent] + list(here.parents):
        if (parent / _SENTINEL).exists() or (parent / "Tools" / "BlenderAddons").is_dir():
            # Heuristic: must be named BS_GodFile or contain that sentinel
            if _is_c_authority_path(parent) and (parent.name == "BS_GodFile" or (parent / _SENTINEL).exists()):
                return parent
    # Fallback - the canonical path even if not yet on disk (lets callers report health)
    return _CANONICAL_C_ROOT


def studio_root() -> Path:
    return repo_root() / "Tools" / "MelodiaProceduralStudio"


def voxel_tool_dir() -> Path:
    return repo_root() / "Tools" / "midi_to_voxel"


def midi_content_dir() -> Path:
    return repo_root() / "Content" / "MelodiaIntegration" / "MIDI"


def scenes_dir() -> Path:
    return studio_root() / "GeneratedScenes"


def presets_path() -> Path:
    return studio_root() / "midi_presets.json"


# ------------------------------------------------------------------ health

def health_check() -> dict:
    """Offline health snapshot - no bpy required."""
    root = repo_root()
    midi_dir = midi_content_dir()
    voxel_dir = voxel_tool_dir()
    studio = studio_root()

    # MIDI presence
    midi_ok = midi_dir.is_dir()
    midi_count = 0
    has_default = False
    if midi_ok:
        for p in midi_dir.rglob("*.mid*"):
            midi_count += 1
        has_default = (midi_dir / "128BPMarpeggiomelody.mid").exists()

    # Voxel tool
    voxel_ok = (voxel_dir / "midi_voxel_v3.py").exists()

    # Presets file (optional - defaults are in code)
    presets_exists = presets_path().exists()

    # Authority guard - should never be off C:
    is_non_c_drive = not _is_c_authority_path(root)
    is_g_drive = str(root).lower().startswith("g:\\") or str(root).lower().startswith("g:/")

    issues: list[str] = []
    if is_non_c_drive:
        issues.append("repo_root resolved off C: - C: is authority; set MELODIA_PROJECT_ROOT=C:\\EnvironmentPortfolio\\BS_GodFile")
    if not midi_ok:
        issues.append(f"MIDI dir missing: {midi_dir}")
    elif not has_default:
        issues.append("128BPMarpeggiomelody.mid not found in MIDI dir")
    if not voxel_ok:
        issues.append(f"midi_to_voxel missing: {voxel_dir / 'midi_voxel_v3.py'}")
    if not (root / "Tools" / "BlenderAddons").is_dir():
        issues.append(f"BlenderAddons missing under {root}")

    ok = not issues and not is_non_c_drive and midi_ok and voxel_ok

    return {
        "ok": ok,
        "repo_root": str(root),
        "is_g_drive": is_g_drive,
        "is_non_c_drive": is_non_c_drive,
        "midi_dir": str(midi_dir),
        "midi_ok": midi_ok,
        "midi_count": midi_count,
        "has_default_midi": has_default,
        "voxel_dir": str(voxel_dir),
        "voxel_ok": voxel_ok,
        "studio_root": str(studio),
        "presets_path": str(presets_path()),
        "presets_exists": presets_exists,
        "issues": issues,
    }


def discover_midi(extra_dirs: list[str | Path] | None = None) -> list[Path]:
    """Find .mid/.midi files - deduped, sorted."""
    roots: list[Path] = [midi_content_dir(), repo_root() / "Imports" / "Audio"]
    if extra_dirs:
        roots.extend(Path(p) for p in extra_dirs)
    found: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        if not root.is_dir():
            continue
        for p in root.rglob("*.mid"):
            key = os.path.normcase(str(p.resolve()))
            if key in seen:
                continue
            seen.add(key)
            found.append(p)
        for p in root.rglob("*.midi"):
            key = os.path.normcase(str(p.resolve()))
            if key in seen:
                continue
            seen.add(key)
            found.append(p)
    return sorted(found)


def addon_versions(addons_root: str | Path | None = None) -> list[dict]:
    """Scan Tools/BlenderAddons/*/bl_info versions."""
    root = Path(addons_root) if addons_root else repo_root() / "Tools" / "BlenderAddons"
    out: list[dict] = []
    if not root.is_dir():
        return out
    for child in sorted(root.iterdir()):
        init = child / "__init__.py"
        if not init.exists():
            continue
        text = init.read_text(encoding="utf-8", errors="ignore")
        # crude parse of bl_info version tuple
        import re
        m = re.search(r'"version"\s*:\s*\(([^)]+)\)', text)
        ver = m.group(1).strip() if m else "?"
        name_m = re.search(r'"name"\s*:\s*"([^"]+)"', text)
        name = name_m.group(1) if name_m else child.name
        out.append({"folder": child.name, "name": name, "version": ver, "path": str(child)})
    return out
