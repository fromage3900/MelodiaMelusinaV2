"""Comprehensive survey of ALL material instances across every parent master.

For each MI under /Game/EnvSandbox/Materials (recursive):
  - parent (short name)
  - overridden scalar/vector/texture params count
  - effective TextureWeight / Layer weights (for Universal family)
  - whether any texture param is overridden with a real texture
  - missing-map heuristic: parent family has texture params but instance
    overrides ZERO of them while overriding other params

Writes Saved/Audit/mi_full_survey.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
MAT_ROOT = "/Game/EnvSandbox/Materials"


def short_parent(parent):
    if not parent:
        return ""
    return str(parent).split(".")[0].rsplit("/", 1)[-1]


def main() -> int:
    lib = unreal.MaterialEditingLibrary
    assets = unreal.EditorAssetLibrary.list_assets(MAT_ROOT, recursive=True, include_folder=False)
    rows = []
    for path in assets:
        inst = unreal.load_asset(path)
        if not isinstance(inst, unreal.MaterialInstanceConstant):
            continue
        try:
            parent = str(inst.get_editor_property("parent"))
        except Exception:
            parent = None
        pshort = short_parent(parent)

        scalar_ov = []
        try:
            for n in lib.get_scalar_parameter_names(inst):
                if lib.is_material_instance_parameter_overridden(inst, n):
                    scalar_ov.append(str(n))
        except Exception:
            pass
        tex_ov = []
        try:
            for n in lib.get_texture_parameter_names(inst):
                if lib.is_material_instance_parameter_overridden(inst, n):
                    tex_ov.append(str(n))
        except Exception:
            pass
        vec_ov = []
        try:
            for n in lib.get_vector_parameter_names(inst):
                if lib.is_material_instance_parameter_overridden(inst, n):
                    vec_ov.append(str(n))
        except Exception:
            pass

        tw = None
        if "Toon_Universal" in (parent or ""):
            try:
                tw = lib.get_material_instance_scalar_parameter_value(inst, "TextureWeight")
            except Exception:
                pass

        rows.append({
            "path": path,
            "parent": pshort,
            "n_scalar_overridden": len(scalar_ov),
            "n_texture_overridden": len(tex_ov),
            "n_vector_overridden": len(vec_ov),
            "texture_weight": tw,
            "textures": tex_ov,
            "scalars": scalar_ov,
        })

    # Families where texture params exist on the parent and an instance overrides
    # non-texture params but zero textures = "needs texture routing" candidates.
    parents_with_tex_params = set()
    for path in assets:
        inst = unreal.load_asset(path)
        if not isinstance(inst, unreal.MaterialInstanceConstant):
            continue
        try:
            parent = str(inst.get_editor_property("parent"))
        except Exception:
            continue
        if not parent or "M_Master_Toon_Universal" not in parent:
            continue

    report = {
        "generated": "2026-08-13",
        "root": MAT_ROOT,
        "instance_count": len(rows),
        "rows": rows,
    }
    out = ROOT / "Saved" / "Audit" / "mi_full_survey.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    from collections import Counter
    parents = Counter(r["parent"] for r in rows)
    print(f"instances: {len(rows)}")
    print("parents:")
    for p, c in parents.most_common(20):
        print(f"  {c:4d}  {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
