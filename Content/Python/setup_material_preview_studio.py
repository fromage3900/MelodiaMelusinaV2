"""Build L_MaterialPreview_Studio — frozen rig for MI loop captures.

Creates:
  - Melodia void/iri gradient backdrop (no SkyAtmosphere / UDS — avoids UE headquarters look)
  - 3-point + rim lighting
  - Unbound PPV with manual exposure + toon/vines/Melu grade stack
  - Tagged swatch actor + cine camera for orbit sequences

Run in-editor:
  py Content/Python/setup_melodia_void_gradient.py   # once, creates backdrop MI
  py Content/Python/setup_material_preview_studio.py
"""
from __future__ import annotations

import json
import sys

import mi_preview_studio as studio

REPORT = studio.PROJECT_ROOT / "Saved" / "Audit" / "material_preview_studio.json"


def _find_actor_by_label(eas, label: str):
    for actor in eas.get_all_level_actors() or []:
        if actor.get_actor_label() == label:
            return actor
    return None


def _set_tag(actor, tag: str) -> None:
    try:
        tags = list(actor.tags)
        if tag not in tags:
            tags.append(tag)
            actor.tags = tags
    except Exception:
        pass


def _spawn_or_get(eas, cls, label: str, loc=(0, 0, 0), rot=(0, 0, 0), tag: str | None = None):
    actor = _find_actor_by_label(eas, label)
    if actor:
        return actor
    try:
        actor = eas.spawn_actor_from_class(
            cls,
            __import__("unreal").Vector(*loc),
            studio.ue_rotator(rot),
        )
    except Exception as exc:
        import unreal

        unreal.log_warning(f"[MIStudio] spawn {label}: {exc}")
        return None
    if actor:
        actor.set_actor_label(label)
        if tag:
            _set_tag(actor, tag)
    return actor


def _configure_ppv(ppv) -> list[str]:
    import unreal
    import material_lib as mlib
    import portfolio_scene_integration as scene

    ppv.set_editor_property("unbound", True)
    ppv.set_editor_property("priority", 10.0)
    s = ppv.get_editor_property("settings")
    mlib.try_set_editor_property(s, "b_override_auto_exposure_method", True)
    mlib.try_set_editor_property(s, "auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
    mlib.try_set_editor_property(s, "b_override_auto_exposure_bias", True)
    mlib.try_set_editor_property(s, "auto_exposure_bias", studio.PPV_EXPOSURE_BIAS)
    mlib.try_set_editor_property(s, "b_override_bloom_intensity", True)
    mlib.try_set_editor_property(s, "bloom_intensity", studio.PPV_BLOOM)
    mlib.try_set_editor_property(s, "b_override_vignette_intensity", True)
    mlib.try_set_editor_property(s, "vignette_intensity", studio.PPV_VIGNETTE)
    mlib.try_set_editor_property(s, "b_override_grain_intensity", True)
    mlib.try_set_editor_property(s, "grain_intensity", studio.PPV_GRAIN)
    mlib.try_set_editor_property(s, "b_override_scene_fringe_intensity", True)
    mlib.try_set_editor_property(s, "scene_fringe_intensity", studio.PPV_CHROMATIC)
    ppv.set_editor_property("settings", s)

    applied = scene.apply_post_process_stack(ppv)
    s = ppv.get_editor_property("settings")
    if unreal.EditorAssetLibrary.does_asset_exist(studio.PP_MELU_GRADE):
        mat = unreal.load_asset(studio.PP_MELU_GRADE)
        if mat:
            try:
                weighted = unreal.WeightedBlendables()
                existing = list(s.get_editor_property("weighted_blendables").get_editor_property("array") or [])
                existing.append(unreal.WeightedBlendable(1.0, mat))
                weighted.set_editor_property("array", existing)
                s.set_editor_property("weighted_blendables", weighted)
                ppv.set_editor_property("settings", s)
                applied.append(mat.get_name())
            except Exception as exc:
                unreal.log_warning(f"[MIStudio] Melu grade skipped: {exc}")
    return applied


def _ensure_backdrop(eas, backdrop_key: str | None = None) -> dict:
    import unreal

    key = backdrop_key or studio.DEFAULT_BACKDROP
    actor = _spawn_or_get(
        eas,
        unreal.StaticMeshActor,
        "Backdrop_MelodiaVoid",
        loc=(0, 0, 0),
        tag=studio.TAG_BACKDROP,
    )
    # Migrate legacy cyclorama label if present
    legacy = _find_actor_by_label(eas, "Backdrop_Cyclorama")
    if legacy and actor and legacy != actor:
        try:
            eas.destroy_actor(legacy)
        except Exception:
            pass
    if not actor and legacy:
        actor = legacy
        actor.set_actor_label("Backdrop_MelodiaVoid")
        _set_tag(actor, studio.TAG_BACKDROP)
    if not actor:
        return {"status": "spawn_failed"}
    mesh = unreal.load_asset(studio.SPHERE)
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.set_actor_scale3d(unreal.Vector(3200.0, 3200.0, 3200.0))
    mi_path = studio.BACKDROP_MIS.get(key, studio.BACKDROP_MIS[studio.DEFAULT_BACKDROP])
    if not unreal.EditorAssetLibrary.does_asset_exist(mi_path):
        # Bootstrap gradient MI if missing
        try:
            import setup_melodia_void_gradient as void_grad

            void_grad.build_master()
            void_grad.build_instance(f"{void_grad.MASTER_DIR}/{void_grad.MASTER_NAME}.{void_grad.MASTER_NAME}")
        except Exception as exc:
            unreal.log_warning(f"[MIStudio] void gradient bootstrap: {exc}")
    if unreal.EditorAssetLibrary.does_asset_exist(mi_path):
        actor.static_mesh_component.set_material(0, unreal.load_asset(mi_path))
    return {"status": "ok", "backdrop": key, "mi": mi_path}


def _ensure_lighting(eas) -> dict:
    import unreal

    key = _spawn_or_get(
        eas,
        unreal.DirectionalLight,
        studio.TAG_KEY_LIGHT,
        loc=(400, -200, 600),
        rot=(-42, 35, 0),
        tag=studio.TAG_KEY_LIGHT,
    )
    fill = _spawn_or_get(
        eas,
        unreal.DirectionalLight,
        studio.TAG_FILL_LIGHT,
        loc=(-300, 250, 350),
        rot=(-28, -120, 0),
        tag=studio.TAG_FILL_LIGHT,
    )
    rim = _spawn_or_get(
        eas,
        unreal.DirectionalLight,
        studio.TAG_RIM_LIGHT,
        loc=(-450, -350, 500),
        rot=(-20, 145, 0),
        tag=studio.TAG_RIM_LIGHT,
    )
    sky = _spawn_or_get(eas, unreal.SkyLight, "MI_Preview_SkyLight", loc=(0, 0, 400))
    if sky:
        try:
            comp = sky.get_component_by_class(unreal.SkyLightComponent.static_class())
            if comp:
                comp.set_editor_property("intensity", 0.35)
            else:
                sky.set_editor_property("light_component", sky.light_component)
                sky.light_component.set_editor_property("intensity", 0.35)
        except Exception:
            try:
                sky.light_component.set_editor_property("intensity", 0.35)
            except Exception as exc:
                unreal.log_warning(f"[MIStudio] skylight intensity: {exc}")
    for light, intensity in (
        (key, 4.5),
        (fill, 2.2),
        (rim, 1.8),
    ):
        if not light:
            continue
        try:
            comp = light.get_component_by_class(unreal.DirectionalLightComponent.static_class())
            if comp:
                comp.set_editor_property("intensity", intensity)
            else:
                light.light_component.set_editor_property("intensity", intensity)
        except Exception:
            try:
                light.set_editor_property("intensity", intensity)
            except Exception:
                pass
    return {
        "key": key.get_actor_label() if key else None,
        "fill": fill.get_actor_label() if fill else None,
        "rim": rim.get_actor_label() if rim else None,
        "sky": sky.get_actor_label() if sky else None,
    }


def _ensure_swatch(eas) -> dict:
    import unreal

    actor = _spawn_or_get(
        eas,
        unreal.StaticMeshActor,
        "MI_Preview_Swatch",
        loc=(0, 0, 40),
        tag=studio.TAG_SWATCH,
    )
    if not actor:
        return {"status": "spawn_failed"}
    mesh = unreal.load_asset(studio.SPHERE)
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.set_actor_scale3d(unreal.Vector(*studio.SWATCH_SPHERE_SCALE))
    return {"status": "ok", "actor": actor.get_actor_label()}


def _ensure_set_dress(eas) -> dict:
    """Minimal Nikki fashion set-dress — pedestal, hydro sheet, optional trim card."""
    import unreal

    pedestal = _spawn_or_get(
        eas,
        unreal.StaticMeshActor,
        studio.TAG_PEDESTAL,
        loc=(0, 0, -55),
        tag=studio.TAG_PEDESTAL,
    )
    ped_mi = f"{studio.SHOWCASE_DIR}/MI_Show_Default"
    if pedestal:
        cube = unreal.load_asset(studio.CUBE)
        pedestal.static_mesh_component.set_static_mesh(cube)
        pedestal.set_actor_scale3d(unreal.Vector(1.35, 1.35, 0.45))
        if unreal.EditorAssetLibrary.does_asset_exist(ped_mi):
            pedestal.static_mesh_component.set_material(0, unreal.load_asset(ped_mi))

    hydro = _spawn_or_get(
        eas,
        unreal.StaticMeshActor,
        studio.TAG_HYDRO,
        loc=(90, -70, -80),
        rot=(0, 15, 0),
        tag=studio.TAG_HYDRO,
    )
    hydro_mi = f"{studio.SHOWCASE_DIR}/MI_Show_ElementHydro"
    if hydro:
        plane = unreal.load_asset(studio.PLANE)
        hydro.static_mesh_component.set_static_mesh(plane)
        hydro.set_actor_scale3d(unreal.Vector(2.2, 2.2, 1.0))
        if unreal.EditorAssetLibrary.does_asset_exist(hydro_mi):
            hydro.static_mesh_component.set_material(0, unreal.load_asset(hydro_mi))

    trim = _spawn_or_get(
        eas,
        unreal.StaticMeshActor,
        studio.TAG_TRIM_CARD,
        loc=(-95, 80, 20),
        rot=(0, 55, 0),
        tag=studio.TAG_TRIM_CARD,
    )
    trim_mi = "/Game/EnvSandbox/Materials/Instances/Environment/Stylized/MI_ZenTrim_FlowersLots"
    if trim:
        plane = unreal.load_asset(studio.PLANE)
        trim.static_mesh_component.set_static_mesh(plane)
        trim.set_actor_rotation(unreal.Rotator(0.0, 90.0, 55.0), False)
        trim.set_actor_scale3d(unreal.Vector(0.85, 0.85, 0.08))
        trim.set_actor_hidden_in_game(True)
        try:
            trim.set_is_temporarily_hidden_in_editor(True)
        except Exception:
            pass
        if unreal.EditorAssetLibrary.does_asset_exist(trim_mi):
            trim.static_mesh_component.set_material(0, unreal.load_asset(trim_mi))

    return {
        "pedestal": pedestal.get_actor_label() if pedestal else None,
        "hydro": hydro.get_actor_label() if hydro else None,
        "trim_card": trim.get_actor_label() if trim else None,
    }


def _ensure_camera(eas) -> dict:
    import unreal

    cam = _spawn_or_get(
        eas,
        unreal.CineCameraActor,
        studio.TAG_CAMERA,
        loc=studio.orbit_camera_position(0),
        rot=studio.look_at_rotation(studio.orbit_camera_position(0)),
        tag=studio.TAG_CAMERA,
    )
    if not cam:
        return {"status": "spawn_failed"}
    cine = cam.get_cine_camera_component()
    if cine:
        try:
            cine.set_editor_property("current_focal_length", float(studio.CAMERA_FOCAL_LENGTH))
        except Exception:
            pass
        try:
            cine.set_editor_property("current_aperture", 4.0)
        except Exception:
            pass
        # UE5.x property name varies: filmback_settings vs filmback
        for prop in ("filmback_settings", "filmback"):
            try:
                settings = cine.get_editor_property(prop)
                settings.set_editor_property("sensor_width", 24.0)
                settings.set_editor_property("sensor_height", 24.0)
                cine.set_editor_property(prop, settings)
                break
            except Exception:
                continue
    return {"status": "ok", "actor": cam.get_actor_label()}


def _remove_atmosphere_actors(eas) -> int:
    import unreal

    removed = 0
    for actor in list(eas.get_all_level_actors() or []):
        if isinstance(
            actor,
            (
                unreal.SkyAtmosphere,
                unreal.ExponentialHeightFog,
                unreal.VolumetricCloud,
            ),
        ):
            try:
                eas.destroy_actor(actor)
                removed += 1
            except Exception:
                pass
    return removed


def build_studio(*, backdrop: str | None = None) -> dict:
    import unreal

    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not unreal.EditorAssetLibrary.does_asset_exist(studio.LEVEL_ASSET):
        unreal.EditorAssetLibrary.make_directory("/Game/EnvSandbox/_Template")
        les.new_level(studio.LEVEL)
    else:
        les.load_level(studio.LEVEL)

    removed = _remove_atmosphere_actors(eas)

    ppv = _find_actor_by_label(eas, studio.TAG_PPV)
    if not ppv:
        ppv = eas.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0, 0, 0))
        if ppv:
            ppv.set_actor_label(studio.TAG_PPV)
    pp_stack = _configure_ppv(ppv) if ppv else []

    backdrop_key = backdrop or studio.DEFAULT_BACKDROP
    report = {
        "display_name": studio.STUDIO_DISPLAY_NAME,
        "level": studio.LEVEL,
        "doctrine": "melodia_void_nikki_lens",
        "removed_atmosphere": removed,
        "backdrop": _ensure_backdrop(eas, backdrop_key),
        "lighting": _ensure_lighting(eas),
        "swatch": _ensure_swatch(eas),
        "set_dress": _ensure_set_dress(eas),
        "camera": _ensure_camera(eas),
        "pp_stack": pp_stack,
        "pp_contract": {
            "bloom": studio.PPV_BLOOM,
            "vignette": studio.PPV_VIGNETTE,
            "grain": studio.PPV_GRAIN,
            "chromatic": studio.PPV_CHROMATIC,
            "exposure_bias": studio.PPV_EXPOSURE_BIAS,
        },
        "framing": {
            "orbit_radius": studio.ORBIT_RADIUS,
            "orbit_elevation_deg": studio.ORBIT_ELEVATION_DEG,
            "focal_length": studio.CAMERA_FOCAL_LENGTH,
            "swatch_scale": list(studio.SWATCH_SPHERE_SCALE),
            "swatch_z": 40.0,
        },
        "nikki_priority": list(studio.NIKKI_PRIORITY),
    }

    les.save_current_level()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    studio.LOOPS_ROOT.mkdir(parents=True, exist_ok=True)
    unreal.log(f"[MIStudio] Built {studio.LEVEL}")
    return report


def main() -> int:
    result = build_studio()
    if "json" in sys.argv:
        print(json.dumps(result, indent=2))
    else:
        print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
