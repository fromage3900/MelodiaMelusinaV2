"""P4 wave 13 — small hand percussion lane: maracas, wood block, cowbell,
castanets, shaker, vibraslap.

Gap audit first (repo-wide grep over `deploy/surreal_arch/` + the live registry +
`Tools/registry_baseline.json`, 2026-10-04): the percussion lane owns timpani,
snare drum, bass drum, cymbals, tambourine, carillon, steelpan, gong, ocarina,
glockenspiel, celesta, marimba, vibraphone, tubular bells, wave 10's six hand
drums (djembe, congas, bongos, cajon, frame drum, tabla) and wave 11's six
auxiliary pieces (tom-tom, xylophone, washboard, claves, cabasa, guiro). NONE of
the six ids below existed anywhere (grep count 0 each, 0 in the baseline):

    maracas, wood block, cowbell, castanets, shaker, vibraslap

Each of the six is distinct from its closest existing neighbour by its OWN
anatomy, not by a parameter:

    MEL_music_maracas   vs MEL_music_cabasa    a gourd HEAD on a separate handle,
                                               as a PAIR of identical rattles;
                                               the cabasa is a bead-wrapped
                                               cylinder on a handle, single
    MEL_music_wood_block vs MEL_music_claves   a hollow SLOTTED block (two proud
                                               slot rails straddling a groove);
                                               the claves are two solid rods
    MEL_music_cowbell   vs MEL_music_church_bell a 4-SIDED tapered steel shell
                                               with a mounting loop; the church
                                               bell is a round revolved cup
    MEL_music_castanets vs MEL_music_tambourine two shallow SHELLS on a cord;
                                               the tambourine is a wide open ring
                                               with a jingle rank
    MEL_music_shaker    vs MEL_music_maracas   a plain CLOSED ridged tube with no
                                               handle at all
    MEL_music_vibraslap vs MEL_music_ratchet   a toothed box on a BENT rod ending
                                               in a wooden ball (not written yet,
                                               and still a different machine)

Design rules (same as music_wind_solo / music_aux_percussion /
music_world_percussion):
  - Native-only. These are revolved shells, plates, rods and bead rings that 5.2
    primitives express exactly; a Higgsas subtree here would be decoration, not a
    lead. Every builder still stores `higgsas_lead` (1.0 = native) so the family
    gate and the instruments gate read the lane uniformly.
  - The wave-6/wave-10/wave-11 origin-explicit helpers are REUSED, never
    re-authored: `_cone_x` / `_cone_z` take the BASE (`MeshCone`'s origin is its
    base), `_cyl_x` / `_cyl_z` take the CENTRE, `_shell_z` / `_disc_z` /
    `_ring_rank` / `_tube_y` come from the world-percussion lane, `_plate` links
    all three `Size` components, `_rank_inst` places a rank ONLY by its points,
    `_inst_rank` accepts either a node or a geometry socket as the proto.
  - Zero `MeshBoolean` in the lane: a cutter that touches the mesh's own boundary
    emits ZERO geometry with no error and no `link_failures` entry. Every slot,
    window and mouth is LAID ON, never cut.
  - A primitive `Size` component is never left at LITERAL ZERO (the
    castle-merlon zero-width-slab class).
  - A cone's tip radius is never 0: an NGON top cap at radius 0 is a degenerate
    face by construction.
  - Every lane builder sits ON the floor (realized min_z >= -0.01).

Lane-local law 1 — `_slot_rails`, a groove expressed as TWO proud rails. A wood
block's slot cannot be cut (the boolean class above), so it is authored as a pair
of rails standing on the body's top face, their INNER faces exactly `Slot Width M`
apart: the body's own top face becomes the slot floor. The placement is a factor
law (`|y| >= 0.5 x Slot Width M`), never a snapshot, so a dial change cannot
silently close the slot.

Lane-local law 2 — a rank of SHORT members must clear the member WIDTH, not just
the host: the vibraslap's teeth are sized from the rank PITCH
(`span/(count-1) x 0.55`), not from the count x a constant, so 9 teeth never
merge into one slab (the wave-10 tabla gatta defect).

Lane-local law 3 — a bent rod is built from PLATES with per-segment rotations,
placed at their own midpoints. A `Transform` rotates about its own origin, so a
segment authored at the origin and rotated + translated lands exactly on its own
run; a rod built from `_cyl_x` (which hard-codes a 90 deg Y rotation) could not
carry a per-segment tilt at all.

Builders:
    MEL_music_maracas    pair of gourd heads on handles, bead bands
    MEL_music_wood_block slotted hardwood block (two slot rails + body)
    MEL_music_cowbell    4-sided tapered shell + mouth rim + mounting loop
    MEL_music_castanets  two shallow shells on a cord with loops
    MEL_music_shaker     closed ridged tube with proud end bands
    MEL_music_vibraslap  toothed box + bent rod + wooden ball
"""

from __future__ import annotations

import math

from .core import (
    safe_node, link_sockets, label_tree, new_geometry_tree, add_float_param,
    add_int_param, add_bool_param, register_builder, sock,
)
from .music_harps_real import _math, _combine
from .music_higgsas_instruments import _cyl, _xf, _cone
from .music_string_kit import _finish
from .music_percussion_kit import _inst_rank
from .music_keyboard_kit import _m, _plate
from .music_wind_reed_brass import (
    _vec, _sphere, _cyl_x, _cyl_z, _join, _rank_inst, _rank_axis,
    _half_span, _count_minus_one,
)
from .music_world_percussion import _disc_z, _shell_z, _ring_rank, _tube_y


# ---------------------------------------------------------------------------
# Lane-local laws
# ---------------------------------------------------------------------------

def _open_ring_proto_z(tree, loc, r_sock, h_sock, verts=24):
    """An OPEN ring (fill NONE) CENTRED on its own origin — a rank proto.

    `_shell_z` seats a ring on a base; a rank member must be centred on its own
    instance origin instead, so this is the proto sibling. `MeshCylinder`'s
    origin is already its centre, so no Transform is needed.
    """
    prim = _cyl(tree, loc, r_sock, h_sock, vertices=verts, fill=1)
    if prim is None:
        return None
    return prim.outputs["Mesh"]


def _slot_rails(tree, loc, length_sock, slot_sock, rail_w_sock, rail_h_sock,
                top_z_sock):
    """Two proud rails straddling a groove on the top face at `top_z_sock`.

    Returns a list of geometry sockets. The inner faces sit at +/- `slot_sock/2`,
    so the clear groove width IS the dial and the body's top face is the floor.
    """
    bx, by = loc
    off = _m(tree, "ADD", (bx - 400, by - 200), _m(
        tree, "MULTIPLY", (bx - 600, by - 200), slot_sock, 0.5),
        _m(tree, "MULTIPLY", (bx - 600, by - 340), rail_w_sock, 0.5))
    cz = _m(tree, "ADD", (bx - 400, by - 480), top_z_sock,
            _m(tree, "MULTIPLY", (bx - 600, by - 480), rail_h_sock, 0.5))
    out = []
    for i, sx in enumerate((-1.0, 1.0)):
        y = _m(tree, "MULTIPLY", (bx - 400, by - 620 - i * 200), off, sx)
        out.append(_plate(
            tree, (bx, by - 620 - i * 200), length_sock, rail_w_sock,
            rail_h_sock,
            translation=_vec(tree, (bx - 200, by - 780 - i * 200), 0.0, y, cz)))
    return out


def _aux2_attrs(tree, loc):
    """The lane's shared attribute pair: a semitone tag + the native lead flag."""
    bx, by = loc
    sidx = safe_node(tree, "GeometryNodeInputIndex", (bx, by))
    smod = _m(tree, "MODULO", (bx, by - 140), sidx.outputs["Index"], 12.0)
    return [("drum_semitone_mod12", smod), ("higgsas_lead", 1.0)]


# ---------------------------------------------------------------------------
# MEL_music_maracas
# ---------------------------------------------------------------------------

def build_music_maracas(group_name="MEL_music_maracas"):
    """Maracas: a PAIR of gourd heads on handles with bead bands.

    The pair is the identity — `MEL_music_cabasa` is a single bead-wrapped
    cylinder, `MEL_music_shaker` has no handle at all. Both maracas are the same
    size (a matched pair), placed by a rank whose Count is a literal int 2.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_maracas"
    bx, by = 0, 0

    add_float_param(tree, "Handle Length M", 0.140, 0.060, 0.300)
    add_float_param(tree, "Head Diameter M", 0.076, 0.040, 0.140)
    add_float_param(tree, "Pair Gap M", 0.150, 0.080, 0.300)
    add_int_param(tree, "Bead Count", 10, 6, 20)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    HL = gin.outputs["Handle Length M"]
    HD = gin.outputs["Head Diameter M"]
    GAP = gin.outputs["Pair Gap M"]

    head_r = _m(tree, "MULTIPLY", (bx - 2200, by + 300), HD, 0.5)
    handle_r = _m(tree, "MULTIPLY", (bx - 2200, by + 140), HD, 0.085)
    head_cz = _m(tree, "ADD", (bx - 2200, by - 20), HL,
                 _m(tree, "MULTIPLY", (bx - 2400, by - 20), head_r, 0.85))
    bead_r = _m(tree, "MULTIPLY", (bx - 2200, by - 180), handle_r, 0.55)
    band_r = _m(tree, "MULTIPLY", (bx - 2200, by - 340), handle_r, 1.55)
    band_z = _m(tree, "MULTIPLY", (bx - 2200, by - 500), HL, 0.55)

    handle = _cyl_z(tree, (bx - 1400, by), handle_r, HL,
                    _m(tree, "MULTIPLY", (bx - 2200, by - 660), HL, 0.5),
                    verts=16)
    egg = _sphere(tree, (bx - 1400, by - 800), 1.0, segments=32, rings=16)
    head = _xf(tree, (bx - 1200, by - 800), egg.outputs["Mesh"],
               scale=_vec(tree, (bx - 1600, by - 1000), head_r, head_r,
                          _m(tree, "MULTIPLY", (bx - 2200, by - 1000),
                             head_r, 1.15)),
               translation=_vec(tree, (bx - 1600, by - 1200), 0.0, 0.0,
                               head_cz)).outputs["Geometry"]
    bead = _sphere(tree, (bx - 1400, by - 1500), bead_r, segments=10, rings=6)
    band = _ring_rank(tree, (bx - 1400, by - 1700), gin.outputs["Bead Count"],
                      bead.outputs["Mesh"], band_r, cz=band_z)

    one = _join(tree, (bx + 400, by), [handle, head, band])
    # The pair is TWO explicit placements, not a rank: a builder whose ENTIRE
    # output is instances reads as 0 verts on an un-realized tree (gate D /
    # census), and a two-member pair is exactly the `_box_pair` idiom. The
    # opposed factors (-1.0 and +0.5 on `Pair Gap M`) are the asserted law.
    half_gap = _m(tree, "MULTIPLY", (bx - 2200, by - 2000), GAP, 0.5)
    pair = []
    for i, sx in enumerate((-1.0, 1.0)):
        x = _m(tree, "MULTIPLY", (bx - 2000, by - 2160 - i * 200), half_gap, sx)
        pair.append(_xf(tree, (bx + 600, by - 2160 - i * 200), one,
                        translation=_vec(tree, (bx + 600, by - 2320 - i * 200),
                                         x, 0.0, 0.0)).outputs["Geometry"])
    pair = _join(tree, (bx + 800, by), pair)
    _finish(tree, gin, gout, pair, (bx + 900, by), BID,
            _aux2_attrs(tree, (bx + 400, by - 2400)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Gourd Head + Handle", "nodes": ("UV Sphere", "Cylinder"),
         "role": "geometry"},
        {"title": "Bead Band", "nodes": ("Mesh Circle", "Instance on Points"),
         "role": "instance"},
        {"title": "Matched Pair", "nodes": ("Mesh Line", "Instance on Points"),
         "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_wood_block
# ---------------------------------------------------------------------------

def build_music_wood_block(group_name="MEL_music_wood_block"):
    """Wood block: a slotted hardwood block — two proud rails over a groove.

    The SLOT is the identity: it is authored as two rails whose inner faces are
    `Slot Width M` apart (the body's top face is the slot floor), because a
    boolean cutter on a boundary emits zero geometry silently. `MEL_music_claves`
    are two solid rods with no slot at all.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_wood_block"
    bx, by = 0, 0

    add_float_param(tree, "Body Length M", 0.205, 0.100, 0.400)
    add_float_param(tree, "Body Width M", 0.078, 0.040, 0.160)
    add_float_param(tree, "Body Height M", 0.066, 0.030, 0.140)
    add_float_param(tree, "Slot Width M", 0.015, 0.006, 0.040)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    L = gin.outputs["Body Length M"]
    W = gin.outputs["Body Width M"]
    H = gin.outputs["Body Height M"]
    SW = gin.outputs["Slot Width M"]

    body = _plate(tree, (bx - 1400, by), L, W, H,
                  translation=_vec(tree, (bx - 1600, by - 200), 0.0, 0.0,
                                   _m(tree, "MULTIPLY", (bx - 2200, by - 200),
                                      H, 0.5)))
    rail_h = _m(tree, "MULTIPLY", (bx - 2200, by - 600), H, 0.34)
    rail_w = _m(tree, "MULTIPLY", (bx - 2200, by - 760), SW, 0.34)
    rail_l = _m(tree, "MULTIPLY", (bx - 2200, by - 920), L, 0.78)
    rails = _slot_rails(tree, (bx - 1400, by - 1200), rail_l, SW, rail_w,
                        rail_h, H)

    geom = _join(tree, (bx + 400, by), [body] + rails)
    _finish(tree, gin, gout, geom, (bx + 700, by), BID,
            _aux2_attrs(tree, (bx + 400, by - 2600)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Block Body", "nodes": ("Cube",), "role": "geometry"},
        {"title": "Slot Rails", "nodes": ("Cube", "Transform"),
         "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_cowbell
# ---------------------------------------------------------------------------

def build_music_cowbell(group_name="MEL_music_cowbell"):
    """Cowbell: a 4-SIDED tapered steel shell, mouth rim, crown, mount loop.

    The square section is the identity — `MEL_music_church_bell` is a round
    revolved cup. The shell is an OPEN 4-vertex cone (mouth at z = 0, waist at the
    top) with a laid-on mouth rim and a crown plate; the mounting loop is an open
    tube standing in the XZ plane.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_cowbell"
    bx, by = 0, 0

    add_float_param(tree, "Body Height M", 0.155, 0.070, 0.300)
    add_float_param(tree, "Mouth Width M", 0.105, 0.050, 0.200)
    add_float_param(tree, "Waist Ratio", 0.50, 0.25, 0.80)
    add_float_param(tree, "Mount Loop Radius M", 0.014, 0.006, 0.030)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    H = gin.outputs["Body Height M"]
    MW = gin.outputs["Mouth Width M"]
    WR = gin.outputs["Waist Ratio"]
    LOOP = gin.outputs["Mount Loop Radius M"]

    mouth_r = _m(tree, "MULTIPLY", (bx - 2200, by + 300), MW, 0.5)
    waist_r = _m(tree, "MULTIPLY", (bx - 2200, by + 140), mouth_r, WR)
    rim_h = _m(tree, "MULTIPLY", (bx - 2200, by - 20), H, 0.05)
    crown_t = _m(tree, "MULTIPLY", (bx - 2200, by - 180), H, 0.05)
    crown_cz = _m(tree, "ADD", (bx - 2200, by - 340), H,
                  _m(tree, "MULTIPLY", (bx - 2400, by - 340), crown_t, 0.5))

    # the shell: an OPEN 4-vertex cone, BASE (the mouth) at z = 0
    prim = _cone(tree, (bx - 1400, by), mouth_r, waist_r, H, vertices=4, fill=1)
    shell = _xf(tree, (bx - 1200, by), prim.outputs["Mesh"],
                translation=_vec(tree, (bx - 1600, by - 200), 0.0, 0.0,
                                 0.0)).outputs["Geometry"]
    rim = _shell_z(tree, (bx - 1400, by - 600),
                   _m(tree, "MULTIPLY", (bx - 2200, by - 600), mouth_r, 1.06),
                   rim_h, 0.0, verts=4)
    crown = _plate(tree, (bx - 1400, by - 1000),
                   _m(tree, "MULTIPLY", (bx - 2200, by - 1000), waist_r, 2.0),
                   _m(tree, "MULTIPLY", (bx - 2200, by - 1160), waist_r, 2.0),
                   crown_t,
                   translation=_vec(tree, (bx - 1600, by - 1160), 0.0, 0.0,
                                   crown_cz))
    loop = _tube_y(tree, (bx - 1400, by - 1600), LOOP,
                   _m(tree, "MULTIPLY", (bx - 2200, by - 1600), LOOP, 0.55),
                   0.0, x=0.0, z=_m(tree, "MULTIPLY", (bx - 2200, by - 1760),
                                    H, 1.02), verts=20)

    geom = _join(tree, (bx + 400, by), [shell, rim, crown, loop])
    _finish(tree, gin, gout, geom, (bx + 700, by), BID,
            _aux2_attrs(tree, (bx + 400, by - 2200)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Square Shell", "nodes": ("Cone",), "role": "geometry"},
        {"title": "Mouth Rim + Crown", "nodes": ("Cylinder", "Cube"),
         "role": "geometry"},
        {"title": "Mount Loop", "nodes": ("Cylinder",), "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_castanets
# ---------------------------------------------------------------------------

def build_music_castanets(group_name="MEL_music_castanets"):
    """Castanets: two shallow SHELLS on a cord, each with a mounting loop.

    The pair of shallow domes is the identity — `MEL_music_tambourine` is a wide
    open ring with a jingle rank. Each shell is a UV sphere squashed on Z (the
    shell depth is its own dial), placed by a literal-2 rank, and the cord is a
    thin tube running between the two loops.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_castanets"
    bx, by = 0, 0

    add_float_param(tree, "Shell Diameter M", 0.058, 0.030, 0.120)
    add_float_param(tree, "Shell Depth M", 0.026, 0.012, 0.060)
    add_float_param(tree, "Cord Length M", 0.200, 0.100, 0.400)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    D = gin.outputs["Shell Diameter M"]
    SD = gin.outputs["Shell Depth M"]
    CL = gin.outputs["Cord Length M"]

    shell_r = _m(tree, "MULTIPLY", (bx - 2200, by + 300), D, 0.5)
    half_d = _m(tree, "MULTIPLY", (bx - 2200, by + 140), SD, 0.5)
    cord_r = _m(tree, "MULTIPLY", (bx - 2200, by - 20), shell_r, 0.10)
    cord_z = _m(tree, "MULTIPLY", (bx - 2200, by - 180), half_d, 1.50)
    loop_r = _m(tree, "MULTIPLY", (bx - 2200, by - 340), shell_r, 0.22)
    loop_z = _m(tree, "MULTIPLY", (bx - 2200, by - 500), half_d, 1.70)

    ball = _sphere(tree, (bx - 1400, by), 1.0, segments=32, rings=16)
    shell = _xf(tree, (bx - 1200, by), ball.outputs["Mesh"],
                scale=_vec(tree, (bx - 1600, by - 200), shell_r, shell_r,
                           half_d),
                translation=_vec(tree, (bx - 1600, by - 400), 0.0, 0.0,
                                 half_d)).outputs["Geometry"]
    pair = _rank_inst(tree, (bx - 800, by), 2, shell, CL,
                      _m(tree, "MULTIPLY", (bx - 2200, by - 600), CL, -0.5),
                      axis="x")

    cord = _cyl_x(tree, (bx - 1400, by - 1000), cord_r, CL, 0.0, z=cord_z,
                  verts=8)
    loop = _tube_y(tree, (bx - 1400, by - 1400), loop_r, loop_r, 0.0,
                   x=0.0, z=loop_z, verts=16)
    loops = _rank_inst(tree, (bx - 800, by - 1400), 2, loop, CL,
                       _m(tree, "MULTIPLY", (bx - 2200, by - 1600), CL, -0.5),
                       axis="x")

    geom = _join(tree, (bx + 400, by), [pair, cord, loops])
    _finish(tree, gin, gout, geom, (bx + 700, by), BID,
            _aux2_attrs(tree, (bx + 400, by - 2000)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Shell Proto", "nodes": ("UV Sphere", "Transform"),
         "role": "geometry"},
        {"title": "Shell Pair + Loops", "nodes": ("Mesh Line", "Instance on Points"),
         "role": "instance"},
        {"title": "Cord", "nodes": ("Cylinder",), "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_shaker
# ---------------------------------------------------------------------------

def build_music_shaker(group_name="MEL_music_shaker"):
    """Shaker: a plain CLOSED ridged tube with proud end bands.

    No handle and no head — that is what separates it from `MEL_music_maracas`.
    The ridges are a rank of open rings centred on their own origins, so the rank
    does all the placement (a proto carrying its own offset would double it).
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_shaker"
    bx, by = 0, 0

    add_float_param(tree, "Body Length M", 0.190, 0.080, 0.400)
    add_float_param(tree, "Body Diameter M", 0.047, 0.020, 0.100)
    add_int_param(tree, "Ridge Count", 5, 2, 10)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    L = gin.outputs["Body Length M"]
    D = gin.outputs["Body Diameter M"]
    RC = gin.outputs["Ridge Count"]

    r = _m(tree, "MULTIPLY", (bx - 2200, by + 300), D, 0.5)
    band_h = _m(tree, "MULTIPLY", (bx - 2200, by + 140), L, 0.04)
    ridge_h = _m(tree, "MULTIPLY", (bx - 2200, by - 20), L, 0.035)
    ridge_span = _m(tree, "MULTIPLY", (bx - 2200, by - 180), L, 0.62)
    ridge_first = _m(tree, "MULTIPLY", (bx - 2200, by - 340), L, 0.22)
    top_base = _m(tree, "SUBTRACT", (bx - 2200, by - 500), L, band_h)

    body = _cyl_z(tree, (bx - 1400, by), r, L,
                  _m(tree, "MULTIPLY", (bx - 2200, by - 660), L, 0.5),
                  verts=24)
    base = _shell_z(tree, (bx - 1400, by - 800),
                    _m(tree, "MULTIPLY", (bx - 2200, by - 800), r, 1.10),
                    band_h, 0.0, verts=24)
    top = _shell_z(tree, (bx - 1400, by - 1200),
                   _m(tree, "MULTIPLY", (bx - 2200, by - 1200), r, 1.10),
                   band_h, top_base, verts=24)
    ridge = _open_ring_proto_z(
        tree, (bx - 1400, by - 1600),
        _m(tree, "MULTIPLY", (bx - 2200, by - 1600), r, 1.14), ridge_h, verts=24)
    ridges = _rank_inst(tree, (bx - 800, by - 1600), RC, ridge, ridge_span,
                        ridge_first, axis="z")

    geom = _join(tree, (bx + 400, by), [body, base, top, ridges])
    _finish(tree, gin, gout, geom, (bx + 700, by), BID,
            _aux2_attrs(tree, (bx + 400, by - 2200)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Closed Tube + Bands", "nodes": ("Cylinder",),
         "role": "geometry"},
        {"title": "Ridge Rank", "nodes": ("Cylinder", "Instance on Points"),
         "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_vibraslap
# ---------------------------------------------------------------------------

def build_music_vibraslap(group_name="MEL_music_vibraslap"):
    """Vibraslap: a toothed box on a BENT rod ending in a wooden ball.

    The teeth are sized from the rank PITCH (span/(count-1) x 0.55), so a 9-tooth
    setting cannot merge into one slab. The rod is two PLATES with per-segment
    rotations (a `Transform` rotates about its own origin, so a segment authored
    at the origin and then translated lands exactly on its own run) — the first
    segment slopes from the box top down to the ball's height, the second runs
    level into the ball. A single straight stick would be a rattle, not a
    vibraslap, so the gate asserts the ARCTAN2 on the rod chain.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_vibraslap"
    bx, by = 0, 0

    add_float_param(tree, "Box Length M", 0.125, 0.060, 0.250)
    add_float_param(tree, "Box Width M", 0.056, 0.028, 0.120)
    add_float_param(tree, "Box Height M", 0.054, 0.026, 0.110)
    add_int_param(tree, "Tooth Count", 9, 4, 16)
    add_float_param(tree, "Rod Length M", 0.300, 0.150, 0.600)
    add_float_param(tree, "Ball Radius M", 0.030, 0.014, 0.060)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    BL = gin.outputs["Box Length M"]
    BW = gin.outputs["Box Width M"]
    BH = gin.outputs["Box Height M"]
    TC = gin.outputs["Tooth Count"]
    RL = gin.outputs["Rod Length M"]
    BR = gin.outputs["Ball Radius M"]

    half_L = _m(tree, "MULTIPLY", (bx - 2200, by + 300), BL, 0.5)
    box_cz = _m(tree, "MULTIPLY", (bx - 2200, by + 140), BH, 0.5)
    tooth_h = _m(tree, "MULTIPLY", (bx - 2200, by - 20), BH, 0.30)
    tooth_span = _m(tree, "MULTIPLY", (bx - 2200, by - 180), BL, 0.80)
    tooth_first = _m(tree, "MULTIPLY", (bx - 2200, by - 340), BL, -0.40)
    pitch = _m(tree, "DIVIDE", (bx - 2200, by - 500), tooth_span,
               _m(tree, "MAXIMUM", (bx - 2400, by - 500),
                  _m(tree, "SUBTRACT", (bx - 2600, by - 500), TC, 1.0), 1.0))
    tooth_w = _m(tree, "MULTIPLY", (bx - 2200, by - 660), pitch, 0.55)
    tooth_d = _m(tree, "MULTIPLY", (bx - 2200, by - 820), BW, 0.80)

    box = _plate(tree, (bx - 1400, by), BL, BW, BH,
                 translation=_vec(tree, (bx - 1600, by - 200), 0.0, 0.0,
                                  box_cz))
    tooth = _plate(tree, (bx - 1400, by - 600), tooth_w, tooth_d, tooth_h,
                   translation=_vec(tree, (bx - 1600, by - 800), 0.0, 0.0,
                                    _m(tree, "MULTIPLY", (bx - 2200, by - 800),
                                       tooth_h, 0.5)))
    teeth = _rank_inst(tree, (bx - 800, by - 600), TC, tooth, tooth_span,
                       tooth_first, axis="x", z=BH)

    # the bent rod: seg1 slopes from the box's +X top corner to the ball height,
    # seg2 runs level into the ball.
    s1 = _m(tree, "MULTIPLY", (bx - 2200, by - 1200), RL, 0.40)
    s2 = _m(tree, "MULTIPLY", (bx - 2200, by - 1360), RL, 0.60)
    rod_w = _m(tree, "MULTIPLY", (bx - 2200, by - 1520), BH, 0.22)
    dz = _m(tree, "SUBTRACT", (bx - 2200, by - 1680), BH, BR)
    len1 = _m(tree, "SQRT", (bx - 2200, by - 1840),
              _m(tree, "ADD", (bx - 2400, by - 1840),
                 _m(tree, "MULTIPLY", (bx - 2600, by - 1840), s1, s1),
                 _m(tree, "MULTIPLY", (bx - 2600, by - 2000), dz, dz)))
    ang1 = _m(tree, "ARCTAN2", (bx - 2200, by - 2160), dz, s1)
    mid1_x = _m(tree, "ADD", (bx - 2200, by - 2320), half_L,
                _m(tree, "MULTIPLY", (bx - 2400, by - 2320), s1, 0.5))
    mid1_z = _m(tree, "MULTIPLY", (bx - 2200, by - 2480),
                _m(tree, "ADD", (bx - 2400, by - 2480), BH, BR), 0.5)
    mid2_x = _m(tree, "ADD", (bx - 2200, by - 2640),
                _m(tree, "ADD", (bx - 2400, by - 2640), half_L, s1),
                _m(tree, "MULTIPLY", (bx - 2400, by - 2640), s2, 0.5))
    ball_x = _m(tree, "ADD", (bx - 2200, by - 2800),
                _m(tree, "ADD", (bx - 2400, by - 2800),
                   _m(tree, "ADD", (bx - 2600, by - 2800), half_L, s1), s2), BR)

    seg1 = _plate(tree, (bx - 1400, by - 3000), len1, rod_w, rod_w,
                  translation=_vec(tree, (bx - 1600, by - 3000), mid1_x, 0.0,
                                   mid1_z),
                  rotation=_vec(tree, (bx - 2200, by - 3200), 0.0, ang1, 0.0))
    seg2 = _plate(tree, (bx - 1400, by - 3400), s2, rod_w, rod_w,
                  translation=_vec(tree, (bx - 1600, by - 3400), mid2_x, 0.0,
                                   BR))
    ball = _sphere(tree, (bx - 1400, by - 3800), BR, segments=32, rings=16)
    ball = _xf(tree, (bx - 1200, by - 3800), ball.outputs["Mesh"],
               translation=_vec(tree, (bx - 1600, by - 3800), ball_x, 0.0,
                                BR)).outputs["Geometry"]

    geom = _join(tree, (bx + 400, by), [box, teeth, seg1, seg2, ball])
    _finish(tree, gin, gout, geom, (bx + 700, by), BID,
            _aux2_attrs(tree, (bx + 400, by - 4200)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Toothed Box", "nodes": ("Cube", "Mesh Line",
                                          "Instance on Points"),
         "role": "geometry"},
        {"title": "Bent Rod", "nodes": ("Cube", "Transform"), "role": "geometry"},
        {"title": "Ball", "nodes": ("UV Sphere",), "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

register_builder(
    "MEL_music_maracas", build_music_maracas, "Maracas",
    "Maracas: a matched pair of gourd heads on handles with bead bands, placed "
    "by a literal-2 rank. Native-only.",
    "music",
)
register_builder(
    "MEL_music_wood_block", build_music_wood_block, "Wood Block",
    "Wood block: a slotted hardwood block — two proud slot rails straddling a "
    "groove whose floor is the body's own top face. Native-only.",
    "music",
)
register_builder(
    "MEL_music_cowbell", build_music_cowbell, "Cowbell",
    "Cowbell: a 4-sided tapered open steel shell with a mouth rim, a crown "
    "plate and a mounting loop. Native-only.",
    "music",
)
register_builder(
    "MEL_music_castanets", build_music_castanets, "Castanets",
    "Castanets: two shallow shells on a cord, each with a mounting loop, placed "
    "by a literal-2 rank. Native-only.",
    "music",
)
register_builder(
    "MEL_music_shaker", build_music_shaker, "Shaker",
    "Shaker: a plain closed ridged tube with proud end bands and no handle. "
    "Native-only.",
    "music",
)
register_builder(
    "MEL_music_vibraslap", build_music_vibraslap, "Vibraslap",
    "Vibraslap: a toothed box on a bent rod ending in a wooden ball. The teeth "
    "are sized from the rank pitch, never from the count. Native-only.",
    "music",
)
