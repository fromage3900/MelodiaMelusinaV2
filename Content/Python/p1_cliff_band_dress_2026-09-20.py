"""P1 MelusinaMorning: cliff-stuck flower cull, band rebalance, approach midground dress."""
from __future__ import annotations
import json
import math
import random
from datetime import datetime, timezone
from pathlib import Path
import unreal

MEL = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary
PREFIX = "/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowSpeedTree_"
BAND_TINTS = [
    ("B0_Red", (1.0, 0.12, 0.16), 1.35),
    ("B1_Orange", (1.0, 0.42, 0.12), 1.1),
    ("B2_Gold", (1.0, 0.78, 0.18), 1.05),
    ("B3_Green", (0.28, 0.85, 0.35), 1.0),
    ("B4_Blue", (0.22, 0.42, 0.95), 0.72),  # dial down
    ("B5_Indigo", (0.35, 0.28, 0.95), 1.15),
    ("B6_Violet", (0.82, 0.28, 1.0), 1.4),
]
FLOWER_MESH_HINTS = ("GenericFlower",)
KEEP_SURFACE = ("BrushifyIsland_",)
MIN_NORMAL_Z = 0.70
MAX_FLOAT_CM = 90.0
BLUE_LABELS = ("B4_Blue",)
DRESS_MESHES = [
    "/Game/Brushify/Materials/Landscape/ProceduralMeshes/Rocks/Rock_01/S_Rock_01",
    "/Game/Brushify/Materials/Landscape/ProceduralMeshes/Rocks/Rock_02/S_Rock_02",
    "/Game/Brushify/Meshes/Foliage/Bushes/GenericBush/S_GenericBush_Small",
    "/Game/Brushify/Meshes/Foliage/Bushes/GenericBush/S_GenericBush_Medium",
    "/Game/Brushify/Meshes/FloatingIslands/Dressing/Overgrowth_01/S_Overgrowth_01",
]


def _label(a):
    try:
        return a.get_actor_label() or ""
    except Exception:
        return ""


def _mat_band(comp):
    try:
        m = comp.get_material(0)
        if not m:
            return ""
        p = m.get_path_name()
        for lab, _, _ in BAND_TINTS:
            if lab in p:
                return lab
    except Exception:
        pass
    return ""


def _is_flower_comp(comp):
    try:
        mesh = comp.get_editor_property("static_mesh")
        if not mesh:
            return False
        name = mesh.get_name()
        return any(h in name for h in FLOWER_MESH_HINTS)
    except Exception:
        return False


def cliff_cull_flowers(svc, world, field):
    removed = []
    kept = 0
    reasons = {"not_island": 0, "steep": 0, "float": 0, "no_hit": 0}
    comps = list(field.get_components_by_class(unreal.InstancedStaticMeshComponent) or [])
    for comp in comps:
        if not _is_flower_comp(comp):
            continue
        band = _mat_band(comp)
        n = int(comp.get_instance_count())
        # collect indices to remove (high to low)
        kill = []
        for i in range(n):
            try:
                xf = comp.get_instance_transform(i, True)
            except Exception:
                continue
            t = xf.translation
            start = unreal.Vector(t.x, t.y, t.z + 400.0)
            end = unreal.Vector(t.x, t.y, t.z - 2500.0)
            hit = unreal.SystemLibrary.line_trace_single(
                world, start, end,
                unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [],
                unreal.DrawDebugTrace.NONE, True,
                unreal.LinearColor.RED, unreal.LinearColor.GREEN, 0.0,
            )
            tup = hit.to_tuple() if hit else None
            if not tup or not tup[0]:
                kill.append(i)
                reasons["no_hit"] += 1
                continue
            hit_loc = tup[4]
            normal = tup[5]
            actor = tup[9]
            lab = actor.get_actor_label() if actor else ""
            on_island = any(lab.startswith(p) for p in KEEP_SURFACE)
            if not on_island:
                kill.append(i)
                reasons["not_island"] += 1
                continue
            nz = float(normal.z) if normal else 1.0
            if nz < MIN_NORMAL_Z:
                kill.append(i)
                reasons["steep"] += 1
                continue
            if abs(float(t.z) - float(hit_loc.z)) > MAX_FLOAT_CM:
                kill.append(i)
                reasons["float"] += 1
                continue
            kept += 1
        for i in sorted(kill, reverse=True):
            try:
                comp.remove_instance(i)
                removed.append({"band": band, "idx": i})
            except Exception:
                pass
        try:
            comp.mark_render_state_dirty()
        except Exception:
            pass
    return {
        "removed": len(removed),
        "kept_flower_traces": kept,
        "reasons": reasons,
        "by_band_removed": _count_bands(removed),
    }


def _count_bands(rows):
    d = {}
    for r in rows:
        b = r.get("band") or "?"
        d[b] = d.get(b, 0) + 1
    return d


def count_flower_by_band(field):
    counts = {}
    for comp in list(field.get_components_by_class(unreal.InstancedStaticMeshComponent) or []):
        if not _is_flower_comp(comp):
            continue
        band = _mat_band(comp) or "?"
        counts[band] = counts.get(band, 0) + int(comp.get_instance_count())
    return counts


def thin_blue(field, target_ratio=1.15):
    """Cull excess Blue so Blue ≈ target_ratio * max(Red, Violet) average."""
    counts = count_flower_by_band(field)
    red = counts.get("B0_Red", 0)
    vio = counts.get("B6_Violet", 0)
    blue = counts.get("B4_Blue", 0)
    target = int(max(40, ((red + vio) / 2.0) * target_ratio)) if (red + vio) else 80
    if blue <= target:
        return {"thinned": 0, "blue_before": blue, "blue_target": target, "counts_before": counts}

    need = blue - target
    # gather blue flower comps
    slots = []
    for comp in list(field.get_components_by_class(unreal.InstancedStaticMeshComponent) or []):
        if not _is_flower_comp(comp):
            continue
        if _mat_band(comp) != "B4_Blue":
            continue
        n = int(comp.get_instance_count())
        for i in range(n):
            slots.append((comp, i))
    random.Random(20260920).shuffle(slots)
    # remove from end of each comp — regroup by comp and remove high indices
    by_comp = {}
    for comp, i in slots[:need]:
        by_comp.setdefault(comp, []).append(i)
    thinned = 0
    for comp, idxs in by_comp.items():
        for i in sorted(idxs, reverse=True):
            try:
                # after prior removes indices shift — safer: remove random remaining from end
                n = int(comp.get_instance_count())
                if n <= 0:
                    break
                # map original i may be stale; remove last instance instead for count target
                comp.remove_instance(n - 1)
                thinned += 1
            except Exception:
                pass
        try:
            comp.mark_render_state_dirty()
        except Exception:
            pass
    return {
        "thinned": thinned,
        "blue_before": blue,
        "blue_target": target,
        "counts_before": counts,
        "counts_after": count_flower_by_band(field),
    }


def rebalance_tints():
    out = []
    for label, tint, boost in BAND_TINTS:
        path = PREFIX + label
        mi = EAL.load_asset(path)
        if not mi:
            out.append({"label": label, "ok": False})
            continue
        r, g, b = tint
        br = min(1.5, r * boost)
        bg = min(1.5, g * boost)
        bb = min(1.5, b * boost)
        MEL.set_material_instance_vector_parameter_value(
            mi, "MelodiaWindRevealTint", unreal.LinearColor(br, bg, bb, 1.0)
        )
        try:
            MEL.set_material_instance_scalar_parameter_value(mi, "MelodiaWindResponse", 0.5)
        except Exception:
            pass
        # slight hue seed spread
        try:
            idx = int(label[1])
            MEL.set_material_instance_scalar_parameter_value(
                mi, "MelodiaWindHueSeed", (idx + 1) / 14.0
            )
        except Exception:
            pass
        EAL.save_asset(path)
        out.append({"label": label, "ok": True, "tint": [br, bg, bb], "boost": boost})
    return out


def _ground_at(world, x, y, z_hint=2000.0):
    hit = unreal.SystemLibrary.line_trace_single(
        world,
        unreal.Vector(x, y, z_hint + 3000.0),
        unreal.Vector(x, y, z_hint - 4000.0),
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [],
        unreal.DrawDebugTrace.NONE, True,
        unreal.LinearColor.RED, unreal.LinearColor.GREEN, 0.0,
    )
    tup = hit.to_tuple() if hit else None
    if not tup or not tup[0]:
        return None
    return {
        "loc": tup[4],
        "normal": tup[5],
        "actor": tup[9].get_actor_label() if tup[9] else None,
    }


def dress_approach(svc, world):
    # destroy prior portfolio dress
    destroyed = []
    for a in list(svc.get_all_level_actors()):
        if _label(a).startswith("WC_PortfolioDress_"):
            if svc.destroy_actor(a):
                destroyed.append(_label(a))

    landing = next((a for a in svc.get_all_level_actors() if _label(a) == "WC_EscherWalk_platform_landing_00"), None)
    meadow = next((a for a in svc.get_all_level_actors() if _label(a) == "WC_EscherWalk_spur_westbank_00"), None)
    field = next((a for a in svc.get_all_level_actors() if _label(a) == "WC_morning_rainbow_bloom_Field"), None)
    if not landing or not field:
        return {"ok": False, "error": "missing landing or field", "destroyed": destroyed}

    a0 = landing.get_actor_location()
    a1 = field.get_actor_location()
    # pull toward meadow deck if present
    if meadow:
        a1 = unreal.Vector(
            (field.get_actor_location().x + meadow.get_actor_location().x) * 0.5,
            (field.get_actor_location().y + meadow.get_actor_location().y) * 0.5,
            field.get_actor_location().z,
        )

    meshes = []
    for p in DRESS_MESHES:
        m = EAL.load_asset(p)
        if m:
            meshes.append((p, m))
    if not meshes:
        return {"ok": False, "error": "no dress meshes", "destroyed": destroyed}

    rng = random.Random(20260920)
    spawned = []
    # 10 anchors along approach, with lateral jitter
    for i in range(10):
        t = (i + 1) / 11.0
        x = a0.x + (a1.x - a0.x) * t
        y = a0.y + (a1.y - a0.y) * t
        # perpendicular offset
        dx, dy = a1.x - a0.x, a1.y - a0.y
        length = math.sqrt(dx * dx + dy * dy) or 1.0
        px, py = -dy / length, dx / length
        side = rng.choice([-1.0, 1.0])
        off = rng.uniform(180.0, 520.0) * side
        x += px * off
        y += py * off
        g = _ground_at(world, x, y, z_hint=max(a0.z, a1.z))
        if not g:
            continue
        lab = g["actor"] or ""
        if not (lab.startswith("BrushifyIsland_") or lab.startswith("WC_EscherWalk_")):
            continue
        if float(g["normal"].z) < 0.65:
            continue
        path, mesh = meshes[i % len(meshes)]
        loc = unreal.Vector(g["loc"].x, g["loc"].y, g["loc"].z)
        yaw = rng.uniform(0, 360)
        scale = rng.uniform(0.75, 1.35)
        if "Rock" in path:
            scale = rng.uniform(0.9, 1.6)
        if "Bush" in path:
            scale = rng.uniform(0.7, 1.1)
        actor = unreal.EditorLevelLibrary.spawn_actor_from_object(mesh, loc, unreal.Rotator(0, yaw, 0))
        if not actor:
            continue
        name = "WC_PortfolioDress_%02d_%s" % (i, Path(path).name)
        actor.set_actor_label(name)
        try:
            actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))
        except Exception:
            pass
        try:
            actor.tags = ["Portfolio", "SetDress", "ApproachFill"]
            actor.set_folder_path("PortfolioDress/Approach")
        except Exception:
            pass
        spawned.append({
            "label": name,
            "mesh": path,
            "loc": [loc.x, loc.y, loc.z],
            "scale": scale,
            "ground": lab,
        })

    # optional mist: ensure WC_NS_Morning_mist visible (Material Artist owns system)
    mist_shown = []
    for a in svc.get_all_level_actors():
        lab = _label(a)
        if lab.startswith("WC_NS_Morning_mist") or lab == "WC_NS_Morning_mist":
            a.set_is_temporarily_hidden_in_editor(False)
            a.set_actor_hidden_in_game(False)
            mist_shown.append(lab)

    return {
        "ok": True,
        "destroyed": destroyed,
        "spawned": spawned,
        "mist_shown": mist_shown,
    }


def capture_key_plates(svc):
    names = [
        "WC_Lookdev_walk_deck_meadow",
        "WC_Lookdev_walk_deck_approach",
        "WC_Lookdev_website_oblique",
        "WC_Lookdev_website_south",
    ]
    cams = [a for a in svc.get_all_level_actors() if _label(a) in names]
    # keep midmorning
    uds = next((a for a in svc.get_all_level_actors() if _label(a) == "Ultra_Dynamic_Sky2"), None)
    if uds:
        try:
            uds.set_editor_property("Animate Time of Day", False)
            uds.set_editor_property("Time of Day", 1100.0)
            uds.set_editor_property("Cloud Coverage", 1.8)
            uds.set_editor_property("Sun Light Intensity", 5.5)
            uds.set_editor_property("Overall Intensity", 1.25)
        except Exception:
            pass
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    out_dir = Path(unreal.Paths.project_dir()) / "Saved" / "Portfolio" / "Hero" / "MelusinaMorning"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = "2026-09-20"
    rt = unreal.RenderingLibrary.create_render_target2d(
        world, 1920, 1080, unreal.TextureRenderTargetFormat.RTF_RGBA8, unreal.LinearColor(0, 0, 0, 1), False
    )
    cap = svc.spawn_actor_from_class(unreal.SceneCapture2D, unreal.Vector(0, 0, 0))
    shots = []
    try:
        comp = cap.get_editor_property("capture_component2d")
        comp.set_editor_property("texture_target", rt)
        comp.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
        for a in cams:
            loc = a.get_actor_location()
            rot = a.get_actor_rotation()
            cap.set_actor_location_and_rotation(loc, rot, False, False)
            cam = a.get_component_by_class(unreal.CameraComponent)
            fov = 60.0
            if cam:
                try:
                    fov = float(cam.get_editor_property("field_of_view"))
                except Exception:
                    pass
            comp.set_editor_property("fov_angle", fov)
            for _ in range(4):
                comp.capture_scene()
            short = _label(a).replace("WC_Lookdev_", "")
            fn = out_dir / ("hero_midmorning_%s_p1_%s.png" % (short, stamp))
            opts = unreal.ImageWriteOptions()
            opts.set_editor_property("format", unreal.DesiredImageFormat.PNG)
            opts.set_editor_property("overwrite_file", True)
            opts.set_editor_property("async_", False)
            unreal.ImageWriteBlueprintLibrary.export_to_disk(rt, str(fn).replace("\\", "/"), opts)
            shots.append({"name": short, "file": str(fn), "bytes": fn.stat().st_size if fn.exists() else 0})
    finally:
        cap.destroy_actor()
    return shots


def main():
    svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    field = next((a for a in svc.get_all_level_actors() if _label(a) == "WC_morning_rainbow_bloom_Field"), None)
    if not field:
        print("P1ERR no field")
        return 1

    before = count_flower_by_band(field)
    cull = cliff_cull_flowers(svc, world, field)
    after_cull = count_flower_by_band(field)
    thin = thin_blue(field)
    after_thin = count_flower_by_band(field)
    tints = rebalance_tints()
    dress = dress_approach(svc, world)
    shots = capture_key_plates(svc)

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        saved = True
    except Exception as e:
        saved = str(e)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "before_bands": before,
        "cull": cull,
        "after_cull": after_cull,
        "thin_blue": thin,
        "after_thin": after_thin,
        "tints": tints,
        "dress": dress,
        "shots": shots,
        "level_saved": saved,
    }
    out = Path(unreal.Paths.project_dir()) / "Saved" / "Audit" / "p1_cliff_band_dress_2026-09-20.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    summary = {
        "before": before,
        "after_thin": after_thin,
        "removed_cliff": cull.get("removed"),
        "reasons": cull.get("reasons"),
        "blue_thinned": thin.get("thinned"),
        "dress_count": len((dress or {}).get("spawned") or []),
        "shots": [(s["name"], s["bytes"]) for s in shots],
        "saved": saved,
        "report": str(out),
    }
    print("P1DONE " + json.dumps(summary, default=str))
    unreal.log("P1DONE " + json.dumps(summary, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
