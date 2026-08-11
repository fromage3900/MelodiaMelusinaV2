"""Audit the generated PCG piano assets and, when run in a level, its actors."""

from __future__ import annotations

from pcg_piano_layout import build_layout, split_layout, unpack_seed


GRAPH_PATH = "/Game/EnvSandbox/PCG/Musical/PCG_PianoKeyboard"
PROFILE_PATH = "/Game/EnvSandbox/PCG/Musical/DA_PianoKeyboardProfile"
LEVEL_PATH = "/Game/EnvSandbox/PCG/Musical/L_PCG_PianoKeyboard"


def audit() -> dict:
    import unreal

    specs = build_layout()
    whites, blacks = split_layout(specs)
    report = {
        "expected": {"total": len(specs), "white": len(whites), "black": len(blacks)},
        "assets": {},
        "graph": {},
        "level": {},
        "checks": {},
    }

    for path in (
        GRAPH_PATH,
        PROFILE_PATH,
        "/Game/EnvSandbox/PCG/Musical/SM_PianoKey_White_Bevel",
        "/Game/EnvSandbox/PCG/Musical/SM_PianoKey_Black_Bevel",
        "/Game/EnvSandbox/PCG/Musical/SM_Piano_Keybed",
        "/Game/EnvSandbox/PCG/Musical/MI_Piano_Ivory",
        "/Game/EnvSandbox/PCG/Musical/MI_Piano_Ebony",
    ):
        report["assets"][path] = unreal.EditorAssetLibrary.does_asset_exist(path)

    graph = unreal.EditorAssetLibrary.load_asset(GRAPH_PATH)
    if graph:
        nodes = list(graph.get_editor_property("nodes") or [])
        edges = []
        for node in nodes:
            try:
                edges.extend(list(node.get_editor_property("edges") or []))
            except Exception:
                pass
        report["graph"] = {"nodes": len(nodes), "edges_seen": len(edges), "path": GRAPH_PATH}

    report["checks"]["seed_round_trip"] = all(unpack_seed(spec.seed) == (spec.key_index, spec.midi_note) for spec in specs)
    report["checks"]["key_counts"] = (len(specs), len(whites), len(blacks)) == (88, 52, 36)

    level = unreal.EditorAssetLibrary.load_asset(LEVEL_PATH)
    if level:
        report["level"]["exists"] = True
    try:
        eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        actors = eas.get_all_level_actors() or []
        piano_keys = [actor for actor in actors if "PCG_PianoKey" in [str(tag) for tag in (actor.tags or [])]]
        report["level"].update(
            {
                "loaded_level_actor_count": len(actors),
                "piano_key_actor_count": len(piano_keys),
                "white_actor_count": sum("PCG_PianoWhite" in [str(tag) for tag in (actor.tags or [])] for actor in piano_keys),
                "black_actor_count": sum("PCG_PianoBlack" in [str(tag) for tag in (actor.tags or [])] for actor in piano_keys),
            }
        )
    except Exception as exc:
        report["level"]["actor_audit_error"] = str(exc)

    report["checks"]["assets_present"] = all(report["assets"].values())
    unreal.log(f"[PCG Piano] audit {report}")
    return report


if __name__ == "__main__":
    print(audit())
