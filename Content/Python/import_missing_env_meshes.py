"""Import the meshes the 2026-08-13 mass GLB import missed (see Saved/Audit/mesh_import_diff.json).

Missing set (verified 2026-08-13, binary FBX, all licensed):
  - AvatarGarden_PolygonalMind (141 files; pack had no GLB -> skipped by GLB-route mass import)
  - KenneyMiniForest character-archer (FBX route; obj/glb duplicates skipped)
  - CrystalCrossroads Rooms_Paradise_SmallWall02_Art
  - StylizedEnchantedForest crystalslow

Imports with materials AND textures disabled (intake contract: never let the FBX
factory generate junk materials). Dest: /Game/EnvSandbox/Meshes/Environment (same
root as the mass import). Never overwrites: replace_existing=False, stems already
on disk are skipped and counted.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import unreal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DIFF = PROJECT_ROOT / "Saved" / "Audit" / "mesh_import_diff.json"
DEST = "/Game/EnvSandbox/Meshes/Environment"

# Same mesh in several formats; pick one importer per stem.
FORMAT_PRIORITY = [".fbx", ".glb", ".obj"]


def choose_files(missing: list[str]) -> list[Path]:
    by_stem: dict[str, Path] = {}
    for rel in missing:
        p = PROJECT_ROOT / "Imports" / "Environment" / rel
        if not p.exists():
            continue
        stem = p.stem.lower()
        if stem not in by_stem:
            by_stem[stem] = p
        else:
            cur = by_stem[stem].suffix.lower()
            new = p.suffix.lower()
            if FORMAT_PRIORITY.index(new) < FORMAT_PRIORITY.index(cur):
                by_stem[stem] = p
    return sorted(by_stem.values(), key=lambda p: str(p).lower())


def main() -> int:
    if not DIFF.exists():
        unreal.log_error(f"[mesh_import] missing diff manifest: {DIFF}")
        return 2
    report = json.loads(DIFF.read_text(encoding="utf-8"))
    files = choose_files(report.get("missing", []))
    unreal.log(f"[mesh_import] candidates from diff: {len(files)}")

    existing = set()
    skipped: list[str] = []
    to_import: list[str] = []
    for p in files:
        game = f"{DEST}/{p.stem}"
        if unreal.EditorAssetLibrary.does_asset_exist(game):
            existing.add(p.stem)
            skipped.append(str(p))
        else:
            to_import.append(str(p))
    unreal.log(f"[mesh_import] already exist: {len(existing)} | to import: {len(to_import)}")

    failures: list[str] = []
    imported: list[str] = []
    for path in to_import:
        p = Path(path)
        fbx_options = unreal.FbxImportUI()
        fbx_options.set_editor_property("import_materials", False)
        fbx_options.set_editor_property("import_textures", False)
        fbx_options.set_editor_property("import_as_skeletal", False)
        task = unreal.AssetImportTask()
        task.set_editor_property("automated", True)
        task.set_editor_property("filename", path)
        task.set_editor_property("destination_path", DEST)
        task.set_editor_property("replace_existing", False)
        task.set_editor_property("save", False)
        task.options = fbx_options
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        task_done = task.get_editor_property("is_complete") if hasattr(task, "is_complete") else True
        if task_done:
            imported.append(p.stem)
        else:
            failures.append(path)
        if len(imported) % 10 == 0 and imported:
            unreal.log(f"[mesh_import] progress: {len(imported)}/{len(to_import)}")

    unreal.log(f"[mesh_import] imported: {len(imported)} | failures: {len(failures)} | skipped-existing: {len(skipped)}")

    if imported:
        saved = 0
        for stem in imported:
            try:
                if unreal.EditorAssetLibrary.save_asset(f"{DEST}/{stem}"):
                    saved += 1
            except Exception:
                pass
        unreal.log(f"[mesh_import] saved: {saved}/{len(imported)}")

    manifest = {
        "generated": "2026-08-13",
        "dest": DEST,
        "imported": imported,
        "failures": failures,
        "skipped_existing": skipped,
    }
    out = PROJECT_ROOT / "Saved" / "Audit" / "mesh_import_results.json"
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    unreal.log(f"[mesh_import] manifest -> {out}")
    return 0 if not failures else 1


if __name__ == "__main__":
    time.sleep(5)
    sys.exit(main())
