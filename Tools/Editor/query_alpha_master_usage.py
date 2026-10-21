"""
Authoritative query: which material instances are REALLY parented to
M_Master_Toon_Universal_Alpha, and which assets use it directly as a slot.

The offline string scan is not trustworthy here: after a reparent, the saved
package can still carry the old master path in its editor-only data, so a raw
string match over-reports. This asks the asset registry / reflection instead.

Read-only. Run: UnrealEditor-Cmd <proj> -run=pythonscript -script=<this file> -unattended -nullrhi
Writes Saved/Audit/alpha_master_usage.json
"""

from __future__ import annotations

import json
from pathlib import Path

import unreal

ROOT = Path(r"C:\EnvironmentPortfolio\BS_GodFile")
OUT = ROOT / "Saved" / "Audit" / "alpha_master_usage.json"

ALPHA = "M_Master_Toon_Universal_Alpha"


def main():
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    opts = unreal.AssetRegistryDependencyOptions(
        include_soft_package_references=True,
        include_hard_package_references=True)

    # 1. instances whose PARENT is the alpha master
    children = []
    for a in ar.get_assets_by_path("/Game", recursive=True):
        if str(a.asset_class_path.asset_name) != "MaterialInstanceConstant":
            continue
        mi = a.get_asset()
        if mi is None:
            continue
        parent = mi.get_editor_property("parent")
        pname = parent.get_path_name() if parent else None
        if pname and ALPHA in pname:
            children.append({"package": str(a.package_name),
                             "name": str(a.asset_name),
                             "parent": pname,
                             "folder": str(a.package_name).rsplit("/", 1)[0]})
    unreal.log(f"[ALPHA] instances parented to {ALPHA}: {len(children)}")

    # 2. direct referencers of the alpha master package (meshes/BPs using it as a slot)
    alpha_pkg = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal_Alpha"
    direct = sorted(str(r) for r in (ar.get_referencers(alpha_pkg, opts) or []))
    unreal.log(f"[ALPHA] direct referencers of the master package: {len(direct)}")
    for d in direct[:20]:
        unreal.log(f"[ALPHA]   {d}")

    by_folder = {}
    for c in children:
        by_folder[c["folder"]] = by_folder.get(c["folder"], 0) + 1

    report = {
        "generated": "2026-10-21",
        "alpha_master": alpha_pkg,
        "instances_parented_to_alpha": len(children),
        "by_folder": dict(sorted(by_folder.items(), key=lambda kv: -kv[1])),
        "direct_referencers": direct,
        "direct_referencer_count": len(direct),
        "instances": children,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    unreal.log(f"[ALPHA] DONE -> {OUT}")
    return 0


if __name__ == "__main__":
    main()
