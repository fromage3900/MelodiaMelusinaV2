"""Apply manifest entry to the studio swatch + backdrop actors."""
from __future__ import annotations

from typing import Any

import mi_preview_studio as studio


def _find_actor_by_label(eas, label: str):
    for actor in eas.get_all_level_actors() or []:
        if actor.get_actor_label() == label:
            return actor
    return None


def _find_actor_by_tag(eas, tag: str):
    for actor in eas.get_all_level_actors() or []:
        if tag in list(getattr(actor, "tags", []) or []):
            return actor
    return None


def apply_backdrop(eas, backdrop_key: str) -> dict:
    import unreal

    actor = (
        _find_actor_by_tag(eas, studio.TAG_BACKDROP)
        or _find_actor_by_label(eas, "Backdrop_MelodiaVoid")
        or _find_actor_by_label(eas, "Backdrop_Cyclorama")
    )
    if not actor:
        return {"ok": False, "error": "backdrop_missing"}
    key = backdrop_key or studio.DEFAULT_BACKDROP
    mi_path = studio.BACKDROP_MIS.get(key, studio.BACKDROP_MIS[studio.DEFAULT_BACKDROP])
    if not unreal.EditorAssetLibrary.does_asset_exist(mi_path):
        return {"ok": False, "error": f"backdrop_mi_missing:{mi_path}"}
    actor.static_mesh_component.set_material(0, unreal.load_asset(mi_path))
    return {"ok": True, "backdrop": key, "mi": mi_path}


def apply_swatch(eas, entry: dict[str, Any]) -> dict:
    import unreal

    actor = _find_actor_by_tag(eas, studio.TAG_SWATCH) or _find_actor_by_label(eas, "MI_Preview_Swatch")
    if not actor:
        return {"ok": False, "error": "swatch_missing"}

    preview_mesh = str(entry.get("preview_mesh") or "sphere")
    mesh_path = studio.PREVIEW_MESHES.get(preview_mesh, studio.SPHERE)
    mesh = unreal.load_asset(mesh_path)
    if not mesh:
        return {"ok": False, "error": f"mesh_missing:{mesh_path}"}

    rot = studio.mesh_rotation(preview_mesh)
    actor.set_actor_rotation(studio.ue_rotator(rot), False)
    scale = entry.get("mesh_scale") or list(studio.default_mesh_scale(preview_mesh))
    actor.set_actor_scale3d(unreal.Vector(float(scale[0]), float(scale[1]), float(scale[2])))

    sm = actor.static_mesh_component
    # Editor-created preview actors can retain a transient hidden flag after a
    # level reload.  Reassert visibility before assigning the material so the
    # still path cannot silently capture only the backdrop.
    try:
        actor.set_actor_hidden_in_game(False)
        actor.set_is_temporarily_hidden_in_editor(False)
        sm.set_visibility(True)
        sm.set_hidden_in_game(False)
    except Exception:
        pass
    sm.set_static_mesh(mesh)

    asset_path = str(entry.get("asset_path") or "")
    if not unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        return {"ok": False, "error": f"mi_missing:{asset_path}"}
    mi = unreal.load_asset(asset_path)
    sm.set_material(0, mi)
    # StaticMeshComponent material overrides are editor-side state.  Explicitly
    # invalidate the render state so a subsequent SceneCapture cannot reuse the
    # previous MI for every plate in a batch.
    try:
        sm.mark_render_state_dirty()
    except Exception:
        pass
    try:
        flush = getattr(unreal.SystemLibrary, "flush_rendering_commands", None)
        if callable(flush):
            flush()
    except Exception:
        pass
    return {"ok": True, "mi": asset_path, "preview_mesh": preview_mesh}


def apply_set_dress(eas, entry: dict[str, Any]) -> dict:
    """Show trim card for cloth/trim plates; keep pedestal + hydro soft always."""
    import unreal

    mi_id = str(entry.get("id") or "")
    preview_mesh = str(entry.get("preview_mesh") or "sphere")
    show_trim = preview_mesh == "plane_vertical" or "Trim" in mi_id or "Cloth" in mi_id

    trim = _find_actor_by_tag(eas, studio.TAG_TRIM_CARD) or _find_actor_by_label(
        eas, studio.TAG_TRIM_CARD
    )
    if trim:
        trim.set_actor_hidden_in_game(not show_trim)
        try:
            trim.set_is_temporarily_hidden_in_editor(not show_trim)
        except Exception:
            pass
    return {"trim_visible": show_trim}


def apply_preview_entry(entry: dict[str, Any]) -> dict:
    import unreal

    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    backdrop = apply_backdrop(eas, str(entry.get("backdrop") or studio.DEFAULT_BACKDROP))
    # Fallback: if tint MI missing, use canonical void
    if not backdrop.get("ok") and "backdrop_mi_missing" in str(backdrop.get("error") or ""):
        backdrop = apply_backdrop(eas, studio.DEFAULT_BACKDROP)
    swatch = apply_swatch(eas, entry)
    dress = apply_set_dress(eas, entry)
    return {"backdrop": backdrop, "swatch": swatch, "set_dress": dress, "id": entry.get("id")}
