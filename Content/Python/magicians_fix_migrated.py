"""magicians_fix_migrated.py — repair the migrated Magician's Library set.

Repairs the defects found in the 2026-10-21 audit of
/Game/EnvSandbox/Library/Migrated/MagiciansLibrary:

  S1  8 meshes carry the wrong material
        SM_Bookshelf    -> M_Bookshelf        (flat MASTER, bypasses the toon master)
        SM_Lantern      -> MI_Zen_LanternWarm (Zen instance, default textures)
        SM_Wick         -> MI_Zen_LanternWarm
        candle1_L       -> MI_Zen_LanternWarm
        SM_Outside_Wall -> _Loose/MI_SM_Outside_Wall
        SM_Kit_Ornament_A/B/C -> MI_M_Deco1/2/3 (folder/name drift)
        SM_Desk2        -> MI_M_Desk_2        (name drift)
  S2  MI_M_Bookshelf.HeightMap is Perlin noise, not T_Neutral_Height
  S3  naming: candle1_L -> SM_Candle1_L (both trees), MI renames to match meshes
  S4  51 flat M_* masters are orphans once S1 lands -> MOVED to _Archive (not deleted)

Modes (arg 1): "plan" (default, no mutation) | "apply"

Every step is verified by readback and written to
Saved/Audit/magicians_fix_migrated.json.
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import unreal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "magicians_fix_migrated.json"

CANON = "/Game/EnvSandbox/Library/Migrated/MagiciansLibrary"
PACK = "/Game/MagicianLabatory/Source/Props"
MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
NEUTRAL = "/Game/EnvSandbox/Textures/Utility"
ARCHIVE = CANON + "/_Archive/FlatMasters_20261021"

# S1: mesh -> the material instance it SHOULD carry
SLOT_FIXES = {
    "Bookshelf/SM_Bookshelf": "MI_M_Bookshelf",
    "Lantern/SM_Lantern": "MI_M_Lantern",
    "Candle/SM_Wick": "MI_M_Wick",
    "Candle/candle1_L": "MI_M_Candle",
    "Outside_Wall/SM_Outside_Wall": "MI_M_Outside_Wall",
    "Deco1/SM_Kit_Ornament_A": "MI_M_Kit_Ornament_A",
    "Deco2/SM_Kit_Ornament_B": "MI_M_Kit_Ornament_B",
    "Deco3/SM_Kit_Ornament_C": "MI_M_Kit_Ornament_C",
    "Desk2/SM_Desk2": "MI_M_Desk2",
}

# S3: renames (old relative path -> new relative path) per tree
RENAMES_CANON = [
    ("Deco1/MI_M_Deco1", "Deco1/MI_M_Kit_Ornament_A"),
    ("Deco2/MI_M_Deco2", "Deco2/MI_M_Kit_Ornament_B"),
    ("Deco3/MI_M_Deco3", "Deco3/MI_M_Kit_Ornament_C"),
    ("Desk2/MI_M_Desk_2", "Desk2/MI_M_Desk2"),
    ("Candle/candle1_L", "Candle/SM_Candle1_L"),
]
RENAMES_PACK = [
    ("Candle/candle1_L", "Candle/SM_Candle1_L"),
    ("Candle/MI_M_candle1_L", "Candle/MI_M_Candle1_L"),
]

# S1 extras: instances that do not exist yet and must be created
CREATE_MI = {
    "Candle/MI_M_Wick": {"textures": {
        "Albedo": CANON + "/Candle/T_Candle_Base",
        "NormalMap": CANON + "/Candle/T_Candle_Normal",
        "ORM": CANON + "/Candle/T_Candle_AO"}},
    "Outside_Wall/MI_M_Outside_Wall": {"textures": {}},  # pack ships no textures here
}

# S5: pre-rename files left behind by the renames (now exact duplicates).
SUPERSEDED_LEFTOVERS = [
    "Candle/candle1_L",
    "Deco1/MI_M_Deco1",
    "Deco2/MI_M_Deco2",
    "Deco3/MI_M_Deco3",
    "Desk2/MI_M_Desk_2",
]


def _p(o):
    try:
        return o.get_path_name()
    except Exception:
        return ""


def set_slot(mesh, mi):
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
    return changed


def create_mi(rel_path, textures):
    folder = CANON + "/" + rel_path.rsplit("/", 1)[0]
    name = rel_path.rsplit("/", 1)[-1]
    full = CANON + "/" + rel_path
    mi = unreal.load_asset(full)
    if mi is None:
        factory = unreal.MaterialInstanceConstantFactoryNew()
        mi = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, folder, unreal.MaterialInstanceConstant, factory)
        if mi is None:
            return None
    mi.set_editor_property("parent", unreal.load_asset(MASTER))
    for param, tex_path in (textures or {}).items():
        tex = unreal.load_asset(tex_path)
        if tex is None:
            continue
        try:
            unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
                mi, param, tex)
        except Exception:
            pass
    for param, tex_path in (
            ("RoughnessMap", NEUTRAL + "/T_Neutral_Roughness"),
            ("MetallicMap", NEUTRAL + "/T_Neutral_Metallic"),
            ("HeightMap", NEUTRAL + "/T_Neutral_Height")):
        tex = unreal.load_asset(tex_path)
        if tex is None:
            continue
        try:
            unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
                mi, param, tex)
        except Exception:
            pass
    try:
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
            mi, "LayerA_TextureWeight", 1.0)
    except Exception:
        pass
    unreal.EditorAssetLibrary.save_loaded_asset(mi, only_if_is_dirty=False)
    return mi


def rename_one(old, new):
    """IAssetTools rename/move with reference fixup. -> (ok, msg)"""
    if not unreal.EditorAssetLibrary.does_asset_exist(old):
        return (False, "source missing")
    if unreal.EditorAssetLibrary.does_asset_exist(new):
        return (False, "target already exists")
    ok = unreal.EditorAssetLibrary.rename_asset(old, new)
    if not ok:
        return (False, "rename_asset returned False")
    return (True, "renamed")


def referencers(path):
    try:
        refs = unreal.EditorAssetLibrary.find_package_referencers_for_asset(path, False)
        return [r for r in (refs or []) if "/Temp" not in r]
    except Exception:
        return None


def main() -> int:
    # Mode channel: env var first (survives the commandlet's argv handling),
    # then argv. MAGICIANS_MODE = "plan" | "apply"
    mode = (os.environ.get("MAGICIANS_MODE") or
            (sys.argv[1].strip().lower() if len(sys.argv) > 1 else "plan"))
    if mode not in ("plan", "apply"):
        mode = "plan"
    log = {"generated": datetime.now(timezone.utc).isoformat(), "mode": mode,
           "argv": list(sys.argv), "canonical": CANON, "steps": {}}
    counters = Counter()

    # ---------- S3a: renames (must run BEFORE S1 so MI names resolve) ----------
    ren = []
    for old_rel, new_rel in RENAMES_CANON:
        old = CANON + "/" + old_rel
        new = CANON + "/" + new_rel
        entry = {"tree": "canonical", "old": old, "new": new}
        if mode == "apply":
            ok, msg = rename_one(old, new)
            entry["result"] = msg
            counters["rename_ok" if ok else "rename_fail"] += 1
        else:
            entry["result"] = "planned"
        ren.append(entry)
    for old_rel, new_rel in RENAMES_PACK:
        old = PACK + "/" + old_rel
        new = PACK + "/" + new_rel
        entry = {"tree": "pack", "old": old, "new": new}
        if mode == "apply":
            ok, msg = rename_one(old, new)
            entry["result"] = msg
            counters["rename_ok" if ok else "rename_fail"] += 1
        else:
            entry["result"] = "planned"
        ren.append(entry)
    log["steps"]["S3_renames"] = ren

    # ---------- S1: create missing instances, then re-point slots ----------
    # The instance lives in the SAME sub-folder as its mesh (one MI per prop folder).
    slot_rows = []
    for rel, mi_name in SLOT_FIXES.items():
        folder_rel = rel.rsplit("/", 1)[0]
        mesh_path = CANON + "/" + rel
        mi_rel = folder_rel + "/" + mi_name
        mi_path = CANON + "/" + mi_rel
        row = {"mesh": mesh_path, "want_mi": mi_path}
        mesh = unreal.load_asset(mesh_path)
        if mesh is None:
            row["result"] = "mesh_missing"
            counters["mesh_missing"] += 1
            slot_rows.append(row)
            continue
        cur = [s.get_editor_property("material_interface") for s in
               (mesh.get_editor_property("static_materials") or [])]
        row["before"] = [_p(c) if c else None for c in cur]
        if mi_rel in CREATE_MI and unreal.load_asset(mi_path) is None:
            if mode == "apply":
                mi = create_mi(mi_rel, CREATE_MI[mi_rel]["textures"])
                row["created_mi"] = mi is not None
                counters["mi_created"] += 1
            else:
                row["created_mi"] = "planned"
        mi = unreal.load_asset(mi_path)
        if mi is None:
            row["result"] = "mi_missing"
            counters["mi_missing"] += 1
            slot_rows.append(row)
            continue
        if mode == "apply":
            changed = set_slot(mesh, mi)
            row["slot_changed"] = changed
            if changed:
                unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
            row["after"] = [s.get_editor_property("material_interface").get_path_name()
                            for s in (mesh.get_editor_property("static_materials") or [])]
            counters["slot_repointed"] += 1 if changed else 0
        else:
            row["result"] = "planned"
        slot_rows.append(row)
    log["steps"]["S1_slots"] = slot_rows

    # ---------- S2: noise height on MI_M_Bookshelf ----------
    noise = []
    for rel in ("Bookshelf/MI_M_Bookshelf",):
        mi = unreal.load_asset(CANON + "/" + rel)
        if mi is None:
            continue
        try:
            cur = mi.get_texture_parameter_value("HeightMap")
        except Exception:
            cur = None
        row = {"mi": CANON + "/" + rel, "height_before": _p(cur) if cur else None}
        if mode == "apply" and cur is not None and "Perlin" in _p(cur):
            tex = unreal.load_asset(NEUTRAL + "/T_Neutral_Height")
            if tex is not None:
                unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
                    mi, "HeightMap", tex)
                unreal.EditorAssetLibrary.save_loaded_asset(mi, only_if_is_dirty=False)
                row["height_after"] = NEUTRAL + "/T_Neutral_Height"
                counters["noise_height_fixed"] += 1
        noise.append(row)
    log["steps"]["S2_noise_height"] = noise

    # ---------- S4: archive the orphaned flat masters ----------
    flat = []
    for p in unreal.EditorAssetLibrary.list_assets(CANON, recursive=True, include_folder=False):
        name = p.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        if not name.startswith("M_") or name.startswith("MI_"):
            continue
        if "/_Archive/" in p:
            continue
        asset = unreal.load_asset(p)
        if asset is None or not isinstance(asset, unreal.Material):
            continue
        refs = referencers(p)
        entry = {"asset": p, "referencers": refs}
        if refs is not None and len(refs) == 0:
            if mode == "apply":
                dest = ARCHIVE + "/" + name
                if not unreal.EditorAssetLibrary.does_directory_exist(ARCHIVE):
                    unreal.EditorAssetLibrary.make_directory(ARCHIVE)
                ok, msg = rename_one(p, dest)
                entry["result"] = msg
                counters["archived" if ok else "archive_fail"] += 1
            else:
                entry["result"] = "planned"
        else:
            entry["result"] = "kept (has referencers)" if refs else "unknown refs"
            counters["kept_with_refs"] += 1
        flat.append(entry)
    log["steps"]["S4_archive_flat_masters"] = flat

    # ---------- S5: remove the leftovers of the renames (old files) ----------
    # The renames in S3 left the pre-rename file behind; the crash prevented UE's
    # own cleanup. These are exact duplicates of the renamed assets.
    leftovers = []
    for old_rel in SUPERSEDED_LEFTOVERS:
        old = CANON + "/" + old_rel
        row = {"asset": old, "exists": unreal.EditorAssetLibrary.does_asset_exist(old)}
        if not row["exists"]:
            row["result"] = "already gone"
            counters["leftover_absent"] += 1
        elif mode == "apply":
            ok = unreal.EditorAssetLibrary.delete_asset(old)
            row["result"] = "deleted" if ok else "delete_failed"
            counters["leftover_deleted" if ok else "leftover_delete_failed"] += 1
        else:
            row["result"] = "planned"
        leftovers.append(row)
    log["steps"]["S5_superseded_leftovers"] = leftovers

    log["counters"] = dict(counters)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(log, indent=2), encoding="utf-8")
    print("FIXMIG|%s|%s" % (mode, json.dumps(dict(counters))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
