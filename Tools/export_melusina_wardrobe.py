# -*- coding: utf-8 -*-
"""Export a Wardrobe_<OutfitId> pack to Exports/MelusinaClothes/<id>/.

Gameplay contract (plan of record — do NOT import V2Test ARP statics):
  Every piece must be a SKELETAL mesh skinned to SK_Melusina_Skeleton
  (465 bones, underscore names, centimeters). Slot components
  SetLeaderPoseComponent(bodyMesh). Retarget risk: zero.
  Docs/MELODIA_WARDROBE_PLUGIN_PLAN_2026-08-07.md
  Saved/Audit/melusina_idle_retarget_rca_2026-08-13.md

This script writes FBX + sidecar only. It does not open Unreal, does not
import, and does not touch SK_Melusina / ABP / locomotion / hair.

Run:
  blender KitbashExport/Melodia_Portfolio_Stage_v4.blend -b -P Tools/export_melusina_wardrobe.py -- --outfit-id <OutfitId>
  blender ... -P Tools/export_melusina_wardrobe.py -- --outfit-id demo --include-armature

Pass --require-live-skeleton to fail the export when character_rig still
has dotted ARP names or a bone count other than 465.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from melodia_stage_paths import EXPORTS_CLOTHES, resolve_stage_blend  # noqa: E402
from melusina_anim_unit_guard import live_skeleton_preflight  # noqa: E402

# Checked-in FBX export contract for Melusina wardrobe → UE
FBX_EXPORT_KWARGS = {
    "use_selection": True,
    "use_visible": True,
    "use_active_collection": False,
    "global_scale": 1.0,
    "apply_unit_scale": True,
    "apply_scale_options": "FBX_SCALE_ALL",
    "use_space_transform": True,
    "bake_space_transform": False,
    "object_types": {"ARMATURE", "MESH"},
    "use_mesh_modifiers": True,
    "use_mesh_modifiers_render": True,
    "mesh_smooth_type": "FACE",
    "use_subsurf": False,
    "use_mesh_edges": False,
    "use_tspace": True,
    "use_custom_props": False,
    "add_leaf_bones": False,
    "primary_bone_axis": "Y",
    "secondary_bone_axis": "X",
    "use_armature_deform_only": True,
    "armature_nodetype": "NULL",
    "bake_anim": False,
    "path_mode": "AUTO",
    "embed_textures": False,
    "batch_mode": "OFF",
    "axis_forward": "-Z",
    "axis_up": "Y",
}


def log(msg: str) -> None:
    print(f"[wardrobe-export] {msg}", flush=True)


def _argv() -> list[str]:
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1 :]
    return []


def wardrobe_rig_preflight(bone_names: list[str]) -> dict:
    """Closed-editor check: live SK is 465 underscore bones, not dotted ARP."""
    return live_skeleton_preflight(bone_names)


def parse_args() -> tuple[str, bool, bool, bool, bool, str | None]:
    args = _argv()
    outfit_id = None
    include_arm = "--include-armature" in args
    no_open = "--no-open" in args
    require_live = "--require-live-skeleton" in args
    v2 = "--v2" in args
    collection_override = None
    if "--outfit-id" in args:
        i = args.index("--outfit-id")
        if i + 1 < len(args):
            outfit_id = args[i + 1].strip()
    if "--collection" in args:
        i = args.index("--collection")
        if i + 1 < len(args):
            collection_override = args[i + 1].strip()
    if not outfit_id:
        raise SystemExit(
            "usage: --outfit-id <OutfitId> [--include-armature] [--no-open] "
            "[--require-live-skeleton] [--v2] [--collection <Collection>]"
        )
    # sanitize id for paths
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in outfit_id)
    return safe, include_arm, no_open, require_live, v2, collection_override


def find_character_rig() -> bpy.types.Object | None:
    for name in ("character_rig", "melusina_character_rig", "Armature"):
        ob = bpy.data.objects.get(name)
        if ob and ob.type == "ARMATURE":
            return ob
    mel = bpy.data.collections.get("Asset_melusina")
    if mel:
        for o in mel.all_objects:
            if o.type == "ARMATURE":
                return o
    return None


def mesh_sidecar_row(obj: bpy.types.Object) -> dict:
    arm = obj.find_armature()
    mats = [s.material.name if s.material else None for s in obj.material_slots]
    return {
        "name": obj.name,
        "vertices": len(obj.data.vertices) if obj.data else 0,
        "vertex_groups": len(obj.vertex_groups) if obj.vertex_groups else 0,
        "materials": mats,
        "armature": arm.name if arm else None,
        "bound_to_character_rig": bool(arm and "character_rig" in arm.name.lower()),
    }


def main() -> int:
    outfit_id, include_arm, no_open, require_live, v2, collection_override = parse_args()
    stage = resolve_stage_blend()
    if not no_open:
        cur = Path(bpy.data.filepath or "")
        if cur.resolve() != stage.resolve():
            if not stage.is_file():
                log(f"FATAL missing stage {stage}")
                return 2
            log(f"opening {stage}")
            bpy.ops.wm.open_mainfile(filepath=str(stage))

    coll_name = collection_override or ("Wardrobe_V2" if v2 else f"Wardrobe_{outfit_id}")
    coll = bpy.data.collections.get(coll_name)
    if coll is None:
        # case-insensitive search
        for c in bpy.data.collections:
            if c.name.lower() == coll_name.lower():
                coll = c
                coll_name = c.name
                break
    if coll is None:
        log(f"FATAL missing collection {coll_name}")
        return 2

    meshes = [o for o in coll.all_objects if o.type == "MESH" and o.data]
    if not meshes:
        log(f"FATAL no meshes in {coll_name}")
        return 2

    rig = find_character_rig()
    unbound = [o.name for o in meshes if o.find_armature() is None]
    if unbound:
        log(f"WARN meshes with no armature modifier/parent: {unbound}")

    # Hair / Water (Advance) must never ride this export
    for o in meshes:
        for s in o.material_slots:
            if s.material and s.material.name == "Water (Advance)":
                log(f"FATAL {o.name} has Water (Advance) — refuse hair on wardrobe export")
                return 3

    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.hide_set(False)
        o.hide_viewport = False
        o.select_set(True)
    exported_arm = None
    if include_arm and rig:
        rig.hide_set(False)
        rig.select_set(True)
        exported_arm = rig.name
        log(f"include armature {rig.name}")
    elif include_arm and not rig:
        log("WARN --include-armature but character_rig not found")

    out_dir = EXPORTS_CLOTHES / ("V2" if v2 else outfit_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    fbx_name = f"SK_Melusina_V2_{outfit_id}.fbx" if v2 else f"SK_Melusina_{outfit_id}.fbx"
    fbx_path = out_dir / fbx_name
    kwargs = dict(FBX_EXPORT_KWARGS)
    kwargs["filepath"] = str(fbx_path)
    bpy.ops.export_scene.fbx(**kwargs)

    if not fbx_path.is_file() or fbx_path.stat().st_size < 100:
        log(f"FATAL empty FBX {fbx_path}")
        return 1

    bone_names = []
    if rig and rig.data:
        bone_names = [b.name for b in rig.data.bones]
    rig_preflight = wardrobe_rig_preflight(bone_names)
    if not rig_preflight["ok"]:
        for err in rig_preflight["errors"]:
            log(f"PREFLIGHT {'FATAL' if require_live else 'WARN'} {err}")
        if require_live:
            return 1

    sidecar = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "export_melusina_wardrobe.py",
        "outfit_id": outfit_id,
        "collection": coll_name,
        "stage_blend": str(Path(bpy.data.filepath or stage)),
        "fbx": str(fbx_path),
        "fbx_bytes": fbx_path.stat().st_size,
        "include_armature": include_arm,
        "exported_armature": exported_arm,
        "character_rig": rig.name if rig else None,
        "character_rig_bone_count": len(bone_names),
        "live_skeleton_preflight": rig_preflight,
        "ue_landing_hint": (
            f"/Game/Melodia/Characters/Melusina/Outfits/V2/" if v2
            else f"/Game/Melodia/Characters/Melusina/Outfits/{outfit_id}/"
        ),
        "fbx_settings": {k: (list(v) if isinstance(v, set) else v) for k, v in FBX_EXPORT_KWARGS.items()},
        "meshes": [mesh_sidecar_row(o) for o in meshes],
        "unbound_meshes": unbound,
    }
    side_path = out_dir / f"{fbx_path.stem}.json"
    side_path.write_text(json.dumps(sidecar, indent=2) + "\n", encoding="utf-8")
    log(f"wrote {fbx_path} ({fbx_path.stat().st_size} bytes)")
    log(f"wrote {side_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
