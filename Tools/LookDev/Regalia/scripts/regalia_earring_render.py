"""Proof renders for the earring pair.

Same two rules the crown pass learned:
  * the stone is identified by CONNECTED COMPONENT (the tree's Set Material
    cannot reach the object -- measured [] on the object, [None, 'Gold'] on the
    evaluated mesh), so the render must find it geometrically
  * render the asset WITHOUT the head proxy, or the proxy hides it
"""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\regalia"
OUTDIR = os.path.join(HERE, "earrings")
os.makedirs(OUTDIR, exist_ok=True)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import regalia_earring_build as EB  # noqa: E402

EAR_L = EB.EAR_L
EAR_R = EB.EAR_R
CENTRE = ((EAR_L[0] + EAR_R[0]) * 0.5, (EAR_L[1] + EAR_R[1]) * 0.5,
          (EAR_L[2] + EAR_R[2]) * 0.5)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for m in list(sys.modules):
        if m.startswith("surreal_arch"):
            del sys.modules[m]
    EB._import_house()

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 48
    scene.render.resolution_x = 1500
    scene.render.resolution_y = 1000
    try:
        scene.view_settings.view_transform = "Standard"
        scene.view_settings.look = "None"
    except Exception:
        pass
    scene.view_settings.exposure = -1.2

    w = bpy.data.worlds.new("EarWorld")
    scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.048, 0.042, 0.058, 1.0)
    bg.inputs[1].default_value = 0.35

    tree = EB.build_regalia_earring_pair()
    ob = bpy.data.objects.new("Earrings", bpy.data.meshes.new("M"))
    scene.collection.objects.link(ob)
    md = ob.modifiers.new("earrings", "NODES")
    md.node_group = tree

    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    oe = ob.evaluated_get(dg)
    new_mesh = bpy.data.meshes.new_from_object(oe)
    zs = [v.co.z for v in new_mesh.vertices]
    print("evaluated verts %d  z %.4f..%.4f" % (len(new_mesh.vertices),
                                                 min(zs), max(zs)))

    # the two drops are the only separate shells; find them by union-find and
    # give them the surreal stone
    verts = new_mesh.vertices
    parent = list(range(len(verts)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for e in new_mesh.edges:
        ra, rb = find(e.vertices[0]), find(e.vertices[1])
        if ra != rb:
            parent[rb] = ra
    import collections
    shells = collections.Counter(find(v.index) for v in verts)
    print("shells: %d  sizes %s" % (len(shells),
                                     sorted(shells.values(), reverse=True)[:6]))

    # Importing regalia_stone does NOT build the materials -- they only exist
    # after build_stone()/build_all() runs. Fetching the name first found None
    # and every "stone" face fell back to gold.
    stone = bpy.data.materials.get("REGALIA_STONE")
    if stone is None:
        import regalia_stone
        # signature is build_stone(key, name) -- it takes a PALETTE KEY, not
        # hue/sat numbers. "Void Orchid" is the circlet's centre stone, so the
        # earrings share the house amethyst.
        regalia_stone.build_stone("Void Orchid", "REGALIA_STONE")
        stone = bpy.data.materials.get("REGALIA_STONE")
    gold = bpy.data.materials.get("SurrealArch_Gold")
    new_mesh.materials.clear()
    if stone:
        new_mesh.materials.append(stone)
    if gold:
        new_mesh.materials.append(gold)
    # The four 1024-vert shells are the top LOOPS (thin rings); the crystals are
    # the 200-vert prisms. Picking the two BIGGEST shells, as the first version
    # did, painted the loops as stone and left the actual drops gold. Select by
    # the crystal's own signature: a compact filled body, not a ring.
    drop_roots = [r for r, n in shells.most_common() if n <= 400]
    print("drop shells:", sorted(shells[r] for r in drop_roots))
    n_stone = 0
    for p in new_mesh.polygons:
        if find(p.vertices[0]) in drop_roots:
            p.material_index = 0 if stone else 1
            n_stone += 1
        else:
            p.material_index = 1 if gold else 0
    print("stone faces: %d (stone material %s)" % (n_stone, stone.name if stone else None))
    ob.data = new_mesh
    ob.modifiers.remove(ob.modifiers[0])

    def area(name, loc, energy, size, color):
        d = bpy.data.lights.new(name, type="AREA")
        d.energy = energy
        d.size = size
        d.color = color
        o = bpy.data.objects.new(name, d)
        scene.collection.objects.link(o)
        o.location = loc
        o.rotation_euler = (Vector(CENTRE) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        return o

    area("EK", (-0.42, -0.55, 1.90), 16, 0.35, (1.0, 0.95, 0.88))
    area("EF", (0.48, -0.42, 1.62), 8, 0.5, (0.84, 0.90, 1.0))
    area("ER", (0.10, 0.52, 1.95), 14, 0.3, (1.0, 0.86, 0.72))

    cd = bpy.data.cameras.new("EarCam")
    cd.lens = 85
    cam = bpy.data.objects.new("EarCam", cd)
    scene.collection.objects.link(cam)
    scene.camera = cam

    # Frame from the MEASURED extent, not a guessed distance. A hand-typed
    # 0.34 m at 85 mm frames only 0.144 m of a 0.294 m pair, so the earrings
    # were cropped to a sliver and the render came back black (max channel sum
    # 67 of 765). Required distance for width W at focal length f on a 36 mm
    # sensor is (W/2) / tan(atan(18/f)).
    xs = [v.co.x for v in new_mesh.vertices]
    ys = [v.co.y for v in new_mesh.vertices]
    W = max(xs) - min(xs)
    H = max(zs) - min(zs)
    print("extent %.4f x %.4f" % (W, H))

    def fit_dist(width, height, lens, pad=1.45):
        hf = 2 * math.atan(18.0 / lens)
        vf = 2 * math.atan(12.0 / lens)   # 24 mm sensor height
        return max((width * pad * 0.5) / math.tan(hf / 2),
                   (height * pad * 0.5) / math.tan(vf / 2))

    def shoot(tag, az, el, dist, target, lens=85):
        cd.lens = lens
        a, e = math.radians(az), math.radians(el)
        cam.location = Vector(target) + Vector(
            (-math.sin(a) * math.cos(e) * dist,
             -math.cos(a) * math.cos(e) * dist,
             math.sin(e) * dist))
        cam.rotation_euler = (Vector(target) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = os.path.join(OUTDIR, "earrings_%s.png" % tag)
        bpy.ops.render.render(write_still=True)
        print("shot " + tag)

    d_pair = fit_dist(W, H, 85)
    print("fit distance for the pair at 85 mm: %.3f m" % d_pair)
    shoot("front", 0, 4, d_pair, CENTRE, lens=85)
    shoot("threequarter", 30, 10, d_pair, CENTRE, lens=85)
    # a macro on ONE drop: 34 mm long, 13 mm wide
    lx, ly, lz = EAR_L
    shoot("macro_left", 16, 2, fit_dist(0.020, 0.100, 100), (lx, ly, lz - 0.045),
          lens=100)
    print("EARRING-RENDER-COMPLETE")


main()
