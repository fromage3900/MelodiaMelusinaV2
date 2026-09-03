# -*- coding: utf-8 -*-
"""Wire the cymatics + optical-LOD parameter contract into every Melodia master material.

Follows the wire_* family contract documented in
`Docs/Production/TEXT_INJECTION_WIRING_PLAYBOOK_2026-08-25.md` row 31: idempotent
locate-or-create, recompile + save tail, audit JSON to Saved/Audit/.

WHY BOTH NODE KINDS
-------------------
The house pattern (established on M_Master_Toon_Landscape_HeightBlend) is:
  CollectionParameter reads the LIVE bus  ->  ScalarParameter is the PER-INSTANCE gain
  ...multiplied together downstream.
A material instance can only set the ScalarParameter half. Setting a CollectionParameter
name on an MI is a silent no-op, so the two halves are deliberately distinct names.

Defaults are chosen so a freshly-wired master is VISUALLY IDENTICAL to before:
every gain that scales a contribution defaults to 0 (Cymatic_*), and the optical-LOD
values default to the neutral/no-op end of their range.

Run inside the editor:
    exec(open(r"C:/EnvironmentPortfolio/BS_GodFile/Content/Python/wire_cymatics_masters.py", encoding="utf-8").read())
"""
import json
import os
from datetime import datetime

try:
    import unreal
except ImportError:
    unreal = None

MPC_PALETTE = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"
MPC_CYMATICS = "/Game/Melodia/Cymatics/MPC_Cymatics_Driver"

# (name, default, slider_min, slider_max, group, sort_priority)
SCALARS = [
    ("Cymatic_ModeN",               4.0, 0.0, 32.0, "90 | Cymatics",    9001),
    ("Cymatic_ModeM",               6.0, 0.0, 32.0, "90 | Cymatics",    9002),
    ("Cymatic_BeatPulse",           0.0, 0.0,  1.0, "90 | Cymatics",    9003),
    ("Cymatic_BassIntensity",       0.0, 0.0,  1.0, "90 | Cymatics",    9004),
    ("Cymatic_MidIntensity",        0.0, 0.0,  1.0, "90 | Cymatics",    9005),
    ("Cymatic_EmissiveScale",       0.0, 0.0,  4.0, "90 | Cymatics",    9006),
    ("Cymatic_IridescenceShift",    0.0, 0.0,  1.0, "90 | Cymatics",    9007),
    ("Cymatic_UVDistortion",        0.0, 0.0,  1.0, "90 | Cymatics",    9008),
    ("CymaticAmplitude",            0.0, 0.0,  2.0, "90 | Cymatics",    9009),
    ("POM_StepCount",              32.0, 0.0, 64.0, "91 | Optical LOD", 9101),
    ("Toksvig_AntiAliasing_Weight", 0.0, 0.0,  1.0, "91 | Optical LOD", 9102),
    ("WPO_Resonance_Scale",         1.0, 0.0,  4.0, "91 | Optical LOD", 9103),
    ("Grazing_Rim_Boost",           1.0, 0.0,  4.0, "91 | Optical LOD", 9104),
    ("LOD_Tier_Index",              0.0, 0.0,  3.0, "91 | Optical LOD", 9105),
]

# (parameter_name, collection_path) — the live read half of the contract.
COLLECTIONS = [
    ("BeatPulse",     MPC_PALETTE),
    ("BassIntensity", MPC_PALETTE),
    ("MidIntensity",  MPC_PALETTE),
]

MASTERS = [
    "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal",
    "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal_Alpha",
    "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki",
    "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape",
    "/Game/EnvSandbox/Materials/Masters/M_Master_SDF_Toon",
    "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend",
    "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Character",
    "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Cosmic",
    "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Unified",
    "/Game/EnvSandbox/Materials/Masters/M_Master_Simple_Universal",
]


def wire_master(path):
    mel = unreal.MaterialEditingLibrary
    m = unreal.EditorAssetLibrary.load_asset(path)
    if not m:
        return {"master": path, "status": "missing"}
    m.modify()
    exprs = list(mel.get_material_expressions(m) or [])

    have_scalar, have_coll = set(), set()
    for e in exprs:
        cls = type(e).__name__
        try:
            pn = str(e.get_editor_property("parameter_name"))
        except Exception:
            continue
        if cls == "MaterialExpressionScalarParameter":
            have_scalar.add(pn)
        elif cls == "MaterialExpressionCollectionParameter":
            have_coll.add(pn)

    added_s, added_c = [], []
    y = -2400
    for nm, dv, lo, hi, grp, sp in SCALARS:
        if nm in have_scalar:
            continue
        n = mel.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -4200, y)
        n.set_editor_property("parameter_name", nm)
        n.set_editor_property("default_value", dv)
        n.set_editor_property("slider_min", lo)
        n.set_editor_property("slider_max", hi)
        n.set_editor_property("group", grp)
        n.set_editor_property("sort_priority", sp)
        added_s.append(nm)
        y += 150

    for nm, coll_path in COLLECTIONS:
        if nm in have_coll:
            continue
        coll = unreal.EditorAssetLibrary.load_asset(coll_path)
        if not coll:
            unreal.log_warning("[CymaticsWire] MPC missing: %s" % coll_path)
            continue
        n = mel.create_material_expression(m, unreal.MaterialExpressionCollectionParameter, -4600, y)
        n.set_editor_property("collection", coll)
        n.set_editor_property("parameter_name", nm)
        added_c.append(nm)
        y += 150

    mel.recompile_material(m)
    unreal.EditorAssetLibrary.save_loaded_asset(m, only_if_is_dirty=False)
    return {
        "master": path,
        "status": "wired",
        "scalars_added": added_s,
        "collections_added": added_c,
        "scalars_preexisting": sorted(have_scalar & {s[0] for s in SCALARS}),
        "node_count_after": len(list(mel.get_material_expressions(m) or [])),
    }


def main():
    if unreal is None:
        print("[CymaticsWire] no editor — simulated")
        return
    results = [wire_master(p) for p in MASTERS]
    for r in results:
        print("[CymaticsWire] %-58s %s  +%d scalars  +%d collections" % (
            r["master"].rsplit("/", 1)[-1], r["status"],
            len(r.get("scalars_added", [])), len(r.get("collections_added", []))))
    out = os.path.join(unreal.Paths.project_saved_dir(), "Audit", "cymatics_master_wire.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"generated": datetime.now().isoformat(), "results": results}, fh, indent=1)
    print("[CymaticsWire] audit -> %s" % out)


main()
