"""Hide Belvedere temp clutter; rebuild shaft-hugging Atlantis stair ramp.
Keep: Shaft, Chamber_*, PortalCard, CryptFloor if present, WC_WalkPath_Belvedere_*
"""
from __future__ import annotations
import json, math
from datetime import datetime, timezone
from pathlib import Path
import unreal

EAL = unreal.EditorAssetLibrary
GOLDEN = math.pi * (3 - math.sqrt(5))
RAMP_PREFIX = "WC_SpireRamp_"
HIDE_PREFIXES = (
    "WC_GreySpire_Helix",
    "WC_GreyRoad_",
    "WC_PhyloWalk_",
    "WC_GreyGrotto_",  # except CryptFloor
)
KEEP = {
    "WC_GreySpire_Shaft",
    "WC_GreySpire_Chamber_Floor",
    "WC_GreySpire_Chamber_N",
    "WC_GreySpire_Chamber_S",
    "WC_GreySpire_Chamber_E",
    "WC_GreySpire_Chamber_W",
    "WC_GreySpire_Chamber_Crown",
    "WC_GreySpire_PortalCard",
    "WC_GreyGrotto_CryptFloor",
}
STAIRS = [
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_StairsA",
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_StairsB",
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_StairsC",
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_StairsD",
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_StepsA",
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_StepsB",
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_StepsC",
]
RAILS = [
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_GuardrailA",
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_GuardrailC",
]
TARGET_HALF = 220.0

def lab(a):
    try: return a.get_actor_label() or ""
    except: return ""

def hide(a):
    try:
        a.set_is_temporarily_hidden_in_editor(True)
        a.set_actor_hidden_in_game(True)
        return True
    except Exception:
        return False

def autofit(mesh, desired=0.45):
    try:
        box = mesh.get_bounding_box()
        half = max(abs(box.max.x - box.min.x), abs(box.max.y - box.min.y), abs(box.max.z - box.min.z)) * 0.5
        if half < 1e-3:
            return desired
        return min(desired, TARGET_HALF / half)
    except Exception:
        return desired

def ground_at(world, x, y, zhint):
    hit = unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(x, y, zhint + 8000), unreal.Vector(x, y, zhint - 20000),
        unreal.TraceTypeQuery.ECC_VISIBILITY, True, [],
        unreal.DrawDebugTrace.NONE, True,
        unreal.LinearColor.RED, unreal.LinearColor.GREEN, 0.0)
    t = hit.to_tuple() if hit else None
    if not t or not t[0]:
        return None
    actor = t[9]
    L = actor.get_actor_label() if actor else ""
    C = actor.get_class().get_name() if actor else ""
    if L.startswith(("WC_Grey", "WC_Phylo", "WC_Walk", "WC_SpireRamp")):
        return None
    if L == "Morning_SheepDell_Lake" or "Oceanology" in C:
        return None
    ok = L.startswith(("BrushifyIsland_", "SM_classic_arch_", "WC_EscherWalk_")) or "Landscape" in C
    if not ok or float(t[5].z) < 0.5:
        return None
    return t[4]

def main():
    svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if not world or world.get_name() != "L_MelusinaMorning":
        print("RAMP " + json.dumps({"error": "need_morning"}))
        return 1

    hidden = []
    for a in list(svc.get_all_level_actors()):
        L = lab(a)
        if L in KEEP or L.startswith("WC_GreySpire_Chamber") or L == "WC_GreySpire_Shaft":
            continue
        if L.startswith("WC_WalkPath_Belvedere_"):
            continue  # keep approach path
        if any(L.startswith(p) for p in HIDE_PREFIXES):
            if L == "WC_GreyGrotto_CryptFloor":
                continue
            if hide(a):
                hidden.append(L)

    # destroy prior ramp
    for a in list(svc.get_all_level_actors()):
        if lab(a).startswith(RAMP_PREFIX):
            svc.destroy_actor(a)

    shaft = next((a for a in svc.get_all_level_actors() if lab(a) == "WC_GreySpire_Shaft"), None)
    floor = next((a for a in svc.get_all_level_actors() if lab(a) == "WC_GreySpire_Chamber_Floor"), None)
    if not shaft:
        print("RAMP " + json.dumps({"error": "no_shaft", "hidden": len(hidden)}))
        return 1

    so, se = shaft.get_actor_bounds(False, False)
    cx, cy = float(so.x), float(so.y)
    # shaft half-height ~11m if scale wrong; use chamber floor Z for top
    shaft_loc = shaft.get_actor_location()
    base_g = ground_at(world, cx, cy, 4000)
    base_z = float(base_g.z) if base_g else float(shaft_loc.z) - 1100.0
    if floor:
        top_z = float(floor.get_actor_location().z) - 40.0
    else:
        top_z = base_z + 2200.0

    # radius: outside shaft footprint (400cm) + tread offset
    radius = 280.0
    rise_total = max(400.0, top_z - base_z)
    steps = 36  # clean readable climb ~1.25 turns
    turns = 1.25
    rise = rise_total / (steps - 1)

    stair_meshes = []
    for p in STAIRS:
        if EAL.does_asset_exist(p):
            stair_meshes.append((p, EAL.load_asset(p)))
    rail_meshes = []
    for p in RAILS:
        if EAL.does_asset_exist(p):
            rail_meshes.append((p, EAL.load_asset(p)))
    if not stair_meshes:
        print("RAMP " + json.dumps({"error": "no_atlantis_stairs"}))
        return 1

    placed = []
    for i in range(steps):
        ang = (i / (steps - 1)) * turns * math.tau
        x = cx + radius * math.cos(ang)
        y = cy + radius * math.sin(ang)
        z = base_z + 20.0 + i * rise
        # bottom few steps: prefer ground if available near spiral foot
        if i < 3:
            g = ground_at(world, x, y, z + 500)
            if g:
                z = float(g.z) + 15.0
        path, mesh = stair_meshes[i % len(stair_meshes)]
        sc = autofit(mesh, 0.4)
        yaw = math.degrees(ang) + 90.0
        actor = unreal.EditorLevelLibrary.spawn_actor_from_object(
            mesh, unreal.Vector(x, y, z), unreal.Rotator(0, yaw, 0))
        if not actor:
            continue
        name = f"{RAMP_PREFIX}Stair_{i:02d}"
        actor.set_actor_label(name)
        actor.set_actor_scale3d(unreal.Vector(sc, sc, sc))
        try:
            actor.set_folder_path("Greybox/Belvedere/SpireRamp")
            actor.tags = ["Portfolio", "SpireRamp", "Atlantis", "Belvedere"]
        except Exception:
            pass
        placed.append({"label": name, "z": z, "yaw": yaw, "scale": sc, "mesh": path})

        if i % 3 == 0 and rail_meshes:
            rp, rm = rail_meshes[i % len(rail_meshes)]
            rsc = autofit(rm, 0.35)
            rx = cx + (radius + 70) * math.cos(ang)
            ry = cy + (radius + 70) * math.sin(ang)
            ra = unreal.EditorLevelLibrary.spawn_actor_from_object(
                rm, unreal.Vector(rx, ry, z + 40), unreal.Rotator(0, yaw, 0))
            if ra:
                rname = f"{RAMP_PREFIX}Rail_{i:02d}"
                ra.set_actor_label(rname)
                ra.set_actor_scale3d(unreal.Vector(rsc, rsc, rsc))
                try:
                    ra.set_folder_path("Greybox/Belvedere/SpireRamp")
                except Exception:
                    pass
                placed.append({"label": rname, "z": z + 40, "scale": rsc, "mesh": rp})

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        saved = True
    except Exception as e:
        saved = str(e)

    report = {
        "schema": "melodia.spire_atlantis_ramp.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "hidden_count": len(hidden),
        "hidden_sample": hidden[:20],
        "center": [cx, cy],
        "base_z": base_z,
        "top_z": top_z,
        "radius_cm": radius,
        "steps": steps,
        "turns": turns,
        "placed": len(placed),
        "placed_sample": placed[:10],
        "level_saved": saved,
        "kept": list(KEEP),
        "walk_path_kept": True,
    }
    out = Path(unreal.Paths.project_dir()) / "Saved" / "Audit" / "spire_atlantis_ramp_2026-09-20.json"
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print("RAMP " + json.dumps({
        "hidden": len(hidden),
        "placed": len(placed),
        "base_z": base_z,
        "top_z": top_z,
        "radius": radius,
        "steps": steps,
        "saved": saved,
        "out": str(out),
    }, default=str))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
