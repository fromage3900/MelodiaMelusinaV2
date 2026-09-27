# Melusina earrings -- a PAIR, seated on the measured ear bones.
#
# Composition rules (from the crown pass, learned the hard way):
#   * every house module a branch reaches for must be in _mods()
#   * a dial SOCKET is never None -- branch on a python bool
#   * nested-group FLOAT params need LITERALS, not linked sockets
#   * placement for a known-constant piece is PYTHON, not a socket chain
#   * render each element with the PROXY out of the way, or it occludes
#
# House parts used:
#   build_crystal_drop  (cute_decor) -- faceted pendant with a top loop
#
# MEASURED: crystal_drop's local Z runs -0.018 .. +0.072, i.e. it GROWS UPWARD
# from its own origin. A drop hung from a lobe must therefore be ROTATED 180
# about X, or the stone points up off the ear like a horn. Rotating (x,y,z) by
# pi about X maps (x,-y,-z), so the stone then occupies -0.072..+0.018 and its
# TOP LOOP -- which is at local z ~ +0.072 -- ends up at the BOTTOM. Hanging it
# means rotating so the loop is at the lobe: pi about X puts the loop down, so
# the pendant hangs from the loop's new position at the top of the travel.

# REJECTED: build_tassel_dangl (cute_decor). Its strands are Cylinder instances
# displaced by `Scene Time` through an audio Math node, and it measures 1.67 m
# across at jewellery params -- the cylinders are never scaled to the strand
# length. It is a time-driven curtain, not a static drop, and it wrecked the
# pair's extents (reaching x 0.4239 on a lobe at 0.1369). The second layer is a
# second CRYSTAL instead: a smaller drop below the first.
#   build_gold_material  (materials_kit)
#   REGALIA_STONE        (regalia_stone.py) -- the surreal gem
#
# Attachment is BAKED INTO WORLD SPACE. Do NOT parent to c_ear_01.*: the
# landmark receipt records that bone-parenting threw a headpiece to y=-1.72,
# about 1.5 m off the skull. The two lobes are NOT symmetric -- the measured
# bones differ by 4 mm in X -- so each side is placed on its own value.

import math

# measured from Melusina_Base, live MCP 9876 (regalia_landmarks.json)
EAR_L = (0.1369, -0.1635, 1.5316)   # c_ear_01.l
EAR_R = (-0.1449, -0.1629, 1.5292)  # c_ear_01.r

STUD = 0.008      # lobe -> crystal top
DROP_LEN = 0.034  # faceted crystal length
DROP_WID = 0.013  # crystal width at its widest (dial default)
FRINGE = 0.026    # tassel below the crystal


def _import_house():
    """Register the house package and put it on sys.path.

    Reuses the circlet builder's own routine rather than re-implementing it:
    the package must be REGISTERED (not merely importable) before its builders
    are called, and a second copy here drifted out of step with it.
    """
    import regalia_baroque_build as RB
    return RB._import_house()


def _mods():
    """The house modules this builder composes, imported as submodules.

    `cute_decor` supplies build_crystal_drop and build_tassel_dangl. It was
    missing from the circlet's list once and the whole finial branch silently
    did nothing while every gate passed -- a builder that never ran cannot be
    measured. Every module a branch reaches for belongs here, and a missing
    module must be LOUD, not None.
    """
    import importlib
    _import_house()
    from surreal_arch.melodia_gn import core
    out = {"core": core}
    for name in ("filigree", "ornament_extras", "nikki_decor", "materials_kit",
                 "ornament_strip", "profiles", "cute_decor", "primitives"):
        try:
            out[name] = importlib.import_module("surreal_arch.melodia_gn." + name)
        except Exception as exc:
            print("REGALIA-WARN cannot import %s: %s" % (name, exc))
            out[name] = None
    return out


def _dial(tree, name, default, lo, hi, loc, label=""):
    """A float interface dial, returned as a SOCKET."""
    from surreal_arch.melodia_gn import core
    core.add_float_param(tree, name, default, lo, hi)
    gin = [n for n in tree.nodes if n.bl_idname == "NodeGroupInput"][0]
    for s in gin.outputs:
        if s.name == name:
            socket = s
            break
    else:
        raise KeyError("dial %r not on the group input" % name)
    dial_node = tree.nodes.new("GeometryNodeInputValue")
    dial_node.location = loc
    dial_node.label = label or name
    tree.links.new(socket, dial_node.outputs[0])
    return socket


def _group_node(tree, name, builder, loc, params=None):
    """Instantiate a house builder as a nested group, with LITERAL params."""
    if builder is None:
        print("REGALIA-WARN no builder for %s" % name)
        return None
    tree_ng = builder(name)
    if tree_ng is None:
        return None
    node = tree.nodes.new("GeometryNodeGroup")
    node.node_tree = tree_ng
    node.name = name
    node.label = name
    node.location = loc
    if params:
        for key, val in params.items():
            for s in node.inputs:
                if s.name == key and s.type == "VALUE":
                    s.default_value = val
    return node


def _material(tree, mat, loc, label, geometry=None):
    """Set Material, with a real material so the slot is never None.

    `geometry` MUST be linked. The first version took no input, so the node was
    created with an unconnected Geometry socket -- which Blender treats as
    empty, silently discarding everything upstream. The pair evaluated 0 verts
    while its Set Material reported no incoming link at all.
    """
    n = tree.nodes.new("GeometryNodeSetMaterial")
    n.location = loc
    n.label = label
    n.inputs["Material"].default_value = mat
    if geometry is not None:
        tree.links.new(geometry, n.inputs["Geometry"])
    return n


def _join(tree, loc, parts):
    """Join named multi-input sockets by LINKING into them.

    `Join Geometry`'s "Geometry" input is a multi-input GEOMETRY socket, so it
    has no `default_value` -- assigning one raises AttributeError. Each part
    needs its own link to the same socket. (This is the same named-socket rule
    as the circlet: Join Geometry takes a NAME, never a positional index.)
    """
    j = tree.nodes.new("GeometryNodeJoinGeometry")
    j.location = loc
    for n, part in enumerate(parts):
        if part is None:
            continue
        # A socket carries a read-only `.links` COLLECTION; the writable one is
        # `tree.links`, so a hasattr check on `.links` passes for a tuple too.
        # Check for the socket type instead, and always create links on the tree.
        if not hasattr(part, "is_output"):
            print("REGALIA-WARN _join part %d is a %s, not a socket: %r"
                  % (n, type(part).__name__, part))
            continue
        tree.links.new(part, j.inputs["Geometry"])
    return j


def _studs(tree, loc, ear, size):
    """A small gold ball at the lobe, then the crystal hanging from it."""
    mods = _mods()
    ball = tree.nodes.new("GeometryNodeMeshUVSphere")
    ball.location = loc
    ball.inputs["Radius"].default_value = size
    ball.inputs["Segments"].default_value = 16
    ball.inputs["Rings"].default_value = 10
    # NO "Location" input on GeometryNodeMeshUVSphere in Blender 5.2 -- it is
    # emitted at the origin. KeyError proved it. Seat it with a Transform.
    mv = tree.nodes.new("GeometryNodeTransform")
    mv.location = (loc[0] + 200, loc[1])
    mv.inputs["Translation"].default_value = (ear[0], ear[1], ear[2] + size * 0.4)
    core.link_sockets(tree, ball.outputs["Mesh"], mv.inputs["Geometry"])
    return mv.outputs["Geometry"]


def build_regalia_earring_group(group_name="MEL_regalia_earring"):
    """ONE earring, built at her LEFT lobe in world space.

    A python bool, because `drop_len` is a dial SOCKET and is never None --
    `if drop_len is not None` is always true, whatever the authored value.
    """
    from surreal_arch.melodia_gn import core
    mods = _mods()
    tree, gin, gout = core.new_geometry_tree(group_name)

    drop_len = _dial(tree, "Drop Length", 0.034, 0.012, 0.09, (-1500, -300))
    drop_wid = _dial(tree, "Drop Width", 0.013, 0.004, 0.05, (-1500, -450))
    facet_n = _dial(tree, "Facet Count", 6, 3, 12, (-1500, -600))
    stud_r = _dial(tree, "Stud Radius", 0.0055, 0.001, 0.02, (-1500, -750))
    fringe_on = _dial(tree, "Fringe Length", 0.026, 0.0, 0.09, (-1500, -900))
    side = _dial(tree, "Side", 1.0, -1.0, 1.0, (-1500, -1050), "1 = L, -1 = R")

    # A python bool, not `side is not None`: a dial socket is never None.
    have_fringe = bool(FRINGE)

    ear = EAR_L  # the LEFT lobe; the pair builder mirrors this for the right

    # gold stud at the lobe
    stud = tree.nodes.new("GeometryNodeMeshUVSphere")
    stud.location = (-1150, -300)
    stud.inputs["Radius"].default_value = 0.0055
    stud.inputs["Segments"].default_value = 18
    stud.inputs["Rings"].default_value = 12
    core.link_sockets(tree, stud_r, stud.inputs["Radius"])
    # NO "Location" input on GeometryNodeMeshUVSphere in Blender 5.2; it emits
    # at the origin. Seat it with a Transform.
    seat = tree.nodes.new("GeometryNodeTransform")
    seat.location = (-1000, -300)
    seat.label = "seat stud on the lobe"
    seat.inputs["Translation"].default_value = ear
    core.link_sockets(tree, stud.outputs["Mesh"], seat.inputs["Geometry"])

    # the faceted drop, hanging DOWN (-Z) from just under the stud
    drop_builder = getattr(mods.get("cute_decor"), "build_crystal_drop", None)
    drop = _group_node(
        tree, "MEL_crystal_drop", drop_builder, (-1150, -620),
        # LITERALS. The house defaults are large (0.12 long, 0.04 wide) and a
        # linked socket did not override them in the crown pass.
        params={"Crystal Length": DROP_LEN,
                "Crystal Width": DROP_WID * 0.5,
                "Facet Count": 6,
                "Top Radius": 0.004})
    parts = [seat.outputs["Geometry"]]
    if drop is not None:
        mv = tree.nodes.new("GeometryNodeTransform")
        mv.location = (-850, -620)
        mv.label = "seat drop under the lobe"
        mv.inputs["Translation"].default_value = (
            ear[0], ear[1], ear[2] - STUD - DROP_LEN * 0.5)
        core.link_sockets(tree, drop.outputs["Geometry"], mv.inputs["Geometry"])
        parts.append(mv.outputs["Geometry"])

    # the fringed second layer, hanging below the crystal
    if have_fringe:
        drop2 = _group_node(
            tree, "MEL_crystal_drop2", drop_builder, (-1150, -980),
            params={"Crystal Length": DROP_LEN * 0.62,
                    "Crystal Width": DROP_WID * 0.34,
                    "Facet Count": 6,
                    "Top Radius": 0.003})
        if drop2 is not None:
            mv2 = tree.nodes.new("GeometryNodeTransform")
            mv2.location = (-850, -980)
            mv2.label = "seat second drop"
            mv2.inputs["Translation"].default_value = (
                ear[0], ear[1], ear[2] - STUD - DROP_LEN - DROP_LEN * 0.31)
            core.link_sockets(tree, drop2.outputs["Geometry"],
                              mv2.inputs["Geometry"])
            parts.append(mv2.outputs["Geometry"])

    joined = _join(tree, (-500, -520), parts)

    # gold on the metal, surreal stone reserved for a gem layer added later
    mods_mat = mods.get("materials_kit")
    gold = None
    if mods_mat is not None and hasattr(mods_mat, "build_gold_material"):
        try:
            gold = mods_mat.build_gold_material()
        except Exception as exc:
            print("REGALIA-WARN gold material: %s" % exc)
    sm = _material(tree, gold, (-260, -520), "gold",
                   geometry=joined.outputs["Geometry"])

    gout = [n for n in tree.nodes if n.bl_idname == "NodeGroupOutput"][0]
    tree.links.new(sm.outputs["Geometry"], gout.inputs["Geometry"])

    return tree


def build_regalia_earring_pair():
    """BOTH earrings: this group plus its mirror, joined at world scale.

    The lobes are NOT symmetric -- c_ear_01.l is 4 mm outboard of a mirrored
    c_ear_01.r -- so the pair is two independently placed instances, not one
    mirrored copy. A mirror would put the left stone on the wrong ear.
    """
    from surreal_arch.melodia_gn import core
    mods = _mods()
    tree, gin, gout = core.new_geometry_tree("MEL_regalia_earrings")

    mats = _mods().get("materials_kit")
    gold = None
    if mats is not None and hasattr(mats, "build_gold_material"):
        try:
            gold = mats.build_gold_material()
        except Exception as exc:
            print("REGALIA-WARN gold material: %s" % exc)

    parts = []
    for tag, ear in (("l", EAR_L), ("r", EAR_R)):
        one = getattr(mods.get("cute_decor"), "build_crystal_drop", None)
        if one is None:
            continue
        stud = tree.nodes.new("GeometryNodeMeshUVSphere")
        stud.location = (-1200 if tag == "l" else -900, -300)
        stud.inputs["Radius"].default_value = 0.0055
        stud.inputs["Segments"].default_value = 18
        stud.inputs["Rings"].default_value = 12
        seat = tree.nodes.new("GeometryNodeTransform")
        seat.location = (-1050 if tag == "l" else -760, -300)
        seat.inputs["Translation"].default_value = ear
        core.link_sockets(tree, stud.outputs["Mesh"], seat.inputs["Geometry"])
        parts.append(seat.outputs["Geometry"])

        drop = _group_node(
            tree, "MEL_crystal_drop_%s" % tag, one,
            (-1200 if tag == "l" else -900, -640),
            params={"Crystal Length": DROP_LEN,
                    "Crystal Width": DROP_WID * 0.5,
                    "Facet Count": 6,
                    "Top Radius": 0.004})
        if drop is None:
            continue
        mv = tree.nodes.new("GeometryNodeTransform")
        mv.location = (-1000 if tag == "l" else -700, -640)
        mv.inputs["Translation"].default_value = (
            ear[0], ear[1], ear[2] - STUD - DROP_LEN * 0.5)
        core.link_sockets(tree, drop.outputs["Geometry"], mv.inputs["Geometry"])
        parts.append(mv.outputs["Geometry"])

        # second layer: a smaller crystal below the first, in place of the
        # time-driven tassel (see the module docstring).
        drop2 = _group_node(
            tree, "MEL_crystal_drop2_%s" % tag, one,
            (-1200 if tag == "l" else -900, -1000),
            params={"Crystal Length": DROP_LEN * 0.62,
                    "Crystal Width": DROP_WID * 0.34,
                    "Facet Count": 6,
                    "Top Radius": 0.003})
        if drop2 is not None:
            mv2 = tree.nodes.new("GeometryNodeTransform")
            mv2.location = (-1000 if tag == "l" else -700, -1000)
            mv2.label = "seat second drop"
            mv2.inputs["Translation"].default_value = (
                ear[0], ear[1], ear[2] - STUD - DROP_LEN - DROP_LEN * 0.31)
            core.link_sockets(tree, drop2.outputs["Geometry"],
                              mv2.inputs["Geometry"])
            parts.append(mv2.outputs["Geometry"])

    if not parts:
        print("REGALIA-WARN no earring parts built")
        return tree

    joined = _join(tree, (-450, -600), parts)
    sm = _material(tree, gold, (-220, -600), "gold",
                   geometry=joined.outputs["Geometry"])
    gout = [n for n in tree.nodes if n.bl_idname == "NodeGroupOutput"][0]
    tree.links.new(sm.outputs["Geometry"], gout.inputs["Geometry"])
    return tree
