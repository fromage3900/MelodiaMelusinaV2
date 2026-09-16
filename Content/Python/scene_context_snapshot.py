r"""Scene Context Snapshot — compact 3D awareness packet for Unreal editor agents.

Run inside UE 5.8 with the target level already open:

    exec(open(r"C:\EnvironmentPortfolio\BS_GodFile\Content\Python\scene_context_snapshot.py").read())

Outputs machine-local artifacts under:
    Saved/Audit/SceneContext/<LevelName>/
        scene_context_latest.json
        viewport_latest.png
        top_latest.png

The snapshot is evidence/context, not project authority. It does not save the level,
modify gameplay state, or replace CURRENT_STATE.md / subsystem contracts.

Purpose:
- give agents immediate spatial context before world/level edits;
- summarize route/exclusion tags, PCG ownership, actor bounds and hero landmarks;
- capture what the owner is currently looking at plus a top-down spatial plate;
- avoid dumping every generated actor into prompt context.

The capture actors are temporary and destroyed before return.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

MAX_CONTEXT_ACTORS = 180
MAX_PCG_ACTORS = 64

ROUTE_TAGS = {
    "WP_PrimaryRoute",
    "WP_NoScatter",
    "PCG_Exclude",
    "WP_LandmarkClear",
}

LANDMARK_WORDS = (
    "PlayerStart",
    "Starskiff",
    "Bridge",
    "Arpeggio",
    "Bell",
    "Tree",
    "Phyllotaxis",
    "Reef",
    "Cathedral",
    "Atlantis",
    "Shrine",
    "Portal",
    "Gate",
    "Destination",
    "Hero",
    "Landmark",
)

SPATIAL_CLASSES = {
    "Landscape",
    "LandscapeStreamingProxy",
    "PlayerStart",
    "PCGVolume",
    "CineCameraActor",
    "CameraActor",
    "WaterBodyOcean",
    "WaterBodyLake",
    "WaterBodyRiver",
}

IGNORE_WORLD_BOUND_WORDS = (
    "Sky",
    "DirectionalLight",
    "SkyLight",
    "ExponentialHeightFog",
    "PostProcessVolume",
    "NavMeshBoundsVolume",
    "RecastNavMesh",
    "WorldDataLayers",
)


def _round(value, digits=3):
    try:
        return round(float(value), digits)
    except Exception:
        return 0.0


def _vec(v):
    return {"x": _round(v.x), "y": _round(v.y), "z": _round(v.z)}


def _rot(r):
    return {
        "pitch": _round(r.pitch),
        "yaw": _round(r.yaw),
        "roll": _round(r.roll),
    }


def _path(obj):
    if obj is None:
        return None
    try:
        return str(obj.get_path_name())
    except Exception:
        return str(obj)


def _bounds(actor):
    try:
        origin, extent = actor.get_actor_bounds(False, False)
    except Exception:
        try:
            origin, extent = actor.get_actor_bounds(False)
        except Exception:
            return None
    return {
        "origin": _vec(origin),
        "extent": _vec(extent),
        "size_cm": {
            "x": _round(abs(extent.x) * 2.0),
            "y": _round(abs(extent.y) * 2.0),
            "z": _round(abs(extent.z) * 2.0),
        },
    }


def _folder(actor):
    try:
        return str(actor.get_folder_path())
    except Exception:
        return ""


def _tags(actor):
    try:
        return sorted(str(tag) for tag in actor.tags)
    except Exception:
        return []


def _static_mesh(actor, unreal):
    try:
        component = actor.get_component_by_class(unreal.StaticMeshComponent)
        if component:
            mesh = component.get_editor_property("static_mesh")
            return _path(mesh)
    except Exception:
        pass
    return None


def _pcg_info(actor, unreal):
    if not hasattr(unreal, "PCGComponent"):
        return None
    try:
        component = actor.get_component_by_class(unreal.PCGComponent)
    except Exception:
        component = None
    if not component:
        return None

    graph = None
    try:
        graph = component.get_editor_property("graph_instance")
    except Exception:
        pass
    if not graph:
        try:
            graph = component.get_graph()
        except Exception:
            pass

    instance_count = 0
    try:
        for comp in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            instance_count += int(comp.get_instance_count())
    except Exception:
        pass

    return {
        "graph": _path(graph),
        "generated_instance_count": instance_count,
    }


def _camera_info(actor, unreal):
    try:
        if not actor.is_a(unreal.CineCameraActor.static_class()):
            return None
        component = actor.get_cine_camera_component()
        return {
            "focal_length_mm": _round(
                component.get_editor_property("current_focal_length")
            ),
            "aperture": _round(component.get_editor_property("current_aperture")),
        }
    except Exception:
        return None


def _actor_row(actor, unreal, selected_ids):
    label = str(actor.get_actor_label())
    class_name = str(actor.get_class().get_name())
    tags = _tags(actor)
    bounds = _bounds(actor)
    try:
        selected_key = str(actor.get_path_name())
    except Exception:
        selected_key = label
    selected = selected_key in selected_ids

    row = {
        "label": label,
        "class": class_name,
        "selected": selected,
        "folder": _folder(actor),
        "tags": tags,
        "location": _vec(actor.get_actor_location()),
        "rotation": _rot(actor.get_actor_rotation()),
        "scale": _vec(actor.get_actor_scale3d()),
        "bounds": bounds,
    }

    mesh = _static_mesh(actor, unreal)
    if mesh:
        row["static_mesh"] = mesh

    pcg = _pcg_info(actor, unreal)
    if pcg:
        row["pcg"] = pcg

    camera = _camera_info(actor, unreal)
    if camera:
        row["camera"] = camera

    priority = 0
    if selected:
        priority += 1000
    if ROUTE_TAGS.intersection(tags):
        priority += 500
    if class_name in SPATIAL_CLASSES:
        priority += 350
    if pcg:
        priority += 300
    if any(word.lower() in label.lower() for word in LANDMARK_WORDS):
        priority += 250
    if bounds:
        sx = bounds["size_cm"]["x"]
        sy = bounds["size_cm"]["y"]
        priority += min(200, int(math.log10(max(1.0, sx * sy)) * 25))

    row["_priority"] = priority
    return row


def _world_bounds(rows):
    included = []
    for row in rows:
        if not row.get("bounds"):
            continue
        if any(word.lower() in row["class"].lower() for word in IGNORE_WORLD_BOUND_WORDS):
            continue
        included.append(row)

    if not included:
        return None

    min_x = min(r["bounds"]["origin"]["x"] - r["bounds"]["extent"]["x"] for r in included)
    max_x = max(r["bounds"]["origin"]["x"] + r["bounds"]["extent"]["x"] for r in included)
    min_y = min(r["bounds"]["origin"]["y"] - r["bounds"]["extent"]["y"] for r in included)
    max_y = max(r["bounds"]["origin"]["y"] + r["bounds"]["extent"]["y"] for r in included)
    min_z = min(r["bounds"]["origin"]["z"] - r["bounds"]["extent"]["z"] for r in included)
    max_z = max(r["bounds"]["origin"]["z"] + r["bounds"]["extent"]["z"] for r in included)

    return {
        "min": {"x": _round(min_x), "y": _round(min_y), "z": _round(min_z)},
        "max": {"x": _round(max_x), "y": _round(max_y), "z": _round(max_z)},
        "center": {
            "x": _round((min_x + max_x) / 2.0),
            "y": _round((min_y + max_y) / 2.0),
            "z": _round((min_z + max_z) / 2.0),
        },
        "size_cm": {
            "x": _round(max_x - min_x),
            "y": _round(max_y - min_y),
            "z": _round(max_z - min_z),
        },
    }


def _capture_from_transform(unreal, world, actor_subsystem, location, rotation, output_path, fov=55.0):
    width, height = 1920, 1080
    render_target = unreal.RenderingLibrary.create_render_target2d(
        world,
        width,
        height,
        unreal.TextureRenderTargetFormat.RTF_RGBA8,
        unreal.LinearColor(0.0, 0.0, 0.0, 1.0),
        False,
    )
    if not render_target:
        return {"ok": False, "error": "render target creation failed"}

    capture_actor = actor_subsystem.spawn_actor_from_class(
        unreal.SceneCapture2D.static_class(),
        location,
        rotation,
    )
    if not capture_actor:
        return {"ok": False, "error": "SceneCapture2D spawn failed"}

    try:
        components = capture_actor.get_components_by_class(unreal.SceneCaptureComponent2D)
        if not components:
            return {"ok": False, "error": "SceneCapture2D component missing"}
        component = components[0]
        component.set_editor_property("texture_target", render_target)
        component.set_editor_property(
            "capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR
        )
        component.set_editor_property("capture_every_frame", False)
        component.set_editor_property("capture_on_movement", False)
        component.set_editor_property("fov_angle", float(fov))
        component.capture_scene()
        unreal.RenderingLibrary.export_render_target(
            world,
            render_target,
            str(output_path.parent),
            output_path.name,
        )
        return {"ok": True, "path": str(output_path)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
    finally:
        try:
            actor_subsystem.destroy_actor(capture_actor)
        except Exception:
            pass


def _capture_views(unreal, world, actor_subsystem, world_bounds, output_dir):
    captures = {}

    try:
        viewport_location, viewport_rotation = (
            unreal.EditorLevelLibrary.get_level_viewport_camera_info()
        )
        captures["viewport"] = _capture_from_transform(
            unreal,
            world,
            actor_subsystem,
            viewport_location,
            viewport_rotation,
            output_dir / "viewport_latest.png",
            55.0,
        )
    except Exception as exc:
        captures["viewport"] = {"ok": False, "error": str(exc)}

    if world_bounds:
        center = world_bounds["center"]
        size = world_bounds["size_cm"]
        span = max(size["x"], size["y"], 1000.0)
        top_location = unreal.Vector(
            center["x"],
            center["y"],
            world_bounds["max"]["z"] + span * 0.75,
        )
        top_rotation = unreal.Rotator(-90.0, 0.0, -90.0)
        # Perspective capture is intentionally used for engine reliability.
        # The JSON carries exact bounds; this image is a spatial orientation plate.
        captures["top"] = _capture_from_transform(
            unreal,
            world,
            actor_subsystem,
            top_location,
            top_rotation,
            output_dir / "top_latest.png",
            75.0,
        )

    return captures


def snapshot_scene(capture_images=True):
    import unreal

    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    unreal_editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)

    current_level = level_editor.get_current_level()
    if not current_level:
        raise RuntimeError("No editor level is currently loaded.")

    level_path = current_level.get_path_name().split(":", 1)[0]
    level_name = level_path.rsplit("/", 1)[-1].split(".", 1)[0]
    world = unreal_editor.get_editor_world()

    actors = actor_subsystem.get_all_level_actors() or []
    selected = actor_subsystem.get_selected_level_actors() or []
    selected_ids = set()
    for actor in selected:
        try:
            selected_ids.add(str(actor.get_path_name()))
        except Exception:
            selected_ids.add(str(actor.get_actor_label()))

    rows = [_actor_row(actor, unreal, selected_ids) for actor in actors]
    class_counts = Counter(row["class"] for row in rows)
    world_bounds = _world_bounds(rows)

    sorted_rows = sorted(
        rows,
        key=lambda row: (-row["_priority"], row["label"].lower()),
    )
    context_rows = []
    for row in sorted_rows[:MAX_CONTEXT_ACTORS]:
        row = dict(row)
        row.pop("_priority", None)
        context_rows.append(row)

    pcg_rows = []
    for row in sorted_rows:
        if "pcg" not in row:
            continue
        clean = dict(row)
        clean.pop("_priority", None)
        pcg_rows.append(clean)
        if len(pcg_rows) >= MAX_PCG_ACTORS:
            break

    selected_rows = [row for row in context_rows if row.get("selected")]
    tagged_rows = [
        row for row in context_rows if ROUTE_TAGS.intersection(row.get("tags", []))
    ]

    try:
        viewport_location, viewport_rotation = (
            unreal.EditorLevelLibrary.get_level_viewport_camera_info()
        )
        viewport = {
            "location": _vec(viewport_location),
            "rotation": _rot(viewport_rotation),
        }
    except Exception:
        viewport = None

    output_dir = (
        Path(unreal.Paths.project_saved_dir())
        / "Audit"
        / "SceneContext"
        / level_name
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "schema": "melodia.scene_context.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "authority": (
            "Ephemeral spatial context only. CURRENT_STATE.md and durable subsystem "
            "contracts remain authoritative."
        ),
        "level": {
            "name": level_name,
            "path": level_path,
            "actor_count": len(rows),
            "world_bounds": world_bounds,
        },
        "viewport": viewport,
        "human_scale_cm": {
            "corridor_width": 300,
            "clear_height": 240,
            "hall_width": 1200,
        },
        "route_tag_contract": sorted(ROUTE_TAGS),
        "class_counts": dict(sorted(class_counts.items())),
        "selected_actors": selected_rows,
        "route_and_exclusion_actors": tagged_rows,
        "pcg_actors": pcg_rows,
        "spatial_context_actors": context_rows,
        "truncation": {
            "spatial_context_limit": MAX_CONTEXT_ACTORS,
            "pcg_limit": MAX_PCG_ACTORS,
            "all_actor_count": len(rows),
        },
        "agent_preflight": [
            "Read CURRENT_STATE.md plus the relevant durable lane contract.",
            "Inspect viewport_latest.png and top_latest.png before changing composition.",
            "Respect WP_PrimaryRoute, WP_NoScatter, PCG_Exclude and WP_LandmarkClear.",
            "Check player-scale and landmark silhouette before adding procedural density.",
            "After edits, regenerate this packet and compare the same spatial anchors.",
            "A saved editor result is not promoted until intended uassets/external actors are tracked.",
        ],
    }

    if capture_images:
        report["captures"] = _capture_views(
            unreal, world, actor_subsystem, world_bounds, output_dir
        )

    latest_path = output_dir / "scene_context_latest.json"
    latest_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    unreal.log(
        "[SceneContext] %s actors=%d pcg=%d selected=%d -> %s"
        % (
            level_name,
            len(rows),
            len(pcg_rows),
            len(selected_rows),
            latest_path,
        )
    )
    return report


if __name__ == "__main__":
    print(json.dumps(snapshot_scene(capture_images=True), indent=2))
