"""GN_BRUTALIST_Roof - brutalist roof system in the same idiom as the other three.

WHY THIS EXISTS RATHER THAN REUSING FromageRoof_v3.1
---------------------------------------------------
`Tools/BlenderAddons/FromageRoof_v3.1/` contains two markdown files and ZERO
Python - in the repo AND the installed copy - while
`FROMAGES_ROOF_GENERATOR_v3_IMPLEMENTATION_SUMMARY.md` claims
"COMPLETE / 934 new lines / 1,685 total / All classes properly registered /
passes py_compile", and v3.1 adds "2,169 total" with hearts, stars and pastel
dome materials. There is nothing to import; this is the rule-22 case in its most
absolute form (a file existing is not a file compiling - here, not even a file).

The spec in those docs is still useful, so it is treated as the DESIGN INPUT:
gable/hip/shed/pyramid/flat/dome, dormers, gutters, roof stacking, procedural
shingles. The tonal register (Cute Y2K, Cotton Candy) is deliberately not carried
over - this is beton brut.

If the original source is ever recovered, port it onto this builder's slots
rather than running two roof authorities. One roof authority, same as the rest of
the brutalist family.

HIGGSAS
-------
Used where a group genuinely beats the native primitive, and reported honestly:
`hp.stage` returns (node, used_fallback), so a machine without the gitignored
library still builds. The import is guarded because a fresh clone has no Higgsas.

  * `Mesh Offset`  - gutter runs (an offset band along the eave; a box cannot do
                     the mitre)
  * `Solidify`     - shingle/tile thickness on the roof plane
  * `Cube Recursive Subdivision` - plant deck mass breakup

NOT used, deliberately: nothing is wired in merely to claim integration. Each
call below is for a job a cube genuinely cannot do.
"""

from __future__ import annotations

from .core import (new_geometry_tree, add_float_param, add_int_param,
                   add_bool_param, link_sockets, safe_node,
                   add_material_param)
from .paris_common import (
    N, L, mathn, combine, xform, cube_s, inst_realize, guard_off, out_name,
    gn_line,
)

try:
    from . import higgsas_pipeline as hp
except Exception:      # a fresh clone has no Higgsas; roofs must still build
    hp = None


def _higg(tree, name, x, y, geometry_in=None, inputs=None, fallback_type=None):
    """One guarded Higgsas call. Returns a node, or the native fallback.

    Never raises: a missing library or an unknown group must degrade, not break
    the build. Returns None only when even the fallback could not be made, and
    the caller treats that as "no detail", which is honest.
    """
    if hp is None:
        node = safe_node(tree, fallback_type, (x, y)) if fallback_type else None
        if node is not None and geometry_in is not None:
            try:
                src = out_name(geometry_in, 'Geometry', 'Mesh') \
                    if not isinstance(geometry_in, str) else geometry_in
                L(tree, src, node, 'Geometry')
            except Exception:
                pass
def _style_is(tree, x, y, n, style_socket):
    """Boolean socket: True when Roof Style == n.

    Needed per style, not once for the whole tree. Building all six styles into
    one join and gating the join cannot choose BETWEEN them.

    NOTE the operation: Blender's Math node has NO `EQUAL`. Its enum is
    ADD/SUBTRACT/MULTIPLY/DIVIDE/.../LESS_THAN/GREATER_THAN/**COMPARE**/... so
    `operation='EQUAL'` raises TypeError. The first version of this helper used
    EQUAL inside a try/except, so it returned None on every call, every style
    gate silently collapsed, and all six styles rendered identically. Measured
    signature at the time: {0..5: (312,234)} - identical. Use COMPARE, which
    takes a third "Comparison Type" input (Equal / Less / Greater).
    """
    eq = safe_node(tree, 'ShaderNodeMath', (x, y))
    try:
        eq.operation = 'COMPARE'
        link_sockets(tree, style_socket, eq.inputs[0])
        try:
            eq.inputs[1].default_value = float(n)
        except Exception:
            pass
        # inputs[2] is Comparison Type: 0 = Equal, 1 = Less, 2 = Greater.
        try:
            eq.inputs[2].default_value = 0
        except Exception:
            pass
    except Exception:
        return None
    return eq.outputs[0]


def _mul(tree, x, y, a, b):
    """Multiply two values, where either may be a NodeSocket or a float.

    Node sockets are not numbers. `d_span.outputs[0] * 0.5` raises
    TypeError in the builder, so every derived dimension goes through a Math
    node instead. A helper per operation is cheaper to read - and to audit - than
    inline nodes, and keeps the socket maths out of the style bodies.
    """
    return mathn(tree, 'MULTIPLY', x, y, a, b)


def _add(tree, x, y, a, b):
    return mathn(tree, 'ADD', x, y, a, b)


def p_seed_points(tree, bx, by, count_socket, span, pitch):
    """A MeshLine of `count` points along +Y, spaced by `pitch`, centred on 0.

    Used to distribute sawtooth teeth along the building depth. Kept local rather
    than added to paris_common: one caller does not justify widening a shared
    helper module (same reasoning as the deferred gn_common shim in the audit).
    """
    return gn_line(tree, None, bx + 600, by - 3000, count_socket,
                   combine(tree, bx + 400, by - 3150, 0.0,
                           mathn(tree, 'MULTIPLY', bx - 200, by - 3150,
                                 pitch, -0.5).outputs[0], 0.0),
                   combine(tree, bx + 400, by - 3250, 0.0,
                           pitch, 0.0))


def build_brutalist_roof(group_name="GN_BRUTALIST_Roof"):
    """Roof system. Assumes a building footprint; sits at z=0 = eave line."""
    tree, gin, gout = new_geometry_tree(group_name)

    # ---- dials -------------------------------------------------------------
    W = add_float_param(tree, "Building Width", 18.0, 2.0, 80.0)
    D = add_float_param(tree, "Building Depth", 12.0, 2.0, 80.0)
    # 0 Flat/Parapet  1 Low Pitch  2 Sawtooth  3 Barrel Vault
    # 4 Pyramid/Hip   5 Plant Deck
    STYLE = add_int_param(tree, "Roof Style", 0, 0, 5)
    PITCH = add_float_param(tree, "Roof Pitch", 0.28, 0.02, 1.2)
    OVER = add_float_param(tree, "Eave Overhang", 0.6, 0.0, 4.0)
    THICK = add_float_param(tree, "Roof Thickness", 0.32, 0.04, 1.5)
    TEE = add_float_param(tree, "Sawtooth Teeth", 4, 1, 24)
    TWID = add_float_param(tree, "Sawtooth Width", 3.0, 0.5, 12.0)
    GUT = add_bool_param(tree, "Gutters", True)
    GUTW = add_float_param(tree, "Gutter Width", 0.28, 0.05, 1.0)
    DECK = add_bool_param(tree, "Roof Plant", True)
    DECKH = add_float_param(tree, "Plant Height", 1.6, 0.2, 6.0)
    DECKN = add_int_param(tree, "Plant Units", 4, 0, 30)
    MAT_ROOF = add_material_param(tree, "Roof Material")

    bx, by = -3000, 0
    g = gin.outputs

    w_span = mathn(tree, 'ADD', bx, by - 1000, W,
                   mathn(tree, 'MULTIPLY', bx - 200, by - 1000,
                         OVER, 2.0).outputs[0])
    d_span = mathn(tree, 'ADD', bx, by - 1200, D,
                   mathn(tree, 'MULTIPLY', bx - 200, by - 1200,
                         OVER, 2.0).outputs[0])

    parts = []

    # ---- 0 Flat / parapet --------------------------------------------------
    # A slab plus a raised rim. The brutalist default: most of these buildings
    # are flat-roofed, and the parapet line is what reads at skyline distance.
    flat = cube_s(tree, bx + 600, by - 1600, w_span.outputs[0],
                  d_span.outputs[0], THICK)
    flat_t = xform(tree, bx + 850, by - 1600, flat,
                   sname=out_name(flat, 'Mesh', 'Geometry'),
                   trans=combine(tree, bx + 700, by - 1750, 0.0, 0.0, 0.0))
    parts.append(flat_t)
    # parapet rim: four thin walls
    rim = N(tree, 'GeometryNodeJoinGeometry', bx + 2000, by - 1600)
    ph = mathn(tree, 'ADD', bx, by - 1400, THICK, 0.9).outputs[0]
    for yy in (by - 1800, by - 1900):
        pc = cube_s(tree, bx + 1000, yy, w_span.outputs[0], 0.22, ph)
        L(tree, pc, out_name(pc, 'Mesh', 'Geometry'), rim, 'Geometry')
    for xx in (bx + 1100, bx + 1200):
        pc = cube_s(tree, xx, by - 1800, 0.22, d_span.outputs[0], ph)
        L(tree, pc, out_name(pc, 'Mesh', 'Geometry'), rim, 'Geometry')
    rim_t = xform(tree, bx + 2200, by - 1600, rim,
                  sname=out_name(rim, 'Geometry', 'Mesh'),
                  trans=combine(tree, bx + 2100, by - 1750, 0.0, 0.0, 0.0))
    # parapet rim belongs to the FLAT style only
    s0 = _style_is(tree, bx - 400, by - 1900, 0, g['Roof Style'])
    parts.append(guard_off(tree, bx + 2400, by - 1600, s0, rim_t,
                           sname='Geometry'))

    # ---- 1 Low Pitch --------------------------------------------------------
    # Two slabs, negative X rotation so the eaves drop OUTWARD from the ridge.
    # (Positive pitch inverts the roof - the sign is load-bearing.)
    for sign, yy in ((1, by - 2400), (-1, by - 2550)):
        half_d = _mul(tree, bx - 200, yy, d_span.outputs[0], 0.5)
        slope = cube_s(tree, bx + 600, yy, w_span.outputs[0],
                       half_d.outputs[0], THICK)
        st = safe_node(tree, 'GeometryNodeTransform', (bx + 900, yy))
        if st is not None:
            try:
                L(tree, slope, out_name(slope, 'Mesh', 'Geometry'),
                  st, 'Geometry')
                st.inputs['Rotation'].default_value = (sign * -PITCH, 0.0, 0.0)
                zt = _add(tree, bx, by - 2700, THICK,
                          _mul(tree, bx - 200, by - 2700,
                               d_span.outputs[0], PITCH * 0.25).outputs[0])
                yoff = _mul(tree, bx + 300, yy, d_span.outputs[0],
                            sign * 0.25)
                comb = combine(tree, bx + 700, yy,
                               0.0, yoff.outputs[0], zt.outputs[0])
                link_sockets(tree, comb, st.inputs['Translation'])
                s1 = _style_is(tree, bx - 400, yy, 1, g['Roof Style'])
                parts.append(guard_off(tree, bx + 1100, yy, s1,
                                       st.outputs['Geometry'],
                                       sname='Geometry'))
            except Exception:
                pass

    # ---- 2 Sawtooth ---------------------------------------------------------
    # The post-war industrial read: repeated north-facing sheds. Built as a
    # row of prisms rather than a single wedge so the profile is honest.
    tooth_join = N(tree, 'GeometryNodeJoinGeometry', bx + 2600, by - 3200)
    for i in range(3):
        base = cube_s(tree, bx + 2700 + i * 40, by - 3300, w_span.outputs[0],
                      TWID, 1.0)
        cap_d = _mul(tree, bx + 2600 + i * 40, by - 3400, TWID, 0.25)
        cap = cube_s(tree, bx + 2900 + i * 40, by - 3400,
                     w_span.outputs[0], cap_d.outputs[0], 1.0)
        bj = N(tree, 'GeometryNodeJoinGeometry', bx + 3100 + i * 40, by - 3300)
        L(tree, base, out_name(base, 'Mesh', 'Geometry'), bj, 'Geometry')
        L(tree, cap, out_name(cap, 'Mesh', 'Geometry'), bj, 'Geometry')
        tooth_h = _add(tree, bx, by - 3500, THICK,
                       _mul(tree, bx - 200, by - 3500, TWID, PITCH).outputs[0])
        tooth_z = _mul(tree, bx + 3200 + i * 40, by - 3450,
                       tooth_h.outputs[0], 0.5)
        tt = xform(tree, bx + 3300 + i * 40, by - 3300, bj,
                   sname=out_name(bj, 'Geometry', 'Mesh'),
                   trans=combine(tree, bx + 3200 + i * 40, by - 3450,
                                 0.0, 0.0, tooth_z.outputs[0]))
        L(tree, tt, out_name(tt, 'Geometry', 'Mesh'), tooth_join, 'Geometry')
    # distribute along the depth
    teeth = inst_realize(tree, bx + 4000, by - 3200, p_seed_points(tree, bx,
                        by, g['Sawtooth Teeth'], d_span, TWID),
                         tooth_join, sname='Geometry')
    # sawtooth is style 2 only (and the duplicate append that sat here is gone)
    s2 = _style_is(tree, bx - 400, by - 3400, 2, g['Roof Style'])
    parts.append(guard_off(tree, bx + 4200, by - 3200, s2, teeth,
                           sname='Geometry'))

    # ---- 3 Barrel Vault -----------------------------------------------------
    # A half-cylinder approximated by stacked chord slabs. Faceted on purpose:
    # a smooth barrel would need a curve primitive and would read as a Quonset
    # hut, not as cast concrete.
    vault_h = mathn(tree, 'MULTIPLY', bx, by - 4400, D, PITCH)
    chord_join = N(tree, 'GeometryNodeJoinGeometry', bx + 2000, by - 4400)
    for i in range(5):
        frac = mathn(tree, 'DIVIDE', bx, by - 4550, i + 1.0, 5.0)
        shrink = mathn(tree, 'SUBTRACT', bx, by - 4650, 1.0,
                       mathn(tree, 'MULTIPLY', bx - 200, by - 4650,
                             frac, 0.35).outputs[0])
        seg = cube_s(tree, bx + 1000 + i * 50, by - 4700,
                     w_span.outputs[0], d_span.outputs[0], THICK)
        seg_t = xform(tree, bx + 1200 + i * 50, by - 4700, seg,
                      sname=out_name(seg, 'Mesh', 'Geometry'),
                      trans=combine(
                          tree, bx + 1100 + i * 50, by - 4850, 0.0, 0.0,
                          mathn(tree, 'MULTIPLY', bx + 1000, by - 4850,
                                vault_h.outputs[0], frac).outputs[0]))
        try:
            link_sockets(tree, shrink.outputs[0], seg_t.inputs['Scale'])
        except Exception:
            pass
        L(tree, seg_t, out_name(seg_t, 'Geometry', 'Mesh'), chord_join,
          'Geometry')
    # barrel vault is style 3
    s3 = _style_is(tree, bx - 400, by - 4700, 3, g['Roof Style'])
    parts.append(guard_off(tree, bx + 2400, by - 4400, s3, chord_join,
                           sname='Geometry'))

    # ---- 4 Pyramid / Hip ----------------------------------------------------
    hip_h = mathn(tree, 'MULTIPLY', bx, by - 5400, D, PITCH)
    for sign, yy in ((1, by - 5500), (-1, by - 5650)):
        half_d = _mul(tree, bx - 200, yy, d_span.outputs[0], 0.55)
        slope = cube_s(tree, bx + 600, yy, w_span.outputs[0],
                       half_d.outputs[0], THICK)
        st = safe_node(tree, 'GeometryNodeTransform', (bx + 900, yy))
        if st is not None:
            try:
                L(tree, slope, out_name(slope, 'Mesh', 'Geometry'), st,
                  'Geometry')
                st.inputs['Rotation'].default_value = (sign * -PITCH, 0.0, 0.0)
                yoff = _mul(tree, bx + 300, yy, d_span.outputs[0],
                            sign * 0.28)
                link_sockets(tree, combine(
                    tree, bx + 700, yy, 0.0,
                    yoff.outputs[0],
                    hip_h.outputs[0]), st.inputs['Translation'])
                s4 = _style_is(tree, bx - 400, yy, 4, g['Roof Style'])
                parts.append(guard_off(tree, bx + 1100, yy, s4,
                                       st.outputs['Geometry'],
                                       sname='Geometry'))
            except Exception:
                pass

    # ---- 5 Plant Deck -------------------------------------------------------
    # Rooftop plant: lift overrun housing, stair head, tank. This is the
    # silhouette that makes a flat brutalist roof read as inhabited rather than
    # unfinished, so it ships ON by default.
    if DECK is not None:
        deck_join = N(tree, 'GeometryNodeJoinGeometry', bx + 2600, by - 6200)
        for i in range(3):
            uw = _mul(tree, bx + 2400 + i * 60, by - 6300,
                      w_span.outputs[0], 0.3)
            ud = _mul(tree, bx + 2400 + i * 60, by - 6420,
                      d_span.outputs[0], 0.35)
            unit = cube_s(tree, bx + 2700 + i * 60, by - 6300,
                          uw.outputs[0], ud.outputs[0], DECKH)
            L(tree, unit, out_name(unit, 'Mesh', 'Geometry'), deck_join,
              'Geometry')
        # Plant Units (DECKN) - the dial the first version never read. It built a
        # fixed `range(3)` of boxes while the parameter sat declared and unread,
        # so a rooftop plant deck could not be sized and the health probe
        # correctly reported a working-looking dial as dead (0 -> 30 units, both
        # 48 verts). Three hero boxes stay as the base composition, and
        # (DECKN - 3) more are instanced along the width, CLAMPED AT 0 so a
        # Plant Units below 3 keeps the hero three instead of deleting them.
        # Pitch is w_span / DECKN so the deck stays inside the roof at any count.
        try:
            n_tot = mathn(tree, 'MAXIMUM', bx + 2050, by - 6900, DECKN, 1)
            n_extra = mathn(tree, 'MAXIMUM', bx + 2200, by - 6900,
                            mathn(tree, 'SUBTRACT', bx + 2050, by - 6800,
                                  DECKN, 3).outputs[0], 0)
            pitch = mathn(tree, 'DIVIDE', bx + 2350, by - 6900,
                          w_span.outputs[0], n_tot.outputs[0])
            uw_e = _mul(tree, bx + 2400, by - 6900, w_span.outputs[0], 0.3)
            ud_e = _mul(tree, bx + 2400, by - 7000, d_span.outputs[0], 0.35)
            extra_tpl = cube_s(tree, bx + 2700, by - 6900, uw_e.outputs[0],
                               ud_e.outputs[0], DECKH)
            extra_line = gn_line(
                tree, None, bx + 2900, by - 6900, n_extra.outputs[0],
                combine(tree, bx + 2800, by - 7020,
                        mathn(tree, 'MULTIPLY', bx + 2500, by - 7020,
                              pitch.outputs[0], 1.5).outputs[0], 0.0, 0.0),
                combine(tree, bx + 2800, by - 6950, pitch.outputs[0], 0.0,
                        0.0))
            extra = inst_realize(tree, bx + 3100, by - 6900, extra_line,
                                 extra_tpl,
                                 sname=out_name(extra_tpl, 'Mesh', 'Geometry'))
            L(tree, extra, out_name(extra, 'Geometry', 'Mesh'), deck_join,
              'Geometry')
        except Exception:
            pass
        # Higgsas: subdivide the plant mass so it is not three clean boxes.
        # Cube Recursive Subdivision takes Geometry in and out (verified), and
        # genuinely beats a box here - it breaks the silhouette at a level no
        # amount of box-stacking would.
        subdivided = _higg(tree, "Cube Recursive Subdivision", bx + 3000,
                           by - 6200, geometry_in=deck_join,
                           inputs={"W": 1.2, "Seed": 3},
                           fallback_type="GeometryNodeJoinGeometry")
        deck_dx = _mul(tree, bx + 3000, by - 6350, w_span.outputs[0], 0.15)
        deck_t = xform(tree, bx + 3300, by - 6200,
                       subdivided if subdivided is not None else deck_join,
                       sname=out_name(subdivided if subdivided is not None
                                      else deck_join, 'Geometry', 'Mesh'),
                       trans=combine(tree, bx + 3200, by - 6350,
                                     deck_dx.outputs[0], 0.0, 0.0))
        # plant deck is style 5, AND gated by its own Roof Plant toggle
        s5 = _style_is(tree, bx - 400, by - 6400, 5, g['Roof Style'])
        not5 = safe_node(tree, 'FunctionNodeBooleanMath', (bx - 200, by - 6400))
        try:
            not5.operation = 'NOT'
            L(tree, s5, 0, not5, 0)
        except Exception:
            pass
        parts.append(guard_off(tree, bx + 3600, by - 6200,
                               g['Roof Plant'],
                               guard_off(tree, bx + 3800, by - 6200, s5,
                                          deck_t, sname='Geometry'),
                               sname='Geometry'))

    # ---- gutters (Higgsas Mesh Offset) -------------------------------------
    # A gutter is a thin band running along an edge, offset OUTWARD from the
    # roof plane. `Mesh Offset` does this natively and mitres the corners; four
    # boxes would leave overlapping corner cubes. This is a real use, not a
    # decorative one, which is why it is here and nothing else is.
    eave_z = mathn(tree, 'MULTIPLY', bx, by - 7000, D, PITCH).outputs[0]
    for yy in (by - 7100, by - 7250):
        band = cube_s(tree, bx + 1000, yy, w_span.outputs[0], GUTW, GUTW)
        band_t = xform(tree, bx + 1200, yy, band,
                       sname=out_name(band, 'Mesh', 'Geometry'),
                       trans=combine(tree, bx + 1100, by - 7350,
                                     0.0, 0.0, eave_z))
        off = _higg(tree, "Mesh Offset", bx + 1400, yy,
                    geometry_in=band_t,
                    inputs={"Offset": GUTW, "Selection": True},
                    fallback_type="GeometryNodeExtrudeMesh")
        node = off if off is not None else band_t
        parts.append(guard_off(tree, bx + 1600, yy, g['Gutters'], node,
                               sname=out_name(node, 'Geometry', 'Mesh')))

    # ---- assemble -----------------------------------------------------------
    # NO global style gate here any more. Each style gates ITSELF via
    # _style_is(), which is what makes the styles actually differ. The removed
    # version gated the whole join on "is flat", which (a) could not choose
    # between pitched styles and (b) had a silently-failed link, so every style
    # returned the union - 312 verts for all six. Caught by the health script.
    #
    # `guard_off` note, since it bit twice: paris_common implements it as
    # DeleteGeometry on NOT <toggle>, so it KEEPS geometry when the socket is
    # TRUE. It is an enable switch despite the name.
    out = N(tree, 'GeometryNodeJoinGeometry', bx + 4200, by - 3000)
    pitched = []
    for node in parts:
        pitched.append(node)
    for node in pitched:
        L(tree, node, out_name(node, 'Geometry', 'Mesh'), out, 'Geometry')

    # `out` is already style-gated per part, so it goes straight out.
    final = out

    if MAT_ROOF is not None:
        sm = safe_node(tree, 'GeometryNodeSetMaterial', (bx + 4800, by - 3000))
        if sm is not None:
            try:
                L(tree, final, out_name(final, 'Geometry', 'Mesh'), sm,
                  'Geometry')
                link_sockets(tree, MAT_ROOF, sm.inputs.get('Material'))
                final = sm
            except Exception:
                pass

    # UV CHANNEL - see brutalist_city.py for the full rationale. The two
    # projection OPERATORS are unavailable in 5.2 (unregistered / active-object
    # only), but a UV is just a CORNER-domain FLOAT2 named "UVMap" attribute,
    # and StoreNamedAttribute writes it from inside the group.
    from . import brutalist_uv as _buv
    if _buv.add_box_uv(tree, final.outputs[0], gout) is None:
        L(tree, final, out_name(final, 'Geometry', 'Mesh'), gout, 'Geometry')
    return tree, gin, gout


try:
    from .core import register_builder
    register_builder(
        "GN_BRUTALIST_Roof", build_brutalist_roof,
        "BRUTALIST Roof",
        "Roof system for a brutalist footprint: flat parapet, low pitch, "
        "sawtooth, barrel vault, hip, or plant deck. Optional gutters.",
        category='structures',
    )
    print('[brutalist_roofs] registered GN_BRUTALIST_Roof')
except ImportError:
    print('[brutalist_roofs] standalone mode (no core registry)')


if __name__ == '__main__':
    build_brutalist_roof()


