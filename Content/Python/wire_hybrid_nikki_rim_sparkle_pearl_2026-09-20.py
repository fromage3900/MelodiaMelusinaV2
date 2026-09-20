"""Wire MF_NikkiRimGlow + MF_NikkiSparkle + MF_NikkiPearlSheen into M_MelodiaPlant_Wind_NikkiToon.

Keeps SpeedTree WPO / SharedBend chain untouched. Color chain only:
  (existing BaseColor / DreamGrade) -> RimGlow -> Sparkle -> PearlSheen -> BaseColor out
Expose Nikki-group scalars; push hero defaults onto B0–B6.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
HYBRID = "/Game/EnvSandbox/Materials/Masters/M_MelodiaPlant_Wind_NikkiToon"
MF_RIM = "/Game/EnvSandbox/Materials/Functions/MF_NikkiRimGlow"
MF_SPARK = "/Game/EnvSandbox/Materials/Functions/MF_NikkiSparkle"
MF_PEARL = "/Game/EnvSandbox/Materials/Functions/MF_NikkiPearlSheen"
BAND_PREFIX = "/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowSpeedTree_"
BANDS = ["B0_Red", "B1_Orange", "B2_Gold", "B3_Green", "B4_Blue", "B5_Indigo", "B6_Violet"]

# Foliage-safe hero stills defaults
HERO = {
    "PastelLift": 0.42,
    "DreamSaturation": 0.38,
    "DreamContrast": -0.04,
    "DreamShadowLift": 0.18,
    "DreamIntensity": 0.78,
    "DreamWarmth": 0.12,
    "RimIntensity": 0.35,
    "RimWidth": 0.28,
    "RimPower": 4.2,
    "GlowIntensity": 0.12,
    "BloomBoost": 0.08,
    "SparkleIntensity": 0.18,
    "SparkleScale": 160.0,
    "SparkleThreshold": 0.50,
    "SparkleTwinkleSpeed": 0.3,
    "PearlSheen": 0.22,
    "Iridescence": 0.15,
    "IridescencePower": 3.0,
    "FabricSheen": 0.18,
}


def _ensure_scalar(m, name, default, x, y):
    names = [str(n) for n in MEL.get_scalar_parameter_names(m)]
    # find existing expression
    for e in MEL.get_material_expressions(m) or []:
        if "ScalarParameter" in e.get_class().get_name():
            try:
                if str(e.get_editor_property("parameter_name")) == name:
                    return e, False
            except Exception:
                pass
    p = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, x, y)
    p.set_editor_property("parameter_name", name)
    p.set_editor_property("default_value", float(default))
    try:
        p.set_editor_property("group", "Nikki")
    except Exception:
        pass
    return p, True


def _ensure_vector(m, name, rgba, x, y):
    for e in MEL.get_material_expressions(m) or []:
        if "VectorParameter" in e.get_class().get_name():
            try:
                if str(e.get_editor_property("parameter_name")) == name:
                    return e, False
            except Exception:
                pass
    p = MEL.create_material_expression(m, unreal.MaterialExpressionVectorParameter, x, y)
    p.set_editor_property("parameter_name", name)
    p.set_editor_property("default_value", unreal.LinearColor(*rgba))
    try:
        p.set_editor_property("group", "Nikki")
    except Exception:
        pass
    return p, True


def _mf_call(m, path, x, y):
    # reuse if already present
    for e in MEL.get_material_expressions(m) or []:
        if "FunctionCall" in e.get_class().get_name():
            try:
                fn = e.get_editor_property("material_function")
                if fn and path.split("/")[-1] in fn.get_path_name():
                    return e, False
            except Exception:
                pass
    mf = EAL.load_asset(path)
    if not mf:
        return None, False
    call = MEL.create_material_expression(m, unreal.MaterialExpressionMaterialFunctionCall, x, y)
    try:
        call.set_material_function(mf)
    except Exception:
        call.set_editor_property("material_function", mf)
    return call, True


def _connect(src, src_out, dst, dst_in, notes, tag):
    alts = dst_in if isinstance(dst_in, (list, tuple)) else [dst_in]
    for pin in alts:
        try:
            MEL.connect_material_expressions(src, src_out or "", dst, pin)
            notes.append(f"ok:{tag}->{pin}")
            return True
        except Exception:
            continue
    notes.append(f"fail:{tag}->{alts}")
    return False


def _find_param(m, name):
    for e in MEL.get_material_expressions(m) or []:
        cn = e.get_class().get_name()
        if "ScalarParameter" in cn or "VectorParameter" in cn:
            try:
                if str(e.get_editor_property("parameter_name")) == name:
                    return e
            except Exception:
                pass
    return None


def wire_hybrid():
    notes = []
    if not EAL.does_asset_exist(HYBRID):
        return {"ok": False, "error": "hybrid missing"}
    m = EAL.load_asset(HYBRID)

    # Ensure params
    created = []
    for name, default in (
        ("RimIntensity", 0.35), ("RimWidth", 0.28), ("RimPower", 4.2),
        ("GlowIntensity", 0.12), ("BloomBoost", 0.08),
        ("SparkleIntensity", 0.18), ("SparkleThreshold", 0.5),
        ("SparkleScale", 160.0), ("SparkleTwinkleSpeed", 0.3),
        ("PearlSheen", 0.22), ("Iridescence", 0.15), ("IridescencePower", 3.0),
        ("FabricSheen", 0.18),
        ("PastelLift", 0.42), ("DreamSaturation", 0.38), ("DreamContrast", -0.04),
        ("DreamShadowLift", 0.18), ("DreamIntensity", 0.78), ("DreamWarmth", 0.12),
    ):
        _, is_new = _ensure_scalar(m, name, default, -2600, 200 + 70 * len(created))
        if is_new:
            created.append(name)
    rim_col, rc_new = _ensure_vector(m, "RimColor", (0.95, 0.88, 1.0, 1.0), -2600, 1600)
    if rc_new:
        created.append("RimColor")
    spark_col, sc_new = _ensure_vector(m, "SparkleColor", (1.0, 0.95, 1.0, 1.0), -2600, 1720)
    if sc_new:
        created.append("SparkleColor")
    dream_tint, dt_new = _ensure_vector(m, "DreamTint", (1.0, 0.92, 0.98, 1.0), -2600, 1840)
    if dt_new:
        created.append("DreamTint")
    sheen_tint, st_new = _ensure_vector(m, "SheenTint", (0.9, 0.85, 1.0, 1.0), -2600, 1960)
    if st_new:
        created.append("SheenTint")
    irid_tint, it_new = _ensure_vector(m, "IridescenceTint", (0.7, 0.85, 1.0, 1.0), -2600, 2080)
    if it_new:
        created.append("IridescenceTint")

    # Current base color source
    base_node = None
    base_out = ""
    try:
        base_node = MEL.get_material_property_input_node(m, unreal.MaterialProperty.MP_BASE_COLOR)
        try:
            base_out = MEL.get_material_property_input_node_output_name(
                m, unreal.MaterialProperty.MP_BASE_COLOR) or ""
        except Exception:
            base_out = ""
        notes.append({"base_node": base_node.get_class().get_name() if base_node else None, "out": base_out})
    except Exception as e:
        notes.append(f"base_probe:{e}")

    # Prefer existing DreamGrade call as chain start if present
    dream_call = None
    for e in MEL.get_material_expressions(m) or []:
        if "FunctionCall" in e.get_class().get_name():
            try:
                fn = e.get_editor_property("material_function")
                if fn and "MF_NikkiDreamGrade" in fn.get_path_name():
                    dream_call = e
                    break
            except Exception:
                pass

    chain_in = dream_call if dream_call else base_node
    if chain_in is None:
        return {"ok": False, "error": "no base color to chain", "notes": notes}

    rim_call, rim_new = _mf_call(m, MF_RIM, -400, 200)
    spark_call, spark_new = _mf_call(m, MF_SPARK, -100, 200)
    pearl_call, pearl_new = _mf_call(m, MF_PEARL, 200, 200)
    notes.append({"rim_new": rim_new, "spark_new": spark_new, "pearl_new": pearl_new})

    # Rim
    if rim_call:
        _connect(chain_in, "" if dream_call else base_out, rim_call, ["BaseColor", "BaseColorIn"], notes, "rim_base")
        _connect(_find_param(m, "RimColor") or rim_col, "", rim_call, ["RimColor"], notes, "rim_col")
        for pname, pin in (
            ("RimIntensity", ["RimIntensity", "Intensity"]),
            ("RimWidth", ["RimWidth", "Width"]),
            ("RimPower", ["RimPower", "Power"]),
            ("GlowIntensity", ["GlowIntensity"]),
            ("BloomBoost", ["BloomBoost"]),
        ):
            p = _find_param(m, pname)
            if p:
                _connect(p, "", rim_call, pin, notes, pname)
        chain_in = rim_call

    # Sparkle (light)
    if spark_call:
        _connect(chain_in, "", spark_call, ["BaseColor", "BaseColorIn"], notes, "spark_base")
        for pname, pin in (
            ("SparkleIntensity", ["SparkleIntensity", "Intensity"]),
            ("SparkleThreshold", ["SparkleThreshold", "Threshold"]),
            ("SparkleScale", ["SparkleScale", "Scale"]),
            ("SparkleTwinkleSpeed", ["SparkleTwinkleSpeed", "TwinkleSpeed", "Speed"]),
        ):
            p = _find_param(m, pname)
            if p:
                _connect(p, "", spark_call, pin, notes, pname)
        sc = _find_param(m, "SparkleColor")
        if sc:
            _connect(sc, "", spark_call, ["SparkleColor", "Color"], notes, "SparkleColor")
        # UV optional — TexCoord
        try:
            uv = MEL.create_material_expression(m, unreal.MaterialExpressionTextureCoordinate, -100, 400)
            _connect(uv, "", spark_call, ["UV", "UVs"], notes, "spark_uv")
        except Exception as e:
            notes.append(f"uv:{e}")
        chain_in = spark_call

    # Pearl sheen
    if pearl_call:
        _connect(chain_in, "", pearl_call, ["BaseColor", "BaseColorIn"], notes, "pearl_base")
        for pname, pin in (
            ("PearlSheen", ["PearlSheen", "Sheen", "Amount", "Strength"]),
            ("Iridescence", ["Iridescence", "IridescenceAmount"]),
            ("IridescencePower", ["IridescencePower", "Power"]),
            ("FabricSheen", ["FabricSheen", "SheenAmount"]),
        ):
            p = _find_param(m, pname)
            if p:
                _connect(p, "", pearl_call, pin, notes, pname)
        for pname, pin in (
            ("SheenTint", ["SheenTint"]),
            ("IridescenceTint", ["IridescenceTint", "Tint"]),
        ):
            p = _find_param(m, pname)
            if p:
                _connect(p, "", pearl_call, pin, notes, pname)
        chain_in = pearl_call

    # Connect final to BaseColor (and soft add to Emissive for glow read on stills)
    try:
        MEL.connect_material_property(chain_in, "", unreal.MaterialProperty.MP_BASE_COLOR)
        notes.append("final->BaseColor")
    except Exception as e:
        try:
            MEL.connect_material_property(chain_in, "Result", unreal.MaterialProperty.MP_BASE_COLOR)
            notes.append("final Result->BaseColor")
        except Exception as e2:
            notes.append(f"final_base_fail:{e2}")

    # Soft emissive from chain * small GlowIntensity (optional beauty)
    try:
        glow = _find_param(m, "GlowIntensity")
        if glow and chain_in:
            mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, 400, 400)
            MEL.connect_material_expressions(chain_in, "", mul, "A")
            MEL.connect_material_expressions(glow, "", mul, "B")
            MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
            notes.append("glow*chain->Emissive")
    except Exception as e:
        notes.append(f"emissive:{e}")

    try:
        MEL.layout_material_expressions(m)
    except Exception:
        pass
    try:
        MEL.recompile_material(m)
        notes.append("recompiled")
    except Exception as e:
        notes.append(f"recompile:{e}")
    EAL.save_asset(HYBRID)

    sc = [str(n) for n in MEL.get_scalar_parameter_names(m)]
    return {
        "ok": True,
        "created_params": created,
        "notes": notes,
        "has_RimIntensity": "RimIntensity" in sc,
        "has_SparkleIntensity": "SparkleIntensity" in sc,
        "has_PearlSheen": "PearlSheen" in sc,
        "has_SharedBend": "SharedBend" in sc,
        "has_PastelLift": "PastelLift" in sc,
    }


def push_band_defaults():
    out = []
    for lab in BANDS:
        path = BAND_PREFIX + lab
        mi = EAL.load_asset(path)
        if not mi:
            out.append({"label": lab, "ok": False})
            continue
        names = set(str(n) for n in MEL.get_scalar_parameter_names(mi))
        wrote = {}
        for k, v in HERO.items():
            if k not in names:
                continue
            try:
                MEL.set_material_instance_scalar_parameter_value(mi, k, float(v))
                wrote[k] = float(v)
            except Exception as e:
                wrote[k] = f"ERR:{e}"
        # wind intact
        if "MelodiaWindResponse" in names:
            MEL.set_material_instance_scalar_parameter_value(mi, "MelodiaWindResponse", 0.45)
        # vectors
        for vname, rgba in (
            ("RimColor", (0.95, 0.88, 1.0, 1.0)),
            ("SparkleColor", (1.0, 0.95, 1.0, 1.0)),
            ("SheenTint", (0.9, 0.85, 1.0, 1.0)),
        ):
            try:
                MEL.set_material_instance_vector_parameter_value(
                    mi, vname, unreal.LinearColor(*rgba))
            except Exception:
                pass
        EAL.save_asset(path)
        out.append({
            "label": lab,
            "ok": True,
            "wrote_n": sum(1 for v in wrote.values() if not str(v).startswith("ERR")),
            "has_RimIntensity": "RimIntensity" in names or "RimIntensity" in wrote,
            "has_SparkleIntensity": "SparkleIntensity" in names or "SparkleIntensity" in wrote,
            "has_PearlSheen": "PearlSheen" in names or "PearlSheen" in wrote,
            "has_SharedBend": "SharedBend" in names,
        })
    return out


def main():
    hybrid = wire_hybrid()
    bands = push_band_defaults() if hybrid.get("ok") else []
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "hybrid": hybrid,
        "bands": bands,
        "skipped": ["MF_NikkiSquishWPO", "MF_NikkiSDFRibbon", "sticker MFs"],
        "wind": "Shared*/Branch*/Ripple*/MelodiaWind* untouched",
    }
    out = Path(unreal.Paths.project_dir()) / "Saved" / "Audit" / "hybrid_nikki_mf_wire_2026-09-20.json"
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    summary = {
        "hybrid_ok": hybrid.get("ok"),
        "has_rim_sparkle_pearl_wind": all([
            hybrid.get("has_RimIntensity"),
            hybrid.get("has_SparkleIntensity"),
            hybrid.get("has_PearlSheen"),
            hybrid.get("has_SharedBend"),
        ]),
        "bands_ok": sum(1 for b in bands if b.get("ok")),
        "b0": bands[0] if bands else None,
        "report": str(out),
        "created": hybrid.get("created_params"),
    }
    print("WIRE_NIKKI_MF " + json.dumps(summary, default=str))
    unreal.log("WIRE_NIKKI_MF " + json.dumps(summary, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
