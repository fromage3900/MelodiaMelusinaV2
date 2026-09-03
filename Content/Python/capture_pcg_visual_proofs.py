"""Capture additive PCG proof cameras without entering PIE.

This is intentionally a render-only harness. It loads each protected proof
level, resolves the authored overview camera, and asks the editor automation
renderer for a high-resolution frame from that camera. No gameplay world or
audio subsystem is started.
"""
from __future__ import annotations

import json
from pathlib import Path


PROOFS = (
    (
        "/Game/EnvSandbox/PCG/Musical/Hero/L_PCG_Hero_ResonanceCathedral",
        "Resonance Cathedral Overview Camera",
        "PCG_Hero_ResonanceCathedral_ScaleWorld_Polish.png",
    ),
    (
        "/Game/EnvSandbox/PCG/Musical/Hero/L_PCG_Hero_ArpeggioBridge",
        "Arpeggio Bridge Overview Camera",
        "PCG_Hero_ArpeggioBridge_ScaleWorld_Polish.png",
    ),
    (
        "/Game/EnvSandbox/PCG/Musical/Hero/L_PCG_Hero_BellTreeGarden",
        "BellTreeGarden Overview Camera",
        "PCG_Hero_BellTreeGarden_ScaleWorld_Polish.png",
    ),
    (
        "/Game/EnvSandbox/PCG/Musical/Hero/L_PCG_Hero_CrystalHarpGrove",
        "Crystal Harp Grove Overview Camera",
        "PCG_Hero_CrystalHarpGrove_ScaleWorld_Polish.png",
    ),
)


def capture() -> dict:
    import unreal

    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    output_dir = Path(unreal.Paths.project_saved_dir()) / "Audit"
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for level_path, camera_label, filename in PROOFS:
        if not level_editor.load_level(level_path):
            raise RuntimeError(f"could not load proof level: {level_path}")
        camera = next(
            (actor for actor in (actors.get_all_level_actors() or []) if actor.get_actor_label() == camera_label),
            None,
        )
        if camera is None:
            raise RuntimeError(f"overview camera missing: {camera_label}")
        output_path = output_dir / filename
        unreal.AutomationLibrary.finish_loading_before_screenshot()
        unreal.AutomationLibrary.take_high_res_screenshot(
            1920,
            1080,
            str(output_path),
            camera,
            False,
            False,
            delay=0.20,
            force_game_view=True,
        )
        rows.append({"level": level_path, "camera": camera_label, "output": str(output_path)})
    result = {"ok": True, "pie": False, "music_framework_started": False, "captures": rows}
    unreal.log(f"[PCG Visual Proofs] {json.dumps(result)}")
    return result


if __name__ == "__main__":
    print(json.dumps(capture(), indent=2))
