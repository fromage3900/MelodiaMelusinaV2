"""Merge the 48 Shorewake dress panels into 10 labeled garment materials (OBJ).

Reads garment_layers_manifest.json (silhouette classifier output) + the slotted
OBJ, and rewrites each panel's `usemtl` block to the merged garment-material
group (SW_Dress_Pxx -> M_<layer>). Emits a merged OBJ + MTL whose material
slots are the semantic garment pieces, ready for a Substance 10-texture-set
project. Deterministic, headless.

Disjoint panels are already material-slot-disjoint in the slotted OBJ, so a
rename-only merge preserves vertex/UV space exactly.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

OBJ = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
    r"C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/melusina_lookdev/bake/"
    r"night_pkg_2026-08-31/SM_ShorewakeDress_48MAT_v2_slotted.obj")
LAYERS = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(
    r"C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/melusina_lookdev/"
    r"night_pkg_2026-08-31/garment_layers_manifest.json")
OUT = Path(sys.argv[3]) if len(sys.argv) > 3 else OBJ.with_name(
    "SM_ShorewakeDress_48MAT_garment.obj")


def main():
    data = json.loads(LAYERS.read_text(encoding="utf-8"))
    panel_to_group = {r["panel"]: r["material_group"] for r in data["panels"]}
    groups = data["material_groups"]
    group_names = sorted(groups.keys())
    print(f"[merge] {len(panel_to_group)} panels -> {len(group_names)} garment groups")

    # Build a clean MTL with a generic white/base material per group.
    mtl_lines = ["# Melodia Shorewake garment layers MTL",
                 "# material groups from silhouette classifier (garment_layers_manifest.json)"]
    for g in group_names:
        mtl_lines += [
            f"newmtl {g}",
            "Ka 0.2 0.2 0.2",
            f"Kd 0.85 0.85 0.85",
            "Ks 0.12 0.12 0.12",
            "d 1.0",
            f"illum 2",
            "",
        ]

    # Rewrite OBJ: usemtl SW_Dress_Pxx -> group. 'g' name kept descriptive.
    out_lines = []
    n_blocks = 0
    renumbered = {}
    with open(OBJ, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.startswith("usemtl "):
                cur = line.split()[1]
                grp = panel_to_group.get(cur, cur)
                out_lines.append(f"usemtl {grp}\n")
                n_blocks += 1
                renumbered[cur] = grp
            elif line.startswith("mtllib "):
                out_lines.append("mtllib SM_ShorewakeDress_48MAT_garment.mtl\n")
            else:
                out_lines.append(line)
    OUT.write_text("".join(out_lines), encoding="utf-8")
    OUT.with_name("SM_ShorewakeDress_48MAT_garment.mtl").write_text(
        "\n".join(mtl_lines), encoding="utf-8")

    # verify renumbering
    expect = set(group_names)
    got = set(renumbered.values())
    print(f"[merge] blocks renumbered: {n_blocks}; distinct groups present: {len(got)}")
    missing = expect - got
    if missing:
        print(f"[merge] WARNING groups with no panels: {sorted(missing)}")
    print(f"[merge] wrote {OUT.name} + {OUT.with_name('SM_ShorewakeDress_48MAT_garment.mtl').name}")

    # manifest
    manifest = {
        "schema": "melodia.shorewake_garment_merge_obj.v1",
        "source_obj": str(OBJ),
        "layers_manifest": str(LAYERS),
        "output": str(OUT),
        "panel_count": n_blocks,
        "garment_materials": group_names,
        "panel_to_material": renumbered,
        "group_counts": {g: len(groups[g]["panels"]) for g in group_names},
    }
    out_man = OUT.with_name("garment_merge_obj_manifest.json")
    out_man.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[merge] wrote {out_man.name}")


if __name__ == "__main__":
    main()