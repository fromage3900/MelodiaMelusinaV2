#!/usr/bin/env python
"""Read-only inventory of the Shorewake dress blends.

Finds which blend still carries the 48 labeled material slots
(SW_Dress_P01..P48) so the slotted bake export can use it.

Run: blender -b --factory-startup -noaudio --python shorewake_blend_inventory.py
Out: Saved/Audit/melusina_lookdev/bake/blend_inventory.json
"""
import bpy
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[3]
OUT = PROJECT / "Saved" / "Audit" / "melusina_lookdev" / "bake"
BLENDS = [
    PROJECT / "Saved" / "Audit" / "melusina_lookdev" / "Shorewake_48MAT.blend",
    PROJECT / "Saved" / "Audit" / "melusina_lookdev" / "Shorewake_48MAT_frozen_snapshot.blend",
    PROJECT / "Saved" / "Audit" / "melusina_lookdev" / "Shorewake_48MAT_consolidated.blend",
]
TARGET = "SM_ShorewakeDress_48MAT"

results = []
for blend in BLENDS:
    rec = {"blend": blend.name, "exists": blend.exists()}
    if not blend.exists():
        results.append(rec)
        continue
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    obj = bpy.data.objects.get(TARGET)
    if obj is None:
        rec["target_found"] = False
        results.append(rec)
        continue
    rec["target_found"] = True
    slots = [ms.material.name if ms.material else "NONE" for ms in obj.material_slots]
    per_slot = {}
    for poly in obj.data.polygons:
        name = slots[poly.material_index] if poly.material_index < len(slots) else "OUT_OF_RANGE"
        per_slot[name] = per_slot.get(name, 0) + 1
    rec.update({
        "slot_count": len(slots),
        "unique_materials": len(set(slots)),
        "polys": len(obj.data.polygons),
        "verts": len(obj.data.vertices),
        "uv_layers": [u.name for u in obj.data.uv_layers],
        "color_attrs": [c.name for c in obj.data.color_attributes],
        "shape_keys": len(obj.data.shape_keys.key_blocks) if obj.data.shape_keys else 0,
        "first_slots": slots[:6],
        "last_slots": slots[-4:],
        "empty_slots": sum(1 for s in slots if s == "NONE"),
        "poly_total_check": sum(per_slot.values()),
    })
    results.append(rec)

OUT.mkdir(parents=True, exist_ok=True)
out = OUT / "blend_inventory.json"
out.write_text(json.dumps({"schema": "melodia.shorewake_blend_inventory.v1", "results": results}, indent=1),
               encoding="utf-8")
print("INVENTORY " + json.dumps(results))
