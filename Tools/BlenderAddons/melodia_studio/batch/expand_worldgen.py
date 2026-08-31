"""Expand Melodia world-gen pipeline outputs for UE import.

Produces:
- heightfield PNG from generated OBJ
- dressing plan JSON from terrain dressing
- evidence JSON with SHA, voxel stats, and output paths
"""
import importlib.util
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

REPO = "C:/EnvironmentPortfolio/BS_GodFile"
OUT = os.path.join(REPO, "Saved", "Audit", "world_build_waltz_garden_20260824")
MIDI = os.path.join(REPO, "Content", "MelodiaIntegration", "MIDI", "128BPMarpeggiomelody.mid")


def load_mb():
    path = os.path.join(REPO, "Tools", "BlenderAddons", "melodia_studio", "midi_bridge.py")
    spec = importlib.util.spec_from_file_location("mb", path)
    mb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mb)
    return mb


def load_td():
    path = os.path.join(REPO, "Tools", "BlenderAddons", "melodia_studio", "terrain_dressing.py")
    spec = importlib.util.spec_from_file_location("td", path)
    td = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(td)
    return td


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def export_heightfield_from_obj(obj_path, out_png):
    """Minimal heightfield PNG export from OBJ vertices.

    Assumes OBJ is axis-aligned voxel terrain with vertex colors.
    Produces a 16-bit grayscale PNG where Z -> height.
    """
    try:
        from PIL import Image
    except Exception as exc:
        raise RuntimeError("PIL required for heightfield export: %s" % exc)

    xs = []
    ys = []
    zs = []
    with open(obj_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("v "):
                parts = line.strip().split()
                x, y, z = map(float, parts[1:4])
                xs.append(x)
                ys.append(y)
                zs.append(z)

    if not xs:
        raise RuntimeError("No vertices in OBJ")

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    min_z, max_z = min(zs), max(zs)
    z_range = max(1.0, max_z - min_z)

    width = int(max_x - min_x) + 1
    height = int(max_y - min_y) + 1
    width = max(width, 1)
    height = max(height, 1)

    img = Image.new("I;16", (width, height))
    pixels = img.load()
    for x, y, z in zip(xs, ys, zs):
        ix = int(x - min_x)
        iy = int(y - min_y)
        if 0 <= ix < width and 0 <= iy < height:
            norm = int((z - min_z) / z_range * 65535)
            pixels[ix, iy] = min(65535, max(0, norm))

    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    img.save(out_png)
    return {
        "path": out_png,
        "width": width,
        "height": height,
        "z_min": min_z,
        "z_max": max_z,
        "z_range": z_range,
    }


def export_dressing_plan(td, world, out_json, style_id="waltz_garden", seed=11, budget=1400):
    """Export dressing/magic plan JSON from generated terrain."""
    obj_path = world.get("obj", "")
    if not obj_path or not os.path.exists(obj_path):
        raise RuntimeError("Terrain OBJ missing: %s" % obj_path)

    # Build a minimal field from OBJ for planning
    field = {}
    with open(obj_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("v "):
                parts = line.strip().split()
                x, y, z = map(float, parts[1:4])
                key = (int(x), int(y))
                if key not in field or z > field[key][0]:
                    field[key] = (z, float(parts[4]) if len(parts) > 4 else 0.5)

    dress_plan, dress_stats = td.plan_dressing(field, style_id=style_id, seed=seed, budget=budget)
    magic_plan, magic_stats = td.plan_magic(field, style_id=style_id)
    style_label = td.load_styles().get(style_id, {}).get("label", style_id)

    plan = {
        "style_id": style_id,
        "style_label": style_label,
        "seed": seed,
        "budget": budget,
        "terrain_obj": obj_path,
        "field_cells": len(field),
        "dressing": {
            "count": len(dress_plan),
            "stats": dress_stats,
            "items": dress_plan[:20],  # sample for review
        },
        "magic": {
            "count": len(magic_plan),
            "stats": magic_stats,
            "items": magic_plan[:20],
        },
    }

    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2)
    return plan


def main():
    os.makedirs(OUT, exist_ok=True)
    mb = load_mb()
    td = load_td()

    # 1. Generate terrain
    world = mb.generate_world(MIDI, preset_id="waltz_garden")
    obj_path = world["obj"]
    print("TERRAIN=" + obj_path)
    print("VERTS=" + str(world.get("verts")))
    print("FACES=" + str(world.get("faces")))

    # 2. Heightfield PNG
    hf_path = os.path.join(OUT, "heightfield_waltz_garden.png")
    hf = export_heightfield_from_obj(obj_path, hf_path)
    print("HEIGHTFIELD=" + hf_path)
    print("HF_SIZE=" + str(os.path.getsize(hf_path)))

    # 3. Dressing plan JSON
    plan_path = os.path.join(OUT, "dressing_plan_waltz_garden.json")
    plan = export_dressing_plan(td, world, plan_path)
    print("DRESS_PLAN=" + plan_path)
    print("PROPS=" + str(plan["dressing"]["count"]))
    print("MAGIC=" + str(plan["magic"]["count"]))

    # 4. Evidence JSON
    evidence = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "preset": "waltz_garden",
        "midi": MIDI,
        "terrain": {
            "obj": obj_path,
            "sha256": sha256(obj_path),
            "voxels": world.get("voxels"),
            "verts": world.get("verts"),
            "faces": world.get("faces"),
            "blocks": world.get("blocks"),
        },
        "heightfield": {
            "png": hf_path,
            "sha256": sha256(hf_path),
            **hf,
        },
        "dressing_plan": {
            "json": plan_path,
            "sha256": sha256(plan_path),
            "props": plan["dressing"]["count"],
            "magic": plan["magic"]["count"],
        },
    }
    ev_path = os.path.join(OUT, "evidence_waltz_garden.json")
    with open(ev_path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2)
    print("EVIDENCE=" + ev_path)
    print("DONE")


if __name__ == "__main__":
    main()
