"""Shared scene integration — UDS actors, post-process outline stack."""
from __future__ import annotations

UDS_ROOT = "/Game/UltraDynamicSky"
UDS_SKY_BP = f"{UDS_ROOT}/Blueprints/Ultra_Dynamic_Sky"
UDS_WEATHER_BP = f"{UDS_ROOT}/Blueprints/Ultra_Dynamic_Weather"
TAG_UDS_SKY = "UDS_Sky"
TAG_UDS_WEATHER = "UDS_Weather"

PP_OUTLINE = "/Game/EnvSandbox/Materials/PostProcess/M_PP_ToonOutline.M_PP_ToonOutline"
PP_VINES = "/Game/EnvSandbox/Materials/PostProcess/M_PP_StorybookVines.M_PP_StorybookVines"
PP_VINES_INST = "/Game/EnvSandbox/Materials/PostProcess/M_PP_StorybookVines_Inst.M_PP_StorybookVines_Inst"


def _load_bp_class(asset_path: str):
    import unreal

    if not unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        return None
    bp = unreal.load_asset(asset_path)
    if not bp:
        return None
    try:
        return bp.generated_class()
    except Exception:
        pass
    try:
        return unreal.load_class(None, f"{asset_path}_C")
    except Exception:
        return None


def _set_tag(actor, tag: str) -> None:
    try:
        tags = list(actor.tags)
        if tag not in tags:
            tags.append(tag)
            actor.tags = tags
    except Exception:
        pass


def _find_actor_by_tag(eas, tag: str):
    for actor in eas.get_all_level_actors() or []:
        tags = list(getattr(actor, "tags", []) or [])
        if tag in tags:
            return actor
    return None


def ensure_uds_actors(eas, *, time_of_day: float = 1750.0, spawn_weather: bool = True) -> dict:
    """Spawn or refresh Ultra Dynamic Sky (+ optional weather) in the level."""
    import unreal

    result: dict = {"sky": None, "weather": None, "spawned": []}
    sky_cls = _load_bp_class(f"{UDS_SKY_BP}.Ultra_Dynamic_Sky")
    if not sky_cls:
        result["error"] = "uds_sky_bp_missing"
        return result

    sky = _find_actor_by_tag(eas, TAG_UDS_SKY)
    if not sky:
        sky = eas.spawn_actor_from_class(sky_cls, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
        if sky:
            sky.set_actor_label("Ultra_Dynamic_Sky")
            _set_tag(sky, TAG_UDS_SKY)
            result["spawned"].append("sky")
    result["sky"] = sky.get_actor_label() if sky else None

    if sky:
        for prop, val in (("Time of Day", float(time_of_day)), ("Animate Time of Day", False)):
            try:
                sky.set_editor_property(prop, val)
            except Exception:
                pass

    if spawn_weather:
        weather_cls = _load_bp_class(f"{UDS_WEATHER_BP}.Ultra_Dynamic_Weather")
        if weather_cls:
            weather = _find_actor_by_tag(eas, TAG_UDS_WEATHER)
            if not weather:
                weather = eas.spawn_actor_from_class(
                    weather_cls, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)
                )
                if weather:
                    weather.set_actor_label("Ultra_Dynamic_Weather")
                    _set_tag(weather, TAG_UDS_WEATHER)
                    result["spawned"].append("weather")
            result["weather"] = weather.get_actor_label() if weather else None

    return result


def disable_manual_sun_if_uds(eas) -> bool:
    """Hide duplicate directional light when UDS sky is present."""
    import unreal

    if not _find_actor_by_tag(eas, TAG_UDS_SKY):
        return False
    changed = False
    for actor in eas.get_all_level_actors() or []:
        if isinstance(actor, unreal.DirectionalLight):
            try:
                actor.set_actor_hidden_in_game(True)
                actor.set_is_temporarily_hidden_in_editor(True)
                changed = True
            except Exception:
                pass
    return changed


def apply_post_process_stack(ppv) -> list[str]:
    """Attach toon outline + storybook vines blendables in order."""
    import unreal
    import material_lib as mlib

    if not ppv:
        return []
    ppv.set_editor_property("unbound", True)
    s = ppv.get_editor_property("settings")
    blendables = []
    vines_path = PP_VINES_INST if unreal.EditorAssetLibrary.does_asset_exist(PP_VINES_INST) else PP_VINES
    for pp_path in (PP_OUTLINE, vines_path):
        if unreal.EditorAssetLibrary.does_asset_exist(pp_path):
            mat = unreal.load_asset(pp_path)
            if mat:
                blendables.append(mat)
    if blendables:
        mlib.try_set_editor_property(s, "b_override_blendables", True)
        try:
            weighted = unreal.WeightedBlendables()
            weighted.set_editor_property(
                "array",
                [unreal.WeightedBlendable(1.0, mat) for mat in blendables],
            )
            s.set_editor_property("weighted_blendables", weighted)
        except Exception as exc:
            unreal.log_warning(f"[ScenePP] blendables skipped: {exc}")
    ppv.set_editor_property("settings", s)
    return [m.get_name() for m in blendables]


def find_or_spawn_ppv(eas, loc=(0, 0, 300)):
    import unreal

    for actor in eas.get_all_level_actors() or []:
        if isinstance(actor, unreal.PostProcessVolume):
            return actor
    return eas.spawn_actor_from_class(
        unreal.PostProcessVolume, unreal.Vector(*loc), unreal.Rotator(0, 0, 0)
    )
