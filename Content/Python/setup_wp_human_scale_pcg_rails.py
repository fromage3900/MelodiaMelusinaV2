"""Place procedural human-scale corridor wall rails in each WP level."""
from __future__ import annotations

import json
from pathlib import Path

import unreal
import pcg_graph_builder as gb

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "Saved" / "Audit" / "wp_human_scale_pcg_rails.json"
GRAPH = "/Game/EnvSandbox/PCG/Styles/WP/PCG_WP_HumanScaleCorridor"
LEVELS = {"SakuraDream": 1200.0, "SpaceCathedral": 1600.0, "BaroqueGrotto": 1600.0, "CosmicOrrery": 400.0}


def build_level(key: str, length: float) -> dict:
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not les.load_level(f"/Game/EnvSandbox/Environments/WP/L_WP_{key}"):
        return {"level": key, "error": "load_failed"}
    try:
        ds = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
        unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in ds])
    except Exception:
        pass
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    graph = unreal.EditorAssetLibrary.load_asset(GRAPH)
    if not graph:
        return {"level": key, "error": "graph_missing"}
    prefix = f"PCG_{key}_HumanRail_"
    for actor in eas.get_all_level_actors() or []:
        if actor.get_actor_label().startswith(prefix):
            eas.destroy_actor(actor)
    rails = []
    for side, x in (("L", -165.0), ("R", 165.0)):
        actor = eas.spawn_actor_from_class(unreal.PCGVolume, unreal.Vector(x, length / 2.0, 120.0))
        try:
            actor.set_editor_property("is_spatially_loaded", False)
        except Exception:
            pass
        actor.set_actor_label(f"{prefix}{side}")
        actor.set_actor_scale3d(unreal.Vector(1.0, max(8.5, length / 200.0), 1.0))
        actor.tags = [unreal.Name("WP_PrimaryRoute"), unreal.Name("WP_NoScatter"), unreal.Name("GB_HumanScale"), unreal.Name("PCG_Exclude")]
        comp = actor.get_component_by_class(unreal.PCGComponent)
        gb.assign_pcg_graph(comp, graph)
        gb.configure_pcg_component(comp, seed=7001 + len(rails) * 17, activated=True)
        try:
            comp.cleanup(True)
        except Exception:
            pass
        comp.generate(True)
        actor.modify()
        rails.append(actor)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    unreal.EditorLoadingAndSavingUtils.save_map(world, f"/Game/EnvSandbox/Environments/WP/L_WP_{key}")
    return {"level": key, "route_length_cm": length, "rail_count": len(rails), "rail_spacing_cm": 330, "clear_lane_cm": 300, "clear_height_cm": 240}


def main() -> int:
    results = [build_level(k, v) for k, v in LEVELS.items()]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({"results": results}, indent=2), encoding="utf-8")
    unreal.log(f"[WPHumanRails] wrote {REPORT}")
    return 0 if all("error" not in x for x in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
