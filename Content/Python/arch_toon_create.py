#!/usr/bin/env python3
"""Create missing Material Instances for architecture meshes (Cathedral + Atlantis).

Reads mesh slots → maps slot names to Material Instances of M_Master_Toon_Universal
→ assigns MIs to mesh slots via set_material().

Summary:
  - Cathedral: 82 mesh targets → 65 unique slot stems → 65 MIs
  - Atlantis:   105 mesh targets → 295 unique slot stems → ??? MIs
  - Total MIs created: #{{total_mi}}
  - Mesh slots assigned: #{{assigned_slots}}

DO NOT renames existing MIs. Only create new ones.

Dry-run output: Saved/Audit/arch_toon_missing_mi.json
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

# Try to import unreal, fall back with helpful message
try:
    import unreal
except ImportError as e:
    print(f"[FATAL] unreal module not available: {e}")
    print("  Run inside UE Python environment: Tools/ue_run_python.py --file ...")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
MESH_ROOTS = {
    "cathedral": Path("/Game/EnvSandbox/Meshes/Cathedral"),
    "atlantis":   Path("/Game/EnvSandbox/Meshes/Atlantis"),
}
MI_ROOTS = {
    "cathedral": Path("/Game/EnvSandbox/Materials/Instances/Architecture/Cathedral"),
    "atlantis":   Path("/Game/EnvSandbox/Materials/Instances/Architecture/Atlantis"),
}
PARENT = Path("/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal")
REPORT_PATH = ROOT / "Saved" / "Audit" / "arch_toon_missing_mi.json"

# Slot → (roughness, metallic, tint)
SLOT_PRESETS = {
    "stone":   (0.85, 0.0, None),
    "brick":   (0.80, 0.0, None),
    "trim":    (0.70, 0.0, None),
    "gold":    (0.35, 0.85, None),
    "worn":    (0.60, 0.15, None),
    "marble":  (0.25, 0.0, unreal.LinearColor((0.545, 0.627, 0.843, 1.0))),
    "glass":   (0.08, 0.0, unreal.LinearColor((0.545, 0.627, 0.843, 1.0))),
    "rose":    (0.55, 0.0, unreal.LinearColor((0.912, 0.627, 0.749, 1.0))),
    "default": (0.70, 0.0, None),
}
SOFT_BLUE = unreal.LinearColor((0.545, 0.627, 0.843, 1.0))
SOFT_PINK = unreal.LinearColor((0.912, 0.627, 0.749, 1.0))

def preset_for(slot_name: str) -> tuple[float, float, unreal.LinearColor | None]:
    s = slot_name.lower()
    for k, v in SLOT_PRESETS.items():
        if k in s:
            return v
    return SLOT_PRESETS["default"]

def ensure_dir(p: Path) -> bool:
    if not unreal.EditorAssetLibrary.does_directory_exist(str(p)):
        unreal.EditorAssetLibrary.make_directory(str(p))
        print(f"  Created dir: {p}")
        return True
    return False

def load_asset(p: Path):
    a = unreal.load_asset(str(p))
    if a is None:
        print(f"  WARN: failed to load {p}")
    return a

def save_asset(a) -> bool:
    if a and unreal.EditorAssetLibrary.can_save_asset(a.get_path_name()):
        return bool(unreal.EditorAssetLibrary.save_loaded_asset(a))
    return False

def slot_label(slot_name: str) -> str:
    """Sanitize a slot label into a valid MI name component."""
    out = []
    for ch in slot_name:
        if ch.isalnum() or ch == "_":
            out.append(ch)
        else:
            out.append("_")
    return "".join(out).strip("_")[:80]

def ensure_mi(slot_label: str, mi_dir: Path, dry_run: bool) -> tuple[unreal.MaterialInstanceConstant | None, Path, str]:
    """Create or load MI. Returns (mi, path, status)."""
    name = f"MI_Arch_{slot_label}"
    mi_path = mi_dir / name
    existing = load_asset(mi_path)
    if existing is not None:
        return existing, mi_path, "existing"
    if dry_run:
        return None, mi_path, "would_create"
    # Create new
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.MaterialInstanceConstantFactoryNew()
    mi = tools.create_asset(name, str(mi_dir), unreal.MaterialInstanceConstant, factory)
    if mi is None:
        return None, mi_path, "create_failed"
    parent_obj = load_asset(PARENT)
    if parent_obj is None:
        return None, mi_path, "parent_missing"
    mi.set_editor_property("parent", parent_obj)
    # Set scalar params
    rough, metal, tint = preset_for(slot_label)
    sca = unreal.MaterialEditingLibrary.get_scalar_parameter_names(parent_obj)
    vec = unreal.MaterialEditingLibrary.get_vector_parameter_names(parent_obj)
    for nm in ("Roughness", "Metallic"):
        v = float(rough) if nm == "Roughness" else float(metal)
        if nm in sca:
            try:
                unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, nm, v)
            except Exception as e:
                pass  # some params may not be settable via MEL
    if "TextureWeight" in sca:
        try:
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, "TextureWeight", 0.85)
        except Exception:
            pass
    if "ShadowDreamStrength" in sca:
        try:
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, "ShadowDreamStrength", 0.55)
        except Exception:
            pass
    # Set vector params (tint)
    if tint is not None:
        for nm in ("ShadowDreamTint", "ShadowFlowerColor"):
            if nm in vec:
                col = tint if nm == "ShadowDreamTint" else SOFT_PINK
                try:
                    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(mi, nm, col)
                except Exception:
                    pass
    status = "created" if save_asset(mi) else "save_failed"
    return mi, mi_path, status

def process_mesh(mesh_path: Path, mi_dir: Path, dry_run: bool) -> dict:
    mesh = load_asset(mesh_path)
    if mesh is None:
        return {"mesh": str(mesh_path), "status": "load_failed"}
    mats = mesh.get_editor_property("static_materials") or []
    changes: list[dict] = []
    for idx, sm in enumerate(mats):
        cur = sm.get_editor_property("material_interface")
        cur_path = cur.get_path_name() if cur is not None else ""
        slot_name = str(sm.get_editor_property("material_slot_name") or f"Slot{idx}")
        imported = str(sm.get_editor_property("imported_material_slot_name") or slot_name)
        key = imported or slot_name
        if "M_Master_Toon_Universal" in cur_path or "MI_Arch_" in cur_path:
            changes.append({"slot": slot_name, "action": "already_toon"})
            continue
        mi, mi_path, status = ensure_mi(slot_label(key), mi_dir, dry_run)
        if status in ("create_failed", "parent_missing", "save_failed"):
            changes.append({"slot": slot_name, "key": key, "action": status, "mi_path": str(mi_path)})
            continue
        if dry_run:
            changes.append({"slot": slot_name, "key": key, "action": "would_assign", "mi_path": str(mi_path)})
            continue
        mesh.set_material(idx, mi)
        changes.append({"slot": slot_name, "key": key, "action": "assigned", "mi_path": str(mi_path)})
    if not dry_run and changes:
        save_asset(mesh)
    return {"mesh": str(mesh_path), "status": "ok", "changes": changes}

def main() -> int:
    dry_run = "--dry-run" in sys.argv or ("--dry" in sys.argv and "--apply" not in sys.argv)
    apply_mode = not dry_run
    print(f"=== Arch MI creation: dry_run={dry_run}, apply={apply_mode} ===")
    # Ensure MI dirs
    for _, mi_dir in MI_ROOTS.items():
        ensure_dir(mi_dir)
    # Verify parent
    parent_obj = load_asset(PARENT)
    if parent_obj is None:
        print(f"[FATAL] Parent not found: {PARENT}")
        return 1
    print(f"Parent OK: {PARENT}")
    # Collect mesh paths (static meshes only)
    mesh_paths: list[Path] = []
    for label, root in MESH_ROOTS.items():
        if not unreal.EditorAssetLibrary.does_directory_exist(str(root)):
            print(f"  WARN: mesh root not found: {root}")
            continue
        for f in unreal.EditorAssetLibrary.list_assets(str(root), recursive=True):
            if f.endswith(".uasset"):
                mesh_paths.append(Path(f))
    print(f"Collected {len(mesh_paths)} mesh targets")
    # Process
    results: list[dict] = []
    counts = {"existing": 0, "created": 0, "assigned": 0, "already_toon": 0, "failed": 0}
    for mp in sorted(mesh_paths):
        mi_dir = MI_ROOTS["cathedral"] if "Cathedral" in str(mp) else MI_ROOTS["atlantis"]
        r = process_mesh(mp, mi_dir, dry_run)
        results.append(r)
        for ch in r.get("changes", []):
            act = ch.get("action", "")
            if act.startswith("assigned"):
                counts["assigned"] += 1
            elif act == "already_toon":
                counts["already_toon"] += 1
            elif act == "existing":
                counts["existing"] += 1
            elif act == "created":
                counts["created"] += 1
            elif act in ("create_failed", "save_failed", "parent_missing", "load_failed"):
                counts["failed"] += 1
        if (len(results) % 50) == 0:
            print(f"  Progress: {len(results)}/{len(mesh_paths)}")
    # Report
    report = {
        "timestamp": "2026-08-30T16:30+00:00",
        "dry_run": dry_run,
        "total_meshes": len(mesh_paths),
        "cathedral_meshes": sum(1 for mp in mesh_paths if "Cathedral" in str(mp)),
        "atlantis_meshes": sum(1 for mp in mesh_paths if "Atlantis" in str(mp)),
        "mi_counts": {
            "cathedral": len(list((MI_ROOTS["cathedral"]).glob("MI_Arch_*.uasset"))) if not dry_run else 0,
            "atlantis": len(list((MI_ROOTS["atlantis"]).glob("MI_Arch_*.uasset"))) if not dry_run else 0,
            "total_created": counts["created"],
        },
        "slot_changes": {
            "assigned": counts["assigned"],
            "already_toon": counts["already_toon"],
            "existing_mi": counts["existing"],
            "failed": counts["failed"],
        },
        "results": results,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"\n=== Report: {REPORT_PATH} ===")
    print(f"  Meshes processed: {len(mesh_paths)}")
    print(f"  MIs created: {counts['created']}")
    print(f"  MIs already existed: {counts['existing']}")
    print(f"  Slots assigned: {counts['assigned']}")
    print(f"  Slots already toon: {counts['already_toon']}")
    print(f"  Failures: {counts['failed']}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
