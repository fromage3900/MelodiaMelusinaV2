"""Survey Paradise (Rooms_Paradise_*) meshes + their materials in EnvSandbox/Meshes/Environment root."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
ENV_DIR = ROOT / "Content" / "EnvSandbox" / "Meshes" / "Environment"
OUT = ROOT / "Saved" / "Audit" / "paradise_survey.json"


def main() -> int:
    lib = unreal.MaterialEditingLibrary
    paradise = sorted(p for p in ENV_DIR.glob("Rooms_Paradise*.uasset"))
    rows = []
    pack_mi = 0
    for p in paradise:
        game = "/Game/EnvSandbox/Meshes/Environment/" + p.stem
        m = unreal.load_asset(game)
        if not m:
            continue
        slots = []
        for i, s in enumerate(m.static_materials or []):
            mi = s.material_interface
            path = str(mi.get_path_name()) if mi else "NONE"
            if "ImportedPacks/MI_Env" in path:
                pack_mi += 1
            slots.append({"i": i, "name": str(s.material_slot_name), "mat": path})
        rows.append({"mesh": p.stem, "slots": slots})

    # Paradise-related MICs in the root (Atlas_01_Mat etc.)
    mats = {}
    for p in sorted(ENV_DIR.glob("*.uasset")):
        if p.stem in ("Atlas_01_Mat", "Atlas_01_Trans_Mat", "Seam_Floor_Mat", "Seam_Sand_Mat", "Seam_Shadows_Mat"):
            inst = unreal.load_asset("/Game/EnvSandbox/Meshes/Environment/" + p.stem)
            tex_ov = []
            if isinstance(inst, unreal.MaterialInstanceConstant):
                try:
                    for n in lib.get_texture_parameter_names(inst):
                        if lib.is_material_instance_parameter_overridden(inst, n):
                            tex_ov.append(str(n))
                except Exception:
                    pass
            mats[p.stem] = {"textures_overridden": tex_ov}

    report = {
        "generated": "2026-08-13",
        "paradise_meshes": len(rows),
        "paradise_slots_on_pack_mi": pack_mi,
        "meshes": rows,
        "root_mats": mats,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"paradise meshes: {len(rows)} | slots on pack MI: {pack_mi}")
    print("root mats:", mats)
    # what slot names do paradise meshes use?
    from collections import Counter
    names = Counter()
    for m in rows:
        for s in m["slots"]:
            names[s["name"]] += 1
    print("slot names:", dict(names.most_common(12)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
