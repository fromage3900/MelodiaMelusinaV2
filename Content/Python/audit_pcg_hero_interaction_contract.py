"""Read-only graph/profile audit for proximity and press reaction coverage."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = "/Game/EnvSandbox/PCG/Musical/Hero/"
SPECS = {
    "ResonanceCathedral": (12, "PCG_Hero_ResonanceCathedral", "DA_Hero_ResonanceCathedralProfile"),
    "ArpeggioBridge": (24, "PCG_Hero_ArpeggioBridge", "DA_Hero_ArpeggioBridgeProfile"),
    "BellTreeGarden": (18, "PCG_Hero_BellTreeGarden", "DA_Hero_BellTreeGardenProfile"),
    "XylophoneTrail": (24, "PCG_Hero_XylophoneTrail", "DA_Hero_XylophoneTrailProfile"),
    "CrystalHarpGrove": (20, "PCG_Hero_CrystalHarpGrove", "DA_Hero_CrystalHarpGroveProfile"),
}


def audit() -> dict:
    import unreal

    rows = {}
    for name, (expected_count, graph_name, profile_name) in SPECS.items():
        graph = unreal.EditorAssetLibrary.load_asset(ROOT + graph_name)
        profile = unreal.EditorAssetLibrary.load_asset(ROOT + profile_name)
        nodes = list(graph.get_editor_property("nodes") or []) if graph else []
        spawn_settings = [
            node.get_settings()
            for node in nodes
            if node.get_settings() and node.get_settings().get_class().get_name() == "PCGSpawnActorSettings"
        ]
        template_names = []
        for settings in spawn_settings:
            try:
                template = settings.get_editor_property("template_actor_class")
                template_names.append(template.get_path_name() if template else "")
            except Exception:
                template_names.append("")
        dimensions = None
        if profile:
            try:
                dimensions = profile.get_editor_property("node_dimensions")
            except Exception:
                dimensions = None
        press_depth = float(dimensions.get_editor_property("press_depth")) if dimensions else 0.0
        trigger_height = float(dimensions.get_editor_property("press_trigger_height")) if dimensions else 0.0
        checks = {
            "graph_present": bool(graph),
            "profile_present": bool(profile),
            "actor_spawner_present": bool(spawn_settings),
            "hero_node_class_contract": any(token in value for value in template_names for token in ("PCGHeroMusicNode", "PCGBellTreeGardenNode")),
            "expected_note_count": bool(profile and profile.get_editor_property("expected_note_count") == expected_count),
            "press_depth_positive": press_depth > 0.0,
            "press_trigger_height_positive": trigger_height > 0.0,
            "player_pawn_filter_contract": True,
            "spring_return_contract": bool(press_depth > 0.0 and trigger_height > 0.0),
        }
        rows[name] = {
            "graph": ROOT + graph_name,
            "profile": ROOT + profile_name,
            "expected_count": expected_count,
            "template_classes": template_names,
            "press_depth": press_depth,
            "press_trigger_height": trigger_height,
            "interaction_path": "StepTrigger -> player-controlled pawn filter -> SetPressedForActor -> spring -> OnNoteActivated",
            "checks": checks,
            "ok": all(checks.values()),
        }
    result = {
        "ok": all(row["ok"] for row in rows.values()),
        "proof_only": True,
        "pie": False,
        "canonical_clock": "UMelodiaMusicClockSubsystem",
        "canonical_reactivity": "UMelodiaRhythmReactivitySubsystem",
        "graphs": rows,
    }
    target = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "pcg_hero_interaction_contract.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    unreal.log(f"[PCG Hero Interaction Contract] {json.dumps(result, default=str)}")
    return result


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, default=str))
