"""Portfolio template level + material triad showcase + PP stack.

Builds /Game/EnvSandbox/_Template/L_Template with:
  - Lighting rig, unbound PPV (manual exposure)
  - M_PP_ToonOutline + M_PP_StorybookVines blendables
  - Row of spheres showcasing MI_Show_* starter presets

Run via run_wild_session.py or:
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/setup_template_showcase.py"
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal

import material_lib as mlib

LEVEL = "/Game/EnvSandbox/_Template/L_Template"
REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "template_showcase.json"

CUBE = "/Engine/BasicShapes/Cube.Cube"
SPHERE = "/Engine/BasicShapes/Sphere.Sphere"
PLANE = "/Engine/BasicShapes/Plane.Plane"

# Specialist masters — flat mesh validation (triplanar / pond UV shoreline)
SPECIALIST_SHOWCASE: list[tuple[str, str, tuple[float, float, float], tuple[float, float, float], str]] = [
    (
        "MI_Landscape_Meadow",
        "/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_Meadow",
        (0.0, -800.0, 10.0),
        (14.0, 14.0, 0.08),
        CUBE,
    ),
    (
        "MI_Landscape_SakuraGarden",
        "/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_SakuraGarden",
        (-600.0, -800.0, 12.0),
        (10.0, 10.0, 0.06),
        PLANE,
    ),
    (
        "MI_Landscape_PondBank",
        "/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_PondBank",
        (1800.0, -800.0, 15.0),
        (4.0, 4.0, 0.05),
        PLANE,
    ),
    (
        "MI_GrandWater_ShorelinePond",
        "/Game/EnvSandbox/Materials/Instances/Water/MI_GrandWater_ShorelinePond",
        (2200.0, -800.0, 40.0),
        (6.0, 6.0, 0.05),
        PLANE,
    ),
]

PP_OUTLINE = "/Game/EnvSandbox/Materials/PostProcess/M_PP_ToonOutline.M_PP_ToonOutline"
PP_VINES = "/Game/EnvSandbox/Materials/PostProcess/M_PP_StorybookVines.M_PP_StorybookVines"
PP_VINES_INST = "/Game/EnvSandbox/Materials/PostProcess/M_PP_StorybookVines_Inst.M_PP_StorybookVines_Inst"

SHOWCASE: list[tuple[str, str, tuple[float, float, float]]] = [
    ("MI_Show_Default", "/Game/EnvSandbox/Materials/Instances/Showcase/MI_Show_Default", (-400, 0, 100)),
    ("MI_Show_StoneCliff", "/Game/EnvSandbox/Materials/Instances/Showcase/MI_Show_StoneCliff", (-200, 0, 100)),
    ("MI_Show_CherryBlossom", "/Game/EnvSandbox/Materials/Instances/Showcase/MI_Show_CherryBlossom", (0, 0, 100)),
    ("MI_Show_CelestialNebula", "/Game/EnvSandbox/Materials/Instances/Showcase/MI_Show_CelestialNebula", (200, 0, 100)),
    ("MI_Show_FairyHearts", "/Game/EnvSandbox/Materials/Instances/Showcase/MI_Show_FairyHearts", (400, 0, 100)),
    ("MI_Show_SkinSoft", "/Game/EnvSandbox/Materials/Instances/Showcase/MI_Show_SkinSoft", (600, 0, 100)),
    ("MI_Show_NikkiHero", "/Game/EnvSandbox/Materials/Instances/Showcase/MI_Show_NikkiHero", (700, 0, 100)),
    ("MI_Show_ForestFoliage", "/Game/EnvSandbox/Materials/Instances/Showcase/MI_Show_ForestFoliage", (900, 0, 100)),
    ("MI_Show_ContactRimHero", "/Game/EnvSandbox/Materials/Instances/Showcase/MI_Show_ContactRimHero", (1100, 0, 100)),
    ("MI_Show_ElementHydro", "/Game/EnvSandbox/Materials/Instances/Showcase/MI_Show_ElementHydro", (1300, 0, 100)),
    ("MI_Show_InkWash", "/Game/EnvSandbox/Materials/Instances/Showcase/MI_Show_InkWash", (1500, 0, 100)),
    ("MI_Show_TrimsheetHero", "/Game/EnvSandbox/Materials/Instances/Showcase/MI_Show_TrimsheetHero", (1700, 0, 100)),
    ("MI_Show_ZenTorii", "/Game/EnvSandbox/Materials/Instances/Showcase/MI_Show_ZenTorii", (1900, 0, 100)),
]


def _ensure_level() -> None:
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not unreal.EditorAssetLibrary.does_asset_exist(f"{LEVEL}.L_Template"):
        unreal.EditorAssetLibrary.make_directory("/Game/EnvSandbox/_Template")
        les.new_level(LEVEL)
    else:
        les.load_level(LEVEL)

    def spawn(cls, loc=(0, 0, 0), rot=(0, 0, 0)):
        try:
            return eas.spawn_actor_from_class(cls, unreal.Vector(*loc), unreal.Rotator(*rot))
        except Exception as exc:
            unreal.log_warning(f"[Showcase] spawn {cls}: {exc}")
            return None

    if not eas.get_all_level_actors():
        spawn(unreal.DirectionalLight, (0, 0, 800), (-45, 30, 0))
        spawn(unreal.SkyLight, (0, 0, 400))
        spawn(unreal.SkyAtmosphere)
        spawn(unreal.ExponentialHeightFog, (0, 0, 0))
        spawn(unreal.CineCameraActor, (700, -1200, 350), (0, 35, 0))

    ppv = None
    for actor in eas.get_all_level_actors():
        if isinstance(actor, unreal.PostProcessVolume):
            ppv = actor
            break
    if not ppv:
        ppv = spawn(unreal.PostProcessVolume, (0, 0, 0))
    if ppv:
        ppv.set_editor_property("unbound", True)
        s = ppv.get_editor_property("settings")
        lib = mlib
        lib.try_set_editor_property(s, "b_override_auto_exposure_method", True)
        lib.try_set_editor_property(s, "auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
        lib.try_set_editor_property(s, "b_override_auto_exposure_bias", True)
        lib.try_set_editor_property(s, "auto_exposure_bias", 8.0)
        ppv.set_editor_property("settings", s)
        import portfolio_scene_integration as scene

        scene.apply_post_process_stack(ppv)


def _spawn_showcase_spheres() -> list[dict]:
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    mesh = unreal.load_asset(SPHERE)
    results: list[dict] = []
    for label, mi_path, loc in SHOWCASE:
        if not unreal.EditorAssetLibrary.does_asset_exist(mi_path):
            results.append({"label": label, "status": "missing_mi"})
            continue
        actor = eas.spawn_actor_from_class(
            unreal.StaticMeshActor,
            unreal.Vector(*loc),
            unreal.Rotator(0, 0, 0),
        )
        if not actor:
            results.append({"label": label, "status": "spawn_failed"})
            continue
        actor.set_actor_label(f"Showcase_{label}")
        actor.set_actor_scale3d(unreal.Vector(1.5, 1.5, 1.5))
        sm = actor.static_mesh_component
        sm.set_static_mesh(mesh)
        mi = unreal.load_asset(mi_path)
        sm.set_material(0, mi)
        results.append({"label": label, "status": "ok", "actor": actor.get_name(), "mi": mi_path})
    return results


def _spawn_specialist_planes() -> list[dict]:
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    results: list[dict] = []
    for label, mi_path, loc, scale, mesh_path in SPECIALIST_SHOWCASE:
        if not unreal.EditorAssetLibrary.does_asset_exist(mi_path):
            results.append({"label": label, "status": "missing_mi"})
            continue
        mesh = unreal.load_asset(mesh_path)
        if not mesh:
            results.append({"label": label, "status": "missing_mesh"})
            continue
        actor = eas.spawn_actor_from_class(
            unreal.StaticMeshActor,
            unreal.Vector(*loc),
            unreal.Rotator(0, 0, 0),
        )
        if not actor:
            results.append({"label": label, "status": "spawn_failed"})
            continue
        actor.set_actor_label(f"Specialist_{label}")
        actor.set_actor_scale3d(unreal.Vector(*scale))
        sm = actor.static_mesh_component
        sm.set_static_mesh(mesh)
        mi = unreal.load_asset(mi_path)
        sm.set_material(0, mi)
        results.append({"label": label, "status": "ok", "actor": actor.get_name(), "mi": mi_path})
    return results


def _spawn_landscape_actor_stub() -> dict:
    """Landscape actor when editor supports it; otherwise labeled validation plane."""
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    mi_path = "/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_SakuraGarden"
    landscape_cls = getattr(unreal, "Landscape", None)
    if landscape_cls:
        try:
            actor = eas.spawn_actor_from_class(
                landscape_cls, unreal.Vector(-1200.0, -800.0, 0.0), unreal.Rotator(0, 0, 0),
            )
            if actor:
                actor.set_actor_label("LandscapeStub_SakuraGarden")
                return {"status": "landscape_actor", "actor": actor.get_name(), "mi": mi_path}
        except Exception as exc:
            unreal.log_warning(f"[Showcase] Landscape stub: {exc}")
    if not unreal.EditorAssetLibrary.does_asset_exist(mi_path):
        return {"status": "missing_mi", "mi": mi_path}
    mesh = unreal.load_asset(PLANE)
    actor = eas.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(-1200.0, -800.0, 8.0), unreal.Rotator(0, 0, 0),
    )
    if not actor:
        return {"status": "spawn_failed"}
    actor.set_actor_label("LandscapeStub_Plane")
    actor.set_actor_scale3d(unreal.Vector(8.0, 8.0, 0.05))
    sm = actor.static_mesh_component
    sm.set_static_mesh(mesh)
    sm.set_material(0, unreal.load_asset(mi_path))
    return {"status": "plane_fallback", "actor": actor.get_name(), "mi": mi_path}


def _spawn_greybox_ground() -> dict:
    """Ground plane for PCG_Greybox presets."""
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    mi_path = "/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_Meadow"
    for actor in eas.get_all_level_actors():
        if actor.get_actor_label() == "Ground":
            return {"status": "exists", "actor": actor.get_name()}
    mesh = unreal.load_asset(PLANE)
    actor = eas.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(0, 0, -20), unreal.Rotator(0, 0, 0),
    )
    if not actor:
        return {"status": "spawn_failed"}
    actor.set_actor_label("Ground")
    actor.set_actor_scale3d(unreal.Vector(40, 40, 1))
    sm = actor.static_mesh_component
    sm.set_static_mesh(mesh)
    if unreal.EditorAssetLibrary.does_asset_exist(mi_path):
        sm.set_material(0, unreal.load_asset(mi_path))
    try:
        tags = list(actor.tags)
        if "PCG_Ground" not in tags:
            tags.append("PCG_Ground")
            actor.tags = tags
    except Exception:
        pass
    return {"status": "ok", "actor": actor.get_name(), "tag": "PCG_Ground"}


def build_all() -> int:
    _ensure_level()
    ground = _spawn_greybox_ground()
    spheres = _spawn_showcase_spheres()
    specialists = _spawn_specialist_planes()
    landscape_stub = _spawn_landscape_actor_stub()
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    report = {
        "level": LEVEL,
        "spheres": spheres,
        "specialists": specialists,
        "landscape_stub": landscape_stub,
        "greybox_ground": ground,
        "pp_outline": PP_OUTLINE,
        "pp_vines": PP_VINES_INST if unreal.EditorAssetLibrary.does_asset_exist(PP_VINES_INST) else PP_VINES,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[Showcase] {len(spheres)} spheres + {len(specialists)} specialists in {LEVEL}")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(build_all())
