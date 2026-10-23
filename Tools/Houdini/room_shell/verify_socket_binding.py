"""Read-only verifier: do the Poitou salon shell's portal sockets agree with the level of truth?

The level (L_MelusinaHouse_P0) is the level of truth and its dressing is hand-placed; this
script NEVER moves or deletes anything. It builds the curved salon shell in pure Python,
reads the dressing plan's salon room record + door placements, and reports, side by side:

  - the shell's two portal sockets (centre, inward, clear width/height, spring, arch rise)
  - the level's door placements (story threshold, front doors, hidden door)
  - the salon's interior/exterior extents from the dressing plan
  - for each cardinal rotation, where the sockets would land in world space and the residual
    to the nearest level door (decision aid, not a transform to apply)

Output: Saved/Audit/SalonConvergence_20261022/socket_binding.json (gitignored, local).
"""
from __future__ import annotations

import json
import math
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SHELL_DIR = ROOT / "Tools" / "Houdini" / "room_shell"
PLAN = ROOT / "specs" / "p0" / "melusina_house_p0_dressing.v1.json"
OUT_DIR = ROOT / "Saved" / "Audit" / "SalonConvergence_20261022"
OUT = OUT_DIR / "socket_binding.json"

sys.path.insert(0, str(SHELL_DIR))
import room_shell_rounded as rsh  # noqa: E402


def shell_sockets():
    _, rep = rsh.build(
        W=15.84, D=12.06, H=7.6, wall_t=0.24, shape="ellipse", sides=32,
        exponent=2.0, segments=96,
        openings=[dict(id="salon_entry", theta=0.25, width=1.8, height=3.2),
                  dict(id="salon_front", theta=0.75, width=2.4, height=3.2)],
    )
    return rep["sockets"], rep["room"], rep["params"]


def level_doors(plan):
    salon = plan["rooms"]["salon"]
    doors = []
    for p in plan["placements"]:
        blob = (p.get("role", "") + " " + p.get("cite", "") + " " + p.get("mesh_name", "")).lower()
        if "door" in blob:
            doors.append(dict(mesh=p["mesh_name"], x=p["x"], y=p["y"], rot_z=p["rot_z"],
                             size=p.get("size"), role=p.get("role"), cite=p.get("cite")))
    return salon, doors


def alignment(sockets, doors, salon):
    sc = [(s["centre_local_m"][0] * 100.0, s["centre_local_m"][1] * 100.0) for s in sockets]
    cx = (salon["interior_x"][0] + salon["interior_x"][1]) / 2.0
    cy = (salon["interior_y"][0] + salon["interior_y"][1]) / 2.0
    dc = [(d["x"], d["y"]) for d in doors]
    rotations = []
    best = None
    for rot in (0, 90, 180, 270):
        rad = math.radians(rot)
        cosr, sinr = math.cos(rad), math.sin(rad)
        world = [(cx + (x * cosr - y * sinr), cy + (x * sinr + y * cosr)) for (x, y) in sc]
        resid = []
        assign = []
        for (wx, wy) in world:
            j = min(range(len(dc)), key=lambda i: (dc[i][0] - wx) ** 2 + (dc[i][1] - wy) ** 2)
            assign.append(j)
            resid.append(math.hypot(dc[j][0] - wx, dc[j][1] - wy))
        entry = dict(rotation_deg=rot,
                     socket_world_cm=[(round(w[0], 1), round(w[1], 1)) for w in world],
                     assignments=[dict(socket=i, door=doors[assign[i]]["mesh"],
                                    residual_cm=round(resid[i], 1)) for i in range(len(sc))],
                     max_residual_cm=round(max(resid) if resid else 0.0, 1))
        rotations.append(entry)
        if best is None or entry["max_residual_cm"] < best["max_residual_cm"]:
            best = entry
    return dict(salon_interior_centre_cm=(round(cx, 1), round(cy, 1)),
                rotations=rotations, best=best)


def main() -> int:
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    sockets, room, params = shell_sockets()
    salon, doors = level_doors(plan)
    align = alignment(sockets, doors, salon)
    report = dict(
        contract="melodia_salon_socket_binding.v1",
        generated=datetime.now().isoformat(timespec="seconds"),
        shell=dict(perimeter_m=params["perimeter_m"], bays=params["bays"],
                   bay_m=params["bay_m_actual"], sockets=sockets),
        level=dict(salon_room=salon, door_placements=doors),
        alignment=align,
        notes=[
            "Shell sockets are in shell-local metres (centre_local_m). Level doors are in "
            "level-world centimetres. The alignment above is a cardinal-rotation diagnostic, "
            "not a transform the dressing pass should apply blindly.",
            "Promotion path: once the curved shell is placed in L_MelusinaHouse_P0, the dressing "
            "pass reads each socket's centre_local_m + inward + clear_width_m and emits anchor "
            "placements relative to the shell actor, tagged pending_shell_swap, so no existing "
            "owner-placed actor is moved or deleted.",
        ],
        ok=align["best"]["max_residual_cm"] < 150.0,
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"contract": report["contract"], "best_rotation": align["best"]["rotation_deg"],
                      "best_max_residual_cm": align["best"]["max_residual_cm"], "ok": report["ok"]}, indent=2))
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
