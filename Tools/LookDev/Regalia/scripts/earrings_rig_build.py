"""Earring skeletal-rig prep (NEW files only). Opens regalia_v4_it2.blend (never saved), bakes REG_earrings into ONE
skinned mesh with a tiny own skeleton (rigid weights), posed->rest corrected with head.x like the static regalia export,
writes SK_Regalia_v4_Earrings.fbx + sidecar. Space: Blender REST world (BU=m), UE=(x,-y,z)*100 ('blender-cm').
Skeleton: earrings_root(origin) -> ear_{L,R}_root(stud) -> ear_{s}_dangle_01 (ring1..bezel, loops) -> _02 (ring2) -> _03 (cap+drop)."""
import bpy, bmesh, json, os, sys
from mathutils import Vector, Matrix
A = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUTD = A[0] if A else r"C:\EnvironmentPortfolio\_lookdev_work\regalia_v2\ue_export_v4\earrings_physics"
POSE = A[1] if len(A) > 1 else r"C:\EnvironmentPortfolio\_lookdev_work\regalia_v2\ue_export_v4\melusina_pose_dump_v4.json"
os.makedirs(OUTD, exist_ok=True)
FBX = os.path.join(OUTD, "SK_Regalia_v4_Earrings.fbx"); SIDE = os.path.join(OUTD, "SK_Regalia_v4_Earrings_sidecar.json")
assert not os.path.exists(FBX), "refusing to overwrite " + FBX
PD = json.load(open(POSE))
CM = Matrix(PD["bones"]["head.x"]["rest"]) @ Matrix(PD["bones"]["head.x"]["pose"]).inverted()
bpy.context.scene.unit_settings.scale_length = 1.0
dg = bpy.context.evaluated_depsgraph_get()
col = bpy.data.collections["REG_earrings"]
SEG = {"stud": "root", "ring1": "dangle_01", "stone_round": "dangle_01", "bezel": "dangle_01", "loopTop": "dangle_01", "loopBot": "dangle_01",
       "ring2": "dangle_02", "cap": "dangle_03", "stone_drop": "dangle_03"}
def slot_for(mn):
    l = (mn or "").lower()
    if "gold" in l: return "MS_Gold"
    if "orchid" in l or "purple" in l or "amethyst" in l or "violet" in l: return "MS_GemPurple"
    return "MS_Other"
def rest_bbox(o):
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg)); me.transform(o.matrix_world); me.transform(CM)
    vs = [v.co.copy() for v in me.vertices]; bpy.data.meshes.remove(me)
    mn = Vector([min(v[i] for v in vs) for i in range(3)]); mx = Vector([max(v[i] for v in vs) for i in range(3)]); return mn, mx
# bone joints from the rest-space part bboxes
J = {}
for s in ("L", "R"):
    b = {k: rest_bbox(bpy.data.objects["ear%s_%s" % (s, k)]) for k in SEG}
    c = {k: (v[0] + v[1]) * 0.5 for k, v in b.items()}
    J[s] = {"root": (c["stud"], Vector((c["stud"].x, c["stud"].y, b["ring1"][1].z))),
            "dangle_01": (Vector((c["ring1"].x, c["ring1"].y, b["ring1"][1].z)), Vector((c["ring2"].x, c["ring2"].y, b["ring2"][1].z))),
            "dangle_02": (Vector((c["ring2"].x, c["ring2"].y, b["ring2"][1].z)), Vector((c["cap"].x, c["cap"].y, b["cap"][1].z))),
            "dangle_03": (Vector((c["cap"].x, c["cap"].y, b["cap"][1].z)), Vector((c["stone_drop"].x, c["stone_drop"].y, b["stone_drop"][0].z)))}
# throwaway scene objects: armature + one mesh
arm_d = bpy.data.armatures.new("Armature_SK_Regalia_v4_Earrings"); arm = bpy.data.objects.new("Armature", arm_d)
sc = bpy.context.scene; vl = bpy.context.view_layer   # session only, file never saved
sc.collection.objects.link(arm); vl.objects.active = arm
if True:
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm_d.edit_bones; r = eb.new("earrings_root"); r.head = (0, 0, 0); r.tail = (0, 0, 0.02)
    for s in ("L", "R"):
        prev = r
        for k in ("root", "dangle_01", "dangle_02", "dangle_03"):
            h, t = J[s][k]
            if (t - h).length < 1e-4: t = h + Vector((0, 0, -0.004))
            e = eb.new("ear_%s_%s" % (s, k)); e.head = h; e.tail = t; e.roll = 0.0; e.parent = prev
            e.use_connect = False; prev = e
    bpy.ops.object.mode_set(mode="OBJECT")
bm = bmesh.new(); mats = []; vg_of_vert = []; info_parts = {}
for s in ("L", "R"):
    for k, seg in SEG.items():
        o = bpy.data.objects["ear%s_%s" % (s, k)]
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg)); me.transform(o.matrix_world); me.transform(CM)
        sl = slot_for(o.material_slots[0].material.name if o.material_slots and o.material_slots[0].material else None)
        if sl not in mats: mats.append(sl)
        for p in me.polygons: p.material_index = mats.index(sl)
        n0 = len(bm.verts); bm.from_mesh(me); n1 = len(bm.verts); bpy.data.meshes.remove(me)
        vg_of_vert += ["ear_%s_%s" % (s, seg)] * (n1 - n0); info_parts["ear%s_%s" % (s, k)] = {"bone": "ear_%s_%s" % (s, seg), "verts": n1 - n0}
me = bpy.data.meshes.new("SK_Regalia_v4_Earrings"); bm.to_mesh(me); bm.free()
for sl in mats: me.materials.append(bpy.data.materials.get(sl) or bpy.data.materials.new(sl))
ob = bpy.data.objects.new("SK_Regalia_v4_Earrings", me); sc.collection.objects.link(ob); ob.parent = arm
groups = {}
for i, g in enumerate(vg_of_vert): groups.setdefault(g, []).append(i)
for g, idx in groups.items(): ob.vertex_groups.new(name=g).add(idx, 1.0, "REPLACE")
ob.modifiers.new("Armature", "ARMATURE").object = arm
ue = lambda v: [round(v.x * 100, 4), round(-v.y * 100, 4), round(v.z * 100, 4)]
side = {"space": "Blender REST world (head.x posed->rest), UE=(x,-y,z)*100 (component space of SK_Melusina_V2_Body up to the solved similarity)",
        "attach_bone": "head_x", "attach_like": "SM_Regalia_v4_Earrings (ue_attach_v4.json attach entry)", "slots": mats,
        "verts": len(me.vertices), "tris": sum(len(p.vertices) - 2 for p in me.polygons),
        "bones": {b.name: {"parent": b.parent.name if b.parent else None, "head_ue_bcm": ue(b.head_local), "tail_ue_bcm": ue(b.tail_local)} for b in arm_d.bones},
        "parts": info_parts, "weights": "rigid 1.0, one bone per part",
        "kawaii_suggest": {"root_bones": ["ear_L_root", "ear_R_root"], "damping": 0.6, "stiffness": 0.15, "world_damping_location": 0.8,
                           "world_damping_rotation": 0.8, "radius_cm": 0.3, "gravity": [0, 0, -981], "limit_angle_deg": 50,
                           "colliders": "optional sphere on neck_x/jaw: skip v1"}}
for o in vl.objects:
    try: o.select_set(False)
    except Exception: pass
arm.select_set(True); ob.select_set(True); vl.objects.active = arm
if True:
    bpy.ops.export_scene.fbx(filepath=FBX, use_selection=True, object_types={"ARMATURE", "MESH"}, apply_unit_scale=True, global_scale=1.0,
        apply_scale_options="FBX_SCALE_NONE", axis_forward="-Z", axis_up="Y", mesh_smooth_type="FACE", use_mesh_modifiers=False,
        add_leaf_bones=False, use_armature_deform_only=False, primary_bone_axis="Y", secondary_bone_axis="X", bake_anim=False,
        path_mode="STRIP", use_custom_props=False)
side["fbx"] = FBX; side["fbx_bytes"] = os.path.getsize(FBX)
json.dump(side, open(SIDE, "w"), indent=1)
print("EARRIG", json.dumps({k: side[k] for k in ("verts", "tris", "slots")}), {b: v["head_ue_bcm"] for b, v in side["bones"].items()})
