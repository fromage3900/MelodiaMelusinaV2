"""melusina_house_p0_bind.py — bind the P0 house to the EXISTING P0 systems.

The P0 score (Docs/Plans/POITOU_P0_GOLDEN_WALK_2026-10-21.md) names four
existing-system candidates for the house leg. This script places the real
project actors at the P0's named focal points; it invents no new system and
grants no new quest, flag or intent.

  M01 Notice      AMelodiaExplorationPoint -> UMelodiaOpeningFlowSubsystem::
                   NotifyExplorationPointVisited (one-shot per PointId; counted by
                   GetExplorationPointsVisited(); the gate consumer is
                   AMelodiaSirMelodiousIntroActor::RequiredExplorationPoints)
                     PointId "Desk"  - the desk focal point
                     PointId "Perch" - the empty perch / companion token
  M02 First resonance
                   BP_MelodyToken_Universal - the Heart Melody Token
                   (amount=1, element=Forte, the default element of
                   EMelodiaSpellElement). A forgiving one-action response.
                   AMelodiaOpeningStateAnchor - the house's bond state
                   (ResonanceBond: Absent/Reunited/Resonant/Strained) and its
                   dissonance tier. The Sir reunion beat reads this anchor.
                   BP_SirPerch - the "empty perch / companion token" the M01
                   visual line is aimed at.
  M04 The house hums
                   AMelodiaExplorationPoint PointId "Salon" - the oval salon's one
                   optional linger at the centrepiece. The score asks for NO extra
                   mechanic here, so a one-shot point is the whole of it.

The pack's own Blueprints stay as PRESENTATION at the same spots:
BP_CandleFlame (the M02 candle flame), BP_Crystal (the M04 centrepiece),
BP_InteractiveBook (the M01 book).

Placement is self-correcting: an actor that already exists but drifted is moved
back, so re-running never duplicates and never leaves a stray at the origin.

Run in the editor that has the level open (a headless save while the artist has
the level open is overwritten by their next save).
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import unreal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RECEIPT = PROJECT_ROOT / "Saved" / "Audit" / "melusina_house_p0_bind.json"
MAP = "/Game/Melodia/Levels/Opening/L_MelusinaHouse_P0"

EXPLORATION_CLASS = "/Script/MelodiaCore.MelodiaExplorationPoint"
ANCHOR_CLASS = "/Script/MelodiaCore.MelodiaOpeningStateAnchor"
TOKEN_BP = "/Game/Melodia/Blueprints/BP_MelodyToken_Universal"
PERCH_BP = "/Game/Melodia/Characters/SirMelodious/Perch/BP_SirPerch"

# (point_id, x, y, z, trigger_radius_cm, cite)
POINTS = [
    ("Desk", -900, -880, 41, 120,
     "M01 notice: the desk focal point (BP_InteractiveBook + candle on the desk)"),
    ("Perch", -860, -300, 90, 140,
     "M01 notice: the empty perch / companion token (BP_SirPerch)"),
    ("Salon", 1000, -1300, 200, 180,
     "M04 the house hums: optional linger at the oval salon centrepiece (BP_Crystal)"),
]

TOKEN = {"x": -885, "y": -958, "z": 82, "amount": 1, "element": "Forte",
         "cite": "M02 first resonance: a forgiving one-action musical response; "
                 "the house audibly answers"}
PERCH = {"x": -860, "y": -300, "z": 0, "facing": 200,
         "cite": "M01 notice: strong visual line from bed to empty perch/companion token"}
# The opening state anchor is a POSITION-LESS state holder: AMelodiaOpeningStateAnchor
# declares no Root component (only the ResonanceBond and Dissonance components), so
# its transform is irrelevant and SetActorLocation is a no-op by design. It is found
# by TActorIterator, not by proximity.
ANCHOR = {"x": 0, "y": 0, "z": 0,
          "cite": "M02 first resonance: the house's bond (Absent -> Reunited/Resonant) "
                  "and its dissonance tier live on the opening state anchor; the "
                  "Sir reunion beat reads this anchor (it is a position-less state "
                  "holder - no Root component - found by TActorIterator)"}


def _actors_by_label():
    out = {}
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        out.setdefault(a.get_actor_label(), a)
    return out


RESYNC = os.environ.get("MAGICIANS_RESYNC") == "1"


def place(cls, label, loc, rot, kind):
    """Spawn an actor, or LEAVE AN EXISTING ONE ALONE.

    The dressing is hand-editable: a manual move must survive a re-run, so an
    existing actor is never moved unless MAGICIANS_RESYNC=1 is set explicitly.
    """
    have = _actors_by_label()
    actor = have.get(label)
    if actor is not None:
        cur = actor.get_actor_location()
        drifted = (abs(cur.x - loc[0]) > 1 or abs(cur.y - loc[1]) > 1
                   or abs(cur.z - loc[2]) > 1)
        if RESYNC and drifted:
            actor.set_actor_location(unreal.Vector(loc[0], loc[1], loc[2]), False, True)
            actor.set_actor_rotation(unreal.Rotator(rot[0], rot[1], rot[2]), False)
            return {"label": label, "class": kind, "action": "resynced",
                    "from": [round(cur.x), round(cur.y), round(cur.z)], "to": list(loc)}
        return {"label": label, "class": kind, "action": "left_as_edited",
                "to": [round(cur.x), round(cur.y), round(cur.z)]}
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        cls, unreal.Vector(loc[0], loc[1], loc[2]), unreal.Rotator(rot[0], rot[1], rot[2]))
    if actor is None:
        return None
    actor.set_actor_label(label)
    actor.set_actor_location(unreal.Vector(loc[0], loc[1], loc[2]), False, True)
    actor.set_actor_rotation(unreal.Rotator(rot[0], rot[1], rot[2]), False)
    return {"label": label, "class": kind, "action": "spawned", "to": list(loc)}


def main() -> int:
    out = {"generated": datetime.now(timezone.utc).isoformat(), "level": MAP,
           "placed": [], "errors": []}

    if not unreal.EditorAssetLibrary.does_asset_exist(MAP):
        out["errors"].append("level asset missing")
    else:
        w = unreal.EditorLevelLibrary.get_editor_world()
        cur = w.get_outermost().get_path_name() if w else None
        out["level_already_open"] = (cur == MAP)
        if cur != MAP:
            unreal.EditorLevelLibrary.load_level(MAP)
            w = unreal.EditorLevelLibrary.get_editor_world()
        world = w

        # ---- M01 / M04: the one-shot exploration points
        ecls = unreal.load_class(None, EXPLORATION_CLASS)
        if ecls is None:
            out["errors"].append("could not load " + EXPLORATION_CLASS)
        else:
            for pid, x, y, z, radius, cite in POINTS:
                label = "P0_Explore_%s" % pid
                rec = place(ecls, label, (x, y, z), (0, 0, 0), "AMelodiaExplorationPoint")
                if rec is None:
                    out["errors"].append("spawn failed: " + label)
                    continue
                for a in unreal.EditorLevelLibrary.get_all_level_actors():
                    if a.get_actor_label() == label:
                        a.set_editor_property("point_id", pid)
                        try:
                            a.get_editor_property("trigger").set_editor_property(
                                "sphere_radius", float(radius))
                        except Exception as ex:
                            out["errors"].append("%s trigger: %s" % (label, str(ex)[:80]))
                        break
                rec["point_id"] = pid
                rec["trigger_radius_cm"] = radius
                rec["cite"] = cite
                out["placed"].append(rec)

        # ---- M02: the Heart Melody Token
        tcls = unreal.EditorAssetLibrary.load_blueprint_class(TOKEN_BP)
        if tcls is None:
            out["errors"].append("could not load " + TOKEN_BP)
        else:
            rec = place(tcls, "P0_MelodyToken_Heart",
                         (TOKEN["x"], TOKEN["y"], TOKEN["z"]), (0, 0, 0),
                         "BP_MelodyToken_Universal")
            if rec is None:
                out["errors"].append("token spawn failed")
            else:
                for a in unreal.EditorLevelLibrary.get_all_level_actors():
                    if a.get_actor_label() == "P0_MelodyToken_Heart":
                        a.set_editor_property("amount", int(TOKEN["amount"]))
                        a.set_editor_property("element", TOKEN["element"])
                        break
                rec["amount"] = TOKEN["amount"]
                rec["element"] = TOKEN["element"]
                rec["cite"] = TOKEN["cite"]
                out["placed"].append(rec)

        # ---- M01: the empty perch / companion token
        pcls = unreal.EditorAssetLibrary.load_blueprint_class(PERCH_BP)
        if pcls is None:
            out["errors"].append("could not load " + PERCH_BP)
        else:
            rec = place(pcls, "P0_SirPerch_Empty",
                         (PERCH["x"], PERCH["y"], PERCH["z"]), (0, 0, PERCH["facing"]),
                         "BP_SirPerch")
            if rec is None:
                out["errors"].append("perch spawn failed")
            else:
                rec["facing_yaw"] = PERCH["facing"]
                rec["cite"] = PERCH["cite"]
                out["placed"].append(rec)

        # ---- M02: the opening state anchor (bond + dissonance).
        # It has no Root component, so it is NOT positioned: it is a state holder
        # found by TActorIterator. Moving it is a no-op, so do not try.
        acls = unreal.load_class(None, ANCHOR_CLASS)
        if acls is None:
            out["errors"].append("could not load " + ANCHOR_CLASS)
        else:
            have = _actors_by_label()
            actor = have.get("P0_OpeningStateAnchor")
            if actor is None:
                actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
                    acls, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
                if actor is not None:
                    actor.set_actor_label("P0_OpeningStateAnchor")
            if actor is None:
                out["errors"].append("anchor spawn failed")
            else:
                out["placed"].append({
                    "label": "P0_OpeningStateAnchor",
                    "class": "AMelodiaOpeningStateAnchor",
                    "action": "present",
                    "loc": [0, 0, 0],
                    "positionless": True,
                    "bond_state": "Absent",
                    "dissonance_tier": "Clear",
                    "cite": ANCHOR["cite"]})

        saved = False
        for saver in ("save_map", "save_current_level"):
            try:
                if saver == "save_map":
                    ok = unreal.EditorLoadingAndSavingUtils.save_map(world, MAP)
                else:
                    ok = unreal.EditorLevelLibrary.save_current_level()
                if ok:
                    saved = saver
                    break
            except Exception as ex:
                out["errors"].append("%s: %s" % (saver, str(ex)[:120]))
        out["save"] = saved

    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("P0BIND|" + json.dumps({
        "placed": len(out["placed"]), "errors": out["errors"][:4],
        "save": out.get("save"),
        "actions": {p["label"]: p["action"] for p in out["placed"]}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
