"""Author the 85 Atlantis MaterialInstanceConstants under M_Master_Toon_Universal
(water set -> M_Water_Master_Grand_v10_Upgrade), wired to imported textures.

Driven by Imports/KitBash3D_Atlantis/atlantis_toon.material_map.json (85 entries).

Conventions (proven by 08-13/14/15 sweeps): toon MIs must override
bLayerA_Active=True + LayerA_TextureWeight=1.0 + TextureWeight=1.0 or the
textures render as invisible/noise. Opacity sets additionally get the master's
gated opacity path (bUseOpacityMap=True + OpacityMap + OpacityStrength) when the
master exposes it.

Verify-by-reread: every MI is re-read after save and its overrides are checked
against what was written. Manifest: Saved/Audit/atlantis_mi_author.json

Run inside the live editor via Monolith run_python:
  import author_atlantis_mis as aa; aa.main()
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CROSSWALK = PROJECT_ROOT.parent / "Imports" / "KitBash3D_Atlantis" / "atlantis_toon.material_map.json"
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "atlantis_mi_author.json"

TEX_DEST = "/Game/EnvSandbox/Textures/Atlantis"
MI_ROOT = "/Game/EnvSandbox/Materials/Instances/Atlantis"
MASTER_TOON = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
MASTER_WATER = "/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v10_Upgrade"

WATER_SETS = {"WaterClean"}

# channel tag -> master texture slot. Confirmed by reflection probe 1+2
# (2026-08-17): Substrate masters store params as graph expressions; these are
# the exact parameter names.
TOON_CHANNEL_SLOTS: dict[str, str] = {
    "basecolor": "Albedo",
    "normal": "NormalMap",
    "metallic": "MetallicMap",
    "roughness": "RoughnessMap",
    "height": "HeightMap",
    "emissive": "EmissiveMap",
    "opacity": "OpacityMap",
}
WATER_CHANNEL_SLOTS: dict[str, str] = {
    "basecolor": "BaseColorTexture",
    "normal": "BaseNormalTexture",
    "roughness": "BaseRoughnessTexture",
    "height": "BaseHeightTexture",
}

# Opacity sets parent the masked variant master (BLEND_MASKED + two_sided +
# gated OpacityMap path); opaque Universal cannot cut out.
OPACITY_PARENT = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal_Alpha"
OPACITY_SETS = {
    "AtlasDecalOrnamets", "AtlasFlowersA", "AtlasIvy", "AtlasLeafA", "AtlasLeafB",
    "AtlasOrnaments", "AtlasPaintPatternsA", "AtlasTreeA", "Burlap", "Grass",
    "HaleBale", "PropsSpear",
}


def channel_of(stem: str) -> str:
    return stem.rsplit("_", 1)[-1].lower()


def texture_assets(set_name: str) -> dict[str, str]:
    """{channel_tag: texture_asset_path} for a set, from the texture folder."""
    found: dict[str, str] = {}
    folder = PROJECT_ROOT.parent / "Imports" / "KitBash3D_Atlantis" / "Source" / "Textures 4K"
    for png in folder.glob(f"KB3D_ATL_{set_name}_*.png"):
        channel = channel_of(png.stem)
        if channel and channel != "kb3d":
            found[channel] = f"{TEX_DEST}/{png.stem}"
    return found


EXPR_PARAM_CLASSES = {
    "scalar": ("MaterialExpressionScalarParameter",),
    "switch": ("MaterialExpressionStaticSwitchParameter", "MaterialExpressionStaticBoolParameter"),
    "texture": ("MaterialExpressionTextureObjectParameter", "MaterialExpressionTextureSampleParameter2D"),
}


def expression_params(mat: unreal.Material, kinds: tuple[str, ...]) -> set[str]:
    """Substrate masters report empty parameter_value arrays; enumerate the
    graph expressions instead (probe 2, 2026-08-17)."""
    names: set[str] = set()
    for e in unreal.MaterialEditingLibrary.get_material_expressions(mat) or []:
        if type(e).__name__ not in kinds:
            continue
        try:
            names.add(str(e.get_editor_property("parameter_name")))
        except Exception:
            continue
    return names


def master_params(parent_path: str) -> tuple[set[str], set[str], set[str]]:
    mat = unreal.EditorAssetLibrary.load_asset(parent_path)
    if not mat:
        return set(), set(), set()
    scalars = expression_params(mat, EXPR_PARAM_CLASSES["scalar"])
    switches = expression_params(mat, EXPR_PARAM_CLASSES["switch"])
    textures = expression_params(mat, EXPR_PARAM_CLASSES["texture"])
    return scalars, switches, textures


def ensure_mi(mat_name: str, parent_path: str) -> unreal.MaterialInstanceConstant | None:
    mi_path = f"{MI_ROOT}/MI_{mat_name}"
    if unreal.EditorAssetLibrary.does_asset_exist(mi_path):
        return unreal.EditorAssetLibrary.load_asset(mi_path)
    if not unreal.EditorAssetLibrary.does_directory_exist(MI_ROOT):
        unreal.EditorAssetLibrary.make_directory(MI_ROOT)
    factory = unreal.MaterialInstanceConstantFactoryNew()
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    mi = tools.create_asset(f"MI_{mat_name}", MI_ROOT, unreal.MaterialInstanceConstant, factory)
    if not mi:
        return None
    parent = unreal.EditorAssetLibrary.load_asset(parent_path)
    if not parent:
        return None
    mi.set_editor_property("parent", parent)
    return mi


def apply_toon_conventions(mi: unreal.MaterialInstanceConstant, scalars: set[str],
                           switches: set[str]) -> dict:
    written: dict = {"scalars": {}, "switches": {}}
    if "bLayerA_Active" in switches:
        unreal.MaterialEditingLibrary.set_material_instance_static_switch_parameter_value(
            mi, "bLayerA_Active", True)
        written["switches"]["bLayerA_Active"] = True
    if "LayerA_TextureWeight" in scalars:
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
            mi, "LayerA_TextureWeight", 1.0)
        written["scalars"]["LayerA_TextureWeight"] = 1.0
    if "TextureWeight" in scalars:
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
            mi, "TextureWeight", 1.0)
        written["scalars"]["TextureWeight"] = 1.0
    return written


def wire_textures(mi: unreal.MaterialInstanceConstant, channels: dict[str, str],
                  slot_map: dict[str, str]) -> tuple[list[str], list[str]]:
    wired, missed = [], []
    for channel, tex_path in sorted(channels.items()):
        slot = slot_map.get(channel)
        if not slot:
            missed.append(f"{channel} (no slot in map)")
            continue
        tex = unreal.EditorAssetLibrary.load_asset(tex_path)
        if not tex:
            missed.append(f"{channel} ({tex_path} missing)")
            continue
        try:
            unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
                mi, slot, tex)
            wired.append(f"{channel}->{slot}")
        except Exception as exc:
            missed.append(f"{channel}->{slot} ({exc})")
    return wired, missed


def apply_opacity(mi: unreal.MaterialInstanceConstant, tex_path: str,
                  scalars: set[str], switches: set[str]) -> dict:
    written: dict = {"scalars": {}, "switches": {}, "textures": {}}
    if "bUseOpacityMap" in switches:
        unreal.MaterialEditingLibrary.set_material_instance_static_switch_parameter_value(
            mi, "bUseOpacityMap", True)
        written["switches"]["bUseOpacityMap"] = True
    if "OpacityStrength" in scalars:
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
            mi, "OpacityStrength", 1.0)
        written["scalars"]["OpacityStrength"] = 1.0
    tex = unreal.EditorAssetLibrary.load_asset(tex_path)
    if tex:
        for slot_cand in ("OpacityMap", "OpacityMask", "Opacity"):
            try:
                unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
                    mi, slot_cand, tex)
                written["textures"][slot_cand] = tex_path
                break
            except Exception:
                continue
    return written


def reread_check(mi: unreal.MaterialInstanceConstant, expected: dict) -> dict:
    """Verify-by-reread: confirm overrides landed on the saved asset."""
    ok = True
    detail: dict = {}
    for kind, values in expected.items():
        detail[kind] = {}
        for name, want in values.items():
            try:
                if kind == "switches":
                    got = unreal.MaterialEditingLibrary.get_material_instance_static_switch_parameter_value(
                        mi, name, unreal.MaterialParameterAssociation.GLOBAL_PARAMETER)
                elif kind == "textures":
                    got = unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(
                        mi, name)
                    got = str(got.get_path_name()).rsplit(".", 1)[0] if got else None
                else:
                    got = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(
                        mi, name)
                match = (got == want)
                ok = ok and match
                detail[kind][name] = {"wanted": want, "got": got, "match": match}
            except Exception as exc:
                ok = False
                detail[kind][name] = {"wanted": want, "error": str(exc), "match": False}
    return {"ok": ok, "detail": detail}


def main(force: bool = False) -> dict:
    if not TOON_CHANNEL_SLOTS or not WATER_CHANNEL_SLOTS:
        return {"ok": False, "error": "slot maps empty — run probe first and fill maps"}

    crosswalk = json.loads(CROSSWALK.read_text(encoding="utf-8"))
    _, _, water_slots = master_params(MASTER_WATER)
    water_missing_slots = [s for s in WATER_CHANNEL_SLOTS.values() if s not in water_slots]
    if water_missing_slots:
        return {"ok": False, "error": f"water master missing slots: {water_missing_slots}"}
    if OPACITY_SETS and not unreal.EditorAssetLibrary.does_asset_exist(OPACITY_PARENT):
        return {"ok": False, "error": f"opacity variant missing: {OPACITY_PARENT} — run wire_atlantis_opacity_master first"}

    results: list[dict] = []
    for mat_name, _mi_path in sorted(crosswalk.items()):
        channels = texture_assets(mat_name)
        is_water = mat_name in WATER_SETS
        is_opacity = mat_name in OPACITY_SETS
        parent = OPACITY_PARENT if is_opacity else (MASTER_WATER if is_water else MASTER_TOON)
        slot_map = WATER_CHANNEL_SLOTS if is_water else TOON_CHANNEL_SLOTS
        parent_scalars, parent_switches, _ = master_params(parent)
        rec = {"mat_name": mat_name, "parent": parent, "texture_channels": sorted(channels)}

        mi = ensure_mi(mat_name, parent)
        if not mi:
            rec["ok"] = False
            rec["error"] = "MI create/load failed"
            results.append(rec)
            continue

        expected: dict = {"scalars": {}, "switches": {}, "textures": {}}
        if is_water:
            conv = wire_textures(mi, channels, slot_map)
            rec["wired"], rec["missed"] = conv
            for pair in rec["wired"]:
                ch, slot = pair.split("->", 1)
                expected["textures"][slot] = str(channels[ch])
        else:
            conv = wire_textures(mi, channels, slot_map)
            rec["wired"], rec["missed"] = conv
            for pair in rec["wired"]:
                ch, slot = pair.split("->", 1)
                expected["textures"][slot] = str(channels[ch])
            convw = apply_toon_conventions(mi, parent_scalars, parent_switches)
            expected["scalars"].update(convw["scalars"])
            expected["switches"].update(convw["switches"])
            if "opacity" in channels:
                op = apply_opacity(mi, channels["opacity"], parent_scalars, parent_switches)
                rec["opacity"] = op
                expected["scalars"].update(op["scalars"])
                expected["switches"].update(op["switches"])
                expected["textures"].update(op["textures"])

        try:
            unreal.MaterialEditingLibrary.update_material_instance(mi)
            unreal.EditorAssetLibrary.save_loaded_asset(mi)
        except Exception as exc:
            rec["ok"] = False
            rec["error"] = f"save: {exc}"
            results.append(rec)
            continue

        rec["verify"] = reread_check(mi, expected)
        rec["ok"] = rec["verify"]["ok"]
        results.append(rec)

    ok_count = sum(1 for r in results if r.get("ok"))
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total": len(results),
        "ok": ok_count,
        "failed": [r["mat_name"] for r in results if not r.get("ok")],
        "results": results,
        "all_ok": ok_count == len(results),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    raise SystemExit(0 if main().get("all_ok") else 1)