"""Read-only Blender audit for reusable Melusina hair rigs and simulation sources."""
import json
from pathlib import Path
import bpy

rows = []
for obj in bpy.data.objects:
    name = obj.name.lower()
    relevant = "hair" in name or "hairexp" in name or "flip" in name
    if not relevant:
        continue
    row = {"name": obj.name, "type": obj.type, "parent": obj.parent.name if obj.parent else None}
    if obj.type == "ARMATURE":
        row["bone_count"] = len(obj.data.bones)
        row["hair_bones"] = [bone.name for bone in obj.data.bones if "hair" in bone.name.lower()]
    elif obj.type == "MESH":
        row["vertex_count"] = len(obj.data.vertices)
        row["hair_vertex_groups"] = [group.name for group in obj.vertex_groups if "hair" in group.name.lower()]
        row["armature_modifiers"] = [mod.object.name if mod.object else None for mod in obj.modifiers if mod.type == "ARMATURE"]
    rows.append(row)

report = {
    "schema": "melodia.melusina_hair_source_audit.v1",
    "blend": bpy.data.filepath,
    "object_count": len(bpy.data.objects),
    "relevant_objects": rows,
    "armatures": [{"name": obj.name, "bone_count": len(obj.data.bones)} for obj in bpy.data.objects if obj.type == "ARMATURE"],
    "flip_domains": [obj.name for obj in bpy.data.objects if obj.flip_fluid.is_domain()] if hasattr(bpy.types.Object, "flip_fluid") else [],
}
output = Path(r"C:\EnvironmentPortfolio\_wt_morning_closeout\Saved\Audit\melusina_hair_source_audit_20260921.json")
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("MELUSINA_HAIR_SOURCE_AUDIT=" + json.dumps({"relevant": len(rows), "armatures": len(report["armatures"]), "output": str(output)}))
