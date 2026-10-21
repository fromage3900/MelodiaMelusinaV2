"""magicians_neutral_height.py — kill the remaining Perlin-noise height maps.

The 2026-08-14 `route_neutral_maps` pass routed every textured MI onto
T_Neutral_* utility maps, but four Magician's Library instances kept an abstract
Perlin height map, and one mesh still pointed at a shared Zen instance.

Steps:
  N1  re-point SM_Candle1_L -> MI_M_Candle (the renamed candle mesh reverted
      to the Zen instance when the pre-rename file was restored from Perforce)
  N2  any MI in either Magician tree whose HeightMap resolves to a Perlin /
      abstract noise texture is re-routed to T_Neutral_Height
  N3  report (and only fix) the shared Zen instance if nothing outside the
      Magician trees references it

Mode: MAGICIANS_MODE=apply (default plan). Writes Saved/Audit/magicians_neutral_height.json
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import unreal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "magicians_neutral_height.json"

CANON = "/Game/EnvSandbox/Library/Migrated/MagiciansLibrary"
PACK = "/Game/MagicianLabatory/Source"
NEUTRAL_HEIGHT = "/Game/EnvSandbox/Textures/Utility/T_Neutral_Height"
ZEN_INSTANCE = "/Game/EnvSandbox/Materials/Instances/Environment/Zen/MI_Zen_LanternWarm"

# noise textures that must never be a HeightMap
NOISE_MARKERS = ("Perlin", "sbs_-_noise", "Cracks", "Gradient", "Marble", "Abstract")


def _p(o):
    try:
        return o.get_path_name()
    except Exception:
        return ""


def is_noise(path):
    return any(m.lower() in (path or "").lower() for m in NOISE_MARKERS)


def main() -> int:
    mode = (os.environ.get("MAGICIANS_MODE") or
            (sys.argv[1].strip().lower() if len(sys.argv) > 1 else "plan"))
    if mode not in ("plan", "apply"):
        mode = "plan"
    log = {"generated": datetime.now(timezone.utc).isoformat(), "mode": mode, "steps": {}}

    # ---------- N1: re-point the renamed candle mesh ----------
    n1 = []
    for rel, mi_name in (("Candle/SM_Candle1_L", "MI_M_Candle"),
                          ("Candle/SM_Wick", "MI_M_Wick")):
        mesh = unreal.load_asset("%s/%s" % (CANON, rel))
        mi = unreal.load_asset("%s/Candle/%s" % (CANON, mi_name))
        row = {"mesh": "%s/%s" % (CANON, rel), "want": "%s/Candle/%s" % (CANON, mi_name)}
        if mesh is None:
            row["result"] = "mesh_missing"
        elif mi is None:
            row["result"] = "mi_missing"
        else:
            slots = list(mesh.get_editor_property("static_materials") or [])
            changed = False
            for s in slots:
                cur = s.get_editor_property("material_interface")
                if cur is None or cur.get_path_name() == mi.get_path_name():
                    continue
                s.set_editor_property("material_interface", mi)
                changed = True
            if changed:
                mesh.set_editor_property("static_materials", slots)
                if mode == "apply":
                    unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
            row["result"] = "repointed" if changed else "already_correct"
        n1.append(row)
    log["steps"]["N1_repoint"] = n1

    # ---------- N2: neutralise noise height maps in both trees ----------
    n2 = []
    for root in (CANON, PACK):
        if not unreal.EditorAssetLibrary.does_directory_exist(root):
            continue
        for p in unreal.EditorAssetLibrary.list_assets(root, recursive=True, include_folder=False):
            name = p.rsplit("/", 1)[-1].rsplit(".", 1)[0]
            if not name.startswith("MI_"):
                continue
            mi = unreal.load_asset(p)
            if mi is None or not isinstance(mi, unreal.MaterialInstanceConstant):
                continue
            try:
                cur = mi.get_texture_parameter_value("HeightMap")
            except Exception:
                continue
            cur_path = _p(cur) if cur else None
            if not is_noise(cur_path):
                continue
            row = {"mi": p, "height_before": cur_path}
            if mode == "apply":
                tex = unreal.load_asset(NEUTRAL_HEIGHT)
                if tex is not None:
                    unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
                        mi, "HeightMap", tex)
                    unreal.EditorAssetLibrary.save_loaded_asset(mi, only_if_is_dirty=False)
                    row["height_after"] = NEUTRAL_HEIGHT
                    row["result"] = "fixed"
            else:
                row["result"] = "planned"
            n2.append(row)
    log["steps"]["N2_neutralise"] = n2

    # ---------- N3: the shared Zen instance ----------
    n3 = {"instance": ZEN_INSTANCE}
    zi = unreal.load_asset(ZEN_INSTANCE)
    if zi is None:
        n3["result"] = "not_found"
    else:
        try:
            cur = zi.get_texture_parameter_value("HeightMap")
            n3["height_before"] = _p(cur) if cur else None
        except Exception:
            n3["height_before"] = None
        try:
            refs = unreal.EditorAssetLibrary.find_package_referencers_for_asset(ZEN_INSTANCE, False)
            n3["referencers"] = sorted(r for r in (refs or []) if "/Temp" not in r)
        except Exception:
            n3["referencers"] = None
        outside = [r for r in (n3.get("referencers") or [])
                   if "MagiciansLibrary" not in r and "MagicianLabatory" not in r]
        n3["referencers_outside_magicians"] = outside
        if is_noise(n3.get("height_before")):
            if not outside:
                if mode == "apply":
                    tex = unreal.load_asset(NEUTRAL_HEIGHT)
                    if tex is not None:
                        unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
                            zi, "HeightMap", tex)
                        unreal.EditorAssetLibrary.save_loaded_asset(zi, only_if_is_dirty=False)
                        n3["result"] = "fixed"
                        n3["height_after"] = NEUTRAL_HEIGHT
                else:
                    n3["result"] = "planned"
            else:
                n3["result"] = "LEFT ALONE - used outside the Magician trees: %s" % outside
        else:
            n3["result"] = "already_clean"
    log["steps"]["N3_zen_instance"] = n3

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(log, indent=2), encoding="utf-8")
    print("NEUTRALHEIGHT|%s|repoint=%s|neutralised=%d|zen=%s" % (
        mode, [r.get("result") for r in n1], len(n2), n3.get("result")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
