"""Headless proof for the necklace.

New lesson, applied here: a house builder that RETURNS A TUPLE
`(tree, gin, gout)` is not a tree. Passing that tuple to
`modifier.node_group` raises a TypeError that names the type, so the failure is
loud -- but `build_nikki_bead_string` also needs its `Guide From Curve` switch
ON, and a nested consumer cannot satisfy the `Guide` OBJECT reference. Both
are gated here: a necklace that evaluated 0 verts while the graph looked
complete is exactly the failure mode of the crown and earring passes.
"""
import sys

import bpy

HERE = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\regalia"
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import regalia_necklace_build as NB  # noqa: E402

NECK_Z = NB.NECK_Z
NECK_HW = NB.NECK_HW
NECK_HD = NB.NECK_HD
COLLAR_R = NB.COLLAR_R
DROP_Z = NB.DROP_Z


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for m in list(sys.modules):
        if m.startswith("surreal_arch"):
            del sys.modules[m]
    NB._import_house()

    tree = NB.build_regalia_necklace_group()
    ob = bpy.data.objects.new("Necklace", bpy.data.meshes.new("M"))
    bpy.context.scene.collection.objects.link(ob)
    md = ob.modifiers.new("necklace", "NODES")
    md.node_group = tree

    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    oe = ob.evaluated_get(dg)
    ev = oe.to_mesh()
    verts = [v.co.copy() for v in ev.vertices] if ev else []
    oe.to_mesh_clear()

    g = {}
    if not verts:
        print("STATUS FAIL_NECKLACE 0/1")
        print("FAILED ['geometry']")
        print("NO GEOMETRY: the necklace evaluated empty")
        return

    xs = [v.x for v in verts]
    ys = [v.y for v in verts]
    zs = [v.z for v in verts]
    dims = [max(a) - min(a) for a in (xs, ys, zs)]
    print("evaluated: verts=%d dims=%.4f x %.4f x %.4f  z %.4f..%.4f" % (
        len(verts), dims[0], dims[1], dims[2], min(zs), max(zs)))

    # 1. geometry
    g["geometry"] = len(verts) > 500
    # 2. house builders nested
    nested = [n.node_tree.name for n in tree.nodes
              if n.bl_idname == "GeometryNodeGroup" and n.node_tree]
    print("house groups:", sorted(set(nested)))
    g["nests_house_builders"] = any("bead_string" in n for n in nested)
    # 3. EVERY geometry input is linked -- an unlinked one discards everything
    unlinked = []
    for n in tree.nodes:
        for s in n.inputs:
            if s.type == "GEOMETRY" and not s.is_linked and s.name == "Geometry":
                # a nested group node's own Geometry input may legitimately be
                # empty; a Set Material / Join / Transform may not
                if n.bl_idname in ("GeometryNodeSetMaterial",
                                   "GeometryNodeTransform",
                                   "GeometryNodeSetPosition"):
                    unlinked.append(n.name)
    print("unlinked geometry inputs:", unlinked)
    g["no_unlinked_geometry"] = not unlinked
    # 4. the collar encircles her neck: wider than the neck
    g["clears_the_neck"] = dims[0] > NECK_HW * 2 * 0.85
    # 5. and is not absurdly wide (a 0.5 m collar is a hoop, not a necklace)
    g["collar_width_sane"] = 0.10 < dims[0] < 0.28
    # 6. it sits at the neck, not the brow
    g["at_neck_height"] = abs((max(zs) + min(zs)) * 0.5 - NECK_Z) < 0.10
    # 7. something hangs BELOW the collar (the pendant)
    g["has_pendant"] = min(zs) < NECK_Z - 0.020
    # 8. nothing rises above the collar top (no beads floating overhead)
    g["nothing_above"] = max(zs) < NECK_Z + 0.075
    # 9. the drop is a plausible pendant size
    g["pendant_reaches"] = (NECK_Z - min(zs)) > 0.040
    # 10. a real material on the EVALUATED mesh (never the object -- a tree's
    #     Set Material emits slot order on the evaluated mesh only)
    oe2 = ob.evaluated_get(dg)
    me2 = oe2.to_mesh()
    emats = [m.name if m else None for m in me2.materials] if me2 else []
    oe2.to_mesh_clear()
    print("evaluated mesh materials:", emats)
    g["has_material"] = any(m for m in emats)
    # 11. the guide curve is actually connected to the bead string
    linked_guide = False
    for n in tree.nodes:
        if n.bl_idname == "GeometryNodeGroup" and n.node_tree \
                and "bead_string" in n.node_tree.name:
            for s in n.inputs:
                if s.name == "Guide Curve" and s.is_linked:
                    linked_guide = True
    print("guide curve linked to the bead string:", linked_guide)
    g["guide_is_wired"] = linked_guide

    failed = [k for k, ok in g.items() if not ok]
    print("STATUS %s %d/%d" % ("PASS_NECKLACE" if not failed else "FAIL_NECKLACE",
                               len(g) - len(failed), len(g)))
    print("FAILED %s" % failed)
    print("NECKLACE-VERIFY-COMPLETE")


main()
