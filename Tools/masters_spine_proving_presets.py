"""Proving-preset MI authoring for the masters spine.

Run INSIDE the Unreal editor via Monolith editor_query(run_python, mode=execute_file):

    run_python execute_file C:/.../Tools/masters_spine_proving_presets.py M_Master_Toon_Character

Creates ONE MaterialInstanceConstant per parameter-column group on a spine master,
each carrying authored overrides for every MI-overridable parameter in that column,
so every column family is verifiable in-editor without graph surgery.

Idempotent: if a preset instance already exists it is re-parented, re-authored and
re-saved (repair), never skipped - the previous run may have died mid-loop and left
a partial instance in memory.

Rules honoured (specs/materials/master_spine_canon.v1.json):
  - additive content authoring only: masters are never touched;
  - save only the exact new packages (no bulk save);
  - CollectionParameters (MPC readers) are intentionally NOT overridden - they are
    proven by the runtime lane, and recorded in the receipt as non-MI params;
  - engine placeholder textures are fallback-only: proving presets may bind engine
    textures to prove override semantics, and are marked as verification artifacts.

UE 5.8 API notes (learned live):
  - MaterialInstanceConstant creation needs MaterialInstanceConstantFactoryNew;
    MaterialFactoryNew now rejects MIC (AssetTools.cpp:1763 ensure).
  - MaterialEditingLibrary renamed the MI parameter surface to
    set/get_material_instance_{scalar,vector,texture}_parameter_value; short names
    are kept as runtime fallbacks for older engines.
"""
import json
import os
import sys
import unreal

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUTDIR = os.path.join(ROOT, "Saved", "Audit", "MastersSpine_20261028")

ENGINE_TEX = "/Engine/EngineResources/WhiteSquare"

COLS = {
    "M_Master_Toon_Character": {
        "master": "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Character",
        "out_dir": "/Game/EnvSandbox/Materials/Instances/Proving",
        "tag": "ToonChar",
        "columns": [
            {"n": 1, "slug": "Surface", "ov": {
                "CharacterBaseTint": {"v": [0.93, 0.86, 0.80, 1.0]},
                "CharacterRoughness": {"s": 0.70},
                "CharacterRoughnessBlend": {"s": 0.50},
            }},
            {"n": 2, "slug": "Maps", "ov": {
                "CharacterUVTiling": {"s": 2.0},
                "CharacterAlbedo": {"t": "/Game/EnvSandbox/Materials/Textures/T_Ramp_4Band"},
                "CharacterRoughnessMap": {"t": "/Game/EnvSandbox/Materials/Textures/T_Noise_White"},
            }},
            {"n": 3, "slug": "Role", "ov": {
                "CharacterMaterialID": {"s": 2.0},
                "CharacterRoleBlend": {"s": 0.40},
                "CharacterRoleTint": {"v": [0.75, 0.65, 0.95, 1.0]},
            }},
            {"n": 4, "slug": "FaceSDF", "ov": {
                "CharacterFaceSDFTiling": {"s": 2.0},
                "CharacterFaceSDFStrength": {"s": 0.80},
                "CharacterFaceTint": {"v": [0.92, 0.72, 0.62, 1.0]},
            }},
            {"n": 5, "slug": "Sheen", "ov": {
                "CharacterHeroSheenPower": {"s": 16.0},
                "CharacterHeroSheenStrength": {"s": 1.0},
                "CharacterHeroSheenColor": {"v": [1.0, 0.88, 0.50, 1.0]},
                "CharacterEmissiveBase": {"v": [0.04, 0.02, 0.012, 1.0]},
            }},
            {"n": 6, "slug": "Wind", "ov": {
                "CharacterWindSpeed": {"s": 2.0},
                "CharacterWindAmplitude": {"s": 0.35},
            }},
            {"n": 7, "slug": "Cymatics", "ov": {
                "CymaticsLandscapeAmount": {"s": 0.60},
                "CymaticsTint": {"v": [0.82, 0.74, 1.00, 1.0]},
            }},
            {"n": 8, "slug": "Chladni", "ov": {
                "ChladniUVTiling": {"s": 3.0},
                "ChladniIntensity": {"s": 1.0},
                "HarmonizeActive": {"s": 1.0},
                "BeatAccent": {"s": 1.5},
                "ChladniEmissiveStrength": {"s": 4.0},
                "ChladniSheenStrength": {"s": 0.9},
                "ChladniPearlSilkColor": {"v": [0.88, 0.84, 1.00, 1.0]},
            }},
        ],
    },
    "M_Water_Oceanology_Melodia": {
        "master": "/Game/EnvSandbox/Materials/Masters/M_Water_Oceanology_Melodia",
        "out_dir": "/Game/EnvSandbox/Materials/Instances/Proving",
        "tag": "Water",
        "columns": [
            {"n": 1, "slug": "Biolum", "ov": {
                "Biolum_ShearProxy": {"s": 0.72},
                "Biolum_RippleMask": {"s": 0.85},
                "Biolum_CrestCompression": {"s": 0.35},
                "Biolum_DepthMask": {"s": 0.70},
                "Biolum_BlueGreenTint": {"v": [0.05, 0.62, 0.58, 1.0]},
                "Biolum_CyanTint": {"v": [0.30, 0.95, 1.00, 1.0]},
                "Biolum_GreenTint": {"v": [0.15, 0.85, 0.40, 1.0]},
                "Biolum_Intensity": {"s": 1.35},
                "Biolum_Density": {"s": 0.45},
                "Biolum_FlashRate": {"s": 2.2},
                "Biolum_FlashThreshold": {"s": 0.28},
                "Biolum_FlashDecay": {"s": 2.4},
                "Biolum_Weight": {"s": 0.90},
            }},
            {"n": 2, "slug": "ToonBands", "ov": {
                "Toon_Bands": {"s": 5.0},
                "Toon_Weight": {"s": 0.80},
            }},
            {"n": 3, "slug": "Sparkle", "ov": {
                "Nikki_SparkleIntensity": {"s": 1.60},
                "Nikki_SparkleThreshold": {"s": 0.45},
                "Nikki_SparkleColor": {"v": [0.95, 0.85, 0.55, 1.0]},
                "Nikki_SparkleMask": {"t": "/Game/EnvSandbox/Materials/Textures/T_Noise_White"},
            }},
        ],
    },
}

# Generated tables (Tools/masters_spine_generate_cols.py) extend COLS without
# hand-editing this file; a missing module is not an error.
try:
    sys.path.insert(0, HERE)
    from masters_spine_cols_generated import GENERATED_COLS

    for _gen_key, _gen_val in GENERATED_COLS.items():
        COLS.setdefault(_gen_key, _gen_val)
except Exception as _gen_exc:
    print("NO_GENERATED_COLS", _gen_exc)


def param_sets_from_master(master):
    sets = {"S": set(), "V": set(), "T": set(), "MPC": []}
    for e in unreal.MaterialEditingLibrary.get_material_expressions(master):
        cls = str(e.get_class().get_name())
        try:
            name = str(e.get_editor_property("parameter_name"))
        except Exception:
            continue
        if cls == "MaterialExpressionScalarParameter":
            sets["S"].add(name)
        elif cls == "MaterialExpressionVectorParameter":
            sets["V"].add(name)
        elif cls.startswith("MaterialExpressionTextureSampleParameter") or cls in (
            "MaterialExpressionTextureParameter", "MaterialExpressionTextureSampleParameterCube",
            "MaterialExpressionTextureObjectParameter",
        ):
            sets["T"].add(name)
        elif cls == "MaterialExpressionCollectionParameter":
            sets["MPC"].append(name)
    return sets


def _mel(new_name, old_name):
    lib = unreal.MaterialEditingLibrary
    return getattr(lib, new_name) if hasattr(lib, new_name) else getattr(lib, old_name)


def mel_set_scalar(mi, name, v):
    return _mel("set_material_instance_scalar_parameter_value", "set_scalar_parameter_value")(mi, name, float(v))


def mel_get_scalar(mi, name):
    return float(_mel("get_material_instance_scalar_parameter_value", "get_scalar_parameter_value")(mi, name))


def mel_set_vector(mi, name, lin):
    return _mel("set_material_instance_vector_parameter_value", "set_vector_parameter_value")(mi, name, lin)


def mel_get_vector(mi, name):
    return _mel("get_material_instance_vector_parameter_value", "get_vector_parameter_value")(mi, name)


def mel_set_texture(mi, name, tex):
    return _mel("set_material_instance_texture_parameter_value", "set_texture_parameter_value")(mi, name, tex)


def mel_get_texture(mi, name):
    return _mel("get_material_instance_texture_parameter_value", "get_texture_parameter_value")(mi, name)


def auth_param(mi, name, kind, value):
    if kind == "s":
        mel_set_scalar(mi, name, value)
        return float(value), round(mel_get_scalar(mi, name), 6)
    if kind == "v":
        lin = unreal.LinearColor(value[0], value[1], value[2], value[3])
        mel_set_vector(mi, name, lin)
        got = mel_get_vector(mi, name)
        return value, [round(got.r, 6), round(got.g, 6), round(got.b, 6), round(got.a, 6)]
    if kind == "t":
        tex = unreal.EditorAssetLibrary.load_asset(value)
        if tex is None or tex.get_class().get_name() != "Texture2D":
            return value, "BIND_SKIPPED_NOT_TEXTURE2D"
        mel_set_texture(mi, name, tex)
        got = mel_get_texture(mi, name)
        return value, (str(got) if got else "READBACK_NONE")
    raise ValueError(kind)


def decode_override(val):
    if len(val) == 1 and "s" in val:
        return "s", val["s"]
    if len(val) == 1 and "v" in val:
        return "v", val["v"]
    if len(val) == 1 and "t" in val:
        return "t", val["t"]
    return None, None


def apply_overrides(mi, col, sets, row):
    for pname, val in col["ov"].items():
        kind, v = decode_override(val)
        have = (kind == "s" and pname in sets["S"]) or (kind == "v" and pname in sets["V"]) \
            or (kind == "t" and pname in sets["T"])
        if not have:
            row["overrides"][pname] = "ERROR_PARAM_TYPE_MISMATCH"
            row["status"] = "failed"
            continue
        authored, got = auth_param(mi, pname, kind, v)
        if kind == "s":
            ok = isinstance(got, float) and abs(got - float(authored)) < 1e-4
        elif kind == "v":
            ok = isinstance(got, list) and len(got) == 4 and abs(sum(got) - sum(authored)) < 1e-3
        else:
            ok = got not in ("BIND_SKIPPED_NOT_TEXTURE2D", "READBACK_NONE")
        row["overrides"][pname] = {"kind": {"s": "scalar", "v": "vector", "t": "texture"}[kind],
                                   "value": authored, "readback": got, "ok": bool(ok)}
        if not ok:
            row["status"] = "failed"


def main():
    key = sys.argv[1] if len(sys.argv) > 1 else "M_Master_Toon_Character"
    cfg = COLS.get(key)
    if cfg is None:
        print("NO_PRESET_TABLE for", key)
        sys.exit(1)
    master = unreal.load_asset(cfg["master"])
    if master is None:
        print("MASTER_LOAD_FAILED", cfg["master"])
        sys.exit(1)
    sets = param_sets_from_master(master)
    at = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.MaterialInstanceConstantFactoryNew()

    receipt = {"schema": "melodia.proving_presets_receipt.v1", "when": "2026-10-28",
               "master": key, "master_path": cfg["master"],
               "out_dir": cfg["out_dir"], "presets": []}
    unreal.EditorAssetLibrary.make_directory(cfg["out_dir"])

    for col in cfg["columns"]:
        name = "MI_Prove_%s_%02d_%s" % (cfg["tag"], col["n"], col["slug"])
        path = cfg["out_dir"] + "/" + name
        repaired = False
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            mi = unreal.load_asset(path)
            if mi is not None and mi.get_class().get_name() == "MaterialInstanceConstant":
                repaired = True
                print("REPAIR", name)
            else:
                receipt["presets"].append({"name": name, "status": "REPAIR_LOAD_FAILED"})
                continue
        else:
            mi = at.create_asset(name, cfg["out_dir"], unreal.MaterialInstanceConstant, factory)
            if mi is None:
                receipt["presets"].append({"name": name, "status": "CREATE_FAILED"})
                continue
        mi.set_editor_property("parent", master)
        row = {"name": name, "status": ("repaired_authored" if repaired else "authored"),
               "package": path, "overrides": {}}
        apply_overrides(mi, col, sets, row)
        saved = unreal.EditorAssetLibrary.save_loaded_asset(mi, False)
        row["saved_return"] = bool(saved)
        receipt["presets"].append(row)
        print("MI", name, "|", row["status"], "| ok:",
              all(o["ok"] for o in row["overrides"].values() if isinstance(o, dict)),
              "| saved_return", saved)

    receipt["non_mi_collection_params"] = sets["MPC"]
    receipt["param_set_sizes"] = {"scalar": len(sets["S"]), "vector": len(sets["V"]),
                                  "texture": len(sets["T"])}
    os.makedirs(OUTDIR, exist_ok=True)
    out_path = os.path.join(OUTDIR, "receipt_proving_presets_%s.json" % key)
    with open(out_path, "w") as fh:
        json.dump(receipt, fh, indent=1)
    print("RECEIPT", out_path)
    print("NON_MI_COLLECTION_QUEUE", sets["MPC"])
    print("DONE_OK")


main()
