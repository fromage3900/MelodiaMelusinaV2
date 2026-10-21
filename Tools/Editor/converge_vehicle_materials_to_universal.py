"""
Converge the enchanted-vehicle material instances onto the single toon master.

State found by the offline audit (Saved/Audit/enchanted_vehicle_materials_audit.json):

  set A  /Game/KitBash_EnchantedVehicles/M_KB3D_ECV_<Stem>   (72) - referenced by the
         172 vehicle meshes. Fully map-routed, but 17 of them are still parented to
         M_Master_Toon_Universal_Alpha - the master that was converged away into
         M_Master_Toon_Universal on 2026-09-05 (commit 44398419e). That commit left
         the Alpha master on disk, orphaned, and told us nothing should be
         reparented back to it.

  set B  /Game/Melodia/Imported/EnchantedVehicles/MI_KB3D_ECV_<Stem> (73) - referenced
         by nothing; a duplicate of set A that was reparented to Universal but never
         got its opacity/emissive maps routed and carries no masked override.

This script fixes set A in place: every instance whose parent is the deprecated
Alpha master is reparented to M_Master_Toon_Universal and, to preserve appearance
exactly as commit 44398419e did for 109 instances, carries BlendMode=Masked +
TwoSided=true + bUseOpacityMap=True as per-instance base property overrides.
All texture routes are re-applied from the stem's own textures so nothing depends
on the old parent having the same parameter names.

Set B is NOT touched here: retiring a duplicate asset set is an owner decision
(asset deletion is owner-ask-first in this repo).

Run inside the editor: Monolith editor_query run_python.
Writes Saved/Audit/vehicle_material_convergence_run.json
"""

from __future__ import annotations

import json
from pathlib import Path

import unreal

ROOT = Path(r"C:\EnvironmentPortfolio\BS_GodFile")
OUT = ROOT / "Saved" / "Audit" / "vehicle_material_convergence_run.json"

SET_A = "/Game/KitBash_EnchantedVehicles"
TEX_ROOT = "/Game/KitBash_EnchantedVehicles"
MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
DEPRECATED = "M_Master_Toon_Universal_Alpha"

MAP_TO_PARAM = {
    "basecolor": "Albedo",
    "normal": "NormalMap",
    "metallic": "MetallicMap",
    "roughness": "RoughnessMap",
    "height": "HeightMap",
    "ao": "ORM",
    "orm": "ORM",
    "emissive": "EmissiveColor",
    "opacity": "Opacity",
}
SUFFIXES = ("basecolor", "normal", "metallic", "roughness", "height", "ao",
            "orm", "emissive", "opacity")


def log(m):
    unreal.log(f"[ECV] {m}")


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
    # UE 5.8: the SETTER takes a plain FName (ParameterName); only the GETTER
    # takes a MaterialParameterInfo.
    try:
        unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
            mi, param, tex)
        return True, None
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def _masked_blend_mode():
    """UE 5.8 exposes the blend-mode enum members under different names; find it."""
    for cand in ("BLEND_MASKED", "MASKED", "BLEND_TRANSLUCENT", "TRANSLUCENT"):
        v = getattr(unreal.BlendMode, cand, None)
        if v is not None:
            return v
    for name in dir(unreal.BlendMode):
        if "MASK" in name.upper():
            return getattr(unreal.BlendMode, name)
    return None


def _apply_overrides(mi):
    """BlendMode=Masked + TwoSided=true (the fields UE 5.8 exposes) plus the
    master's bUseOpacityMap static switch (not a base-override field in 5.8)."""
    applied, failed = {}, []
    try:
        bpo = mi.get_editor_property("base_property_overrides")
    except Exception as exc:
        return {}, [f"read: {exc}"]
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
        failed.append(f"write: {exc}")
    try:
        unreal.MaterialEditingLibrary.set_material_instance_static_switch_parameter_value(
            mi, "bUseOpacityMap", True)
        applied["bUseOpacityMap(static switch)"] = "True"
    except Exception as exc:
        failed.append(f"bUseOpacityMap: {exc}")
    return applied, failed


def _stem_textures(stem):
    """stem -> {map_suffix: texture_path} from the pack textures on disk."""
    out = {}
    for suf in SUFFIXES:
        p = f"{TEX_ROOT}/{stem}_{suf}"
        if unreal.EditorAssetLibrary.does_asset_exist(p):
            out[suf] = p
    return out


def main():
    report = {"generated": "2026-10-21", "master": MASTER, "results": []}
    master = unreal.EditorAssetLibrary.load_asset(MASTER)
    if master is None:
        report["fatal"] = f"master missing {MASTER}"
        OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        log("FATAL master missing")
        return 1

    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    assets = [a for a in ar.get_assets_by_path(SET_A, recursive=True)
              if str(a.asset_class_path.asset_name) == "MaterialInstanceConstant"
              and str(a.asset_name).startswith("M_KB3D_ECV_")]

    for a in assets:
        mi = a.get_asset()
        stem = str(a.asset_name)[len("M_KB3D_ECV_"):]
        parent = mi.get_editor_property("parent")
        parent_name = parent.get_path_name() if parent else None
        row = {"stem": stem, "package": str(a.package_name),
               "parent_before": parent_name, "reparented": False,
               "overrides": {}, "routed": {}, "failed": []}

        if parent_name and DEPRECATED in parent_name:
            try:
                mi.set_editor_property("parent", master)
                row["reparented"] = True
            except Exception:
                try:
                    unreal.MaterialEditingLibrary.set_material_instance_parent(mi, master)
                    row["reparented"] = True
                except Exception as exc:
                    row["failed"].append(f"reparent: {exc}")

        if row["reparented"]:
            applied, failed = _apply_overrides(mi)
            row["overrides"] = applied
            row["failed"].extend(failed)

        # re-apply every map from the stem's own textures, for every instance, so
        # the whole set is verified rather than only the reparented ones
        for suf, path in sorted(_stem_textures(stem).items()):
            param = MAP_TO_PARAM.get(suf)
            if not param:
                continue
            tex = unreal.EditorAssetLibrary.load_asset(path)
            if tex is None:
                row["failed"].append(f"{suf}: texture load failed")
                continue
            ok, err = _set_texture(mi, param, tex)
            if ok:
                row["routed"][suf] = param
            else:
                row["failed"].append(f"{suf}->{param}: {err}")

        parent_after = mi.get_editor_property("parent")
        row["parent_after"] = parent_after.get_path_name() if parent_after else None
        unreal.EditorAssetLibrary.save_loaded_asset(mi, only_if_is_dirty=False)
        report["results"].append(row)
        if row["reparented"]:
            log(f"reparented {stem}: {row['parent_before']} -> {row['parent_after']} "
                f"routed={len(row['routed'])} failed={len(row['failed'])}")

    report["summary"] = {
        "instances": len(report["results"]),
        "reparented": sum(1 for r in report["results"] if r["reparented"]),
        "failed": sum(1 for r in report["results"] if r["failed"]),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    log(f"DONE {report['summary']} -> {OUT}")
    return 0


if __name__ == "__main__":
    main()
