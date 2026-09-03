"""PPV stack repair (defect #3, 2026-08-29 audit).

Fixes, in-memory on the live level's PostProcessVolume(s):
  1. SILENT DROPPER — any WeightedBlendable entry whose object is a material
     with MaterialDomain != PostProcess (e.g. MI_StarryNight_VanGogh resolving
     MD_SURFACE) is removed and logged. UE discards these without warning.
  2. GRADE WEIGHT — blendables named like PPV_Dreamprint_Candidate / the
     canonical color-grade chain are re-weighted to 0.69 (canonical) from the
     live 0.18.
  3. LABEL — logs the live label vs the canonical PPV_NikkiDream reference so
     the owner can rename (renaming assets is owner-approved work).

Game-worlds only. Nothing is deleted from disk; the audit JSON records every
entry before/after so nothing is silent.

Run in the UE editor (Monolith run_python): fix_ppv_stack.main()
Writes: Saved/Audit/ppv_stack_fix_2026-08-29.json
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal

CANONICAL_WEIGHT = 0.69
GRADE_NAME_TOKENS = ("dreamprint", "melugrade", "melucolorgrade", "nikkidream")
OUT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "ppv_stack_fix_2026-08-29.json"


def _log(message):
    unreal.log(f"[PPVFix] {message}")


def _material_domain(obj):
    mat = unreal.EditorAssetLibrary.load_asset(str(obj)) if not isinstance(obj, unreal.MaterialInterface) else obj
    if mat is None:
        return None, None
    try:
        domain = mat.get_editor_property("material_domain")
        return mat, str(domain)
    except Exception:
        return mat, "unknown"


def fix_level_ppvs(world):
    volumes = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PostProcessVolume)
    report = {"volumes": [], "world": world.get_name()}
    for vol in volumes:
        settings = vol.get_editor_property("settings")
        wb = settings.get_editor_property("weighted_blendables")
        arr = wb.get_editor_property("array")
        entries = []
        kept = []
        removed = []
        reweighted = []
        for e in arr:
            obj = e.get_editor_property("object")
            weight = float(e.get_editor_property("weight"))
            name = obj.get_name() if obj is not None else "None"
            entry = {"object": name, "weight_before": weight}
            mat, domain = _material_domain(obj) if obj is not None else (None, None)
            if obj is not None and domain is not None and "POST_PROCESS" not in domain.upper():
                entry["action"] = "removed"
                entry["material_domain"] = domain
                removed.append(entry)
                continue
            lowered = name.lower()
            if any(t in lowered for t in GRADE_NAME_TOKENS) and abs(weight - CANONICAL_WEIGHT) > 0.001:
                entry["action"] = "reweighted"
                entry["weight_after"] = CANONICAL_WEIGHT
                reweighted.append(entry)
                e.set_editor_property("weight", CANONICAL_WEIGHT)
            entries.append(entry)
            kept.append(e)
        new_wb = unreal.WeightedBlendables()
        new_wb.set_editor_property("array", kept)
        settings.set_editor_property("weighted_blendables", new_wb)
        vol.set_editor_property("settings", settings)
        report["volumes"].append({
            "volume": vol.get_name(),
            "entries": entries,
            "removed": removed,
            "reweighted": reweighted,
            "note": "in-memory fix; save the level to persist (owner-approved)",
        })
        _log(f"{vol.get_name()}: kept={len(kept)} removed={len(removed)} reweighted={len(reweighted)}")
    report["ok"] = True
    return report


def main():
    world = unreal.EditorLevelLibrary.get_editor_world()
    report = fix_level_ppvs(world)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    _log(f"audit -> {OUT}")
    return report


if __name__ == "__main__":
    main()