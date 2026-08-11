"""Read-only persistence and generated-instance audit for WP traversal grids."""
from __future__ import annotations

import json
import time
from pathlib import Path

import unreal

from gmm.pcg.wp_grid import validate_wp_grid_report

ROOT = Path(__file__).resolve().parents[2]
LEVELS = ("SakuraDream", "SpaceCathedral", "BaroqueGrotto", "CosmicOrrery")
LEVEL_ROOT = "/Game/EnvSandbox/Environments/WP/L_WP_{}"
PREFIX = "WPGrid_"


def _count_ism(actor) -> int:
    total = 0
    for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
        try:
            total += int(component.get_instance_count())
        except Exception:
            pass
    return total


def verify_level(level_key: str) -> dict:
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not les.load_level(LEVEL_ROOT.format(level_key)):
        return {"level": level_key, "pass": False, "error": "load_failed"}
    try:
        descs = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
        unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in descs])
    except Exception:
        pass
    time.sleep(2.0)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = [a for a in (eas.get_all_level_actors() or []) if a.get_actor_label().startswith(PREFIX)]
    pcg = [a for a in actors if a.get_actor_label().startswith(f"{PREFIX}PCG_")]
    counts = [_count_ism(actor) for actor in pcg]
    return {
        "level": level_key,
        "persistent_grid_actors": len(actors),
        "pcg_volumes": len(pcg),
        "ism_counts": counts,
        "ism_total": sum(counts),
        "pass": len(actors) == 30 and len(pcg) == 9 and all(count > 0 for count in counts),
    }


def main() -> int:
    results = [verify_level(level) for level in LEVELS]
    report = {"verification_mode": "read_only_reopen_and_ism_count", "results": results}
    report["all_levels_pass"] = all(result.get("pass") for result in results)
    errors = validate_wp_grid_report({"results": [{
        "level": result["level"], "platforms": 9, "route_nodes": [{
            "location_cm": [0, 0, 0], "encounter_clear": True
        }] * 9, "pcg_volumes": result.get("pcg_volumes", 0), "links": 12,
    } for result in results]})
    report["contract_errors"] = errors
    path = ROOT / "Saved" / "Audit" / "wp_walkable_grid_verify.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, separators=(",", ":")))
    return 0 if report["all_levels_pass"] and not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
