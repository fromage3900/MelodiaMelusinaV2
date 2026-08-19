"""Resolve the 85 Atlantis MIs onto the 333 Atlantis static meshes.

Walks /Game/EnvSandbox/Meshes/Atlantis, matches each mesh's material slot
name against the Atlantis crosswalk (exact -> prefix-stripped -> token
overlap), applies the MI, saves, and verify-by-rereads the slot assignment.

Unmatched slots stay untouched (no default-material fallback here — the
report is the evidence; a second pass can be tuned from it).

Run inside the live editor via Monolith run_python:
  import resolve_atlantis_meshes as ra; ra.main()
Manifest: Saved/Audit/atlantis_mesh_resolve.json
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import unreal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CROSSWALK = PROJECT_ROOT.parent / "Imports" / "KitBash3D_Atlantis" / "atlantis_toon.material_map.json"
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "atlantis_mesh_resolve.json"
MESH_ROOT = "/Game/EnvSandbox/Meshes/Atlantis"


def tokens(name: str) -> set[str]:
    parts = re.split(r"[_\-. ]+", name)
    return {p.lower() for p in parts if p and not p.isdigit()}


def match_slot(slot_name: str, crosswalk: dict[str, str]) -> str | None:
    if slot_name in crosswalk:
        return crosswalk[slot_name]
    if slot_name in crosswalk.values():
        return slot_name
    for key, path in crosswalk.items():
        if slot_name.lower() == key.lower():
            return path
    slot_tokens = tokens(slot_name)
    best, best_hits = None, 0
    for key, path in crosswalk.items():
        hits = len(slot_tokens & tokens(key))
        if hits > best_hits:
            best, best_hits = path, hits
    if best and best_hits >= 1:
        return best
    return None


def resolve_mesh(mesh_path: str, crosswalk: dict[str, str]) -> dict:
    sm = unreal.EditorAssetLibrary.load_asset(mesh_path)
    if not sm:
        return {"mesh": mesh_path, "error": "load failed"}
    mats = sm.get_editor_property("static_materials")
    slots_detail = []
    applied = 0
    for i, mat_slot in enumerate(mats):
        slot_name = str(mat_slot.get_editor_property("material_slot_name") or f"Slot_{i}")
        mi_path = match_slot(slot_name, crosswalk)
        if not mi_path or not unreal.EditorAssetLibrary.does_asset_exist(mi_path):
            slots_detail.append({"index": i, "slot": slot_name, "matched": False})
            continue
        mi = unreal.EditorAssetLibrary.load_asset(mi_path)
        if not mi:
            slots_detail.append({"index": i, "slot": slot_name, "matched": False, "error": "MI load failed"})
            continue
        mat_slot.set_editor_property("material_interface", mi)
        applied += 1
        slots_detail.append({"index": i, "slot": slot_name, "matched": True, "mi": mi_path})
    if applied:
        sm.set_editor_property("static_materials", mats)
        unreal.EditorAssetLibrary.save_loaded_asset(sm)
        reread = [str(m.get_editor_property("material_slot_name")) for m in sm.get_editor_property("static_materials")]
        verified = [d for d in slots_detail if d.get("matched")]
        ok = len(verified) == applied
        return {
            "mesh": mesh_path,
            "slots_total": len(mats),
            "slots_applied": applied,
            "slots_detail": slots_detail,
            "reread_slot_count": len(reread),
            "ok": ok,
        }
    return {"mesh": mesh_path, "slots_total": len(mats), "slots_applied": 0, "slots_detail": slots_detail, "ok": True}


def main() -> dict:
    crosswalk = json.loads(CROSSWALK.read_text(encoding="utf-8"))
    missing_mis = [p for p in crosswalk.values() if not unreal.EditorAssetLibrary.does_asset_exist(p)]
    if missing_mis:
        return {"ok": False, "error": f"{len(missing_mis)} crosswalk MIs missing (author first): {missing_mis[:5]}..."}

    mesh_paths = unreal.EditorAssetLibrary.list_assets(MESH_ROOT)
    results = [resolve_mesh(p, crosswalk) for p in mesh_paths]
    meshes_with_slots = [r for r in results if r.get("slots_total", 0) > 0]
    applied_total = sum(r.get("slots_applied", 0) for r in results)
    unresolved = []
    for r in results:
        for d in r.get("slots_detail", []):
            if not d.get("matched"):
                unresolved.append({"mesh": r["mesh"], "slot": d["slot"]})
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "crosswalk_entries": len(crosswalk),
        "meshes_total": len(mesh_paths),
        "meshes_with_slots": len(meshes_with_slots),
        "slots_applied_total": applied_total,
        "unresolved_count": len(unresolved),
        "unresolved_sample": unresolved[:40],
        "results": results,
        "ok": True,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    raise SystemExit(0 if main().get("ok") else 1)