"""
Enchanted Interiors (Kitbash3D, UE4.26+) -> project material instances.

The pack's own `KB3D_ECI_*` materials are `kb3d_master_*` proxy instances and are
NOT imported. Instead one MaterialInstance per texture stem is authored on the
project's single toon master (M_Master_Toon_Universal) and created at the *same
package path* the pack material occupied:

    /Game/EnchantedInteriors/Materials/KB3D_ECI_<Stem>

The 1,696 pack meshes reference that path, so every material slot resolves to the
new instance with no mesh re-save and no re-import.

Map routing (KitBash ARM = AO/Roughness/Metallic packed -> master ORM):
    basecolor -> Albedo
    normal    -> NormalMap
    arm       -> ORM
    emissive  -> EmissiveColor
    opacity   -> Opacity

Translucent stems (opacity or refraction) get BlendMode=Masked + TwoSided=true as
per-instance base property overrides, plus the master's `bUseOpacityMap` static
switch, so translucency survives now that M_Master_Toon_Universal_Alpha was
converged into M_Master_Toon_Universal (commit 44398419e).

UE 5.8 API (verified by Tools/Editor/discover_material_api.py):
    unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(mi, MaterialParameterInfo, tex)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, MaterialParameterInfo, float)
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(mi, MaterialParameterInfo, LinearColor)
    unreal.MaterialEditingLibrary.set_material_instance_static_switch_parameter_value(mi, MaterialParameterInfo, bool)
    unreal.MaterialParameterAssociation.GLOBAL_PARAMETER
    unreal.BlendMode.BLEND_MASKED
    base_property_overrides: blend_mode, two_sided  (no b_use_opacity_map in 5.8)

Run inside the editor: Monolith editor_query run_python, or
    UnrealEditor-Cmd <proj> -run=pythonscript -script=<this file> -unattended -nullrhi
Writes Saved/Audit/enchanted_interiors_conversion.json
"""

from __future__ import annotations

import json
from pathlib import Path

import unreal

ROOT = Path(r"C:\EnvironmentPortfolio\BS_GodFile")
OUT = ROOT / "Saved" / "Audit" / "enchanted_interiors_conversion.json"

TEX_ROOT = "/Game/EnchantedInteriors/Textures"
MAT_ROOT = "/Game/EnchantedInteriors/Materials"
MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"

MAP_TO_PARAM = {
    "basecolor": "Albedo",
    "normal": "NormalMap",
    "arm": "ORM",
    "ao": "ORM",
    "metallic": "MetallicMap",
    "roughness": "RoughnessMap",
    "height": "HeightMap",
    "emissive": "EmissiveColor",
    "opacity": "Opacity",
}
SUFFIXES = ("basecolor", "normal", "arm", "ao", "metallic", "roughness",
            "height", "emissive", "opacity", "refraction")

SHADOW_DREAM = {"ShadowDreamStrength": 0.7, "ShadowFlowerStrength": 0.45,
                "ShadowFlowerScale": 1.0}
SHADOW_TINT = (0.541, 0.627, 0.839, 1.0)   # #8AA0D6
FLOWER_COLOR = (0.910, 0.627, 0.749, 1.0)  # #E8A0BF

OUT_LINES = []


def log(m):
    OUT_LINES.append(str(m))
    unreal.log(f"[ECI] {m}")


def _param_info(name):
    pi = unreal.MaterialParameterInfo()
    pi.set_editor_property("name", name)
    try:
        pi.set_editor_property("association",
                               unreal.MaterialParameterAssociation.GLOBAL_PARAMETER)
    except Exception:
        pass
    return pi


def _set_texture(mi, param, tex):
    # UE 5.8: the SETTER takes a plain FName (ParameterName), not a
    # MaterialParameterInfo - only the GETTER takes the struct.
    try:
        unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
            mi, param, tex)
        return True, None
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def _set_scalar(mi, name, value):
    try:
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
            mi, name, float(value))
        return True, None
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def _set_vector(mi, name, rgba):
    try:
        unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
            mi, name, unreal.LinearColor(*rgba))
        return True, None
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def _set_static_switch(mi, name, value):
    try:
        unreal.MaterialEditingLibrary.set_material_instance_static_switch_parameter_value(
            mi, name, bool(value))
        return True, None
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def _set_overrides(mi):
    """BlendMode=Masked + TwoSided=true (the fields UE 5.8 actually exposes)."""
    applied, failed = {}, []
    try:
        bpo = mi.get_editor_property("base_property_overrides")
    except Exception as exc:
        return {}, [f"read base_property_overrides: {exc}"]
    for prop, value in (("blend_mode", unreal.BlendMode.BLEND_MASKED),
                        ("two_sided", True)):
        try:
            bpo.set_editor_property(prop, value)
            applied[prop] = str(value)
        except Exception as exc:
            failed.append(f"{prop}: {exc}")
    try:
        mi.set_editor_property("base_property_overrides", bpo)
    except Exception as exc:
        failed.append(f"write base_property_overrides: {exc}")
    return applied, failed


def _discover_stems():
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    stems = {}
    for a in ar.get_assets_by_path(TEX_ROOT, recursive=True):
        name = str(a.asset_name)
        for suf in SUFFIXES:
            if name.endswith("_" + suf):
                stems.setdefault(name[: -(len(suf) + 1)], {})[suf] = str(a.package_name)
                break
    return stems


def _ensure_folder(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def _create_mi(stem, parent):
    # the stem already carries the pack's own "KB3D_ECI_" prefix, and the instance
    # must land on exactly the package path the pack material occupied so the
    # 1696 meshes resolve their slots to it.
    path = f"{MAT_ROOT}/{stem}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        mi = unreal.EditorAssetLibrary.load_asset(path)
        return mi, path, "existing"
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    mi = tools.create_asset(stem, MAT_ROOT, unreal.MaterialInstanceConstant,
                            unreal.MaterialInstanceConstantFactoryNew())
    if mi is None:
        return None, path, "create_failed"
    try:
        mi.set_editor_property("parent", parent)
    except Exception as exc:
        log(f"WARN parent set failed for {stem}: {exc}")
    return mi, path, "created"


def _read_back(mi):
    parent = None
    try:
        p = mi.get_editor_property("parent")
        parent = p.get_path_name() if p else None
    except Exception:
        pass
    tex_params = {}
    try:
        mi.get_editor_property("texture_parameter_values")
    except Exception:
        pass
    # read back through the master-facing getters
    try:
        for param in ("Albedo", "NormalMap", "ORM", "MetallicMap", "RoughnessMap",
                      "HeightMap", "EmissiveColor", "Opacity"):
            val = unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(
                mi, _param_info(param))
            if val:
                tex_params[param] = val.get_path_name()
    except Exception as exc:
        log(f"WARN texture readback: {exc}")
    blend = two_sided = None
    try:
        bpo = mi.get_editor_property("base_property_overrides")
        blend = str(bpo.get_editor_property("blend_mode"))
        two_sided = bool(bpo.get_editor_property("two_sided"))
    except Exception:
        pass
    return {"parent": parent, "textures": tex_params, "blend_mode": blend,
            "two_sided": two_sided}


def main():
    report = {"generated": "2026-10-21", "master": MASTER, "results": []}
    parent = unreal.EditorAssetLibrary.load_asset(MASTER)
    if parent is None:
        report["fatal"] = f"master not found: {MASTER}"
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        log(f"FATAL master missing: {MASTER}")
        return 1

    _ensure_folder(MAT_ROOT)
    stems = _discover_stems()
    report["stems_found"] = len(stems)
    log(f"stems found: {len(stems)}")

    for stem in sorted(stems):
        maps = stems[stem]
        translucent = ("opacity" in maps) or ("refraction" in maps)
        mi, path, status = _create_mi(stem, parent)
        row = {"stem": stem, "path": path, "status": status,
               "maps_on_disk": sorted(maps.keys()), "translucent": translucent,
               "routed": {}, "failed": []}
        if mi is None:
            row["status"] = "create_failed"
            report["results"].append(row)
            continue

        for suf, tex_path in sorted(maps.items()):
            param = MAP_TO_PARAM.get(suf)
            if param is None:
                row["failed"].append(f"{suf}: no master param")
                continue
            tex = unreal.EditorAssetLibrary.load_asset(tex_path)
            if tex is None:
                row["failed"].append(f"{suf}: texture failed to load {tex_path}")
                continue
            ok, err = _set_texture(mi, param, tex)
            if ok:
                row["routed"][suf] = param
            else:
                row["failed"].append(f"{suf} -> {param}: {err}")

        for name, value in SHADOW_DREAM.items():
            ok, err = _set_scalar(mi, name, value)
            if not ok:
                row["failed"].append(f"scalar {name}: {err}")
        for name, value in (("TextureWeight", 1.0), ("LayerA_TextureWeight", 1.0)):
            _set_scalar(mi, name, value)
        _set_vector(mi, "ShadowDreamTint", SHADOW_TINT)
        _set_vector(mi, "ShadowFlowerColor", FLOWER_COLOR)

        if translucent:
            applied, failed = _set_overrides(mi)
            row["overrides_applied"] = applied
            row["failed"].extend(failed)
            ok, err = _set_static_switch(mi, "bUseOpacityMap", True)
            row["opacity_switch"] = "set" if ok else f"FAILED: {err}"

        unreal.EditorAssetLibrary.save_loaded_asset(mi, only_if_is_dirty=False)
        row["readback"] = _read_back(mi)
        report["results"].append(row)
        log(f"{stem}: {status} routed={len(row['routed'])} failed={len(row['failed'])}")

    ok_rows = [r for r in report["results"] if r.get("status") in ("created", "existing")
               and not r.get("failed")]
    report["summary"] = {
        "total": len(report["results"]),
        "clean": len(ok_rows),
        "with_failures": len(report["results"]) - len(ok_rows),
        "translucent": sum(1 for r in report["results"] if r.get("translucent")),
        "routed_total": sum(len(r.get("routed", {})) for r in report["results"]),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    log(f"DONE {report['summary']} -> {OUT}")
    return 0


if __name__ == "__main__":
    main()
