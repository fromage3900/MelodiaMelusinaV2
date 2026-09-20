"""Careful ground-snap: relocate only. Hide if no ground. Never lake/PCG/cams/HeroCorner/shaft/chamber."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

PREFIXES = (
    "WC_GreySpire_Helix",
    "WC_GreyRoad_",
    "WC_GreyGrotto_",
    "WC_PhyloWalk_",
)
# Do NOT touch these even if they match somehow
SKIP_EXACT_START = (
    "WC_GreySpire_Shaft",
    "WC_GreySpire_Chamber",
    "WC_GreySpire_PortalCard",
    "WC_GreySpire_Chamber_Crown",
)

def _label(a):
    try: return a.get_actor_label() or ""
    except: return ""

def is_target(lab: str) -> bool:
    if any(lab.startswith(s) for s in SKIP_EXACT_START):
        return False
    return any(lab.startswith(p) for p in PREFIXES)

def ground_at(world, x, y, zhint, ignore_actors):
    hit = unreal.SystemLibrary.line_trace_single(
        world,
        unreal.Vector(x, y, zhint + 8000),
        unreal.Vector(x, y, zhint - 8000),
        unreal.TraceTypeQuery.ECC_VISIBILITY,
        True,
        ignore_actors,
        unreal.DrawDebugTrace.NONE,
        True,
        unreal.LinearColor.RED,
        unreal.LinearColor.GREEN,
        0.0,
    )
    t = hit.to_tuple() if hit else None
    if not t or not t[0]:
        return None
    actor = t[9]
    lab = actor.get_actor_label() if actor else ""
    cls = actor.get_class().get_name() if actor else ""
    # ignore our own dress/grey/phylo on hit
    if lab.startswith(("WC_Grey", "WC_PhyloWalk_", "WC_MA_Dress", "WC_HeroDress", "WC_PortfolioDress")):
        return None
    if "SetDress" in lab or lab.startswith("WC_HeroCornerDress"):
        return None
    if lab == "Morning_SheepDell_Lake" or "Oceanology" in cls:
        return None
    if "Camera" in cls or "PCGVolume" in cls or "PostProcess" in cls:
        return None
    ok = (
        lab.startswith("BrushifyIsland_")
        or lab.startswith("Landscape")
        or "Landscape" in cls
        or lab.startswith("SM_classic_arch_")
        or lab.startswith("WC_EscherWalk_")
    )
    # solid island static meshes that aren't props we spawned
    if not ok and cls == "StaticMeshActor" and lab.startswith("SM_") and "ATL" not in lab and "KB3D" not in lab:
        # classic arches already covered; allow other SM_ environment
        if lab.startswith("SM_classic") or lab.startswith("SM_Brushify"):
            ok = True
    if not ok:
        return None
    nz = float(t[5].z)
    if nz < 0.55:
        return None
    return {"loc": t[4], "actor": lab, "nz": nz}

def mesh_bottom_offset(actor, scale_z=1.0):
    try:
        for c in actor.get_components_by_class(unreal.StaticMeshComponent) or []:
            sm = c.static_mesh
            if not sm:
                continue
            box = sm.get_bounding_box()
            zmin = float(box.min.z)
            sc = actor.get_actor_scale3d()
            return -zmin * abs(sc.z)
    except Exception:
        pass
    return 10.0

def main():
    svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    wname = world.get_name() if world else None
    if wname != "L_MelusinaMorning":
        print("SNAP " + json.dumps({"error": "wrong_world", "world": wname}))
        return 1

    targets = [a for a in svc.get_all_level_actors() if is_target(_label(a))]
    # ignore list = all targets so traces pass through them
    ignore = list(targets)

    snapped = []
    hidden = []
    still = []

    for a in targets:
        lab = _label(a)
        t = a.get_actor_transform()
        x, y, z = float(t.translation.x), float(t.translation.y), float(t.translation.z)
        g = ground_at(world, x, y, z, ignore)
        if not g:
            # try a few XY jitters for helix/road
            for dx, dy in ((50, 0), (-50, 0), (0, 50), (0, -50), (100, 100), (-100, -100)):
                g = ground_at(world, x + dx, y + dy, z, ignore)
                if g:
                    x, y = x + dx, y + dy
                    break
        if not g:
            try:
                a.set_is_temporarily_hidden_in_editor(True)
                a.set_actor_hidden_in_game(True)
            except Exception:
                pass
            hidden.append({"label": lab, "xy": [x, y], "z": z})
            continue

        off = mesh_bottom_offset(a)
        new_z = float(g["loc"].z) + max(5.0, min(off, 80.0))
        # for thin road pads use small offset
        if lab.startswith("WC_GreyRoad_") or "Pad_" in lab:
            new_z = float(g["loc"].z) + 12.0
        if lab.startswith("WC_GreySpire_Helix"):
            new_z = float(g["loc"].z) + 8.0

        old = [x, y, z]
        a.set_actor_location(unreal.Vector(x, y, new_z), False, False)
        try:
            a.set_is_temporarily_hidden_in_editor(False)
            a.set_actor_hidden_in_game(False)
        except Exception:
            pass
        snapped.append({
            "label": lab,
            "from": old,
            "to": [x, y, new_z],
            "ground": g["actor"],
            "dz": new_z - z,
        })

    # second pass: anything still > 400 above its ground?
    for a in targets:
        lab = _label(a)
        if any(h["label"] == lab for h in hidden):
            continue
        t = a.get_actor_transform()
        g = ground_at(world, t.translation.x, t.translation.y, t.translation.z, ignore)
        if not g:
            still.append({"label": lab, "z": float(t.translation.z), "reason": "no_ground_post"})
            continue
        dz = float(t.translation.z) - float(g["loc"].z)
        if abs(dz) > 400:
            still.append({"label": lab, "z": float(t.translation.z), "ground_z": float(g["loc"].z), "dz": dz})

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        saved = True
    except Exception as e:
        saved = str(e)

    report = {
        "schema": "melodia.careful_ground_snap.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "world": wname,
        "targets": len(targets),
        "snapped": len(snapped),
        "hidden": len(hidden),
        "still_floating": len(still),
        "snapped_sample": snapped[:20],
        "hidden_sample": hidden[:30],
        "still_sample": still[:20],
        "snapped_full": snapped,
        "hidden_full": hidden,
        "still_full": still,
        "level_saved": saved,
        "never_touched": ["Morning_SheepDell_Lake", "Shaft/Chamber", "PCG", "cams", "PPV", "HeroCorner"],
    }
    out = Path(unreal.Paths.project_dir()) / "Saved" / "Audit" / "careful_ground_snap_2026-09-20.json"
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print("SNAP " + json.dumps({
        "targets": len(targets),
        "snapped": len(snapped),
        "hidden": len(hidden),
        "still_floating": len(still),
        "hidden_sample": [h["label"] for h in hidden[:12]],
        "still_sample": still[:8],
        "saved": saved,
        "out": str(out),
    }, default=str))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
