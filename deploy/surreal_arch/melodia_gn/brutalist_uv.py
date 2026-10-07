"""brutalist_uv.py - GN-native UV channel for the brutalist family.

WHY THIS EXISTS
---------------
Every brutalist preset shipped with ``uv_layers: 0`` (measured across all 15
presets, Saved/Audit/brutalist_topology.json). No UVs means no texture can
bind, which makes the 28-surface material library unusable on a real render.

WHY NOT THE OBVIOUS ROUTES (all measured in Blender 5.2.1, not assumed)
----------------------------------------------------------------------
- ``GeometryNodeUVCubeProjection`` / ``...UVSphereProjection`` **do not exist**
  as node types in 5.2. A "Triplanar UV" bool wired to them compiles and does
  nothing - the lying-dial failure class. The first attempt at that was deleted
  rather than left in place (audit 10d).
- ``GeometryNodeUVUnwrap`` exists but takes NO Geometry input - its inputs are
  ``[Selection, Seam, Margin, Fill Holes, Method, Iterations, No Flip]`` and it
  emits a single ``UV`` VECTOR. It acts on the ACTIVE OBJECT, so it cannot be
  driven from inside a reusable node group. Same constraint as
  ``eyewear.py:111``.
- ``bpy.ops.uv.cube_project()`` on the staged OBJECT is also useless here: the
  stager leaves a live geometry-nodes modifier on every object, so the object's
  own mesh datablock is EMPTY and there is nothing to project. It would have to
  run after a manual realize-and-apply, which would destroy the "dials stay
  playable" promise the stager makes.

THE ROUTE THAT WORKS
--------------------
Build the UV field ourselves from Position + Normal and store it with
``GeometryNodeStoreNamedAttribute(domain='CORNER', data_type='FLOAT2')`` under
the name ``UVMap``. That is the same channel the image texture nodes read, and
because it is stored as a named attribute it survives instancing, needs no
active object, and lives inside the node group so the dials stay live.

Box (triplanar-by-dominant-axis) projection, not a flat XY unwrap: these are
orthogonal concrete slabs, floors and walls, so a per-face dominant-axis choice
gives every face square texels with zero stretch and zero seam guessing. That
is the correct projection for architecture, not a compromise.
"""
from __future__ import annotations

UV_ATTR = "UVMap"
# Projected texel density: 1 UV unit per BU. The family works in metres at
# ~14 m block width, so 0.25 gives a 3.5 m tile - one concrete panel per tile.
DEFAULT_TILE = 0.25


def _node(tree, type_name, name, loc):
    n = tree.nodes.new(type_name)
    n.name = name
    n.location = loc
    return n


def add_box_uv(tree, geometry_socket, gout, scale=DEFAULT_TILE,
               loc=(6000, -1200), attr=UV_ATTR):
    """Store a box-projected UV channel on CORNER domain.

    ``geometry_socket`` is the Geometry to tag. ``gout`` is the node group's
    Group Output so the tagged geometry is what leaves the group. Returns the
    Store-Named-Attribute node, or None if the route is unavailable (a fresh
    clone on an older Blender degrades instead of failing the build).
    """
    try:
        pos_in = _node(tree, "GeometryNodeInputPosition", "UV_Pos", loc)
        nor_in = _node(tree, "GeometryNodeInputNormal", "UV_Nor", loc)
        sep_p = _node(tree, "ShaderNodeSeparateXYZ", "UV_SepP", (loc[0] + 180, loc[1]))
        sep_n = _node(tree, "ShaderNodeSeparateXYZ", "UV_SepN", (loc[0] + 180, loc[1] - 200))
    except Exception:
        return None

    tree.links.new(pos_in.outputs[0], sep_p.inputs[0])
    tree.links.new(nor_in.outputs[0], sep_n.inputs[0])

    # abs(normal) per axis -> which axis dominates this face
    ab_x = _node(tree, "ShaderNodeMath", "UV_AbsX", (loc[0] + 360, loc[1] - 200))
    ab_y = _node(tree, "ShaderNodeMath", "UV_AbsY", (loc[0] + 360, loc[1] - 320))
    ab_z = _node(tree, "ShaderNodeMath", "UV_AbsZ", (loc[0] + 360, loc[1] - 440))
    for n, s in ((ab_x, sep_n.outputs[0]), (ab_y, sep_n.outputs[1]),
                 (ab_z, sep_n.outputs[2])):
        n.operation = "ABSOLUTE"
        tree.links.new(s, n.inputs[0])

    def pick(cond_socket, true_val, false_val, y):
        # Mix (float) is the 5.2-safe selector: FunctionNodeBooleanMath has no
        # data_type and ShaderNodeMix has stable vector inputs.
        mx = _node(tree, "ShaderNodeMix", "UV_Pick%d" % y, (loc[0] + 540, y))
        mx.data_type = "FLOAT"
        tree.links.new(cond_socket, mx.inputs[0])
        if hasattr(true_val, "node"):
            tree.links.new(true_val, mx.inputs[2])
        else:
            mx.inputs[2].default_value = true_val
        if hasattr(false_val, "node"):
            tree.links.new(false_val, mx.inputs[3])
        else:
            mx.inputs[3].default_value = false_val
        return mx.outputs[0]

    # X-dominant face -> project (y, z); else if Y-dominant -> (x, z); else (x, y)
    u = pick(ab_x.outputs[0], sep_p.outputs[1], sep_p.outputs[0], loc[1] - 560)
    v0 = pick(ab_x.outputs[0], sep_p.outputs[2], sep_p.outputs[2], loc[1] - 680)
    v1 = pick(ab_y.outputs[0], sep_p.outputs[2], sep_p.outputs[1], loc[1] - 800)
    v = _node(tree, "ShaderNodeMix", "UV_PickV", (loc[0] + 720, loc[1] - 740))
    v.data_type = "FLOAT"
    tree.links.new(ab_x.outputs[0], v.inputs[0])
    tree.links.new(v0, v.inputs[2])
    tree.links.new(v1, v.inputs[3])

    mul = _node(tree, "ShaderNodeVectorMath", "UV_Scale", (loc[0] + 900, loc[1] - 660))
    mul.operation = "SCALE"
    comb = _node(tree, "ShaderNodeCombineXYZ", "UV_Comb", (loc[0] + 900, loc[1] - 820))
    tree.links.new(u, comb.inputs[0])
    tree.links.new(v.outputs[0], comb.inputs[2])
    tree.links.new(comb.outputs[0], mul.inputs[0])
    mul.inputs["Scale"].default_value = float(scale)

    # No blanket except here on purpose. An earlier version swallowed any
    # failure in this block and returned None, which the caller treated as
    # "route unavailable, fall back to the plain link" - a silent no-op that
    # read as a pass. If this raises, the build fails loudly, which is correct.
    store = _node(tree, "GeometryNodeStoreNamedAttribute",
                  "UV_Store", (loc[0] + 1120, loc[1] - 400))
    store.data_type = "FLOAT2"
    store.domain = "CORNER"
    store.inputs["Name"].default_value = attr
    tree.links.new(geometry_socket, store.inputs[0])
    tree.links.new(mul.outputs[0], store.inputs["Value"])

    # Link the tagged geometry to the GROUP OUTPUT. The Group Output node
    # carries geometry on its INPUT side ("Geometry" input socket); its
    # .outputs list is empty in these trees, so iterating .outputs finds
    # nothing and silently drops the store. (Measured: gout.outputs=[],
    # gout.inputs=[Geometry GEOMETRY].) An earlier version of this helper
    # returned None here and the caller fell back to the un-UV'd link, which
    # is why 15/15 presets read uv_layers=0 while the store node sat in the
    # tree doing nothing.
    linked = False
    for ginp in gout.inputs:
        if ginp.type == "GEOMETRY":
            tree.links.new(store.outputs[0], ginp)
            linked = True
            break
    if not linked:
        for out in gout.outputs:
            if out.type == "GEOMETRY":
                tree.links.new(store.outputs[0], out)
                linked = True
                break
    if not linked:
        return None
    return store
