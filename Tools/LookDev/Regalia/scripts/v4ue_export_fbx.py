"""Headless: open regalia_v4_it2.blend (never saved), bake each regalia piece (all objects of its collection, evaluated:
curves->mesh, modifiers applied) into ONE static mesh in a throwaway scene and export NEW FBX files.
Coordinates: Blender world BU treated as metres (1 BU -> 100 UE units); FBX default axes so UE import gives
UE = (Bx, -By, Bz) * 100 ("blender-cm space"). The true Blender->UE component similarity is solved in UE from bone pairs."""
import bpy, bmesh, json, os
from mathutils import Vector
OUTD = r"C:\EnvironmentPortfolio\_lookdev_work\regalia_v2\ue_export_v4"
PIECES = [("SM_Regalia_v4_Circlet", "REG_circlet_hair"), ("SM_Regalia_v4_Tiara", "REG_tiara_hair"),
          ("SM_Regalia_v4_Earrings", "REG_earrings"), ("SM_Regalia_v4_Necklace", "REG_necklace"),
          ("SM_Regalia_v4_Circlet_BaldFit", "REG_circlet_bald"), ("SM_Regalia_v4_Tiara_BaldFit", "REG_tiara_bald")]
SLOT = {}  # source material name -> UE slot name
def slot_for(mn):
    l = (mn or "").lower()
    if "gold" in l: return "MS_Gold"
    if "aqua" in l or "blue" in l or "topaz" in l or "sapph" in l: return "MS_GemAqua"
    if "amethyst" in l or "purple" in l or "orchid" in l or "violet" in l: return "MS_GemPurple"
    if "pearl" in l: return "MS_Pearl"
    return "MS_Other_" + (mn or "none").replace(" ", "_")
R = {"src": bpy.data.filepath, "unit_scale_src": bpy.context.scene.unit_settings.scale_length, "pieces": {}}
bpy.context.scene.unit_settings.scale_length = 1.0   # session only: 1 BU -> 1 m -> 100 UE units
dg = bpy.context.evaluated_depsgraph_get()
built = []
for smname, cname in PIECES:
    print("V4UE-BUILD", smname, flush=True)
    col = bpy.data.collections.get(cname)
    if not col: R["pieces"][smname] = "MISSING " + cname; continue
    bm = bmesh.new(); mats = []; srcmats = {}; nobj = 0; skipped = []; names = []
    _all = list(col.all_objects); _objs = [o for o in _all if o is not None]; print("  n_all", len(_all), "non-none", len(_objs), "col.objects", len(col.objects), flush=True)
    for ob in _objs:
        if ob.type not in ("MESH", "CURVE") or not ob.visible_camera or "kick" in ob.name.lower() or "card" in ob.name.lower(): skipped.append(ob.name); continue
        names.append(ob.name); print("  obj", ob.name, ob.type, flush=True)
        oe = ob.evaluated_get(dg); me = bpy.data.meshes.new_from_object(oe, preserve_all_data_layers=False, depsgraph=dg)
        if me is None: continue
        if not me.polygons: bpy.data.meshes.remove(me); continue
        me.transform(ob.matrix_world)
        remap = []
        for ms in (ob.material_slots if ob.material_slots else []):
            s = slot_for(ms.material.name if ms.material else None); srcmats.setdefault(s, set()).add(ms.material.name if ms.material else "None")
            if s not in mats: mats.append(s)
            remap.append(mats.index(s))
        if not remap:
            s = slot_for(None); mats.append(s) if s not in mats else None; remap = [mats.index(s)]
        for p in me.polygons: p.material_index = remap[min(p.material_index, len(remap) - 1)]
        bm.from_mesh(me); bpy.data.meshes.remove(me); nobj += 1
    me = bpy.data.meshes.new(smname); bm.to_mesh(me); bm.free()
    for s in mats:
        m = bpy.data.materials.get(s) or bpy.data.materials.new(s); me.materials.append(m)
    ob = bpy.data.objects.new(smname, me)
    vs = [v.co for v in me.vertices]
    mn = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs))); mx = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    ue = lambda v: [round(v.x * 100, 3), round(-v.y * 100, 3), round(v.z * 100, 3)]
    info = {"collection": cname, "objects": nobj, "verts": len(me.vertices), "tris": sum(len(p.vertices) - 2 for p in me.polygons),
            "slots": mats, "object_names": names, "skipped": skipped, "src_materials": {k: sorted(v) for k, v in srcmats.items()},
            "bbox_blender_bu": [list(mn), list(mx)], "bbox_ue_bcm": [ue(Vector((mn.x, mx.y, mn.z))), ue(Vector((mx.x, mn.y, mx.z)))]}
    # key points for alignment checks
    for key in ("circlet_hair_stone", "tiara_hair_stone", "circlet_bald_stone"):
        so = bpy.data.objects.get(key)
        if so and any(o is so for o in col.all_objects if o is not None):
            c = sum((so.matrix_world @ v.co for v in so.data.vertices), Vector()) / len(so.data.vertices); info["stone_centre_ue_bcm"] = ue(c)
    fp = os.path.join(OUTD, smname + ".fbx")
    if os.path.exists(fp): info["fbx"] = "EXISTS-skipped " + fp
    else:
        sc = bpy.context.scene; sc.collection.objects.link(ob)
        for o in bpy.context.view_layer.objects:
            try: o.select_set(False)
            except Exception: pass
        print("V4UE-EXPORTING", smname, len(me.vertices), flush=True)
        ob.select_set(True); bpy.context.view_layer.objects.active = ob
        bpy.ops.export_scene.fbx(filepath=fp, use_selection=True, object_types={"MESH"}, apply_unit_scale=True, global_scale=1.0,
            apply_scale_options="FBX_SCALE_NONE", axis_forward="-Z", axis_up="Y", mesh_smooth_type="FACE", use_mesh_modifiers=False,
            use_triangles=False, add_leaf_bones=False, bake_anim=False, path_mode="STRIP", use_custom_props=False)
        sc.collection.objects.unlink(ob)
        info["fbx"] = fp; info["fbx_bytes"] = os.path.getsize(fp)
    R["pieces"][smname] = info
    print("V4UE-PIECE", smname, json.dumps(info)[:600])
# earring lobe anchors + necklace pendant, from the build receipt objects if present
for ob in bpy.data.objects:
    if ob.type == "MESH" and any(t in ob.name.lower() for t in ("earring", "pendant")) and ("stud" in ob.name.lower() or "post" in ob.name.lower() or "pendant" in ob.name.lower()):
        c = sum((ob.matrix_world @ v.co for v in ob.data.vertices), Vector()) / max(1, len(ob.data.vertices))
        R.setdefault("anchors", {})[ob.name] = [round(c.x * 100, 3), round(-c.y * 100, 3), round(c.z * 100, 3)]
R["all_material_names"] = sorted(m.name for m in bpy.data.materials if m.users)
json.dump(R, open(os.path.join(OUTD, "regalia_v4_ue_export_sidecar.json"), "w"), indent=1, default=str)
print("V4UE-DONE")
