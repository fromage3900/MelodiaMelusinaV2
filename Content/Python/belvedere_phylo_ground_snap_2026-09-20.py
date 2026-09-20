# -*- coding: utf-8 -*-
"""Ground-snap floaters for Belvedere + PhyloWalk. RELOCATE only; destroy only if no solid.
Labels: WC_GreySpire_Helix*, WC_GreyRoad_*, WC_GreyGrotto_* (optional), WC_PhyloWalk_*.
NEVER touch lake/ocean/PCG/cams/PPV/HeroCorner/shaft/chamber (chamber stays on arch).
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

OUT = Path(unreal.Paths.project_saved_dir()) / "Audit" / "belvedere_phylo_ground_snap_2026-09-20.json"

IGNORE_PREFIXES = (
    "WC_GreySpire_", "WC_GreyGrotto_", "WC_GreyRoad_", "WC_PhyloWalk_",
    "WC_MA_Dress_", "WC_HeroDress_", "WC_PortfolioDress_",
)
GOOD_TOKENS = ("BrushifyIsland_", "Landscape", "SM_classic_arch", "Island", "Terrain", "arch")


def _label(a):
    try:
        return a.get_actor_label() or ""
    except Exception:
        return ""


def _should_snap(lab: str) -> bool:
    if lab.startswith("WC_GreySpire_Helix"):
        return True
    if lab.startswith("WC_GreyRoad_"):
        return True
    if lab.startswith("WC_PhyloWalk_"):
        return True
    if lab.startswith("WC_GreyGrotto_"):
        # snap crypt/side pieces; keep portal twin careful
        return True
    return False


def _is_ignore(lab: str) -> bool:
    return any(lab.startswith(p) for p in IGNORE_PREFIXES)


def _is_good(lab: str) -> bool:
    if not lab or _is_ignore(lab):
        return False
    return any(t in lab for t in GOOD_TOKENS) or lab.startswith("Brushify")


def _collect_ignore(svc):
    return [a for a in svc.get_all_level_actors() if _is_ignore(_label(a))]


def _ground(world, x, y, z_hint, ignore):
    start = unreal.Vector(x, y, z_hint + 6000.0)
    end = unreal.Vector(x, y, z_hint - 10000.0)
    hit = unreal.SystemLibrary.line_trace_single(
        world, start, end,
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, ignore,
        unreal.DrawDebugTrace.NONE, True,
        unreal.LinearColor.RED, unreal.LinearColor.GREEN, 0.0,
    )
    try:
        t = hit.to_tuple()
    except Exception:
        return None
    if not t or not t[0]:
        return None
    actor = t[9]
    lab = _label(actor) if actor else ""
    if not _is_good(lab):
        return None
    if float(t[5].z) < 0.55:
        return None
    return t[4], lab, float(t[5].z)


def _extent_z(actor):
    try:
        _, ext = actor.get_actor_bounds(False, True)
        return abs(float(ext.z))
    except Exception:
        return 20.0


def main():
    svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    ignore = _collect_ignore(svc)
    report = {
        "schema": "melodia.belvedere_phylo_ground_snap.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "snapped": [],
        "hidden": [],
        "still_floating": [],
        "skipped": [],
    }
    FLOAT_THRESH = 80.0  # cm above ground before considered floating after snap check

    for a in list(svc.get_all_level_actors()):
        lab = _label(a)
        if not _should_snap(lab):
            continue
        loc = a.get_actor_location()
        g = _ground(world, loc.x, loc.y, loc.z, ignore)
        if not g:
            # hide rather than delete first
            try:
                a.set_actor_hidden_in_game(True)
                a.set_is_temporarily_hidden_in_editor(True)
                report["hidden"].append({"label": lab, "reason": "no_ground", "loc": [loc.x, loc.y, loc.z]})
            except Exception:
                report["still_floating"].append({"label": lab, "reason": "no_ground_hide_failed"})
            continue
        gLOC, gLab, nz = g
        hz = _extent_z(a)
        new_z = float(gLOC.z) + max(5.0, hz * 0.15)
        dz = abs(float(loc.z) - new_z)
        if dz < 15.0:
            report["skipped"].append({"label": lab, "reason": "already_grounded", "dz": dz, "ground": gLab})
            continue
        try:
            a.set_actor_location(unreal.Vector(loc.x, loc.y, new_z), False, False)
            report["snapped"].append({
                "label": lab,
                "from_z": float(loc.z),
                "to_z": new_z,
                "dz": dz,
                "ground": gLab,
                "normal_z": nz,
            })
        except Exception as e:
            report["still_floating"].append({"label": lab, "error": str(e)})

    # second pass: anything still > FLOAT_THRESH above good ground
    for a in svc.get_all_level_actors():
        lab = _label(a)
        if not _should_snap(lab):
            continue
        if any(x["label"] == lab for x in report["hidden"]):
            continue
        loc = a.get_actor_location()
        g = _ground(world, loc.x, loc.y, loc.z, ignore)
        if not g:
            continue
        gLOC, gLab, _ = g
        if float(loc.z) - float(gLOC.z) > FLOAT_THRESH + _extent_z(a):
            report["still_floating"].append({
                "label": lab,
                "z": float(loc.z),
                "ground_z": float(gLOC.z),
                "ground": gLab,
            })

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        report["level_saved"] = True
    except Exception as e:
        report["level_saved"] = str(e)

    report["counts"] = {
        "snapped": len(report["snapped"]),
        "hidden": len(report["hidden"]),
        "still_floating": len(report["still_floating"]),
        "skipped_ok": len(report["skipped"]),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print("GROUND_SNAP " + json.dumps(report["counts"]))
    unreal.log("GROUND_SNAP " + json.dumps(report["counts"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
