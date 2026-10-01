"""Brutalist city block - the 2D exterior massing layer.

GN_BRUTALIST_CityBlock (build_brutalist_city_block)

Why this exists (audit 2026-09-25, Saved/Audit/BRUTALIST_CONVERGENCE_AUDIT_2026-09-25.md §5e):
the `city_gen` category held 9 builders but they are baroque / Infinity-Nikki houses
(melodia_city_gen.py wraps MEL_greybox_room_kit). And the scene-composition system that
ALREADY arranges multiple arch types - `greybox_graph.spawn_graph` / GRAPH_REGISTRY -
walks a single X axis (`x += spacing`, `location = (x, 0, 0)`) and then pairwise-snaps,
so it is a 1D chain that cannot lay out a 2D grid. It also spawns greybox `arch_type`s
through `bpy.ops.surreal_arch.generate()`, not `GN_*` node groups. A 2D procedural city
therefore had no owner at all.

Layout contract (what the health script asserts):
  * lot grid is `Blocks X` x `Blocks Y`, pitch = Lot/Sidewalk + Street on each axis;
  * each lot carries a sidewalk slab, and a massing block inset by Setback;
  * massing height is RANDOM per lot, uniform in [Height Min, Height Max], driven by
    the Seed - so a failed Scale link collapses every block to 1 unit and the
    `zmax >= Height Min` assertion catches the classic silently-dropped-link defect;
  * the block itself is a recessed core with four FULL-HEIGHT corner piers plus a
    capping parapet band. All three live in ONE unit-height template (base z=0) that
    is scaled in Z by the per-lot height, so the piers stay full-height and the
    parapet stays on top without a second translate pass;
  * roads are two MeshLine-driven strip sets (one per axis) at Blocks+1 counts, so
    `Roads off` deletes strips rather than leaving stubs;
  * `Ground off` deletes the base slab; `Sidewalks off` deletes the lot slabs.

Front face is -Y (viewer looks into the grid), same as the brutalist family.
Massing is intentionally lightweight - this is the placement layer. Plugging
GN_BRUTALIST_OfficeBlock in as the per-lot massing group (the `_ensure_group_node`
pattern already used by melodia_city_gen.py) is P4b, as is street furniture reusing
MEL_street_lamp / MEL_fence / MEL_stylized_tree instead of rebuilding them.
"""

from __future__ import annotations

from .core import (new_geometry_tree, add_float_param, add_int_param,
                   add_bool_param, link_sockets, safe_node,
                   add_material_param)
from .paris_common import (
    N, L, mathn, combine, xform, cube_s, inst_realize, guard_off,
    out_name, gn_line,
)


def _rv_float_bounds(rv, lo, hi):
    """Set the FLOAT Min/Max on a FunctionNodeRandomValue.

    The node exposes 'Min'/'Max' THREE times (vector, float, int) and only the
    active data_type pair is meaningful. A name-only lookup returns the VECTOR
    socket, the float assignment is swallowed by the house try/except, and the
    random silently never took - the 'declared but never applied' defect class this
    project keeps getting bitten by. Match name AND socket type instead.
    """
    for want, value in (('Min', lo), ('Max', hi)):
        for s in rv.inputs:
            if s.name == want and s.type == 'VALUE':
                try:
                    s.default_value = float(value)
                except Exception:
                    pass
                break
    return rv


def _rv_float_socket(rv, name):
    """The FLOAT-typed 'Min'/'Max' socket on a RandomValue, or None.

    `rv.inputs['Min']` returns the VECTOR socket because RandomValue declares
    Min/Max three times. Linking a float into that is not a silent no-op - it is a
    RECORDED dropped link, which the health gate would (correctly) fail on.
    """
    for s in rv.inputs:
        if s.name == name and s.type == 'VALUE':
            return s
    return None

def _style_is(tree, x, y, n, style_socket):
    """Boolean socket: True when Facade Style == n.

    Twin of `_style_is` in brutalist_roofs.py (which gates Roof Style). Kept
    local for the same reason: one caller does not justify widening the shared
    helper module.

    Blender's Math node has NO `EQUAL` - its enum is ADD/SUBTRACT/MULTIPLY/
    DIVIDE/.../LESS_THAN/GREATER_THAN/**COMPARE**/... so `operation='EQUAL'`
    raises TypeError. COMPARE takes a third "Comparison Type" input (Equal /
    Less / Greater); inputs[2] = 0 selects Equal. See the roofs module, whose
    first version used EQUAL inside a try/except, returned None on every call,
    and rendered all six roof styles identically.
    """
    eq = safe_node(tree, 'ShaderNodeMath', (x, y))
    try:
        eq.operation = 'COMPARE'
        link_sockets(tree, style_socket, eq.inputs[0])
        try:
            eq.inputs[1].default_value = float(n)
        except Exception:
            pass
        try:
            eq.inputs[2].default_value = 0
        except Exception:
            pass
    except Exception:
        return None
    return eq.outputs[0]


def _style_is_int(tree, x, y, n, style_socket):
    """Boolean socket: True when an INT style socket == n (COMPARE-based).

    paris_common has no int-compare helper, and Blender's Math node has no
    EQUAL operation (see brutalist_roofs._style_is) - so stylesheet gating
    goes through COMPARE with threshold n and Comparison Type 0 (Equal).
    Returns the boolean socket, or None when the node could not be made
    (caller then treats the branch as absent, which is honest).
    """
    eq = safe_node(tree, 'ShaderNodeMath', (x, y))
    if eq is None:
        return None
    try:
        eq.operation = 'COMPARE'
        link_sockets(tree, style_socket, eq.inputs[0])
        try:
            eq.inputs[1].default_value = float(n)
        except Exception:
            pass
        try:
            eq.inputs[2].default_value = 0
        except Exception:
            pass
    except Exception:
        return None
    return eq.outputs[0]


def _build_facade(tree, bx, by, g, p):
    """Fenestration for the realised city massing. Returns a node, or None.

    Styles
        0 Blank     - nothing at all (default; pre-existing presets unchanged)
        1 Ribbon    - one continuous glazing band per floor
        2 Punched   - discrete windows on a bay grid
        3 Colonnade - deep vertical fins plus slot windows

    Higgsas is used where it earns its place, and reports honestly when absent:
    `hp.stage` returns `(node, used_fallback)`, so a machine without the
    (gitignored, machine-local) library degrades to the native path instead of
    failing the build. The import itself is guarded, because a fresh clone has no
    Higgsas at all and the city must still build.
    """
    try:
        from . import higgsas_pipeline as hp
    except Exception:
        hp = None

    style = p["style"]

    # --- style gate: emit NOTHING when Facade Style == 0 -------------------
    # A real boolean, so the gate can assert geometry is ABSENT for style 0
    # rather than merely small. The failure guarded here is a toggle that
    # quietly leaves a stub behind - the same defect the Ground/Roads toggles
    # are written against.
    #
    # Three Blender 5.2 facts, each of which cost a debugging round. All are
    # now recorded because all three fail SILENTLY through `except Exception`:
    #
    # 1. This CANNOT be a Boolean Math COMPARE. FunctionNodeBooleanMath exposes
    #    only AND/OR/NOT/NAND/NOR/XNOR/XOR/IMPLY/NIMPLY and has no `data_type`,
    #    so `operation='COMPARE'` raises TypeError. Use a Math node.
    #
    # 2. `guard_off` is misleadingly named. paris_common.py implements it as
    #    `DeleteGeometry` on `NOT <toggle>`, so it KEEPS geometry when the socket
    #    is TRUE and DELETES when FALSE. It is an enable switch. Passing
    #    "style != 0" therefore KEPT the facade for style 0 and deleted it for
    #    styles 1-3 - exactly inverted, and the opposite of what the name and
    #    the existing Ground/Roads call sites imply at a glance.
    #
    # 3. So the socket must be plain `style > 0`.
    try:
        has_facade = safe_node(tree, 'ShaderNodeMath', (bx - 400, by - 3000))
        has_facade.operation = 'GREATER_THAN'
        link_sockets(tree, style, has_facade.inputs[0])
        try:
            has_facade.inputs[1].default_value = 0.0
        except Exception:
            pass
    except Exception:
        return None
    # One gate per live style, so Ribbon / Punched / Colonnade are genuinely
    # different geometry instead of one branch with three names. Gate sockets
    # are None only when the compare node itself failed - and then the matching
    # branch is skipped below rather than leaking in.
    s1 = _style_is_int(tree, bx - 400, by - 3080, 1, style)
    s2 = _style_is_int(tree, bx - 400, by - 3160, 2, style)
    s3 = _style_is_int(tree, bx - 400, by - 3240, 3, style)

    # --- shared band template ------------------------------------------------
    # A ring of four thin slabs, one per face, rather than one full box: that
    # keeps the corners reading as solid concrete, which is the brutalist
    # signature. A full-width slab reads as a glass box, not a concrete building.
    ring = N(tree, 'GeometryNodeJoinGeometry', bx + 2200, by - 3400)
    for yy in (by - 3560, by - 3700):          # front / back faces
        piece = cube_s(tree, bx + 900, yy, 1.0, p["reveal"], p["band_h"])
        L(tree, piece, out_name(piece, 'Mesh', 'Geometry'), ring, 'Geometry')
    for xx in (bx + 1000, bx + 1120):          # left / right faces
        piece = cube_s(tree, xx, by - 3560, p["reveal"], 1.0, p["band_h"])
        L(tree, piece, out_name(piece, 'Mesh', 'Geometry'), ring, 'Geometry')

    band_node = ring
    if hp is not None:
        # `Inset Face` deepens the band so it reads as a reveal rather than a
        # decal. Verified socket contract: IN [Mesh, Offset, Depth, Individual,
        # Reletive Offset, Selection] -> OUT [Geometry, Inner, Outer].
        try:
            n, _used = hp.stage(tree, "Inset Face", bx + 2400, by - 3400,
                                geometry_in=ring,
                                inputs={"Depth": p["reveal"] * 0.5})
            if n is not None:
                band_node = n
        except Exception:
            pass

    # --- floor stack: one band per floor ------------------------------------
    line = gn_line(tree, p["seed"], bx + 900, by - 4000, p["floors"],
                   combine(tree, bx + 700, by - 4100, 0.0, 0.0, 0.0),
                   combine(tree, bx + 700, by - 4200, 0.0, 0.0, 0.0))
    stack = inst_realize(tree, bx + 2700, by - 4000, line, band_node,
                         sname=out_name(band_node, 'Mesh', 'Geometry'))

    # --- Punched windows on a bay grid (style 2) --------------------------------
    # Discrete windows, one per bay per floor, on a per-face grid. The grid
    # counts are SOCKET-DRIVEN: facade width / Window Bay, clamped >= 1, so
    # the health probe's bay 0.6->6.0 sweep changes the actual window COUNT.
    # The grid lives OUTSIDE the style gate (unlinked); style 2 picks it via
    # SWITCH. Selection is per-window (modulo of point index), never a face
    # count.
    #
    # Layout: TWO MeshLines (facade axis x floor axis), native-instance a
    # window template cube, realize, translate into place. Realizing BEFORE
    # translating means each instance can be offset individually.
    punched_node = None
    try:
        # Facade span is the lot minus setback - reuse the mw/md socket chain.
        # Bay count = max(1, round(span / Window Bay)), a NodeSocketInt that
        # gn_line can consume directly as its count.
        n_bays_x = N(tree, 'ShaderNodeMath', bx + 400, by - 3200)
        n_bays_z = N(tree, 'ShaderNodeMath', bx + 400, by - 3350)

        def _fsock(v):
            # Group-input sockets pass through; builder nodes resolve to
            # outputs[0]. link_sockets needs SOCKETS - passing a NODE fails
            # links.new with "expected a NodeSocket, not ShaderNodeMath"
            # (red baseline 2026-09-30: Math.011/Math.013 -> Value).
            return v.outputs[0] if hasattr(v, 'outputs') else v

        try:
            n_bays_x.operation = 'DIVIDE'
            link_sockets(tree, _fsock(p["mw"]), n_bays_x.inputs[0])
            link_sockets(tree, _fsock(p["bay"]), n_bays_x.inputs[1])
        except Exception:
            pass
        try:
            n_bays_z.operation = 'DIVIDE'
            link_sockets(tree, _fsock(p["md"]), n_bays_z.inputs[0])
            link_sockets(tree, _fsock(p["bay"]), n_bays_z.inputs[1])
        except Exception:
            pass
        n_bays_x_r = N(tree, 'ShaderNodeMath', bx + 550, by - 3200)
        n_bays_z_r = N(tree, 'ShaderNodeMath', bx + 550, by - 3350)
        try:
            n_bays_x_r.operation = 'ROUND'
            link_sockets(tree, n_bays_x.outputs[0], n_bays_x_r.inputs[0])
        except Exception:
            pass
        try:
            n_bays_z_r.operation = 'ROUND'
            link_sockets(tree, n_bays_z.outputs[0], n_bays_z_r.inputs[0])
        except Exception:
            pass
        # Clamp to >= 1 via MAXIMUM (a bay wider than the building still
        # yields exactly one window per floor, never an empty grid).
        n_bays_x_c = N(tree, 'ShaderNodeMath', bx + 700, by - 3200)
        n_bays_z_c = N(tree, 'ShaderNodeMath', bx + 700, by - 3350)
        try:
            n_bays_x_c.operation = 'MAXIMUM'
            link_sockets(tree, n_bays_x_r.outputs[0], n_bays_x_c.inputs[0])
            n_bays_x_c.inputs[1].default_value = 1.0
        except Exception:
            pass
        try:
            n_bays_z_c.operation = 'MAXIMUM'
            link_sockets(tree, n_bays_z_r.outputs[0], n_bays_z_c.inputs[0])
            n_bays_z_c.inputs[1].default_value = 1.0
        except Exception:
            pass
        # One window template: the inset glass piece (reveal x band section).
        punch_tpl = cube_s(tree, bx + 900, by - 3200, p["reveal"],
                           p["band_h"], p["band_h"])
        # Front/back faces carry the X grid; side faces carry the Z grid. The
        # two grids have DIFFERENT counts, so build and join them separately -
        # one MeshLine cannot carry two counts on two axes.
        fb_line = gn_line(tree, p["seed"], bx + 1100, by - 3200,
                          n_bays_x_c.outputs[0],
                          combine(tree, bx + 950, by - 3050, 0.0, 0.0, 0.0),
                          combine(tree, bx + 950, by - 2950, p["bay"], 0.0, 0.0))
        side_line = gn_line(tree, p["seed"], bx + 1100, by - 3350,
                            n_bays_z_c.outputs[0],
                            combine(tree, bx + 950, by - 3200, 0.0, 0.0, 0.0),
                            combine(tree, bx + 950, by - 3100, 0.0, p["bay"],
                                    0.0))
        # Floors line shared by both grids: Z-start at one floor height so the
        # punch grid aligns with the ribbon bands, offset = band pitch.
        floor_h = mathn(tree, 'DIVIDE', bx + 950, by - 2850,
                        p["hmax"] if "hmax" in p else 34.0, p["floors"])
        punch_floors = gn_line(
            tree, p["seed"], bx + 1100, by - 3500, p["floors"],
            combine(tree, bx + 950, by - 3650, 0.0, 0.0,
                    floor_h.outputs[0]),
            combine(tree, bx + 950, by - 3750, 0.0, 0.0,
                    floor_h.outputs[0]))
        fb_grid = inst_realize(tree, bx + 1500, by - 3200, fb_line,
                               punch_tpl,
                               sname=out_name(punch_tpl, 'Mesh', 'Geometry'))
        side_grid = inst_realize(tree, bx + 1500, by - 3350, side_line,
                                 punch_tpl,
                                 sname=out_name(punch_tpl, 'Mesh', 'Geometry'))
        fb_stack = inst_realize(tree, bx + 1900, by - 3200, punch_floors,
                                fb_grid, sname='Geometry')
        side_stack = inst_realize(tree, bx + 1900, by - 3350, punch_floors,
                                  side_grid, sname='Geometry')
        punched_join = N(tree, 'GeometryNodeJoinGeometry', bx + 2200,
                         by - 3275)
        for node in (fb_stack, side_stack):
            try:
                L(tree, node, out_name(node, 'Geometry', 'Mesh'),
                  punched_join, 'Geometry')
            except Exception:
                pass
        punched_node = punched_join
    except Exception:
        punched_node = None


    # --- Colonnade fins (style 3) ---------------------------------------------
    # Built NATIVELY, not via Higgsas, on purpose: a fin is a box, and no Higgsas
    # group does it better. Wiring one in here would be decoration dressed as
    # integration - the thing this project keeps catching.
    #
    # Fin Count is a FLOAT param socket, so it is ROUNDed before it drives a
    # MeshLine Count. Spacing comes from Window Bay - the same dial the Punched
    # grid uses - so one control sets the rhythm of both styles.
    #
    # Without this block style 3 gated the SAME band stack as style 1, which made
    # Ribbon and Colonnade the identical mesh and left Fin Count reading nothing.
    fins_node = None
    try:
        n_fin = N(tree, 'ShaderNodeMath', bx + 400, by - 4700)
        n_fin.operation = 'ROUND'
        link_sockets(tree, _fsock(p["fin_count"]), n_fin.inputs[0])

        fin_tpl = cube_s(tree, bx + 900, by - 4700, p["fin_depth"], 1.0, 1.0)
        fin_line = gn_line(tree, p["seed"], bx + 1100, by - 4700,
                           n_fin.outputs[0],
                           combine(tree, bx + 950, by - 4820, 0.0, 0.0, 0.0),
                           combine(tree, bx + 950, by - 4720, p["bay"], 0.0,
                                   0.0))
        fins_node = inst_realize(tree, bx + 1500, by - 4700, fin_line,
                                 fin_tpl,
                                 sname=out_name(fin_tpl, 'Mesh', 'Geometry'))
    except Exception:
        fins_node = None

    # --- assemble, per-style, then gate --------------------------------------
    # Each live style gates ITSELF on s1/s2/s3 (the roofs pattern): Ribbon
    # keeps the band stack, Punched keeps the bay grid, Colonnade keeps the
    # band stack plus fins. Routing all three through one ungated join is the
    # defect this replaces - it made styles 1/2/3 the identical mesh.
    join = N(tree, 'GeometryNodeJoinGeometry', bx + 3000, by - 3600)
    if s1 is not None:
        try:
            ribbon_g = guard_off(tree, bx + 2800, by - 4000, s1, stack,
                                 sname='Geometry')
            L(tree, ribbon_g, out_name(ribbon_g, 'Geometry', 'Mesh'),
              join, 'Geometry')
        except Exception:
            pass
    if s2 is not None and punched_node is not None:
        try:
            punched_g = guard_off(tree, bx + 2800, by - 3275, s2,
                                  punched_node, sname='Geometry')
            L(tree, punched_g, out_name(punched_g, 'Geometry', 'Mesh'),
              join, 'Geometry')
        except Exception:
            pass
    if s3 is not None:
        try:
            slot_join = N(tree, 'GeometryNodeJoinGeometry', bx + 2600, by - 4150)
            # Colonnade = slot windows (the band stack) PLUS the fins. Gating
            # only the band stack made style 3 byte-identical to style 1 and
            # left Fin Count reading nothing.
            L(tree, stack, out_name(stack, 'Geometry', 'Mesh'), slot_join,
              'Geometry')
            if fins_node is not None:
                L(tree, fins_node, out_name(fins_node, 'Geometry', 'Mesh'),
                  slot_join, 'Geometry')
            slot_g = guard_off(tree, bx + 2800, by - 4100, s3, slot_join,
                               sname='Geometry')
            L(tree, slot_g, out_name(slot_g, 'Geometry', 'Mesh'),
              join, 'Geometry')
        except Exception:
            pass

    out = guard_off(tree, bx + 3300, by - 3600, has_facade.outputs[0], join,
                    sname='Geometry')

    if p.get("glass") is not None:
        sm = safe_node(tree, 'GeometryNodeSetMaterial', (bx + 3600, by - 3600))
        if sm is not None:
            try:
                L(tree, out, out_name(out, 'Geometry', 'Mesh'), sm, 'Geometry')
                link_sockets(tree, p["glass"], sm.inputs.get('Material'))
                out = sm
            except Exception:
                pass
    return out



def build_brutalist_city_block(group_name="GN_BRUTALIST_CityBlock"):
    tree, gin, gout = new_geometry_tree(group_name)

    # ---- dials -------------------------------------------------------------
    BLOCKSX = add_int_param(tree, "Blocks X", 3, 1, 6)
    BLOCKSY = add_int_param(tree, "Blocks Y", 3, 1, 6)
    LW = add_float_param(tree, "Lot Width", 14.0, 8.0, 30.0)
    LD = add_float_param(tree, "Lot Depth", 14.0, 8.0, 30.0)
    SW = add_float_param(tree, "Street Width", 8.0, 4.0, 24.0)
    SB = add_float_param(tree, "Setback", 1.5, 0.0, 6.0)
    HMIN = add_float_param(tree, "Height Min", 12.0, 4.0, 40.0)
    HMAX = add_float_param(tree, "Height Max", 34.0, 8.0, 90.0)
    SEED = add_int_param(tree, "Seed", 7, 0, 9999)
    GROUND = add_bool_param(tree, "Ground", True)
    ROADS = add_bool_param(tree, "Roads", True)
    WALKS = add_bool_param(tree, "Sidewalks", True)
    PARAPET = add_bool_param(tree, "Parapet", True)
    PIERS = add_bool_param(tree, "Piers", True)

    # ---- material inputs ----------------------------------------------------
    # Added 2026-09-25 after the topology audit measured mats=1 on every preset:
    # one mesh, one material, so asphalt roads and concrete massing cannot differ
    # inside a single object. The stager works around this today by building a
    # separate object per surface, which multiplies objects and breaks any
    # per-building selection.
    #
    # Both default to None. An unset Material input sets nothing on any face, so
    # the evaluated mesh is IDENTICAL to before when a caller leaves them alone -
    # proven by Saved/Audit/_diag_material_slots.py, which asserts BOTH vertex
    # count and slot count are unchanged with the inputs empty.
    MAT_MASS = add_material_param(tree, "Massing Material")
    MAT_GROUND = add_material_param(tree, "Ground Material")
    MAT_GLASS = add_material_param(tree, "Glazing Material")

    # ---- facade + window dials ---------------------------------------------
    # The topology audit found the city builder had NO window geometry at all
    # (zero matches for glass/glaz/window) while the office builder already had
    # recessed glass per floor. A 90 m tower of blank slab does not read as a
    # building, so this closes that gap.
    #
    # Facade Style is the architectural-variation knob:
    #   0 Blank     - no fenestration (DEFAULT: every pre-existing preset is
    #                 unchanged, which is what lets this ship without re-cutting
    #                 the contact sheets)
    #   1 Ribbon    - continuous horizontal glazing band per floor
    #   2 Punched   - discrete windows on a per-floor grid
    #   3 Colonnade - deep vertical fins + slot windows
    FACADE = add_int_param(tree, "Facade Style", 0, 0, 3)
    FLOORS = add_int_param(tree, "Window Floors", 8, 1, 40)
    BAYSP = add_float_param(tree, "Window Bay", 2.4, 0.6, 6.0)
    BANDH = add_float_param(tree, "Window Band Height", 1.4, 0.2, 3.0)
    WREV = add_float_param(tree, "Window Reveal", 0.28, 0.02, 1.2)
    FINDEPTH = add_float_param(tree, "Fin Depth", 0.5, 0.05, 2.0)
    FINT = add_float_param(tree, "Fin Count", 6, 0, 40)

    bx, by = -3000, 0
    g = gin.outputs

    # ---- derived layout ----------------------------------------------------
    pitch_x = mathn(tree, 'ADD', bx, by - 100, LW, SW)
    pitch_y = mathn(tree, 'ADD', bx, by - 300, LD, SW)
    w_tot = mathn(tree, 'MULTIPLY', bx, by - 500, pitch_x.outputs[0],
                  g['Blocks X'])
    d_tot = mathn(tree, 'MULTIPLY', bx, by - 700, pitch_y.outputs[0],
                  g['Blocks Y'])
    half_w = mathn(tree, 'MULTIPLY', bx, by - 900, w_tot.outputs[0], -0.5)
    half_d = mathn(tree, 'MULTIPLY', bx, by - 1100, d_tot.outputs[0], -0.5)
    # first lot centre: block centre + half a lot
    cell0_x = mathn(tree, 'ADD', bx, by - 1300, half_w.outputs[0],
                    mathn(tree, 'MULTIPLY', bx - 200, by - 1300, LW,
                          0.5).outputs[0])
    cell0_y = mathn(tree, 'ADD', bx, by - 1500, half_d.outputs[0],
                    mathn(tree, 'MULTIPLY', bx - 200, by - 1500, LD,
                          0.5).outputs[0])
    # massing footprint = lot inset by Setback
    mw = mathn(tree, 'SUBTRACT', bx, by - 1700, LW,
               mathn(tree, 'MULTIPLY', bx - 200, by - 1700, SB, 2.0).outputs[0])
    md = mathn(tree, 'SUBTRACT', bx, by - 1900, LD,
               mathn(tree, 'MULTIPLY', bx - 200, by - 1900, SB, 2.0).outputs[0])
    n_road_x = mathn(tree, 'ADD', bx, by - 2100, g['Blocks X'], 1)
    n_road_y = mathn(tree, 'ADD', bx, by - 2300, g['Blocks Y'], 1)
    # road strip start sits half a street outside the first lot edge
    road_x0 = mathn(tree, 'SUBTRACT', bx, by - 2500, cell0_x.outputs[0],
                    mathn(tree, 'MULTIPLY', bx - 200, by - 2500, LW,
                          0.5).outputs[0])
    road_y0 = mathn(tree, 'SUBTRACT', bx, by - 2700, cell0_y.outputs[0],
                    mathn(tree, 'MULTIPLY', bx - 200, by - 2700, LD,
                          0.5).outputs[0])

    parts = []

    # ---- lot grid: one 2D point cloud from two MeshLines --------------------
    # rows carry a col-line whose VERTICES land on every lot centre, so the
    # realized grid is exactly Blocks X * Blocks Y points, each with its own
    # instance index - which is what makes the per-lot height below vary.
    col_line = gn_line(tree, gin, bx + 600, by - 3200, 'Blocks X',
                       combine(tree, bx + 450, by - 3350, cell0_x.outputs[0],
                               0.0, 0.0),
                       combine(tree, bx + 450, by - 3500, pitch_x.outputs[0],
                               0.0, 0.0))
    row_line = gn_line(tree, gin, bx + 600, by - 3700, 'Blocks Y',
                       combine(tree, bx + 450, by - 3850, 0.0,
                               cell0_y.outputs[0], 0.0),
                       combine(tree, bx + 450, by - 4000, 0.0,
                               pitch_y.outputs[0], 0.0))
    grid = inst_realize(tree, bx + 1000, by - 3500, row_line, col_line,
                        sname='Mesh')

    # ---- massing template: unit height, base at z=0 (so Z-scale == height) --
    core = cube_s(tree, bx + 600, by - 4400, mw.outputs[0], md.outputs[0], 1.0)
    core_tr = xform(tree, bx + 850, by - 4400, core,
                    sname=out_name(core, 'Mesh', 'Geometry'),
                    trans=combine(tree, bx + 700, by - 4550, 0.0, 0.0, 0.5))

    # four FULL-HEIGHT corner piers: X/Y size is unscaled, Z stretches to height,
    # so the brutalist pier read survives the per-lot Z scale.
    p = mathn(tree, 'MULTIPLY', bx, by - 4700, SB, 0.6)
    p_in = mathn(tree, 'SUBTRACT', bx, by - 4900, mw.outputs[0],
                 mathn(tree, 'MULTIPLY', bx - 200, by - 4900, p.outputs[0],
                       0.5).outputs[0])
    p_id = mathn(tree, 'SUBTRACT', bx, by - 5100, md.outputs[0],
                 mathn(tree, 'MULTIPLY', bx - 200, by - 5100, p.outputs[0],
                       0.5).outputs[0])
    p_join = N(tree, 'GeometryNodeJoinGeometry', bx + 1800, by - 4700)
    for ix, sx in ((0, -1.0), (1, 1.0)):
        for iy, sy in ((0, -1.0), (1, 1.0)):
            pier = cube_s(tree, bx + 600, by - 5300 - ix * 200 - iy * 60,
                          p.outputs[0], p.outputs[0], 1.0)
            pier_tr = xform(
                tree, bx + 850, by - 5300 - ix * 200 - iy * 60, pier,
                sname=out_name(pier, 'Mesh', 'Geometry'),
                trans=combine(
                    tree, bx + 700, by - 5450 - ix * 200 - iy * 60,
                    mathn(tree, 'MULTIPLY', bx + 300, by - 5450 - ix * 200 - iy * 60,
                          p_in.outputs[0], sx).outputs[0],
                    mathn(tree, 'MULTIPLY', bx + 300, by - 5550 - ix * 200 - iy * 60,
                          p_id.outputs[0], sy).outputs[0],
                    0.5))
            L(tree, pier_tr, out_name(pier_tr, 'Geometry', 'Mesh'),
              p_join, 'Geometry')
    piers_g = guard_off(tree, bx + 2000, by - 4700, PIERS, p_join,
                        sname='Geometry')

    # parapet band sits at the TOP of the unit-height template (z 0.97..1.0) so the
    # Z-scale puts it on the roof without a second per-lot translate pass.
    par_w = mathn(tree, 'ADD', bx, by - 6100, mw.outputs[0],
                  mathn(tree, 'MULTIPLY', bx - 200, by - 6100, p.outputs[0],
                        2.0).outputs[0])
    par_d = mathn(tree, 'ADD', bx, by - 6300, md.outputs[0],
                  mathn(tree, 'MULTIPLY', bx - 200, by - 6300, p.outputs[0],
                        2.0).outputs[0])
    par = cube_s(tree, bx + 600, by - 6600, par_w.outputs[0], par_d.outputs[0], 0.03)
    par_tr = xform(tree, bx + 850, by - 6600, par,
                   sname=out_name(par, 'Mesh', 'Geometry'),
                   trans=combine(tree, bx + 700, by - 6750, 0.0, 0.0, 0.985))
    par_g = guard_off(tree, bx + 1100, by - 6600, PARAPET, par_tr,
                      sname='Geometry')

    bld_tpl = N(tree, 'GeometryNodeJoinGeometry', bx + 2300, by - 4400)
    for node in (core_tr, piers_g, par_g):
        L(tree, node, out_name(node, 'Geometry', 'Mesh'), bld_tpl, 'Geometry')

    # ---- per-lot height: random in [Hmin, Hmax], seeded ---------------------
    rv = N(tree, 'FunctionNodeRandomValue', bx + 2600, by - 4400)
    try:
        rv.data_type = 'FLOAT'
    except Exception:
        pass
    _rv_float_bounds(rv, 0.0, 1.0)
    rv_min, rv_max = _rv_float_socket(rv, 'Min'), _rv_float_socket(rv, 'Max')
    if rv_min is not None:
        link_sockets(tree, g['Height Min'], rv_min)
    if rv_max is not None:
        link_sockets(tree, g['Height Max'], rv_max)
    L(tree, gin, 'Seed', rv, 'Seed')
    # scale X/Y stay 1: only Z is the per-lot height
    zscale = combine(tree, bx + 2800, by - 4400, 1.0, 1.0, 0.0)
    L(tree, rv, 0, zscale, 'Z')
    bld_real = inst_realize(tree, bx + 3100, by - 4400, grid, bld_tpl,
                            sname='Geometry', scale=zscale)
    # massing takes the concrete slot; unset input leaves faces on slot 0
    if MAT_MASS is not None:
        sm = safe_node(tree, 'GeometryNodeSetMaterial', (bx + 3300, by - 4400))
        if sm is not None:
            try:
                L(tree, bld_real, out_name(bld_real, 'Geometry', 'Mesh'),
                  sm, 'Geometry')
                link_sockets(tree, MAT_MASS, sm.inputs.get('Material'))
                bld_real = sm
            except Exception:
                pass
    parts.append(bld_real)

    # ---- facade: windows + fins, per realised massing -----------------------
    # ATTACHED HERE, AFTER inst_realize, and that placement is load-bearing: the
    # massing template is a UNIT-HEIGHT box Z-scaled per lot (see zscale above),
    # so anything built inside `bld_tpl` would be stretched vertically with the
    # building. Working on the realised mesh means one facade definition serves
    # every lot regardless of its random height.
    #
    # Glazing goes to its own material slot so a whole city can be one object
    # with concrete + asphalt + glass. Left unset it is a no-op (slot 0).
    facade = _build_facade(tree, bx, by, g, {
        "style": FACADE, "floors": FLOORS, "bay": BAYSP, "band_h": BANDH,
        "reveal": WREV, "fin_depth": FINDEPTH, "fin_count": FINT,
        "mw": mw, "md": md, "seed": gin, "hmin": g['Height Min'],
        "hmax": g['Height Max'], "glass": MAT_GLASS,
    })
    if facade is not None:
        parts.append(facade)

    # ---- sidewalk slabs: same lot grid, no Z scale ------------------------
    slab = cube_s(tree, bx + 600, by - 7100, LW, LD, 0.10)
    slab_tr = xform(tree, bx + 850, by - 7100, slab,
                    sname=out_name(slab, 'Mesh', 'Geometry'),
                    trans=combine(tree, bx + 700, by - 7250, 0.0, 0.0, 0.05))
    walk_real = inst_realize(tree, bx + 1100, by - 7100, grid, slab_tr,
                             sname='Geometry')
    parts.append(guard_off(tree, bx + 1400, by - 7100, WALKS, walk_real,
                           sname='Geometry'))

    # ---- roads: Blocks+1 strips per axis, so 'Roads off' deletes them all ---
    road_d = mathn(tree, 'ADD', bx, by - 7500, d_tot.outputs[0], SW)
    road_w = mathn(tree, 'ADD', bx, by - 7700, w_tot.outputs[0], SW)
    vroad_t = cube_s(tree, bx + 600, by - 8000, SW, road_d.outputs[0], 0.06)
    vroad_tr = xform(tree, bx + 850, by - 8000, vroad_t,
                     sname=out_name(vroad_t, 'Mesh', 'Geometry'),
                     trans=combine(tree, bx + 700, by - 8150, 0.0, 0.0, 0.03))
    vroad_line = gn_line(tree, gin, bx + 600, by - 8400, n_road_x,
                         combine(tree, bx + 450, by - 8550,
                                 road_x0.outputs[0], 0.0, 0.0),
                         combine(tree, bx + 450, by - 8700,
                                 pitch_x.outputs[0], 0.0, 0.0))
    vroad = inst_realize(tree, bx + 1100, by - 8400, vroad_line, vroad_tr,
                         sname='Geometry')

    hroad_t = cube_s(tree, bx + 600, by - 9000, road_w.outputs[0], SW, 0.06)
    hroad_tr = xform(tree, bx + 850, by - 9000, hroad_t,
                     sname=out_name(hroad_t, 'Mesh', 'Geometry'),
                     trans=combine(tree, bx + 700, by - 9150, 0.0, 0.0, 0.03))
    hroad_line = gn_line(tree, gin, bx + 600, by - 9400, n_road_y,
                         combine(tree, bx + 450, by - 9550, 0.0,
                                 road_y0.outputs[0], 0.0),
                         combine(tree, bx + 450, by - 9700, 0.0,
                                 pitch_y.outputs[0], 0.0))
    hroad = inst_realize(tree, bx + 1100, by - 9400, hroad_line, hroad_tr,
                         sname='Geometry')

    road_join = N(tree, 'GeometryNodeJoinGeometry', bx + 1600, by - 8700)
    for node in (vroad, hroad):
        L(tree, node, out_name(node, 'Geometry', 'Mesh'), road_join, 'Geometry')
    parts.append(guard_off(tree, bx + 1900, by - 8700, ROADS, road_join,
                           sname='Geometry'))

    # ---- per-surface material assignment ------------------------------------
    # The topology audit measured mats=1 on every preset: one mesh, one material,
    # so asphalt roads and concrete massing could not differ inside one object.
    # These two Set Material nodes give that back, driven by the group inputs.
    #
    # Applied ONLY to the part lists that exist, and a None material leaves faces
    # on slot 0 - so with both inputs unset the evaluated mesh is unchanged, which
    # Saved/Audit/_diag_material_slots.py asserts by vertex count AND slot count.
    def _set_mat(node, mat_socket, x, y):
        sm = safe_node(tree, 'GeometryNodeSetMaterial', (x, y))
        if sm is None:
            return node
        try:
            L(tree, node, out_name(node, 'Geometry', 'Mesh'), sm, 'Geometry')
            link_sockets(tree, mat_socket, sm.inputs.get('Material'))
        except Exception:
            return node
        return sm

    # roads take the ground/asphalt slot
    if MAT_GROUND is not None:
        road_g = parts[-1]
        parts[-1] = _set_mat(road_g, MAT_GROUND, bx + 2100, by - 8700)

    # ---- ground slab (top face at z=0) -------------------------------------
    gw = mathn(tree, 'ADD', bx, by - 10000, w_tot.outputs[0],
               mathn(tree, 'MULTIPLY', bx - 200, by - 10000, SW, 3.0).outputs[0])
    gd = mathn(tree, 'ADD', bx, by - 10200, d_tot.outputs[0],
               mathn(tree, 'MULTIPLY', bx - 200, by - 10200, SW, 3.0).outputs[0])
    ground = cube_s(tree, bx + 600, by - 10500, gw.outputs[0], gd.outputs[0], 0.4)
    ground_tr = xform(tree, bx + 850, by - 10500, ground,
                      sname=out_name(ground, 'Mesh', 'Geometry'),
                      trans=combine(tree, bx + 700, by - 10650, 0.0, 0.0, -0.2))
    parts.append(guard_off(tree, bx + 1100, by - 10500, GROUND, ground_tr,
                           sname='Geometry'))

    # ---- join all ----------------------------------------------------------
    out = N(tree, 'GeometryNodeJoinGeometry', bx + 2400, by - 4000)
    for node in parts:
        L(tree, node, out_name(node, 'Geometry', 'Mesh'), out, 'Geometry')
    # UV CHANNEL (added 2026-09-27). This supersedes the "no UV stage here,
    # deliberately" note that stood here before. That note correctly ruled out
    # two routes but drew the wrong conclusion from them:
    #
    #   - `GeometryNodeUVCubeProjection` really is unregistered in 5.2, and
    #     `GeometryNodeUVUnwrap` really has no geometry socket (inputs are
    #     [Selection, Seam, Margin, Fill Holes, Method, Iterations, No Flip],
    #     and it acts on the ACTIVE OBJECT - same constraint as eyewear.py:111).
    #   - Both of those are PROJECTION OPERATORS. Neither is required to
    #     produce a UV channel. A UV is just a CORNER-domain FLOAT2 named
    #     attribute called "UVMap", which is exactly what the image texture
    #     nodes read. `GeometryNodeStoreNamedAttribute` (domain=CORNER,
    #     data_type=FLOAT2) writes it from inside the group, with no active
    #     object, so the dials stay live.
    #
    # Verified in 5.2.1 before writing this: the node exists, takes Geometry,
    # and accepts both enum values.
    #
    # Box projection by dominant normal axis, not a flat XY unwrap: these are
    # orthogonal slabs, walls and floors, so per-face axis selection gives
    # square texels with no stretch and no seam guessing.
    from . import brutalist_uv as _buv
    if _buv.add_box_uv(tree, out.outputs[0], gout) is None:
        L(tree, out, 'Geometry', gout, 'Geometry')

    return tree, gin, gout


try:
    from .core import register_builder
    register_builder(
        "GN_BRUTALIST_CityBlock", build_brutalist_city_block,
        "BRUTALIST City Block",
        "2D city grid: lot grid with streets and sidewalks, per-lot random "
        "height between Height Min/Max, full-height corner piers, parapet band.",
        category='city_gen',
    )
    print('[brutalist_city] registered GN_BRUTALIST_CityBlock')
except ImportError:
    print('[brutalist_city] standalone mode (no core registry)')


if __name__ == '__main__':
    build_brutalist_city_block()


