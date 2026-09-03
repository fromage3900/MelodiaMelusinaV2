"""Give ZenForestTest's Landscape2 the dream landscape material.

Assigns MI_Landscape_NikkiDream to every LandscapeComponent of Landscape2,
saves the level, and reports the assignment.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "zenforest_landscape_fix.json"
MAT = "/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_NikkiDream"


def main() -> dict:
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    les.load_level("/Game/ZenForestTest")

    mat = unreal.load_asset(MAT)
    if not mat:
        raise RuntimeError(f"missing {MAT}")

    assigned = []
    for actor in eas.get_all_level_actors() or []:
        if type(actor).__name__ != "Landscape":
            continue
        for comp in actor.get_components_by_class(unreal.LandscapeComponent) or []:
            try:
                comp.set_editor_property("landscape_material", mat)
                assigned.append(comp.get_name())
            except Exception as exc:
                assigned.append(f"{comp.get_name()} ERROR {exc}")
    les.save_current_level()

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "material": MAT,
        "components_assigned": assigned,
        "count": len(assigned),
        "ok": len(assigned) > 0,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    raise SystemExit(0 if main().get("ok") else 1)