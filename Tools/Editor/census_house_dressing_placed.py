"""
Read-only census of what is ACTUALLY placed in the P0 house level.

The dressing contract is a plan; the level is the truth. This dumps every
dressing-labelled actor with its mesh and transform so the contract can be
reconciled with reality (and the owner's own hand-placed props can be recorded
rather than guessed at).

Read-only: loads the level and writes a JSON file. It mutates nothing.

Run: UnrealEditor-Cmd <proj> -run=pythonscript -script=<this file> -unattended -nullrhi
Writes Saved/Audit/melusina_house_p0_placed_census.json
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

PROJECT_ROOT = Path(r"C:\EnvironmentPortfolio\BS_GodFile")
MAP = "/Game/Melodia/Levels/Opening/L_MelusinaHouse_P0"
OUT = PROJECT_ROOT / "Saved" / "Audit" / "melusina_house_p0_placed_census.json"


def main() -> int:
    unreal.EditorLevelLibrary.load_level(MAP)
    world = unreal.EditorLevelLibrary.get_editor_world()

    dressing = []
    others = 0
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        try:
            lbl = a.get_actor_label()
        except Exception:
            continue
        cls = a.get_class().get_name()
        mesh_path = None
        try:
            comp = a.static_mesh_component
            if comp is not None and comp.static_mesh is not None:
                mesh_path = comp.static_mesh.get_path_name()
        except Exception:
            pass
        # a Blueprint actor has no static mesh; find its own class path instead
        bp_path = None
        if mesh_path is None:
            try:
                gen = a.get_class()
                if gen is not None and gen.get_path_name():
                    bp_path = gen.get_path_name()
            except Exception:
                pass
        is_dressing = (lbl.startswith("Mag_") or "KB3D_ECI" in lbl
                       or (bp_path and "/MagicianLabatory/BP/" in bp_path))
        if not is_dressing:
            others += 1
            continue
        loc = a.get_actor_location()
        rot = a.get_actor_rotation()
        dressing.append({
            "label": lbl,
            "class": cls,
            "mesh": mesh_path,
            "bp": bp_path,
            "location_cm": [round(loc.x, 1), round(loc.y, 1), round(loc.z, 1)],
            "rot_z": round(rot.yaw, 1),
        })

    report = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "level": MAP,
        "dressing_actor_count": len(dressing),
        "other_actor_count": others,
        "distinct_labels": len({d["label"] for d in dressing}),
        "ecv_actors": sorted([d["label"] for d in dressing if "KB3D_ECI" in d["label"]]),
        "actors": sorted(dressing, key=lambda d: d["label"]),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("CENSUS|dressing=%d|distinct=%d|ecv=%d|others=%d"
          % (report["dressing_actor_count"], report["distinct_labels"],
             len(report["ecv_actors"]), others))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
