#!/usr/bin/env python
"""Probe the UE 5.8 Python Asset Registry API so the real referencer query
uses the functions that actually exist.

    UnrealEditor-Cmd.exe BS_GodFile.uproject -run=pythonscript -script=... -unattended -nullrhi -stdout

Prints the relevant surface and nothing else. Read-only.
"""
from __future__ import annotations

import unreal


def show(label, obj, needles):
    names = [n for n in dir(obj) if any(k in n.lower() for k in needles)]
    unreal.log("[probe] %s -> %s" % (label, sorted(names)))


def main():
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    show("AssetRegistry", ar, ["refer", "depend"])
    show("AssetRegistry", ar, ["asset", "path", "class"])
    show("AssetRegistryHelpers", unreal.AssetRegistryHelpers, ["registry", "asset"])

    sample = ar.get_assets_by_path("/Game/EnvSandbox/Meshes/Environment/_RetroFantasyKit", True)
    unreal.log("[probe] _RetroFantasyKit assets: %d" % len(sample))
    if sample:
        a = sample[0]
        show("AssetData", a, ["tag", "size", "class", "name", "package"])
        unreal.log("[probe] sample package: %s" % str(a.package_name))
        unreal.log("[probe] sample class  : %s" % str(a.asset_class_path))
        # try the plausible referencer calls and report which ones work
        pkg = str(a.package_name)
        for expr in (
            "ar.get_referencers(pkg)",
            "ar.get_referencers(pkg, unreal.AssetRegistryDependencyType.HARD)",
            "ar.get_dependents(pkg)",
            "ar.get_dependencies(pkg)",
        ):
            try:
                val = eval(expr)
                n = len(val) if hasattr(val, "__len__") else "?"
                unreal.log("[probe] OK   %-62s -> %s" % (expr, n))
            except Exception as exc:
                unreal.log("[probe] FAIL %-62s -> %s" % (expr, exc))
        # AssetData size
        for expr in (
            "a.get_tag_value('Tag_AssetSize', 0)",
            "a.get_tag_value('Tag_AssetSize')",
            "a.get_full_name()",
        ):
            try:
                unreal.log("[probe] OK   %-46s -> %s" % (expr, eval(expr)))
            except Exception as exc:
                unreal.log("[probe] FAIL %-46s -> %s" % (expr, exc))


main()
