import json, os

REPO = "C:/EnvironmentPortfolio/BS_GodFile"
OUT_BASE = os.path.join(REPO, "Saved", "Audit", "world_build_20260824")
PRESETS = [
    "verdant_default",
    "cathedral_wide_crystalline",
    "toccata_spires_toccata",
    "waltz_garden_waltz",
    "ballad_plaza_ballad",
    "fugue_maze_fugue",
    "nocturne_reflection_nocturne",
    "lullaby_cave_lullaby",
    "tarantella_bounce_saltarello",
    "canon_echo_pavane",
    "gavotte_hedges_aria",
    "rhapsody_fold_chaconne",
    "berceuse_overhang_madrigal",
    "ritornello_rings_madrigal",
]

manifest = {
    "timestamp": "2026-08-24T13:00:00Z",
    "presets": {},
}

for preset in PRESETS:
    plan_path = os.path.join(OUT_BASE, preset, "dressing_plan_" + preset + ".json")
    hf_path = os.path.join(OUT_BASE, preset, "heightfield_" + preset + ".png")
    entry = {
        "status": "missing",
        "dressing_plan": plan_path if os.path.exists(plan_path) else None,
        "heightfield": hf_path if os.path.exists(hf_path) else None,
    }
    if os.path.exists(plan_path):
        with open(plan_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        entry.update({
            "status": "ready",
            "style_label": data["style_label"],
            "seed": data["seed"],
            "budget": data["budget"],
            "field_cells": data["field_cells"],
            "props_count": data["dressing"]["count"],
            "magic_count": data["magic"]["count"],
            "terrain_obj": data["terrain_obj"],
            "sample_items": data["dressing"]["items"][:5],
        })
    manifest["presets"][preset] = entry

manifest_path = os.path.join(OUT_BASE, "manifest_all_presets.json")
with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)
ready = sum(1 for e in manifest["presets"].values() if e["status"] == "ready")
print("MANIFEST=" + manifest_path)
print("READY=" + str(ready) + "/" + str(len(PRESETS)))
