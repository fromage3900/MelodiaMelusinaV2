# -*- coding: utf-8 -*-
"""Force Melusina visible_get True — walk parents + layer collections."""
from __future__ import annotations

import json
from pathlib import Path

import bpy

OUT = Path(r"G:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\melusina_force_visible.json")


def unexclude_layer_collections_for(obj_name: str) -> list[str]:
    touched = []
    obj = bpy.data.objects.get(obj_name)
    if not obj:
        return touched
    target_colls = {c.name for c in obj.users_collection}

    def walk(lc):
        if lc.collection.name in target_colls or any(
            n in lc.collection.name.lower() for n in ("melusina", "character", "asset_melusina", "rig")
        ):
            if lc.exclude:
                lc.exclude = False
                touched.append(f"unexclude:{lc.collection.name}")
            if hasattr(lc, "hide_viewport") and lc.hide_viewport:
                lc.hide_viewport = False
                touched.append(f"layer_show:{lc.collection.name}")
        for child in lc.children:
            walk(child)

    for vl in bpy.context.scene.view_layers:
        walk(vl.layer_collection)
    return touched


def main() -> int:
    mel = bpy.data.objects.get("Melusina")
    report = {"steps": [], "before": None, "after": None, "parent": None}
    if not mel:
        raise SystemExit("no Melusina")

    report["before"] = {
        "visible_get": mel.visible_get(),
        "hide_get": mel.hide_get(),
        "hide_render": mel.hide_render,
        "collections": [c.name for c in mel.users_collection],
        "parent": mel.parent.name if mel.parent else None,
    }
    report["parent"] = mel.parent.name if mel.parent else None

    # Unhide object + ancestors
    cur = mel
    while cur:
        cur.hide_set(False)
        cur.hide_viewport = False
        cur.hide_render = False
        if hasattr(cur, "visible_camera"):
            cur.visible_camera = True
        report["steps"].append(f"show_obj:{cur.name}")
        cur = cur.parent

    # Unhide every collection in the blend that smells like character
    for c in bpy.data.collections:
        nl = c.name.lower()
        if any(k in nl for k in ("melusina", "character", "asset_melusina", "grp_rig", "hair")):
            c.hide_render = False
            c.hide_viewport = False
            report["steps"].append(f"show_coll:{c.name}")

    report["steps"].extend(unexclude_layer_collections_for("Melusina"))
    for name in ("Hair Strand.002", "Hair Strand.004", "Hair Strand.007"):
        report["steps"].extend(unexclude_layer_collections_for(name))
        o = bpy.data.objects.get(name)
        if o:
            o.hide_set(False)
            o.hide_render = False
            o.hide_viewport = False

    # Link Melusina into scene collection if somehow orphaned from view
    scene_coll = bpy.context.scene.collection
    if mel.name not in scene_coll.objects:
        try:
            scene_coll.objects.link(mel)
            report["steps"].append("linked_to_scene_collection")
        except RuntimeError:
            report["steps"].append("already_in_hierarchy")

    report["after"] = {
        "visible_get": mel.visible_get(),
        "hide_get": mel.hide_get(),
        "hide_render": mel.hide_render,
        "collections": [c.name for c in mel.users_collection],
    }

    # Also dump layer exclude tree for character_grp_rig
    excludes = []

    def walk(lc, path=""):
        p = f"{path}/{lc.name}"
        if lc.exclude or (hasattr(lc, "hide_viewport") and lc.hide_viewport):
            excludes.append({"path": p, "exclude": lc.exclude, "hide_viewport": getattr(lc, "hide_viewport", None)})
        for child in lc.children:
            walk(child, p)

    for vl in bpy.context.scene.view_layers:
        walk(vl.layer_collection)
    report["excluded_or_hidden_layers"] = excludes[:100]

    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2)[:5000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
