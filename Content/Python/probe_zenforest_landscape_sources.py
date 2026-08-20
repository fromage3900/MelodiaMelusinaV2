"""Find the landscape material to assign to ZenForestTest's Landscape2.

Reads the level's other landscape actor's material (consistency), then lists
the project's landscape material assets as candidates.
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal

LEVEL = "/Game/ZenForestTest"
REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "zenforest_landscape_sources.json"

out: dict = {"level_materials": {}, "candidates": []}


def main() -> None:
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    les.load_level(LEVEL)
    for actor in eas.get_all_level_actors() or []:
        if type(actor).__name__ != "Landscape":
            continue
        label = actor.get_actor_label()
        mats = set()
        for comp in actor.get_components_by_class(unreal.LandscapeComponent) or []:
            try:
                lm = comp.get_editor_property("landscape_material")
                mats.add(str(lm.get_path_name()) if lm else None)
            except Exception:
                pass
        out["level_materials"][label] = sorted(str(m) for m in mats)
        print(label, sorted(str(m) for m in mats))

    for folder in ("/Game/EnvSandbox/Materials/Landscape",
                   "/Game/EnvSandbox/Materials/Instances/Landscape"):
        assets = unreal.EditorAssetLibrary.list_assets(folder, recursive=True) or []
        for a in assets:
            if a.endswith((".M_Landscape", ".MI_Landscape", ".M_Grass", ".MI_Grass")):
                out["candidates"].append(a)
        print(folder, [a for a in assets if "Landscape" in a or "Grass" in a][:12])

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(out, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()