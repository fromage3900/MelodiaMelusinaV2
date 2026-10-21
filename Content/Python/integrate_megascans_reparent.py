"""Reparent Megascans MIs onto Melodia Toon Universal master.

Searches for assets by name pattern (census names may not match disk exactly).
Run inside UE editor via Monolith run_python:
    import integrate_megascans_reparent as imr
    imr.run()

Targets (from megascans_census_2026-09-15.json):
  - MI_MossyRock_21 (parent unknown "?", dead_vs_universal=69) -> M_Master_Toon_Universal
  - MI_Rock_01 (parent stock Quixel, dead_vs_universal=69) -> M_Master_Toon_Universal
"""

from __future__ import annotations

import unreal

TOON_UNIVERSAL = "/Game/Melodia/Materials/Masters/M_Master_Toon_Universal"
SEARCH_PATTERNS = ["MossyRock", "Rock_01"]


def _find_asset(pattern: str) -> str | None:
    """Return first asset path whose basename contains pattern (case-insensitive)."""
    try:
        assets = unreal.EditorAssetLibrary.list_assets("/Game/Megascans", recursive=True)
    except Exception as exc:  # noqa: BLE001
        unreal.log_error(f"[MEGASCANS] list_assets failed: {exc}")
        return None
    pat = pattern.lower()
    for a in assets:
        if pat in a.lower():
            return a
    return None


def _load(path: str):
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if asset is None:
        raise FileNotFoundError(f"Asset not found: {path}")
    return asset


def run() -> dict:
    master = _load(TOON_UNIVERSAL)
    results = {}

    for pattern in SEARCH_PATTERNS:
        path = _find_asset(pattern)
        if path is None:
            results[pattern] = f"NOT FOUND on disk (pattern: {pattern})"
            continue
        mi = _load(path)
        old_parent = str(mi.get_editor_property("parent"))
        if old_parent == str(master.get_path_name()):
            results[path] = f"already on {TOON_UNIVERSAL}"
            continue
        try:
            mi.set_editor_property("parent", master)
            unreal.EditorAssetLibrary.save_asset(path, False)
            results[path] = f"reparented {old_parent} -> {TOON_UNIVERSAL}"
            unreal.log(f"[MEGASCANS] {path}: reparented onto {TOON_UNIVERSAL}")
        except Exception as exc:  # noqa: BLE001
            results[path] = f"FAILED: {exc}"
            unreal.log_error(f"[MEGASCANS] {path}: reparent failed: {exc}")

    return results


if __name__ == "__main__":
    print(run())
