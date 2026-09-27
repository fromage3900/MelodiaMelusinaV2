"""Proof renders for the necklace.

Three rules carried from the earlier passes:
  * derive camera distance from the MEASURED extent (a hand-typed distance
    framed 0.144 m of a 0.294 m pair and rendered black)
  * identify the stone by CONNECTED COMPONENT, not a tuned window or "the
    biggest shells" (those were the loop rings)
  * build the stone material by CALLING build_stone -- importing regalia_stone
    creates nothing
"""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\regalia"
OUTDIR = os.path.join(HERE, "necklace")
os.makedirs(OUTDIR, exist_ok=True)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import regalia_necklace_build as NB  # noqa: E402


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for m in list(sys.modules):
        if m.startswith("surreal_arch"):
            del sys.modules[m]
    NB._import_house()

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 48
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 1400
    try:
        scene.view_settings.view_transform = "Standard"
        scene.view_settings.look = "None"
    except Exception:
        pass
    scene.view_settings.exposure = -1.1

    w = bpy.data.worlds.new("NeckWorld")
    scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.045, 0.040, 0.055, 1.0)
    bg.inputs[1].default_value = 0.35

    tree = NB.build_regalia_necklace_group()
    ob = bpy.data.objects.new("Necklace", bpy.data.meshes.new("M"))
    scene.collection.objects.link(ob)
    md = ob.modifiers.new("necklace", "NODES")
    md.node_group = tree

    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    oe = ob.evaluated_get(dg)
    new_mesh = bpy.data.meshes.new_from_object(oe)
    zs = [v.co.z for v in new_mesh.vertices]
    xs = [v.co.x for v in new_mesh.vertices]
    W = max(xs) - min(xs)
    H = max(zs) - min(zs)
    print("evaluated verts %d  extent %.4f x %.4f  z %.4f..%.4f" % (
        len(new_mesh.vertices), W, H, min(zs), max(zs)))

    # stone by connected component
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
                                     sorted(shells.values(), reverse=True)[:8]))

    import regalia_stone
    regalia_stone.build_stone("Void Orchid", "REGALIA_STONE")
    stone = bpy.data.materials.get("REGALIA_STONE")
    gold = bpy.data.materials.get("SurrealArch_Gold")
    new_mesh.materials.clear()
    if stone:
        new_mesh.materials.append(stone)
    if gold:
        new_mesh.materials.append(gold)
    # the pendant is the lowest shell: it hangs below everything else
    lows = {}
    for r in shells:
        lows[r] = min(verts[i].co.z for i in range(len(verts)) if find(i) == r)
    # The pendant CANNOT be found by connected component: it is welded to the
    # collar. Proven by subtraction -- the beads alone measure 7676 verts and
    # beads + drop measure 8716, so the drop's full 1040 verts ARE present,
    # split across the 16-vert tip shell, the 128-vert cord, and a bead shell it
    # touches. Four separate "find the isolated stone" rules each failed:
    # lowest-with->150-verts caught the cord, compact-box caught 19 beads, exact
    # box-equality caught 36, and vert-count<200 caught the cord's 128.
    #
    # Use the one thing that is AUTHORED and KNOWN: the drop's own translation
    # (0.0, -(COLLAR_R + 0.016), DROP_Z). Select every face whose centre is
    # within the drop's measured half-extent of that point.
    import regalia_necklace_build as _NB
    piv_x = 0.0
    piv_y = -0.012 - (_NB.COLLAR_R + 0.004)
    piv_z = _NB.DROP_Z
    # The crystal realizes 46 mm long, so its faces sit up to ~23 mm from the
    # pivot ALONG ITS OWN AXIS. A 30 mm ball around the pivot caught only 10
    # faces -- the tip and the loop -- because the body is 68 mm away at its
    # far end once the house Set Position.001 audio offset is included.
    # Select on the drop's own AXIS instead: a vertical capsule around the
    # pivot, tall enough for the full 46 mm crystal and narrow enough to miss
    # the collar beads (which are 82 mm out on x).
    half_xz = 0.026
    half_y = 0.030
    z_lo, z_hi = piv_z - 0.030, piv_z + 0.050
    drop_roots = None
    say_pivot = "pivot %.4f %.4f %.4f" % (piv_x, piv_y, piv_z)
    print(say_pivot)
    n_stone = 0
    for p in new_mesh.polygons:
        c = p.center
        if (abs(c.x - piv_x) < half_xz
                and abs(c.y - piv_y) < half_y
                and z_lo <= c.z <= z_hi):
            p.material_index = 0 if stone else 1
            n_stone += 1
        else:
            p.material_index = 1 if gold else 0
    print("stone faces: %d" % n_stone)
    ob.data = new_mesh
    ob.modifiers.remove(ob.modifiers[0])

    target = Vector((0.0, -0.012, (min(zs) + max(zs)) * 0.5))

    def area(name, loc, energy, size, color):
        d = bpy.data.lights.new(name, type="AREA")
        d.energy = energy
        d.size = size
        d.color = color
        o = bpy.data.objects.new(name, d)
        scene.collection.objects.link(o)
        o.location = loc
        o.rotation_euler = (target - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        return o

    area("NK", (-0.40, -0.50, 1.62), 15, 0.35, (1.0, 0.95, 0.88))
    area("NF", (0.44, -0.40, 1.42), 8, 0.5, (0.84, 0.90, 1.0))
    area("NR", (0.08, 0.46, 1.66), 13, 0.3, (1.0, 0.86, 0.72))

    cd = bpy.data.cameras.new("NeckCam")
    cam = bpy.data.objects.new("NeckCam", cd)
    scene.collection.objects.link(cam)
    scene.camera = cam

    def fit(width, height, lens, pad=1.5):
        hf = 2 * math.atan(18.0 / lens)
        vf = 2 * math.atan(12.0 / lens)
        return max((width * pad * 0.5) / math.tan(hf / 2),
                   (height * pad * 0.5) / math.tan(vf / 2))

    def shoot(tag, az, el, dist, tgt, lens=85):
        cd.lens = lens
        a, e = math.radians(az), math.radians(el)
        cam.location = Vector(tgt) + Vector(
            (-math.sin(a) * math.cos(e) * dist,
             -math.cos(a) * math.cos(e) * dist,
             math.sin(e) * dist))
        cam.rotation_euler = (Vector(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = os.path.join(OUTDIR, "necklace_%s.png" % tag)
        bpy.ops.render.render(write_still=True)
        print("shot " + tag)

    d = fit(W, H, 85)
    print("fit distance %.3f m" % d)
    shoot("front", 0, 6, d, target, lens=85)
    shoot("threequarter", 32, 12, d, target, lens=85)
    shoot("top", 0, 62, d, target, lens=85)
    shoot("macro_pendant", 12, 0, fit(0.030, 0.070, 100),
          (0.0, -0.100, min(zs) + 0.030), lens=100)
    print("NECKLACE-RENDER-COMPLETE")


main()
