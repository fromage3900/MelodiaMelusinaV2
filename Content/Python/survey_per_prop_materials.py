"""Survey per-prop mesh materials: what do the MICs under Meshes/Environment/*/Materials/
actually reference, and which props have imported Textures/ folders?"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
MESH_ROOT = "/Game/EnvSandbox/Meshes/Environment"
OUT = ROOT / "Saved" / "Audit" / "per_prop_material_survey.json"


def main() -> int:
    lib = unreal.MaterialEditingLibrary
    mats = unreal.EditorAssetLibrary.list_assets(f"{MESH_ROOT}", recursive=True, include_folder=False)
    mat_rows = []
    for path in mats:
        if "/Materials/" not in path:
            continue
        inst = unreal.load_asset(path)
        if not isinstance(inst, unreal.MaterialInstanceConstant):
            continue
        try:
            parent = str(inst.get_editor_property("parent"))
        except Exception:
            parent = None
        tex_ov = []
        try:
            for n in lib.get_texture_parameter_names(inst):
                if lib.is_material_instance_parameter_overridden(inst, n):
                    tex_ov.append(f"{n}={lib.get_material_instance_texture_parameter_value(inst, n)}")
        except Exception:
            pass
        tw = None
        try:
            tw = lib.get_material_instance_scalar_parameter_value(inst, "TextureWeight")
        except Exception:
            pass
        mat_rows.append({
            "path": path,
            "parent": parent.split(".")[0].rsplit("/", 1)[-1] if parent else None,
            "textures_overridden": tex_ov,
            "texture_weight": tw,
        })

    # Props with an imported Textures/ folder (real per-prop maps) - from disk.
    mesh_disk = ROOT / "Content" / "EnvSandbox" / "Meshes" / "Environment"
    props_with_textures, props_without = [], []
    if mesh_disk.exists():
        for d in sorted(p for p in mesh_disk.iterdir() if p.is_dir()):
            tex_dir = d / "Textures"
            mats_dir = d / "Materials"
            if not mats_dir.exists():
                continue
            if tex_dir.exists():
                n = len([p for p in tex_dir.rglob("*.uasset") if p.is_file()])
                props_with_textures.append((d.name, n))
            else:
                props_without.append(d.name)

    report = {
        "generated": "2026-08-13",
        "per_prop_materials": mat_rows,
        "materials_with_textures": sum(1 for r in mat_rows if r["textures_overridden"]),
        "materials_without_textures": sum(1 for r in mat_rows if not r["textures_overridden"]),
        "props_with_textures_dir": props_with_textures,
        "props_without_textures_dir": props_without,
        "counts": {
            "props_with": len(props_with_textures),
            "props_without": len(props_without),
        },
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"per-prop materials: {len(mat_rows)}")
    print(f"  with texture overrides: {report['materials_with_textures']}")
    print(f"  without texture overrides: {report['materials_without_textures']}")
    print(f"props with Textures/ dir: {len(props_with_textures)}")
    print(f"props without Textures/ dir: {len(props_without)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
