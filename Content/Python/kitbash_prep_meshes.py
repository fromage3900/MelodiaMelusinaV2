"""Kitbash packaging: LODs, collision, material slots, FBX export for ornamental meshes.

Run in Unreal Editor Python:
  import kitbash_prep_meshes as k; k.main()

Or:
  py Content/Python/kitbash_prep_meshes.py
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

from ornament_kitbash_catalog import MESHES, ORNAMENT_DIR

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIR = PROJECT_ROOT / "KitbashExport" / "OrnamentalMeshes"
MANIFEST_PATH = PROJECT_ROOT / "Saved" / "Audit" / "kitbash_export_manifest.json"

MATERIAL_SLOTS = [
    ("Base", "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal"),
    ("Trim", "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal"),
]


def setup_lods(mesh: unreal.StaticMesh, num_lods: int = 3) -> bool:
    try:
        mesh.editor_set_lod_count(num_lods + 1)
        for lod_idx in range(1, num_lods + 1):
            settings = unreal.MeshReductionSettings()
            settings.percent_triangles = max(0.2, 1.0 - lod_idx * 0.25)
            settings.recalculate_normals = True
            mesh.build_lod(lod_idx, settings)
        return True
    except Exception as exc:
        unreal.log_error(f"[Kitbash] LOD failed: {exc}")
        return False


def setup_collision(mesh: unreal.StaticMesh) -> bool:
    try:
        body_setup = mesh.get_editor_property("body_setup")
        if not body_setup:
            body_setup = unreal.BodySetup()
            mesh.set_editor_property("body_setup", body_setup)
        body_setup.collision_trace_flag = unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX
        body_setup.build_physics_meshes()
        return True
    except Exception as exc:
        unreal.log_error(f"[Kitbash] Collision failed: {exc}")
        return False


def setup_material_slots(mesh: unreal.StaticMesh) -> bool:
    try:
        mesh.set_editor_property("static_materials", [])
        for slot_name, mat_path in MATERIAL_SLOTS:
            mat = unreal.load_asset(mat_path)
            if not mat:
                unreal.log_warning(f"[Kitbash] Material missing: {mat_path}")
                continue
            slot = unreal.StaticMaterial()
            slot.material_interface = mat
            slot.material_slot_name = slot_name
            slot.uv_channel_data = unreal.MeshUVChannelInfo()
            mesh.add_material_slot(slot)
        return True
    except Exception as exc:
        unreal.log_error(f"[Kitbash] Material slots failed: {exc}")
        return False


def export_fbx(mesh: unreal.StaticMesh, export_path: str) -> bool:
    try:
        export_options = unreal.FbxExportOption()
        export_options.ascii = False
        export_options.level_of_detail = False
        export_options.collision = True
        export_options.vertex_color = True
        export_options.materials = True
        export_options.textures = False

        task = unreal.AssetExportTask()
        task.object = mesh
        task.filename = export_path
        task.exporter = unreal.StaticMeshExporterFBX()
        task.options = export_options
        task.automated = True
        task.prompt = False
        return unreal.Exporter.run_asset_export_task(task)
    except Exception as exc:
        unreal.log_error(f"[Kitbash] FBX export failed: {exc}")
        return False


def main() -> bool:
    unreal.log("[Kitbash] Ornamental mesh export starting...")
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)

    manifest_entries: list[dict] = []
    success = 0

    for spec in MESHES:
        path = f"{spec.ue_path}.{spec.asset_name}"
        mesh = unreal.load_asset(path)
        entry = {
            "asset_name": spec.asset_name,
            "tier": spec.tier,
            "pillar": spec.pillar,
            "ue_path": spec.ue_path,
            "exists": mesh is not None,
            "lod_ok": False,
            "collision_ok": False,
            "materials_ok": False,
            "fbx_exported": False,
            "fbx_path": None,
        }

        if not mesh:
            unreal.log_warning(f"[Kitbash] Missing mesh — run generate_ornamental_meshes.py --all: {path}")
            manifest_entries.append(entry)
            continue

        unreal.log(f"[Kitbash] Processing {spec.asset_name}...")
        entry["lod_ok"] = setup_lods(mesh, spec.lods)
        entry["collision_ok"] = setup_collision(mesh)
        entry["materials_ok"] = setup_material_slots(mesh)
        unreal.EditorAssetLibrary.save_asset(spec.ue_path, only_if_is_dirty=False)

        fbx_path = EXPORT_DIR / spec.fbx_name
        if export_fbx(mesh, str(fbx_path)):
            entry["fbx_exported"] = True
            entry["fbx_path"] = str(fbx_path.resolve())
            success += 1

        manifest_entries.append(entry)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ornament_dir": ORNAMENT_DIR,
        "export_dir": str(EXPORT_DIR.resolve()),
        "meshes": manifest_entries,
        "success_count": success,
        "total": len(MESHES),
        "complete": success == len(MESHES),
    }
    MANIFEST_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[Kitbash] {success}/{len(MESHES)} exported -> {EXPORT_DIR}")
    unreal.log(f"[Kitbash] Manifest -> {MANIFEST_PATH}")
    unreal.log("[Kitbash] Next: python Content/Python/package_ornament_kitbash.py --zip")
    return report["complete"]


if __name__ == "__main__":
    main()
