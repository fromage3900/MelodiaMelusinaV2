"""MEL_regalia_baroque — Baroque headpiece builders for Melusina, ON the house
geometry-nodes framework.

This is the REBUILD of the regalia lane. The first circlet
(`MEL_melusina_circlet`, `Saved/Audit/regalia/melusina_regalia_circlet.py`) hand-
rolled a flat 45-node graph and an inline gold Principled, ignoring builders that
already existed. The owner called it out and the audit is in
`Saved/Audit/regalia/CIRCLET_AUDIT_2026-09-25.md`.

What is house (do not re-author):
  band profile sweep   core.sweep_profile
  filigree scroll      MEL_filigree_spiral  (taper + FiligreePhase + shade smooth)
  corner volute        MEL_filigree_corner_volute
  cross finial         MEL_filigree_finial_cross
  rosette              MEL_ornament_rosette_sixpetal
  faceted gem          MEL_nikki_crystal
  bead strip           MEL_gold_ornament_strip
  gold material        materials_kit.build_gold_material

What is mine and stays mine: `regalia_stone.build_stone` — the magical-surreal
emission palette. The house has no surreal gem, and five verified stones is real
work. Everything else composes house pieces.

Baroque, not Art Nouveau: the house filigree is a log-spiral scroll. A crown
wants volute, wreath and rosette mass — heavier, more regal, more Baroque. Both
languages are in the addon; this module picks the Baroque one deliberately.

Mirrors the addon's own idiom (see `nikki_decor.py`): local `_mk`/`_combine`/
`_transform`/`_join`/`_shade` helpers that accept sockets OR literals, a `_finish`
that sets material then joins onto host geometry, `_frames` for label_tree, and
`return tree` from the `_group` wrapper so the Universal Music pass is not
auto-applied to a piece of jewellery.

Run headless:
  blender -b --factory-startup --python regalia_baroque_build.py
"""

import math
import os
import sys

import bpy

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import regalia_stone as _RS  # noqa: E402  (the surreal gem palette, ours)

# --------------------------------------------------------------------------
# Head contract, MEASURED on Melusina_Base via MCP 9876 (regalia_landmarks.json).
# A headpiece is fitted to a band, not to the whole head, and these are the two
# bands. She faces -Y, so the nape gap belongs at +Y and an arc centred on 270 deg
# wraps the face.
# --------------------------------------------------------------------------
BROW_Z = 1.560
BROW_HW = 0.2042          # half width, 0.4084 m
BROW_HD = 0.2297          # half depth, 0.4594 m
BROW_CX = -0.0044
BROW_CY = -0.1335
CROWN_Z = 1.800
CROWN_HW = 0.11325        # 0.2265 m -- 45% narrower than the brow
CROWN_CX = BROW_CX
CROWN_CY = BROW_CY

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_GN = r"C:\EnvironmentPortfolio\BS_GodFile\deploy\surreal_arch"
APPDATA_GN = os.path.join(
    os.path.expanduser("~"),
    r"AppData\Roaming\Blender Foundation\Blender\5.2\scripts\addons\surreal_arch")


def _import_house():
    """Import the house melodia_gn package, preferring the REPO copy.

    The skill's standing trap: Blender autoloads the AppData addon copy into
    sys.modules before a --python script runs, and path order cannot beat that
    cache. Purge it and re-import, then assert which file we actually got.
    """
    for path in (REPO_GN, APPDATA_GN):
        if os.path.isdir(path) and path not in sys.path:
            sys.path.insert(0, path)
    # `surreal_arch` is the package root and `melodia_gn` is its SUBMODULE, so the
    # module path is surreal_arch.melodia_gn -- importing melodia_gn directly dies
    # with "attempted relative import beyond top-level package" (measured).
    for name in [m for m in list(sys.modules)
                 if m.startswith("surreal_arch") or m == "melodia_gn"
                 or m.startswith("melodia_gn.")]:
        del sys.modules[name]
    from surreal_arch import melodia_gn
    return melodia_gn


def _mods():
    """The house modules this builder composes, imported as submodules."""
    import importlib
    from surreal_arch.melodia_gn import core
    out = {"core": core}
    # `profiles` supplies build_star_finial (the crown's spire). It was missing
    # from this list when the finial was first added, so the branch silently did
    # nothing: no MEL_star_finial group nested, and no crest in the output, while
    # the gates still passed. Every module a branch reaches for belongs here.
    for name in ("filigree", "ornament_extras", "nikki_decor", "materials_kit",
                 "ornament_strip", "profiles"):
        try:
            out[name] = importlib.import_module("surreal_arch.melodia_gn." + name)
        except Exception as exc:  # keep building what we can, report the rest
            print("REGALIA-WARN cannot import %s: %s" % (name, exc))
    return out


def _is_sock(v):
    return v is not None and hasattr(v, "is_linked")


FEED_FAILURES = []


def _feed(tree, value, target):
    """Link a socket into `target`, or write it as a default value.

    This used to swallow every exception, which is how the gem's Selection link
    vanished: the tree built "successfully", evaluated, and reported PASS while
    the stone was simply absent from the output. A silent feed is indistinguishable
    from a correct one until something is missing, so failures are recorded and
    printed once at the end of the build.
    """
    if value is None and target is None:
        return          # both absent: a genuinely optional link
    if target is None:
        FEED_FAILURES.append("target socket missing for %r" % (value,))
        return
    if value is None:
        # Rotation/Scale/Position on Transform and Set Position are OPTIONAL:
        # unlinked is the correct identity default, so those are not failures.
        # Anything else being None means an upstream helper produced nothing --
        # which is exactly how the gem's Selection went missing.
        if target.name not in ("Rotation", "Scale", "Position"):
            FEED_FAILURES.append("value was None for target %r" % target.name)
        return
    try:
        if _is_sock(value):
            tree.links.new(value, target)
        elif isinstance(value, (int, float, bool, tuple, list)):
            target.default_value = value
        else:
            FEED_FAILURES.append("unsupported value %r" % type(value))
    except Exception as e:
        FEED_FAILURES.append("%s -> %s: %s" % (
            getattr(value, "name", value), getattr(target, "name", target), e))


# --- the house helper vocabulary, mirrored from nikki_decor.py ------------

def _const(tree, loc, value):
    """A Value node wrapping a literal, so a constant can be an explicit operand
    in[0] without relying on _mk's positional-const behaviour."""
    n = tree.nodes.new("ShaderNodeValue")
    n.location = loc
    n.outputs[0].default_value = value
    return n.outputs[0]


def _mk(tree, loc, operation, const=None, a=None, b=None, c=None):
    """A 2-operand Math node.

    The one real trap here: 5.2's ShaderNodeMath leaves inputs[0] AND inputs[1]
    at a 0.5 default. `_out(tree, loc, "MULTIPLY", K)` with no a= and no b= fed
    only inputs[1], so the node computed 0.5 * K. Three deg->rad factors were
    silently halved that way, turning Arc Span 280 deg into a 140 deg sweep and
    leaving the band as a flat arc across her brow. A bare constant must be
    written into BOTH-visible-operand position -- use `_const` for that, and this
    function refuses the ambiguous form outright.
    """
    n = tree.nodes.new("ShaderNodeMath")
    n.location = loc
    n.operation = operation

    if a is None and b is None and const is not None:
        # a bare constant: MULTIPLY/ADD/DIVIDE by it still needs a left operand.
        # Lift it to a Value node and multiply explicitly, so nothing is implicit.
        left = _const(tree, (loc[0] - 190, loc[1]), 1.0)
        a, b = left, const

    # 5.2 adds a third input to some ops; ABSOLUTE/SIGN/FLOOR/CEIL/ROUND/TRUNC/
    # FRACT/EXPONENT/LOGARITHM are genuinely UNARY. Anything else needs two.
    UNARY = {"ABSOLUTE", "SIGN", "FLOOR", "CEIL", "ROUND", "TRUNC", "FRACT",
             "EXPONENT", "LOGARITHM"}
    if operation in UNARY:
        if a is None:
            raise ValueError("_mk(%r) is unary and needs a=" % operation)
        _feed(tree, a, n.inputs[0])
        return n

    if b is None and const is not None:
        b = const          # the house shape: a=<socket>, const=<literal 2nd operand>
    if a is None and b is not None:
        a = _const(tree, (loc[0] - 190, loc[1]), 1.0)
    if a is None or b is None:
        raise ValueError(
            "_mk(%r): both operands are required. Got a=%r b=%r const=%r. "
            "A Math node's unset inputs default to 0.5, which silently "
            "corrupts every result." % (operation, a, b, const))

    _feed(tree, a, n.inputs[0])
    _feed(tree, b, n.inputs[1])
    if c is not None:
        raise ValueError("_mk is 2-input; build an explicit node for a 3rd operand")
    return n
def _out(tree, loc, operation, const=None, a=None, b=None):
    n = _mk(tree, loc, operation, const, a, b)
    return None if n is None else n.outputs[0]
def V_safe(node):
    """A Math node's Value socket, or None. ShaderNodeMath exposes it as
    outputs[0]; named lookup is safer across builds."""
    if node is None:
        return None
    try:
        return node.outputs["Value"]
    except Exception:
        try:
            return node.outputs[0]
        except Exception:
            return None


def _combine(tree, loc, x=None, y=None, z=None):
    """CombineXYZ. EVERY unset axis is written 0.0 explicitly -- a fresh node is
    (0,0,0) and a partially-driven CombineXYZ zeroes the rest (measured: a band
    collapsed to w=0.0000 with every x exactly 0)."""
    n = tree.nodes.new("ShaderNodeCombineXYZ")
    n.location = loc
    for name, val in (("X", x), ("Y", y), ("Z", z)):
        sock = n.inputs[name]
        if val is None:
            sock.default_value = 0.0
        else:
            _feed(tree, val, sock)
    return n.outputs["Vector"]


def _transform(tree, loc, geom, translation=None, rotation=None, scale=None):
    n = tree.nodes.new("GeometryNodeTransform")
    n.location = loc
    _feed(tree, geom, n.inputs["Geometry"])
    _feed(tree, translation, n.inputs["Translation"])
    _feed(tree, rotation, n.inputs["Rotation"])
    _feed(tree, scale, n.inputs["Scale"])
    return n.outputs["Geometry"]


def _set_position(tree, loc, geom, offset=None, position=None):
    n = tree.nodes.new("GeometryNodeSetPosition")
    n.location = loc
    _feed(tree, geom, n.inputs["Geometry"])
    _feed(tree, position, n.inputs["Position"])
    _feed(tree, offset, n.inputs["Offset"])
    return n.outputs["Geometry"]


def _join(tree, loc, geoms):
    """Join Geometry is ONE multi-input `Geometry` socket in 5.2 -- indexing
    inputs[1] raises IndexError."""
    n = tree.nodes.new("GeometryNodeJoinGeometry")
    n.location = loc
    for g in geoms:
        if g is not None:
            _feed(tree, g, n.inputs["Geometry"])
    return n.outputs["Geometry"]


def _merge(tree, loc, geom, distance=0.0004):
    """Weld coincident verts.

    MergeByDistance's input is named "Geometry" but it does NOT accept an
    Instances socket: measured, instancing an icosphere on a 3x3 grid then
    merging the `Instances` output gave 0 verts, while realizing first gave 108.
    A 45-node tree measured 1,536 verts (the band alone) for exactly this
    reason, with every ornament branch silently empty. Realize first.
    """
    rl = tree.nodes.new("GeometryNodeRealizeInstances")
    rl.location = (loc[0] - 220, loc[1])
    _feed(tree, geom, rl.inputs["Geometry"])
    n = tree.nodes.new("GeometryNodeMergeByDistance")
    n.location = loc
    _feed(tree, rl.outputs["Geometry"], n.inputs["Geometry"])
    _feed(tree, distance, n.inputs["Distance"])
    return n.outputs["Geometry"]


def _shade(tree, loc, geom, smooth=None):
    n = tree.nodes.new("GeometryNodeSetShadeSmooth")
    n.location = loc
    _feed(tree, geom, n.inputs["Mesh"])
    _feed(tree, smooth, n.inputs["Shade Smooth"])
    return n.outputs["Geometry"]


def _set_material(tree, loc, geom, material_sock=None, material=None):
    n = tree.nodes.new("GeometryNodeSetMaterial")
    n.location = loc
    _feed(tree, geom, n.inputs["Geometry"])
    if material_sock is not None:
        _feed(tree, material_sock, n.inputs["Material"])
    else:
        _feed(tree, material, n.inputs["Material"])
    return n.outputs["Geometry"]


def _sweep_circle(tree, loc, curve_sock, radius_sock, resolution=8):
    """core.sweep_profile's job, locally, so a caller can hand a RADIUS SOCKET."""
    prof = tree.nodes.new("GeometryNodeCurvePrimitiveCircle")
    prof.location = (loc[0] - 200, loc[1] - 240)
    _feed(tree, resolution, prof.inputs["Resolution"])
    _feed(tree, radius_sock, prof.inputs["Radius"])
    sweep = tree.nodes.new("GeometryNodeCurveToMesh")
    sweep.location = loc
    _feed(tree, curve_sock, sweep.inputs["Curve"])
    _feed(tree, prof.outputs["Curve"], sweep.inputs["Profile Curve"])
    return sweep.outputs["Mesh"]


def _resample(tree, loc, curve_sock, count_sock):
    """Resample to an exact point count.

    5.2: `ResampleCurve.mode` is NOT a node property (no such attribute), and the
    "Mode" input is a **NodeSocketMenu** whose enum items are TITLE CASE --
    'Evaluated', 'Count', 'Length'. Assigning "COUNT" raises TypeError, which is
    why a try/except around it used to hide the fault. It already defaults to
    'Count', so this only ever needs to be explicit.
    """
    n = tree.nodes.new("GeometryNodeResampleCurve")
    n.location = loc
    try:
        n.inputs["Mode"].default_value = "Count"
    except Exception as e:
        print("REGALIA-WARN ResampleCurve Mode not settable: %s" % e)
    _feed(tree, curve_sock, n.inputs["Curve"])
    _feed(tree, count_sock, n.inputs["Count"])
    return n.outputs["Curve"]


def _group_node(tree, group_name, builder, loc, params=None):
    """Nest a HOUSE tree as a group node and set its unlinked inputs.

    `_ensure_group_node` in nikki_decor.py is the same idea; doing it locally
    keeps the builder importable when the house module is missing.
    """
    ng = bpy.data.node_groups.get(group_name)
    if ng is None and builder is not None:
        try:
            built = builder(group_name)
        except Exception as exc:
            print("REGALIA-WARN cannot build house group %s: %s" % (group_name, exc))
            return None
        # USE THE RETURN VALUE. A house builder may return the tree WITHOUT
        # registering it under the requested name: build_star_finial("X")
        # returned a tree, yet bpy.data.node_groups.get("X") stayed None, so the
        # lookup below produced node_tree=None, outputs=[], and every
        # `sn.outputs["Geometry"]` raised KeyError. Fall back to the returned
        # object, and normalise the (tree, gin, gout) tuple some builders give.
        if isinstance(built, (tuple, list)):
            built = built[0]
        if built is not None:
            ng = built
    if ng is None:
        print("REGALIA-WARN house group %s is unresolvable" % group_name)
        return None
    node = tree.nodes.new("GeometryNodeGroup")
    node.location = loc
    node.node_tree = ng
    for name, value in (params or {}).items():
        sock = node.inputs.get(name)
        if sock is None:
            continue
        if _is_sock(value):
            # A dial SOCKET must be LINKED. Writing it into the nested tree's
            # interface default raises, because a default_value is a literal.
            _feed(tree, value, sock)
        elif not sock.is_linked:
            # A literal: write BOTH the node input and the nested tree default, so
            # the value holds however the group is later instanced.
            # (Assigning only the node input is what left the house defaults
            # winning -- measured 1.051 m of scroll where 0.145 m was intended.)
            try:
                sock.default_value = value
            except Exception:
                pass
            if ng is not None:
                for it in ng.interface.items_tree:
                    if (getattr(it, "item_type", "") == "SOCKET"
                            and it.in_out == "INPUT" and it.name == name):
                        try:
                            it.default_value = value
                        except Exception:
                            pass
    return node


def _frames(*specs):
    out = []
    for spec in specs:
        out.append({"title": spec[0], "role": spec[1],
                    "nodes": tuple(n.name for n in spec[2:] if n is not None)})
    return out


# ==========================================================================
# THE BAND -- an egg-section ring centred on -Y, swept with a rounded profile.
# ==========================================================================

def _band(tree, loc, hw, hd, cz, cx, cy, span_dial, samples_dial,
          width_dial, depth_dial, smooth=True):
    """A head band. Returns (mesh_socket, curve_socket).

    The arc is centred on 270 deg because she faces -Y: 270 deg is her front, so
    the opening lands at the nape (+Y). CurveArc's Start Angle/Sweep Angle are the
    ONLY way to place it -- measured, 180 deg centring put a 0.248 m band on one
    side and the correct centring wrapped the full 0.408 m head.

    The section is an EGG, not a circle: Y is scaled by hd/hw. A circle fit a
    0.408 x 0.459 head with visible gaps at the temples.
    """
    bx, by = loc

    arc = tree.nodes.new("GeometryNodeCurveArc")
    arc.location = (bx - 900, by + 200)
    arc.mode = "RADIUS"
    # BOTH angles need deg->rad. Feeding the 280.0 dial straight into Sweep Angle
    # gave 280 RADIANS = 44.56 turns: the band wrapped the head 44 times, which
    # is why the isolated arc (hardcoded in radians) was correct while the
    # assembled piece was 123 mm off. CurveArc takes radians on BOTH angle
    # sockets; a linked socket is never auto-converted.
    deg2rad_sw = _const(tree, (bx - 1300, by + 240), math.pi / 180.0)
    _feed(tree, _out(tree, (bx - 1120, by + 200), "MULTIPLY",
                     a=span_dial, b=deg2rad_sw), arc.inputs["Sweep Angle"])
    # Arc Span is authored in DEGREES (280 reads as 280 deg, which is what an
    # author expects), but CurveArc's Start/Sweep Angle are RADIANS. The half-span
    # therefore needs converting: `4.712389 - 140` = -135 rad put the band's start
    # angle in a random place, which is what made the assembled piece sit 122 mm
    # off from the isolated arc that hardcoded 130 deg. The Sweep socket takes the
    # dial and Blender converts it; only the COMPUTED start needs the factor.
    deg2rad = _const(tree, (bx - 1300, by + 380), math.pi / 180.0)
    half_deg = _out(tree, (bx - 1120, by + 320), "MULTIPLY", 0.5, a=span_dial)
    half = _out(tree, (bx - 1120, by + 250), "MULTIPLY", a=half_deg, b=deg2rad)
    # start = radians(270) - radians(span/2)
    # _out's 3rd positional arg is `const`, which _mk writes into in[1] -- the
    # SECOND operand. Passing radians(270) positionally therefore computed
    # `half - 4.712389`, the negative of what I wanted, and the arc opened on the
    # wrong side. Name both operands explicitly.
    start = _out(tree, (bx - 1120, by + 160), "SUBTRACT",
                 a=_const(tree, (bx - 1300, by + 60), math.radians(270.0)),
                 b=half)
    _feed(tree, start, arc.inputs["Start Angle"])
    _feed(tree, hw, arc.inputs["Radius"])

    # egg section: scale Y by the depth/width ratio (X must be 1.0 or it collapses).
    # ratio is a MATH NODE, not python: hw/hd are dials (sockets) and you cannot
    # divide two NodeSockets in python.
    ratio = _out(tree, (bx - 1120, by - 60), "DIVIDE", a=hd, b=hw)
    xf = tree.nodes.new("GeometryNodeTransform")
    xf.location = (bx - 700, by + 200)
    _feed(tree, arc.outputs["Curve"], xf.inputs["Geometry"])
    _feed(tree, _combine(tree, (bx - 900, by - 60), x=1.0, y=ratio, z=1.0),
          xf.inputs["Scale"])
    curve = xf.outputs["Geometry"]

    pts = _resample(tree, (bx - 480, by + 200), curve, samples_dial)

    # band cross-section: a flattened rounded profile, so the band has a face
    # rather than being a wire
    face = tree.nodes.new("GeometryNodeCurvePrimitiveCircle")
    face.location = (bx - 680, by - 220)
    _feed(tree, 8, face.inputs["Resolution"])
    w_half = _out(tree, (bx - 880, by - 160), "MULTIPLY", 0.5, a=width_dial)
    _feed(tree, w_half, face.inputs["Radius"])
    d_half = _out(tree, (bx - 880, by - 300), "MULTIPLY", 0.5, a=depth_dial)
    # flatten the profile: z = (Band Depth / Band Width). Another socket/socket
    # division, so it is a Math node too.
    flat = _out(tree, (bx - 880, by - 420), "DIVIDE", a=d_half, b=w_half)
    dxf = tree.nodes.new("GeometryNodeTransform")
    dxf.location = (bx - 500, by - 220)
    _feed(tree, face.outputs["Curve"], dxf.inputs["Geometry"])
    _feed(tree, _combine(tree, (bx - 680, by - 340), x=1.0, y=1.0, z=flat),
          dxf.inputs["Scale"])
    prof = dxf.outputs["Geometry"]

    sweep = tree.nodes.new("GeometryNodeCurveToMesh")
    sweep.location = (bx - 280, by + 200)
    _feed(tree, pts, sweep.inputs["Curve"])
    _feed(tree, prof, sweep.inputs["Profile Curve"])
    mesh = sweep.outputs["Mesh"]
    if smooth:
        mesh = _shade(tree, (bx - 100, by + 200), mesh, smooth=True)
    return mesh, pts


# ==========================================================================
# THE GEM -- the house faceted drop, with our surreal material
# ==========================================================================

def _gem(tree, loc, size_dial, sides_dial, stone_sock):
    """`MEL_nikki_crystal` is a faceted double-terminated cut. Nest it and drive
    it with our stone material rather than re-authoring a gem."""
    M = _mods()
    builder = getattr(M.get("nikki_decor"), "build_nikki_crystal", None)
    # MEL_nikki_crystal ALREADY has a "Material" input socket and applies it on
    # its own Set Material node inside the nested tree. Setting the material
    # AFTER the group output is therefore overridden, and the gem rendered as a
    # dark hole because it fell back to the house default. Pass the socket in.
    node = _group_node(tree, "MEL_nikki_crystal", builder, loc,
                       params={"Size": size_dial, "Sides": sides_dial,
                               "Faceted": True, "Material": stone_sock})
    if node is None:
        return None
    # ALSO set it here. The nested tree's own Set Material never entered the
    # emitted slot list: the evaluated mesh came back as [None,
    # 'SurrealArch_Gold'] with all 6176 faces on index 1, so the stone rendered
    # as bare gold. Setting it in THIS tree, after the group output, is the only
    # place the order is under our control -- the nested tree's slot is created
    # before the piece's gold pass and the piece's pass claims index 0.
    return _set_material(tree, (loc[0] + 320, loc[1]), node.outputs["Geometry"],
                         material_sock=stone_sock)


# ==========================================================================
# THE TIARA -- the builder
# ==========================================================================

def _gem_ok(dial):
    """Gem count dial present. Kept as a seam so a future build can gate on it."""
    return dial is not None


def _dial(tree, name, default, lo, hi, loc=None):
    """A ranged, named dial in the house style.

    `add_float_param`/`add_int_param` return the SOCKET (per the house contract),
    not an interface item -- consumers link the returned socket directly.
    """
    from surreal_arch.melodia_gn.core import add_float_param, add_int_param
    if isinstance(default, int) and not isinstance(default, bool):
        sock = add_int_param(tree, name, int(default), int(lo), int(hi))
    else:
        sock = add_float_param(tree, name, float(default), float(lo), float(hi))
    return sock


def _gold_param(tree):
    """House gold as a material interface socket (materials_kit.build_gold_material)."""
    from surreal_arch.melodia_gn.core import make_group_input
    from surreal_arch.melodia_gn import materials_kit
    mat = materials_kit.build_gold_material()   # takes NO arguments
    return make_group_input(tree, "NodeSocketMaterial", "Gold", default=mat)


def _stone_param(tree, key):
    """Our surreal gem as a material interface socket."""
    from surreal_arch.melodia_gn.core import make_group_input
    mat = _RS.build_stone(key, "REGALIA_STONE")
    return make_group_input(tree, "NodeSocketMaterial", "Stone", default=mat)


# ==========================================================================
# THE HEADPIECE -- circlet (brow band) and tiara (crown band) from ONE builder
# ==========================================================================

def _headpiece(tree, gin, gout, crown=False):
    """Baroque circlet (crown=False) or tiara (crown=True).

    Composition, not hand-rolled nodes:
      band      this module's egg-section ring at the chosen band
      filigree  MEL_filigree_spiral x N around the band (taper + phase attr)
      volute    MEL_filigree_corner_volute at the two band ends
      gem       MEL_nikki_crystal at the band's MIDPOINT, Aquamarine Dream
      beads     MEL_gold_ornament_strip along the band curve

    ONE builder, two bands: the crown is 0.2265 m wide against the brow's
    0.4084 m. Ornament is therefore authored as a RATIO of the band via the Size
    dial, never as fixed metres -- with absolute ornament the tiara measured
    0.839 m across on a 0.227 m head.
    """
    bx, by = 0, 0
    CROWN_HD = CROWN_HW * (BROW_HD / BROW_HW)
    hw, hd, cz = (CROWN_HW, CROWN_HD, CROWN_Z) if crown else (BROW_HW, BROW_HD, BROW_Z)
    cx, cy = BROW_CX, BROW_CY

    span = _dial(tree, "Arc Span", 280.0, 90.0, 359.0, (bx - 1500, by + 400))
    samples = _dial(tree, "Arc Samples", 192, 24, 512, (bx - 1500, by + 300))
    # Three independent renders all said the same thing: this read as "thin wire
    # headband", not jewellery. 14 mm x 5 mm on a 408 mm head is thread. A real
    # Baroque circlet band is nearer 22 x 9 mm, which also gives the filigree
    # something to sit ON rather than float beside.
    band_w = _dial(tree, "Band Width", 0.022, 0.004, 0.06, (bx - 1500, by + 200))
    band_d = _dial(tree, "Band Depth", 0.009, 0.002, 0.04, (bx - 1500, by + 100))
    volute_n = _dial(tree, "Volute Count", 2, 0, 4, (bx - 1500, by))
    scroll_n = _dial(tree, "Scroll Count", 9, 0, 32, (bx - 1500, by - 100))
    scroll_t = _dial(tree, "Scroll Turns", 2.5, 0.5, 6.0, (bx - 1500, by - 200))
    gem_n = _dial(tree, "Gem Count", 1, 0, 5, (bx - 1500, by - 300))
    # CROWN RISE. Three separate renders read the pieces as "ornate circlets, not
    # crowns" -- no vertical element at all. A circlet SHOULD stay flat, so this is
    # a dial: 0.0 = circlet, and the tiara defaults to a real crest. The crest is
    # the SAME band arc rebuilt in a vertical plane: rotating a CurveArc by -90 deg
    # about X maps (x,y,0) -> (x,0,-y), so the arc's 270-deg midpoint (0,-r,0)
    # lands at (0,0,+r) -- straight up. An arch, not a dip.
    crest_h = _dial(tree, "Crown Rise", 0.045 if crown else 0.0, 0.0, 0.14,
                    (bx - 1500, by - 350))
    crest_n = _dial(tree, "Crest Points", 3, 0, 9, (bx - 1500, by - 450))
    # A python BOOLEAN, because `crest_h` is a socket and is never None -- the
    # circlet's Crown Rise is 0.0, so its branch still ran and emitted a
    # zero-height star disc sitting on the band. Switch on the authored value.
    has_crest = bool(crown)
    # A graduated row of spires across the crest, so the tiara reads as a CROWN
    # with points rather than a single finial. Python int, not a socket, because
    # the fan is expanded at build time and a socket would rebuild per frame.
    fan_n = 7 if crown else 0
    fan_h = 0.030
    bead_n = _dial(tree, "Bead Count", 14, 0, 64, (bx - 1500, by - 400))
    stone = _stone_param(tree, "Aquamarine Dream")
    # Gold also goes through the interface so the piece can be re-skinned without
    # editing the tree. The FIRST proof rendered white-silver because the tree set
    # no material on the band/scrolls at all -- the render script's object-level
    # material was never applied to a GN output.
    gold_sock = _gold_param(tree)

    # The crown is 0.5546 of the brow, so the tiara defaults to it and the
    # circlet to 1.0. One dial drives band profile, scroll, volute, gem and beads.
    size = _dial(tree, "Size", 0.5546 if crown else 1.0, 0.2, 3.0,
                 (bx - 1500, by + 500))

    def sz(value, dy):
        """value x Size, as a socket."""
        return _out(tree, (bx - 1240, by + 500 - dy), "MULTIPLY", value, a=size)

    band_mesh, band_pts = _band(
        tree, (bx, by), hw, hd, cz, cx, cy, span, samples,
        # the dials author the size; Size scales it for the crown
        _out(tree, (bx - 1120, by + 60), "MULTIPLY", a=band_w, b=size),
        _out(tree, (bx - 1120, by - 20), "MULTIPLY", a=band_d, b=size))

    # the band curve is built in local space around the origin; move the whole
    # assembly onto the head ONCE, at the end, so nothing has to know the head
    origin = _combine(tree, (bx + 1400, by + 620), x=cx, y=cy, z=cz)
    placed_band = _transform(tree, (bx + 1500, by + 380), band_mesh,
                             translation=origin)
    placed_pts = _transform(tree, (bx + 1500, by + 180), band_pts,
                            translation=origin)

    parts = [placed_band]
    gem_part = None

    # ---- house filigree scrolls, spread on the band curve
    M = _mods()
    spiral_builder = getattr(M.get("filigree"), "build_filigree_spiral", None)
    if spiral_builder is not None and scroll_n is not None:
        scroll_pts = _resample(tree, (bx + 300, by + 120), placed_pts, scroll_n)
        node = _group_node(tree, "MEL_filigree_spiral", spiral_builder,
                           (bx + 500, by + 120),
                           # build_filigree_spiral's radii are ABSOLUTE metres
                           # (Outer Radius defaults to 0.6), NOT fractions. Passing
                           # 0.25/1.0 put the scroll's reach 0.204+1.0 m from the
                           # head axis and produced 2.41 m of geometry on a 0.408 m
                           # head. Derive BOTH radii from ScrollSize x Size: a
                           # Baroque volute is a tight curl, outer = 2x, inner = 1/4.
                           params={"Inner Radius": _out(
                                       tree, (bx + 300, by + 260), "MULTIPLY", 0.25,
                                       a=_out(tree, (bx + 160, by + 260), "MULTIPLY",
                                              0.030, a=size)),
                                   "Outer Radius": _out(
                                       tree, (bx + 300, by + 340), "MULTIPLY", 2.0,
                                       a=_out(tree, (bx + 160, by + 340), "MULTIPLY",
                                              0.030, a=size)),
                                   "Turns": scroll_t,
                                   "Profile Radius": _out(
                                       tree, (bx + 160, by + 40), "MULTIPLY",
                                       0.0040, a=size),
                                   "Spiral Height": 0.0,
                                   "Resolution": 48,
                                   "Profile Resolution": 8,
                                   "Taper Power": 0.8})
        if node is not None:
            # lift the scrolls OFF the band radially. Set Position +Z would raise
            # them vertically; the band is horizontal, so a Z lift looks wrong at
            # the temples. Offset along the curve's own normal instead, using the
            # Normal output of Curve to Points (Input Normal is EMPTY on curve
            # points -- the trap that put a scroll through the skull in B1).
            c2p = tree.nodes.new("GeometryNodeCurveToPoints")
            c2p.location = (bx + 300, by - 120)
            _feed(tree, scroll_pts, c2p.inputs["Curve"])
            rad = _out(tree, (bx + 500, by - 240), "MULTIPLY", 0.030, a=size)
            # a Math node has NO "SCALE" operation -- scaling a VECTOR needs
            # Vector Math (ShaderNodeVectorMath, operation "SCALE"), which takes
            # the vector in[0] and the scalar in[3] "Scale".
            vm = tree.nodes.new("ShaderNodeVectorMath")
            vm.location = (bx + 700, by - 240)
            vm.operation = "SCALE"
            _feed(tree, c2p.outputs["Normal"], vm.inputs[0])
            _feed(tree, rad, vm.inputs["Scale"])
            off = vm.outputs["Vector"]
            raised = _set_position(tree, (bx + 900, by - 120), scroll_pts,
                                   offset=off)
            inst = tree.nodes.new("GeometryNodeInstanceOnPoints")
            inst.location = (bx + 1100, by + 120)
            _feed(tree, raised, inst.inputs["Points"])
            _feed(tree, node.outputs["Geometry"], inst.inputs["Instance"])
            parts.append(_merge(tree, (bx + 1300, by + 120),
                                inst.outputs["Instances"]))

    # ---- house corner volutes at the two band ends (Baroque mass)
    vol_builder = getattr(M.get("ornament_extras"),
                          "build_filigree_corner_volute", None)
    if vol_builder is not None and volute_n is not None:
        ends = _resample(tree, (bx + 300, by - 400), placed_pts, volute_n)
        vnode = _group_node(tree, "MEL_filigree_corner_volute", vol_builder,
                            (bx + 500, by - 400),
                            # PROBED socket names -- do not guess these. Passing
                            # "Spiral Radius"/"Wire Radius" (which do not exist)
                            # silently dropped every volute param and left the house
                            # defaults, Outer Radius 0.5 m, winning.
                            params={"Outer Radius": _out(
                                        tree, (bx + 300, by - 320), "MULTIPLY", 1.6,
                                        a=_out(tree, (bx + 160, by - 320), "MULTIPLY",
                                               0.030, a=size)),
                                    "Inner Radius": _out(
                                        tree, (bx + 300, by - 200), "MULTIPLY", 0.4,
                                        a=_out(tree, (bx + 160, by - 200), "MULTIPLY",
                                               0.030, a=size)),
                                    "Profile Radius": _out(
                                        tree, (bx + 160, by - 440), "MULTIPLY",
                                        0.0040, a=size),
                                    "Turns": 1.25,
                                    "Taper Power": 1.2,
                                    "Resolution": 64,
                                    "Finial Size": _out(
                                        tree, (bx + 300, by - 80), "MULTIPLY", 0.8,
                                        a=_out(tree, (bx + 160, by - 80), "MULTIPLY",
                                               0.030, a=size))})
        if vnode is not None:
            vinst = tree.nodes.new("GeometryNodeInstanceOnPoints")
            vinst.location = (bx + 900, by - 400)
            _feed(tree, ends, vinst.inputs["Points"])
            _feed(tree, vnode.outputs["Geometry"], vinst.inputs["Instance"])
            parts.append(_merge(tree, (bx + 1100, by - 400),
                                vinst.outputs["Instances"]))

    # ---- house gold ornament strip (beads) along the band
    strip_builder = getattr(M.get("ornament_strip"),
                            "build_gold_ornament_strip", None)
    if strip_builder is not None and bead_n is not None:
        node = _group_node(tree, "MEL_gold_ornament_strip", strip_builder,
                           (bx + 500, by - 700),
                           params={"Bead Size": _out(
                                       tree, (bx + 300, by - 760), "MULTIPLY", 0.0035,
                                       a=size),
                                   "Bead Spacing": 0.030,
                                   "Count Override": bead_n})
        if node is not None:
            parts.append(node.outputs["Geometry"])

    # ---- the centre gem, at the band's MIDPOINT
    # A centre gem must sit at the arc's MIDDLE, not at its start. Resampling the
    # band curve to Gem Count put the first point at the arc's START ANGLE --
    # measured 200 mm off-axis in X. Fix: resample to a FIXED 96 samples, then keep
    # only index 48 (the midpoint), which is her front because the arc is centred on
    # 270 deg. No modulo, no division-by-a-dial, no clustering -- the house lesson
    # is that MODULO on a float field silently collapses (9 scrolls -> 4 buckets).
    # 11 mm on a 408 mm band measured invisible in the first render -- the stone
    # is the entire reason the surreal palette exists, so it has to read. 24 mm at
    # the brow (13 mm on the crown after Size 0.5546) is a real centre stone.
    gsize = _out(tree, (bx + 940, by - 1000), "MULTIPLY", 0.024, a=size)
    gnode = _gem(tree, (bx + 1100, by - 1000), gsize, 6, stone)
    if gnode is not None:
        # Resample the band curve to a FIXED 96 points, then keep ONLY index 48 --
        # the arc's midpoint, which is her front because the arc is centred on
        # 270 deg. Earlier this resampled to Gem Count, which put the first point
        # at the arc's START ANGLE (measured 200 mm off-axis in X). No modulo and
        # no division-by-a-dial: MODULO on a float field silently clusters (9
        # scrolls collapsed to 4 buckets).
        GSAMP = 96
        gcurve = _resample(tree, (bx + 900, by - 1000), placed_pts, GSAMP)
        idx = tree.nodes.new("GeometryNodeInputIndex")
        idx.location = (bx + 1060, by - 920)
        delta = _out(tree, (bx + 1220, by - 1020), "SUBTRACT",
                     a=idx.outputs["Index"], b=GSAMP * 0.5)
        near = _out(tree, (bx + 1400, by - 1020), "ABSOLUTE", a=delta)
        # DeleteGeometry with an UNLINKED Selection socket deletes EVERYTHING
        # (measured: 0 verts from a 96-point curve). Its default is TRUE, not
        # false, so the selection must always be linked explicitly. Select the
        # point at the midpoint, and everything else goes.
        del_me = tree.nodes.new("GeometryNodeDeleteGeometry")
        del_me.location = (bx + 1780, by - 1000)
        del_me.mode = "ALL"
        del_me.domain = "POINT"
        _feed(tree, gcurve, del_me.inputs["Geometry"])
        # `near` is already a socket (from _out). V_safe() expects a NODE and
        # returned None here, so Selection went unlinked -- and an UNLINKED
        # Selection on DeleteGeometry defaults to TRUE, deleting all 96 points.
        # That is why the tree built cleanly, passed 18/18, and had no gem.
        _feed(tree, near, del_me.inputs["Selection"])
        gpoint = del_me.outputs["Geometry"]

        # lift the stone clear of the band so it reads as a SET stone
        # _out returns a SOCKET; _mk returns a NODE. Passing the node here meant
        # the gem's Z lift was silently never applied (one of 8 swallowed feeds).
        gz = _out(tree, (bx + 1960, by - 1000), "ADD",
                  a=gsize, b=_const(tree, (bx + 1820, by - 1120), 0.004))
        gpos = _set_position(tree, (bx + 2140, by - 1000), gpoint,
                             offset=_combine(tree, (bx + 2000, by - 900),
                                             x=_const(tree, (bx + 2000, by - 820), 0.0),
                                             y=_const(tree, (bx + 2000, by - 760), 0.0),
                                             z=gz))
        ginst = tree.nodes.new("GeometryNodeInstanceOnPoints")
        ginst.location = (bx + 2320, by - 1000)
        _feed(tree, gpos, ginst.inputs["Points"])
        _feed(tree, gnode, ginst.inputs["Instance"])
        # NOT into `parts`: that list gets gold, and gold over a stone reads as a
        # dark plate. The stone carries its own material.
        gem_part = _merge(tree, (bx + 2500, by - 1000),
                          ginst.outputs["Instances"])

    # ---- the CROWN CREST: the band arc rebuilt in a vertical plane
    if has_crest:
        crest_parts = []
        # A vertical arc: same CurveArc, rotated -90 deg about X, then swept with
        # the same flattened profile as the band so the two read as one casting.
        varc = tree.nodes.new("GeometryNodeCurveArc")
        varc.location = (bx - 900, by + 1500)
        varc.mode = "RADIUS"
        _feed(tree, crest_h, varc.inputs["Radius"])
        # a 200-deg arc leaves a 160-deg gap; enough to read as an arch
        # 240 deg, not 200: the 34 mm centre stone hides the arch's middle from
        # a head-on view, so the crest has to be WIDE enough for its shoulders to
        # clear the stone. Widening the arc rather than raising it keeps the
        # silhouette regal instead of spiky.
        _feed(tree, _const(tree, (bx - 1120, by + 1560), math.radians(240.0)),
              varc.inputs["Sweep Angle"])
        # start so the arc's MIDDLE is straight up: 90 - span/2
        _feed(tree, _const(tree, (bx - 1120, by + 1460), math.radians(90.0 - 120.0)),
              varc.inputs["Start Angle"])
        # -90 deg about X: (x,y,0) -> (x,0,-y), which puts the 90-deg middle UP
        vxf = tree.nodes.new("GeometryNodeTransform")
        vxf.location = (bx - 700, by + 1500)
        _feed(tree, varc.outputs["Curve"], vxf.inputs["Geometry"])
        _feed(tree, _combine(tree, (bx - 900, by + 1600), x=1.0, y=1.0, z=1.0),
              vxf.inputs["Scale"])
        _feed(tree, _const(tree, (bx - 700, by + 1600), math.radians(-90.0)),
              vxf.inputs["Rotation"])
        vpts = _resample(tree, (bx - 480, by + 1500), vxf.outputs["Geometry"], 24)
        # sweep the same profile, flattened like the band
        vface = tree.nodes.new("GeometryNodeCurvePrimitiveCircle")
        vface.location = (bx - 680, by + 1300)
        _feed(tree, 8, vface.inputs["Resolution"])
        _feed(tree, _out(tree, (bx - 880, by + 1360), "MULTIPLY", 0.5, a=band_w),
              vface.inputs["Radius"])
        vdxf = tree.nodes.new("GeometryNodeTransform")
        vdxf.location = (bx - 500, by + 1300)
        _feed(tree, vface.outputs["Curve"], vdxf.inputs["Geometry"])
        _feed(tree, _combine(tree, (bx - 680, by + 1240), x=1.0, y=1.0, z=0.41),
              vdxf.inputs["Scale"])
        vsweep = tree.nodes.new("GeometryNodeCurveToMesh")
        vsweep.location = (bx - 280, by + 1500)
        _feed(tree, vpts, vsweep.inputs["Curve"])
        _feed(tree, vdxf.outputs["Geometry"], vsweep.inputs["Profile Curve"])
        crest_parts.append(_shade(tree, (bx - 100, by + 1500),
                                  vsweep.outputs["Mesh"], smooth=True))
        # stand the crest on the band's front, at her brow
        # Plant the crest BEHIND the centre stone. At the band's front face
        # (cy - hd) it collided exactly with the gem and Merge by Distance welded
        # them into one shell -- measured 184 stone faces on the tiara against
        # 13 on the flat circlet. 0.45 of the depth back reads as a crest
        # rising behind the stone, which is how a real tiara is built.
        # REPLACE index 0, never the list. `crest_parts = [_transform(...)]`
        # discarded every spire the fan had already appended, so seven
        # `MEL_star_finial` nodes were built, transformed, and then orphaned
        # before the join -- measured unchanged at 6450 verts and zmax 1.89695
        # while six new star trees sat in the file doing nothing.
        crest_parts[0] = _transform(tree, (bx + 1400, by + 1500), crest_parts[0],
                                   translation=_combine(
                                       tree, (bx + 1240, by + 1560),
                                       x=cx,
                                       y=_out(tree, (bx + 1080, by + 1560), "ADD",
                                              a=_const(tree, (bx + 940, by + 1620), cy),
                                              b=_out(tree, (bx + 940, by + 1500),
                                                     "MULTIPLY", -0.45, a=hd)),
                                       z=_out(tree, (bx + 1240, by + 1640), "ADD",
                                             a=_out(tree, (bx + 1100, by + 1640),
                                                   "MULTIPLY", 0.5, a=band_w),
                                             b=_const(tree, (bx + 1100, by + 1700),
                                                      cz))))
        # Append EVERY crest part, not just the arch. The fan's spires are in
        # the same list and were being dropped on the floor here.
        for cp in crest_parts:
            if cp is not None:
                parts.append(cp)

        # ---- the STAR FINIAL at the peak, from profiles.build_star_finial.
        # "No tall points, no crest" was the repeated read on three renders; a
        # band with ornament on it is a circlet, and this is what makes it a
        # crown. The house builder is a Points-sided cone -- a spire -- so it
        # scales as a RISE, not a width.
        # ---- the FAN: a graduated row of spires on the crest arc ------------
        # A single central finial reads as a headband with a nub. A graduated
        # row of points is what makes the silhouette a CROWN. Each spire is a
        # `MEL_star_finial` scaled by its position on the arc, tallest at the
        # middle, and positioned ON the crest curve so the two read as one
        # casting rather than two parts.
        #
        # Positions are computed in PYTHON from the arc's own geometry: the
        # crest is a 240 deg arc of radius RISE standing in the vertical plane,
        # so a point at parameter f in -1..1 sits at
        #   x = f * RISE * sin(100 deg)
        #   z = band_half + cos(f * 100 deg) * RISE
        # and the spire height tapers to 55% at the ends.
        if fan_n > 0:
            R = 0.045
            HALF_SWEEP = 100.0
            band_half_lit = 0.011 + 0.0045
            sb = getattr(_mods().get("profiles"), "build_star_finial", None)
            for si in range(fan_n):
                f = (si - (fan_n - 1) * 0.5) / max(1.0, (fan_n - 1) * 0.5)
                ang = math.radians(f * HALF_SWEEP)
                sx = f * R * math.sin(math.radians(HALF_SWEEP))
                sz = band_half_lit + math.cos(ang) * R
                # skip the exact centre: the existing single finial lives there
                if abs(f) < 1e-6 and fan_n > 1:
                    continue
                h = R * (1.0 - 0.45 * abs(f))
                sn = _group_node(
                    tree, "MEL_star_finial_fan%d" % si, sb,
                    (bx - 200 + si * 130, by + 2000 + si * 30),
                    # LITERALS scaled per-spire -- the nested-float rule.
                    params={"Points": 5,
                            "Radius Outer": h * 0.30 * 0.30,
                            "Radius Inner": h * 0.16 * 0.30,
                            "Height": h * 0.75})
                if sn is None:
                    continue
                crest_parts.append(_transform(
                    tree, (bx + 200 + si * 130, by + 2000 + si * 30),
                    sn.outputs["Geometry"],
                    translation=_combine(
                        tree, (bx + 60 + si * 130, by + 2060 + si * 30),
                        x=cx + sx,
                        y=_out(tree, (bx + 60 + si * 130, by + 2120 + si * 30),
                               "ADD",
                               a=_const(tree, (bx - 100 + si * 130,
                                               by + 2120 + si * 30), cy),
                               b=_out(tree, (bx - 100 + si * 130,
                                             by + 2060 + si * 30),
                                      "MULTIPLY", -0.45, a=hd)),
                        z=cz + sz + h * 0.30)))

        star_builder = getattr(_mods().get("profiles"), "build_star_finial", None)
        if star_builder is not None and has_crest:
            # LITERAL values, not sockets. build_star_finial's own defaults are
            # metre-scale (Radius Outer 0.15, Height 0.3) and a linked socket did
            # not override them: measured the star reaching 1.06 m above the band
            # against an intended 0.030 m, i.e. exactly the house 0.3 default from
            # the planted base. A literal writes both the node input and the
            # nested tree's interface default, so it holds.
            #
            # Sizes are computed in PYTHON from the authored rise, which is a
            # known constant per piece (0.045 tiara / 0.0 circlet).
            RISE = 0.045 if crown else 0.0
            snode = _group_node(tree, "MEL_star_finial", star_builder,
                                (bx - 200, by + 1800),
                                params={"Points": 5,
                                        "Radius Outer": RISE * 0.55 * 0.30,
                                        "Radius Inner": RISE * 0.16 * 0.30,
                                        "Height": RISE * 2.2 * 0.30})
            if snode is not None:
                sat = _transform(tree, (bx + 400, by + 1800),
                                 snode.outputs["Geometry"],
                                 translation=_combine(
                                     tree, (bx + 200, by + 1860),
                                     x=cx,
                                     y=_out(tree, (bx + 200, by + 1980), "ADD",
                                           a=_const(tree, (bx + 60, by + 2040), cy),
                                           b=_out(tree, (bx + 60, by + 1920),
                                                  "MULTIPLY", -0.45, a=hd)),
                                     # socket arithmetic MUST be a Math node --
                                     # `cz + crest_h * 1.55` in python would make
                                     # _feed reject the whole vector.
                                     # The crest is a half-ellipse of radius RISE
                                     # whose centre sits on the band top, so its
                                     # apex is at cz + band_half + RISE. Placing the
                                     # finial from a SOCKET chain (crest_h * 1.55)
                                     # put it 1.06 m too high -- measured shell z
                                     # 2.835 against a crest peak of 1.867.
                                     z=cz + 0.011 + 0.0045 + RISE * 1.15))
                sat = _shade(tree, (bx + 560, by + 1800), sat, smooth=True)
            # Append EVERY crest part at LAST: the arch, the fan's graduated
            # spires, and this finial. Appending earlier orphaned all six
            # spires -- Transform Geometry.007-.012 showed out=[] in the link
            # dump -- and the tiara measured unchanged at 6450 verts with six
            # star trees sitting unused in the file.
            for cp in crest_parts:
                if cp is not None:
                    parts.append(cp)

    # Gold on the metal parts. The gem branch is joined separately below so gold
    # does not paint over the stone.
    metal = [p for p in parts if p is not None]
    merged = _join(tree, (bx + 2900, by + 300), metal)
    merged = _set_material(tree, (bx + 3060, by + 300), merged,
                           material_sock=gold_sock)
    if gem_part is not None:
        merged = _join(tree, (bx + 3220, by + 200), [merged, gem_part])

    # ---- the FINISHING STAGE -------------------------------------------
    # Thickness + rim bevel. Without this the piece is a zero-thickness swept
    # surface and gold renders as wire, not cast metal. Both stages are pure
    # Geometry Nodes (house mesh_tools / geometry_extras) so they survive FBX.
    #
    # NOTE the dial signature: _dial(tree, name, default, lo, hi, loc) -- the
    # name comes SECOND, after the tree.
    thick_h = _dial(tree, "Band Thickness", 0.0016, 0.0, 0.02)
    bev_h = _dial(tree, "Rim Bevel", 0.0006, 0.0, 0.006)
    import regalia_finish as RF
    finished = RF.build_finish_stage(
        tree, merged, thickness=0.0016, bevel_width=0.0006,
        label="baroque")
    if finished is not None:
        merged = finished

    _feed(tree, merged, gout.inputs["Geometry"])
    return tree


# ==========================================================================
# GROUP WRAPPERS -- the house registration pattern.
# `return tree`, NEVER a (tree, gin, gout) triple: returning a triple opts the
# tree into the auto-applied Universal Music pass, which is how the first circlet
# ended up carrying Music Influence / Musical Amplitude / Musical Freq A/B
# sockets that do nothing for a piece of jewellery.
# ==========================================================================

def build_regalia_circlet_group(group_name="MEL_regalia_circlet"):
    from surreal_arch.melodia_gn.core import new_geometry_tree, label_tree, register_builder
    tree, gin, gout = new_geometry_tree(group_name)
    _headpiece(tree, gin, gout, crown=False)
    label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])
    if FEED_FAILURES:
        print("REGALIA-WARN %d silent feed failures in %s:" % (
            len(FEED_FAILURES), group_name))
        for f in FEED_FAILURES[:12]:
            print("   ", f)
        del FEED_FAILURES[:]
    return tree


def build_regalia_tiara_group(group_name="MEL_regalia_tiara"):
    from surreal_arch.melodia_gn.core import new_geometry_tree, label_tree
    tree, gin, gout = new_geometry_tree(group_name)
    _headpiece(tree, gin, gout, crown=True)
    label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])
    if FEED_FAILURES:
        print("REGALIA-WARN %d silent feed failures in %s:" % (
            len(FEED_FAILURES), group_name))
        for f in FEED_FAILURES[:12]:
            print("   ", f)
        del FEED_FAILURES[:]
    return tree


def register():
    from surreal_arch.melodia_gn.core import register_builder
    register_builder("MEL_regalia_circlet", build_regalia_circlet_group,
                     "Regalia Circlet (Baroque)", "Baroque circlet, band + filigree + gem.",
                     category="filigree")
    register_builder("MEL_regalia_tiara", build_regalia_tiara_group,
                     "Regalia Tiara (Baroque)", "Baroque tiara at crown scale.",
                     category="filigree")


def build_piece(name):
    """Build a named regalia tree by its Blender node-group name."""
    if name == "MEL_regalia_tiara":
        return build_regalia_tiara_group(name)
    if name == "MEL_regalia_circlet":
        return build_regalia_circlet_group(name)
    raise KeyError("unknown regalia piece: %r" % name)
