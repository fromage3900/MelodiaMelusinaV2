"""Non-destructive PCG/world-partition audit for a named level."""
from __future__ import annotations
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "Saved/Audit/pcg_environment_audit.json"
MAP = os.environ.get("PCG_AUDIT_MAP", "/Game/ZenForestTest")

def main() -> dict:
    import unreal
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    # EditorLevelLibrary is deprecated in UE 5.8; retain the fallback for older
    # editor sessions so this audit remains portable across project branches.
    actor_subsystem = getattr(unreal, "EditorActorSubsystem", None)
    if actor_subsystem is not None:
        actors = list(unreal.get_editor_subsystem(actor_subsystem).get_all_level_actors() or [])
    else:
        actors = list(unreal.EditorLevelLibrary.get_all_level_actors() or [])
    rows = []
    ism_total = 0
    for actor in actors:
        components = list(actor.get_components_by_class(unreal.InstancedStaticMeshComponent) or [])
        components += list(actor.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent) or [])
        count = sum(int(c.get_instance_count()) for c in components)
        ism_total += count
        label = actor.get_actor_label()
        if count or any(key in label.lower() for key in ("pcg", "exclude", "ground", "pond", "path", "water")):
            rows.append({"label": label, "class": actor.get_class().get_path_name(),
                         "instance_count": count, "tags": [str(t) for t in actor.tags]})
    result = {"map": MAP, "actor_count": len(actors), "ism_total": ism_total,
              "actors": rows, "mutation": "none",
              "acceptance": {"structural_context": bool(actors), "nonzero_instances": ism_total > 0,
                             "visual_verification": "editor_pie_required"}}
    result["ok"] = bool(result["acceptance"]["structural_context"])
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    unreal.log("PCG environment audit: " + json.dumps(result, sort_keys=True))
    return result

if __name__ == "__main__":
    main()
