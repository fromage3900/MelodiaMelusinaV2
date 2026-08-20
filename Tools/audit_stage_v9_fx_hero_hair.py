# -*- coding: utf-8 -*-
"""Inventory Stage v9 FX_Hero + hair/physics/liquid lanes.

  blender -b KitbashExport/Melodia_Portfolio_Stage_v9.blend -P Tools/audit_stage_v9_fx_hero_hair.py
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Saved" / "Audit" / "stage_v9_fx_hero_hair_inventory.json"
HAIR_MESH = ("Hair Strand.002", "Hair Strand.004", "Hair Strand.007")
FLOOR_Z_PIN = -0.2935


def _world_tip(obj: bpy.types.Object) -> list[float] | None:
    if obj.type != "MESH" or not obj.data.vertices:
        return None
    zs = sorted(v.co.z for v in obj.data.vertices)
    thresh = zs[max(0, int(len(zs) * 0.02))]
    tips = [obj.matrix_world @ v.co for v in obj.data.vertices if v.co.z <= thresh + 1e-5]
    if not tips:
        return None
    t = sum(tips, Vector()) / len(tips)
    return [round(t.x, 4), round(t.y, 4), round(t.z, 4)]


def main() -> None:
    fx = bpy.data.collections.get("FX_Hero")
    fx_rows = []
    if fx:
        for o in fx.objects:
            fx_rows.append(
                {
                    "name": o.name,
                    "type": o.type,
                    "hide_viewport": o.hide_viewport,
                    "hide_render": o.hide_render,
                    "mats": [s.material.name if s.material else None for s in o.material_slots],
                    "mods": [{"name": m.name, "type": m.type} for m in o.modifiers],
                }
            )

    hair = []
    for name in HAIR_MESH:
        o = bpy.data.objects.get(name)
        if not o:
            hair.append({"name": name, "missing": True})
            continue
        shp = bpy.data.objects.get(f"SHP_Armature ({name})")
        hair.append(
            {
                "name": name,
                "type": o.type,
                "mats": [s.material.name if s.material else None for s in o.material_slots],
                "mods": [{"name": m.name, "type": m.type} for m in o.modifiers],
                "tip_world": _world_tip(o),
                "shp_armature": shp.name if shp else None,
                "hide_render": o.hide_render,
            }
        )

    water_coll = bpy.data.collections.get("Melusina_WaterFX")
    floor = bpy.data.objects.get("Studio_FloorCard")
    floor_z = None
    if floor:
        floor_z = round(floor.matrix_world.translation.z, 6)

    liquifeel = []
    for o in bpy.data.objects:
        for m in o.modifiers:
            if m.type == "NODES" and m.node_group and "liqui" in m.node_group.name.lower():
                liquifeel.append({"obj": o.name, "mod": m.name, "group": m.node_group.name})

    flip_active = []
    for o in bpy.data.objects:
        if hasattr(o, "flip_fluid"):
            try:
                if o.flip_fluid.is_active:
                    flip_active.append(
                        {"name": o.name, "type": str(o.flip_fluid.object_type)}
                    )
            except Exception:
                pass

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "filepath": bpy.data.filepath,
        "doctrine": {
            "fx_hero": "stage dressing only (sparkles/veil/jewelry/ribbon)",
            "hair_look": "Water (Advance).001 keep",
            "hair_drip": "LiquiFeel tip proxies in Melusina_HairDrip — not FX_Hero",
            "elixir": "Asset_melusina_elixir LiquiFeel glass only",
            "flip": "Melusina_WaterFX paused for this lane",
        },
        "FX_Hero": {
            "exists": fx is not None,
            "hide_viewport": fx.hide_viewport if fx else None,
            "hide_render": fx.hide_render if fx else None,
            "objects": fx_rows,
            "beauty_quiet": "hide_render collection or use beauty_clean preset",
        },
        "hair_physics_mesh": hair,
        "Melusina_WaterFX": {
            "exists": water_coll is not None,
            "hide_viewport": water_coll.hide_viewport if water_coll else None,
            "hide_render": water_coll.hide_render if water_coll else None,
            "objects": [o.name for o in water_coll.objects] if water_coll else [],
        },
        "liquifeel_modifiers": liquifeel,
        "flip_active_objects": flip_active,
        "Studio_FloorCard_z": floor_z,
        "floor_pin_ok": floor_z is not None and abs(floor_z - FLOOR_Z_PIN) < 0.01,
        "Melusina_HairDrip_exists": bpy.data.collections.get("Melusina_HairDrip") is not None,
        "collections_sample": sorted(
            c.name
            for c in bpy.data.collections
            if any(
                k in c.name
                for k in ("FX_", "Water", "Hair", "Elixir", "Melusina", "FLIP")
            )
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[audit-v9] wrote {OUT} fx={len(fx_rows)} hair={len(hair)} floor_z={floor_z}")


if __name__ == "__main__":
    main()
