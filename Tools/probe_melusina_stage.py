# -*- coding: utf-8 -*-
"""Probe Melodia stage: Melusina visibility + hair strands (bangs).

  blender KitbashExport/Melodia_Portfolio_Stage_v4.blend -b -P Tools/probe_melusina_stage.py
"""
from __future__ import annotations

import json
from pathlib import Path

import bpy

ROOT = Path(r"G:\EnvironmentPortfolio\BS_GodFile")
OUT = ROOT / "Saved" / "Audit" / "melusina_stage_probe.json"


def main() -> int:
    mel = bpy.data.collections.get("Asset_melusina")
    report = {
        "blend": bpy.data.filepath,
        "has_Asset_melusina": mel is not None,
        "cameras": [o.name for o in bpy.data.objects if o.type == "CAMERA"],
        "hair_strands": [],
        "melusina_meshes": [],
        "scene_camera": bpy.context.scene.camera.name if bpy.context.scene.camera else None,
    }
    if mel:
        report["coll_hide_render"] = mel.hide_render
        for o in list(mel.objects):
            try:
                entry = {
                    "name": o.name,
                    "type": o.type,
                    "hide_render": o.hide_render,
                    "hide_viewport": o.hide_viewport,
                }
                if o.type == "MESH":
                    mats = [s.material.name if s.material else "" for s in o.material_slots]
                    entry["materials"] = mats
                    entry["verts"] = len(o.data.vertices) if o.data else 0
                    report["melusina_meshes"].append(entry)
                    if "hair" in o.name.lower() or "strand" in o.name.lower() or "Water (Advance)" in mats:
                        report["hair_strands"].append(entry)
                else:
                    report["melusina_meshes"].append(entry)
            except ReferenceError:
                continue
        for child in mel.children:
            report.setdefault("child_collections", []).append(
                {"name": child.name, "hide_render": child.hide_render, "objects": len(child.objects)}
            )

    # Also scan scene for Hair Strand / Melusina by name
    report["scene_hair"] = [
        {"name": o.name, "hide_render": o.hide_render, "users_collection": [c.name for c in o.users_collection]}
        for o in bpy.data.objects
        if o.type == "MESH" and ("Hair Strand" in o.name or o.name.lower() == "melusina")
    ]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[Probe] wrote {OUT}")
    print(json.dumps({k: report[k] for k in ("has_Asset_melusina", "scene_camera", "hair_strands", "scene_hair")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
