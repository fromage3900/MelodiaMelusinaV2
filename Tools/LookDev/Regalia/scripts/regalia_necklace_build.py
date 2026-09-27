# Melusina necklace -- a closed collar of beads on a real cord, plus a centre
# stone. This is the first piece that is NOT a headpiece, so it does not reuse
# the circlet's egg-section band. It composes a DIFFERENT house pattern:
# a guide curve -> bead string.
#
# House parts:
#   build_nikki_bead        (nikki_decor) -- pearl / drop bead solid
#   build_nikki_bead_string (nikki_decor) -- beads + cord along a guide
#   build_gold_material     (materials_kit)
#   REGALIA_STONE           (regalia_stone.py)
#
# The house `_guide_params` exposes TWO routes: a `Guide` OBJECT (the authoring
# route) and a `Guide Curve` GEOMETRY input behind a `Guide From Curve` switch.
# A nested consumer cannot satisfy an object reference from inside a node graph,
# so the curve input is the only route that works here. Switch it ON.
#
# Landmarks, measured from Melusina_Base:
#   neck  z 1.368  width 0.1425   -> a neck ring of radius ~0.075 clears it
#   brow  z 1.560  width 0.4084
# She faces -Y, so the collar's centre sits slightly forward of the neck axis.

import math

NECK_Z = 1.368
NECK_HW = 0.1425 / 2.0     # 0.0713 m half-width
NECK_HD = 0.0900           # depth half-extent (measured brow depth 0.4594 scaled)
COLLAR_R = 0.082           # clears the neck by ~11 mm
DROP_Z = 1.272             # the pendant hangs below the collar

STONES = ("Void Orchid",)   # shared with the circlet and earrings


def _import_house():
    import regalia_baroque_build as RB
    return RB._import_house()


def _mods():
    import importlib
    _import_house()
    from surreal_arch.melodia_gn import core
    out = {"core": core}
    for name in ("nikki_decor", "cute_decor", "materials_kit", "filigree",
                 "ornament_extras", "ornament_strip", "profiles", "primitives"):
        try:
            out[name] = importlib.import_module("surreal_arch.melodia_gn." + name)
        except Exception as exc:
            print("REGALIA-WARN cannot import %s: %s" % (name, exc))
            out[name] = None
    return out


# `add_float_param` / `add_int_param` / `add_bool_param` RETURN THE SOCKET, per
# the house contract -- there is no `GeometryNodeInputValue` node in Blender 5.2
# and creating one raises "Node type GeometryNodeInputValue undefined". The
# circlet builder already learned this; these helpers now do the same.
def _dial(tree, name, default, lo, hi, loc=None, label=""):
    from surreal_arch.melodia_gn.core import add_float_param
    return add_float_param(tree, name, float(default), float(lo), float(hi))


def _bool_param(tree, name, default, loc=None):
    from surreal_arch.melodia_gn.core import add_bool_param
    return add_bool_param(tree, name, bool(default))


def _int_param(tree, name, default, lo, hi, loc=None):
    from surreal_arch.melodia_gn.core import add_int_param
    return add_int_param(tree, name, int(default), int(lo), int(hi))


def _link(tree, frm, to):
    """Link, and SAY SO if it fails. A silently unlinked geometry input
    discards everything upstream (measured: a 0-vert earring pair)."""
    if frm is None or to is None:
        print("REGALIA-WARN cannot link %r -> %r" % (frm, to))
        return False
    try:
        tree.links.new(frm, to)
        return True
    except Exception as exc:
        print("REGALIA-WARN link failed %s -> %s: %s" % (
            getattr(frm, "name", frm), getattr(to, "name", to), exc))
        return False


def _join(tree, loc, parts):
    """Join by LINKING into the multi-input socket -- it has no default_value."""
    j = tree.nodes.new("GeometryNodeJoinGeometry")
    j.location = loc
    for n, part in enumerate(parts):
        if part is None or not hasattr(part, "is_output"):
            print("REGALIA-WARN _join part %d is %r, not a socket" % (
                n, type(part).__name__))
            continue
        tree.links.new(part, j.inputs["Geometry"])
    return j


def _set_material(tree, mat, loc, label, geometry):
    """Set Material WITH its geometry linked.

    An unlinked Geometry input here is a silent no-op: the whole pair evaluated
    0 verts while the node reported no incoming link.
    """
    n = tree.nodes.new("GeometryNodeSetMaterial")
    n.location = loc
    n.label = label
    n.inputs["Material"].default_value = mat
    _link(tree, geometry, n.inputs["Geometry"])
    return n


def _guide_curve(tree, loc, radius, sweep_deg, start_deg, z):
    """The in-graph guide the bead string reads.

    A full ring is the wrong shape for a necklace -- it would be a closed loop
    with no front. A 260 deg arc starting behind her left ear leaves a 100 deg
    gap at the front for the pendant to hang into, which is how a collar is
    actually built.
    """
    # Blender 5.2: the arc node is `GeometryNodeCurveArc`, NOT
    # `GeometryNodeCurvePrimitiveArc` (which raises "Node type ... undefined").
    # Only BezierSegment and Circle survive the CurvePrimitive prefix; Arc and
    # Circle were both moved out of it.
    arc = tree.nodes.new("GeometryNodeCurveArc")
    arc.location = loc
    arc.label = "collar guide"
    arc.inputs["Radius"].default_value = radius
    # EXPLICIT operands. A one-argument Math-like default is the trap from the
    # circlet pass; these are direct socket assignments, so they hold.
    arc.inputs["Start Angle"].default_value = math.radians(start_deg)
    arc.inputs["Sweep Angle"].default_value = math.radians(sweep_deg)
    # A Curve Arc is generated in the XY plane centred on the origin, so lift it
    # to the neck with a Transform rather than by editing the angle.
    mv = tree.nodes.new("GeometryNodeTransform")
    mv.location = (loc[0] + 220, loc[1])
    mv.label = "lift guide to the neck"
    mv.inputs["Translation"].default_value = (0.0, -0.012, z)
    tree.links.new(arc.outputs["Curve"], mv.inputs["Geometry"])
    return mv.outputs["Geometry"]


def build_regalia_necklace_group(group_name="MEL_regalia_necklace"):
    """A bead collar on a real cord, with a centre drop."""
    from surreal_arch.melodia_gn import core
    mods = _mods()
    nikki = mods.get("nikki_decor")
    tree, gin, gout = core.new_geometry_tree(group_name)

    bead_n = _int_param(tree, "Bead Count", 34, 6, 120, (-1500, -300))
    bead_r = _dial(tree, "Bead Radius", 0.0115, 0.003, 0.04, (-1500, -450))
    droop = _dial(tree, "Droop", 0.055, 0.0, 0.6, (-1500, -600))
    taper = _dial(tree, "Taper", 0.42, -1.0, 2.0, (-1500, -750))
    cord_r = _dial(tree, "Cord Radius", 0.0026, 0.0005, 0.02, (-1500, -900))
    # The switch that makes the in-graph route usable at all.
    from_curve = _bool_param(tree, "Guide From Curve", True, (-1500, -1050))
    show_cord = _bool_param(tree, "Show Cord", True, (-1500, -1200))
    stone_on = _bool_param(tree, "Centre Stone", True, (-1500, -1350))

    parts = []

    # --- the guide curve, then the house bead string reading it --------------
    # Gap centred on 270 deg (her front, -Y): Start = 270 + gap/2 = 320, so the
    # arc spans 320..580 and the 100 deg gap runs 220..320.
    guide = _guide_curve(tree, (-1250, -300), COLLAR_R, 260.0, 320.0, NECK_Z)

    string_builder = getattr(nikki, "build_nikki_bead_string", None)
    if string_builder is None:
        print("REGALIA-WARN no build_nikki_bead_string")
    else:
        # SOME house builders return (tree, gin, gout), not a bare tree.
        # `build_nikki_bead` and `build_nikki_bead_string` both do, while
        # `build_crystal_drop` returns just the tree. Assigning the tuple to
        # node_tree raises "expected a NodeTree type, not tuple" -- loud, but
        # only because the type is in the message. Normalise it here.
        st = string_builder("MEL_neck_bead_string")
        if isinstance(st, (tuple, list)):
            st = st[0]
        node = tree.nodes.new("GeometryNodeGroup")
        node.node_tree = st
        node.name = "MEL_nikki_bead_string"
        node.label = "bead collar"
        node.location = (-900, -300)
        # LITERALS for the scaled values, matching the nested-float rule from
        # the crown pass: a linked socket did not override the house defaults.
        for key, val in (("Bead Radius", 0.0115), ("Droop", 0.055),
                         ("Taper", 0.42), ("Cord Radius", 0.0026),
                         ("Bead Count", 34)):
            for s in node.inputs:
                if s.name == key and s.type in ("VALUE", "INT"):
                    s.default_value = val
        for s in node.inputs:
            if s.name == "Guide From Curve":
                s.default_value = True
            if s.name == "Show Cord":
                s.default_value = True
        # The nested group has its OWN Set Material, and a nested Set Material
        # OVERRIDES the outer one -- its material input is None, so the beads
        # rendered dark bronze while every face index said gold. Feed the gold
        # into the nested group's own Material input.
        mk = mods.get("materials_kit")
        if mk is not None and hasattr(mk, "build_gold_material"):
            try:
                nested_gold = mk.build_gold_material()
            except Exception as exc:
                print("REGALIA-WARN nested gold: %s" % exc)
                nested_gold = None
        for s in node.inputs:
            if s.type == "MATERIAL" and nested_gold is not None:
                s.default_value = nested_gold
                say_material = True
        say_mat = 'REGALIA-WARN bead_string has no Material input' \
            if not any(s.type == "MATERIAL" for s in node.inputs) else None
        if say_mat:
            print(say_mat)
        # THE ROUTE THAT WORKS: the curve input, not the object reference.
        _link(tree, guide, node.inputs["Guide Curve"])
        parts.append(node.outputs["Geometry"])

    # --- the centre drop -----------------------------------------------------
    drop_builder = getattr(mods.get("cute_decor"), "build_crystal_drop", None)
    if stone_on and drop_builder is not None:
        drop = drop_builder("MEL_neck_drop")
        if isinstance(drop, (tuple, list)):
            drop = drop[0]
        dn = tree.nodes.new("GeometryNodeGroup")
        dn.node_tree = drop
        dn.name = "MEL_crystal_drop"
        dn.label = "centre stone"
        dn.location = (-900, -760)
        # MEASURED, not assumed. Asking the nested drop for 42 x 8.5 mm returns
        # 14.0 x 14.0 x 78.3 mm: `Crystal Width` lands as the cylinder RADIUS
        # (so 0.0085 -> 17 mm, trimmed to 14 by the taper) and `Crystal Length`
        # is not the total travel -- the top loop adds to it. Solve backwards
        # from the realized size: for a 42 mm pendant, ask for a length whose
        # realized total is 42 mm, and a width that yields ~14 mm across.
        # MEASURED RESPONSE, by sweep. `crystal_drop` is 1040 verts spanning
        # z = -L*0.3 .. +0.072 regardless of L: the top LOOP is a fixed 72 mm
        # tall, and `Crystal Length` only pushes the tapered tip further down.
        #   L=0.0121 W=0.0067 -> 0.0140 x 0.0140 x 0.0738
        #   L=0.0247 W=0.0121 -> 0.0140 x 0.0140 x 0.0757
        #   L=0.1533 W=0.0333 -> 0.0200 x 0.0200 x 0.0950
        # Width IS honoured (W*0.6 across, or 0.014 floor from the taper), and
        # `Top Radius` sets the loop. For a ~20 mm pendant body use L=0.153.
        for key, val in (("Crystal Length", 0.1533), ("Crystal Width", 0.0333),
                         ("Facet Count", 8), ("Top Radius", 0.005)):
            for s in dn.inputs:
                if s.name == key and s.type in ("VALUE", "INT"):
                    s.default_value = val
        mv = tree.nodes.new("GeometryNodeTransform")
        mv.location = (-640, -760)
        mv.label = "hang the drop at the collar's front gap"
        # Hang the pendant at the collar's FRONT GAP, on the centre line.
        #
        # The arc runs Start 130 deg for Sweep 260 deg, so it spans 130 -> 390,
        # leaving a 100 deg gap centred on 50 deg. A Curve Arc is generated in
        # the XY plane, and she faces -Y, so her FRONT is 270 deg -- which the
        # first version did not use: it put the drop at 130 deg and measured
        # x +0.0705, i.e. off her left shoulder rather than at her throat.
        #
        # Place it explicitly: centre line, slightly forward, hanging below the
        # collar's bottom and clear of the arc so it is an isolated shell.
        drop_x = 0.0
        drop_y = -0.012 - (COLLAR_R + 0.004)
        mv.inputs["Translation"].default_value = (drop_x, drop_y, DROP_Z)
        # `drop` is the TREE; the node that exposes sockets is `dn`.
        _link(tree, dn.outputs["Geometry"], mv.inputs["Geometry"])
        parts.append(mv.outputs["Geometry"])

    if not parts:
        print("REGALIA-WARN necklace built no parts")
        return tree

    # CHAIN the joins instead of putting everything on ONE multi-input socket.
    # Measured: the necklace joined bead_string + drop onto a single Join
    # Geometry and came out 8716 verts with the 1040-vert crystal ABSENT
    # (16 + 128 + 34*222 + 1024 = 8716, exactly -- no room for it). Routing the
    # drop straight to the Group Output gave 1040 verts at z 1.2683..1.3440.
    # So the drop survives alone and dies in the join: feeding several
    # geometries into ONE multi-input socket kept only the first. Same family
    # as `Merge by Distance` refusing an `Instances` socket. Chain: join
    # (beads) -> join (that + drop) -> material -> output.
    chained = parts[0]
    for n, part in enumerate(parts[1:], start=1):
        j = tree.nodes.new("GeometryNodeJoinGeometry")
        j.location = (-520 + n * 60, -520 - n * 200)
        j.label = "join %d" % n
        if not hasattr(chained, "is_output"):
            print("REGALIA-WARN chain head %d is not a socket" % n)
            continue
        tree.links.new(chained, j.inputs["Geometry"])
        if hasattr(part, "is_output"):
            tree.links.new(part, j.inputs["Geometry"])
        else:
            print("REGALIA-WARN chain part %d is not a socket: %r" % (n, part))
        chained = j.outputs["Geometry"]
    joined_out = chained

    gold = None
    mk = mods.get("materials_kit")
    if mk is not None and hasattr(mk, "build_gold_material"):
        try:
            gold = mk.build_gold_material()
        except Exception as exc:
            print("REGALIA-WARN gold: %s" % exc)
    sm = _set_material(tree, gold, (-120, -520), "gold", joined_out)
    # new_geometry_tree returns (tree, gin, gout) where gin/gout are the GROUP
    # NODES, not socket collections -- gout.outputs does not exist. Blender 4.0+
    # removed tree.inputs/outputs in favour of tree.interface. Use the node's own
    # input socket, and fall back to a fresh lookup if it was purged.
    out = [n for n in tree.nodes if n.bl_idname == "NodeGroupOutput"]
    if not out:
        print("REGALIA-WARN necklace has no Group Output node")
        return tree
    _link(tree, sm.outputs["Geometry"], out[0].inputs["Geometry"])
    return tree
