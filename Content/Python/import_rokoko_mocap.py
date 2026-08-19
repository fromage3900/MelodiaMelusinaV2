"""Import Rokoko FBX takes onto SK_MocapSource, then retarget to Melusina.

Drop exports in:
  Imports/Mocap/Rokoko/Inbox/*.fbx

Naming:
  MyIdle.fbx  ->  A_Src_Rokoko_MyIdle  ->  A_Mocap_Rokoko_MyIdle

Run in a live editor (MCP / py console) OR headless after import via Tools script:

  # Editor open — import only:
  #   import import_rokoko_mocap as m; m.main(import_only=True)

  # Editor CLOSED — full retarget of everything already imported as A_Src_*:
  #   Tools/run_headless_mocap_retarget.ps1

Bone-name gate:
  FBX must match SK_MocapSource_Skeleton. Export from Rokoko using the
  CharacterRef profile built from SK_MocapSource (see Docs/ROKOKO_MELUSINA_MOCAP.md).
  If bones differ, import still lands but retarget quality will be wrong —
  create RTG_Rokoko_to_Melusina instead of reusing RTG_Mocap_to_Melusina.
"""
from __future__ import annotations

import json
import os
import re
import unreal

# Content/Python → repo root (works on any clone; no G:\ hardcode)
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INBOX = os.path.join(_PROJECT_ROOT, "Imports", "Mocap", "Rokoko", "Inbox")
SRC_SKELETON = "/Game/Melodia/Mocap/Source/SK_MocapSource_Skeleton"
SRC_MESH = "/Game/Melodia/Mocap/Source/SK_MocapSource"
RTG = "/Game/Melodia/Mocap/RTG_Mocap_to_Melusina"
SRC_ANIM_DIR = "/Game/Melodia/Mocap/Source/Anims"
OUT_DIR = "/Game/Melodia/Characters/Melusina/Animations/Mocap"
TGT_MESH = "/Game/Melodia/Characters/Melusina/SK_Melusina"
TGT_SKEL = "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton"
REPORT = os.path.join(_PROJECT_ROOT, "Saved", "Melodia", "rokoko_import_report.json")

PREFIX = "A_Src_Rokoko_"


def _stem(path: str) -> str:
    name = os.path.splitext(os.path.basename(path))[0]
    name = re.sub(r"[^\w\-]+", "_", name).strip("_")
    return name or "Take"


def list_inbox_fbx() -> list[str]:
    if not os.path.isdir(INBOX):
        return []
    return sorted(
        os.path.join(INBOX, f)
        for f in os.listdir(INBOX)
        if f.lower().endswith(".fbx")
    )


def import_source_anim(fbx_path: str, dest_name: str) -> str | None:
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", fbx_path)
    task.set_editor_property("destination_path", SRC_ANIM_DIR)
    task.set_editor_property("destination_name", dest_name)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    task.set_editor_property("automated", True)

    options = unreal.FbxImportUI()
    skeleton = unreal.load_asset(SRC_SKELETON)
    options.set_editor_property("skeleton", skeleton)
    options.set_editor_property("import_mesh", False)
    options.set_editor_property("import_textures", False)
    options.set_editor_property("import_materials", False)
    options.set_editor_property("import_as_skeletal", True)
    options.set_editor_property("import_animations", True)
    src_mesh = unreal.load_asset(SRC_MESH)
    if src_mesh:
        options.set_editor_property("skeletal_mesh", src_mesh)
    task.set_editor_property("options", options)

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    imported = task.get_editor_property("imported_object_paths") or []
    if imported:
        unreal.log(f"[Rokoko] Imported {dest_name} -> {imported[0]}")
        return imported[0]
    unreal.log_warning(f"[Rokoko] No imported paths for {dest_name}")
    return None


def retarget_clip(src_path: str) -> dict:
    rtg = unreal.load_asset(RTG)
    sm = unreal.load_asset(SRC_MESH)
    tm = unreal.load_asset(TGT_MESH)
    tgt_skel = unreal.load_asset(TGT_SKEL)
    try:
        unreal.MelodiaAssetRepairLibrary.set_skeletal_mesh_skeleton(tm, tgt_skel)
        unreal.EditorAssetLibrary.save_asset(TGT_MESH, False)
    except Exception as exc:
        unreal.log_warning(f"[Rokoko] skeleton rebind skipped: {exc}")

    rtgc = unreal.IKRetargeterController.get_controller(rtg)
    rtgc.auto_map_chains(unreal.AutoMapChainType.EXACT, False)

    ad = unreal.EditorAssetLibrary.find_asset_data(src_path.split(".")[0])
    inp = unreal.IKRetargetBatchOperationInputs()
    inp.set_editor_property("assets_to_retarget", [ad])
    inp.set_editor_property("source_mesh", sm)
    inp.set_editor_property("target_mesh", tm)
    inp.set_editor_property("ik_retarget_asset", rtg)
    inp.set_editor_property("target_path", OUT_DIR)
    inp.set_editor_property("search", "A_Src_")
    inp.set_editor_property("replace", "A_Mocap_")
    inp.set_editor_property("overwrite_existing_files", True)
    inp.set_editor_property("use_source_path", False)
    created = unreal.IKRetargetBatchOperation().run_batch_retarget(inp) or []
    entry = {"src": src_path, "created": [], "ok": False, "skeleton": None}
    for c in created:
        obj = unreal.AssetRegistryHelpers.get_asset(c)
        if not obj:
            continue
        unreal.EditorAssetLibrary.save_loaded_asset(obj)
        sk = obj.get_editor_property("skeleton")
        entry["created"].append(str(c.package_name))
        entry["skeleton"] = sk.get_name() if sk else None
        entry["ok"] = sk is not None
    return entry


def main(import_only: bool = False, retarget: bool = True) -> dict:
    fbxs = list_inbox_fbx()
    report = {
        "inbox": INBOX,
        "fbx_count": len(fbxs),
        "imported": [],
        "retargeted": [],
        "warnings": [],
    }
    if not fbxs:
        msg = f"Inbox empty — drop Rokoko FBX into {INBOX}"
        unreal.log_warning(f"[Rokoko] {msg}")
        report["warnings"].append(msg)

    for fbx in fbxs:
        dest = PREFIX + _stem(fbx)
        path = import_source_anim(fbx, dest)
        report["imported"].append({"fbx": fbx, "dest": dest, "path": path})

    if import_only or not retarget:
        _write(report)
        return report

    # Retarget every A_Src_Rokoko_* currently in Source/Anims
    all_src = unreal.EditorAssetLibrary.list_assets(SRC_ANIM_DIR, False, False) or []
    rokoko_srcs = [
        a.split(".")[0]
        for a in all_src
        if a.split("/")[-1].split(".")[0].startswith(PREFIX)
    ]
    for sp in rokoko_srcs:
        try:
            report["retargeted"].append(retarget_clip(sp))
        except Exception as exc:
            report["retargeted"].append({"src": sp, "ok": False, "error": str(exc)[:200]})

    ok = sum(1 for r in report["retargeted"] if r.get("ok"))
    unreal.log(f"[Rokoko] Retarget {ok}/{len(report['retargeted'])} OK")
    _write(report)
    return report


def _write(report: dict) -> None:
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    unreal.log(f"[Rokoko] Wrote {REPORT}")


if __name__ == "__main__":
    main()
