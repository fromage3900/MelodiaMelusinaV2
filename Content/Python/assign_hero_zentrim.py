"""Assign owner ZenTrim_Base4K onto hero prop meshes.

Closed-editor default is disk inventory (no Unreal spawn — A1 holds the editor).
In-editor apply:  py Content/Python/assign_hero_zentrim.py --apply

Does NOT:
  - treat Magicians T_Lantern_* as owner handpaint
  - use T_Hatch_Cross as the vow cross
  - create a cross mesh (FBX still missing)
  - launch UnrealEditor-Cmd
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTENT = PROJECT_ROOT / "Content"
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "hero_zentrim_assign.json"

MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal"
TRIM_FOLDER = "/Game/EnvSandbox/Materials/Instances/Environment/Stylized"
HERO_MI_NAME = "MI_ZenTrim_Base4K"
HERO_MI_PATH = f"{TRIM_FOLDER}/{HERO_MI_NAME}.{HERO_MI_NAME}"

# Canonical meshes. Magicians lantern is silhouette fallback only.
HERO_MESHES = {
    "wand": {
        "game": "/Game/EnvSandbox/Greybox_Kit/SM_Retopo_wand",
        "disk": CONTENT / "EnvSandbox" / "Greybox_Kit" / "SM_Retopo_wand.uasset",
        "assign": True,
    },
    "streetlamp": {
        "game": "/Game/Greybox_Kit/SM_SM_StreetLamp",
        "disk": CONTENT / "Greybox_Kit" / "SM_SM_StreetLamp.uasset",
        "assign": True,
    },
    "magicians_lantern": {
        "game": "/Game/Library/Migrated/MagiciansLibrary/Lantern/SM_Lantern",
        "disk": CONTENT / "Library" / "Migrated" / "MagiciansLibrary" / "Lantern" / "SM_Lantern.uasset",
        "assign": False,
        "note": "Marketplace silhouette only. Do not wire T_Lantern_*. Optional --include-magicians.",
    },
    "cross": {
        "game": "/Game/EnvSandbox/Greybox_Kit/StylizedCrossProp_FBX.StylizedCrossProp_FBX",
        "disk": CONTENT / "EnvSandbox" / "Greybox_Kit" / "StylizedCrossProp_FBX.uasset",
        "assign": True,
        "note": "Imported 2026-08-13 from G:\\stylizedcrossprop\\stylizedcrossprop_fromage39.zip (owner asset). Textures at /Game/EnvSandbox/Textures/cross_*. Never T_Hatch_Cross.",
    },
}

EXISTING_ZEN_MI = [
    CONTENT / "EnvSandbox" / "Materials" / "Instances" / "Environment" / "Stylized" / "MI_ZenTrim_Wet.uasset",
]
HATCH_FALSE_FRIEND = CONTENT / "Stylization" / "T_Hatch_Cross.uasset"
BASE4K_CHANNELS = ("Alpha", "BaseColor", "Displacement", "Emission", "Metallic", "Normal", "Roughness")


def _in_ue() -> bool:
    try:
        import unreal  # noqa: F401
        return True
    except ImportError:
        return False


def disk_inventory() -> dict:
    tex = CONTENT / "Textures"
    channels = {
        ch: (tex / f"ZenTrim_Base4K_{ch}.uasset").exists()
        for ch in BASE4K_CHANNELS
    }
    heroes = {}
    for key, spec in HERO_MESHES.items():
        disk = spec.get("disk")
        heroes[key] = {
            "game": spec.get("game"),
            "disk_exists": bool(disk and Path(disk).exists()),
            "disk": str(disk) if disk else None,
            "would_assign": spec.get("assign", False),
            "note": spec.get("note"),
        }
    mi_disk = CONTENT / "EnvSandbox" / "Materials" / "Instances" / "Environment" / "Stylized" / f"{HERO_MI_NAME}.uasset"
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "disk_inventory",
        "hero_mi": {
            "name": HERO_MI_NAME,
            "game": HERO_MI_PATH,
            "exists": mi_disk.exists(),
            "create_on_apply": not mi_disk.exists(),
        },
        "master": MASTER,
        "zen_trim_base4k_channels": channels,
        "existing_variation_mi_wet": EXISTING_ZEN_MI[0].exists(),
        "hatch_cross_false_friend": str(HATCH_FALSE_FRIEND) if HATCH_FALSE_FRIEND.exists() else None,
        "heroes": heroes,
        "cathedral_kit_fbx": len(list((PROJECT_ROOT / "KitbashExport" / "CathedralKit").glob("*.fbx")))
        if (PROJECT_ROOT / "KitbashExport" / "CathedralKit").is_dir()
        else 0,
        "notes": [
            "No MI_ZenTrim_Base4K on disk — create on --apply.",
            "Closest live MI is MI_ZenTrim_Wet (Base4K + Wet overlay).",
            "Do not spawn UnrealEditor-Cmd; A1 owns the editor slot.",
        ],
    }


def ensure_hero_mi():
    import material_lib as lib
    import unreal
    import zen_trim_textures as zt

    if not unreal.EditorAssetLibrary.does_asset_exist(MASTER):
        raise RuntimeError(f"Missing master: {MASTER}")
    inst = lib.create_material_instance(HERO_MI_NAME, TRIM_FOLDER, MASTER)
    profiles = lib.create_toon_profiles(["TP_Stone"])
    stone = profiles.get("TP_Stone")
    if stone:
        lib.set_instance_toon_profile(inst, stone)
    lib.set_instance_scalar(inst, "LayerBlend", 0.0)
    lib.set_instance_scalar(inst, "TextureWeight", 1.0)
    wired = zt.apply_zen_trim_layers(inst, "Base4K", "Base4K")
    lib.save_package(inst)
    return {"path": HERO_MI_PATH, "textures": wired}


def assign_static_mesh_material(mesh_path: str, mi_path: str) -> dict:
    import unreal

    sm = unreal.EditorAssetLibrary.load_asset(mesh_path)
    mi = unreal.EditorAssetLibrary.load_asset(mi_path)
    if not sm:
        return {"mesh": mesh_path, "ok": False, "error": "mesh_missing"}
    if not mi:
        return {"mesh": mesh_path, "ok": False, "error": "mi_missing"}
    materials = list(sm.get_editor_property("static_materials") or [])
    if not materials:
        return {"mesh": mesh_path, "ok": False, "error": "no_slots"}
    before = []
    for i, slot in enumerate(materials):
        cur = slot.get_editor_property("material_interface")
        before.append(str(cur.get_path_name()) if cur else None)
        if i == 0:
            slot.set_editor_property("material_interface", mi)
    sm.set_editor_property("static_materials", materials)
    unreal.EditorAssetLibrary.save_asset(mesh_path)
    return {"mesh": mesh_path, "ok": True, "slots_before": before, "slot0_after": mi_path}


def apply(include_magicians: bool) -> dict:
    created = ensure_hero_mi()
    assigned = []
    for key, spec in HERO_MESHES.items():
        if not spec.get("game"):
            assigned.append({"hero": key, "skipped": spec.get("note")})
            continue
        do = spec.get("assign") or (key == "magicians_lantern" and include_magicians)
        if not do:
            assigned.append({"hero": key, "skipped": spec.get("note")})
            continue
        assigned.append({"hero": key, **assign_static_mesh_material(spec["game"], HERO_MI_PATH)})
    return {"created_or_updated_mi": created, "assigned": assigned}


def main() -> int:
    parser = argparse.ArgumentParser(description="ZenTrim hero MI inventory / assign")
    parser.add_argument("--apply", action="store_true", help="In-editor only. Create MI and assign slot 0.")
    parser.add_argument("--include-magicians", action="store_true", help="Also assign MI onto Magicians SM_Lantern (maps stay unused).")
    args = parser.parse_args()

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    payload = disk_inventory()
    if args.apply:
        if not _in_ue():
            payload["apply_error"] = "Not in Unreal Python. Run inside the already-open editor; do not spawn a second UnrealEditor."
            REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            print(json.dumps(payload, indent=2))
            return 2
        payload["mode"] = "apply"
        payload["apply"] = apply(args.include_magicians)
    REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
