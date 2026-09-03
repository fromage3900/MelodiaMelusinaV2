"""Read-only verify: three cine cams present, no void backdrop.

Does not spawn/move cameras, lights, materials, or PPV unless --repair-cameras
(only then: destroy void labels + ensure three cams via prep_cameras).

  py Content/Python/verify_material_studio_session.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

import mi_preview_studio as studio

REPORT = studio.PROJECT_ROOT / "Saved" / "Audit" / "material_studio_session_verify.json"

EXPECTED_CAMS = (
    "CineCamera_PreviewLoop",
    "CineCamera_StillBeauty",
    "CineCamera_Detail",
)

VOID_HINTS = (
    "Backdrop_MelodiaVoid",
    "Backdrop_Cyclorama",
    "MelodiaVoid",
)


def verify(*, repair: bool = False) -> dict:
    import unreal

    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)

    world = ues.get_editor_world() if ues else None
    world_name = world.get_name() if world else None
    if world_name and "MaterialPreview_Studio" not in str(world_name):
        if les:
            les.load_level(studio.LEVEL)
            world = ues.get_editor_world() if ues else None
            world_name = world.get_name() if world else None

    labels = [a.get_actor_label() for a in (eas.get_all_level_actors() or [])]
    cams_found = [c for c in EXPECTED_CAMS if c in labels]
    void_present = [
        lab
        for lab in labels
        if any(h in lab for h in VOID_HINTS) or lab == studio.TAG_BACKDROP
    ]

    repaired = None
    if repair and (len(cams_found) < 3 or void_present):
        import prep_nikki_material_studio as prep

        repaired = prep.prep_cameras()
        labels = [a.get_actor_label() for a in (eas.get_all_level_actors() or [])]
        cams_found = [c for c in EXPECTED_CAMS if c in labels]
        void_present = [
            lab
            for lab in labels
            if any(h in lab for h in VOID_HINTS) or lab == studio.TAG_BACKDROP
        ]

    ok = len(cams_found) == 3 and not void_present
    report = {
        "ok": ok,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "level": studio.LEVEL,
        "world": world_name,
        "scope": "verify_cameras_no_void",
        "cameras_expected": list(EXPECTED_CAMS),
        "cameras_found": cams_found,
        "void_backdrop_actors": void_present,
        "actor_count": len(labels),
        "labels": labels,
        "repaired": repaired,
        "session_rules": {
            "agent_may": ["cine_cameras_place_aim_focal_pilot"],
            "agent_must_not": [
                "void_backdrop",
                "lights",
                "ppv",
                "material_params",
                "HighResShot",
                "SceneCapture",
                "NightShift_remount",
                "MRQ_unless_asked",
            ],
        },
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({
        "ok": ok,
        "cameras_found": cams_found,
        "void_backdrop_actors": void_present,
        "world": world_name,
    }))
    return report


def main() -> int:
    repair = "--repair-cameras" in sys.argv
    report = verify(repair=repair)
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
