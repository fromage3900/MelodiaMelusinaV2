"""Small, additive proof-level assembly helpers for hero music graphs."""
from __future__ import annotations

from typing import Any, Mapping

import pcg_hero_music_control as control


CONTROL_CLASS_PATH = "/Game/EnvSandbox/PCG/Universal/BP_MelodiaPCGControl.BP_MelodiaPCGControl_C"


def set_if_present(obj: Any, prop: str, value: Any) -> bool:
    try:
        obj.set_editor_property(prop, value)
        return True
    except Exception:
        return False


def set_tag(actor: Any, tag: str) -> None:
    try:
        tags = list(actor.tags or [])
        if tag not in [str(item) for item in tags]:
            tags.append(tag)
            actor.tags = tags
    except Exception:
        pass


def remove_tag(actor: Any, tag: str) -> None:
    try:
        actor.tags = [item for item in list(actor.tags or []) if str(item) != tag]
    except Exception:
        pass


def spawn_or_reuse(unreal: Any, actor_subsystem: Any, existing: dict[str, Any], cls: Any, label: str, location=(0.0, 0.0, 0.0), rotation=(0.0, 0.0, 0.0)) -> Any:
    actor = existing.get(label)
    if actor:
        actor.set_actor_location(unreal.Vector(*location), False, False)
        actor.set_actor_rotation(
            unreal.Rotator(
                pitch=float(rotation[0]),
                yaw=float(rotation[1]),
                roll=float(rotation[2]),
            ),
            False,
        )
        return actor
    actor = actor_subsystem.spawn_actor_from_class(cls, unreal.Vector(*location), unreal.Rotator(*rotation))
    if not actor:
        raise RuntimeError(f"could not spawn {label}")
    # ``unreal.Rotator(*rotation)`` is positional in UE Python as
    # (yaw, roll, pitch), while our proof recipes are authored as
    # (pitch, yaw, roll). Reapply the named fields after spawning so new
    # cameras/lights/starts do not silently rotate into the wrong axis.
    actor.set_actor_rotation(
        unreal.Rotator(
            pitch=float(rotation[0]),
            yaw=float(rotation[1]),
            roll=float(rotation[2]),
        ),
        False,
    )
    actor.set_actor_label(label)
    existing[label] = actor
    return actor


def resolve_class(unreal: Any, name: str) -> Any:
    cls = getattr(unreal, name, None)
    if cls is not None:
        return cls
    candidates = [name]
    if name[:1] in {"A", "U"}:
        candidates.append(name[1:])
    for candidate in candidates:
        cls = unreal.load_class(None, f"/Script/BS_GodFile.{candidate}")
        if cls is not None:
            return cls
    return None


def ensure_control_driver(unreal: Any, actor_subsystem: Any, existing: dict[str, Any], values: Mapping[str, Any]) -> Any:
    actor = control.find_control_actor(unreal, existing.values())
    if not actor:
        control_class = unreal.load_class(None, CONTROL_CLASS_PATH)
        if control_class is None:
            raise RuntimeError(f"canonical control blueprint unavailable: {CONTROL_CLASS_PATH}")
        actor = spawn_or_reuse(unreal, actor_subsystem, existing, control_class, "PCG Hero Music Control", (0.0, 0.0, -500.0))
    set_tag(actor, control.CONTROL_TAG)
    for name, value in values.items():
        set_if_present(actor, name, value)
    # The actor is a generation driver rather than a visible prop.
    try:
        actor.set_actor_hidden_in_game(True)
    except Exception:
        pass
    return actor


def assign_and_generate(unreal: Any, host: Any, graph: Any) -> None:
    import time

    component = host.get_component_by_class(unreal.PCGComponent)
    if not component:
        raise RuntimeError("hero host has no PCGComponent")
    if hasattr(component, "set_graph"):
        component.set_graph(graph)
    else:
        set_if_present(component, "graph", graph)
    # Static spawner outputs are owned by the PCG component. Use the local
    # cleanup path so UE 5.8 keeps the generated-component shell available for
    # the next editor recook; cleanup(True) marks the component generated but
    # can leave the next static-spawner pass empty.
    try:
        component.cleanup_local(False)
    except Exception:
        pass
    # Run a short local/normal recook ladder so the current static spawner
    # branches are materialized before the proof map is saved.
    if not hasattr(component, "generate_local") and not hasattr(component, "generate"):
        raise RuntimeError("hero PCG component exposes no generation method")
    for _ in range(3):
        if hasattr(component, "generate_local"):
            component.generate_local(True)
        if hasattr(component, "generate"):
            component.generate(True)
        time.sleep(0.5)
    # PCG static spawner branches are finalized on the editor's async task
    # queue. Allow that queue to settle before the proof setup saves its map,
    # otherwise a reload can resurrect the previous serialized ISM set.


def ensure_pcg_architecture_volume(
    unreal: Any,
    actor_subsystem: Any,
    existing: dict[str, Any],
    *,
    label: str,
    graph_path: str,
    architecture_tag: str = "PCG_CathedralPCGEx",
    location: tuple[float, float, float] = (0.0, 0.0, 0.0),
    scale: tuple[float, float, float] = (1.0, 1.0, 1.0),
) -> Any:
    """Attach an authored architecture graph to a proof volume at measured scale."""
    import pcg_graph_builder as graph_builder

    graph = unreal.EditorAssetLibrary.load_asset(graph_path)
    if not graph:
        raise RuntimeError(f"architecture graph missing: {graph_path}")
    volume = next(
        (
            actor
            for actor in existing.values()
            if actor and actor.get_class().get_name() == "PCGVolume"
            and "PCG_HeroArchitecture" in [str(tag) for tag in (actor.tags or [])]
        ),
        None,
    )
    if volume is None:
        volume = spawn_or_reuse(unreal, actor_subsystem, existing, unreal.PCGVolume, label, location)
    else:
        volume.set_actor_label(label)
        existing[label] = volume
        volume.set_actor_location(unreal.Vector(*location), False, False)
    set_tag(volume, "PCG_HeroArchitecture")
    for old_tag in ("PCG_CathedralPCGEx", "PCG_CathedralClassic", "PCG_ArpeggioBridgePCGEx", "PCG_ArpeggioBridgeClassic"):
        if old_tag != architecture_tag:
            remove_tag(volume, old_tag)
    set_tag(volume, architecture_tag)
    set_if_present(volume, "is_spatially_loaded", False)
    volume.set_actor_scale3d(unreal.Vector(*scale))
    component = volume.get_component_by_class(unreal.PCGComponent)
    if not component:
        raise RuntimeError(f"architecture volume {label} has no PCG component")
    graph_builder.assign_pcg_graph(component, graph)
    graph_builder.configure_pcg_component(component, seed=90731, activated=True)
    try:
        component.cleanup(True)
    except Exception:
        pass
    component.generate(True)
    return volume


def hide_pcg_architecture_volumes(unreal: Any, existing: dict[str, Any]) -> int:
    """Hide legacy proof volumes when direct measured library pieces own the composition."""
    hidden = 0
    for actor in list(existing.values()):
        if not actor or actor.get_class().get_name() != "PCGVolume":
            continue
        if "PCG_HeroArchitecture" not in [str(tag) for tag in (actor.tags or [])]:
            continue
        try:
            if hasattr(actor, "set_actor_hidden"):
                actor.set_actor_hidden(True)
            elif hasattr(actor, "set_is_temporarily_hidden_in_editor"):
                actor.set_is_temporarily_hidden_in_editor(True)
            elif hasattr(actor, "set_actor_hidden_in_editor"):
                actor.set_actor_hidden_in_editor(True)
        except Exception:
            pass
        try:
            actor.set_actor_hidden_in_game(True)
        except Exception:
            pass
        component = actor.get_component_by_class(unreal.PCGComponent)
        if component:
            try:
                component.cleanup(True)
            except Exception:
                pass
        hidden += 1
    return hidden


def add_lighting_and_camera(unreal: Any, actor_subsystem: Any, existing: dict[str, Any], prefix: str, camera_location: tuple[float, float, float], camera_rotation: tuple[float, float, float], floor_scale: tuple[float, float, float], floor_location: tuple[float, float, float]) -> None:
    floor = spawn_or_reuse(unreal, actor_subsystem, existing, unreal.StaticMeshActor, f"{prefix} Proof Floor", floor_location)
    # Use the authored classic architecture floor tile. The incoming scale is
    # expressed in world-footprint units so every proof recipe gets the same
    # tile grammar instead of a giant unbroken cube-equivalent slab.
    floor_mesh = unreal.EditorAssetLibrary.load_asset("/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Floor_4x4")
    if not floor_mesh:
        raise RuntimeError("classic proof floor mesh is missing: /Game/EnvSandbox/Greybox_Kit/SM_Greybox_Floor_4x4")
    floor.static_mesh_component.set_editor_property("static_mesh", floor_mesh)
    floor_material = unreal.EditorAssetLibrary.load_asset("/Game/EnvSandbox/Materials/Instances/Environment/MI_Env_Stone_Cathedral")
    if floor_material:
        floor.static_mesh_component.set_material(0, floor_material)
    floor.set_actor_scale3d(
        unreal.Vector(
            floor_scale[0] * 100.0 / 4.0,
            floor_scale[1] * 100.0 / 4.0,
            max(0.12, floor_scale[2] / 0.30),
        )
    )

    sun = spawn_or_reuse(unreal, actor_subsystem, existing, unreal.DirectionalLight, f"{prefix} Key Light", (0.0, 0.0, 900.0), (-35.0, -35.0, 0.0))
    set_if_present(sun.get_component_by_class(unreal.DirectionalLightComponent), "intensity", 1.2)
    set_if_present(sun.get_component_by_class(unreal.DirectionalLightComponent), "light_color", unreal.Color(214, 228, 255, 255))
    fill = spawn_or_reuse(unreal, actor_subsystem, existing, unreal.PointLight, f"{prefix} Warm Fill", (0.0, -360.0, 360.0))
    fill_component = fill.get_component_by_class(unreal.PointLightComponent)
    set_if_present(fill_component, "intensity", 420.0)
    set_if_present(fill_component, "attenuation_radius", 1500.0)
    set_if_present(fill_component, "light_color", unreal.Color(255, 184, 128, 255))

    sky = spawn_or_reuse(unreal, actor_subsystem, existing, unreal.SkyLight, f"{prefix} Sky Fill", (0.0, 0.0, 2200.0))
    sky_component = sky.get_component_by_class(unreal.SkyLightComponent)
    set_if_present(sky_component, "intensity", 0.55)
    set_if_present(sky_component, "light_color", unreal.Color(170, 190, 220, 255))

    camera = spawn_or_reuse(unreal, actor_subsystem, existing, unreal.CineCameraActor, f"{prefix} Overview Camera", camera_location, camera_rotation)
    set_if_present(camera.get_cine_camera_component(), "current_focal_length", 38.0)


def load_or_create_level(unreal: Any, level_dir: str, level_path: str) -> Any:
    if not unreal.EditorAssetLibrary.does_directory_exist(level_dir):
        unreal.EditorAssetLibrary.make_directory(level_dir)
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not unreal.EditorAssetLibrary.does_asset_exist(level_path):
        if not levels.new_level(level_path):
            raise RuntimeError(f"could not create {level_path}")
    elif not levels.load_level(level_path):
        raise RuntimeError(f"could not load {level_path}")
    return levels
