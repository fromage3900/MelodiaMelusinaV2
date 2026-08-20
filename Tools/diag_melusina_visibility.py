# -*- coding: utf-8 -*-
"""Diagnose why Melusina vanishes in EEVEE renders."""
from __future__ import annotations

import json
from pathlib import Path

import bpy

OUT = Path(r"G:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\melusina_visibility_diag.json")


def main() -> int:
    mel = bpy.data.objects.get("Melusina")
    info: dict = {"melusina": None, "strands": [], "camera": None, "view_layers": []}
    if mel:
        info["melusina"] = {
            "hide_render": mel.hide_render,
            "hide_viewport": mel.hide_viewport,
            "hide_get": mel.hide_get(),
            "visible_get": mel.visible_get(),
            "visible_camera": getattr(mel, "visible_camera", None),
            "is_holdout": getattr(mel, "is_holdout", None),
            "is_shadow_catcher": getattr(mel, "is_shadow_catcher", None),
            "type": mel.type,
            "users_collection": [c.name for c in mel.users_collection],
            "materials": [],
            "modifiers": [m.type for m in mel.modifiers],
        }
        for s in mel.material_slots:
            mat = s.material
            entry = {"slot": s.name, "mat": mat.name if mat else None}
            if mat and mat.use_nodes and mat.node_tree:
                outs = [n for n in mat.node_tree.nodes if n.type == "OUTPUT_MATERIAL"]
                entry["has_output"] = bool(outs)
                entry["node_types"] = sorted({n.type for n in mat.node_tree.nodes})
                # surface link?
                if outs:
                    links = list(outs[0].inputs["Surface"].links)
                    entry["surface_linked"] = bool(links)
                    if links:
                        entry["surface_from"] = links[0].from_node.type
            info["melusina"]["materials"].append(entry)

    for name in ("Hair Strand.002", "Hair Strand.004", "Hair Strand.007"):
        o = bpy.data.objects.get(name)
        if not o:
            continue
        info["strands"].append(
            {
                "name": name,
                "hide_render": o.hide_render,
                "visible_camera": getattr(o, "visible_camera", None),
                "is_holdout": getattr(o, "is_holdout", None),
                "materials": [s.material.name if s.material else None for s in o.material_slots],
            }
        )

    cam = bpy.context.scene.camera or bpy.data.objects.get("Cam_Beauty")
    if cam and cam.data:
        info["camera"] = {
            "name": cam.name,
            "loc": list(cam.location),
            "clip_start": cam.data.clip_start,
            "clip_end": cam.data.clip_end,
            "lens": cam.data.lens,
            "type": cam.data.type,
        }

    for vl in bpy.context.scene.view_layers:
        excluded = []
        # layer_collection tree
        def walk(lc, path=""):
            p = f"{path}/{lc.name}" if path else lc.name
            if lc.exclude:
                excluded.append(p)
            for child in lc.children:
                walk(child, p)

        walk(vl.layer_collection)
        info["view_layers"].append({"name": vl.name, "excluded": excluded[:80]})

    # Try forcing camera visibility + no holdout
    fixed = []
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        n = o.name.lower()
        if "melusina" in n or o.name.startswith("Hair Strand") or o.name.startswith("Retopo_"):
            if getattr(o, "visible_camera", True) is False:
                o.visible_camera = True
                fixed.append(o.name + ":visible_camera")
            if getattr(o, "is_holdout", False):
                o.is_holdout = False
                fixed.append(o.name + ":holdout_off")
    info["fixed"] = fixed

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(info, indent=2)[:4000])
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
