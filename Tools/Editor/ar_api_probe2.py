#!/usr/bin/env python
"""Find the working UE 5.8 Python call for AssetRegistry.get_referencers.

    UnrealEditor-Cmd.exe BS_GodFile.uproject -run=pythonscript -script=... -unattended -nullrhi -stdout
"""
from __future__ import annotations

import unreal


def main():
    names = [n for n in dir(unreal) if "Dependency" in n or "Reference" in n or "Registry" in n]
    unreal.log("[probe2] unreal types: %s" % sorted(names))

    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    assets = ar.get_assets_by_path("/Game/EnvSandbox/Meshes/Environment/_RetroFantasyKit", True)
    if not assets:
        unreal.log("[probe2] no assets")
        return
    pkg = str(assets[0].package_name)
    unreal.log("[probe2] probing package: %s" % pkg)

    # candidate option struct names
    for type_name in ("AssetRegistryDependencyOptions", "AssetRegistryReferenceOptions",
                      "AssetRegistryDependencyQuery", "DependencyOptions"):
        t = getattr(unreal, type_name, None)
        if t is None:
            unreal.log("[probe2] %-34s ABSENT" % type_name)
            continue
        try:
            opts = t()
        except Exception as exc:
            unreal.log("[probe2] %-34s ctor failed: %s" % (type_name, exc))
            continue
        props = [p for p in dir(opts) if not p.startswith("_")]
        unreal.log("[probe2] %-34s OK props=%s" % (type_name, props))
        try:
            res = ar.get_referencers(pkg, opts)
            unreal.log("[probe2]   get_referencers -> %d" % len(res))
            for r in list(res)[:5]:
                unreal.log("[probe2]     %s" % str(r))
        except Exception as exc:
            unreal.log("[probe2]   get_referencers failed: %s" % exc)


main()
