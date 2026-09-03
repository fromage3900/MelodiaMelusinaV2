"""Capture scene metadata (actors, PCG volumes, material usage) to Saved/Portfolio/SceneMetadata/.

Run (editor):
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/capture_scene_metadata.py"
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = PROJECT_ROOT / "Saved" / "Portfolio" / "SceneMetadata"
REPORT = OUT_DIR / "scene_metadata.json"


def _actor_summary(actor) -> dict:
    label = actor.get_actor_label()
    loc = actor.get_actor_location()
    return {
        "label": label,
        "class": actor.get_class().get_name(),
        "location": [loc.x, loc.y, loc.z] if loc else None,
        "tags": list(getattr(actor, "tags", []) or []),
    }


def _pcg_summary(vol) -> dict:
    graph = None
    try:
        comp = vol.get_component_by_class(type(vol).__bases__[0] if hasattr(type(vol), "__bases__") else None)
    except Exception:
        comp = None
    try:
        for comp in vol.get_components_by_class(None):
            if hasattr(comp, "get_graph"):
                graph = comp.get_graph()
                if graph:
                    break
    except Exception:
        pass
    return {
        "label": vol.get_actor_label(),
        "graph": graph.get_path_name() if graph else None,
    }


def capture_scene_metadata() -> dict:
    import unreal

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    actors = []
    pcg_volumes = []
    material_counts = {}
    try:
        eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    except Exception as exc:
        return {"ok": False, "error": f"EditorActorSubsystem unavailable: {exc}"}
    try:
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    except Exception as exc:
        return {"ok": False, "error": f"editor world unavailable: {exc}"}

    for actor in eas.get_all_level_actors() or []:
        actors.append(_actor_summary(actor))
        try:
            for comp in actor.get_components_by_class(unreal.PCGComponent):
                pcg_volumes.append(_pcg_summary(actor))
                break
        except Exception:
            pass
        try:
            for smc in actor.get_components_by_class(unreal.StaticMeshComponent):
                mats = smc.get_materials()
                for m in mats:
                    if m:
                        material_counts[m.get_name()] = material_counts.get(m.get_name(), 0) + 1
        except Exception:
            pass

    return {
        "ok": True,
        "world": world.get_name() if world else None,
        "actor_count": len(actors),
        "pcg_volume_count": len(pcg_volumes),
        "material_instance_counts": material_counts,
        "actors": actors,
        "pcg_volumes": pcg_volumes,
    }


def main() -> int:
    result = capture_scene_metadata()
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "capture_scene_metadata.py",
        "ok": result.get("ok", False),
        **result,
    }
    REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"SCENE_METADATA captured -> {REPORT}")
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())