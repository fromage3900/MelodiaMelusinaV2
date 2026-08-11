"""Create deterministic CineCamera shot markers for technical portfolio captures.

Run inside the UE editor Python environment. Existing cameras with the same
labels are reused; no level actors are deleted. The script writes a manifest
consumed by the offline website exporter.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


PROJECT_ROOT = Path(unreal.Paths.project_dir())
MANIFEST = PROJECT_ROOT / "Saved" / "Portfolio" / "technical_breakdown_cameras.json"

SHOTS = (
    {"id": "shader_master", "label": "Cam_Breakdown_ShaderMaster", "target": "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal", "proof": "shader_graph", "destination": "renders.breakdown"},
    {"id": "material_instance", "label": "Cam_Breakdown_MaterialInstance", "target": "/Game/EnvSandbox/Materials/Instances", "proof": "material_instance", "destination": "renders.materials"},
    {"id": "pcg_heatmap", "label": "Cam_Breakdown_PCGHeatmap", "target": "PCG volumes in current level", "proof": "pcg_heatmap", "destination": "renders.pcg"},
    {"id": "trim_sheet", "label": "Cam_Breakdown_TrimSheet", "target": "/Game/EnvSandbox/Materials/Functions", "proof": "trim_sheet", "destination": "renders.breakdown"},
    {"id": "world_shader", "label": "Cam_Breakdown_WorldShader", "target": "current level hero material", "proof": "world_shader", "destination": "renders.breakdown"},
)


def _actor_by_label(label: str):
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in subsystem.get_all_level_actors() or []:
        if actor.get_actor_label() == label:
            return actor
    return None


def _make_camera(entry: dict):
    actor = _actor_by_label(entry["label"])
    created = False
    if actor is None:
        subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        actor = subsystem.spawn_actor_from_class(unreal.CineCameraActor, unreal.Vector(0, 0, 250), unreal.Rotator(-90, 0, 0))
        actor.set_actor_label(entry["label"])
        created = True
    actor.set_actor_hidden_in_game(True)
    camera = actor.get_cine_camera_component()
    filmback = unreal.CameraFilmbackSettings()
    filmback.set_editor_property("sensor_width", 36.0)
    filmback.set_editor_property("sensor_height", 20.25)
    camera.set_editor_property("filmback", filmback)
    camera.set_editor_property("current_focal_length", 50.0)
    return {**entry, "actor_name": actor.get_name(), "path": actor.get_path_name(), "created": created}


def main() -> int:
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).get_current_level()
    if not level:
        raise RuntimeError("Open a target portfolio level before running this script")
    cameras = [_make_camera(entry) for entry in SHOTS]
    payload = {
        "format": "melodia_technical_breakdown_cameras_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "level": level.get_path_name(),
        "camera_count": len(cameras),
        "shots": cameras,
        "capture_contract": {
            "beauty_plus_proof": True,
            "resolution": [1920, 1080],
            "material_instances_source": "Saved/Audit/material_instance_audit.json",
            "pcg_source": "Saved/Portfolio/PCG/",
            "website_manifest": "my-site-clean/generated/technical/unreal-breakdown-manifest.json",
        },
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log(f"[TechnicalBreakdown] configured {len(cameras)} cameras -> {MANIFEST}")
    return 0


if __name__ == "__main__":
    main()
