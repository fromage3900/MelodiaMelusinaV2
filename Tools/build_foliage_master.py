"""Build M_Melodia_Foliage_Master + palette MIs for the flower-field lane.

Run INSIDE the editor via Monolith editor_query(run_python, mode=execute_file):
    run_python execute_file Tools/build_foliage_master.py

Master contract:
- Masked, two-sided foliage surface.
- BaseColor * PerInstanceCustomData3Vector (default white) -> PCG can drive per-point colour.
- PetalTint / LeafTint vector params for palette instances.
- ChladniMask texture parameter (16-bit canonical mask) * ChladniStrength * PetalTint -> Emissive.
- Roughness / OpacityMask scalars.

Palette MIs (same folder, MI_Foliage_<Name>):
Rose, Peony, Lotus, Camellia, Lavender, Cream.

Writes Saved/Audit/PCG_FlowerField_20261029/foliage_master_receipt.json.
"""
import json
import os
import sys

import unreal

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUTDIR = os.path.join(ROOT, "Saved", "Audit", "PCG_FlowerField_20261029")
MASTER_DIR = "/Game/EnvSandbox/Materials/Masters"
MASTER_NAME = "M_Melodia_Foliage_Master"
MASTER_PATH = MASTER_DIR + "/" + MASTER_NAME

PALETTES = {
    "Rose":     {"BaseColor": [0.95, 0.42, 0.55, 1.0], "PetalTint": [1.0, 0.55, 0.65, 1.0], "LeafTint": [0.28, 0.45, 0.22, 1.0]},
    "Peony":    {"BaseColor": [0.98, 0.62, 0.72, 1.0], "PetalTint": [1.0, 0.75, 0.82, 1.0], "LeafTint": [0.24, 0.42, 0.20, 1.0]},
    "Lotus":    {"BaseColor": [0.99, 0.86, 0.80, 1.0], "PetalTint": [1.0, 0.92, 0.86, 1.0], "LeafTint": [0.22, 0.40, 0.24, 1.0]},
    "Camellia": {"BaseColor": [0.98, 0.30, 0.36, 1.0], "PetalTint": [1.0, 0.45, 0.48, 1.0], "LeafTint": [0.20, 0.38, 0.20, 1.0]},
    "Lavender": {"BaseColor": [0.62, 0.48, 0.92, 1.0], "PetalTint": [0.78, 0.68, 1.0, 1.0], "LeafTint": [0.26, 0.36, 0.24, 1.0]},
    "Cream":    {"BaseColor": [0.97, 0.93, 0.82, 1.0], "PetalTint": [1.0, 0.97, 0.88, 1.0], "LeafTint": [0.30, 0.44, 0.26, 1.0]},
}


def find_texture(*names):
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    for a in ar.get_assets_by_path('/Game', True, False):
        n = str(a.asset_name)
        if n in names and str(a.asset_class_path.asset_name) == 'Texture2D':
            return str(a.package_name)
    return None


def make_param(mel, m, cls, name, x, y, **props):
    e = mel.create_material_expression(m, cls, x, y)
    e.set_editor_property('parameter_name', name)
    for k, v in props.items():
        e.set_editor_property(k, v)
    return e


def main():
    mel = unreal.MaterialEditingLibrary
    at = unreal.AssetToolsHelpers.get_asset_tools()
    if unreal.EditorAssetLibrary.does_asset_exist(MASTER_PATH):
        m = unreal.load_asset(MASTER_PATH)
        repaired = True
    else:
        m = at.create_asset(MASTER_NAME, MASTER_DIR, unreal.Material, unreal.MaterialFactoryNew())
        repaired = False
    if m is None:
        print("MASTER_CREATE_FAILED")
        sys.exit(1)

    m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED)
    m.set_editor_property('two_sided', True)
    try:
        m.set_editor_property('opacity_mask_clip_value', 0.33)
    except Exception:
        pass

    base = make_param(mel, m, unreal.MaterialExpressionVectorParameter, 'BaseColor', -1000, -200,
                      default_value=unreal.LinearColor(0.95, 0.85, 0.9, 1.0))
    petal = make_param(mel, m, unreal.MaterialExpressionVectorParameter, 'PetalTint', -1000, 0,
                       default_value=unreal.LinearColor(1.0, 0.9, 0.95, 1.0))
    leaf = make_param(mel, m, unreal.MaterialExpressionVectorParameter, 'LeafTint', -1000, 200,
                      default_value=unreal.LinearColor(0.28, 0.45, 0.22, 1.0))
    rough = make_param(mel, m, unreal.MaterialExpressionScalarParameter, 'Roughness', -1000, 400,
                       default_value=0.55, slider_min=0.0, slider_max=1.0)
    opacity = make_param(mel, m, unreal.MaterialExpressionScalarParameter, 'OpacityMask', -1000, 600,
                         default_value=1.0, slider_min=0.0, slider_max=1.0)
    chladni_strength = make_param(mel, m, unreal.MaterialExpressionScalarParameter, 'ChladniStrength', -1000, 800,
                                  default_value=0.0, slider_min=0.0, slider_max=4.0)

    # Per-instance colour: default white so points without custom data stay lit.
    cid = mel.create_material_expression(m, unreal.MaterialExpressionPerInstanceCustomData3Vector, -800, -200)
    try:
        cid.set_editor_property('data_index', 0)
    except Exception as exc:
        print('CID_INDEX_NOTE', str(exc)[:80])
    try:
        cid.set_editor_property('default_value', unreal.LinearColor(1.0, 1.0, 1.0, 1.0))
    except Exception as exc:
        print('CID_DEFAULT_NOTE', str(exc)[:80])

    tint = mel.create_material_expression(m, unreal.MaterialExpressionMultiply, -600, -200)
    mel.connect_material_expressions(base, '', tint, 'A')
    mel.connect_material_expressions(cid, '', tint, 'B')

    # Chladni emissive (canonical 16-bit mask)
    chladni_path = find_texture('T_Chladni_16bit', 'T_Chladni_Mask', 'T_Cymatic_Chladni') or find_texture('T_Noise_White')
    chladni_tex = unreal.load_asset(chladni_path) if chladni_path else None
    emissive = None
    if chladni_tex is not None:
        uv = mel.create_material_expression(m, unreal.MaterialExpressionTextureCoordinate, -1200, 900)
        sample = mel.create_material_expression(m, unreal.MaterialExpressionTextureSampleParameter2D, -1000, 900)
        sample.set_editor_property('parameter_name', 'ChladniMask')
        sample.set_editor_property('texture', chladni_tex)
        mel.connect_material_expressions(uv, '', sample, 'UVs')
        emul = mel.create_material_expression(m, unreal.MaterialExpressionMultiply, -800, 900)
        mel.connect_material_expressions(sample, 'RGB', emul, 'A')
        mel.connect_material_expressions(chladni_strength, '', emul, 'B')
        emissive = mel.create_material_expression(m, unreal.MaterialExpressionMultiply, -600, 900)
        mel.connect_material_expressions(emul, '', emissive, 'A')
        mel.connect_material_expressions(petal, '', emissive, 'B')
        mel.connect_material_property(emissive, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)

    mel.connect_material_property(tint, '', unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(opacity, '', unreal.MaterialProperty.MP_OPACITY_MASK)

    try:
        receipt_compile = str(mel.recompile_material(m))
    except Exception as exc:
        receipt_compile = 'EXC ' + str(exc)[:100]
    saved = bool(unreal.EditorAssetLibrary.save_loaded_asset(m, False))

    receipt = {"schema": "melodia.foliage_master.v1", "when": "2026-10-29",
               "master": MASTER_PATH, "repaired": repaired, "saved": saved,
               "recompile": receipt_compile,
               "chladni_texture": chladni_path, "palettes": {}}
    for name, vals in PALETTES.items():
        mi_name = "MI_Foliage_" + name
        mi_path = MASTER_DIR + "/" + mi_name
        if unreal.EditorAssetLibrary.does_asset_exist(mi_path):
            mi = unreal.load_asset(mi_path)
        else:
            mi = at.create_asset(mi_name, MASTER_DIR, unreal.MaterialInstanceConstant,
                                 unreal.MaterialInstanceConstantFactoryNew())
        if mi is None:
            receipt["palettes"][name] = "CREATE_FAILED"
            continue
        mi.set_editor_property('parent', m)
        for pname, rgba in (('BaseColor', vals['BaseColor']), ('PetalTint', vals['PetalTint']), ('LeafTint', vals['LeafTint'])):
            mel.set_material_instance_vector_parameter_value(mi, pname, unreal.LinearColor(*rgba))
        receipt["palettes"][name] = bool(unreal.EditorAssetLibrary.save_loaded_asset(mi, False))

    os.makedirs(OUTDIR, exist_ok=True)
    out = os.path.join(OUTDIR, "foliage_master_receipt.json")
    with open(out, "w") as fh:
        json.dump(receipt, fh, indent=1)
    print("MASTER_SAVED", saved, "| recompile", receipt_compile)
    print("CHLADNI", chladni_path)
    print("PALETTES", receipt["palettes"])
    print("RECEIPT", out)


main()
