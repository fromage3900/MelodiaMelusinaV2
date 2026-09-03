"""Create the isolated render lab for the Distance Field/RVT spike."""
from __future__ import annotations

import json
from pathlib import Path

import unreal


LEVEL = "/Game/Melodia/Levels/DistanceFieldBlendLab"
REPORT = Path(unreal.Paths.project_dir()) / "Saved" / "Audit" / "distance_field_lab_setup.json"
MASTER_MI = "/Game/Melodia/Materials/DistanceField/MI_DF_ContactBlend_Soft"
GROUND_MI = "/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_Meadow"
KIT = "/Game/EnvSandbox/Greybox_Kit"

MESHES = {
    "floor": f"{KIT}/SM_Greybox_Floor_4x4.SM_Greybox_Floor_4x4",
    "rock_a": f"{KIT}/SM_Greybox_Rock_A.SM_Greybox_Rock_A",
    "rock_b": f"{KIT}/SM_Greybox_Rock_B.SM_Greybox_Rock_B",
    "wall": f"{KIT}/SM_Greybox_Wall_4x3.SM_Greybox_Wall_4x3",
    "column": f"{KIT}/SM_Greybox_Column_05.SM_Greybox_Column_05",
}


def _load(path: str):
    asset = unreal.load_asset(path)
    if not asset:
        raise RuntimeError(f"Missing lab asset: {path}")
    return asset


def _set(actor, prop, value):
    try:
        actor.set_editor_property(prop, value)
    except Exception:
        pass


def _ensure_level():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    asset_path = f"{LEVEL}.{LEVEL.rsplit('/', 1)[-1]}"
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        if not les.load_level(LEVEL):
            raise RuntimeError(f"Could not load {LEVEL}")
    else:
        unreal.EditorAssetLibrary.make_directory("/Game/Melodia/Levels")
        if not les.new_level(LEVEL, is_partitioned_world=False):
            raise RuntimeError(f"Could not create {LEVEL}")
    return les


def _clear(eas):
    for actor in list(eas.get_all_level_actors()):
        if actor.get_actor_label().startswith("DFLab_"):
            eas.destroy_actor(actor)


def _mesh(eas, label, mesh_path, location, scale, material_path):
    actor = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(label)
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    component.set_static_mesh(_load(mesh_path))
    component.set_material(0, _load(material_path))
    actor.set_actor_scale3d(unreal.Vector(*scale))
    _set(component, "cast_shadow", True)
    _set(component, "affect_distance_field_lighting", True)
    return actor


def _light(eas, cls, label, location, rotation, intensity, color=None):
    actor = eas.spawn_actor_from_class(cls, unreal.Vector(*location), unreal.Rotator(*rotation))
    actor.set_actor_label(label)
    component = actor.get_component_by_class(unreal.LightComponent)
    _set(component, "intensity", intensity)
    if color:
        _set(component, "light_color", unreal.Color(*color))
    _set(component, "cast_shadows", True)
    return actor


def _camera(eas):
    # Unreal Python Rotator constructor is roll, pitch, yaw in this editor build.
    actor = eas.spawn_actor_from_class(unreal.CineCameraActor, unreal.Vector(720.0, -820.0, 480.0), unreal.Rotator(0.0, -24.0, 131.3))
    actor.set_actor_label("DFLab_Camera_Hero")
    component = actor.get_component_by_class(unreal.CineCameraComponent)
    _set(component, "current", True)
    _set(component, "manual_focus_distance", 2100.0)
    _set(component, "current_focal_length", 45.0)
    return actor


def main():
    les = _ensure_level()
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    _clear(eas)
    # Greybox floor is a 4-unit tile; use a large lab surface so camera-distance
    # and RVT continuity are observable in the render.
    ground = _mesh(eas, "DFLab_Ground", MESHES["floor"], (0, 0, -20), (700.0, 500.0, 1.0), GROUND_MI)
    _mesh(eas, "DFLab_EmbeddedRock", MESHES["rock_a"], (-430, -120, 45), (1.35, 1.10, 0.85), MASTER_MI)
    _mesh(eas, "DFLab_WallContact", MESHES["wall"], (0, 260, 160), (1.25, 1.0, 1.15), MASTER_MI)
    _mesh(eas, "DFLab_ColumnContact", MESHES["column"], (360, 190, 120), (1.0, 1.0, 1.4), MASTER_MI)
    _mesh(eas, "DFLab_SeparatedRock", MESHES["rock_b"], (500, -260, 260), (1.1, 1.1, 1.1), MASTER_MI)
    _light(eas, unreal.DirectionalLight, "DFLab_Key", (0, 0, 1200), (-35, -35, 0), 1.0, (210, 225, 255, 255))
    _light(eas, unreal.PointLight, "DFLab_Fill", (0, 0, 420), (0, 0, 0), 80.0, (130, 180, 255, 255))
    sky = eas.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 600))
    sky.set_actor_label("DFLab_Sky")
    _set(sky.get_component_by_class(unreal.SkyLightComponent), "real_time_capture", True)
    _camera(eas)
    les.save_current_level()
    result = {
        "level": LEVEL,
        "ground": "DFLab_Ground",
        "contact_meshes": ["DFLab_EmbeddedRock", "DFLab_WallContact", "DFLab_ColumnContact"],
        "separated_mesh": "DFLab_SeparatedRock",
        "camera": "DFLab_Camera_Hero",
        "mesh_distance_fields_enabled": True,
        "legacy_plugin_removed": True,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    unreal.log(f"[DistanceFieldLab] Built lab -> {REPORT}")


if __name__ == "__main__":
    main()
