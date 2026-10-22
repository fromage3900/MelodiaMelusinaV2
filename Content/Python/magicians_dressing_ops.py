"""magicians_dressing_ops.py — the editing toolkit for the P0 house dressing.

The dressing is 94 actors in L_MelusinaHouse_P0 (76 Magician's Library props +
8 pack Blueprints + 10 P0 actors). They are ordinary level actors, so you can
move, rotate, scale, re-mesh or delete them in the editor and the state is
saved with the map.

This tool exists so the automation never fights your hands:

  * the dressing/bind scripts are CREATE-ONLY. They never move or delete an
    actor that already exists, so a manual tweak is never reverted.
  * resyncing to the written manifest is an EXPLICIT command, never automatic.
  * every dressing and P0 actor carries TAGS, so you can find and
    multi-select them in the World Outliner (search for the tag) and bulk-edit.

Commands (env var MAGICIANS_OPS, optional MAGICIANS_OPS_ARG):

  list                 print the full dressing inventory (label, room, prop,
                       class, location, mesh, tags)
  tag                  (re)apply the tags to every dressing and P0 actor
  select [room]        select the dressing actors (optionally of one room) so
                       they can be moved as a group in the editor
  remove [room]        delete the dressing actors of one room (destructive)
  resync [room]        re-apply the manifest's positions to the dressing actors
                       (destructive to manual position edits - that is the point)
  stats                one-line summary of what is in the house

Run in the editor that has the level open.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import unreal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RECEIPT = PROJECT_ROOT / "Saved" / "Audit" / "magicians_dressing_ops.json"
MAP = "/Game/Melodia/Levels/Opening/L_MelusinaHouse_P0"
SPEC = PROJECT_ROOT / "specs" / "p0" / "melusina_house_p0_dressing.v1.json"

TAG_DRESSING = "MagDressing"
TAG_P0 = "MagP0"


def _all_actors():
    return list(unreal.EditorLevelLibrary.get_all_level_actors())


def _label(a):
    try:
        return a.get_actor_label()
    except Exception:
        return a.get_name()


def _is_dressing(a):
    l = _label(a)
    return l.startswith("Mag_") or l.startswith("MagBP_")


def _is_p0(a):
    return _label(a).startswith("P0_")


def _tags(a):
    try:
        return [str(t) for t in (a.get_editor_property("tags") or [])]
    except Exception:
        return []


def _set_tags(a, tags):
    try:
        a.set_editor_property("tags", tags)
        return True
    except Exception:
        return False


def _spec_rooms():
    try:
        return json.load(open(SPEC, encoding="utf-8")).get("rooms", {})
    except Exception:
        return {}


def _room_at(x, y):
    """Room whose interior footprint contains the point."""
    for name, r in _spec_rooms().items():
        ix, iy = r.get("interior_x", [0, 0]), r.get("interior_y", [0, 0])
        if ix[0] - 60 <= x <= ix[1] + 60 and iy[0] - 60 <= y <= iy[1] + 60:
            return name
    return ""


# the P0 actors sit at named focal points; the anchor is position-less
P0_ROOM = {
    "P0_Explore_Desk": "bedroom",
    "P0_Explore_Perch": "bedroom",
    "P0_MelodyToken_Heart": "bedroom",
    "P0_SirPerch_Empty": "bedroom",
    "P0_Explore_Salon": "salon",
    "P0_OpeningStateAnchor": "",
}


def _room_of(label, actor=None):
    for part in label.split("_"):
        if part in ("bedroom", "landing", "salon"):
            return part
    if label in P0_ROOM:
        return P0_ROOM[label]
    if actor is not None:
        loc = actor.get_actor_location()
        r = _room_at(loc.x, loc.y)
        if r:
            return r
    return ""


def _prop_of(label):
    if label.startswith("MagBP_"):
        return label[6:]
    if label.startswith("Mag_"):
        return label.split("_", 2)[-1]
    return label[3:] if label.startswith("P0_") else label


def _mesh_of(a):
    try:
        c = a.get_component_by_class(unreal.StaticMeshComponent)
        if c and c.static_mesh:
            return c.static_mesh.get_path_name().rsplit(".", 1)[0]
    except Exception:
        pass
    return None


def _loc(a):
    l = a.get_actor_location()
    return [round(l.x), round(l.y), round(l.z)]


def _load_spec():
    try:
        return json.load(open(SPEC, encoding="utf-8"))
    except Exception:
        return {"placements": []}


def _spec_index():
    """label -> (x, y, z) from the written manifest."""
    idx = {}
    for p in _load_spec().get("placements", []):
        if p.get("tree") == "bp":
            idx["MagBP_%s" % p["bp_name"]] = (p["x"], p["y"], p.get("z", 0))
        else:
            idx["Mag_%s_%s" % (p["room"], p["mesh_name"])] = (p["x"], p["y"], p.get("actor_z", 0))
    return idx


def main() -> int:
    cmd = (os.environ.get("MAGICIANS_OPS") or "list").strip().lower()
    arg = (os.environ.get("MAGICIANS_OPS_ARG") or "").strip()
    out = {"generated": datetime.now(timezone.utc).isoformat(), "command": cmd, "arg": arg,
           "level": MAP, "rows": [], "actions": []}

    w = unreal.EditorLevelLibrary.get_editor_world()
    cur = w.get_outermost().get_path_name() if w else None
    if cur != MAP:
        unreal.EditorLevelLibrary.load_level(MAP)
        w = unreal.EditorLevelLibrary.get_editor_world()
    actors = _all_actors()

    dressing = [a for a in actors if _is_dressing(a)]
    p0 = [a for a in actors if _is_p0(a)]

    if cmd == "list":
        for a in sorted(dressing + p0, key=_label):
            l = _label(a)
            out["rows"].append({"label": l, "class": a.get_class().get_name(),
                                "room": _room_of(l, a), "prop": _prop_of(l),
                                "loc": _loc(a), "mesh": _mesh_of(a), "tags": _tags(a)})
    elif cmd == "stats":
        out["actions"].append("dressing=%d p0=%d total_actors=%d" % (len(dressing), len(p0), len(actors)))
    elif cmd == "tag":
        n = 0
        for a in dressing + p0:
            l = _label(a)
            room = _room_of(l, a)
            tags = [TAG_P0 if l.startswith("P0_") else TAG_DRESSING,
                    ("Room_" + room) if room else "Room_Unknown",
                    "Prop_" + _prop_of(l)]
            if _set_tags(a, tags):
                n += 1
        out["actions"].append("tagged %d actors" % n)
    elif cmd == "select":
        target = [a for a in dressing if not arg or _room_of(_label(a), a) == arg]
        for a in target:
            a.select_actor(True) if hasattr(a, "select_actor") else None
        try:
            unreal.EditorLevelLibrary.editor_set_game_view(
                unreal.EditorLevelLibrary.get_editor_world())
        except Exception:
            pass
        out["actions"].append("selected %d dressing actors" % len(target))
    elif cmd == "remove":
        target = [a for a in dressing if not arg or _room_of(_label(a), a) == arg]
        for a in target:
            a.destroy()
        out["actions"].append("removed %d dressing actors (room=%s)" % (len(target), arg or "all"))
    elif cmd == "resync":
        idx = _spec_index()
        n = 0
        for a in dressing:
            l = _label(a)
            if l not in idx:
                continue
            x, y, z = idx[l]
            a.set_actor_location(unreal.Vector(x, y, z), False, True)
            n += 1
        out["actions"].append("resynced %d dressing actors to the manifest" % n)
    else:
        out["actions"].append("unknown command: " + cmd)

    try:
        ok = unreal.EditorLoadingAndSavingUtils.save_map(w, MAP)
        out["save"] = bool(ok)
    except Exception as ex:
        out["save"] = "ERR " + str(ex)[:160]

    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("DOP|" + json.dumps({"cmd": cmd, "arg": arg, "actions": out["actions"],
                               "rows": len(out["rows"]), "save": out.get("save")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
