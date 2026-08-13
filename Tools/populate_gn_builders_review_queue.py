# -*- coding: utf-8 -*-
"""Populate Review_Queue with all Melodia GN builders (RQ_MEL_* children).

Each builder gets a child collection under Review_Queue containing one mesh
with a Geometry Nodes modifier wired to that builder's node group — so
Stage Prev/Solo/Next can cycle the full catalog.

Run:
  $env:MELODIA_ALLOW_STAGE_SAVE=1
  blender "<stage>.blend" -b -P Tools/populate_gn_builders_review_queue.py -- --clear --save

Flags:
  --clear       Remove prior RQ_MEL_* children only
  --clear-all   Remove ALL Review_Queue children (destructive)
  --save        Save blend (requires MELODIA_ALLOW_STAGE_SAVE=1 for portfolio stages)
  --limit N     Only first N builders (debug)
  --sidecar     Save to KitbashExport/OrnamentMusic_WIP/ instead of overwriting stage
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy

_TOOLS = Path(__file__).resolve().parent
ROOT = _TOOLS.parent
DEPLOY = ROOT / "deploy"
sys.path.insert(0, str(_TOOLS))
sys.path.insert(0, str(DEPLOY))

from melodia_stage_paths import (  # noqa: E402
    is_portfolio_stage_path,
    resolve_stage_blend,
    stage_save_allowed,
)

RQ_NAME = "Review_Queue"
PREFIX = "RQ_MEL_"
AUDIT = ROOT / "Saved" / "Audit" / "gn_builders_review_queue_sync.json"
SIDECAR_DIR = ROOT / "KitbashExport" / "OrnamentMusic_WIP"


def log(msg: str) -> None:
    print(f"[gn-rq] {msg}", flush=True)


def _load_monolith():
    mono_path = DEPLOY / "surreal_architecture_gen.py"
    if not mono_path.is_file():
        raise SystemExit(f"Missing monolith: {mono_path}")
    sys.modules.pop("surreal_architecture_gen", None)
    spec = importlib.util.spec_from_file_location(
        "surreal_architecture_gen",
        str(mono_path),
        submodule_search_locations=[],
    )
    mono = importlib.util.module_from_spec(spec)
    sys.modules["surreal_architecture_gen"] = mono
    assert spec.loader is not None
    spec.loader.exec_module(mono)
    try:
        mono.register()
    except Exception as exc:
        log(f"monolith register warning: {exc}")
    return mono


def ensure_review_queue() -> bpy.types.Collection:
    rq = bpy.data.collections.get(RQ_NAME)
    if rq is None:
        rq = bpy.data.collections.new(RQ_NAME)
        bpy.context.scene.collection.children.link(rq)
    return rq


def clear_rq_mel(rq: bpy.types.Collection, clear_all: bool = False) -> int:
    removed = 0
    for child in list(rq.children):
        if clear_all or child.name.startswith(PREFIX):
            for obj in list(child.objects):
                bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(child)
            removed += 1
    return removed


def _builder_result_tree(result):
    if isinstance(result, (tuple, list)):
        return result[0]
    return result


def build_one(tree_name: str, builder, index: int, rq: bpy.types.Collection) -> dict:
    col_name = f"{PREFIX}{tree_name}"
    # Blender collection names max ~63; keep unique
    if len(col_name) > 60:
        col_name = f"{PREFIX}{index:03d}_{tree_name[-40:]}"
    col = bpy.data.collections.new(col_name)
    rq.children.link(col)

    mesh = bpy.data.meshes.new(f"{tree_name}_mesh")
    # Minimal seed geometry (builders typically replace/expand from group input)
    mesh.from_pydata(
        [(-0.05, -0.05, 0), (0.05, -0.05, 0), (0.05, 0.05, 0), (-0.05, 0.05, 0)],
        [],
        [(0, 1, 2, 3)],
    )
    obj = bpy.data.objects.new(tree_name[:60], mesh)
    col.objects.link(obj)
    obj.location = (index * 0.01, 0.0, 0.0)  # slight offset; solo cycle hides siblings

    try:
        result = builder()
        tree = _builder_result_tree(result)
        if tree is None:
            raise RuntimeError("builder returned None")
        # Prefer canonical name
        if getattr(tree, "name", None) and tree.name != tree_name:
            try:
                tree.name = tree_name
            except Exception:
                pass
        mod = obj.modifiers.new(name=tree_name[:60], type="NODES")
        mod.node_group = tree
        return {"name": tree_name, "status": "ok", "collection": col.name, "nodes": len(tree.nodes)}
    except Exception as exc:
        obj["mel_gn_build_error"] = str(exc)[:200]
        return {"name": tree_name, "status": "fail", "collection": col.name, "error": str(exc)[:200]}


def soft_solo_first(rq: bpy.types.Collection) -> None:
    """Hide viewport on all RQ children except the first (soft solo)."""
    children = list(rq.children)
    for i, child in enumerate(children):
        hide = i != 0
        try:
            child.hide_viewport = False  # never hard-lock collection
        except Exception:
            pass
        # Soft: use layer collection if available
        try:
            from surreal_arch.stage_visibility import find_layer_collection

            lc = find_layer_collection(bpy.context.view_layer.layer_collection, child.name)
            if lc is not None:
                lc.hide_viewport = hide
                lc.exclude = False
        except Exception:
            for obj in child.objects:
                obj.hide_viewport = hide
                obj.hide_render = hide


def apply_review_preset() -> None:
    try:
        from surreal_arch.stage_visibility import apply_stage_preset
        apply_stage_preset("review_all")
        log("applied stage preset review_all")
        return
    except Exception as exc:
        log(f"apply_stage_preset skipped: {exc}")
    try:
        if hasattr(bpy.ops.surreal_arch, "set_stage_visibility_preset"):
            bpy.ops.surreal_arch.set_stage_visibility_preset(preset="review_all")
            log("applied stage preset via operator")
    except Exception as exc:
        log(f"stage preset skipped: {exc}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    else:
        argv = []
    ap = argparse.ArgumentParser()
    ap.add_argument("--clear", action="store_true")
    ap.add_argument("--clear-all", action="store_true")
    ap.add_argument("--save", action="store_true")
    ap.add_argument("--sidecar", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    return ap.parse_args(argv)


def main() -> int:
    args = parse_args(sys.argv)
    _load_monolith()

    from surreal_arch.melodia_gn.core import GROUP_BUILDERS, GROUP_METADATA

    builders = sorted(GROUP_BUILDERS.items())
    if args.limit and args.limit > 0:
        builders = builders[: args.limit]

    rq = ensure_review_queue()
    if args.clear or args.clear_all:
        n = clear_rq_mel(rq, clear_all=args.clear_all)
        log(f"cleared {n} Review_Queue children")

    results = []
    ok = fail = 0
    for i, (name, builder) in enumerate(builders):
        log(f"[{i + 1}/{len(builders)}] {name}")
        row = build_one(name, builder, i, rq)
        results.append(row)
        if row["status"] == "ok":
            ok += 1
        else:
            fail += 1
            log(f"  FAIL {name}: {row.get('error', '')[:120]}")

    soft_solo_first(rq)
    apply_review_preset()

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "blend": bpy.data.filepath or "(unsaved)",
        "total": len(builders),
        "ok": ok,
        "fail": fail,
        "prefix": PREFIX,
        "builders": results,
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    log(f"wrote {AUDIT}")
    log(f"SUMMARY ok={ok} fail={fail} total={len(builders)}")

    if args.save or args.sidecar:
        path = Path(bpy.data.filepath) if bpy.data.filepath else resolve_stage_blend()
        if args.sidecar:
            SIDECAR_DIR.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = SIDECAR_DIR / f"Melodia_GN_ReviewQueue_{stamp}.blend"
        elif is_portfolio_stage_path(path) and not stage_save_allowed():
            log("REFUSED save: set MELODIA_ALLOW_STAGE_SAVE=1 to overwrite portfolio stage")
            return 2
        bpy.ops.wm.save_as_mainfile(filepath=str(path))
        log(f"saved {path}")
        report["saved"] = str(path)
        AUDIT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
