"""
Close out the deprecated M_Master_Toon_Universal_Alpha master.

Facts (Saved/Audit/alpha_master_usage.json, UE-side asset registry, 2026-10-21):
the Alpha master has exactly 5 referencers left - five root-level material
instances, all of which are the master's own children:

    /Game/M_Halftone_Circles___Circles__3_Inputs__001
    /Game/M_Iris_002
    /Game/M_Material_015
    /Game/M_Material_023
    /Game/M_Outline

An offline string scan reports ~215 "users"; that is stale editor-only data in
the saved packages, not live references. The registry is the truth.

This script:
  * for each of the 5: if something still references it, reparent it to
    M_Master_Toon_Universal and carry BlendMode=Masked + TwoSided=true +
    the master's bUseOpacityMap static switch (the mechanism commit 44398419e
    used for the same convergence, so appearance is preserved); if nothing
    references it, it is root-level slop and is deleted
  * re-applies every texture map from the instance's own source textures
  * verifies the Alpha master has zero referencers and deletes it
  * writes a receipt

Owner-approved 2026-10-21 ("no proxies, no slop").

Run: UnrealEditor-Cmd <proj> -run=pythonscript -script=<this file> -unattended -nullrhi
Writes Saved/Audit/alpha_master_closeout.json
"""

from __future__ import annotations

import json
from pathlib import Path

import unreal

ROOT = Path(r"C:\EnvironmentPortfolio\BS_GodFile")
OUT = ROOT / "Saved" / "Audit" / "alpha_master_closeout.json"

ALPHA_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal_Alpha"
MASTER_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"

LINES = []


def log(m):
    LINES.append(str(m))
    unreal.log(f"[AC] {m}")
    try:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text("\n".join(LINES), encoding="utf-8")
    except Exception:
        pass


def _param_info(name):
    pi = unreal.MaterialParameterInfo()
    pi.set_editor_property("name", name)
    try:
        pi.set_editor_property("association",
                               unreal.MaterialParameterAssociation.GLOBAL_PARAMETER)
    except Exception:
        pass
    return pi


def _reparent_and_fix(mi, master):
    """Reparent to the single master and carry the translucency overrides."""
    applied, failed = {}, []
    try:
        mi.set_editor_property("parent", master)
        applied["parent"] = MASTER_PATH
    except Exception as exc:
        failed.append(f"parent: {exc}")
    try:
        bpo = mi.get_editor_property("base_property_overrides")
        bpo.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
        bpo.set_editor_property("two_sided", True)
        mi.set_editor_property("base_property_overrides", bpo)
        applied["overrides"] = "Masked + TwoSided"
    except Exception as exc:
        failed.append(f"overrides: {exc}")
    try:
        unreal.MaterialEditingLibrary.set_material_instance_static_switch_parameter_value(
            mi, "bUseOpacityMap", True)
        applied["bUseOpacityMap"] = "True"
    except Exception as exc:
        failed.append(f"bUseOpacityMap: {exc}")
    return applied, failed


def _reapply_maps(mi):
    """Re-apply every texture the instance had, by name, onto the new parent."""
    routed, failed = {}, []
    try:
        tex_params = mi.get_editor_property("texture_parameter_values")
    except Exception:
        tex_params = None
    names = []
    try:
        for p in ("Albedo", "NormalMap", "ORM", "MetallicMap", "RoughnessMap",
                  "HeightMap", "EmissiveColor", "Opacity"):
            val = unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(
                mi, _param_info(p))
            if val:
                names.append((p, val))
    except Exception as exc:
        failed.append(f"read: {exc}")
    for p, tex in names:
        try:
            unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
                mi, p, tex)
            routed[p] = tex.get_path_name()
        except Exception as exc:
            failed.append(f"{p}: {exc}")
    return routed, failed


def main():
    report = {"generated": "2026-10-21", "alpha_master": ALPHA_PATH,
              "instances": [], "deleted_instances": [], "master_deleted": False}
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    opts = unreal.AssetRegistryDependencyOptions(
        include_soft_package_references=True,
        include_hard_package_references=True)
    master = unreal.EditorAssetLibrary.load_asset(MASTER_PATH)
    if master is None:
        log(f"FATAL master missing {MASTER_PATH}")
        return 1

    # the five root-level children of the deprecated master
    targets = []
    for a in ar.get_assets_by_path("/Game", recursive=False):
        if str(a.asset_class_path.asset_name) != "MaterialInstanceConstant":
            continue
        mi = a.get_asset()
        parent = mi.get_editor_property("parent") if mi else None
        pname = parent.get_path_name() if parent else None
        if pname and "M_Master_Toon_Universal_Alpha" in pname:
            targets.append((str(a.package_name), mi))

    log(f"instances still parented to the Alpha master: {len(targets)}")

    for pkg, mi in targets:
        refs = ar.get_referencers(pkg, opts)
        ref_names = sorted(str(r) for r in refs) if refs else []
        row = {"package": pkg, "referencers": len(ref_names),
               "referencer_list": ref_names[:12]}
        if not ref_names:
            # root-level slop, nothing uses it
            ok = unreal.EditorAssetLibrary.delete_asset(pkg)
            row["action"] = "deleted (unreferenced root-level slop)"
            row["deleted"] = bool(ok)
            report["deleted_instances"].append(pkg)
            log(f"{pkg}: deleted (0 referencers)")
        else:
            applied, failed = _reparent_and_fix(mi, master)
            routed, rfail = _reapply_maps(mi)
            unreal.EditorAssetLibrary.save_loaded_asset(mi, only_if_is_dirty=False)
            row["action"] = "reparented to M_Master_Toon_Universal"
            row["applied"] = applied
            row["routed"] = routed
            row["failed"] = failed + rfail
            log(f"{pkg}: reparented, {len(ref_names)} referencer(s), "
                f"{len(routed)} map(s) re-applied, failed={len(row['failed'])}")
        report["instances"].append(row)

    # now the master itself
    remaining = sorted(str(r) for r in (ar.get_referencers(ALPHA_PATH, opts) or []))
    report["alpha_master_referencers_after"] = remaining
    if remaining:
        log(f"Alpha master still referenced by {len(remaining)} asset(s) - NOT deleting: "
            + ", ".join(remaining[:10]))
    else:
        ok = unreal.EditorAssetLibrary.delete_asset(ALPHA_PATH)
        report["master_deleted"] = bool(ok)
        log(f"Alpha master deleted (0 referencers): {ok}")

    report["summary"] = {
        "instances_processed": len(report["instances"]),
        "instances_deleted": len(report["deleted_instances"]),
        "instances_reparented": sum(1 for r in report["instances"]
                                    if r.get("action", "").startswith("reparented")),
        "master_deleted": report["master_deleted"],
        "master_referencers_left": len(report.get("alpha_master_referencers_after", [])),
    }
    OUT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    log(f"DONE {report['summary']} -> {OUT}")
    return 0


if __name__ == "__main__":
    main()
