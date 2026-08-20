"""Read-only probe of the bound v22 objects selected for V2 piece export."""

from __future__ import annotations

import json
import sys
from pathlib import Path
import bpy


PROJECT = Path(__file__).resolve().parents[1]
CONTRACT = PROJECT / "specs/anim_presets/melusina_contract_bones.json"
PIECES = {
    "Body": ["Melusina.001"],
    "Shirt": ["newshirt"],
    "Skirt": ["Melusina_Skirt", "Melusina_SkirtPanel"],
    "Boots": ["Retopo_boot 2.001", "Retopo_boot 2.002"],
    "Accessories": ["Melusina_Bow", "Melusina_FrontPanel", "Melusina_Gloves", "Melusina_Shawl", "Melusina_Sleeve"],
}


def row(name: str) -> dict:
    obj = bpy.data.objects.get(name)
    if obj is None:
        return {"name": name, "found": False}
    scan_weights = "--weights" in sys.argv
    used = set()
    group_names = {group.index: group.name for group in obj.vertex_groups}
    zero = 0
    if scan_weights:
        for vertex in obj.data.vertices:
            total = 0.0
            for assignment in vertex.groups:
                total += assignment.weight
                if assignment.weight > 1e-7 and assignment.group in group_names:
                    used.add(group_names[assignment.group])
            if total <= 1e-7:
                zero += 1
    return {
        "name": name,
        "found": True,
        "type": obj.type,
        "vertices": len(obj.data.vertices),
        "armature_targets": [m.object.name if m.object else None for m in obj.modifiers if m.type == "ARMATURE"],
        "vertex_group_count": len(obj.vertex_groups),
        "used_group_count": len(used),
        "used_groups": sorted(used),
        "zero_weight_vertices": zero,
        "weights_scanned": scan_weights,
        "shape_key_count": len(obj.data.shape_keys.key_blocks) if obj.data.shape_keys else 0,
        "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
        "collections": [collection.name for collection in obj.users_collection],
    }


def main() -> int:
    contract = set(json.loads(CONTRACT.read_text(encoding="utf-8"))["bone_names"])
    only = None
    if "--only" in sys.argv:
        index = sys.argv.index("--only")
        if index + 1 < len(sys.argv):
            only = sys.argv[index + 1]
    selected = {label: names for label, names in PIECES.items() if only is None or label == only}
    pieces = {label: [row(name) for name in names] for label, names in selected.items()}
    for rows in pieces.values():
        for item in rows:
            item["sanitized_unmatched"] = sorted(
                name.replace(".", "_") for name in item.get("used_groups", []) if name.replace(".", "_") not in contract
            )
    report = {
        "schema": "melodia.melusina_v2_piece_candidate_probe.v1",
        "stage": bpy.data.filepath,
        "read_only": True,
        "contract_bone_count": len(contract),
        "pieces": pieces,
        "promotion_allowed": False,
    }
    path = PROJECT / "Saved/Audit/melusina_v2_piece_candidate_probe.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
