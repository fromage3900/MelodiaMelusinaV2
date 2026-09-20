"""Walk-POV cams + full-level mesh placement heatmap + set-dress pass for L_MelusinaMorning."""
from __future__ import annotations
import json
import math
from datetime import datetime, timezone
from pathlib import Path
import unreal

EAL = unreal.EditorAssetLibrary
LOOKDEV_TAG = "WorldCompiler.lookdev"
EYE_Z = 170.0  # cm above deck


def _label(a):
    try:
        return a.get_actor_label() or ""
    except Exception:
        return ""


def _cls(a):
    try:
        return a.get_class().get_name()
    except Exception:
        return ""


def _look_at(from_v, to_v):
    d = unreal.Vector(to_v.x - from_v.x, to_v.y - from_v.y, to_v.z - from_v.z)
    yaw = math.degrees(math.atan2(d.y, d.x))
    horiz = math.sqrt(d.x * d.x + d.y * d.y) or 1.0
    pitch = math.degrees(math.atan2(d.z, horiz))
    return unreal.Rotator(-pitch, yaw, 0.0)


def place_walk_pov_cams(svc, field_loc):
    # Destroy prior walk POV cams
    destroyed = []
    for a in list(svc.get_all_level_actors()):
        lab = _label(a)
        if lab.startswith("WC_Lookdev_walk_"):
            if svc.destroy_actor(a):
                destroyed.append(lab)

    walks = [a for a in svc.get_all_level_actors() if _label(a).startswith("WC_EscherWalk_")]
    # Score decks: prefer closer to field, with clear look toward field
    scored = []
    for w in walks:
        loc = w.get_actor_location()
        dx, dy = field_loc.x - loc.x, field_loc.y - loc.y
        dist = math.sqrt(dx * dx + dy * dy)
        # Prefer mid-distance decks (8–35 m) with view of field
        if 800 <= dist <= 4500:
            scored.append((abs(dist - 2000), dist, w, loc))
    scored.sort(key=lambda t: t[0])

    spawned = []
    picks = []
    # pick two diverse: closest-to-ideal and one more lateral
    for item in scored:
        if len(picks) >= 2:
            break
        _, dist, w, loc = item
        # avoid near-duplicates
        if picks and abs(picks[-1][0] - dist) < 400:
            continue
        picks.append((dist, w, loc))

    names = ["walk_deck_meadow", "walk_deck_approach"]
    for i, (dist, w, loc) in enumerate(picks):
        cam_loc = unreal.Vector(loc.x, loc.y, loc.z + EYE_Z)
        # look slightly above field center for horizon
        look = unreal.Vector(field_loc.x, field_loc.y, field_loc.z + 80)
        rot = _look_at(cam_loc, look)
        actor = svc.spawn_actor_from_class(unreal.CameraActor, cam_loc, rot)
        if not actor:
            continue
        name = names[i] if i < len(names) else ("walk_deck_%d" % i)
        actor.set_actor_label("WC_Lookdev_%s" % name)
        try:
            actor.tags = [LOOKDEV_TAG, "Portfolio", "WalkPOV"]
        except Exception:
            pass
        cam_comp = actor.camera_component if hasattr(actor, "camera_component") else actor.get_component_by_class(unreal.CameraComponent)
        if cam_comp:
            cam_comp.set_editor_property("field_of_view", 60.0)
        spawned.append({
            "label": _label(actor),
            "deck": _label(w),
            "loc_cm": [cam_loc.x, cam_loc.y, cam_loc.z],
            "dist_to_field_cm": dist,
            "fov": 60,
        })
    return {"destroyed": destroyed, "spawned": spawned, "candidates_scored": len(scored)}


def collect_placement_points(svc):
    """All static mesh actor origins + ISM/HISM instance world locations."""
    points = []  # {x,y,z,kind,label,mesh}
    for a in svc.get_all_level_actors():
        lab = _label(a)
        cn = _cls(a)
        # StaticMeshActor center
        if cn == "StaticMeshActor":
            loc = a.get_actor_location()
            mesh = None
            try:
                for c in a.get_components_by_class(unreal.StaticMeshComponent) or []:
                    mesh = c.get_editor_property("static_mesh")
                    break
            except Exception:
                pass
            points.append({
                "x": float(loc.x), "y": float(loc.y), "z": float(loc.z),
                "kind": "static", "label": lab,
                "mesh": mesh.get_path_name() if mesh else None,
            })
        # ISM / HISM instances
        try:
            comps = list(a.get_components_by_class(unreal.InstancedStaticMeshComponent) or [])
            comps += list(a.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent) or [])
        except Exception:
            comps = []
        for c in comps:
            mesh = None
            try:
                mesh = c.get_editor_property("static_mesh")
            except Exception:
                pass
            mesh_path = mesh.get_path_name() if mesh else None
            try:
                n = int(c.get_instance_count())
            except Exception:
                n = 0
            # Cap per-component samples for huge counts but keep accuracy for morning (~1k)
            step = 1 if n <= 2000 else max(1, n // 1500)
            for i in range(0, n, step):
                try:
                    xf = c.get_instance_transform(i, True)  # world space
                    t = xf.translation
                    points.append({
                        "x": float(t.x), "y": float(t.y), "z": float(t.z),
                        "kind": "ism", "label": lab, "mesh": mesh_path,
                        "weight": float(step),
                    })
                except Exception:
                    break
    return points


def build_heatmap(points, grid_n=64):
    if not points:
        return {"error": "no points"}
    xs = [p["x"] for p in points]
    ys = [p["y"] for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    # pad 5%
    pad_x = (max_x - min_x) * 0.05 + 100
    pad_y = (max_y - min_y) * 0.05 + 100
    min_x -= pad_x
    max_x += pad_x
    min_y -= pad_y
    max_y += pad_y
    w = max(1.0, max_x - min_x)
    h = max(1.0, max_y - min_y)
    # make square bounds for clean heatmap
    side = max(w, h)
    cx = (min_x + max_x) * 0.5
    cy = (min_y + max_y) * 0.5
    min_x, max_x = cx - side * 0.5, cx + side * 0.5
    min_y, max_y = cy - side * 0.5, cy + side * 0.5

    cells = [[0.0] * grid_n for _ in range(grid_n)]
    kind_counts = {"static": 0.0, "ism": 0.0}
    for p in points:
        wt = float(p.get("weight") or 1.0)
        kind_counts[p["kind"]] = kind_counts.get(p["kind"], 0.0) + wt
        u = (p["x"] - min_x) / side
        v = (p["y"] - min_y) / side
        col = int(min(grid_n - 1, max(0, u * grid_n)))
        row = int(min(grid_n - 1, max(0, (1.0 - v) * grid_n)))  # flip Y for image
        cells[row][col] += wt

    flat = [c for row in cells for c in row]
    peak = max(flat) if flat else 1.0
    mean = sum(flat) / len(flat) if flat else 0.0
    # sparse / hot cells
    sparse = []
    hot = []
    for r in range(grid_n):
        for c in range(grid_n):
            val = cells[r][c]
            # world center of cell
            wx = min_x + (c + 0.5) / grid_n * side
            wy = min_y + (1.0 - (r + 0.5) / grid_n) * side
            if val <= 0:
                sparse.append({"row": r, "col": c, "x": wx, "y": wy, "count": 0})
            elif val >= peak * 0.6:
                hot.append({"row": r, "col": c, "x": wx, "y": wy, "count": val})

    return {
        "grid_n": grid_n,
        "bounds": {"min_x": min_x, "max_x": max_x, "min_y": min_y, "max_y": max_y, "side_cm": side},
        "point_count": len(points),
        "kind_counts": kind_counts,
        "peak": peak,
        "mean": mean,
        "cells": cells,
        "sparse_cell_count": len(sparse),
        "hot_cell_count": len(hot),
        "sparse_sample": sparse[:40],
        "hot_sample": sorted(hot, key=lambda x: -x["count"])[:20],
    }


def write_heatmap_png(heat, out_path: Path):
    cells = heat["cells"]
    grid_n = heat["grid_n"]
    peak = heat["peak"] or 1.0
    try:
        from PIL import Image
        img = Image.new("RGB", (grid_n, grid_n))
        px = img.load()
        for r in range(grid_n):
            for c in range(grid_n):
                t = cells[r][c] / peak
                # black -> amber -> white density
                if t <= 0:
                    px[c, r] = (12, 14, 22)
                else:
                    # heatmap: blue low, yellow mid, red high
                    if t < 0.5:
                        u = t / 0.5
                        px[c, r] = (int(30 + 40 * u), int(60 + 120 * u), int(140 + 40 * u))
                    else:
                        u = (t - 0.5) / 0.5
                        px[c, r] = (int(70 + 185 * u), int(180 - 100 * u), int(180 - 160 * u))
        img = img.resize((1024, 1024), Image.NEAREST)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(out_path))
        return {"ok": True, "path": str(out_path), "bytes": out_path.stat().st_size, "via": "pillow"}
    except Exception as e:
        # SVG fallback
        svg = out_path.with_suffix(".svg")
        parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 %d %d">' % (grid_n, grid_n)]
        for r in range(grid_n):
            for c in range(grid_n):
                t = cells[r][c] / peak
                if t <= 0:
                    fill = "#0c0e16"
                elif t < 0.5:
                    fill = "#26468c"
                else:
                    fill = "#e65a20"
                parts.append('<rect x="%d" y="%d" width="1" height="1" fill="%s"/>' % (c, r, fill))
        parts.append("</svg>")
        svg.parent.mkdir(parents=True, exist_ok=True)
        svg.write_text("\n".join(parts), encoding="utf-8")
        return {"ok": True, "path": str(svg), "bytes": svg.stat().st_size, "via": "svg", "pillow_err": str(e)[:120]}


def set_dress_from_heatmap(svc, heat):
    """Hide leftover clutter; keep walk + meadow; note sparse zones for dressing."""
    hidden = []
    for a in svc.get_all_level_actors():
        lab = _label(a)
        folder = ""
        try:
            folder = str(a.get_folder_path() or "")
        except Exception:
            pass
        hide = False
        if lab.startswith("SM_PM3D_Sphere3D") or lab.startswith("SM_Greybox_"):
            hide = True
        if folder.startswith("BowStage") and "PondMist" not in lab:
            hide = True
        if "Preview" in lab and "ChoralSheep" in lab:
            hide = True
        if lab in ("HoudiniEngine_RainbowBloom_3900", "Houdini_RainbowBloom_3900"):
            hide = True
        if hide:
            a.set_is_temporarily_hidden_in_editor(True)
            a.set_actor_hidden_in_game(True)
            hidden.append(lab)
        # ensure hero visible
        if lab.startswith("WC_EscherWalk_") or lab.startswith("WC_Lookdev_") or lab == "WC_morning_rainbow_bloom_Field":
            a.set_is_temporarily_hidden_in_editor(False)
            a.set_actor_hidden_in_game(False)
        if lab.startswith("FX_Morning_") or lab.startswith("WC_NS_Morning_"):
            a.set_is_temporarily_hidden_in_editor(False)
            a.set_actor_hidden_in_game(False)

    # Folder hygiene tags via labels already; report sparse cells as dress opportunities
    return {
        "hidden_count": len(hidden),
        "hidden_sample": hidden[:30],
        "sparse_dress_targets": heat.get("sparse_sample", [])[:25],
        "hot_clusters": heat.get("hot_sample", [])[:15],
    }


def capture_walk_cams(svc):
    """SceneCapture stills for WC_Lookdev_walk_* only."""
    cams = [a for a in svc.get_all_level_actors() if _label(a).startswith("WC_Lookdev_walk_")]
    if not cams:
        return {"shots": [], "error": "no walk cams"}
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    out_dir = Path(unreal.Paths.project_dir()) / "Saved" / "Audit" / "Screens"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).date().isoformat()
    rt = unreal.RenderingLibrary.create_render_target2d(
        world, 1920, 1080, unreal.TextureRenderTargetFormat.RTF_RGBA8, unreal.LinearColor(0, 0, 0, 1), False)
    cap = svc.spawn_actor_from_class(unreal.SceneCapture2D, unreal.Vector(0, 0, 0))
    shots = []
    try:
        comp = cap.get_editor_property("capture_component2d")
        comp.set_editor_property("texture_target", rt)
        comp.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
        comp.set_editor_property("capture_every_frame", False)
        for a in cams:
            loc = a.get_actor_location()
            rot = a.get_actor_rotation()
            cap.set_actor_location_and_rotation(loc, rot, False, False)
            cam_comp = a.camera_component if hasattr(a, "camera_component") else a.get_component_by_class(unreal.CameraComponent)
            fov = 60.0
            if cam_comp:
                try:
                    fov = float(cam_comp.get_editor_property("field_of_view"))
                except Exception:
                    pass
            comp.set_editor_property("fov_angle", fov)
            try:
                pps = comp.get_editor_property("post_process_settings")
                pps.set_editor_property("override_auto_exposure_bias", True)
                pps.set_editor_property("auto_exposure_bias", 0.5)
                comp.set_editor_property("post_process_settings", pps)
                comp.set_editor_property("post_process_blend_weight", 1.0)
            except Exception:
                pass
            for _ in range(3):
                comp.capture_scene()
            name = _label(a).replace("WC_Lookdev_", "")
            fn = out_dir / ("wc_morning_rainbow_bloom_%s_%s.png" % (name, stamp))
            opts = unreal.ImageWriteOptions()
            opts.set_editor_property("format", unreal.DesiredImageFormat.PNG)
            opts.set_editor_property("overwrite_file", True)
            opts.set_editor_property("async_", False)
            unreal.ImageWriteBlueprintLibrary.export_to_disk(rt, str(fn).replace("\\", "/"), opts)
            shots.append({"name": name, "file": str(fn).replace("\\", "/"), "bytes": fn.stat().st_size if fn.exists() else 0})
    finally:
        cap.destroy_actor()
    return {"shots": shots}


def main():
    svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    field = next((a for a in svc.get_all_level_actors() if _label(a) == "WC_morning_rainbow_bloom_Field"), None)
    field_loc = field.get_actor_location() if field else unreal.Vector(-2300, 1440, 66)

    walk_cams = place_walk_pov_cams(svc, field_loc)
    points = collect_placement_points(svc)
    heat = build_heatmap(points, grid_n=64)
    out_png = Path(unreal.Paths.project_dir()) / "Saved" / "Audit" / "Screens" / "l_melusina_morning_mesh_heatmap_2026-09-20.png"
    png_rec = write_heatmap_png(heat, out_png) if "cells" in heat else {"ok": False}
    dress = set_dress_from_heatmap(svc, heat)
    shots = capture_walk_cams(svc)

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        saved = True
    except Exception as e:
        saved = str(e)

    # strip heavy cells from JSON receipt
    heat_light = {k: v for k, v in heat.items() if k != "cells"}
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "world": unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name(),
        "walk_cams": walk_cams,
        "heatmap": heat_light,
        "heatmap_image": png_rec,
        "set_dress": dress,
        "walk_shots": shots,
        "level_saved": saved,
    }
    out = Path(unreal.Paths.project_dir()) / "Saved" / "Audit" / "morning_walk_heatmap_setdress_2026-09-20.json"
    # also dump cell matrix separately for tooling
    cells_path = Path(unreal.Paths.project_dir()) / "Saved" / "Audit" / "morning_mesh_heatmap_cells_2026-09-20.json"
    if "cells" in heat:
        cells_path.write_text(json.dumps({"bounds": heat["bounds"], "grid_n": heat["grid_n"], "cells": heat["cells"]}), encoding="utf-8")
        report["cells_file"] = str(cells_path)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    summary = {
        "walk_cams": walk_cams.get("spawned"),
        "points": heat_light.get("point_count"),
        "bounds_side_cm": (heat_light.get("bounds") or {}).get("side_cm"),
        "kind_counts": heat_light.get("kind_counts"),
        "sparse_cells": heat_light.get("sparse_cell_count"),
        "hot_cells": heat_light.get("hot_cell_count"),
        "heatmap_image": png_rec,
        "hidden": dress.get("hidden_count"),
        "shots": shots.get("shots"),
        "saved": saved,
        "report": str(out),
    }
    print("WALK_HEAT " + json.dumps(summary, default=str))
    unreal.log("WALK_HEAT " + json.dumps(summary, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
