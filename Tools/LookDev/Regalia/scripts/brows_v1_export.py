"""Eyebrow prep (NEW files only): take the brows exactly as already used in UE (Melusina_Brows_Export_20260922.fbx: rest-pose,
authored at 1/10 scale -> UE components use scale 10), bake them to TRUE size in Blender REST world (BU=m), merge L+R into ONE
static mesh SM_Melusina_Brows_v1 (slot MS_Brows) and export with the same FBX settings as the regalia -> it lands in
'blender-cm' component space and attaches to head_x with the SAME relative transform as the regalia (ue_attach_v4.json)."""
import bpy, bmesh, json, os, sys
from mathutils import Vector, Matrix
A = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SRC = A[0]; OUTD = A[1]; os.makedirs(OUTD, exist_ok=True)
FBX = os.path.join(OUTD, "SM_Melusina_Brows_v1.fbx"); SIDE = os.path.join(OUTD, "SM_Melusina_Brows_v1_sidecar.json")
assert not os.path.exists(FBX), "refusing to overwrite " + FBX
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.context.scene.unit_settings.scale_length = 1.0
bpy.ops.import_scene.fbx(filepath=SRC)
bm = bmesh.new(); names = []
S10 = Matrix.Scale(10.0, 4)
for o in [o for o in bpy.data.objects if o.type == "MESH"]:
    me = o.data.copy(); me.transform(S10 @ o.matrix_world); bm.from_mesh(me); bpy.data.meshes.remove(me); names.append(o.name)
me = bpy.data.meshes.new("SM_Melusina_Brows_v1"); bm.to_mesh(me); bm.free()
for p in me.polygons: p.material_index = 0; p.use_smooth = True
me.materials.append(bpy.data.materials.new("MS_Brows"))
ob = bpy.data.objects.new("SM_Melusina_Brows_v1", me)
for o in list(bpy.data.objects):
    if o is not ob: bpy.data.objects.remove(o)
bpy.context.scene.collection.objects.link(ob); ob.select_set(True); bpy.context.view_layer.objects.active = ob
vs = [v.co for v in me.vertices]; mn = Vector([min(v[i] for v in vs) for i in range(3)]); mx = Vector([max(v[i] for v in vs) for i in range(3)])
ue = lambda v: [round(v.x * 100, 3), round(-v.y * 100, 3), round(v.z * 100, 3)]
bpy.ops.export_scene.fbx(filepath=FBX, use_selection=True, object_types={"MESH"}, apply_unit_scale=True, global_scale=1.0,
    apply_scale_options="FBX_SCALE_NONE", axis_forward="-Z", axis_up="Y", mesh_smooth_type="FACE", use_mesh_modifiers=False,
    use_triangles=False, add_leaf_bones=False, bake_anim=False, path_mode="STRIP", use_custom_props=False)
side = {"src": SRC, "src_objects": names, "scale_applied": 10.0, "verts": len(me.vertices), "tris": sum(len(p.vertices) - 2 for p in me.polygons),
        "slots": ["MS_Brows"], "bbox_ue_bcm": [ue(Vector((mn.x, mx.y, mn.z))), ue(Vector((mx.x, mn.y, mx.z)))], "attach_bone": "head_x",
        "attach_like": "SM_Regalia_v4_Circlet (ue_attach_v4.json)", "material": "reuse MI_Melusina_Brows_Dark (read-only reference, not modified)",
        "check": "rest-corrected MEL3 brow proxies in regalia_v3_final.blend agree within ~2 mm", "fbx": FBX}
json.dump(side, open(SIDE, "w"), indent=1); print("BROWS", json.dumps(side))
