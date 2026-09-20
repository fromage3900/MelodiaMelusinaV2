# -*- coding: utf-8 -*-
"""Measure Melusina house long-floor bases + anchors (READ-ONLY)."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

OUT = Path(unreal.Paths.project_saved_dir()) / "Audit" / "house_room_bases_measure_2026-09-20.json"
FLOOR_TOKENS = ("Floor", "SM_ATL_Palace_Floor", "SM_Greybox_Floor", "SM_room", "corridor")
ANCHORS = (
    "Morning_Bed", "Dress_BedBedding", "Morning_QuillTrigger_Wardrobe",
    "SM_room_2", "SM_room1", "SM_Bookshelf", "SM_corridor",
)


def _lab(a):
    try:
        return a.get_actor_label() or ""
    except Exception:
        return ""


def _cls(a):
    try:
        return a.get_class().get_name()
    except Exception:
        return ""


def _mesh_path(a):
    try:
        c = a.get_component_by_class(unreal.StaticMeshComponent)
        if not c:
            return ""
        m = c.get_editor_property("static_mesh")
        return m.get_path_name() if m else ""
    except Exception:
        return ""


def main():
    svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    floors, anchors, other = [], {}, []
    for a in svc.get_all_level_actors():
        lab = _lab(a)
        mp = _mesh_path(a)
        blob = lab + " " + mp + " " + _cls(a)
        loc = a.get_actor_location()
        rec = {
            "label": lab,
            "class": _cls(a),
            "mesh": mp,
            "loc": [round(loc.x, 1), round(loc.y, 1), round(loc.z, 1)],
        }
        try:
            sc = a.get_actor_scale3d()
            rec["scale"] = [round(sc.x, 3), round(sc.y, 3), round(sc.z, 3)]
        except Exception:
            pass
        if lab in ANCHORS or any(lab.startswith(x) for x in ANCHORS):
            anchors[lab] = rec
        if any(t.lower() in blob.lower() for t in FLOOR_TOKENS):
            floors.append(rec)
        if lab.startswith("MH_") or "Melusina" in lab or "House" in lab:
            other.append(rec)

    report = {
        "schema": "melodia.house_room_bases_measure.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "read_only": True,
        "world": unreal.SystemLibrary.get_object_name(
            unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        ),
        "anchors": anchors,
        "floorish_actors": floors,
        "houseish_sample": other[:80],
        "counts": {"floors": len(floors), "anchors": len(anchors), "houseish": len(other)},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print("HOUSE_BASES " + json.dumps(report["counts"]))
    unreal.log("HOUSE_BASES wrote " + str(OUT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
