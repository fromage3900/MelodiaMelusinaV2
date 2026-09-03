"""
Create enchanted vehicle material instances (MI_EnchantedVehicle_*) from the
saved spec (Saved/Audit/enchanted_vehicles_2026-08-30.json).

Editor-bound: run via Tools/editor_run.py (Monolith editor_query run_python) or
direct editor_query run_python. --dry-run inventories without creating/editing.

What it does (live editor only):
  1. Read the spec JSON (enchanted_vehicles_2026-08-30.json).
  2. Create category subfolders under Instances/Vehicles/Enchanted/ (Atlas/Shared/)
     if they don't exist.
  3. For each of the 75 effective stems:
     - Determine parent: Universal (opaque) or Alpha (has opacity/refraction).
     - Determine texture maps present on disk under Content/KitBash_EnchantedVehicles/.
     - Determine roughness + tile from the family/tile tables below.
     - Create MI_EnchantedVehicle_<StemStem>_R<RR>_Tile<Y>[.<Variant>].
     - Set parent (Universal or Alpha).
     - Route each present texture onto its Universal param (Albedo/NormalMap/ORM/
       HeightMap/MetallicMap/RoughnessMap/EmissiveColor), skipping params that don't
       exist on the master + skipping textures that don't exist on disk.
     - Set TextureWeight=1.0 + LayerA_TextureWeight=1.0.
     - Set ShadowDream params (strength 0.7, tint #8AA0D6, flower #E8A0BF,
       flower_strength 0.45, flower_scale 1.0).
     - Save the instance.
  4. Write Saved/Audit/enchanted_vehicles_conversion_run.json with per-stem result.

Spec stem naming: KB3D_ECV_<Stem>. Instance naming drops the KB3D_ECV_ prefix.
Roughness: R<RR> where RR = int(roughness*100) zero-padded 2 digits.
Tile: Tile4 (standard) / Tile2 (trim/small) / Tile6 (atlas) / Tile1 (unique).

Category assignment:
  - Atlas* stems + EmissiveTrim -> Atlas/ folder
  - Everything else -> Shared/ folder

Parent decision:
  - Stem has 'opacity' or 'refraction' in its texture map list -> Alpha
  - Otherwise -> Universal

Texture-to-param mapping (Universal):
  basecolor  -> Albedo
  normal     -> NormalMap
  metallic   -> MetallicMap
  roughness  -> RoughnessMap
  height     -> HeightMap
  ao         -> ORM
  emissive   -> EmissiveColor
  opacity    -> (Alpha master may handle via opacity; route if param exists)
  refraction -> (skip — no direct Universal/Alpha param; leave for custom node)

Textures live under: /Game/KitBash_EnchantedVehicles/<Stem>_<map>.uasset
(i.e. the same stem name + underscore + map name, as .uasset).

Roughness per family (from orchestration plan §5):
  Wood*       : R078
  Metal*      : R035  (non-gold)
  Gold*       : R028
  Fabric*     : R090
  Glass*      : R008
  Stone*/...  : R082  (BrickStone*, CobblestoneFloorB, ClayPotsTrimA, RopesTrimA,
                         SandStoneWorn, SlateDB, SoilGroundD, StoneGray, StoneGrayLight,
                         TrimLeatherWorn, CandleWax, FirewoodA, Ivy, LeatherWornA/TA,
                         LetterPaperA, PlasticCable, WallWeaveB, EmissiveTrim)
  CandleWax   : R060
  FirewoodA   : R080
  Ivy         : R085
  Leather*    : R070
  LetterPaperA: R085
  PlasticCable: R040
  WallWeaveB  : R075
  EmissiveTrim: R040

Tile per stem:
  Atlas* + EmissiveTrim : Tile6
  Glass* + PlasticCable : Tile2
  ClayPotsTrimA/RopesTrimA/TrimmLeatherWorn : Tile2
  All others : Tile4

Output: Saved/Audit/enchanted_vehicles_conversion_run.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# ---- only import unreal when running live (not dry-run planning) ----
if "--dry-run" not in sys.argv[1:]:
    import unreal

ROOT = Path(r"C:\EnvironmentPortfolio\BS_GodFile")
SPEC_PATH = ROOT / "Saved" / "Audit" / "enchanted_vehicles_2026-08-30.json"
OUT_PATH = ROOT / "Saved" / "Audit" / "enchanted_vehicles_conversion_run.json"

INST_ROOT = "/Game/EnvSandbox/Materials/Instances/Vehicles/Enchanted"
LOCAL_INST_DIR = ROOT / "Content" / "EnvSandbox" / "Materials" / "Instances" / "Vehicles" / "Enchanted"
MASTER_UNIVERSAL = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
MASTER_ALPHA = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal_Alpha"

TEX_ROOT = "/Game/KitBash_EnchantedVehicles"

# ============================================================
# Family -> roughness table (R-value * 100, zero-padded)
# ============================================================
ROUGH_BY_FAMILY = {
    "Wood":                ("Wood", 0.78),
    "Metal":               ("Metal", 0.35),
    "Gold":                ("Gold", 0.28),
    "Fabric":              ("Fabric", 0.90),
    "Glass":               ("Glass", 0.08),
    "Stone":               ("Stone", 0.82),
    "Brick":               ("Brick", 0.82),
    "Cobblestone":         ("Cobblestone", 0.82),
    "Clay":                ("Clay", 0.82),
    "Ropes":               ("Ropes", 0.82),
    "Sand":                ("Sand", 0.82),
    "Slate":               ("Slate", 0.82),
    "Soil":                ("Soil", 0.82),
    "Trim":                ("Trim", 0.82),
    "Candle":              ("Candle", 0.60),
    "Firewood":            ("Firewood", 0.80),
    "Ivy":                 ("Ivy", 0.85),
    "Leather":             ("Leather", 0.70),
    "Letter":              ("Letter", 0.85),
    "Plastic":             ("Plastic", 0.40),
    "WallWeave":           ("WallWeave", 0.75),
    "Emissive":            ("Emissive", 0.40),
    "Atlas":               ("Atlas", 0.82),
    "Bark":                ("Bark", 0.78),
    "Chipped":             ("Chipped", 0.78),
    "Heartwood":           ("Heartwood", 0.78),
    "Orange":              ("Orange", 0.78),
    "PBeige":              ("PBeige", 0.78),
    "PBlue":               ("PBlue", 0.78),
    "PGreen":              ("PGreen", 0.78),
    "PRed":                ("PRed", 0.78),
    "Paint":               ("Paint", 0.78),
    "Painted":             ("Painted", 0.78),
    "Plank":               ("Plank", 0.78),
    "White":               ("White", 0.78),
}

# ============================================================
# Family -> tile
# ============================================================
TILE_BY_FAMILY = {
    "Atlas":       "Tile6",
    "Emissive":    "Tile6",
    "Glass":       "Tile2",
    "Plastic":     "Tile2",
    "ClayPots":    "Tile2",
    "Ropes":       "Tile2",
    "TrimLeather": "Tile2",
}
TILE_DEFAULT = "Tile4"

# ============================================================
# Texture map -> Universal param name
# ============================================================
MAP_TO_PARAM = {
    "basecolor":   "Albedo",
    "normal":      "NormalMap",
    "metallic":    "MetallicMap",
    "roughness":   "RoughnessMap",
    "height":      "HeightMap",
    "ao":          "ORM",
    "emissive":    "EmissiveColor",
    "opacity":     "Opacity",
}

# ============================================================
# Per-stem: which maps it HAS (as listed in the spec JSON)
# ============================================================

def _spec_stem_maps(spec: dict, stem: str) -> list[str]:
    return list(spec.get("stems", {}).get(stem, []))

def _stem_family_from_name(stem: str) -> str:
    """Heuristic: pull the leading family token from the stem name after KB3D_ECV_."""
    inner = stem
    if inner.startswith("KB3D_ECV_"):
        inner = inner[len("KB3D_ECV_"):]
    # split on first underscore or capital-letter boundary
    parts = []
    buf = []
    for ch in inner:
        if ch.isupper() and buf:
            parts.append("".join(buf))
            buf = [ch]
        else:
            buf.append(ch)
    if buf:
        parts.append("".join(buf))
    if not parts:
        return "UNKNOWN"
    # try to match against ROUGH_BY_FAMILY keys (longest match first)
    for p in sorted(parts, key=len, reverse=True):
        for fam in ROUGH_BY_FAMILY:
            if fam.lower() == p.lower():
                return fam
    # fallback: first token
    return parts[0] if parts else "UNKNOWN"

def _roughness_for_stem(stem: str) -> float:
    fam = _stem_family_from_name(stem)
    for key, (label, val) in ROUGH_BY_FAMILY.items():
        if key.lower() == fam.lower():
            return val
    return 0.82  # stone default

def _tile_for_stem(stem: str) -> str:
    fam = _stem_family_from_name(stem)
    for key, tile in TILE_BY_FAMILY.items():
        if key.lower() == fam.lower():
            return tile
    return TILE_DEFAULT

def _parent_for_maps(maps: list[str]) -> str:
    has_opacity_or_refraction = any(m in ("opacity", "refraction") for m in maps)
    return MASTER_ALPHA if has_opacity_or_refraction else MASTER_UNIVERSAL

def _parent_label(parent_path: str) -> str:
    if parent_path == MASTER_ALPHA:
        return "Alpha"
    return "Universal"

def _instance_name(stem: str, roughness: float, tile: str, maps: list[str]) -> str:
    inner = stem
    if inner.startswith("KB3D_ECV_"):
        inner = inner[len("KB3D_ECV_"):]
    # R<RR>
    rr = int(round(roughness * 100))
    rr_s = f"R{rr:02d}"
    # variant suffix
    variants = []
    if "opacity" in maps:
        variants.append("Translucent")
    if "emissive" in maps:
        variants.append("Emissive")
    if "refraction" in maps:
        variants.append("Refraction")
    variant_s = "".join(f"_{v}" for v in variants) if variants else ""
    return f"MI_EnchantedVehicle_{inner}_{rr_s}_{tile}{variant_s}"

def _stem_exists_on_disk(stem: str) -> bool:
    """Check whether any texture for this stem exists on disk under KitBash_EnchantedVehicles."""
    # stem maps are like <Stem>_<map>.uasset
    for m in ("basecolor", "height", "metallic", "normal", "roughness", "ao", "emissive", "opacity", "refraction"):
        p = f"{TEX_ROOT}/{stem}_{m}.uasset"
        try:
            import unreal
            if unreal.EditorAssetLibrary.do_asset_exist(p):
                return True
        except Exception:
            pass
    # also check the raw on-disk path via pathlib
    tex_dir = ROOT / "Content" / "KitBash_EnchantedVehicles"
    if tex_dir.exists():
        for m in ("basecolor", "height", "metallic", "normal", "roughness"):
            if list(tex_dir.glob(f"{stem}_{m}.uasset")):
                return True
    return False

def _texture_path_for_map(stem: str, map_name: str) -> str:
    return f"{TEX_ROOT}/{stem}_{map_name}.uasset"

def _does_tex_exist(stem: str, map_name: str) -> bool:
    p = _texture_path_for_map(stem, map_name)
    try:
        import unreal
        return unreal.EditorAssetLibrary.do_asset_exist(p)
    except Exception:
        path_obj = ROOT / "Content" / "KitBash_EnchantedVehicles" / f"{stem}_{map_name}.uasset"
        return path_obj.exists()
    return False

def _ensure_category_dir(cat: str):
    path = f"{INST_ROOT}/{cat}"
    try:
        import unreal
        unreal.EditorAssetLibrary.make_directory(path)
    except Exception:
        pass
    # also ensure on-disk copy
    d = LOCAL_INST_DIR / cat
    d.mkdir(parents=True, exist_ok=True)

def _load(path: str):
    try:
        return unreal.EditorAssetLibrary.load_asset(path)
    except Exception:
        return None

def _create_mi(parent_path: str, inst_path: str):
    try:
        factory = unreal.MaterialInstanceConstantFactoryNew()
        name = Path(inst_path).stem
        folder = str(Path(inst_path).parent)
        mi = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, folder,
            unreal.MaterialInstanceConstant, factory)
        if mi is None:
            return None
        parent = _load(parent_path)
        if parent is not None:
            mi.set_editor_property("parent", parent)
        return mi
    except Exception:
        return None

def _route_map(mi, param: str, tex_path: str) -> bool:
    tex = _load(tex_path)
    if tex is None:
        return False
    try:
        unreal.MaterialEditingLibrary.set_mic_texture_param_value(mi, param, tex)
        return True
    except Exception:
        return False

def _set_scalar(mi, name: str, value: float) -> bool:
    try:
        unreal.MaterialEditingLibrary.set_mic_scalar_param_value(mi, name, value)
        return True
    except Exception:
        return False

def _set_vector(mi, name: str, r: float, g: float, b: float, a: float = 1.0) -> bool:
    try:
        unreal.MaterialEditingLibrary.set_mic_vec_param_value(
            mi, name, unreal.LinearColor(r, g, b, a))
        return True
    except Exception:
        return False

def _apply_shadawdream(mi) -> dict:
    out = {}
    out["ShadowDreamStrength"] = _set_scalar(mi, "ShadowDreamStrength", 0.7)
    out["ShadowDreamTint"] = _set_vector(mi, "ShadowDreamTint", 0.541, 0.627, 0.839, 1.0)
    out["ShadowFlowerColor"] = _set_vector(mi, "ShadowFlowerColor", 0.910, 0.627, 0.749, 1.0)
    out["ShadowFlowerStrength"] = _set_scalar(mi, "ShadowFlowerStrength", 0.45)
    out["ShadowFlowerScale"] = _set_scalar(mi, "ShadowFlowerScale", 1.0)
    return out

def _apply_weights(mi) -> dict:
    out = {}
    out["TextureWeight"] = _set_scalar(mi, "TextureWeight", 1.0)
    out["LayerA_TextureWeight"] = _set_scalar(mi, "LayerA_TextureWeight", 1.0)
    return out

def convert_one_stem(stem: str, maps: list[str], dry_run: bool) -> dict:
    roughness = _roughness_for_stem(stem)
    tile = _tile_for_stem(stem)
    parent_path = _parent_for_maps(maps)
    parent_label = _parent_label(parent_path)
    inner = stem
    if inner.startswith("KB3D_ECV_"):
        inner = inner[len("KB3D_ECV_"):]
    cat = "Atlas" if any(inner.startswith(a) for a in ("Atlas", "Emissive")) else "Shared"
    inst_name = _instance_name(stem, roughness, tile, maps)
    inst_path = f"{INST_ROOT}/{cat}/{inst_name}"

    result = {
        "stem": stem,
        "maps": maps,
        "roughness": roughness,
        "tile": tile,
        "parent": parent_label,
        "category": cat,
        "instance_name": inst_name,
        "instance_path": inst_path,
        "changes": [],
        "status": "ok" if not dry_run else "dry_run",
    }

    # texture existence check
    missing = [m for m in maps if not _does_tex_exist(stem, m)]
    result["missing_textures_on_disk"] = missing
    result["textures_present_count"] = len(maps) - len(missing)

    if dry_run:
        result["changes"] = [
            f"WOULD create {inst_name} under {cat}/",
            f"WOULD parent to {parent_label}",
            f"WOULD route {len(maps) - len(missing)}/{len(maps)} textures",
            f"WOULD set TextureWeight=1.0 + LayerA_TextureWeight=1.0",
            "WOULD set ShadowDream params",
        ]
        return result

    # create
    _ensure_category_dir(cat)
    if _does_exist(inst_path):
        result["status"] = "exists_skip"
        result["changes"] = ["instance already exists — skipped"]
        return result

    mi = _create_mi(parent_path, inst_path)
    if mi is None:
        result["status"] = "create_failed"
        result["changes"] = ["failed to create MI"]
        return result
    result["changes"].append(f"created {inst_name}")

    # parent already set by create_mi; re-confirm
    try:
        cur = mi.get_editor_property("parent")
        result["parent_on_disk"] = cur.get_path_name() if cur else "<NONE>"
    except Exception:
        pass

    # route textures
    routed = []
    for m in maps:
        if m in missing:
            continue
        param = MAP_TO_PARAM.get(m)
        if param is None:
            continue
        # skip refraction (no direct Universal/Alpha param)
        if m == "refraction":
            result["changes"].append("skipped refraction (no direct param)")
            continue
        ok = _route_map(mi, param, _texture_path_for_map(stem, m))
        if ok:
            routed.append(m)
            result["changes"].append(f"routed {m} -> {param}")
        else:
            result["changes"].append(f"FAILED route {m} -> {param}")
    result["routed_count"] = len(routed)

    # weights
    w = _apply_weights(mi)
    if w["TextureWeight"]:
        result["changes"].append("TextureWeight=1.0")
    if w["LayerA_TextureWeight"]:
        result["changes"].append("LayerA_TextureWeight=1.0")

    # shadawdream
    sd = _apply_shadawdream(mi)
    result["shadawdream"] = {k: ("set" if v else "FAIL") for k, v in sd.items()}
    result["changes"].append("ShadowDream params set")

    # save
    try:
        unreal.EditorAssetLibrary.save_loaded_asset(mi, only_if_is_dirty=False)
        result["changes"].append("saved")
        result["saved"] = True
    except Exception as e:
        result["changes"].append(f"save FAIL: {e}")
        result["saved"] = False

    return result

def _does_exist(path: str) -> bool:
    try:
        import unreal
        return unreal.EditorAssetLibrary.do_asset_exist(path)
    except Exception:
        return (ROOT / "Content" / "EnvSandbox" / "Materials" / "Instances" / "Vehicles" / "Enchanted" /
                Path(path).relative_to("/Game")).exists()

def main() -> int:
    dry = "--dry-run" in sys.argv[1:]
    spec = {}
    if SPEC_PATH.exists():
        try:
            spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[warn] could not read spec: {e}")
    stems = spec.get("stems", {})
    if not stems:
        # fallback: re-read stems from the known list
        stems = _fallback_stems()

    results = []
    for stem, maps in stems.items():
        r = convert_one_stem(stem, list(maps), dry)
        results.append(r)
        print(f"{'DRY' if dry else 'OK '}| {r['stem']:32s} -> {r['instance_name']} [{r['status']}]")

    summary = {
        "generated": "2026-09-01",
        "dry_run": dry,
        "stems_processed": len(results),
        "by_status": {},
        "by_parent": {"Universal": 0, "Alpha": 0},
        "total_missing_textures": sum(len(r.get("missing_textures_on_disk", [])) for r in results),
        "results": results,
    }
    for r in results:
        summary["by_status"][r["status"]] = summary["by_status"].get(r["status"], 0) + 1
        summary["by_parent"][r["parent"]] = summary["by_parent"].get(r["parent"], 0) + 1

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps(summary["by_status"], indent=2))
    return 0

def _fallback_stems() -> dict:
    """Hard-coded list of the 75 stems + their maps (mirror of spec JSON) so the
    script can run even if the spec JSON is missing."""
    return {
        "KB3D_ECV_AtlasFlowersA": ["basecolor","height","metallic","normal","opacity","roughness"],
        "KB3D_ECV_AtlasFoodA": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_AtlasFruitsB": ["basecolor","emissive","height","metallic","normal","opacity","roughness"],
        "KB3D_ECV_AtlasGraphicsA": ["basecolor","emissive","height","metallic","normal","opacity","roughness"],
        "KB3D_ECV_AtlasGraphicsB": ["basecolor","height","metallic","normal","opacity","roughness"],
        "KB3D_ECV_AtlasLeafA": ["basecolor","height","metallic","normal","opacity","roughness"],
        "KB3D_ECV_AtlasLeafB": ["basecolor","height","metallic","normal","opacity","roughness"],
        "KB3D_ECV_AtlasLeafC": ["basecolor","height","metallic","normal","opacity","roughness"],
        "KB3D_ECV_BoxwoodBranch": ["basecolor","height","metallic","normal","opacity","roughness"],
        "KB3D_ECV_BrickStoneGray": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_BrickStoneWarmBTop": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_CandleWax": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_ClayPotsTrimA": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_CobblestoneFloorB": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_Copper": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_EmissiveTrim": ["basecolor","emissive","height","metallic","normal","roughness"],
        "KB3D_ECV_FabricB": ["basecolor","height","metallic","normal","opacity","roughness"],
        "KB3D_ECV_FabricOldBright": ["basecolor","height","metallic","normal","opacity","roughness"],
        "KB3D_ECV_FabricPatternA": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_FabricPatternBlue": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_FabricPatternRed": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_FabricTentPink": ["basecolor","height","metallic","normal","opacity","roughness"],
        "KB3D_ECV_FabricTentRed": ["basecolor","height","metallic","normal","opacity","roughness"],
        "KB3D_ECV_FabricVelvetBlueA": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_FabricVelvetPurpleA": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_FabricVelvetWhite": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_FabricWhiteWorn": ["basecolor","height","metallic","normal","opacity","roughness"],
        "KB3D_ECV_FirewoodA": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_GlassClean": ["basecolor","height","metallic","normal","refraction","roughness"],
        "KB3D_ECV_GlassClean_refraction": ["inverted"],
        "KB3D_ECV_GlassDirty": ["basecolor","height","metallic","normal","refraction","roughness"],
        "KB3D_ECV_GlassDirty_refraction": ["inverted"],
        "KB3D_ECV_GoldCleanA": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_GoldCleanDark": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_GoldDirtyA": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_GoldTrimB": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_Ivy": ["basecolor","height","normal","opacity","roughness"],
        "KB3D_ECV_LeatherWornA": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_LeatherWornTA": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_LetterPaperA": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_MetalCleaner": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_MetalForgedBlackRustedA": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_MetalForgedGrayA": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_MetalForgedGrayB": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_MetalPBlueWorn": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_MetalPWhite": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_PlasticCable": ["basecolor","height","normal","refraction","roughness"],
        "KB3D_ECV_PlasticCable_refraction": ["inverted"],
        "KB3D_ECV_PlasterYellow": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_RopesTrimA": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_SandStoneWorn": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_SlateDB": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_SoilGroundD": ["basecolor","height","normal","roughness"],
        "KB3D_ECV_StoneGray": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_StoneGrayLight": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_TrimLeatherWorn": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_WallWeaveB": ["basecolor","height","normal","roughness"],
        "KB3D_ECV_WoodBarkMoss": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_WoodBarkPineWorn": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_WoodChipped": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_WoodHeartwoodAtlas": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_WoodOldWornBrightA": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_WoodOldWornBrownA": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_WoodOldWornBrownB": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_WoodOldWornBrownBDamaged": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_WoodOldWornGrayA": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_WoodOrangePolished": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_WoodPBeigeWorn": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_WoodPBlueWorn": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_WoodPGreenWorn": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_WoodPRedWorn": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_WoodPaintTrim": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_WoodPaintedGoldMetallic": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_WoodPlankA": ["basecolor","height","metallic","normal","roughness"],
        "KB3D_ECV_WoodWhiteCarriage": ["basecolor","height","metallic","normal","roughness"],
    }

if __name__ == "__main__":
    sys.exit(main())
