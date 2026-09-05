"""Apply the gameplay PPV stack as PPV_NikkiDream on certification levels.

The gameplay stack is the grandmaster outline + grade + ink. StarryNight_Hero is
reserved for cinematic/lookdev use. Sea Above is a shipping map and a gameplay
certification target. No grade tuning values are touched.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

from ppv_contract import GAMEPLAY_PPV_CERTIFICATION_LEVELS, GAMEPLAY_STACK

REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "dream_candidate_ppv_apply.json"

LEVELS = GAMEPLAY_PPV_CERTIFICATION_LEVELS
STACK = GAMEPLAY_STACK


def main() -> dict:
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    mats = []
    for path, _w in STACK:
        mat = unreal.load_asset(path)
        if not mat:
            raise RuntimeError(f"missing stack asset: {path}")
        mats.append(mat)

    results = []
    for level in LEVELS:
        leaf = level.rsplit("/", 1)[-1]
        rec = {"level": level}
        if not unreal.EditorAssetLibrary.does_asset_exist(f"{level}.{leaf}"):
            rec["status"] = "missing"
            results.append(rec)
            continue
        les.load_level(level)
        ppv = next((a for a in eas.get_all_level_actors() or []
                    if a.get_actor_label() == "PPV_NikkiDream"), None)
        if ppv is None:
            ppv = eas.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0, 0, 0))
            ppv.set_actor_label("PPV_NikkiDream")
            rec["spawned"] = True
        ppv.set_editor_property("unbound", True)
        ppv.set_editor_property("enabled", True)
        settings = ppv.get_editor_property("settings")
        settings.set_editor_property("weighted_blendables", unreal.WeightedBlendables(
            [unreal.WeightedBlendable(w, m) for (_, _w), m in zip(STACK, mats) if (w := _w)]))
        ppv.set_editor_property("settings", settings)
        les.save_current_level()
        rec["status"] = "ok"
        results.append(rec)

    les.load_level("/Game/ZenForestTest")
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stack": [p for p, _ in STACK],
        "levels": results,
        "ok": all(r["status"] == "ok" for r in results),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    raise SystemExit(0 if main().get("ok") else 1)
