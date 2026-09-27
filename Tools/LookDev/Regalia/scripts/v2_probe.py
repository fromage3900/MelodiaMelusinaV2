import bpy, bmesh, sys, os, json
W = r"C:\EnvironmentPortfolio\_lookdev_work\regalia_v2"
sys.path.insert(0, W + r"\scripts")
import regalia_baroque_build as RB
RB.REPO_GN = W + r"\pkg"; RB.APPDATA_GN = r"Z:\__none__"
RB._import_house()
import surreal_arch
print("PKG", surreal_arch.__file__)
from surreal_arch.melodia_gn import mesh_tools
print("MESHTOOLS", mesh_tools.__file__)
import regalia_earring_build as RE, regalia_necklace_build as RN

def realize(tree):
    gout = [n for n in tree.nodes if n.bl_idname == "NodeGroupOutput"][0]
    sock = gout.inputs["Geometry"]
    if sock.is_linked:
        src = sock.links[0].from_socket
        r = tree.nodes.new("GeometryNodeRealizeInstances")
        tree.links.new(src, r.inputs["Geometry"]); tree.links.new(r.outputs["Geometry"], sock)

def probe(name, tree):
    if isinstance(tree,(tuple,list)): tree=tree[0]
    realize(tree)
    me = bpy.data.meshes.new(name); ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    m = ob.modifiers.new("g","NODES"); m.node_group = tree
    dg = bpy.context.evaluated_depsgraph_get()
    nm = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    mats = [x.name if x else None for x in nm.materials]
    cnt = {}
    for p in nm.polygons: cnt[p.material_index] = cnt.get(p.material_index,0)+1
    bm = bmesh.new(); bm.from_mesh(nm); bm.verts.ensure_lookup_table()
    # islands
    seen=set(); isl=[]
    for v in bm.verts:
        if v.index in seen: continue
        st=[v]; seen.add(v.index); comp=[]
        while st:
            x=st.pop(); comp.append(x)
            for e in x.link_edges:
                o=e.other_vert(x)
                if o.index not in seen: seen.add(o.index); st.append(o)
        xs=[c.co for c in comp]
        mn=[min(c[i] for c in xs) for i in range(3)]; mx=[max(c[i] for c in xs) for i in range(3)]
        mi=set()
        for c in comp:
            for f in c.link_faces: mi.add(f.material_index)
        isl.append((len(comp), [round(a,4) for a in mn],[round(a,4) for a in mx], sorted(mi)))
    isl.sort(key=lambda t:-t[0])
    print("PROBE", name, "verts", len(nm.vertices), "mats", mats, "faces/mat", cnt, "islands", len(isl))
    for i in isl[:12]: print("   ISL", i)
    if len(isl)>12: print("   ... small islands:", [i[0] for i in isl[12:40]])

probe("circlet", RB.build_piece("MEL_regalia_circlet"))
probe("tiara", RB.build_piece("MEL_regalia_tiara"))
probe("earrings", RE.build_regalia_earring_pair())
probe("necklace", RN.build_regalia_necklace_group())
M = RB._mods()
cd = __import__("surreal_arch.melodia_gn.cute_decor", fromlist=["x"])
for bn in ("build_star_dangl","build_lace_dangl","build_bow_dangl","build_heart_dangl","build_pearl_dangl"):
    f = getattr(cd, bn, None)
    if f:
        try: probe(bn, f(bn))
        except Exception as e: print("PROBE-ERR", bn, e)
    else: print("NO", bn)
