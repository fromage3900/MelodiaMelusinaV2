#!/usr/bin/env python3
"""
Brass Animated MI factory — creates 8 brass MIs with animated params.

Parent: M_Master_Toon_Universal (has DreamPulseSpeed, GlintSpeed, EmissiveMapIntensity, MPC binding)
Texture source: /Game/EnvSandbox/Textures/Copernicus/Brass<Variant>/T_Brass_<Variant>_<Channel>
               channel->slot: BaseColor->Albedo, Normal->NormalMap, ORM->ORM, Height->HeightMap,
                              Emissive->EmissiveMap, Iridescence->Iridescence, Opacity->OpacityMask
Scalar binding: BeatPulse-driven breathing via DreamPulseSpeed/GlintSpeed/EmissiveMapIntensity etc.
MPC: MPC_Melodia_Palette (BeatPulse, RhythmPulse, GlobalEmissiveBoost, GlobalSparkleIntensity)
All MIs also set panning params so brass scrolls without needing flipbook at runtime.

Run in-editor:
  exec(open(r"C:/EnvironmentPortfolio/BS_GodFile/Content/Python/_mi_brass_animated_create.py", encoding="utf-8").read())

Idempotent — skips existing MIs. Report -> Saved/Audit/brass_mi_create.json
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

PROJECT_ROOT = Path("C:/EnvironmentPortfolio/BS_GodFile")

# ── config ──────────────────────────────────────────────────────────
MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
SEA_MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"  # same for SeaAbove
COPERNICUS_DIR = "/Game/EnvSandbox/Materials/Instances/Copernicus"
SEA_DIR = "/Game/Melodia/SeaAbove/Materials"
TEX_COP_ROOT = "/Game/EnvSandbox/Textures/Copernicus"
TEX_SEA_ROOT = "/Game/Melodia/SeaAbove/Textures/Brass"
REPORT = PROJECT_ROOT / "Saved/Audit/brass_mi_create.json"

# 8 brass variants — must match copernicus_brass_animated.py BUILDERS keys
BRASS_VARIANTS = [
    ("PatinaAnimated",  "COPERNICUS_DIR"),  #-> MI_Brass_PatinaAnimated (in Copernicus)
    ("FiligreeGold",    "COPERNICUS_DIR"),
    ("Engraved",        "COPERNICUS_DIR"),
    ("Iridescent",      "COPERNICUS_DIR"),
    ("VerdigrisBloom",  "COPERNICUS_DIR"),
    ("HammeredPulse",   "COPERNICUS_DIR"),
    ("Nautilus",        "SEA_DIR"),       # Starskiff hull brass
    ("FarawayMother",   "SEA_DIR"),       # monumental Faraway Mother brass
]

CHANNEL_SLOTS = {
    "BaseColor":   "Albedo",
    "Normal":      "NormalMap",
    "ORM":         "ORM",
    "Height":      "HeightMap",
    "Emissive":    "EmissiveMap",
    "Iridescence": "Iridescence",
    "Opacity":     "OpacityMask",
}

# Brass-specific scalar defaults — animated panning + BeatPulse breathing
# These are MASTER param names that exist on M_Master_Toon_Universal.
BRASS_SCALARS = {
    # universal plumbing
    "TextureWeight": 1.0,
    "LayerA_TextureWeight": 1.0,
    "LayerBaseHeightScale": 0.08,
    "LayerA_ParallaxScale": 0.02,
    "NormalStrength": 1.0,
    "LayerA_NormalStrength": 1.0,
    "Roughness": 0.45,
    # breathing — MPC_Melodia_Palette.BeatPulse drives emissive via master
    "DreamPulseSpeed": 0.85,      # breathing speed (tied to BeatPulse in master)
    "DreamPulseAmp": 0.22,
    "BeatPulse": 0.0,              # placeholder — MPC drives at runtime
    "GlobalEmissiveBoost": 0.65,
    "GlobalSparkleIntensity": 0.35,
    # panning — brass flows
    "DreamFlowSpeed": 0.35,
    "DreamFlowScale": 1.0,
    "GlintSpeed": 0.45,
    "MistSpeed": 0.18,
    "WindSpeed": 0.12,
    "SigilSpeed": 0.22,
    "SparkleTwinkleSpeed": 0.9,
    "EmissiveMapIntensity": 1.35,
    "GoldEmissive": 1.0,
    "ImpastoStrength": 0.12,
}

BRASS_VARIANT_SCALARS = {
    "PatinaAnimated": {"DreamFlowSpeed": 0.35, "DreamPulseSpeed": 0.60, "GlintSpeed": 0.28, "EmissiveMapIntensity": 1.15, "Roughness": 0.52, "LayerA_ParallaxScale": 0.03},
    "FiligreeGold":    {"DreamFlowSpeed": 0.18, "DreamPulseSpeed": 0.45, "GlintSpeed": 0.60, "EmissiveMapIntensity": 1.50, "Roughness": 0.30, "GoldEmissive": 1.35},
    "Engraved":        {"DreamFlowSpeed": 0.30, "DreamPulseSpeed": 0.50, "GlintSpeed": 0.35, "EmissiveMapIntensity": 1.40, "Roughness": 0.48},
    "Iridescent":      {"DreamFlowSpeed": 0.60, "DreamPulseSpeed": 0.80, "GlintSpeed": 0.85, "EmissiveMapIntensity": 1.20, "Roughness": 0.22},
    "VerdigrisBloom":  {"DreamFlowSpeed": 0.25, "DreamPulseSpeed": 0.35, "GlintSpeed": 0.22, "EmissiveMapIntensity": 1.00, "Roughness": 0.62},
    "HammeredPulse":   {"DreamFlowSpeed": 0.00, "DreamPulseSpeed": 1.00, "GlintSpeed": 0.75, "EmissiveMapIntensity": 1.45, "Roughness": 0.38},
    "Nautilus":        {"DreamFlowSpeed": 0.40, "DreamPulseSpeed": 0.55, "GlintSpeed": 0.52, "EmissiveMapIntensity": 1.25, "Roughness": 0.32, "LayerA_ParallaxScale": 0.06},
    "FarawayMother":   {"DreamFlowSpeed": 0.15, "DreamPulseSpeed": 0.25, "GlintSpeed": 0.18, "EmissiveMapIntensity": 1.10, "Roughness": 0.68, "LayerBaseHeightScale": 0.12},
}

def tex_for(variant: str, channel: str, tex_root: str) -> str | None:
    stem = f"T_Brass_{variant}_{channel}"
    dir_path = f"{tex_root}/Brass{variant}"
    if not unreal.EditorAssetLibrary.does_directory_exist(dir_path):
        return None
    assets = unreal.EditorAssetLibrary.list_assets(dir_path, recursive=False)
    for a in assets:
        leaf = a.rsplit("/",1)[-1].split(".",1)[0]
        if leaf == stem:
            return a
    return None

def param_sets(master):
    out={"scalar":set(),"vector":set(),"texture":set(),"switch":set(),"bool":set()}
    if master is None: return out
    try:
        exprs = unreal.MaterialEditingLibrary.get_material_expressions(master)
    except Exception:
        return out
    for e in exprs or []:
        cls = type(e).__name__
        try: name = str(e.get_editor_property("parameter_name"))
        except Exception: continue
        if cls == "MaterialExpressionScalarParameter": out["scalar"].add(name)
        elif cls == "MaterialExpressionVectorParameter": out["vector"].add(name)
        elif cls == "MaterialExpressionStaticSwitchParameter": out["switch"].add(name)
        elif cls == "MaterialExpressionStaticBoolParameter": out["bool"].add(name)
        elif "Texture" in cls and "Parameter" in cls: out["texture"].add(name)
    return out

def ensure_mi(variant: str, dest: str, master, params) -> dict:
    # dest is key into dir map
    dest_dir = COPERNICUS_DIR if dest=="COPERNICUS_DIR" else SEA_DIR
    tex_root = TEX_COP_ROOT if dest=="COPERNICUS_DIR" else TEX_SEA_ROOT
    name = f"MI_Brass_{variant}"
    path = f"{dest_dir}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return {"variant":variant,"name":name,"path":path,"status":"exists"}
    try:
        inst = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, dest_dir, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    except Exception as e:
        return {"variant":variant,"name":name,"status":f"create_failed: {e}"}
    if inst is None:
        return {"variant":variant,"name":name,"status":"create_failed"}
    try: inst.set_editor_property("parent", master)
    except Exception: pass
    wired={}
    for channel, slot in CHANNEL_SLOTS.items():
        if slot not in params["texture"]:
            continue
        tex_path = tex_for(variant, channel, tex_root)
        if tex_path is None: continue
        obj = unreal.EditorAssetLibrary.load_asset(tex_path)
        if obj is None: continue
        try:
            unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(inst, slot, obj)
            wired[slot]=tex_path
        except Exception: pass
    # also wire shared panning noise as a secondary detail where available
    # try to wire T_Brass_PanningNoise into a known secondary slot if master exposes it
    for extra_slot in ("FabricWeaveTexture","DetailMap","MossTexture"):
        if extra_slot in params["texture"]:
            pn = f"{tex_root}/_BrassShared/T_Brass_PanningNoise"
            if unreal.EditorAssetLibrary.does_asset_exist(pn):
                obj = unreal.EditorAssetLibrary.load_asset(pn)
                if obj is not None:
                    try:
                        unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(inst, extra_slot, obj)
                        wired[extra_slot]=pn
                    except Exception: pass
    # scalars
    applied={}
    merged = dict(BRASS_SCALARS); merged.update(BRASS_VARIANT_SCALARS.get(variant, {}))
    for pname, val in merged.items():
        if pname not in params["scalar"]: continue
        try:
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(inst, pname, float(val))
            applied[pname]=val
        except Exception: pass
    # vector tint — subtle brass warmth
    for vname, vval in {"BaseTint": (1.02, 0.92, 0.72, 1.0), "GoldTint": (1.08, 0.88, 0.42, 1.0), "DreamTint": (1.05, 0.90, 0.60, 1.0)}.items():
        if vname in params["vector"]:
            try:
                col = unreal.LinearColor(*vval)  # type: ignore
                unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(inst, vname, col)  # type: ignore
            except Exception: pass
    # switch on
    for sw in ("bLayerA_Active","bUseTextureLayerA","bUseEmissiveMap"):
        if sw in params["switch"]:
            try: unreal.MaterialEditingLibrary.set_material_instance_static_switch_parameter_value(inst, sw, True)
            except Exception: pass
    try:
        unreal.EditorAssetLibrary.save_loaded_asset(inst, True)
        status="created"
    except Exception:
        status="created_save_failed"
    return {"variant":variant,"name":name,"path":path,"status":status,"textures":wired,"scalars":applied}

def main():
    master = unreal.EditorAssetLibrary.load_asset(MASTER)
    if master is None:
        print(f"[BRASS] ERROR master missing: {MASTER}")
        return 1
    params = param_sets(master)
    print(f"[BRASS] master {MASTER} -> scalars={len(params['scalar'])} tex={len(params['texture'])} switches={len(params['switch'])}")
    # ensure dirs
    for d in (COPERNICUS_DIR, SEA_DIR):
        if not unreal.EditorAssetLibrary.does_directory_exist(d):
            unreal.EditorAssetLibrary.make_directory(d)
    results=[]; counts={"created":0,"exists":0,"failed":0}
    for variant, dest in BRASS_VARIANTS:
        r = ensure_mi(variant, dest, master, params)
        results.append(r)
        st=r["status"]
        if st=="created": counts["created"]+=1
        elif st=="exists": counts["exists"]+=1
        else: counts["failed"]+=1
        print(f"[BRASS] {st:22s} {r['name']:30s} tex={len(r.get('textures',{}))} scalars={len(r.get('scalars',{}))}")
    report={"timestamp": datetime.now(timezone.utc).isoformat(), "master":MASTER, "dirs":{"copernicus":COPERNICUS_DIR,"sea":SEA_DIR},
            "master_params":{k:sorted(v) for k,v in params.items()}, "counts":counts, "results":results,
            "mpc":"/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette",
            "mpc_binding": {"BeatPulse":"Global breathing (DreamPulseSpeed*BeatPulse)", "RhythmPulse":"Hit flash (EmissiveMapIntensity)", "GlobalEmissiveBoost":"Master gain"},
            "animated_params": ["DreamFlowSpeed (panning)","DreamPulseSpeed (breathing)","GlintSpeed (sparkle drift)","EmissiveMapIntensity (pulse)","Roughness/Parallax live per variant"]}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"[BRASS] === {counts} === report -> {REPORT}")
    return 0 if counts["failed"]==0 else 1

if __name__ == "__main__":
    raise SystemExit(main())
