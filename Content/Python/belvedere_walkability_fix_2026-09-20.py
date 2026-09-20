"""Belvedere walkability fix: hide floaters, build one real ground path.
Never touch lake / PCG / cams / PPV / shaft / chamber / PortalCard.
"""
from __future__ import annotations
import json, math
from datetime import datetime, timezone
from pathlib import Path
import unreal

EAL = unreal.EditorAssetLibrary
GREY = "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Cube_1m"
ATL_FLOOR = [
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_FloorA",
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_FloorB",
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_FloorC",
]
KEEP = (
    "WC_GreySpire_Shaft",
    "WC_GreySpire_Chamber_Floor",
    "WC_GreySpire_Chamber_N",
    "WC_GreySpire_Chamber_S",
    "WC_GreySpire_Chamber_E",
    "WC_GreySpire_Chamber_W",
    "WC_GreySpire_Chamber_Crown",
    "WC_GreySpire_PortalCard",
)
PATH_PREFIX = "WC_WalkPath_Belvedere_"
OWN_PATH = (PATH_PREFIX,)

def lab(a):
    try: return a.get_actor_label() or ""
    except: return ""

def ground_at(world, x, y, zhint, ignore=None):
    ignore = ignore or []
    hit = unreal.SystemLibrary.line_trace_single(
        world,
        unreal.Vector(x, y, zhint + 10000),
        unreal.Vector(x, y, zhint - 20000),
        unreal.TraceTypeQuery.ECC_VISIBILITY,
        True,
        ignore,
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
    L = actor.get_actor_label() if actor else ""
    C = actor.get_class().get_name() if actor else ""
    if L.startswith(("WC_Grey", "WC_PhyloWalk_", "WC_WalkPath_", "WC_MA_Dress", "WC_HeroDress")):
        return None
    if L == "Morning_SheepDell_Lake" or "Oceanology" in C:
        return None
    if "Camera" in C or "PCGVolume" in C or "PostProcess" in C:
        return None
    ok = (
        L.startswith("BrushifyIsland_")
        or L.startswith("Landscape")
        or "Landscape" in C
        or L.startswith("SM_classic_arch_")
        or L.startswith("WC_EscherWalk_")
    )
    if not ok:
        return None
    if float(t[5].z) < 0.55:
        return None
    return {"loc": t[4], "actor": L, "nz": float(t[5].z)}

def height_above_ground(world, a, ignore):
    t = a.get_actor_location()
    g = ground_at(world, t.x, t.y, t.z, ignore)
    if not g:
        return None, None
    return float(t.z) - float(g["loc"].z), g

def hide_actor(a):
    try:
        a.set_is_temporarily_hidden_in_editor(True)
        a.set_actor_hidden_in_game(True)
        return True
    except Exception:
        return False

def count_floaters(world, svc, ignore):
    n = 0
    samples = []
    for a in svc.get_all_level_actors():
        L = lab(a)
        if not L.startswith(("WC_Grey", "WC_PhyloWalk_", "WC_WalkPath_")):
            continue
        if L in KEEP or L.startswith("WC_GreySpire_Chamber") or L == "WC_GreySpire_Shaft":
            continue
        try:
            if a.is_temporarily_hidden_in_editor():
                continue
        except Exception:
            pass
        dz, g = height_above_ground(world, a, ignore)
        if g is None or (dz is not None and dz > 80):
            n += 1
            if len(samples) < 12:
                samples.append({"label": L, "dz": dz})
    return n, samples

def main():
    svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if not world or world.get_name() != "L_MelusinaMorning":
        print("WALKFIX " + json.dumps({"error": "need_morning", "world": world.get_name() if world else None}))
        return 1

    all_actors = list(svc.get_all_level_actors())
    ignore_seed = [a for a in all_actors if lab(a).startswith(("WC_Grey", "WC_PhyloWalk_", "WC_WalkPath_"))]

    before_n, before_s = count_floaters(world, svc, ignore_seed)

    hidden = []
    kept = []
    # 1) Hide ALL helix
    for a in list(svc.get_all_level_actors()):
        L = lab(a)
        if L.startswith("WC_GreySpire_Helix"):
            if hide_actor(a):
                hidden.append({"label": L, "reason": "helix_air_climb"})

    # 2) Hide floating roads / phylo / grotto (except crypt floor if grounded)
    for a in list(svc.get_all_level_actors()):
        L = lab(a)
        if L in KEEP or L.startswith("WC_GreySpire_Chamber") or L == "WC_GreySpire_Shaft":
            kept.append(L)
            continue
        if not (L.startswith("WC_GreyRoad_") or L.startswith("WC_PhyloWalk_") or L.startswith("WC_GreyGrotto_")):
            continue
        # crypt floor: keep if grounded
        if L == "WC_GreyGrotto_CryptFloor":
            dz, g = height_above_ground(world, a, ignore_seed)
            if g is not None and dz is not None and abs(dz) <= 120:
                kept.append(L)
                continue
        dz, g = height_above_ground(world, a, ignore_seed)
        if g is None or (dz is not None and dz > 80):
            if hide_actor(a):
                hidden.append({"label": L, "reason": "floater", "dz": dz})
        else:
            # also hide non-corridor phylo/roads for clarity — user wants ONE path
            if L.startswith("WC_PhyloWalk_") or L.startswith("WC_GreyRoad_"):
                if hide_actor(a):
                    hidden.append({"label": L, "reason": "clear_for_single_path", "dz": dz})
            elif L.startswith("WC_GreyGrotto_") and L != "WC_GreyGrotto_CryptFloor":
                # keep grounded grotto accents only if low
                if dz is not None and dz > 40:
                    if hide_actor(a):
                        hidden.append({"label": L, "reason": "grotto_high", "dz": dz})

    # Clear prior walk path labels
    for a in list(svc.get_all_level_actors()):
        L = lab(a)
        if L.startswith(PATH_PREFIX):
            svc.destroy_actor(a)

    # Find spire base and start
    shaft = next((a for a in svc.get_all_level_actors() if lab(a) == "WC_GreySpire_Shaft"), None)
    if shaft:
        o, e = shaft.get_actor_bounds(False, False)
        sx, sy = float(o.x), float(o.y)
    else:
        sx, sy = 160.0, 1600.0
    g_end = ground_at(world, sx, sy, 4000)
    if not g_end:
        for r in (100, 200, 400):
            for ang in range(0, 360, 30):
                g_end = ground_at(world, sx + r * math.cos(math.radians(ang)), sy + r * math.sin(math.radians(ang)), 4000)
                if g_end:
                    sx, sy = float(g_end["loc"].x), float(g_end["loc"].y)
                    break
            if g_end:
                break
    if not g_end:
        print("WALKFIX " + json.dumps({"error": "no_spire_ground", "hidden": len(hidden)}))
        return 1
    end = (float(g_end["loc"].x), float(g_end["loc"].y), float(g_end["loc"].z))

    start_actor = next((a for a in svc.get_all_level_actors() if lab(a) == "WC_EscherWalk_spur_westbank_00"), None)
    if start_actor:
        st = start_actor.get_actor_location()
        start_xy = (float(st.x), float(st.y), float(st.z))
    else:
        start_xy = (-1335.0, 1505.0, 1200.0)
    g_start = ground_at(world, start_xy[0], start_xy[1], start_xy[2] + 2000)
    if not g_start:
        # EastBank fallback
        g_start = ground_at(world, -1450.0, 1520.0, 2000)
        if g_start:
            start_xy = (float(g_start["loc"].x), float(g_start["loc"].y), float(g_start["loc"].z))
    else:
        start_xy = (float(g_start["loc"].x), float(g_start["loc"].y), float(g_start["loc"].z))

    # Mid control toward approach
    mid = ((start_xy[0] + end[0]) * 0.5, (start_xy[1] + end[1]) * 0.5)
    g_mid = ground_at(world, mid[0], mid[1], 2000)
    controls = [start_xy[:2], (mid[0], mid[1]) if g_mid else ((start_xy[0] + end[0]) * 0.5, (start_xy[1] + end[1]) * 0.45), end[:2]]

    # Load meshes
    floors = []
    for p in ATL_FLOOR:
        if EAL.does_asset_exist(p):
            floors.append(EAL.load_asset(p))
    grey = EAL.load_asset(GREY) if EAL.does_asset_exist(GREY) else None
    if not floors and not grey:
        print("WALKFIX " + json.dumps({"error": "no_meshes"}))
        return 1

    # Dense sample polyline ≤150cm
    spacing = 140.0
    samples = []
    for i in range(len(controls) - 1):
        x0, y0 = controls[i]
        x1, y1 = controls[i + 1]
        seg = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(seg / spacing))
        for k in range(n):
            t = k / n
            samples.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
    samples.append(controls[-1])

    placed = []
    failed = []
    path_ignore = list(ignore_seed)
    for i, (x, y) in enumerate(samples):
        g = ground_at(world, x, y, 3000, path_ignore)
        if not g:
            for dx, dy in ((40, 0), (-40, 0), (0, 40), (0, -40), (80, 80), (-80, -80), (120, 0), (0, 120)):
                g = ground_at(world, x + dx, y + dy, 3000, path_ignore)
                if g:
                    x, y = x + dx, y + dy
                    break
        if not g:
            failed.append({"i": i, "xy": [x, y]})
            continue
        loc = g["loc"]
        mesh = floors[i % len(floors)] if floors else grey
        # autofit atl floors roughly
        sc = 0.55 if floors else 2.0
        if floors:
            try:
                box = mesh.get_bounding_box()
                half = max(abs(box.max.x - box.min.x), abs(box.max.y - box.min.y)) * 0.5
                if half > 1:
                    sc = min(0.7, 140.0 / half)
            except Exception:
                sc = 0.5
        else:
            sc = 2.0  # 2m grey pad
        yaw = 0.0
        if i + 1 < len(samples):
            yaw = math.degrees(math.atan2(samples[i + 1][1] - y, samples[i + 1][0] - x))
        actor = unreal.EditorLevelLibrary.spawn_actor_from_object(
            mesh, unreal.Vector(loc.x, loc.y, loc.z + 10), unreal.Rotator(0, yaw, 0))
        if not actor:
            failed.append({"i": i, "xy": [x, y], "reason": "spawn"})
            continue
        name = f"{PATH_PREFIX}{i:03d}"
        actor.set_actor_label(name)
        actor.set_actor_scale3d(unreal.Vector(sc, sc, 0.35 if floors else 0.2))
        try:
            actor.set_folder_path("Greybox/Belvedere/WalkPath")
            actor.tags = ["Portfolio", "WalkPath", "Belvedere"]
        except Exception:
            pass
        placed.append({"label": name, "ground": g["actor"], "loc": [loc.x, loc.y, loc.z + 10], "scale": sc})
        path_ignore.append(actor)

    # path length
    length = 0.0
    for i in range(len(placed) - 1):
        a, b = placed[i]["loc"], placed[i + 1]["loc"]
        length += math.hypot(b[0] - a[0], b[1] - a[1])

    after_ignore = [a for a in svc.get_all_level_actors() if lab(a).startswith(("WC_Grey", "WC_PhyloWalk_", "WC_WalkPath_"))]
    after_n, after_s = count_floaters(world, svc, after_ignore)

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        saved = True
    except Exception as e:
        saved = str(e)

    report = {
        "schema": "melodia.belvedere_walkability_fix.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "before_floaters_visible": before_n,
        "before_sample": before_s,
        "hidden_count": len(hidden),
        "hidden_sample": hidden[:25],
        "kept": sorted(set(kept)),
        "path_placed": len(placed),
        "path_failed": len(failed),
        "path_length_xy_cm": round(length, 1),
        "path_start": start_xy,
        "path_end": end,
        "path_ground_sample": [p["ground"] for p in placed[:8]],
        "after_floaters_visible": after_n,
        "after_sample": after_s,
        "level_saved": saved,
        "placed": placed,
        "failed_sample": failed[:20],
    }
    out = Path(unreal.Paths.project_dir()) / "Saved" / "Audit" / "belvedere_walkability_fix_2026-09-20.json"
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print("WALKFIX " + json.dumps({
        "before_floaters": before_n,
        "hidden": len(hidden),
        "path_pads": len(placed),
        "path_len_cm": round(length, 1),
        "failed": len(failed),
        "after_floaters": after_n,
        "grounds": report["path_ground_sample"],
        "saved": saved,
        "out": str(out),
    }, default=str))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
