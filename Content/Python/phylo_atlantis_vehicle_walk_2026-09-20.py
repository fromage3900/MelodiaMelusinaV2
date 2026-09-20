"""Phyllotaxis Belvedere walkway: Atlantis kitbash + Enchanted Vehicle accents.
Labels: WC_PhyloWalk_* only (destroy-only those). Grey spire massing kept.
Never lake / HeroCorner PCG / cams / PPV.
"""
from __future__ import annotations
import json, math
from datetime import datetime, timezone
from pathlib import Path
import unreal

EAL = unreal.EditorAssetLibrary
GOLDEN = math.pi * (3 - math.sqrt(5))  # ~2.39996 rad
OWN = ("WC_PhyloWalk_",)
TARGET_HALF = 280.0  # cm autofit

ATL = {
    "floor": [
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_FloorA",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_FloorB",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_FloorC",
    ],
    "stairs": [
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_StairsA",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_StairsC",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_StepsA",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_StepsB",
    ],
    "arch": [
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ArchA",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ArchC",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ArchE",
    ],
    "rail": [
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_GuardrailA",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_GuardrailC",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_GuardrailF",
    ],
    "column": [
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ColumnsA",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_BaseColumnsA",
    ],
}

# Enchanted vehicle accents — try common mount points
VEH_CANDIDATES = [
    "/Game/KitBash_EnchantedVehicles/SM_KB3D_ECV_VehicApothecary_A_Ladder",
    "/Game/KitBash_EnchantedVehicles/Meshes/SM_KB3D_ECV_VehicApothecary_A_Ladder",
    "/Game/Melodia/Imported/EnchantedVehicles/SM_KB3D_ECV_VehicApothecary_A_Ladder",
]

def _label(a):
    try: return a.get_actor_label() or ""
    except: return ""

def resolve_veh_paths():
    found = {"ladder": None, "chest": None, "barrel": None, "rug": None, "lantern": None}
    roots = [
        "/Game/KitBash_EnchantedVehicles",
        "/Game/KitBash EnchantedVehicles",
        "/Game/Melodia/Imported/EnchantedVehicles",
    ]
    needles = {
        "ladder": "Ladder",
        "chest": "Chest",
        "barrel": "Barrel",
        "rug": "RugA",
        "lantern": "LanternA",
    }
    for root in roots:
        try:
            if not EAL.does_directory_exist(root):
                continue
            for p in EAL.list_assets(root, True, False) or []:
                name = p.rsplit("/", 1)[-1]
                if not name.startswith("SM_"):
                    continue
                for key, token in needles.items():
                    if found[key]:
                        continue
                    if token in name:
                        found[key] = p.split(".")[0] if "." in p else p
        except Exception:
            pass
    return found

def mesh_half(mesh):
    try:
        box = mesh.get_bounding_box()
        hx = abs(box.max.x - box.min.x) * 0.5
        hy = abs(box.max.y - box.min.y) * 0.5
        hz = abs(box.max.z - box.min.z) * 0.5
        return max(hx, hy, hz), max(hx, hy, hz, 1e-3)
    except Exception:
        return 50.0, 50.0

def autofit_scale(mesh, desired=1.0):
    half, _ = mesh_half(mesh)
    if half < 1e-3:
        return desired
    max_s = TARGET_HALF / half
    if max_s < 0.002:
        return None
    return min(desired, max_s)

def ground_at(world, x, y, zhint):
    hit = unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(x, y, zhint + 12000), unreal.Vector(x, y, zhint - 30000),
        unreal.TraceTypeQuery.ECC_VISIBILITY, True, [],
        unreal.DrawDebugTrace.NONE, True,
        unreal.LinearColor.RED, unreal.LinearColor.GREEN, 0.0)
    t = hit.to_tuple() if hit else None
    if not t or not t[0]:
        return None
    actor = t[9]
    lab = actor.get_actor_label() if actor else ""
    cls = actor.get_class().get_name() if actor else ""
    if lab.startswith(("WC_PhyloWalk_", "WC_Grey", "WC_MA_Dress", "WC_HeroDress")):
        return None
    if lab == "Morning_SheepDell_Lake" or "Oceanology" in cls:
        return None
    if "Camera" in cls or "PCGVolume" in cls:
        return None
    if float(t[5].z) < 0.35:
        return None
    return {"loc": t[4], "actor": lab}

def clear_own(svc):
    rem = []
    for a in list(svc.get_all_level_actors()):
        lab = _label(a)
        if lab.startswith(OWN):
            if svc.destroy_actor(a):
                rem.append(lab)
    return rem

def spawn_mesh(mesh, loc, scale, yaw, label, folder):
    a = unreal.EditorLevelLibrary.spawn_actor_from_object(mesh, loc, unreal.Rotator(0, yaw, 0))
    if not a:
        return None
    a.set_actor_label(label)
    a.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    try:
        a.set_folder_path(folder)
        a.tags = ["Portfolio", "PhyloWalk", "Belvedere", "AtlantisKit"]
    except Exception:
        pass
    return a

def load_list(paths):
    out = []
    for p in paths:
        if EAL.does_asset_exist(p):
            out.append((p, EAL.load_asset(p)))
    return out

def main():
    svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if not world or world.get_name() != "L_MelusinaMorning":
        print("PHYLO " + json.dumps({"error": "need_morning", "world": world.get_name() if world else None}))
        return 1

    # Spire base from shaft
    base = None
    for a in svc.get_all_level_actors():
        if _label(a) == "WC_GreySpire_Shaft":
            try:
                o, e = a.get_actor_bounds(False, False)
                # use XY of shaft; Z from ground trace
                base = [float(o.x), float(o.y), float(o.z)]
            except Exception:
                t = a.get_actor_transform()
                base = [t.translation.x, t.translation.y, t.translation.z]
            break
    if not base:
        base = [160.0, 1600.0, 1200.0]

    # Shaft bounds Z is center — always re-snap XY to real ground
    g0 = ground_at(world, base[0], base[1], 4000.0)
    if not g0:
        for r in (100, 200, 400, 600):
            for ang in range(0, 360, 45):
                g0 = ground_at(world, base[0] + r * math.cos(math.radians(ang)), base[1] + r * math.sin(math.radians(ang)), 4000.0)
                if g0:
                    base[0] = float(g0["loc"].x)
                    base[1] = float(g0["loc"].y)
                    break
            if g0:
                break
    if g0:
        base[2] = float(g0["loc"].z)
    else:
        base[2] = 900.0

    floors = load_list(ATL["floor"])
    stairs = load_list(ATL["stairs"])
    arches = load_list(ATL["arch"])
    rails = load_list(ATL["rail"])
    columns = load_list(ATL["column"])
    veh = resolve_veh_paths()
    veh_meshes = {}
    for k, p in veh.items():
        if p and EAL.does_asset_exist(p):
            veh_meshes[k] = (p, EAL.load_asset(p))

    if not floors:
        print("PHYLO " + json.dumps({"error": "no_atlantis_floors"}))
        return 1

    removed = clear_own(svc)
    placed = []
    skipped = []

    # Phyllotaxis spiral walk: 48 pads, c~95, slight rise
    N = 64
    c = 110.0
    for i in range(N):
        r = c * math.sqrt(i + 1)
        th = i * GOLDEN
        x = base[0] + r * math.cos(th)
        y = base[1] + r * math.sin(th)
        zhint = base[2] + i * 8.0  # gentle climb outward
        g = ground_at(world, x, y, zhint)
        if not g:
            skipped.append({"i": i, "reason": "no_ground"})
            continue
        loc = g["loc"]
        path, mesh = floors[i % len(floors)]
        sc = autofit_scale(mesh, 0.55 if i % 3 else 0.7)
        if sc is None:
            skipped.append({"i": i, "reason": "autofit", "mesh": path})
            continue
        yaw = math.degrees(th) + 90
        lab = f"WC_PhyloWalk_Pad_{i:02d}"
        if spawn_mesh(mesh, unreal.Vector(loc.x, loc.y, loc.z + 8), sc, yaw, lab, "Greybox/Belvedere/PhyloWalk"):
            placed.append({"label": lab, "mesh": path, "scale": sc, "ground": g["actor"], "r": r})

        # stairs every 6th as riser accent
        if i > 0 and i % 6 == 0 and stairs:
            path_s, mesh_s = stairs[(i // 6) % len(stairs)]
            scs = autofit_scale(mesh_s, 0.45)
            if scs:
                lab_s = f"WC_PhyloWalk_Stair_{i:02d}"
                if spawn_mesh(mesh_s, unreal.Vector(loc.x, loc.y, loc.z + 20), scs, yaw, lab_s, "Greybox/Belvedere/PhyloWalk"):
                    placed.append({"label": lab_s, "mesh": path_s, "scale": scs})

        # arch gateways every 12
        if i > 0 and i % 12 == 0 and arches:
            path_a, mesh_a = arches[(i // 12) % len(arches)]
            sca = autofit_scale(mesh_a, 0.35)
            if sca:
                lab_a = f"WC_PhyloWalk_Arch_{i:02d}"
                if spawn_mesh(mesh_a, unreal.Vector(loc.x, loc.y, loc.z + 40), sca, yaw, lab_a, "Greybox/Belvedere/PhyloWalk"):
                    placed.append({"label": lab_a, "mesh": path_a, "scale": sca})

        # rail scraps
        if i % 5 == 2 and rails:
            path_r, mesh_r = rails[i % len(rails)]
            scr = autofit_scale(mesh_r, 0.4)
            if scr:
                lab_r = f"WC_PhyloWalk_Rail_{i:02d}"
                if spawn_mesh(mesh_r, unreal.Vector(loc.x + 40 * math.cos(th), loc.y + 40 * math.sin(th), loc.z + 30), scr, yaw, lab_r, "Greybox/Belvedere/PhyloWalk"):
                    placed.append({"label": lab_r, "mesh": path_r, "scale": scr})

    # Vehicle accents at 3 landings (inner / mid / outer)
    landings = [5, 20, 40]
    accent_order = ["ladder", "chest", "barrel", "rug", "lantern"]
    for li, idx in enumerate(landings):
        # find pad with that index
        pad = next((p for p in placed if p["label"] == f"WC_PhyloWalk_Pad_{idx:02d}"), None)
        if not pad:
            continue
        # re-trace
        # use stored — need loc from actor
        for a in svc.get_all_level_actors():
            if _label(a) == pad["label"]:
                t = a.get_actor_transform()
                for ak in accent_order:
                    if ak not in veh_meshes:
                        continue
                    if (li + accent_order.index(ak)) % 2:
                        continue
                    vp, vm = veh_meshes[ak]
                    scv = autofit_scale(vm, 0.5)
                    if not scv:
                        continue
                    lab_v = f"WC_PhyloWalk_Veh_{ak}_{idx:02d}"
                    off = 60 + 20 * accent_order.index(ak)
                    yaw = t.rotation.rotator().yaw if hasattr(t.rotation, "rotator") else 0
                    try:
                        yaw = float(t.rotator().yaw)
                    except Exception:
                        yaw = 0.0
                    if spawn_mesh(vm, unreal.Vector(t.translation.x + off, t.translation.y, t.translation.z + 10), scv, yaw, lab_v, "Greybox/Belvedere/PhyloWalk/Vehicles"):
                        placed.append({"label": lab_v, "mesh": vp, "scale": scv, "role": "vehicle_accent"})
                break

    # column markers at golden indices
    for i in (1, 8, 21, 34):
        if not columns:
            break
        pad = next((p for p in placed if p["label"] == f"WC_PhyloWalk_Pad_{i:02d}"), None)
        if not pad:
            continue
        for a in svc.get_all_level_actors():
            if _label(a) == pad["label"]:
                t = a.get_actor_transform()
                path_c, mesh_c = columns[i % len(columns)]
                scc = autofit_scale(mesh_c, 0.3)
                if scc and spawn_mesh(mesh_c, unreal.Vector(t.translation.x, t.translation.y, t.translation.z + 5), scc, 0, f"WC_PhyloWalk_Col_{i:02d}", "Greybox/Belvedere/PhyloWalk"):
                    placed.append({"label": f"WC_PhyloWalk_Col_{i:02d}", "mesh": path_c, "scale": scc})
                break

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        saved = True
    except Exception as e:
        saved = str(e)

    report = {
        "schema": "melodia.phylo_atlantis_vehicle_walk.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base": base,
        "removed": removed,
        "placed_count": len(placed),
        "skipped": skipped[:30],
        "veh_resolved": veh,
        "veh_loaded": list(veh_meshes.keys()),
        "floors_loaded": len(floors),
        "stairs_loaded": len(stairs),
        "arches_loaded": len(arches),
        "level_saved": saved,
        "placed_sample": placed[:25],
        "never_touched": ["Morning_SheepDell_Lake", "WC_GreySpire_* kept", "HeroCorners", "PPV"],
    }
    out = Path(unreal.Paths.project_dir()) / "Saved" / "Audit" / "phylo_atlantis_vehicle_walk_2026-09-20.json"
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print("PHYLO " + json.dumps({
        "placed": len(placed),
        "skipped": len(skipped),
        "veh": list(veh_meshes.keys()),
        "base": base,
        "saved": saved,
        "out": str(out),
    }, default=str))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
