# -*- coding: utf-8 -*-
"""Apply Melusina AAA water-hair product in the already-open editor.

Product:
  Geometry Cache  = hair BODY (Flip globules, character-space ABC)
  Niagara Melusina_WaterFX / WaterSplashEmitter = drip
  SK_MelusinaHair + ABP_Melusina_WaterHair = fallback silhouette (hidden when GC is live)

Attach (Decision 010 / 026): sibling GeometryCacheComponent on BP_Melusina,
socketed to head_x with relative transform = inverse of head_x composed bind pose.
Do not parent GC to head_x without the inverse. Do not add a compensation component.

Does not launch UnrealEditor. Does not start Flip.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import unreal

PROJECT_ROOT = Path(unreal.Paths.project_dir()).resolve()
BP_PATH = "/Game/Melodia/Characters/Melusina/BP_Melusina"
BODY_MESH = "/Game/Melodia/Characters/Melusina/SK_Melusina"
GC_ASSET = "/Game/Cinematics/MelusinaWaterHair/GC_MelusinaHairFlip_v22"
WATERFX_PATH = "/Game/Melodia/VFX/Melusina_WaterFX"
HEAD_BONE = "head_x"
GC_COMP_NAME = "WaterHairFlipCache"
FX_COMP_NAME = "WaterHairDripFX"
AUDIT_PATH = PROJECT_ROOT / "Saved" / "Audit" / "melusina_aaa_hair_today.json"


def _log(msg: str) -> None:
    line = f"[aaa-hair] {msg}"
    unreal.log(line)
    print(line, flush=True)


def _prop(obj, name, default=None):
    try:
        return obj.get_editor_property(name)
    except Exception:
        return default


def _parent_index(ref, idx: int) -> int:
    for name in ("get_parent_index", "get_parent_bone_index"):
        fn = getattr(ref, name, None)
        if callable(fn):
            try:
                return int(fn(idx))
            except Exception:
                continue
    info_fn = getattr(ref, "get_ref_bone_info", None)
    if callable(info_fn):
        try:
            info = info_fn()[idx]
            parent = _prop(info, "parent_index")
            if parent is not None:
                return int(parent)
        except Exception:
            pass
    return -1


def composed_head_bind(skel_mesh) -> tuple[unreal.Transform, int]:
    """Component-space head bind pose (UE 5.8: AnimPose WORLD == composed ref)."""
    skeleton = skel_mesh.skeleton
    if skeleton is None:
        raise RuntimeError(f"{skel_mesh.get_path_name()} has no skeleton")
    pose = skeleton.get_reference_pose()
    names = [str(n) for n in pose.get_bone_names()]
    if HEAD_BONE not in names:
        raise RuntimeError(f"{skel_mesh.get_path_name()} has no {HEAD_BONE}")
    bind = pose.get_bone_pose(HEAD_BONE, unreal.AnimPoseSpaces.WORLD)
    return bind, names.index(HEAD_BONE)


def _gather(bp):
    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    library = unreal.SubobjectDataBlueprintFunctionLibrary
    handles = list(subsystem.k2_gather_subobject_data_for_blueprint(bp))
    rows = []
    for handle in handles:
        obj = library.get_object(library.get_data(handle))
        rows.append((handle, obj))
    return subsystem, library, rows


def _find_named(rows, cls, names: tuple[str, ...]):
    for handle, obj in rows:
        if obj is None:
            continue
        if not isinstance(obj, cls):
            continue
        if obj.get_name() in names:
            return handle, obj
    return None, None


def _find_class(rows, cls):
    found = []
    for handle, obj in rows:
        if obj is not None and isinstance(obj, cls):
            found.append((handle, obj))
    return found


def _socket_to_head(child, parent, relative: unreal.Transform) -> None:
    """UE 5.8 templates do not expose attach_socket_name as an editor property."""
    child.k2_attach_to(
        parent, unreal.Name(HEAD_BONE), unreal.AttachLocation.KEEP_RELATIVE_OFFSET, True
    )
    child.set_relative_transform(relative, False, False)
    child.set_hidden_in_game(False)


def ensure_gc_component(bp, cache_asset, inverse: unreal.Transform) -> str:
    subsystem, library, rows = _gather(bp)
    mesh_handle, mesh_obj = _find_named(
        rows, unreal.SkeletalMeshComponent, ("CharacterMesh0", "Mesh")
    )
    existing = _find_class(rows, unreal.GeometryCacheComponent)
    for handle, obj in existing:
        if GC_COMP_NAME in obj.get_name() or _prop(obj, "geometry_cache") == cache_asset:
            obj.set_editor_property("geometry_cache", cache_asset)
            _socket_to_head(obj, mesh_obj or obj.get_attach_parent(), inverse)
            return "already_present"

    mesh_handle, mesh_obj = _find_named(
        rows, unreal.SkeletalMeshComponent, ("CharacterMesh0", "Mesh")
    )
    if mesh_handle is None:
        skels = _find_class(rows, unreal.SkeletalMeshComponent)
        # Prefer non-hair body mesh.
        for handle, obj in skels:
            if "hair" not in obj.get_name().lower():
                mesh_handle, mesh_obj = handle, obj
                break
        if mesh_handle is None and skels:
            mesh_handle, mesh_obj = skels[0]
    if mesh_handle is None:
        mesh_handle = rows[0][0]

    params = unreal.AddNewSubobjectParams(
        parent_handle=mesh_handle,
        new_class=unreal.GeometryCacheComponent,
        blueprint_context=bp,
    )
    new_handle, failure = subsystem.add_new_subobject(params)
    if not failure.is_empty():
        raise RuntimeError(f"Could not add GeometryCacheComponent: {failure}")
    subsystem.rename_subobject(new_handle, unreal.Text(GC_COMP_NAME))
    obj = library.get_object(library.get_data(new_handle))
    obj.set_editor_property("geometry_cache", cache_asset)
    _socket_to_head(obj, mesh_obj or obj.get_attach_parent(), inverse)
    _log(f"parented GC under {mesh_obj.get_name() if mesh_obj else 'root'} socket={HEAD_BONE}")
    return "added"


def ensure_niagara_component(bp, ns) -> str:
    subsystem, library, rows = _gather(bp)
    niagara_cls = getattr(unreal, "NiagaraComponent", None)
    if niagara_cls is None:
        return "niagara_component_class_missing"
    mesh_handle, mesh_obj = _find_named(
        rows, unreal.SkeletalMeshComponent, ("CharacterMesh0", "Mesh")
    )
    existing = _find_class(rows, niagara_cls)
    for handle, obj in existing:
        if FX_COMP_NAME in obj.get_name():
            try:
                obj.set_editor_property("asset", ns)
            except Exception:
                pass
            _socket_to_head(obj, mesh_obj or obj.get_attach_parent(), unreal.Transform())
            return "already_present"

    if mesh_handle is None:
        mesh_handle = rows[0][0]
    params = unreal.AddNewSubobjectParams(
        parent_handle=mesh_handle,
        new_class=niagara_cls,
        blueprint_context=bp,
    )
    new_handle, failure = subsystem.add_new_subobject(params)
    if not failure.is_empty():
        raise RuntimeError(f"Could not add NiagaraComponent: {failure}")
    subsystem.rename_subobject(new_handle, unreal.Text(FX_COMP_NAME))
    obj = library.get_object(library.get_data(new_handle))
    try:
        obj.set_editor_property("asset", ns)
    except Exception as exc:
        _log(f"WARN could not set Niagara asset: {exc}")
    _socket_to_head(obj, mesh_obj or obj.get_attach_parent(), unreal.Transform())
    return "added"


def hide_sk_hair(bp) -> list[str]:
    _subsystem, _library, rows = _gather(bp)
    hidden = []
    hair_cls = getattr(unreal, "MelodiaHairComponent", unreal.SkeletalMeshComponent)
    for _handle, obj in rows:
        if obj is None:
            continue
        is_hair = isinstance(obj, hair_cls) and obj.get_class().get_name() == "MelodiaHairComponent"
        mesh = _prop(obj, "skeletal_mesh_asset") or _prop(obj, "skeletal_mesh")
        mesh_path = mesh.get_path_name() if mesh else ""
        if is_hair or "SK_MelusinaHair" in mesh_path:
            try:
                obj.set_editor_property("hidden_in_game", True)
            except Exception:
                pass
            try:
                obj.set_editor_property("visible", False)
            except Exception:
                pass
            hidden.append(obj.get_name())
    return hidden


def main() -> dict:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "apply_melusina_aaa_hair_today.py",
        "ok": False,
        "project": str(PROJECT_ROOT),
    }

    # 1. Import Geometry Cache (1–240).
    import import_hair_flip_geometry_cache as gc_import

    import_rc = gc_import.main()
    payload["import_rc"] = import_rc
    cache = unreal.load_asset(GC_ASSET)
    payload["gc_class"] = cache.get_class().get_name() if cache else None
    if cache is None:
        payload["error"] = "geometry_cache_missing_after_import"
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        AUDIT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(payload, indent=2), flush=True)
        return payload

    body = unreal.load_asset(BODY_MESH)
    if body is None:
        payload["error"] = f"missing {BODY_MESH}"
        AUDIT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(payload, indent=2), flush=True)
        return payload

    bind, head_idx = composed_head_bind(body)
    inverse = bind.inverse()
    payload["head_x_index"] = head_idx
    payload["head_bind_loc"] = [bind.translation.x, bind.translation.y, bind.translation.z]
    payload["inverse_loc"] = [
        inverse.translation.x,
        inverse.translation.y,
        inverse.translation.z,
    ]

    bp = unreal.load_asset(BP_PATH)
    if bp is None:
        payload["error"] = f"missing {BP_PATH}"
        AUDIT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(payload, indent=2), flush=True)
        return payload

    payload["gc_component"] = ensure_gc_component(bp, cache, inverse)
    ns = unreal.load_asset(WATERFX_PATH)
    payload["niagara_loaded"] = bool(ns)
    if ns:
        payload["niagara_component"] = ensure_niagara_component(bp, ns)
        try:
            import set_melusina_waterfx as waterfx

            payload["waterfx_preset"] = waterfx.apply_preset("subtle_drip", save=True)
        except Exception as exc:
            payload["waterfx_preset_error"] = str(exc)
    else:
        payload["niagara_component"] = "waterfx_asset_missing"

    payload["sk_hair_hidden"] = hide_sk_hair(bp)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    pkg = bp.get_package()
    saved = bool(unreal.EditorLoadingAndSavingUtils.save_packages([pkg], False))
    payload["saved"] = saved
    if not saved:
        payload["error"] = f"could not save {BP_PATH} (check file read-only)"
    else:
        payload["ok"] = payload.get("gc_class") == "GeometryCache" and bool(
            payload.get("sk_hair_hidden") or payload.get("gc_component")
        )
        if payload["gc_class"] != "GeometryCache":
            payload["ok"] = False
            payload["error"] = f"imported class is {payload['gc_class']}, not GeometryCache"

    payload["note"] = (
        "GC is cine hair body on head_x + inverse bind. "
        "Niagara drip on head_x identity. SK hair hidden in-game, kept on disk."
    )
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    _log(f"audit → {AUDIT_PATH} ok={payload['ok']}")
    print(json.dumps(payload, indent=2, default=str), flush=True)
    return payload


if __name__ == "__main__":
    result = main()
    if not result.get("ok"):
        sys.exit(1)
