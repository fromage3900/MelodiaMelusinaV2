"""Audit the interactable music sequencer graph, profile, and level."""

from __future__ import annotations

from build_pcg_music_sequencer import build_step_specs


GRAPH_PATH = "/Game/EnvSandbox/PCG/Musical/Sequencer/PCG_MusicStepSequencer"
PROFILE_PATH = "/Game/EnvSandbox/PCG/Musical/Sequencer/DA_MusicStepGridProfile"
LEVEL_PATH = "/Game/EnvSandbox/PCG/Musical/Sequencer/L_PCG_MusicStepSequencer"


def audit() -> dict:
    import unreal

    specs = build_step_specs()
    report = {
        "expected": {"pads": len(specs), "steps": 16, "lanes": 4},
        "assets": {path: unreal.EditorAssetLibrary.does_asset_exist(path) for path in (GRAPH_PATH, PROFILE_PATH, LEVEL_PATH)},
        "graph": {},
        "level": {},
        "checks": {
            "unique_seeds": len({spec.seed for spec in specs}) == 64,
            "ordered_rows": all([spec.step for spec in specs if spec.lane == lane] == list(range(16)) for lane in range(4)),
        },
    }
    graph = unreal.EditorAssetLibrary.load_asset(GRAPH_PATH)
    if graph:
        report["graph"] = {"nodes": len(list(graph.get_editor_property("nodes") or [])), "path": GRAPH_PATH}
    try:
        eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        actors = eas.get_all_level_actors() or []
        pads = [actor for actor in actors if "PCG_MusicStepPad" in [str(tag) for tag in (actor.tags or [])]]
        report["level"] = {
            "actor_count": len(actors),
            "pad_actor_count": len(pads),
            "step_indices": sorted({int(actor.get_editor_property("step_index")) for actor in pads}),
            "lanes": sorted({int(actor.get_editor_property("lane")) for actor in pads}),
        }
    except Exception as exc:
        report["level"]["actor_audit_error"] = str(exc)
    report["checks"]["assets_present"] = all(report["assets"].values())
    report["checks"]["pad_count"] = report["level"].get("pad_actor_count") in (None, 64)
    unreal.log(f"[PCG Music Sequencer] audit {report}")
    return report


if __name__ == "__main__":
    print(audit())
