"""add_nikki_params_to_magicians.py

Give the 50 converted Magicians masters a Nikki-hero parameter layer and
create one richly-tinted MI per master.

Why: every M_<prop> in the migrated MagiciansLibrary is a flat 3-4 expression
graph (2-3 TextureSamples -> SubstrateToonBSDF) with ZERO parameters. An MI
parented to it would have nothing to override. The owner asked for "nikki hero
parameters" — the established vocabulary in this project is
BaseTint + TintStrength (see mi_preview_studio.NIKKI_HERO_BASE_TINTS).

Injection (per master, additive, reversible):
  1. Find the expression chain feeding the Toon BSDF's color input.
  2. Disconnect it from the BSDF.
  3. Insert LinearInterpolate(
       A = original color,
       B = VectorParameter "BaseTint"   (default white, group "Nikki"),
       Alpha = ScalarParameter "TintStrength" (default 0.0 -> master look unchanged))
     wired to the BSDF's color pin.
  4. Recompile + save.

MI creation:
  MI_<stem> next to M_<stem> in the same subfolder (mirrors the /Game/Library
  naming convention, but parented to the EnvSandbox converted master), with
  toon_profile + BaseTint + TintStrength set per prop family:
    * WOOD/FURNITURE -> TP_Default, warm pastel oak/cream
    * CARPET         -> TP_Default, sage/lavender pastel
    * GOLD/BRASS     -> TP_Gold, soft gold/peach
    * GLASS          -> TP_Default, pearl/aqua pastel
  Deterministic per stem via md5 of the stem (stable re-runs).

Reports: Saved/Audit/magicians_nikki.json
Run (one editor, serialized): Monolith editor_query run_python -> this file
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import unreal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "magicians_nikki.json"

BASE = "/Game/EnvSandbox/Library/Migrated/MagiciansLibrary"
PROFILE_DIR = "/Game/EnvSandbox/Materials/ToonProfiles"

FOLDER_BY_STEM = {
    "M_Bookshelf": "Bookshelf", "M_Box": "Box", "M_Candle": "Candle",
    "M_Carpet": "Carpet", "M_Carpet2": "Carpet2", "M_Carpet3": "Carpet3",
    "M_Deco1": "Deco1", "M_Deco2": "Deco2", "M_Deco3": "Deco3",
    "M_Deco4": "Deco4", "M_Deco5": "Deco5", "M_Deco6": "Deco6", "M_Deco7": "Deco7",
    "M_Desk": "Desk", "M_Desk_2": "Desk2", "M_Desk3": "Desk3", "M_Desk4": "Desk4",
    "M_Desk_Drawer": "DeskDrawer", "M_Drawer_Box002": "Drawer",
    "M_Entrance": "Entrance", "M_Flag": "Flag",
    "M_GlassBottle_Object1715": "GlassBottle", "M_GlassBottle2": "GlassBottle2",
    "M_GlassBottle3": "GlassBottle3", "M_GlassBottle4": "GlassBottle4",
    "M_GlassBottle5": "GlassBottle5", "M_GlassBottle6": "GlassBottle6",
    "M_Globe": "Globe", "M_Globe2": "Globe2",
    "M_HallDeco": "HallDeco", "M_Hallpillar": "Hallpillar",
    "M_Hallwall": "Hallwall", "M_HallwallGlass": "HallwallGlass",
    "M_HallwallGlassBar": "HallwallGlassBar",
    "M_Lantern": "Lantern", "M_LanternGlass": "LanternGlass",
    "M_Microscope": "Microscope", "M_Platform": "Platform",
    "M_Polygon": "Polygon", "M_Polygon2": "Polygon2",
    "M_Pot_Table": "PotTable",
    "M_Shelf": "Shelf", "M_Shelf6": "Shelf6",
    "M_Shelf_2": "Shelf_2", "M_Shelf_3": "Shelf_3", "M_Shelf_4": "Shelf_4",
    "M_Shelf_5": "Shelf_5", "M_Shelf_Prop": "Shelf_Prop",
    "M_Wall_Lamp": "WallLamp", "M_Wall_Lamp_Glass": "WallLampGlass",
}

ALL_STEMS = list(FOLDER_BY_STEM.keys())

WOOD = {"M_Bookshelf", "M_Box", "M_Desk", "M_Desk_2", "M_Desk3", "M_Desk4",
        "M_Desk_Drawer", "M_Drawer_Box002", "M_Entrance", "M_Platform",
        "M_Pot_Table", "M_Polygon", "M_Polygon2",
        "M_Shelf", "M_Shelf6", "M_Shelf_2", "M_Shelf_3", "M_Shelf_4",
        "M_Shelf_5", "M_Shelf_Prop", "M_Hallwall", "M_Hallpillar",
        "M_HallDeco", "M_HallwallGlassBar"}
CARPET = {"M_Carpet", "M_Carpet2", "M_Carpet3"}
GOLD = {"M_Lantern", "M_Wall_Lamp", "M_Globe", "M_Globe2", "M_Microscope",
        "M_Candle", "M_Flag", "M_Deco1", "M_Deco2", "M_Deco3", "M_Deco4",
        "M_Deco5", "M_Deco6", "M_Deco7"}
GLASS = {"M_GlassBottle_Object1715", "M_GlassBottle2", "M_GlassBottle3",
         "M_GlassBottle4", "M_GlassBottle5", "M_GlassBottle6",
         "M_HallwallGlass", "M_LanternGlass", "M_Wall_Lamp_Glass"}

# Pastel Nikki tints (r,g,b,a) per family
TINTS = {
    "WOOD":   [(0.95, 0.90, 0.80), (0.92, 0.85, 0.78), (0.88, 0.82, 0.72), (0.90, 0.86, 0.76)],
    "CARPET": [(0.78, 0.85, 0.80), (0.82, 0.78, 0.88), (0.80, 0.84, 0.90)],
    "GOLD":   [(0.98, 0.88, 0.68), (1.00, 0.90, 0.75), (0.95, 0.82, 0.62), (0.92, 0.88, 0.78)],
    "GLASS":  [(0.85, 0.95, 0.98), (0.96, 0.90, 0.98), (0.82, 0.92, 0.95), (0.95, 0.93, 0.85)],
}

STRENGTHS = {"WOOD": 0.18, "CARPET": 0.20, "GOLD": 0.28, "GLASS": 0.22}


def family_of(stem: str) -> str:
    if stem in WOOD: return "WOOD"
    if stem in CARPET: return "CARPET"
    if stem in GOLD: return "GOLD"
    if stem in GLASS: return "GLASS"
    return "WOOD"


def profile_of(fam: str) -> str:
    return {"WOOD": "TP_Default", "CARPET": "TP_Default",
            "GOLD": "TP_Gold", "GLASS": "TP_Default"}[fam]


def seed(s: str) -> int:
    return int(hashlib.md5(s.encode("utf-8")).hexdigest(), 16)


def pick(pool, s: str):
    return pool[seed(s) % len(pool)]


MEL = unreal.MaterialEditingLibrary


def find_toon_bsdf(material):
    for e in MEL.get_material_expressions(material) or []:
        if "SubstrateToonBSDF" in type(e).__name__:
            return e
    return None


def find_color_feeder(material, toon):
    """Slot-0 (BaseColor) feeder of the Toon BSDF: first wired input.

    get_inputs_for_material_expression returns one entry per BSDF pin in
    declaration order; SubstrateToonBSDF declares BaseColor first. The
    converter wired color to "BaseColor"/"DiffuseColor", so slot 0 is the
    color chain (TextureSample, or Clamp on Lantern/Globe).
    """
    try:
        ins = list(MEL.get_inputs_for_material_expression(material, toon)) or []
    except Exception:
        return None
    for i in ins:
        if i is not None:
            return i
    return None


def inject_layer(material_path: str) -> dict:
    m = unreal.load_asset(material_path)
    if m is None:
        return {"status": "missing"}
    toon = find_toon_bsdf(m)
    if toon is None:
        return {"status": "no_toon_bsdf"}
    feeder = find_color_feeder(m, toon)
    if feeder is None:
        return {"status": "no_feeder"}
    try:
        # 2. params
        tint = MEL.create_material_expression(
            m, unreal.MaterialExpressionVectorParameter, 100, 100)
        tint.set_editor_property("parameter_name", "BaseTint")
        tint.set_editor_property("group", "NikkiHero")
        tint.set_editor_property("default_value", unreal.LinearColor(1.0, 1.0, 1.0, 1.0))
        strength = MEL.create_material_expression(
            m, unreal.MaterialExpressionScalarParameter, 100, 200)
        strength.set_editor_property("parameter_name", "TintStrength")
        strength.set_editor_property("group", "NikkiHero")
        strength.set_editor_property("default_value", 0.0)
        lerp = MEL.create_material_expression(
            m, unreal.MaterialExpressionLinearInterpolate, 300, 100)
        # A=feeder, B=tint, Alpha=strength
        MEL.connect_material_expressions(feeder, "", lerp, "A")
        MEL.connect_material_expressions(tint, "", lerp, "B")
        MEL.connect_material_expressions(strength, "", lerp, "Alpha")
        # lerp out -> toon color pin (connect REPLACES the old feeder link
        # on the same pin, so no explicit disconnect is needed)
        wired = False
        for pin in ("BaseColor", "DiffuseColor"):
            try:
                MEL.connect_material_expressions(lerp, "", toon, pin)
                wired = True
                break
            except Exception:
                continue
        if not wired:
            return {"status": "no_wire_pin"}
        MEL.recompile_material(m)
        unreal.EditorAssetLibrary.save_loaded_asset(m, only_if_is_dirty=False)
        return {"status": "injected", "feeder": type(feeder).__name__}
    except Exception as ex:
        return {"status": "error", "error": str(ex)}


def create_mi(stem: str, fam: str) -> dict:
    folder = FOLDER_BY_STEM[stem]
    mi_name = "MI_" + stem
    mi_path = "%s/%s/%s" % (BASE, folder, mi_name)
    package_path = "%s/%s" % (BASE, folder)
    factory = unreal.MaterialInstanceConstantFactoryNew()
    mi = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        mi_name, package_path, unreal.MaterialInstanceConstant, factory)
    if mi is None:
        return {"status": "create_failed"}
    master = unreal.load_asset("%s/%s/%s.%s" % (BASE, folder, stem, stem))
    if master is None:
        return {"status": "no_parent"}
    mi.set_editor_property("parent", master)
    # profile
    prof_name = profile_of(fam)
    prof_path = "%s/%s.%s" % (PROFILE_DIR, prof_name, prof_name)
    if unreal.EditorAssetLibrary.does_asset_exist(prof_path):
        try:
            mi.set_editor_property("toon_profile", unreal.load_asset(prof_path))
            mi.set_editor_property("override_toon_profile", True)
        except Exception:
            pass
    # tint
    color = pick(TINTS[fam], stem)
    strength = STRENGTHS[fam]
    try:
        MEL.set_material_instance_vector_parameter_value(
            mi, "BaseTint", unreal.LinearColor(color[0], color[1], color[2], 1.0))
        MEL.set_material_instance_scalar_parameter_value(mi, "TintStrength", strength)
    except Exception as ex:
        pass
    saved = unreal.EditorAssetLibrary.save_asset(mi_path, only_if_is_dirty=False)
    return {"status": "created", "saved": bool(saved),
            "profile": prof_name, "tint": color, "strength": strength}


def main() -> int:
    results = []
    fail = 0
    for stem in ALL_STEMS:
        folder = FOLDER_BY_STEM[stem]
        master_path = "%s/%s/%s.%s" % (BASE, folder, stem, stem)
        inj = inject_layer(master_path)
        fam = family_of(stem)
        mi = create_mi(stem, fam) if inj["status"] == "injected" else {"status": "skipped_no_inject"}
        results.append({"stem": stem, "inject": inj, "mi": mi})
        if inj["status"] != "injected" or mi["status"] != "created":
            fail += 1
        print("R|%s|inject=%s|mi=%s" % (stem, inj["status"], mi["status"]))
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "results": results,
        "summary": {"ok": len(results) - fail, "fail": fail},
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("WROTE|%s" % REPORT)
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())