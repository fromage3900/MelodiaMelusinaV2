# FLIP surface sequence -> single Alembic (staged for the next Blender window).
# Reads the verified cache and exports one ABC with per-frame topology变化 handled
# by Alembic's per-frame mesh samples. Run: blender -b <any .blend> -P this_file.py
# (uses bpy.data.libraries-free standalone scene; cache path is absolute).
import bpy, os, struct

CACHE = r"C:\EnvironmentPortfolio\FlipCache\hair_hero_20260922\bakefiles"
OUT = r"C:\EnvironmentPortfolio\BS_GodFile\Exports\MelusinaBakeStaging_20260922\FlipCache\flip_surface_sequence.abc"
os.makedirs(os.path.dirname(OUT), exist_ok=True)

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 240
scene.render.fps = 24

# One animated mesh object: mesh data swapped per frame via Shape Keys is not
# possible across changing topology, so Alembic export uses the archive writer's
# per-frame samples via a MeshSequence cache modifier-friendly route:
# build 240 objects and export the COLLECTION (Alembic writes each as a
# transform + mesh sample; visibility keys carry over as .visible flags).
col = bpy.data.collections.get("FLIPMeshes") or bpy.data.collections.new("FLIPMeshes")
scene.collection.children.link(col)

def read_bobj(p):
    with open(p, "rb") as f:
        data = f.read()
    nv = struct.unpack_from("<i", data, 0)[0]
    off = 4
    verts = list(struct.unpack_from("<%df" % (nv * 3), data, off))
    off += nv * 12
    nt_ = struct.unpack_from("<i", data, off)[0]
    tris = list(struct.unpack_from("<%di" % (nt_ * 3), data, off + 4)) if nt_ else []
    return nv, verts, nt_, tris

frames = {int(fn[:-5]): os.path.join(CACHE, fn)
          for fn in os.listdir(CACHE) if fn.endswith(".bobj") and fn[:-5].isdigit()}
for f in sorted(frames):
    name = "FLIP_surface_%04d" % f
    if name in bpy.data.objects:
        continue
    nv, vflat, ntri, tris = read_bobj(frames[f])
    if ntri == 0:
        continue
    me = bpy.data.meshes.new(name)
    me.vertices.add(nv)
    me.vertices.foreach_set("co", vflat)
    me.loops.add(ntri * 3)
    me.loops.foreach_set("vertex_index", tris)
    me.polygons.add(ntri)
    me.polygons.foreach_set("loop_start", range(0, ntri * 3, 3))
    me.polygons.foreach_set("loop_total", [3] * ntri)
    me.update()
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    for ff, vis in ((f - 1, 1), (f, 0), (f + 1, 1)):
        if scene.frame_start <= ff <= scene.frame_end + 1:
            ob.hide_render = bool(vis)
            ob.keyframe_insert("hide_render", frame=ff)

bpy.ops.wm.alembic_export(
    filepath=OUT, start=scene.frame_start, end=scene.frame_end, xsamples=1,
    flatten=True, uvs=True, packuv=False, face_sets=False,
    selected=False, visible_objects_only=False)
print("ALEMBIC_EXPORTED:", OUT, os.path.getsize(OUT) if os.path.isfile(OUT) else "MISSING")
