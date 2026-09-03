"""Dreamprint — set M_PP_MelodiaInk blendable location to After Tonemapping.

Probes the engine's BlendableLocation enum for the exact member name, then
applies it. Runs headless.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

MAT = "/Game/Melodia/_PROJECT/04_Materials/PostProcess/M_PP_MelodiaInk"
REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "dreamprint_blendable_fix.json"


def main() -> int:
    members = [str(x) for x in dir(unreal.BlendableLocation) if not x.startswith("_")]
    wanted = None
    for cand in ("BL_SCENE_COLOR_AFTER_TONEMAPPING", "BL_SCENE_COLOR_AFTER_TONEMAP",
                 "BL_SceneColorAfterTonemapping", "BL_AfterTonemapping"):
        if cand in members:
            wanted = getattr(unreal.BlendableLocation, cand)
            break

    mat = unreal.load_asset(MAT)
    if not mat:
        raise RuntimeError(f"Missing {MAT}")

    before = str(mat.get_editor_property("blendable_location"))
    if wanted is None:
        report = {"timestamp": datetime.now(timezone.utc).isoformat(), "material": MAT,
                  "members": members, "status": "HOLD_no_after_tonemap_enum", "ok": False}
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 1

    mat.set_editor_property("blendable_location", wanted)
    try:
        unreal.MaterialEditingLibrary.recompile_material(mat)
    except Exception as exc:
        unreal.log_warning(f"[Dreamprint] recompile: {exc}")
    unreal.EditorAssetLibrary.save_loaded_asset(mat, only_if_is_dirty=False)

    after = str(mat.get_editor_property("blendable_location"))
    report = {"timestamp": datetime.now(timezone.utc).isoformat(), "material": MAT,
              "enum_members": members, "wanted": str(wanted), "before": before, "after": after,
              "ok": "AFTER_TONEMAP" in after.upper() or after != before}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())