"""Ground M_Master_Nikki's placeholder texture defaults and broken vector defaults.

Run INSIDE the editor via Monolith editor_query(run_python, mode=execute_file):
    run_python execute_file Tools/nikki_master_grounding.py

Fixes (idempotent, readback-verified, receipted):
- Albedo texture params -> the project's fabric drape base colour (replaces marble).
- NormalMap params (Texture group + Triplanar group) -> T_Neutral_Normal.
- NikkiSDFIris_Mask -> T_RadialMask_01 (white square gave a blank iris).
- NikkiSDFIris_Center vector -> (0.5, 0.5, 0.0, 1.0) (had a 15.56 channel).
- NikkiSquish_Direction -> (0.6, 0.8, 0.0, 0.0) (was unnormalised).
- All BaseTint nodes -> (0.98, 0.93, 0.96, 1.0) (duplicate nodes disagreed).

Leaves OpacityMap white (correct for an opaque master), ORM/Roughness/Metallic
neutral maps, EmissiveMap black, and every scalar default untouched.
Writes Saved/Audit/FarawayProductionHardening_20261029/nikki_master_grounding.json.
"""
import json
import os
import sys
import unreal

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUTDIR = os.path.join(ROOT, "Saved", "Audit", "FarawayProductionHardening_20261029")
MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki"

WANT_TEX = {
    "Albedo": "T_Cymatic_FarawayAlabasterDrape_BaseColor",
    "NormalMap": "T_Neutral_Normal",
    "NikkiSDFIris_Mask": "T_RadialMask_01",
}
WANT_VEC = {
    "NikkiSDFIris_Center": [0.5, 0.5, 0.0, 1.0],
    "NikkiSquish_Direction": [0.6, 0.8, 0.0, 0.0],
    "BaseTint": [0.98, 0.93, 0.96, 1.0],
}


def resolve_tex(name):
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    for a in ar.get_assets_by_path('/Game', True, False):
        if str(a.asset_name) == name and str(a.asset_class_path.asset_name) == 'Texture2D':
            return unreal.load_asset(str(a.package_name))
    return None


def main():
    mel = unreal.MaterialEditingLibrary
    m = unreal.load_asset(MASTER)
    if m is None:
        print("MASTER_LOAD_FAILED")
        sys.exit(1)
    exprs = mel.get_material_expressions(m)
    receipt = {"schema": "melodia.nikki_master_grounding.v1", "when": "2026-10-29",
               "master": MASTER, "textures": {}, "vectors": {}, "skipped": []}

    tex_cache = {k: resolve_tex(v) for k, v in WANT_TEX.items()}
    for name, tex in tex_cache.items():
        if tex is None:
            receipt["skipped"].append("texture_not_found:" + WANT_TEX[name])

    for e in exprs:
        cls = str(e.get_class().get_name())
        try:
            pname = str(e.get_editor_property("parameter_name"))
        except Exception:
            continue
        if "Texture" in cls and pname in WANT_TEX:
            tex = tex_cache.get(pname)
            if tex is None:
                continue
            try:
                e.set_editor_property("texture", tex)
                got = e.get_editor_property("texture")
                receipt["textures"].setdefault(pname, []).append({
                    "node": str(e.get_name()), "target": WANT_TEX[pname],
                    "readback_ok": bool(got) and got.get_name() == tex.get_name(),
                })
            except Exception as exc:
                receipt["skipped"].append("texture_set_failed:%s:%s" % (pname, str(exc)[:80]))
        elif cls == "MaterialExpressionVectorParameter" and pname in WANT_VEC:
            try:
                v = WANT_VEC[pname]
                e.set_editor_property("default_value", unreal.LinearColor(v[0], v[1], v[2], v[3]))
                got = e.get_editor_property("default_value")
                receipt["vectors"].setdefault(pname, []).append({
                    "node": str(e.get_name()),
                    "set": v,
                    "readback": [round(got.r, 4), round(got.g, 4), round(got.b, 4), round(got.a, 4)],
                    "ok": all(abs(getattr(got, k) - v[i]) < 1e-4 for i, k in enumerate("rgba")),
                })
            except Exception as exc:
                receipt["skipped"].append("vector_set_failed:%s:%s" % (pname, str(exc)[:80]))

    try:
        receipt["recompile"] = str(mel.recompile_material(m))
    except Exception as exc:
        receipt["recompile"] = "EXC " + str(exc)[:100]
    receipt["saved"] = bool(unreal.EditorAssetLibrary.save_loaded_asset(m, False))

    os.makedirs(OUTDIR, exist_ok=True)
    out = os.path.join(OUTDIR, "nikki_master_grounding.json")
    with open(out, "w") as fh:
        json.dump(receipt, fh, indent=1)
    print("TEXTURES", json.dumps(receipt["textures"]))
    print("VECTORS", json.dumps(receipt["vectors"]))
    print("SKIPPED", receipt["skipped"])
    print("SAVED", receipt["saved"])
    print("RECEIPT", out)


main()
