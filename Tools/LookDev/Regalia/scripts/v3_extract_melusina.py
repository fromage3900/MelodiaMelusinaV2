"""READ-ONLY extraction from the Melusina source blend (never saves the source).
Bakes the posed (evaluated) head/bust, eyes, brows, lashes and hair meshes into NEW mesh datablocks
(world space, no materials) and writes only those to a new small .blend via bpy.data.libraries.write."""
import bpy, bmesh, json, sys
from mathutils import Vector
OUT = r"C:\EnvironmentPortfolio\_lookdev_work\regalia_v2\v3\melusina_bust_src_v3.blend"
REC = r"C:\EnvironmentPortfolio\_lookdev_work\regalia_v2\v3\melusina_extract_receipt.json"
dg = bpy.context.evaluated_depsgraph_get()
R = {"source": bpy.data.filepath, "frame": bpy.context.scene.frame_current, "unit_scale_length": bpy.context.scene.unit_settings.scale_length, "objects": {}}
WANT = {  # name -> role
    "Melusina_Base": "body", "R_Iris.001": "eye", "R_Iris.002": "eye", "R_Eyebrow": "brow", "L_Eyebrow": "brow",
    "R_Eyelash": "lash", "Hair Strand.007": "hair_main", "Hair Strand.010": "hair_bangs", "Hair Strand.004": "hair_front",
}
ZCUT = 1.05
new_objs = []
for name, role in WANT.items():
    o = bpy.data.objects.get(name)
    if not o: R["objects"][name] = "missing"; continue
    oe = o.evaluated_get(dg)
    try:
        me = bpy.data.meshes.new_from_object(oe, preserve_all_data_layers=False, depsgraph=dg)
    except Exception as e:
        R["objects"][name] = "bake failed: %s" % e; continue
    me.transform(o.matrix_world)
    me.materials.clear()
    nv0 = len(me.vertices)
    if role == "body":
        bm = bmesh.new(); bm.from_mesh(me)
        kill = [v for v in bm.verts if v.co.z < ZCUT or abs(v.co.x) > 0.30]
        bmesh.ops.delete(bm, geom=kill, context="VERTS"); bm.to_mesh(me); bm.free()
    if len(me.vertices) == 0:
        R["objects"][name] = "empty after bake"; continue
    ob = bpy.data.objects.new("MEL3_" + role + "_" + name.replace(" ", "_").replace(".", "_"), me)
    ob["mel3_role"] = role; ob["mel3_src"] = name
    new_objs.append(ob)
    pts = [v.co for v in me.vertices]
    mn = [min(p[i] for p in pts) for i in range(3)]; mx = [max(p[i] for p in pts) for i in range(3)]
    R["objects"][name] = {"role": role, "verts_eval": nv0, "verts_kept": len(me.vertices), "min": [round(v, 4) for v in mn], "max": [round(v, 4) for v in mx]}
# head measurements from the baked body: slices through the head
body = [o for o in new_objs if o["mel3_role"] == "body"]
if body:
    P = [v.co for v in body[0].data.vertices]
    ztop = max(p.z for p in P)
    sl = {}
    for dz in [0.0, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.14, 0.16, 0.18, 0.20, 0.22, 0.24, 0.26, 0.28, 0.30, 0.32, 0.34, 0.36, 0.40, 0.45, 0.50]:
        z = ztop - dz; s = [p for p in P if abs(p.z - z) < 0.006]
        if s:
            sl["%.2f" % dz] = {"z": round(z, 3), "x": [round(min(p.x for p in s), 3), round(max(p.x for p in s), 3)], "y": [round(min(p.y for p in s), 3), round(max(p.y for p in s), 3)], "n": len(s)}
    R["head_slices_from_top"] = sl; R["head_top_z"] = round(ztop, 4)
bpy.data.libraries.write(OUT, set(new_objs), fake_user=True, compress=True)
json.dump(R, open(REC, "w"), indent=1)
print("V3E-WROTE", OUT, len(new_objs))
print("V3E-REC", json.dumps(R))
