# -*- coding: utf-8 -*-
"""HeroCorners MA set-dress: raycast place themed meshes + MI tune.
v3 autofit 2026-09-20: GhostLotus + Overgrowth ALLOWED — auto-scale so
world half-extent <= TARGET (bad scale was the bug, not the assets).
Ignore dress actors on traces. Labels WC_MA_Dress_*.
"""
from __future__ import annotations
import json, math, random
from datetime import datetime, timezone
from pathlib import Path
import unreal

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
OUT = Path(unreal.Paths.project_saved_dir()) / "Audit" / "hero_corners_ma_dress_2026-09-20.json"

# Target world size after scale (uu). ~2.5–3m half-extent for hero dress props.
TARGET_HALF_EXTENT_UU = 250.0
MAX_AXIS_UU = 500.0
MIN_SCALE = 0.002  # skip only if even this still exceeds target

MESHES = {
    "rock": [
        "/Game/Brushify/Materials/Landscape/ProceduralMeshes/Rocks/Rock_01/S_Rock_01",
        "/Game/Brushify/Materials/Landscape/ProceduralMeshes/Rocks/Rock_02/S_Rock_02",
        "/Game/Brushify/Materials/Landscape/ProceduralMeshes/Rocks/Rock_03/S_Rock_03",
        "/Game/Megascans/3D_Assets/MossyForestRock/SM_MossyForestRock_01",
        "/Game/Megascans/3D_Assets/MossyForestRock/SM_MossyForestRock_02",
    ],
    "overgrowth": [
        "/Game/Brushify/Meshes/FloatingIslands/Dressing/Overgrowth_01/S_Overgrowth_01",
        "/Game/Brushify/Meshes/FloatingIslands/Dressing/Overgrowth_01/S_Overgrowth_02",
    ],
    "bush": [
        "/Game/Brushify/Meshes/Foliage/Bushes/GenericBush/S_GenericBush_Small",
        "/Game/Brushify/Meshes/Foliage/Bushes/GenericBush/S_GenericBush_Medium",
    ],
    "flora": [
        "/Game/Megascans/3D_Plants/PurpleShamrock/SM_PurpleShamrock_01",
        "/Game/Megascans/3D_Plants/PurpleShamrock/SM_PurpleShamrock_02",
        "/Game/EnvSandbox/Meshes/SurrealFlora/GhostLotus_GlowCore",
        "/Game/EnvSandbox/Meshes/SurrealFlora/GhostLotus_Receptacle",
    ],
}

PREFERRED_MI = {
    "rock": [
        "/Game/Brushify/Materials/Landscape/ProceduralMeshes/Rocks/Rock_01/MI_Rock_01",
        "/Game/Brushify/Materials/Landscape/ProceduralMeshes/Rocks/Rock_02/MI_Rock_02",
        "/Game/Megascans/3D_Assets/MossyForestRock/MI_MossyForestRock_01",
    ],
    "bush": [
        "/Game/Brushify/Meshes/Foliage/Bushes/GenericBush/Materials/Green/MI_GenericBushLeaves",
        "/Game/Brushify/Meshes/Foliage/Bushes/GenericBush/Materials/Green/MI_GenericBushBark",
    ],
    "overgrowth": [
        "/Game/Brushify/Meshes/Foliage/Bushes/GenericBush/Materials/Green/MI_GenericBushLeaves",
    ],
    "flora": [
        "/Game/Megascans/3D_Plants/PurpleShamrock/MI_PurpleShamrock_01",
    ],
}

CORNERS = [
    {
        "id": "WestRim",
        "cam": "WC_HeroCorner_WestRim_Cam",
        "pcg": "WC_HeroCorner_WestRim_PCG",
        "count": 7,
        "kit": ["rock", "rock", "rock", "overgrowth", "bush", "flora", "rock"],
        "radius": 650.0,
        "scale": (0.55, 1.15),
        "seed": 202609221,
    },
    {
        "id": "EastBank",
        "cam": "WC_HeroCorner_EastBank_Cam",
        "pcg": "WC_HeroCorner_EastBank_PCG",
        "count": 8,
        "kit": ["overgrowth", "bush", "bush", "flora", "flora", "rock", "overgrowth", "bush"],
        "radius": 700.0,
        "scale": (0.5, 1.15),
        "seed": 202609222,
    },
    {
        "id": "MeadowChorus",
        "cam": "WC_HeroCorner_MeadowChorus_Cam",
        "pcg": "WC_morning_rainbow_bloom_Field",
        "count": 6,
        "kit": ["rock", "rock", "flora", "flora", "overgrowth", "bush"],
        "radius": 900.0,
        "scale": (0.45, 1.05),
        "seed": 202609223,
    },
    {
        "id": "NorthDress",
        "cam": "WC_HeroCorner_NorthDress_Cam",
        "pcg": "WC_HeroCorner_NorthDress_PCG",
        "count": 8,
        "kit": ["rock", "rock", "flora", "flora", "flora", "overgrowth", "bush", "rock"],
        "radius": 800.0,
        "scale": (0.5, 1.1),
        "seed": 202609224,
    },
]

BAD_MAT_TOKENS = ("WorldGridMaterial", "M_Material_003", "BasicShape", "Engine/EngineMaterials", "Greybox")
DRESS_LABEL_PREFIXES = ("WC_MA_Dress_", "WC_HeroDress_", "WC_PortfolioDress_", "WC_HeroCornerDress_")
DRESS_TAGS = ("SetDress", "HeroDress", "MA_Dress", "PortfolioDress")
GOOD_GROUND_PREFIXES = ("BrushifyIsland_", "Landscape")


def _label(a):
    try:
        return a.get_actor_label() or ""
    except Exception:
        return ""


def _find(svc, name):
    for a in svc.get_all_level_actors():
        if _label(a) == name:
            return a
    return None


def _is_dress_actor(actor):
    if not actor:
        return False
    lab = _label(actor)
    if any(lab.startswith(p) for p in DRESS_LABEL_PREFIXES):
        return True
    try:
        tags = list(actor.tags or [])
    except Exception:
        tags = []
    return any(str(t) in DRESS_TAGS for t in tags)


def _is_good_ground(lab):
    if not lab:
        return False
    if any(lab.startswith(p) for p in DRESS_LABEL_PREFIXES):
        return False
    if any(lab.startswith(p) for p in GOOD_GROUND_PREFIXES):
        return True
    return "Island" in lab or "Landscape" in lab or "Terrain" in lab


def _collect_ignore(svc):
    return [a for a in svc.get_all_level_actors() if _is_dress_actor(a)]


def _ground(world, x, y, z_hint=2000.0, ignore=None):
    start = unreal.Vector(x, y, z_hint + 5000.0)
    end = unreal.Vector(x, y, z_hint - 8000.0)
    hit = unreal.SystemLibrary.line_trace_single(
        world, start, end,
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, ignore or [],
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
    if _is_dress_actor(actor) or not _is_good_ground(lab):
        return None
    n = t[5]
    if float(n.z) < 0.55:
        return None
    return {"loc": t[4], "normal": n, "actor": lab}


def _load_mesh(path):
    if not EAL.does_asset_exist(path):
        return None
    return EAL.load_asset(path)


def _native_half_extent(mesh):
    """Unscaled max half-extent in UU."""
    try:
        box = mesh.get_bounding_box()
        ex = box.max - box.min
        hx = abs(float(ex.x)) * 0.5
        hy = abs(float(ex.y)) * 0.5
        hz = abs(float(ex.z)) * 0.5
        return max(hx, hy, hz), max(abs(float(ex.x)), abs(float(ex.y)), abs(float(ex.z)))
    except Exception:
        return 100.0, 200.0


def _autofit_scale(mesh, desired):
    """Clamp desired scale so world half-extent <= TARGET and axis <= MAX_AXIS."""
    half0, axis0 = _native_half_extent(mesh)
    max_by_half = (TARGET_HALF_EXTENT_UU / half0) if half0 > 1e-6 else desired
    max_by_axis = (MAX_AXIS_UU / axis0) if axis0 > 1e-6 else desired
    cap = min(max_by_half, max_by_axis)
    sc = min(desired, cap)
    if sc < MIN_SCALE:
        return None, half0, axis0, cap
    return sc, half0, axis0, cap


def _destroy_prior(svc):
    gone = []
    for a in list(svc.get_all_level_actors()):
        lab = _label(a)
        if lab.startswith("WC_MA_Dress_"):
            if svc.destroy_actor(a):
                gone.append(lab)
    return gone


def _bounds_z_offset(mesh, scale):
    try:
        box = mesh.get_bounding_box()
        return abs(float(box.min.z) * scale)
    except Exception:
        return 10.0 * scale


def _tune_mi(actor, kind, report):
    tuned = []
    try:
        comps = actor.get_components_by_class(unreal.StaticMeshComponent) or []
    except Exception:
        comps = []
        c = actor.get_component_by_class(unreal.StaticMeshComponent)
        if c:
            comps = [c]
    for comp in comps:
        try:
            n = comp.get_num_materials()
        except Exception:
            n = 1
        for i in range(int(n)):
            try:
                mat = comp.get_material(i)
            except Exception:
                mat = None
            path = mat.get_path_name() if mat else ""
            bad = any(tok in path for tok in BAD_MAT_TOKENS) or not path
            if bad:
                cands = PREFERRED_MI.get(kind) or PREFERRED_MI.get("rock") or []
                for cp in cands:
                    if EAL.does_asset_exist(cp):
                        mi = EAL.load_asset(cp)
                        if mi:
                            comp.set_material(i, mi)
                            tuned.append({"slot": i, "from": path, "to": cp})
                            break
            else:
                try:
                    if isinstance(mat, unreal.MaterialInstanceConstant):
                        for pname, pval in (("Desaturation", 0.08), ("PastelLift", 0.12), ("TintStrength", 0.15)):
                            try:
                                MEL.set_material_instance_scalar_parameter_value(mat, pname, float(pval))
                            except Exception:
                                pass
                        tuned.append({"slot": i, "kept": path, "soft_tune": True})
                except Exception:
                    tuned.append({"slot": i, "kept": path})
    report["mi_tune"] = tuned
    return tuned


def _focus_for(corner, svc):
    pcg = _find(svc, corner["pcg"])
    if pcg:
        l = pcg.get_actor_location()
        return unreal.Vector(l.x, l.y, l.z)
    cam = _find(svc, corner["cam"])
    if cam:
        l = cam.get_actor_location()
        f = cam.get_actor_forward_vector()
        return unreal.Vector(l.x + f.x * 900.0, l.y + f.y * 900.0, l.z)
    return None


def main():
    svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    gone = _destroy_prior(svc)
    ignore = _collect_ignore(svc)
    loaded = {}
    mesh_caps = {}
    for kind, paths in MESHES.items():
        loaded[kind] = []
        for p in paths:
            m = _load_mesh(p)
            if not m:
                continue
            half0, axis0 = _native_half_extent(m)
            cap = min(
                (TARGET_HALF_EXTENT_UU / half0) if half0 > 1e-6 else 1.0,
                (MAX_AXIS_UU / axis0) if axis0 > 1e-6 else 1.0,
            )
            mesh_caps[p] = {"native_half": half0, "native_axis": axis0, "max_scale": cap}
            loaded[kind].append((p, m))
    report = {
        "schema": "melodia.hero_corners_ma_dress.v3_autofit",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "policy": "GhostLotus+Overgrowth allowed; autofit scale to half_extent<=250uu; ignore dress on traces",
        "target_half_extent_uu": TARGET_HALF_EXTENT_UU,
        "destroyed_prior": gone,
        "ignored_dress_count": len(ignore),
        "mesh_caps": mesh_caps,
        "meshes_loaded": {k: [p for p, _ in v] for k, v in loaded.items()},
        "corners": {},
    }
    total = 0
    for corner in CORNERS:
        rng = random.Random(corner["seed"])
        focus = _focus_for(corner, svc)
        entry = {"focus": None, "spawned": [], "skipped": []}
        if not focus:
            entry["error"] = "no focus (missing cam/pcg)"
            report["corners"][corner["id"]] = entry
            continue
        entry["focus"] = [focus.x, focus.y, focus.z]
        for i in range(corner["count"]):
            kind = corner["kit"][i % len(corner["kit"])]
            pool = loaded.get(kind) or []
            if not pool:
                entry["skipped"].append({"i": i, "reason": "no mesh for %s" % kind})
                continue
            path, mesh = pool[i % len(pool)]
            ang = (2.0 * math.pi * i / max(1, corner["count"])) + rng.uniform(-0.25, 0.25)
            rad = corner["radius"] * rng.uniform(0.35, 1.0)
            x = focus.x + math.cos(ang) * rad
            y = focus.y + math.sin(ang) * rad
            g = _ground(world, x, y, z_hint=focus.z, ignore=ignore)
            if not g:
                x = focus.x + math.cos(ang) * rad * 0.5
                y = focus.y + math.sin(ang) * rad * 0.5
                g = _ground(world, x, y, z_hint=focus.z, ignore=ignore)
            if not g:
                entry["skipped"].append({"i": i, "reason": "no ground", "xy": [x, y]})
                continue
            desired = rng.uniform(*corner["scale"])
            sc, half0, axis0, cap = _autofit_scale(mesh, desired)
            if sc is None:
                entry["skipped"].append({
                    "i": i, "reason": "autofit_impossible", "mesh": path,
                    "native_half": half0, "cap": cap,
                })
                continue
            z_off = _bounds_z_offset(mesh, sc)
            loc = unreal.Vector(g["loc"].x, g["loc"].y, g["loc"].z + z_off * 0.15)
            yaw = rng.uniform(0.0, 360.0)
            actor = unreal.EditorLevelLibrary.spawn_actor_from_object(mesh, loc, unreal.Rotator(0.0, yaw, 0.0))
            if not actor:
                entry["skipped"].append({"i": i, "reason": "spawn_failed", "mesh": path})
                continue
            name = "WC_MA_Dress_%s_%02d_%s" % (corner["id"], i, Path(path).name)
            actor.set_actor_label(name)
            try:
                actor.set_actor_scale3d(unreal.Vector(sc, sc, sc))
                actor.set_folder_path("HeroCorners/%s/MA_Dress" % corner["id"])
                actor.tags = [
                    "Portfolio", "HeroCorner", "SetDress", "MA_Dress",
                    "HeroCorner.%s" % corner["id"],
                ]
            except Exception:
                pass
            ignore.append(actor)
            half_w = half0 * sc
            rec = {
                "label": name,
                "mesh": path,
                "kind": kind,
                "loc": [loc.x, loc.y, loc.z],
                "desired_scale": desired,
                "scale": sc,
                "autofit_capped": sc < desired - 1e-6,
                "native_half": half0,
                "half_extent": half_w,
                "yaw": yaw,
                "ground": g["actor"],
                "normal_z": float(g["normal"].z),
            }
            _tune_mi(actor, kind, rec)
            entry["spawned"].append(rec)
            total += 1
        report["corners"][corner["id"]] = entry

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        report["level_saved"] = True
    except Exception as e:
        report["level_saved"] = str(e)

    report["total_spawned"] = total
    halves = [s.get("half_extent", 0) for c in report["corners"].values() for s in (c.get("spawned") or [])]
    report["max_spawned_half_extent"] = max(halves) if halves else 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    summary = {
        "total": total,
        "per": {cid: len(v.get("spawned") or []) for cid, v in report["corners"].items()},
        "max_half_extent": report["max_spawned_half_extent"],
        "out": str(OUT),
    }
    print("MA_DRESS_AUTOFIT " + json.dumps(summary))
    unreal.log("MA_DRESS_AUTOFIT " + json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
