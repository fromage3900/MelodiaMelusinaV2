"""REGALIA CIRCLET — Melusina, Blender 5.2 GN. 2026-09-25.

Phase B, piece 1 of 9. A thin gold circlet that seats on the brow, using the
SAME proven patterns as the sheep floral crown (MEL_S5_flower_crown, 16/16):
instance-on-arc, Spline Parameter for per-point variation, and a measured seat.

Live head landmarks, measured from Melusina_Base via MCP (z -0.187..1.836):
    neck      z 1.368   width 0.142
    brow      z 1.56    width 0.408   <- widest point of the head
    crown     z 1.80    width 0.226
    she faces -Y
Band radius 0.204 = half the brow width; seated at the brow height.

Every socket name below was taken from a live 5.2 probe, not from memory:
  CurveArc        RADIUS mode, Sweep Angle (not "Sweep")
  CurveSpiral     Rotations / Start Radius / End Radius / Height
  RotateInstances Instances / Selection / Rotation / Pivot Point / Local Space
  JoinGeometry    ONE input named "Geometry" (multi-input, not Geometry + Geometry.001)
  IcoSphere       Radius / Subdivisions
  Transform       Translation / Rotation / Scale
"""

import bpy
import math
import sys
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
for _c in (r"C:\Users\froma\AppData\Roaming\Blender Foundation\Blender\5.2\scripts\addons",
           os.path.join(_HERE, "..", "surreal_arch")):
    if os.path.isdir(_c) and _c not in sys.path:
        sys.path.append(_c)

from surreal_arch.melodia_gn import core as C

TREE_NAME = "MEL_melusina_circlet"
BROW_Z = 1.560
BROW_W = 0.408
BROW_D = 0.459   # measured: brow depth, not half
# Measured head axis at the brow height (Melusina_Base, z 1.54-1.58 slice):
BROW_CX = -0.0044
BROW_CY = -0.1335


def gmat(tree):
    """A Material interface socket carrying the shared REGALIA_GOLD material.

    Created once per tree; reuses the datablock so every regalia piece resolves to
    the same gold without re-authoring node colours.
    """
    for it in tree.interface.items_tree:
        if getattr(it, "item_type", "") == "SOCKET" and it.name == "Gold":
            return tree.nodes["Group Input"].outputs["Gold"]
    mat = bpy.data.materials.get("REGALIA_GOLD") or bpy.data.materials.new("REGALIA_GOLD")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.83, 0.66, 0.30, 1.0)
        bsdf.inputs["Metallic"].default_value = 1.0
        bsdf.inputs["Roughness"].default_value = 0.25
    # There is no add_material_param() in core 5.2 -- create the interface socket
    # directly with the real NodeSocketMaterial TYPE. Passing a plain string raises
    # "expected a NodeSocket type" at link time.
    # no `parent=` kwarg on 5.2 -- it expects a NodeTreeInterfacePanel
    tree.interface.new_socket("Gold", in_out="INPUT",
                              socket_type="NodeSocketMaterial")
    for it in tree.interface.items_tree:
        if getattr(it, "item_type", "") == "SOCKET" and it.name == "Gold":
            try:
                it.default_value = mat
            except Exception:
                pass
    return tree.nodes["Group Input"].outputs["Gold"]


def gsock(tree):
    """Material interface socket for the centre stones.

    Delegates to regalia_stone.build_stone so the circlet and every later piece
    share ONE gem definition. The previous inline version hand-rolled a pale
    sapphire Principled and could not produce the magical-surreal palette.
    """
    import os as _os
    import sys as _sys
    here = _os.path.dirname(_os.path.abspath(__file__))
    if here not in _sys.path:
        _sys.path.append(here)
    import regalia_stone as _rs
    for it in tree.interface.items_tree:
        if getattr(it, "item_type", "") == "SOCKET" and it.name == "Stone":
            return tree.nodes["Group Input"].outputs["Stone"]
    mat = _rs.build_stone("Void Orchid", "REGALIA_STONE")
    tree.interface.new_socket("Stone", in_out="INPUT", socket_type="NodeSocketMaterial")
    for it in tree.interface.items_tree:
        if getattr(it, "item_type", "") == "SOCKET" and it.name == "Stone":
            try:
                it.default_value = mat
            except Exception:
                pass
    return tree.nodes["Group Input"].outputs["Stone"]


def _const(tree, value, loc):
    """A Value node carrying a measured constant."""
    n = C.require_node(tree, "ShaderNodeValue", loc)
    n.outputs[0].default_value = float(value)
    return n.outputs[0]


def _f(tree, name, d, lo, hi, desc=""):
    C.add_float_param(tree, name, d, lo, hi, desc)
    return name


def build():
    tree, gin, gout = C.new_geometry_tree(TREE_NAME)
    L = tree.links
    g = lambda n: gin.outputs[n]           # noqa: E731  interface VALUE by name

    def out_(node, *names):
        """Resolve an OUTPUT socket by name.

        C.sock() defaults to the INPUTS collection. Forgetting outputs=True
        makes it return None, and NodeLinks.new then raises a confusing
        "does not support a 'None' assignment" TypeError. Always go through here.
        """
        s = C.sock(node, *names, outputs=True)
        if s is None:
            raise KeyError("no output socket %s on %s (has: %s)"
                           % (names, node.bl_idname,
                              [o.name for o in node.outputs]))
        return s

    # ---------------------------------------------------------- dial contract
    _f(tree, "Band Radius", 0.204, 0.05, 0.40, "Half the brow width (0.408 / 2)")
    _f(tree, "Band Width", 0.014, 0.002, 0.08, "Vertical height of the band")
    _f(tree, "Band Depth", 0.006, 0.001, 0.03, "Radial thickness of the band")
    _f(tree, "Scroll Rise", 0.010, 0.0, 0.05, "How far scrolls stand off the band")
    _f(tree, "Clearance", 1.03, 1.0, 1.20, "Band standoff from the head surface")
    _f(tree, "Arc Span", 280.0, 60.0, 340.0, "Degrees of head wrap; gap sits at the nape")
    _f(tree, "Arc Samples", 96, 24, 256, "Curve samples around the band (INT)")
    _f(tree, "Filigree Density", 9, 0, 32, "Scroll motifs around the band")
    _f(tree, "Scroll Size", 0.030, 0.004, 0.09, "Radius of each filigree scroll")
    _f(tree, "Scroll Turns", 2.5, 0.5, 8.0, "Spiral turns per motif")
    _f(tree, "Scroll Wire", 0.0022, 0.0004, 0.010, "Thickness of each scroll wire")
    _f(tree, "Gem Count", 5, 0, 16, "Centre gems set into the band (INT)")
    _f(tree, "Gem Size", 0.010, 0.001, 0.04, "Gem radius")
    _f(tree, "Gem Rise", 0.008, 0.0, 0.05, "How far gems stand off the band")
    _f(tree, "Seed", 20260925, 0, 99999999, "Motif variation")

    # ---------------------------------------------------------- 1. the band arc
    # CurveArc is built in the XY plane. Rotate 90 deg about X so it spans X and
    # rises in Z, then lift to the brow.
    arc = C.require_node(tree, "GeometryNodeCurveArc", (-1240, 240))
    arc.mode = "RADIUS"
    # Clearance multiplies the measured half-width, so 1.0 = flush, 1.03 = 3% out
    radm = C.require_node(tree, "ShaderNodeMath", (-1340, 320))
    radm.operation = "MULTIPLY"
    L.new(g("Band Radius"), radm.inputs[0])
    L.new(g("Clearance"), radm.inputs[1])
    L.new(radm.outputs[0], arc.inputs["Radius"])
    sweep = C.require_node(tree, "ShaderNodeMath", (-1140, 140))
    sweep.operation = "MULTIPLY"
    sweep.inputs[1].default_value = math.pi / 180.0
    L.new(g("Arc Span"), sweep.inputs[0])
    L.new(sweep.outputs[0], arc.inputs["Sweep Angle"])
    # Resolution was left at its 16 default, which made the band visibly faceted AND
    # left only point index 0 passing the filigree modulo -> ONE scroll on the whole
    # band. Drive it from a dial.
    L.new(g("Arc Samples"), C.sock(arc, "Resolution"))
    # Arc angles are measured from +X growing CCW. She faces -Y = 270 deg, and the
    # gap belongs at the NAPE = +Y = 90 deg. So the band must be CENTRED ON 270:
    #     Start = 270 - sweep/2
    # Centring on 180 (or -90) puts the band across the back/side of the head and
    # the arc only reached x=+0.21 of a required -0.21..+0.21 -- measured w=0.248
    # against a 0.408 head. Centred on 270 the same 200 deg span gives the full
    # 0.408 width. Do not "fix" this to 180.
    half = C.require_node(tree, "ShaderNodeMath", (-1140, 20))
    half.operation = "DIVIDE"
    half.inputs[0].default_value = 2.0
    L.new(sweep.outputs[0], half.inputs[1])
    startm = C.require_node(tree, "ShaderNodeMath", (-960, 20))
    startm.operation = "SUBTRACT"
    startm.inputs[0].default_value = math.radians(270.0)   # facing direction
    L.new(half.outputs[0], startm.inputs[1])
    L.new(startm.outputs[0], arc.inputs["Start Angle"])

    # A CurveArc is ALREADY a horizontal ring in the XY plane. Rotating it 90 deg
    # about X stood the band on edge (measured z 1.35..1.77 instead of a 0.014
    # ribbon) -- so there is no rotation here at all, only a lift to the brow.
    # She faces -Y, so +Y is the nape: start the arc so the GAP lands there.
    # A circle of radius Band Radius is NOT a head. Measured at the brow the head
    # is 0.408 wide but 0.459 deep, so a circular band pushed 91% of its verts
    # through the skull (measured). Stretch the circle in Y to the head's real
    # depth/width ratio and the band wraps instead of intersecting.
    # Ratio of head half-depth to half-width; since both are halved the ratio is
    # simply depth/width. The arc radius is ALREADY a half-width, so scaling the
    # curve in Y by this ratio makes the band's Y reach the head's real depth.
    egg = C.require_node(tree, "ShaderNodeMath", (-840, 20))
    egg.operation = "DIVIDE"
    L.new(_const(tree, BROW_D, (-960, 20)), egg.inputs[0])
    L.new(_const(tree, BROW_W, (-960, -40)), egg.inputs[1])

    # CRITICAL: a fresh CombineXYZ is (0,0,0). Wiring it to Scale and driving only
    # Y means X=0 -> the band collapses to a plane. Measured w=0.0000. Every axis
    # that is not deliberately driven must be 1.0.
    eggs = C.require_node(tree, "ShaderNodeCombineXYZ", (-700, 20))
    eggs.inputs["X"].default_value = 1.0
    eggs.inputs["Y"].default_value = 1.0
    eggs.inputs["Z"].default_value = 1.0
    L.new(egg.outputs[0], eggs.inputs["Y"])
    eggx = C.require_node(tree, "GeometryNodeTransform", (-700, -120))
    L.new(eggs.outputs[0], eggx.inputs["Scale"])
    L.new(out_(arc, "Curve"), eggx.inputs["Geometry"])

    # Lift to the brow AND centre on the head's measured axis. Without the XY term
    # the band sits 134 mm forward of the skull (measured: circlet centre y=0.0004
    # vs head centre y=-0.1335), which puts the back of the band inside the neck.
    lift = C.require_node(tree, "GeometryNodeTransform", (-540, 240))
    lift.inputs["Translation"].default_value = (BROW_CX, BROW_CY, BROW_Z)
    L.new(eggx.outputs["Geometry"], lift.inputs["Geometry"])
    band_curve = lift.outputs["Geometry"]

    # ---------------------------------------------------------- 2. the ribbon
    # A profile circle swept along the arc, then squashed in Y so the tube reads
    # as a flat band rather than a wire.
    prof = C.require_node(tree, "GeometryNodeCurvePrimitiveCircle", (-840, -40))
    # RADIUS mode: only Resolution and Radius exist here. Point 1/2/3 are
    # POINTS-mode sockets and raise KeyError if touched in RADIUS mode.
    prof.mode = "RADIUS"
    prof.inputs["Resolution"].default_value = 12
    L.new(g("Band Depth"), prof.inputs["Radius"])

    # Flatten the PROFILE into an ellipse: scale its local Y by the width/depth
    # ratio. Curve to Mesh maps the profile's XY onto the curve's normal/binormal,
    # so this is what turns a round wire into a flat band.
    ratio = C.require_node(tree, "ShaderNodeMath", (-620, -120))
    ratio.operation = "DIVIDE"
    L.new(g("Band Width"), ratio.inputs[0])
    L.new(g("Band Depth"), ratio.inputs[1])
    psc = C.require_node(tree, "ShaderNodeCombineXYZ", (-460, -140))
    psc.inputs["X"].default_value = 1.0   # see the CombineXYZ(0,0,0) note above
    psc.inputs["Y"].default_value = 1.0
    psc.inputs["Z"].default_value = 1.0
    L.new(ratio.outputs[0], psc.inputs["Y"])
    psq = C.require_node(tree, "GeometryNodeTransform", (-640, -300))
    L.new(psc.outputs[0], psq.inputs["Scale"])
    L.new(out_(prof, "Curve"), psq.inputs["Geometry"])
    flat_profile = psq.outputs["Geometry"]

    c2m = C.require_node(tree, "GeometryNodeCurveToMesh", (-460, 100))
    L.new(band_curve, c2m.inputs["Curve"])
    L.new(flat_profile, c2m.inputs["Profile Curve"])

    # The swept tube is circular. Scaling Y by Band Width / Band Depth turns it
    # into a flat ribbon; drive the Y component of Scale from the ratio.
    band = c2m.outputs["Mesh"]
    band_set = C.require_node(tree, "GeometryNodeSetMaterial", (-280, -220))
    L.new(band, band_set.inputs["Geometry"])
    L.new(gmat(tree), band_set.inputs["Material"])
    band = band_set.outputs["Geometry"]

    # ---------------------------------------------------------- 3. filigree scrolls
    # A CurveSpiral emits a CURVE, and a curve is not a valid instance source --
    # Instance on Points silently produced ZERO scrolls (measured 0 verts with the
    # selection both wired and unwrapped). Sweep a small circle along the spiral to
    # turn it into a mesh, exactly as the gems' IcoSphere already is.
    scroll = _scroll_proto(tree, (-1000, 620))
    scroll_prof = C.require_node(tree, "GeometryNodeCurvePrimitiveCircle", (-820, 420))
    scroll_prof.mode = "RADIUS"
    scroll_prof.inputs["Resolution"].default_value = 6
    L.new(g("Scroll Wire"), scroll_prof.inputs["Radius"])
    scroll_c2m = C.require_node(tree, "GeometryNodeCurveToMesh", (-820, 620))
    L.new(out_(scroll, "Curve", "Geometry"), scroll_c2m.inputs["Curve"])
    L.new(out_(scroll_prof, "Curve", "Geometry"), scroll_c2m.inputs["Profile Curve"])

    # A CurveSpiral with Height=0 is a flat disc in the XY plane. The band also runs
    # in the XY plane, so an un-rotated scroll lies PARALLEL to the band and is
    # invisible edge-on -- which is why 294 scroll verts rendered as nothing. Stand
    # the proto up in the XZ plane, then spin each instance to its own angle so the
    # scroll faces outward everywhere around the head.
    # No fixed rotation here: the per-instance Z spin (Start + Factor*sweep) is what
    # aims the scroll outward, and a baked 90 deg here fights it.
    scroll_up = C.require_node(tree, "GeometryNodeTransform", (-660, 620))
    scroll_up.inputs["Rotation"].default_value = (math.radians(90.0), 0.0, 0.0)
    L.new(scroll_c2m.outputs["Mesh"], scroll_up.inputs["Geometry"])
    # push the scrolls off the band face so they are not buried inside it
    scroll_off = C.require_node(tree, "GeometryNodeTransform", (-520, 620))
    scroll_off.inputs["Translation"].default_value = (0.0, 0.0, 0.0)
    zc = C.require_node(tree, "ShaderNodeCombineXYZ", (-660, 520))
    L.new(gin_out(tree, "Scroll Rise"), zc.inputs["Z"])
    L.new(zc.outputs[0], scroll_off.inputs["Translation"])
    L.new(scroll_up.outputs["Geometry"], scroll_off.inputs["Geometry"])
    scroll_mesh = scroll_off.outputs["Geometry"]

    iop = C.require_node(tree, "GeometryNodeInstanceOnPoints", (-380, 560))
    L.new(scroll_mesh, iop.inputs["Instance"])
    # density control: the arc has a fixed 64 samples; thin to the dial
    # Keep every Nth curve point so the dial controls how many scrolls appear.
    # The step MUST divide by the same number the arc is sampled at. It previously
    # divided by a hardcoded 64 while the arc was at its 16-sample default, so only
    # index 0 passed and the entire band carried a single scroll (measured: the
    # scroll branch spanned 25 mm of a 426 mm band).
    # ONE instance per motif, by RESAMPLING the band to exactly Filigree Density
    # points -- no selection arithmetic at all.
    #
    # Two earlier attempts failed and both are worth recording:
    #   * `Index % step < 0.5`  -> GN MODULO runs on floats, so the fractional part
    #     CLUSTERS. 9 scrolls collapsed to 4 angular buckets of 486 verts, then 6
    #     scrolls of unequal spacing.
    #   * `FRACT(Factor/step) < 1/step` -> Factor/step is already < 1, so FRACT is
    #     the identity and EVERY point passed: 46,170 verts of scroll.
    # Resampling sidesteps the whole class: the curve is cut into N control points
    # and Instance on Points makes exactly one scroll at each.
    # ONE instance per motif, positioned on the band's OUTER FACE.
    #
    # Three failed approaches, all recorded because the reason is not obvious:
    #  * `Index % step < 0.5`   -> GN MODULO is float, so the fractional part
    #    CLUSTERS: 9 scrolls collapsed to 4 angular buckets of 486 verts.
    #  * `FRACT(Factor/step) < 1/step` -> Factor/step is already < 1, so FRACT is the
    #    identity and EVERY point passed: 46,170 verts of scroll.
    #  * Instancing at the band curve -> each curl is CENTRED on the band surface,
    #    so half of a 30 mm-radius scroll reached r=0.180, 24 mm inside a 0.204 head
    #    (180 verts clustered inward at one bearing).
    #  * Offsetting the centres in +Z -> on a horizontal ring +Z is UP, not radially
    #    outward; the whole circlet climbed 30 mm off the brow.
    #
    # The fix: Curve to Points supplies a per-point NORMAL, which on a ring curve
    # IS the radial direction. Push each point outward along its own normal by the
    # scroll radius, so the whole curl stands clear of the band surface.
    c2p = C.require_node(tree, "GeometryNodeCurveToPoints", (-700, 700))
    L.new(band_curve, c2p.inputs["Curve"])
    L.new(g("Filigree Density"), c2p.inputs["Count"])
    # The radial direction comes from Curve to Points' OWN Normal output, NOT from
    # GeometryNodeInputNormal. On curve points the Input Normal field is EMPTY --
    # measured: offsetting by 0.10 with it left every point bit-identical, so the
    # whole offset silently no-opped and 180 verts stayed inside the skull.
    # CurveToPoints.Normal is real: with a 0.21 radius arc, a 0.10 offset put every
    # point at r=0.310, i.e. exactly radial.
    scroll_lift = C.require_node(tree, "ShaderNodeMath", (-340, 560))
    scroll_lift.operation = "ADD"
    L.new(g("Scroll Rise"), scroll_lift.inputs[0])
    L.new(g("Scroll Size"), scroll_lift.inputs[1])
    # scale that radial direction by (Scroll Rise + Scroll Size)
    stepv = C.require_node(tree, "ShaderNodeVectorMath", (-180, 620))
    stepv.operation = "SCALE"
    L.new(C.sock(c2p, "Normal", outputs=True), stepv.inputs[0])
    L.new(scroll_lift.outputs[0], stepv.inputs["Scale"])

    liftx = C.require_node(tree, "GeometryNodeSetPosition", (20, 700))
    L.new(c2p.outputs["Points"], liftx.inputs["Geometry"])
    L.new(stepv.outputs["Vector"], liftx.inputs["Offset"])
    L.new(liftx.outputs["Geometry"], iop.inputs["Points"])

    # Spin each scroll to face outward. SplineParameter.Factor runs 0..1 along the
    # band; Factor * 360 is the angle. RotateInstances takes a Rotation VECTOR in
    # 5.2 (no rotation_type enum), so build the euler triple via CombineXYZ.
    # Orient each scroll to face OUTWARD along the band's local normal.
    #
    # Factor * 360 spins from the curve's start, which is the nape -- so mid-arc
    # scrolls ended up edge-on and invisible (render showed ornament only at the two
    # arc ends, where the spin happened to line up). Factor is 0..1 over the sweep,
    # so the correct angle is  START + Factor*sweep  (the arc's own Start Angle).
    spl = C.require_node(tree, "GeometryNodeSplineParameter", (-380, 760))
    angm = C.require_node(tree, "ShaderNodeMath", (-200, 760))
    angm.operation = "MULTIPLY"
    L.new(spl.outputs["Factor"], angm.inputs[0])
    L.new(sweep.outputs[0], angm.inputs[1])          # Factor * sweep
    offm = C.require_node(tree, "ShaderNodeMath", (-40, 760))
    offm.operation = "ADD"
    L.new(angm.outputs[0], offm.inputs[0])
    L.new(startm.outputs[0], offm.inputs[1])         # + Start Angle
    rotv = C.require_node(tree, "ShaderNodeCombineXYZ", (120, 760))
    rotv.inputs["X"].default_value = 0.0
    rotv.inputs["Y"].default_value = 0.0
    L.new(offm.outputs[0], rotv.inputs["Z"])
    spin = C.require_node(tree, "GeometryNodeRotateInstances", (300, 620))
    L.new(iop.outputs["Instances"], spin.inputs["Instances"])
    L.new(rotv.outputs[0], spin.inputs["Rotation"])
    scrolls = spin.outputs["Instances"]

    # ---------------------------------------------------------- 4. centre gems
    # Gems ride the BAND CURVE, not a straight chord.
    #
    # The original placed them on a Curve Line at y = BROW_CY, which is the head's
    # own AXIS -- so all 5 gems (60 verts, confirmed present) were buried inside the
    # skull and invisible in every render. Resample the band itself to Gem Count and
    # instance there: the same approach as the filigree, and the gems then sit on the
    # band surface by construction rather than by arithmetic.
    rsm = C.require_node(tree, "GeometryNodeResampleCurve", (-660, 260))
    # 5.2: ResampleCurve has NO .mode property -- it is a menu SOCKET. The addon
    # ships set_resample_count() for exactly this; do not assign rsm.mode.
    C.set_resample_count(rsm, None)
    L.new(band_curve, rsm.inputs["Curve"])
    L.new(g("Gem Count"), rsm.inputs["Count"])

    gem = C.require_node(tree, "GeometryNodeMeshIcoSphere", (-460, 420))
    L.new(g("Gem Size"), gem.inputs["Radius"])
    gem.inputs["Subdivisions"].default_value = 1

    # the gems carry their own stone material so they read as stones, not gold
    gem_set = C.require_node(tree, "GeometryNodeSetMaterial", (-380, 460))
    L.new(out_(gem, "Mesh", "Geometry"), gem_set.inputs["Geometry"])
    L.new(gsock(tree), gem_set.inputs["Material"])

    ginst = C.require_node(tree, "GeometryNodeInstanceOnPoints", (-280, 320))
    L.new(rsm.outputs["Curve"], ginst.inputs["Points"])
    L.new(gem_set.outputs["Geometry"], ginst.inputs["Instance"])
    # stand the gems off the band face so they read as mounted on it
    gem_up = C.require_node(tree, "GeometryNodeTransform", (-60, 300))
    gz = C.require_node(tree, "ShaderNodeCombineXYZ", (-280, 220))
    L.new(g("Gem Rise"), gz.inputs["Z"])
    L.new(gz.outputs[0], gem_up.inputs["Translation"])
    L.new(ginst.outputs["Instances"], gem_up.inputs["Geometry"])
    gems = gem_up.outputs["Geometry"]

    # ---------------------------------------------------------- 5. assemble
    # Material the metal BEFORE the gems join, so the gems keep their own stone.
    # A single Set Material at the very end overwrites everything, which is why an
    # earlier render showed gold knobs where gems should be.
    metal_set = C.require_node(tree, "GeometryNodeSetMaterial", (320, 420))
    L.new(scrolls, metal_set.inputs["Geometry"])
    L.new(gmat(tree), metal_set.inputs["Material"])
    scrolls = metal_set.outputs["Geometry"]

    join = C.require_node(tree, "GeometryNodeJoinGeometry", (320, 200))
    for i, sock in enumerate((band, scrolls, gems)):
        if i == 0:
            L.new(sock, join.inputs["Geometry"])
        else:
            L.new(sock, C.sock(join, "Geometry", i))

    realize = C.require_node(tree, "GeometryNodeRealizeInstances", (520, 200))
    L.new(join.outputs["Geometry"], realize.inputs["Geometry"])

    # Set Material so the gold travels WITH the geometry. Assigning it to the object
    # after the fact silently fails when the base mesh is empty at save time
    # (measured: materials: [] on the staged object, so it rendered white).
    L.new(realize.outputs["Geometry"], gout.inputs["Geometry"])
    return tree


def _scroll_proto(tree, loc):
    """Planar filigree scroll: a small spiral flattened in Y so it lies on the band."""
    n = C.require_node(tree, "GeometryNodeCurveSpiral", loc)
    L = tree.links
    turns = tree.nodes.new("ShaderNodeMath")
    turns.name = "Turns"
    turns.location = (loc[0] + 200, loc[1] - 140)
    turns.operation = "MULTIPLY"
    L.new(gin_out(tree, "Scroll Turns"), turns.inputs[0])
    turns.inputs[1].default_value = 1.0
    L.new(turns.outputs[0], n.inputs["Rotations"])
    # End Radius and Height default to 2.0 on a fresh CurveSpiral, so a small
    # Start Radius produced a 13mm -> 2m funnel instead of a curl. Pin both.
    L.new(gin_out(tree, "Scroll Size"), n.inputs["Start Radius"])
    n.inputs["End Radius"].default_value = 0.0008
    n.inputs["Height"].default_value = 0.0
    n.inputs["Resolution"].default_value = 32
    return n


def gin_out(tree, name):
    return tree.nodes["Group Input"].outputs[name]


if __name__ == "__main__":
    t = build()
    print("BUILT %s nodes=%d" % (t.name, len(t.nodes)))
    bpy.ops.wm.save_as_mainfile(
        filepath=os.path.join(_HERE, "melusina_circlet_stage.blend"))
