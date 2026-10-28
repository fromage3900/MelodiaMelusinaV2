"""Master-spine layout batch executor - identity-preserving group/comment polish.

Run INSIDE the Unreal editor via Monolith editor_query(run_python, mode=execute_file):

    run_python execute_file C:/EnvironmentPortfolio/BS_GodFile/Tools/masters_spine_batch.py

Run target is read from Saved/Audit/MastersSpine_20261028/batch_run_target.json
({"target": "<MasterName>"}) so each invocation mutates exactly one master.

Per run:
  1. Sanity: expression count == canon spec expr_count_before.
  2. Backup duplicate -> Masters/_Backup/<Name>_PreSpinePolish_20261028 (saved separately).
  3. Apply spec group_allocation rewrites (renames + class-guarded by_param rules).
  4. Strip legacy 'MELODIA_COLUMN:' comment prefixes (no other comment edits).
  5. Save ONLY that master package; verify ungrouped-parameter count == 0.
  6. Write receipt JSON under Saved/Audit/MastersSpine_20261028/.

Never touches expression connections, default values, or the LandscapeLayerSample nodes
(they carry no parameter-group property).

Pre/polished receipts and the spec are the evidence chain for CURRENT_STATE.md.
"""
import gc
import json
import os
import unreal

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
AUDIT = os.path.join(ROOT, "Saved", "Audit", "MastersSpine_20261028")
SPEC_PATH = os.path.join(ROOT, "specs", "materials", "master_spine_canon.v1.json")
TARGET_PATH = os.path.join(AUDIT, "batch_run_target.json")

ASSETS = {
    "M_Master_Nikki_Landscape": "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape",
    "M_Master_Nikki": "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki",
    "M_Master_Toon_Universal": "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal",
    "M_Master_Toon_Character": "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Character",
    "M_Water_Oceanology_Melodia": "/Game/EnvSandbox/Materials/Masters/M_Water_Oceanology_Melodia",
    "M_Master_SDF_Toon": "/Game/EnvSandbox/Materials/Masters/SDF/M_Master_SDF_Toon",
}

WITH_GROUP_PROPERTIES = {
    "ScalarParameter", "VectorParameter", "TextureSampleParameter2D",
    "TextureSampleParameter2DArray", "TextureSampleParameterCube",
    "TextureObjectParameter", "StaticSwitchParameter", "CollectionParameter",
    "RuntimeVirtualTextureParameter", "FontParameter", "NamedRerouteDeclaration",
}

import io

with io.open(SPEC_PATH, "r", encoding="utf-8-sig") as f:
    SPEC = json.load(f)
with io.open(TARGET_PATH, "r", encoding="utf-8-sig") as f:
    TARGET = json.load(f)["target"]

ASSET_PATH = ASSETS[TARGET]
RULES = SPEC["group_allocation"][TARGET]
BACKUP_PATH = "/Game/EnvSandbox/Materials/Masters/_Backup/%s_PreSpinePolish_20261028" % TARGET


def short_class(expr):
    return str(expr.get_class().get_name()).replace("MaterialExpression", "")


def get_param(expr):
    try:
        return str(expr.get_editor_property("parameter_name"))
    except Exception:
        return None


def get_group(expr):
    try:
        return str(expr.get_editor_property("group"))
    except Exception:
        return None


def main():
    asset = unreal.load_asset(ASSET_PATH)
    if asset is None:
        raise RuntimeError("load failed: " + ASSET_PATH)
    exprs = unreal.MaterialEditingLibrary.get_material_expressions(asset)
    pre_count = len(exprs)
    expected = RULES["expr_count_before"]
    if pre_count != expected:
        raise RuntimeError("expr count %d != canon %d - abort" % (pre_count, expected))

    backup = None
    if not unreal.EditorAssetLibrary.does_asset_exist(BACKUP_PATH):
        backup = unreal.EditorAssetLibrary.duplicate_asset(ASSET_PATH, BACKUP_PATH)
        if not backup:
            src_file = ASSET_PATH.replace("/Game/", "Content/", 1).replace("/", os.sep) + ".uasset"
            dst_file = os.path.join(AUDIT, "backups", TARGET + "_PreSpinePolish_20261028.uasset")
            if not os.path.isdir(os.path.dirname(dst_file)):
                os.makedirs(os.path.dirname(dst_file))
            import shutil
            shutil.copyfile(src_file, dst_file)
            backup = "disk_copy:" + os.path.relpath(dst_file, ROOT)
            print("BACKUP fallback disk copy ->", dst_file)
    else:
        backup = "exists"

    renamed, allocated, skipped = 0, 0, []
    for e in exprs:
        cls = short_class(e)
        if cls not in WITH_GROUP_PROPERTIES:
            continue
        name = get_param(e)
        cur = get_group(e)
        new = None
        if cur in RULES["renames"]:
            new = RULES["renames"][cur]
        for rule in RULES["by_param"]:
            if rule.get("p") == name:
                guard = rule.get("c")
                if guard is None or guard == cls:
                    new = rule["g"]
                    break
        if new is None or new == cur:
            if name and not cur:
                skipped.append({"p": name, "c": cls})
            continue
        e.set_editor_property("group", new)
        if cur in RULES["renames"]:
            renamed += 1
        else:
            allocated += 1

    comments = []
    for e in exprs:
        if short_class(e) != "Comment":
            continue
        try:
            text = str(e.get_editor_property("text"))
        except Exception:
            continue
        if text.startswith("MELODIA_COLUMN:"):
            stripped = text[len("MELODIA_COLUMN:"):]
            e.set_editor_property("text", stripped)
            comments.append(stripped.splitlines()[0])

    unreal.EditorAssetLibrary.save_asset(ASSET_PATH, only_if_is_dirty=False)

    fresh = unreal.MaterialEditingLibrary.get_material_expressions(asset)
    post_count = len(fresh)
    ungrouped_after = []
    group_after = {}
    for e in fresh:
        cls = short_class(e)
        if cls not in WITH_GROUP_PROPERTIES:
            continue
        g = get_group(e)
        p = get_param(e)
        if p and (g in (None, "None")):
            ungrouped_after.append({"p": p, "c": cls})
        if p and g:
            group_after.setdefault(g, 0)
            group_after[g] += 1

    ok = post_count == pre_count and len(ungrouped_after) == 0 if RULES.get("expected_zero_ungrouped_after") else post_count == pre_count
    receipt = {
        "schema": "melodia.masters_spine_batch_receipt.v1",
        "when": "2026-10-28",
        "master": TARGET,
        "asset_path": ASSET_PATH,
        "backup_path": BACKUP_PATH,
        "expr_count_before": pre_count,
        "expr_count_after": post_count,
        "renamed_params": renamed,
        "allocated_params": allocated,
        "skipped_ungrouped_after": skipped,
        "ungrouped_after": ungrouped_after,
        "groups_after": group_after,
        "comment_headers": comments,
        "ok": bool(ok),
    }
    with open(os.path.join(AUDIT, "receipt_batch_%s.json" % TARGET), "w") as f:
        json.dump(receipt, f, indent=1)
    print("BATCH %s ok=%s touched=%d groups=%d" % (
        TARGET, receipt["ok"], renamed + allocated, len(group_after)))
    if ungrouped_after:
        print("UNGROUPED REMAINING:", json.dumps(ungrouped_after))
    gc.collect()


main()
