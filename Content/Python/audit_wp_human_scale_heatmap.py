"""Audit the live human-scale/heatmap contract in each WP level."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "Saved" / "Audit" / "wp_human_scale_heatmap.json"
LEVELS = ("SakuraDream", "SpaceCathedral", "BaroqueGrotto", "CosmicOrrery")


def audit_level(key: str) -> dict:
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    les.load_level(f"/Game/EnvSandbox/Environments/WP/L_WP_{key}")
    try:
        ds = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
        unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in ds])
    except Exception:
        pass
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() or []
    def has_tag(actor, tag):
        return tag in [str(t) for t in actor.tags]
    blockout = [a for a in actors if a.get_actor_label().startswith(f"GB_{key}_")]
    pcg = [a for a in actors if a.get_actor_label().startswith("PCG_")]
    counts = []
    bounds = []
    for actor in pcg:
        counts.append(sum(c.get_instance_count() for c in actor.get_components_by_class(unreal.InstancedStaticMeshComponent)))
        bounds.append(actor.get_actor_bounds(False)[1].x)
    return {
        "level": key,
        "blockout_actor_count": len(blockout),
        "primary_route_actors": sum(has_tag(a, "WP_PrimaryRoute") for a in blockout),
        "no_scatter_actors": sum(has_tag(a, "WP_NoScatter") for a in blockout),
        "pcg_exclusion_actors": sum(has_tag(a, "PCG_Exclude") for a in blockout),
        "landmark_clear_actors": sum(has_tag(a, "WP_LandmarkClear") for a in blockout),
        "pcg_volume_count": len(pcg),
        "pcg_instance_counts": counts,
        "pcg_max_bound_cm": max(bounds or [0]),
        "scale_contract": {"corridor_width_cm": 300, "clear_height_cm": 240, "hall_width_cm": 1200},
        "heatmap_contract_present": bool(blockout) and sum(has_tag(a, "WP_NoScatter") for a in blockout) > 0,
    }


def main() -> int:
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "levels": [audit_level(k) for k in LEVELS]}
    report["all_contracts_present"] = all(x["heatmap_contract_present"] for x in report["levels"])
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[WPHeatmapAudit] wrote {REPORT}")
    return 0 if report["all_contracts_present"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
