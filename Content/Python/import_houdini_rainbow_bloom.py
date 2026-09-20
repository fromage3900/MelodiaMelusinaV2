"""Import the hython-cooked RainbowBloom OBJ into L_MelusinaMorning and place it at the pond centroid.

Does not touch the proven PCG field. Tagged WorldCompiler.houdini_rainbow_bloom.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import unreal

OBJ = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Houdini/RainbowBloom/RainbowBloom_3900.obj"
HDA = "C:/EnvironmentPortfolio/BS_GodFile/hda/RainbowBloom_1.0.hda"
DEST = "/Game/Melodia/WorldCompiler/Houdini"
ASSET = f"{DEST}/SM_RainbowBloom_Houdini3900"
ANCHOR = unreal.Vector(-950.0, 2300.0, -611.0)
TAG = "WorldCompiler.houdini_rainbow_bloom"
LABEL = "Houdini_RainbowBloom_3900"
OUT = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/houdini_rainbow_bloom_ue_2026-09-17.json"

AL = unreal.EditorAssetLibrary
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
rec = {"schema": "melodia.houdini_rainbow_bloom_ue.v1", "recorded_at_utc": datetime.now(timezone.utc).isoformat()}


def _import_obj() -> str | None:
    if not AL.does_directory_exist(DEST):
        AL.make_directory(DEST)
    if AL.does_asset_exist(ASSET):
        rec["imported"] = "existed"
        return ASSET
    task = unreal.AssetImportTask()
    task.filename = OBJ
    task.destination_path = DEST
    task.destination_name = "SM_RainbowBloom_Houdini3900"
    task.replace_existing = True
    task.automated = True
    task.save = True
    try:
        task.factory = unreal.ObjFactory()
    except Exception:
        rec["obj_factory"] = "missing; trying Interchange"
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    rec["import_imported"] = [str(x) for x in (task.imported_object_paths or [])]
    if AL.does_asset_exist(ASSET):
        rec["imported"] = "created"
        return ASSET
    # Interchange sometimes names from the file
    alt = f"{DEST}/RainbowBloom_3900"
    if AL.does_asset_exist(alt):
        rec["imported"] = "created_alt"
        rec["asset_alt"] = alt
        return alt
    rec["imported"] = "missing"
    return None


def _place(path: str) -> dict:
    mesh = AL.load_asset(path)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    # remove prior
    removed = 0
    for a in EAS.get_all_level_actors():
        if a.get_actor_label() == LABEL or TAG in [str(t) for t in a.tags]:
            EAS.destroy_actor(a)
            removed += 1
    act = EAS.spawn_actor_from_class(unreal.StaticMeshActor, ANCHOR, unreal.Rotator(0, 0, 0))
    act.set_actor_label(LABEL)
    act.tags = [TAG]
    # Houdini metres -> UE centimetres
    act.set_actor_scale3d(unreal.Vector(100.0, 100.0, 100.0))
    c = act.get_component_by_class(unreal.StaticMeshComponent)
    c.set_static_mesh(mesh)
    c.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
    # vertex colors carry the rainbow Cd
    try:
        c.set_editor_property("use_default_collision", True)
    except Exception:
        pass
    return {"label": LABEL, "removed_prior": removed, "location": [ANCHOR.x, ANCHOR.y, ANCHOR.z], "scale": 100, "mesh": path}


def _try_houdini_engine() -> dict:
    out = {"houdini_asset_class": hasattr(unreal, "HoudiniAsset"), "hda_exists": os.path.exists(HDA)}
    if not hasattr(unreal, "HoudiniAssetActor"):
        out["engine"] = "HoudiniAssetActor missing (plugin not compiled into this editor)"
        return out
    out["HoudiniAssetActor"] = True
    try:
        api = getattr(unreal, "HoudiniPublicAPI", None)
        out["public_api"] = api is not None
    except Exception as e:
        out["public_api_error"] = str(e)[:200]
    return out


rec["obj_exists"] = os.path.exists(OBJ)
rec["obj_bytes"] = os.path.getsize(OBJ) if rec["obj_exists"] else 0
path = _import_obj() if rec["obj_exists"] else None
rec["asset"] = path
if path:
    rec["placed"] = _place(path)
rec["houdini_engine"] = _try_houdini_engine()
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
rec["level"] = world.get_path_name() if world else None
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="utf-8").write(json.dumps(rec, indent=2, default=str))
unreal.log(json.dumps({k: rec[k] for k in ("imported", "asset", "placed", "houdini_engine") if k in rec}, indent=1, default=str))
