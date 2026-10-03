"""Set up the MooaToon inverted-hull outline system in BS_GodFile.

WHY
---
PPV depth/normal edge detection is a screen-space filter: it crawls under any
temporal AA (documented live in this project), cannot resolve interior edges,
and costs a full-screen pass. For stylized work the correct primary outline is
per-mesh inverted hull, with PPV kept as a secondary/atmospheric layer.

STATE FOUND 2026-09-30 (binary scan, read-only before any write)
---------------------------------------------------------------
A genuine inverted-hull master already exists and is NOT wired to anything:

    /Game/_ThirdParty/Genshin_Shader_v1_1/M_Hull_Outline     109,242 bytes
    /Game/Genshin_Shader_v1_1/M_Hull_Outline                 107,252 bytes

Graph proves it is a real hull, not a name: VertexNormalWS x
ActorPositionWS/CameraPositionWS -> Distance -> OneMinus, plus TwoSidedSign,
BLEND_Masked, Unlit, OpacityMask. The two copies have DIVERGED (different
bytes, different sizes), so this is not a duplicate to dedupe blindly - the
newer /Game/ copy is the candidate owner and the _ThirdParty copy is archived
Third-Party content.

Separately, 34 near-identical `Outline_Shader___NNN` assets are FBX-imported
MaterialInstanceConstants (`FBXLegacyPhongSurfaceMaterial`), NOT outlines -
they have zero material expression nodes. They are per-mesh FBX junk that
merely inherited an "Outline" name from the DCC export. Do not wire those.

This script therefore:
  1. creates ONE canonical location under /Game/Melodia/_PROJECT/04_Materials/
  2. builds per-asset instances (thin / heavy / hairline) parented to the
     existing hull master
  3. leaves the existing PPV stack completely untouched

Run (BS_GodFile is the ONLY project this is valid in):
    UnrealEditor-Cmd.exe "C:\\EnvironmentPortfolio\\BS_GodFile\\BS_GodFile.uproject" ^
      -ExecutePythonScript="Python/setup_hull_outline.py" -stdout -unattended
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import unreal  # noqa: E402

REPORT = Path(os.environ.get("TEMP", ".")) / "hull_outline_report.json"

# The proven hull master. _ThirdParty is archived vendor content and the two
# copies have diverged, so we reference rather than move anything.
HULL_MASTER = "/Game/Genshin_Shader_v1_1/M_Hull_Outline"
HULL_MASTER_ALT = "/Game/_ThirdParty/Genshin_Shader_v1_1/M_Hull_Outline"

# Canonical home: under the existing Melodia materials tree so it sits beside
# the frozen PPV stack without touching it.
OUTLINE_DIR = "/Game/Melodia/_PROJECT/04_Materials/Outline"


def log(m):
    unreal.log("[HullOutline] " + str(m))


def asset_path(folder, name):
    return f"{folder}/{name}.{name}"


def ensure_dir(p):
    if not unreal.EditorAssetLibrary.does_directory_exist(p):
        unreal.EditorAssetLibrary.make_directory(p)


# The hull master's real parameter surface, recovered by binary string scan.
# Thickness is a ScalarParameter on the master; per-asset control comes from
# instance overrides on the same names.
# The master's real scalar parameter is "Line Width" and its switch is
# "Use Dynamic Outline Width?" - read off the live graph by
# discover_master_params(), NOT guessed. "Line Width" is world-space-ish: it
# feeds a Distance/ActorPositionWS term, so it is camera-distance aware.
SPECS = [
    # name,                        Line Width, extra overrides
    ("MI_HullOutline_Hairline",        0.15, {"Use Dynamic Outline Width?": False}),
    ("MI_HullOutline_Character_Thin",  0.40, {"Use Dynamic Outline Width?": False}),
    ("MI_HullOutline_Environment",     0.70, {"Use Dynamic Outline Width?": False}),
    ("MI_HullOutline_Character_Heavy", 1.20, {"Use Dynamic Outline Width?": True}),
]


def build_instances():
    parent = unreal.load_asset(HULL_MASTER)
    if parent is None:
        parent = unreal.load_asset(HULL_MASTER_ALT)
    if parent is None:
        raise RuntimeError("M_Hull_Outline not found in either location")
    log(f"parent master: {parent.get_path_name()}")

    ensure_dir(OUTLINE_DIR)
    tools = unreal.AssetToolsHelpers.get_asset_tools()

    made = []
    for name, line_width, overrides in SPECS:
        path = asset_path(OUTLINE_DIR, name)
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            # re-apply: the parameter names were corrected after the first pass
            existing = unreal.load_asset(path)
            unreal.MaterialEditingLibrary.set_material_instance_parent(
                existing, parent)
            me0 = unreal.MaterialEditingLibrary
            for pn, pv in list(overrides.items()) + [("Line Width", line_width)]:
                try:
                    if isinstance(pv, bool):
                        me0.set_material_instance_static_switch_parameter_value(
                            existing, pn, pv)
                    else:
                        me0.set_material_instance_scalar_parameter_value(
                            existing, pn, float(pv))
                except Exception:
                    pass
            unreal.EditorAssetLibrary.save_loaded_asset(existing,
                                                        only_if_is_dirty=False)
            made.append(path)
            log(f"REAPPLIED {name}")
            continue
        inst = tools.create_asset(name, OUTLINE_DIR,
                                  unreal.MaterialInstanceConstant,
                                  unreal.MaterialInstanceConstantFactoryNew())
        if inst is None:
            log(f"FAIL create {name}")
            continue
        unreal.MaterialEditingLibrary.set_material_instance_parent(inst, parent)

        # Set by parameter name only if the master actually declares it.
        # Writing an unknown name raises; skip quietly and report.
        applied, skipped = [], []
        me = unreal.MaterialEditingLibrary
        for pname, val in list(overrides.items()) + [("Line Width", line_width)]:
            try:
                if isinstance(val, bool):
                    me.set_material_instance_static_switch_parameter_value(
                        inst, pname, val)
                else:
                    me.set_material_instance_scalar_parameter_value(
                        inst, pname, float(val))
                applied.append(f"{pname}={val}")
            except Exception as exc:
                skipped.append(f"{pname} ({str(exc)[:40]})")

        unreal.EditorAssetLibrary.save_loaded_asset(inst, only_if_is_dirty=False)
        made.append(path)
        log(f"OK {name} LineWidth={line_width} applied={applied} skipped={skipped}")

    return made


def discover_master_params():
    """Read the hull master's parameter names so instance overrides are real."""
    parent = unreal.load_asset(HULL_MASTER) or unreal.load_asset(HULL_MASTER_ALT)
    if parent is None:
        return {}
    names = {}
    try:
        for e in unreal.MaterialEditingLibrary.get_material_expressions(parent) or []:
            t = type(e).__name__
            if "Parameter" in t:
                try:
                    names[str(e.get_editor_property("parameter_name"))] = t
                except Exception:
                    pass
    except Exception as exc:
        log(f"param scan warning: {exc}")
    return names


def verify(paths, master_params):
    out = {"master_params": master_params, "instances": {}, "ok": False}
    parent = unreal.load_asset(HULL_MASTER) or unreal.load_asset(HULL_MASTER_ALT)
    out["master_path"] = parent.get_path_name() if parent else None
    out["master_is_material"] = type(parent).__name__ if parent else None

    good = 0
    for p in paths:
        name = p.rsplit("/", 1)[-1]
        inst = unreal.load_asset(p)
        row = {"loads": inst is not None}
        if inst:
            par = inst.get_editor_property("parent")
            row["parent"] = par.get_name() if par else None
            row["parent_ok"] = row["parent"] == "M_Hull_Outline"
            spec = next((s for s in SPECS
                         if s[0] == name.rsplit(".", 1)[0]), None)
            if spec:
                want_lw = spec[1]
                try:
                    got = unreal.MaterialEditingLibrary\
                        .get_material_instance_scalar_parameter_value(
                            inst, "Line Width")
                    row["line_width"] = float(got)
                    row["line_width_ok"] = abs(float(got) - want_lw) < 1e-4
                except Exception as exc:
                    row["line_width"] = f"err {str(exc)[:50]}"
                    row["line_width_ok"] = False
            row["ok"] = row["parent_ok"] and row.get("line_width_ok", False)
            good += 1 if row["ok"] else 0
        out["instances"][name] = row

    # The PPV stack must be untouched.
    frozen = "/Game/Melodia/_PROJECT/04_Materials/PostProcess/Frozen"
    out["ppv_frozen_intact"] = all(
        unreal.EditorAssetLibrary.does_asset_exist(
            f"{frozen}/MI_{n}")
        for n in ("StorybookOutline_Frozen", "MeluColorGrade_Frozen",
                  "MelodiaInk_Frozen", "StarryNight_Frozen"))

    out["ok"] = (good == len(paths) and out["ppv_frozen_intact"])
    log(f"VERIFY: {good}/{len(paths)} instances ok, "
        f"ppv_frozen_intact={out['ppv_frozen_intact']}")
    return out


def main():
    log("=" * 60)
    log("HULL OUTLINE SETUP (per-mesh inverted hull, PPV untouched)")
    log("=" * 60)

    report = {"phase": "setup", "errors": []}

    try:
        params = discover_master_params()
        log(f"master parameters: {sorted(params.keys())}")
        report["master_params"] = params

        paths = build_instances()
        report["built"] = paths
        report["verify"] = verify(paths, params)
    except Exception as exc:
        report["errors"].append(str(exc))
        log(f"ERROR: {exc}")

    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    log(f"report -> {REPORT}")
    return 0


if __name__ == "__main__":
    main()
