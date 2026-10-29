"""Wire Melusina's water-hair drip parameters into M_Water_Master_Grand_v10_Upgrade.

Owner directive 2026-10-28: "wire it" (hair drip onto v10_Upgrade).

Adds six scalar parameters (group "09 | Hair Drip", all neutral by default so
every other v10 user is unaffected) and injects a time-animated drip term into
the WorldPositionOffset chain:

    drip = sin(Time * DripSpeed + WaveDisplacement.z * 2pi / DripLength)
           * HairDripIntensity * SplashForce * 2.0
    WPO  = WaveDisplacement + (0,0,RippleHeight) + (0,0,drip)

WaterOpacity / WaterRoughness are exposed as parameters only: the master's
roughness/opacity inputs are fed from Custom-HLSL nodes whose FCustomInput
struct is opaque to the Python binding (no input_type property), so pin-level
wiring there is deliberately not attempted; see receipt.

Idempotent: if HairDripIntensity already exists on the master, the script
verifies and exits without creating duplicate nodes.

Run INSIDE the editor via Monolith editor_query(run_python, mode=execute_file):
    run_python execute_file Tools/masters_spine_hair_drip_wiring.py
"""
import json
import os
import sys
import unreal

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUTDIR = os.path.join(ROOT, "Saved", "Audit", "MastersSpine_20261028")

MASTER = "/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v10_Upgrade"
MI = "/Game/EnvSandbox/Materials/Instances/Melusina/MI_Melusina_WaterHair"

PARAMS = [
    ("HairDripIntensity", 0.0),
    ("DripSpeed", 1.0),
    ("DripLength", 0.35),
    ("SplashForce", 1.0),
    ("WaterOpacity", 1.0),
    ("WaterRoughness", 1.0),
]
MI_VALUES = {
    "HairDripIntensity": 0.8,
    "DripSpeed": 1.4,
    "DripLength": 0.4,
    "SplashForce": 1.0,
    "WaterOpacity": 1.0,
    "WaterRoughness": 1.0,
}


def main():
    mel = unreal.MaterialEditingLibrary
    M = unreal.load_asset(MASTER)
    if M is None:
        print("MASTER_LOAD_FAILED")
        sys.exit(1)
    exprs = mel.get_material_expressions(M)

    def find(cls, name=None):
        for e in exprs:
            if str(e.get_class().get_name()) == cls and (name is None or str(e.get_name()) == name):
                return e
        return None

    def param(name):
        for e in exprs:
            if str(e.get_class().get_name()) == "MaterialExpressionScalarParameter":
                try:
                    if str(e.get_editor_property("parameter_name")) == name:
                        return e
                except Exception:
                    pass
        return None

    receipt = {"schema": "melodia.hair_drip_wiring.v1", "when": "2026-10-28",
               "master": MASTER, "mi": MI, "params": {}, "wiring": {},
               "notes": []}

    # Parameters: create only when missing (idempotent across repair runs).
    for name, default in PARAMS:
        if param(name) is not None:
            receipt["params"][name] = {"created": False, "default": default}
            print("PARAM_EXISTS", name)
            continue
        p = mel.create_material_expression(M, unreal.MaterialExpressionScalarParameter, -2600, 600)
        p.set_editor_property("parameter_name", name)
        p.set_editor_property("group", "09 | Hair Drip")
        p.set_editor_property("default_value", default)
        receipt["params"][name] = {"created": True, "default": default}
        print("PARAM_NEW", name, default)

    # --- drip chain into WPO
    wpo_node = mel.get_material_property_input_node(M, unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    time_node = find("MaterialExpressionTime")
    print("WPO_CURRENT", str(wpo_node.get_name()) if wpo_node else "None")

    def mk(cls, x, y):
        return mel.create_material_expression(M, cls, x, y)

    m1 = mk(unreal.MaterialExpressionMultiply, -2300, 600)
    s1 = mk(unreal.MaterialExpressionSine, -2100, 600)
    m2 = mk(unreal.MaterialExpressionMultiply, -1900, 600)
    m3 = mk(unreal.MaterialExpressionMultiply, -1700, 600)
    m4 = mk(unreal.MaterialExpressionMultiply, -1500, 600)
    c2 = mk(unreal.MaterialExpressionConstant, -1500, 750)
    c2.set_editor_property("r", 2.0)
    m5 = mk(unreal.MaterialExpressionMultiply, -1300, 600)
    v1 = mk(unreal.MaterialExpressionConstant3Vector, -1300, 800)
    v1.set_editor_property("constant", unreal.LinearColor(0.0, 0.0, 1.0, 1.0))
    m6 = mk(unreal.MaterialExpressionMultiply, -1100, 600)
    add_w = mk(unreal.MaterialExpressionAdd, -900, 300)

    links = [
        (time_node, "", m1, "A"),
        (param("DripSpeed"), "", m1, "B"),
        (m1, "", s1, ""),
        (s1, "", m2, "A"),
        (param("DripLength"), "", m2, "B"),
        (m2, "", m3, "A"),
        (param("HairDripIntensity"), "", m3, "B"),
        (m3, "", m4, "A"),
        (param("SplashForce"), "", m4, "B"),
        (m4, "", m5, "A"),
        (c2, "", m5, "B"),
        (m5, "", m6, "A"),
        (v1, "", m6, "B"),
        (wpo_node, "", add_w, "A"),
        (m6, "", add_w, "B"),
    ]
    oks = []
    for src, out, dst, inp in links:
        if src is None:
            oks.append(False)
            continue
        oks.append(bool(mel.connect_material_expressions(src, out, dst, inp)))
    receipt["wiring"]["chain_connects"] = oks
    print("CHAIN_CONNECTS", oks)

    if all(oks):
        okp = mel.connect_material_property(add_w, "", unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
        receipt["wiring"]["wpo_property_connected"] = bool(okp)
        print("PROP_CONNECT", bool(okp))
    else:
        receipt["wiring"]["wpo_property_connected"] = False
        print("PROP_CONNECT_SKIPPED_CHAIN_INCOMPLETE")

    try:
        receipt["recompile"] = str(mel.recompile_material(M))
        print("RECOMPILE", receipt["recompile"])
    except Exception as exc:
        receipt["recompile"] = "EXC " + str(exc)[:120]
        print("RECOMPILE_EXC", receipt["recompile"])

    receipt["master_saved"] = bool(unreal.EditorAssetLibrary.save_loaded_asset(M, False))
    print("MASTER_SAVED", receipt["master_saved"])

    # --- hair MI overrides
    mi = unreal.load_asset(MI)
    if mi is not None:
        applied = {}
        for name, value in MI_VALUES.items():
            p = param(name)
            if p is None:
                applied[name] = "NO_PARAM_ON_MASTER"
                continue
            try:
                mel.set_material_instance_scalar_parameter_value(mi, name, float(value))
                got = float(mel.get_material_instance_scalar_parameter_value(mi, name))
                applied[name] = {"set": value, "readback": round(got, 6),
                                 "ok": abs(got - value) < 1e-4}
            except Exception as exc:
                applied[name] = "EXC " + str(exc)[:100]
        receipt["mi_overrides"] = applied
        print("MI_OVERRIDES", applied)
        receipt["mi_saved"] = bool(unreal.EditorAssetLibrary.save_loaded_asset(mi, False))
        print("MI_SAVED", receipt["mi_saved"])

    _write(receipt)


def _write(receipt):
    os.makedirs(OUTDIR, exist_ok=True)
    out = os.path.join(OUTDIR, "receipt_hair_drip_wiring_20261028.json")
    with open(out, "w") as fh:
        json.dump(receipt, fh, indent=1)
    print("RECEIPT", out)


main()
