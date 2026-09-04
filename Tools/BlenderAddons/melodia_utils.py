# melodia_utils - shared pure-Python for all Melodia Blender addons
# Copyright (c) 2026 fromage3900 / Melodia Project - MIT
#
# Cross-workstation rule:
# The active checkout is authority. Drive letters are not authority.

from __future__ import annotations

import os
from pathlib import Path

_SENTINEL = Path("Content") / "MelodiaIntegration" / "MIDI"


def _looks_like_repo(path: Path) -> bool:
    """Return True when path looks like the MelodiaMelusinaV2 checkout."""
    try:
        p = path.expanduser().resolve()
    except (OSError, RuntimeError, ValueError):
        return False

    return (
        (p / "BS_GodFile.uproject").is_file()
        and (p / "Tools").is_dir()
        and (p / "deploy").is_dir()
    )


def _walk_for_repo(start: Path) -> Path | None:
    try:
        resolved = start.expanduser().resolve()
    except (OSError, RuntimeError, ValueError):
        return None

    candidates = [resolved] + list(resolved.parents)
    for candidate in candidates:
        if _looks_like_repo(candidate):
            return candidate
    return None


def repo_root() -> Path:
    """Resolve the active Melodia checkout without assuming a drive letter.

    Order:
      1. explicit MELODIA_PROJECT_ROOT / legacy MELODIA_PROJECT_ROOT_C
      2. checkout containing this module
      3. current working directory's checkout
      4. deterministic module-relative fallback

    A valid laptop checkout is just as authoritative as the PC checkout.
    """
    env = os.environ.get("MELODIA_PROJECT_ROOT") or os.environ.get("MELODIA_PROJECT_ROOT_C")
    if env:
        configured = Path(env).expanduser()
        if _looks_like_repo(configured):
            return configured.resolve()
        raise RuntimeError(
            f"MELODIA_PROJECT_ROOT points to a non-Melodia checkout: {configured}"
        )

    from_module = _walk_for_repo(Path(__file__).resolve().parent)
    if from_module is not None:
        return from_module

    from_cwd = _walk_for_repo(Path.cwd())
    if from_cwd is not None:
        return from_cwd

    fallback = Path(__file__).resolve().parents[2]
    if _looks_like_repo(fallback):
        return fallback

    raise RuntimeError(
        "Could not resolve Melodia project root from environment, module location, or cwd."
    )


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


def health_check() -> dict:
    """Offline health snapshot - no bpy required."""
    root = repo_root()
    midi_dir = midi_content_dir()
    voxel_dir = voxel_tool_dir()
    studio = studio_root()

    midi_ok = midi_dir.is_dir()
    midi_count = 0
    has_default = False
    if midi_ok:
        for _ in midi_dir.rglob("*.mid*"):
            midi_count += 1
        has_default = (midi_dir / "128BPMarpeggiomelody.mid").exists()

    voxel_ok = (voxel_dir / "midi_voxel_v3.py").exists()
    presets_exists = presets_path().exists()

    root_text = str(root).lower()
    drive = root.drive.lower() if root.drive else ""
    is_non_c_drive = bool(drive and drive != "c:")
    is_g_drive = drive == "g:" or root_text.startswith("g:/") or root_text.startswith("g:\\")

    issues: list[str] = []
    if not midi_ok:
        issues.append(f"MIDI dir missing: {midi_dir}")
    elif not has_default:
        issues.append("128BPMarpeggiomelody.mid not found in MIDI dir")
    if not voxel_ok:
        issues.append(f"midi_to_voxel missing: {voxel_dir / 'midi_voxel_v3.py'}")
    if not (root / "Tools" / "BlenderAddons").is_dir():
        issues.append(f"BlenderAddons missing under {root}")

    return {
        "ok": not issues,
        "repo_root": str(root),
        "authority": "active_checkout",
        "drive": drive,
        # Retained for legacy callers as diagnostics only; non-C is no longer unhealthy.
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
        for pattern in ("*.mid", "*.midi"):
            for p in root.rglob(pattern):
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

    import re

    for child in sorted(root.iterdir()):
        init = child / "__init__.py"
        if not init.exists():
            continue
        text = init.read_text(encoding="utf-8", errors="ignore")
        version_match = re.search(r'"version"\s*:\s*\(([^)]+)\)', text)
        name_match = re.search(r'"name"\s*:\s*"([^"]+)"', text)
        out.append({
            "folder": child.name,
            "name": name_match.group(1) if name_match else child.name,
            "version": version_match.group(1).strip() if version_match else "?",
            "path": str(child),
        })

    return out
