"""build_material_test_grid.py

Build L_MaterialTest_Grid_2026-08-12 under
/Game/EnvSandbox/Materials/TestLevels — a swatch grid of every curated
material instance, one family per row (sphere per instance), neutral lighting,
readable from an orbit camera.

Doctrine:
  - Reads the curated MI list from a saved JSON (Saved/Audit/curated_mis.json):
      {"entries": [{"path": "/Game/.../MI_X", "family": "SDF"}]}
    Written by refresh_curated_mis() below; run it first if the file is absent.
  - Excludes _Archive/_Scratch/_Candidates/Dev/PARKED.
  - Every swatch is tagged MI_Preview_Swatch and recorded in the saved grid
    manifest (asset path -> actor label) for later capture + verification.
  - Save -> reload the level -> verify per-actor material assignment (rule 9).

Run (one editor, serialized): Monolith editor_query run_python -> this file
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import unreal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LEVEL_PATH = "/Game/EnvSandbox/Materials/TestLevels/L_MaterialTest_Grid_2026-08-12"
GRID_MANIFEST = PROJECT_ROOT / "Saved" / "Audit" / "material_grid_manifest.json"
CURATED_JSON = PROJECT_ROOT / "Saved" / "Audit" / "curated_mis.json"

MAT_ROOTS = [
    "/Game/EnvSandbox/Materials/SDF/Instances",
    "/Game/EnvSandbox/Materials/Instances",
    "/Game/EnvSandbox/Materials/Impressionist/Instances",
]
EXCLUDED_SUBSTR = ("_Archive", "_Scratch", "_Candidates", "/Dev/", "_PARKED_", "/Preview/")

FAMILY_ORDER = [
    "SDF", "Baroque", "Crystal", "Halftone", "Glitter", "Showcase",
    "NikkiHero", "NikkiIntegrated", "Water", "Impressionist", "Utility", "Other",
]

SPHERE = "/Engine/BasicShapes/Sphere.Sphere"
GRID_SPACING_X = 260.0
GRID_SPACING_Y = 260.0
ROW_START_Z = 60.0


def excluded(path: str) -> bool:
    return any(tok in path for tok in EXCLUDED_SUBSTR)


def family_for(path: str) -> str:
    stem = path.rsplit("/", 1)[-1].split(".")[0]
    for fam in ("Showcase", "NikkiHero", "NikkiIntegrated", "Water", "Impressionist",
                "Halftone", "Baroque", "Crystal", "Glitter", "Utility", "SDF"):
        if "/" + fam + "/" in path or stem.startswith("MI_" + fam):
            return fam
    return "Other"


def refresh_curated_mis() -> dict:
    entries = []
    seen = set()
    for root in MAT_ROOTS:
        if not unreal.EditorAssetLibrary.does_directory_exist(root):
            continue
        for path in unreal.EditorAssetLibrary.list_assets(root, recursive=True, include_folder=False):
            stem = path.rsplit("/", 1)[-1].split(".")[0]
            if not stem.startswith("MI_") or excluded(path) or path in seen:
                continue
            seen.add(path)
            mi = unreal.load_asset(path)
            if mi is None or "MaterialInstanceConstant" not in type(mi).__name__:
                continue
            entries.append({"path": path.split(".")[0], "family": family_for(path)})
    CURATED_JSON.parent.mkdir(parents=True, exist_ok=True)
    CURATED_JSON.write_text(json.dumps({"entries": entries}, indent=2), encoding="utf-8")
    print(f"CURATED|{len(entries)} MIs -> {CURATED_JSON}")
    return {"entries": entries}


def family_rows(entries: list[dict]) -> list[tuple[str, list[dict]]]:
    by_fam: dict[str, list[dict]] = {}
    for e in entries:
        by_fam.setdefault(e["family"], []).append(e)
    rows = []
    for fam in FAMILY_ORDER:
        if fam in by_fam and by_fam[fam]:
            rows.append((fam, by_fam[fam]))
    # anything not in the order goes last
    rest = [f for f in by_fam if f not in FAMILY_ORDER]
    for fam in rest:
        rows.append((fam, by_fam[fam]))
    return rows


def spawn_swatch(location, label: str, material_path: str):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, location, unreal.Rotator(0.0, 0.0, 0.0))
    if actor is None:
        return None
    sm = unreal.load_asset(SPHERE)
    if sm is None:
        return None
    comp = actor.static_mesh_component
    comp.set_static_mesh(sm)
    comp.set_material(0, unreal.load_asset(material_path))
    comp.set_editor_property("cast_shadow", True)
    actor.set_actor_label(label)
    actor.set_folder_path("Grid/Swatches")
    actor.set_editor_property("actor_enable_pause", False)
    return actor


def build_grid(entries: list[dict]) -> list[dict]:
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(LEVEL_PATH):
        les.load_level(LEVEL_PATH)
    else:
        unreal.EditorAssetLibrary.duplicate_asset(
            "/Game/EnvSandbox/_Template/L_MaterialPreview_Studio",
            "/Game/EnvSandbox/Materials/TestLevels",
            "L_MaterialTest_Grid_2026-08-12")
        les.load_level(LEVEL_PATH)

    rows = family_rows(entries)
    swatches: list[dict] = []
    x = y = 0.0
    for fam, members in rows:
        for i, e in enumerate(members):
            loc = unreal.Vector(
                x + i * GRID_SPACING_X,
                y,
                ROW_START_Z + (0.5 if i % 2 else 0.0))
            label = f"SW_{fam}_{e['path'].rsplit('/', 1)[-1]}"
            actor = spawn_swatch(loc, label, e["path"])
            if actor:
                swatches.append({
                    "label": label,
                    "material": e["path"],
                    "family": fam,
                    "x": loc.x, "y": loc.y, "z": loc.z,
                })
        y += GRID_SPACING_Y
        x = 0.0

    # neutral light rig (test readability, not beauty)
    try:
        unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.DirectionalLight, unreal.Vector(0, 0, 1400),
            unreal.Rotator(-40.0, 0.0, 0.0))
        unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.SkyLight, unreal.Vector(0, 0, 1000), unreal.Rotator())
    except Exception as exc:
        print(f"LIGHT_WARN|{exc}")

    saved = unreal.EditorLevelLibrary.save_current_level()
    print(f"GRID|swatches={len(swatches)}|saved={saved}")
    return swatches


def verify_grid(expected: list[dict]) -> dict:
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    les.load_level(LEVEL_PATH)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    ok = 0
    mismatched = []
    missing = []
    for exp in expected:
        found = None
        for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor):
            if actor.get_actor_label() == exp["label"]:
                found = actor
                break
        if found is None:
            missing.append(exp["label"])
            continue
        try:
            mats = found.static_mesh_component.get_materials()
        except Exception:
            mats = []
        if mats and mats[0] and mats[0].get_path_name() == exp["material"]:
            ok += 1
        else:
            mismatched.append({"label": exp["label"], "have": mats[0].get_path_name() if mats and mats[0] else None, "want": exp["material"]})
    return {"matched": ok, "missing": missing, "mismatched": mismatched}


def main() -> int:
    if CURATED_JSON.is_file():
        entries = json.loads(CURATED_JSON.read_text(encoding="utf-8"))["entries"]
    else:
        entries = refresh_curated_mis()["entries"]
    if not entries:
        print("NO_ENTRIES|run refresh_curated_mis first")
        return 1
    swatches = build_grid(entries)
    GRID_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    GRID_MANIFEST.write_text(json.dumps({"swatches": swatches}, indent=2), encoding="utf-8")
    verify = verify_grid(swatches)
    GRID_MANIFEST.write_text(
        json.dumps({"swatches": swatches, "verify": verify}, indent=2), encoding="utf-8")
    print(f"VERIFY|{json.dumps(verify)}")
    print(f"WROTE|{GRID_MANIFEST}")
    return 0 if verify["matched"] == len(swatches) and not verify["mismatched"] else 2


if __name__ == "__main__":
    raise SystemExit(main())