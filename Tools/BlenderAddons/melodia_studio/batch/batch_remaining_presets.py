"""Overnight batch: process remaining Melodia presets through the terrain
world-gen pipeline using the proven Python erosion/weathering fallback
(gaea_erosion_processor). Gaea CLI automation is blocked; do not attempt it.

Per preset:
  1. generate_world(MIDI, preset_id) -> voxel OBJ (midi_bridge)
  2. heightfield PNG export from OBJ (16-bit)
  3. dressing plan JSON (terrain_dressing)
  4. erosion/weathering + ue_handoff via process_preset()

Outputs under Saved/Audit/world_build_20260824/<preset_id>/ plus
ue_handoff/{heightfield.png,dressing_plan.json,handoff_manifest.json}.
Evidence manifest with SHA-256 hashes written next to manifest_all_presets.json.

Batch processing only - no UE .uasset writes, no new features.
"""
import importlib.util
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

REPO = "C:/EnvironmentPortfolio/BS_GodFile"
OUT_BASE = os.path.join(REPO, "Saved", "Audit", "world_build_20260824")
MIDI = os.path.join(REPO, "Content", "MelodiaIntegration", "MIDI", "128BPMarpeggiomelody.mid")
STUDIO = os.path.join(REPO, "Tools", "BlenderAddons", "melodia_studio")

# Presets already in a ue_handoff state (exact preset_id match in handoff manifests).
DONE = {
    "ballad_plaza_ballad", "berceuse_overhang_madrigal", "canon_echo_pavane",
    "cathedral_wide_crystalline", "fugue_maze_fugue", "gavotte_hedges_aria",
    "lullaby_cave_lullaby", "nocturne_reflection_nocturne",
    "rhapsody_fold_chaconne", "ritornello_rings_madrigal",
    "tarantella_bounce_saltarello", "toccata_spires_toccata",
    "verdant_default", "waltz_garden_waltz",
}

# Sensible dressing-style pairing per remaining preset.
STYLE_FOR_PRESET = {
    "resonant_default": "verdant",
    "cathedral_wide": "cathedral",
    "dense_spire": "toccata_surface",
    "surface_only": "bare",
    "abyss_caves": "pavane_grotto",
    "waltz_corridors": "waltz_garden",
    "ballad_broadstage": "ballad_plaza",
    "toccata_spires": "toccata_surface",
    "fugue_labyrinth": "fugue_maze",
    "lullaby_undergrowth": "lullaby_cave",
    "nocturne_ribbon": "nocturne_reflection",
    "tarantella_bounce": "saltarello_ledges",
    "canon_echo": "aria_mist",
    "gavotte_hedges": "verdant",
    "rhapsody_fold": "chaconne_weave",
    "berceuse_overhang": "madrigal_canopy",
    "ritornello_rings": "crystalline",
}


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(STUDIO, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # required: dataclasses resolves annotations via sys.modules
    spec.loader.exec_module(mod)
    return mod


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    mb = _load("midi_bridge")
    td = _load("terrain_dressing")
    gep = _load("gaea_erosion_processor")

    all_presets = list(mb.DEFAULT_PRESETS.keys())
    todo = [p for p in all_presets if p not in DONE]
    print("TODO=%d %s" % (len(todo), ",".join(todo)))

    results = {}
    for preset_id in todo:
        style_id = STYLE_FOR_PRESET[preset_id]
        base = os.path.join(OUT_BASE, preset_id)
        os.makedirs(base, exist_ok=True)
        entry = {"preset_id": preset_id, "style_id": style_id, "status": "error"}

        try:
            # 1. Terrain OBJ from MIDI bridge
            out_obj = os.path.join(base, "terrain_%s.obj" % preset_id)
            world = mb.generate_world(MIDI, preset_id=preset_id, out_obj=out_obj)
            obj_path = world["obj"]
            entry["terrain"] = {
                "obj": obj_path,
                "sha256": sha256(obj_path),
                "verts": world.get("verts"),
                "faces": world.get("faces"),
            }

            # 2. Heightfield PNG (16-bit) from OBJ vertices
            hf_path = os.path.join(base, "heightfield_%s.png" % preset_id)
            hf_info = _export_heightfield(obj_path, hf_path)
            entry["heightfield"] = {"path": hf_path, "sha256": sha256(hf_path), **hf_info}

            # 3. Dressing plan JSON
            plan_path = os.path.join(base, "dressing_plan_%s.json" % preset_id)
            field = _field_from_obj(obj_path)
            seed = 11 + all_presets.index(preset_id)
            dress_plan, dress_stats = td.plan_dressing(field, style_id=style_id, seed=seed, budget=1400)
            magic_plan, magic_stats = td.plan_magic(field, style_id=style_id)
            style_label = td.load_styles().get(style_id, {}).get("label", style_id)
            plan = {
                "style_id": style_id,
                "style_label": "%s_%s" % (preset_id, style_id),
                "seed": seed,
                "budget": 1400,
                "terrain_obj": obj_path,
                "field_cells": len(field),
                "dressing": {"count": len(dress_plan), "stats": dress_stats, "items": dress_plan[:20]},
                "magic": {"count": len(magic_plan), "stats": magic_stats, "items": magic_plan[:20]},
            }
            with open(plan_path, "w", encoding="utf-8") as f:
                json.dump(plan, f, indent=2)
            entry["dressing_plan"] = {
                "path": plan_path, "sha256": sha256(plan_path),
                "props": plan["dressing"]["count"], "magic": plan["magic"]["count"],
            }

            # 4. Erosion/weathering + UE handoff (Python fallback)
            res = gep.process_preset(preset_id, OUT_BASE)
            if res.get("status") != "ok":
                raise RuntimeError("process_preset failed: %s" % res)
            handoff = res["handoff"]
            entry["status"] = "ok"
            entry["ue_handoff"] = {
                "manifest": handoff["artifacts"]["dressing_plan"]["path"].replace(
                    "dressing_plan.json", "handoff_manifest.json"),
                "heightfield": handoff["artifacts"]["heightfield"]["path"],
                "dressing_plan": handoff["artifacts"]["dressing_plan"]["path"],
                "pixel_dimensions": handoff["validation"]["pixel_dimensions"],
                "reprojection_items_updated": handoff["validation"]["dressing_reprojection"]["items_updated"],
            }
            print("OK %s props=%d magic=%d px=%sx%s" % (
                preset_id, plan["dressing"]["count"], plan["magic"]["count"],
                handoff["validation"]["pixel_dimensions"]["width"],
                handoff["validation"]["pixel_dimensions"]["height"]))
        except Exception as exc:  # keep batch going overnight
            entry["error"] = repr(exc)
            print("FAIL %s %r" % (preset_id, exc))

        results[preset_id] = entry

    evidence = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "kind": "melodia_remaining_presets_batch",
        "generator": os.path.basename(__file__),
        "pipeline": "python erosion/weathering fallback (Gaea CLI blocked)",
        "midi": MIDI,
        "presets_done_before": sorted(DONE),
        "presets_processed": results,
        "summary": {
            "attempted": len(todo),
            "ok": sum(1 for e in results.values() if e["status"] == "ok"),
            "failed": sum(1 for e in results.values() if e["status"] != "ok"),
        },
    }
    ev_path = os.path.join(OUT_BASE, "evidence_remaining_presets_20260825.json")
    with open(ev_path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2)
    print("EVIDENCE=" + ev_path)
    print("SUMMARY=%(ok)d ok / %(failed)d failed / %(attempted)d attempted" % evidence["summary"])


def _export_heightfield(obj_path, out_png):
    """16-bit grayscale heightfield PNG from axis-aligned voxel OBJ."""
    from PIL import Image

    xs, ys, zs = [], [], []
    with open(obj_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("v "):
                parts = line.strip().split()
                x, y, z = map(float, parts[1:4])
                xs.append(x); ys.append(y); zs.append(z)
    if not xs:
        raise RuntimeError("No vertices in OBJ: %s" % obj_path)

    min_x, min_y, min_z = min(xs), min(ys), min(zs)
    max_z = max(zs)
    z_range = max(1.0, max_z - min_z)
    width = max(1, int(max(xs) - min_x) + 1)
    height = max(1, int(max(ys) - min_y) + 1)

    img = Image.new("I;16", (width, height))
    pixels = img.load()
    for x, y, z in zip(xs, ys, zs):
        ix, iy = int(x - min_x), int(y - min_y)
        if 0 <= ix < width and 0 <= iy < height:
            norm = int((z - min_z) / z_range * 65535)
            pixels[ix, iy] = min(65535, max(0, norm))

    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    img.save(out_png)
    return {"width": width, "height": height, "z_min": min_z, "z_max": max_z}


def _field_from_obj(obj_path):
    """Minimal {(x,y): (z, color)} field for dressing planning."""
    field = {}
    with open(obj_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("v "):
                parts = line.strip().split()
                x, y, z = map(float, parts[1:4])
                key = (int(x), int(y))
                colour = float(parts[4]) if len(parts) > 4 else 0.5
                if key not in field or z > field[key][0]:
                    field[key] = (z, colour)
    return field


if __name__ == "__main__":
    main()
