"""P4 wave 10 — world percussion lane: djembe, congas, bongos, cajon, frame
drum, tabla.

Gap audit first (repo-wide grep over `deploy/surreal_arch/` + `Tools/registry_baseline.json`,
2026-10-04): the percussion lane owns `MEL_music_timpani`, `MEL_music_snare_drum`,
`MEL_music_bass_drum`, `MEL_music_cymbals`, `MEL_music_tambourine`,
`MEL_music_carillon`, `MEL_music_drum_kit_rail`, `MEL_music_steelpan`,
`MEL_music_gong`, `MEL_music_ocarina`, `MEL_music_glockenspiel`,
`MEL_music_celesta`, `MEL_music_marimba`, `MEL_music_vibraphone` and the
`MEL_chime_*` walls. NONE of the six below existed anywhere (grep count 0 each,
0 in the baseline):

    djembe, congas, bongos, cajon, frame drum, tabla

Every one is a HAND drum whose identity is its shell anatomy — a goblet, a pair
of barrels on a stand, a small joined pair, a box, a shallow braced ring, and a
wooden/metal pair with a black syahi patch. None is a re-sizing of the western
kit drums above: `MEL_music_snare_drum` is a shallow straight cylinder with lugs
and a strainer, not a goblet on a flared foot.

Design rules (same as music_percussion_kit / music_keyboard_kit /
music_electronics_kit):
  - Native-only. These are revolved shells, discs and rings that 5.2 primitives
    express exactly; a Higgsas subtree here would be decoration, not a lead.
    Every builder still stores `higgsas_lead` (1.0 = native) so the family gate
    and the instruments gate read the lane uniformly.
  - The wave-6 origin-explicit helpers are REUSED, never re-authored:
    `_cone_z` takes the BASE (`MeshCone`'s origin is its base), `_cyl_z` /
    `_cyl_x` take the CENTRE (`MeshCylinder`'s origin is its centre).
  - Zero `MeshBoolean` in the lane: a cutter that touches the mesh's own
    boundary emits ZERO geometry with no error and no `link_failures` entry.
    Every rim, ring, port and lace is LAID ON, never cut.
  - A primitive `Size` component is never left at LITERAL ZERO (the
    castle-merlon zero-width-slab class).
  - A cone's tip radius is never 0: an NGON top cap at radius 0 is a degenerate
    face by construction. Every cone here has two non-zero radii.
  - Every drum sits ON the floor (realized min_z >= -0.01).
  - Placement is applied ONCE, in the rank's own points (`_rank_inst` places a
    rank ONLY by its points; there is no second translate to double with).

Lane-local law 1 — `_ring_rank`, a RADIAL rank of protos around a circle, built
from `MeshCircle` (fill NONE) -> `MeshToPoints` -> `InstanceOnPoints`. This is
the lane's lug / rope-lace law, and the reason the lacing on a djembe or a tabla
is real rope rather than a painted band. `CurveToPoints` was probed as the
alternative and REJECTED (2026-10-04, Saved/Audit/probe_w10_ring.py): in COUNT
mode it emits ZERO points at its default Resolution, and its `Rotation` output
lays an instance's +Z along the TANGENT (measured z extent 0.10 with Rotation
linked against 0.20 without), so it is the wrong node for a lug ring.

Lane-local law 2 — a lace rank on a CONICAL host is seated at the host's MEAN
radius over its own span, never at a constant offset from the widest end. A
constant-radius rope on a cone touches at one height and floats at every other;
the mean seat keeps it against the shell for the whole run (same class as the
suona's finger rims, skill pitfall "a rim/collar rank on a CONICAL host").

Builders:
    MEL_music_djembe       flared foot + stem + flaring bowl + head ring + 20 rope laces
    MEL_music_congas       two barrel shells on a T-stand + lug rings + heads
    MEL_music_bongos       asymmetric joined pair (large + small) + bridge + lugs
    MEL_music_cajon        box + tapa plate + laid-on sound port + snare-wire rank
    MEL_music_frame_drum   shallow wide ring + head + crossed braces + grip
    MEL_music_tabla        dayan (tapered wood) + bayan (kettle) + syahi + laces
"""

from __future__ import annotations

from .core import (
    safe_node, link_sockets, label_tree, new_geometry_tree, add_float_param,
    add_int_param, add_bool_param, register_builder, sock,
)
from .music_string_kit import _finish
from .music_wind_reed_brass import (
    _vec, _cyl_x, _cyl_z, _cone_z, _join, _rank_inst,
)
from .music_keyboard_kit import _m, _plate
from .music_higgsas_instruments import _cyl, _xf


# ---------------------------------------------------------------------------
# Lane-local laws
# ---------------------------------------------------------------------------

def _disc_z(tree, loc, r_sock, t_sock, cz, x=0.0, y=0.0, verts=32, fill=2):
    """A disc / head lying in the XY plane with its CENTRE at `cz`."""
    prim = _cyl(tree, (loc[0] - 100, loc[1]), r_sock, t_sock,
                vertices=verts, fill=fill)
    if prim is None:
        return None
    return _xf(tree, (loc[0] + 100, loc[1]), prim.outputs["Mesh"],
               translation=_vec(tree, (loc[0] + 100, loc[1] - 200),
                               x, y, cz)).outputs["Geometry"]


def _shell_z(tree, loc, r_sock, h_sock, base_z, x=0.0, y=0.0, verts=32, fill=1):
    """An open shell standing on `base_z`.

    `MeshCylinder`'s origin is its CENTRE, so the centre is computed as
    `base + h/2` — the cylinder idiom, never the cone idiom. Default `fill=1`
    (NONE) gives an open tube, which is what a rim ring / wall band wants.
    """
    bx, by = loc
    half = _m(tree, "MULTIPLY", (bx - 300, by - 220), h_sock, 0.5)
    cz = _m(tree, "ADD", (bx - 500, by - 220), base_z, half)
    prim = _cyl(tree, (bx - 100, by), r_sock, h_sock, vertices=verts, fill=fill)
    if prim is None:
        return None
    return _xf(tree, (bx + 100, by), prim.outputs["Mesh"],
               translation=_vec(tree, (bx + 100, by - 220), x, y,
                               cz)).outputs["Geometry"]


def _tube_y(tree, loc, r_sock, d_sock, cy, x=0.0, z=0.0, verts=32):
    """An open tube along Y, centred on `cy` — a laid-on sound port.

    `_cyl_y` (music_keyboard_kit) hard-codes the NGON cap, so a port built with
    it would be a solid plug rather than a ring. Built from `_cyl` with fill=1.
    """
    prim = _cyl(tree, (loc[0] - 100, loc[1]), r_sock, d_sock,
                vertices=verts, fill=1)
    if prim is None:
        return None
    return _xf(tree, (loc[0] + 100, loc[1]), prim.outputs["Mesh"],
               rotation=(1.5707963, 0.0, 0.0),
               translation=_vec(tree, (loc[0] + 100, loc[1] - 220),
                               x, cy, z)).outputs["Geometry"]


def _mean_r(tree, loc, a_sock, b_sock):
    """(a + b) / 2 — the mean radius a rank on a CONICAL host must seat at."""
    return _m(tree, "MULTIPLY", loc,
              _m(tree, "ADD", (loc[0] - 200, loc[1] - 140), a_sock, b_sock),
              0.5)


def _ring_rank(tree, loc, count_sock, proto_geo, radius_sock,
               cx=0.0, cy=0.0, cz=0.0):
    """A RADIAL rank of `proto_geo` around a circle of `radius_sock`.

    `MeshCircle` (fill NONE) -> `MeshToPoints` -> `InstanceOnPoints`. Measured
    2026-10-04: a 10-vertex circle realizes 10 lugs (640 verts with the lug
    proto), and `CurveToPoints` was rejected for this job (module docstring).
    The proto's own origin IS the instance origin, so a proto centred on itself
    is centred on its ring point.
    """
    bx, by = loc
    circ = safe_node(tree, "GeometryNodeMeshCircle", (bx, by))
    if circ is None:
        return None
    try:
        circ.fill_type = "NONE"
    except Exception:
        pass
    link_sockets(tree, count_sock, sock(circ, "Vertices"))
    link_sockets(tree, radius_sock, sock(circ, "Radius"))
    pts = safe_node(tree, "GeometryNodeMeshToPoints", (bx + 200, by))
    if pts is None:
        return None
    link_sockets(tree, circ.outputs["Mesh"], sock(pts, "Mesh"))
    place = _xf(tree, (bx + 400, by), pts.outputs["Points"],
                translation=_vec(tree, (bx + 400, by - 220), cx, cy, cz))
    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 600, by))
    if inst is None:
        return None
    link_sockets(tree, place.outputs["Geometry"], sock(inst, "Points"))
    link_sockets(tree, proto_geo, sock(inst, "Instance"))
    return inst.outputs["Instances"]


def _laces(tree, loc, count_sock, radius_sock, r_rope, span_sock,
           z_top, z_bottom, cx=0.0, cy=0.0, verts=6):
    """A radial ring of thin Z-ropes running from `z_bottom` to `z_top`.

    The rope proto is a cylinder CENTRED on its own origin, so the ring is
    placed at the span's midpoint and the ropes straddle the run. `radius_sock`
    must be the host's MEAN radius over that span (lane law 2).
    """
    bx, by = loc
    rope = _cyl_z(tree, (bx, by), r_rope, span_sock, 0.0, verts=verts)
    if rope is None:
        return None
    mid = _m(tree, "MULTIPLY", (bx - 300, by - 220),
             _m(tree, "ADD", (bx - 500, by - 220), z_top, z_bottom), 0.5)
    return _ring_rank(tree, (bx + 300, by), count_sock, rope, radius_sock,
                      cx=cx, cy=cy, cz=mid)


# ---------------------------------------------------------------------------
# MEL_music_djembe
# ---------------------------------------------------------------------------

def build_music_djembe(group_name="MEL_music_djembe"):
    """Djembe: flared foot, narrow stem, flaring bowl, head ring, 20 rope laces.

    The goblet silhouette is THREE revolved pieces stacked base-to-base (the
    cone idiom — `MeshCone`'s origin is its base), which is what makes this a
    djembe rather than the snare drum's straight shell.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_djembe"
    bx, by = 0, 0

    add_float_param(tree, "Head Diameter M", 0.32, 0.18, 0.5)
    add_float_param(tree, "Body Height M", 0.60, 0.3, 1.0)
    add_float_param(tree, "Stem Radius Ratio", 0.34, 0.2, 0.6)
    add_float_param(tree, "Foot Flare Ratio", 1.30, 1.0, 1.8)
    add_float_param(tree, "Head Thickness M", 0.004, 0.001, 0.02)
    add_float_param(tree, "Rim Height M", 0.035, 0.012, 0.08)
    add_int_param(tree, "Lace Count", 20, 8, 40)
    add_float_param(tree, "Rope Radius M", 0.005, 0.002, 0.014)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    R = _m(tree, "MULTIPLY", (bx - 1400, by + 300),
           gin.outputs["Head Diameter M"], 0.5)
    H = gin.outputs["Body Height M"]
    # landmark heights: foot to 0.16 H, stem to 0.44 H, bowl to H
    foot_h = _m(tree, "MULTIPLY", (bx - 1400, by + 140), H, 0.16)
    stem_top = _m(tree, "MULTIPLY", (bx - 1400, by - 20), H, 0.44)
    stem_h = _m(tree, "SUBTRACT", (bx - 1600, by - 20), stem_top, foot_h)
    bowl_h = _m(tree, "SUBTRACT", (bx - 1600, by - 180), H, stem_top)
    stem_r = _m(tree, "MULTIPLY", (bx - 1400, by - 180), R,
                gin.outputs["Stem Radius Ratio"])
    foot_r = _m(tree, "MULTIPLY", (bx - 1400, by - 340), R,
                gin.outputs["Foot Flare Ratio"])

    # foot: base at z=0, flaring from the widest point up to the stem
    foot = _cone_z(tree, (bx - 800, by + 300), foot_r, stem_r, foot_h, 0.0,
                   verts=32)
    # stem: a slightly tapered shaft (a cone, not a tube — the goblet's waist)
    stem_lo_r = _m(tree, "MULTIPLY", (bx - 1400, by + 60), stem_r, 0.92)
    stem = _cone_z(tree, (bx - 800, by + 100), stem_r, stem_lo_r, stem_h,
                   foot_h, verts=32)
    # bowl: from the stem top up to the head, flaring to R
    bowl = _cone_z(tree, (bx - 800, by - 100), stem_r, R, bowl_h, stem_top,
                   verts=32)
    # head: a disc seated at the bowl's mouth
    head = _disc_z(tree, (bx - 800, by - 300), R,
                   gin.outputs["Head Thickness M"], H, verts=32)
    # rim: a ring standing proud of the head
    rim = _shell_z(tree, (bx - 800, by - 500),
                   _m(tree, "MULTIPLY", (bx - 1400, by - 500), R, 1.04),
                   gin.outputs["Rim Height M"], H, verts=32)
    # anchor band: the rope anchor ring at the stem/bowl junction
    anchor = _shell_z(tree, (bx - 800, by - 700),
                      _m(tree, "MULTIPLY", (bx - 1400, by - 700), stem_r, 1.18),
                      _m(tree, "MULTIPLY", (bx - 1400, by - 860),
                         gin.outputs["Rim Height M"], 0.9), stem_top, verts=32)
    # laces: ropes from the head ring down the bowl to the anchor band, seated
    # at the BOWL's mean radius (lane law 2 — the bowl is a cone).
    lace_span = _m(tree, "SUBTRACT", (bx - 1400, by - 1020), H, stem_top)
    laces = _laces(tree, (bx - 500, by - 700), gin.outputs["Lace Count"],
                   _mean_r(tree, (bx - 1400, by - 1180), stem_r, R),
                   gin.outputs["Rope Radius M"], lace_span, H, stem_top)

    geom = _join(tree, (bx + 400, by),
                 [foot, stem, bowl, head, rim, anchor, laces])
    sidx = safe_node(tree, "GeometryNodeInputIndex", (bx + 400, by - 400))
    smod = _m(tree, "MODULO", (bx + 400, by - 520), sidx.outputs["Index"], 12.0)
    _finish(tree, gin, gout, geom, (bx + 700, by), BID,
            [("drum_semitone_mod12", smod), ("higgsas_lead", 1.0)])

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Goblet Shell", "nodes": ("Cone", "Cylinder"), "role": "geometry"},
        {"title": "Head + Rim", "nodes": ("head", "rim"), "role": "geometry"},
        {"title": "Rope Laces", "nodes": ("Circle", "Instance on Points"),
         "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_congas
# ---------------------------------------------------------------------------

def build_music_congas(group_name="MEL_music_congas"):
    """Congas: two barrel shells on a T-stand, lug rings, heads.

    Each drum is a BARREL — two cones base-to-base giving a belly — rather than
    a straight tube. The shells sit on a stand whose feet reach the floor, so
    the drums are lifted (a conga on a stand, not a floor drum).
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_congas"
    bx, by = 0, 0

    add_float_param(tree, "Drum Diameter M", 0.28, 0.18, 0.42)
    add_float_param(tree, "Drum Height M", 0.78, 0.4, 1.1)
    add_float_param(tree, "Pair Gap M", 0.05, 0.0, 0.2)
    add_float_param(tree, "Head Thickness M", 0.004, 0.001, 0.02)
    add_float_param(tree, "Stand Lift M", 0.24, 0.06, 0.5)
    add_float_param(tree, "Belly Ratio", 1.10, 1.0, 1.3)
    add_int_param(tree, "Lug Count", 8, 4, 16)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    R = _m(tree, "MULTIPLY", (bx - 1600, by + 300),
           gin.outputs["Drum Diameter M"], 0.5)
    H = gin.outputs["Drum Height M"]
    lift = gin.outputs["Stand Lift M"]
    t_head = gin.outputs["Head Thickness M"]
    belly = _m(tree, "MULTIPLY", (bx - 1600, by + 140), R,
               gin.outputs["Belly Ratio"])
    lower_h = _m(tree, "MULTIPLY", (bx - 1600, by - 20), H, 0.46)
    upper_h = _m(tree, "SUBTRACT", (bx - 1800, by - 20), H, lower_h)
    upper_base = _m(tree, "ADD", (bx - 1800, by - 180), lift, lower_h)
    r_lo = _m(tree, "MULTIPLY", (bx - 1600, by - 180), R, 0.86)
    r_hi = _m(tree, "MULTIPLY", (bx - 1600, by - 340), R, 0.94)
    top_z = _m(tree, "ADD", (bx - 1800, by - 500), lift, H)
    cx = _m(tree, "ADD", (bx - 1800, by - 660), R,
            _m(tree, "MULTIPLY", (bx - 2000, by - 660),
               gin.outputs["Pair Gap M"], 0.5))

    drums = []
    for i, sx in enumerate((-1.0, 1.0)):
        dx = _m(tree, "MULTIPLY", (bx - 2000, by - 820 + i * 160), cx, sx)
        lo = _cone_z(tree, (bx - 1000, by + 300 + i * 400), r_lo, belly,
                     lower_h, lift, x=dx, verts=32)
        hi = _cone_z(tree, (bx - 1000, by - 100 + i * 400), belly, r_hi,
                     upper_h, upper_base, x=dx, verts=32)
        hd = _disc_z(tree, (bx - 800, by + 100 + i * 400), r_hi, t_head,
                     top_z, x=dx, verts=32)
        ring = _shell_z(tree, (bx - 800, by - 300 + i * 400),
                        _m(tree, "MULTIPLY", (bx - 1400, by - 300 + i * 400),
                           r_hi, 1.05),
                        _m(tree, "MULTIPLY", (bx - 1400, by - 460 + i * 400),
                           t_head, 6.0), top_z, x=dx, verts=32)
        lug = _cyl_z(tree, (bx - 500, by + 100 + i * 400),
                     _m(tree, "MULTIPLY", (bx - 1000, by + 100 + i * 400),
                        t_head, 1.6),
                     _m(tree, "MULTIPLY", (bx - 1000, by - 60 + i * 400),
                        t_head, 11.0), 0.0, verts=8)
        lugs = _ring_rank(tree, (bx - 300, by + 100 + i * 400),
                          gin.outputs["Lug Count"], lug,
                          _m(tree, "MULTIPLY", (bx - 1400, by + 100 + i * 400),
                             r_hi, 1.10), cx=dx, cz=top_z)
        drums.append(_join(tree, (bx + 200, by + 100 + i * 400),
                           [lo, hi, hd, ring, lugs]))

    # stand: a T-bar under both drums + two posts + two feet (feet ON the floor)
    bar_z = _m(tree, "MULTIPLY", (bx - 1800, by + 700), lift, 0.72)
    bar = _plate(tree, (bx - 1000, by + 900),
                 _m(tree, "MULTIPLY", (bx - 1600, by + 900), cx, 2.0),
                 0.045, 0.045,
                 translation=_vec(tree, (bx - 1300, by + 740), 0.0, 0.0, bar_z))
    posts, feet = [], []
    for i, sx in enumerate((-1.0, 1.0)):
        px = _m(tree, "MULTIPLY", (bx - 2000, by + 1100 + i * 160), cx,
                sx * 0.72)
        posts.append(_cyl_z(tree, (bx - 800, by + 1100 + i * 300), 0.020, lift,
                            _m(tree, "MULTIPLY", (bx - 1400, by + 1100 + i * 300),
                               lift, 0.5), x=px, verts=12))
        feet.append(_plate(tree, (bx - 800, by + 900 + i * 300),
                           0.10, 0.055, 0.022,
                           translation=_vec(tree, (bx - 1000, by + 740 + i * 300),
                                           px, 0.0, 0.011)))
    geom = _join(tree, (bx + 600, by), drums + [bar] + posts + feet)
    sidx = safe_node(tree, "GeometryNodeInputIndex", (bx + 600, by - 700))
    smod = _m(tree, "MODULO", (bx + 600, by - 820), sidx.outputs["Index"], 12.0)
    _finish(tree, gin, gout, geom, (bx + 900, by), BID,
            [("drum_semitone_mod12", smod), ("higgsas_lead", 1.0)])

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Barrel Shells", "nodes": ("Cone", "Cylinder"), "role": "geometry"},
        {"title": "Heads + Lugs", "nodes": ("head", "Circle"), "role": "instance"},
        {"title": "T-Stand", "nodes": ("Cube", "post"), "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_bongos
# ---------------------------------------------------------------------------

def build_music_bongos(group_name="MEL_music_bongos"):
    """Bongos: a joined pair — a large drum and a small one — with a bridge.

    The PAIR is the identity: two shells of DIFFERENT diameters side by side,
    joined by a bridge block, each with its own head, rim and lug ring.
    `MEL_music_congas` is two IDENTICAL barrels on a stand; the bongos are
    hand-held and asymmetric.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_bongos"
    bx, by = 0, 0

    add_float_param(tree, "Large Diameter M", 0.22, 0.12, 0.34)
    add_float_param(tree, "Small Diameter M", 0.16, 0.09, 0.28)
    add_float_param(tree, "Drum Height M", 0.20, 0.10, 0.34)
    add_float_param(tree, "Bridge Width M", 0.05, 0.02, 0.1)
    add_float_param(tree, "Head Thickness M", 0.003, 0.001, 0.015)
    add_int_param(tree, "Lug Count", 6, 3, 12)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    H = gin.outputs["Drum Height M"]
    t_head = gin.outputs["Head Thickness M"]
    Rl = _m(tree, "MULTIPLY", (bx - 1600, by + 300),
            gin.outputs["Large Diameter M"], 0.5)
    Rs = _m(tree, "MULTIPLY", (bx - 1600, by + 140),
            gin.outputs["Small Diameter M"], 0.5)
    gap = _m(tree, "MULTIPLY", (bx - 1600, by - 20),
             gin.outputs["Bridge Width M"], 0.5)
    cl = _m(tree, "MULTIPLY", (bx - 1600, by - 180),
            _m(tree, "ADD", (bx - 1800, by - 180), Rl, gap), -1.0)
    cs = _m(tree, "ADD", (bx - 1800, by - 340), Rs, gap)

    parts = []
    for i, (r_sock, c_sock) in enumerate(((Rl, cl), (Rs, cs))):
        # each shell is a slight taper (narrower at the foot) — the cone idiom
        foot_r = _m(tree, "MULTIPLY", (bx - 2000, by - 500 + i * 200),
                    r_sock, 0.90)
        shell = _cone_z(tree, (bx - 1000, by + 300 + i * 400), foot_r, r_sock,
                        H, 0.0, x=c_sock, verts=32)
        head = _disc_z(tree, (bx - 800, by + 100 + i * 400), r_sock, t_head,
                       H, x=c_sock, verts=32)
        rim = _shell_z(tree, (bx - 800, by - 300 + i * 400),
                       _m(tree, "MULTIPLY", (bx - 1400, by - 300 + i * 400),
                          r_sock, 1.05),
                       _m(tree, "MULTIPLY", (bx - 1400, by - 460 + i * 400),
                          t_head, 7.0), H, x=c_sock, verts=32)
        lug = _cyl_z(tree, (bx - 500, by + 100 + i * 400),
                     _m(tree, "MULTIPLY", (bx - 1000, by + 100 + i * 400),
                        t_head, 1.5),
                     _m(tree, "MULTIPLY", (bx - 1000, by - 60 + i * 400),
                        t_head, 9.0), 0.0, verts=8)
        lugs = _ring_rank(tree, (bx - 300, by + 100 + i * 400),
                          gin.outputs["Lug Count"], lug,
                          _m(tree, "MULTIPLY", (bx - 1400, by + 100 + i * 400),
                             r_sock, 1.12), cx=c_sock, cz=H)
        parts += [shell, head, rim, lugs]

    # bridge: a block joining the two shells at mid height
    bridge = _plate(tree, (bx - 800, by + 1100),
                    _m(tree, "MULTIPLY", (bx - 1400, by + 1100),
                       gin.outputs["Bridge Width M"], 2.4),
                    _m(tree, "MULTIPLY", (bx - 1400, by + 940), H, 0.42),
                    _m(tree, "MULTIPLY", (bx - 1400, by + 780), H, 0.16),
                    translation=_vec(tree, (bx - 1000, by + 940), 0.0, 0.0,
                                     _m(tree, "MULTIPLY", (bx - 1400, by + 780),
                                        H, 0.62)))
    geom = _join(tree, (bx + 600, by), parts + [bridge])
    sidx = safe_node(tree, "GeometryNodeInputIndex", (bx + 600, by - 700))
    smod = _m(tree, "MODULO", (bx + 600, by - 820), sidx.outputs["Index"], 12.0)
    _finish(tree, gin, gout, geom, (bx + 900, by), BID,
            [("drum_semitone_mod12", smod), ("higgsas_lead", 1.0)])

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Joined Pair", "nodes": ("Cone", "Cylinder"), "role": "geometry"},
        {"title": "Heads + Lugs", "nodes": ("head", "Circle"), "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_cajon
# ---------------------------------------------------------------------------

def build_music_cajon(group_name="MEL_music_cajon"):
    """Cajon: a box with a proud tapa plate, a laid-on sound port, snare wires.

    The sound port is an open RING laid on the tapa, never a boolean cut — a
    cutter grazing the box's own boundary is the zero-geometry boolean class.
    The wires are a linear rank across the tapa's inner face (the snare rattle),
    and four corner feet lift the box off the floor.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_cajon"
    bx, by = 0, 0

    add_float_param(tree, "Box Width M", 0.30, 0.18, 0.5)
    add_float_param(tree, "Box Depth M", 0.32, 0.18, 0.5)
    add_float_param(tree, "Box Height M", 0.48, 0.25, 0.8)
    add_float_param(tree, "Tapa Thickness M", 0.012, 0.004, 0.03)
    add_float_param(tree, "Port Radius M", 0.055, 0.02, 0.12)
    add_int_param(tree, "Wire Count", 4, 1, 10)
    add_float_param(tree, "Wire Radius M", 0.0025, 0.001, 0.006)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    W = gin.outputs["Box Width M"]
    D = gin.outputs["Box Depth M"]
    H = gin.outputs["Box Height M"]
    tapa_t = gin.outputs["Tapa Thickness M"]
    foot_h = 0.012
    box_cz = _m(tree, "ADD", (bx - 1500, by - 200), foot_h,
                _m(tree, "MULTIPLY", (bx - 1700, by - 200), H, 0.5))

    body = _plate(tree, (bx - 1000, by), W, D, H,
                  translation=_vec(tree, (bx - 1300, by - 200), 0.0, 0.0,
                                   box_cz))
    # tapa: a slightly larger front plate standing proud on -Y
    tapa = _plate(tree, (bx - 1000, by - 400),
                  _m(tree, "MULTIPLY", (bx - 1500, by - 400), W, 1.04),
                  tapa_t,
                  _m(tree, "MULTIPLY", (bx - 1500, by - 560), H, 1.02),
                  translation=_vec(tree, (bx - 1300, by - 560), 0.0,
                                   _m(tree, "MULTIPLY", (bx - 1500, by - 560),
                                      D, -0.5),
                                   _m(tree, "ADD", (bx - 1700, by - 560),
                                      foot_h,
                                      _m(tree, "MULTIPLY",
                                         (bx - 1900, by - 560), H, 0.51))))
    # sound port: an open ring LAID ON the tapa face (axis along Y, no cut)
    port = _tube_y(tree, (bx - 1000, by - 800), gin.outputs["Port Radius M"],
                   _m(tree, "MULTIPLY", (bx - 1500, by - 800), tapa_t, 2.4),
                   _m(tree, "MULTIPLY", (bx - 1500, by - 960), D, -0.5),
                   x=_m(tree, "MULTIPLY", (bx - 1700, by - 960), W, 0.30),
                   z=_m(tree, "ADD", (bx - 1900, by - 960), foot_h,
                        _m(tree, "MULTIPLY", (bx - 2100, by - 960), H, 0.72)),
                   verts=32)
    # snare wires: a rank across the tapa's inner face. The proto is built AT THE
    # ORIGIN and the rank does ALL the placement — a proto that already carries
    # its own y/z and is then instanced on a rank that sets y/z again lands the
    # part at double the offset (measured before the fix: wires at y = -0.2816
    # while the tapa's front face is y = -0.166, and z up to 0.6025 while the box
    # top is 0.492 — the whole rank floating outside and above the box).
    wire = _cyl_x(tree, (bx - 1000, by - 1200), gin.outputs["Wire Radius M"],
                  _m(tree, "MULTIPLY", (bx - 1500, by - 1200), W, 0.86),
                  0.0, y=0.0, z=0.0, verts=8)
    wires = _rank_inst(tree, (bx - 500, by - 1200), gin.outputs["Wire Count"],
                       wire,
                       _m(tree, "MULTIPLY", (bx - 1500, by - 1520), H, 0.34),
                       _m(tree, "ADD", (bx - 1700, by - 1520), foot_h,
                          _m(tree, "MULTIPLY", (bx - 1900, by - 1520), H, 0.24)),
                       axis="z",
                       y=_m(tree, "MULTIPLY", (bx - 1700, by - 1680), D, -0.44),
                       x=0.0)
    # feet: four corner blocks lifting the box off the floor
    feet = []
    for i, (sx, sy) in enumerate(((-1, -1), (-1, 1), (1, -1), (1, 1))):
        feet.append(_plate(tree, (bx - 800, by + 700 + i * 200),
                           0.05, 0.05, 0.024,
                           translation=_vec(tree, (bx - 1000, by + 560 + i * 200),
                                           _m(tree, "MULTIPLY",
                                              (bx - 1500, by + 560 + i * 200),
                                              W, 0.42 * sx),
                                           _m(tree, "MULTIPLY",
                                              (bx - 1500, by + 400 + i * 200),
                                              D, 0.42 * sy),
                                           0.012)))
    geom = _join(tree, (bx + 600, by), [body, tapa, port, wires] + feet)
    sidx = safe_node(tree, "GeometryNodeInputIndex", (bx + 600, by - 700))
    smod = _m(tree, "MODULO", (bx + 600, by - 820), sidx.outputs["Index"], 12.0)
    _finish(tree, gin, gout, geom, (bx + 900, by), BID,
            [("drum_semitone_mod12", smod), ("higgsas_lead", 1.0)])

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Box + Tapa", "nodes": ("Cube",), "role": "geometry"},
        {"title": "Port + Wires", "nodes": ("Cylinder", "Mesh Line"),
         "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_frame_drum
# ---------------------------------------------------------------------------

def build_music_frame_drum(group_name="MEL_music_frame_drum"):
    """Frame drum: a shallow wide ring, a head, two crossed braces, a grip.

    The shallow ring is the whole instrument — the bodhran / def family shape,
    distinct from the snare's deep shell and the cajon's box. The braces cross
    the open back under the head; the grip block sits on the outer wall.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_frame_drum"
    bx, by = 0, 0

    add_float_param(tree, "Diameter M", 0.55, 0.25, 0.9)
    add_float_param(tree, "Frame Depth M", 0.09, 0.03, 0.22)
    add_float_param(tree, "Frame Thickness M", 0.012, 0.004, 0.04)
    add_float_param(tree, "Head Thickness M", 0.004, 0.001, 0.015)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    R = _m(tree, "MULTIPLY", (bx - 1600, by + 300),
           gin.outputs["Diameter M"], 0.5)
    t_fr = gin.outputs["Frame Thickness M"]
    Rf = _m(tree, "SUBTRACT", (bx - 1600, by + 140), R, t_fr)
    depth = gin.outputs["Frame Depth M"]
    bottom_t = _m(tree, "MULTIPLY", (bx - 1600, by - 100), t_fr, 0.6)
    half_bottom = _m(tree, "MULTIPLY", (bx - 1600, by - 260), bottom_t, 0.5)

    outer = _shell_z(tree, (bx - 1000, by + 300), R, depth, 0.0, verts=48)
    inner = _shell_z(tree, (bx - 1000, by + 100), Rf, depth, 0.0, verts=48)
    # a bottom annulus so the wall reads as a solid frame (centre = t/2, so the
    # disc sits ON the floor instead of half through it)
    bottom = _disc_z(tree, (bx - 1000, by - 100), R, bottom_t, half_bottom,
                     verts=48)
    head = _disc_z(tree, (bx - 1000, by - 300), R,
                   gin.outputs["Head Thickness M"], depth, verts=48)
    # crossed braces across the open back, just under the head
    brace_len = _m(tree, "MULTIPLY", (bx - 1600, by - 500), R, 1.96)
    brace_t = _m(tree, "MULTIPLY", (bx - 1600, by - 660), t_fr, 0.7)
    brace_d = _m(tree, "MULTIPLY", (bx - 1600, by - 820), depth, 0.14)
    brace_z = _m(tree, "MULTIPLY", (bx - 1600, by - 980), depth, 0.45)
    braces = []
    for i, rot in enumerate(((0.0, 0.0, 0.0), (0.0, 0.0, 1.5707963))):
        braces.append(_plate(tree, (bx - 600 - i * 200, by - 500),
                             brace_len, brace_t, brace_d,
                             rotation=rot,
                             translation=_vec(tree, (bx - 800 - i * 200,
                                                     by - 660),
                                              0.0, 0.0, brace_z)))
    # grip: a block on the outer wall (a laid-on handle, never a notch cut)
    grip = _plate(tree, (bx - 1000, by + 700),
                  _m(tree, "MULTIPLY", (bx - 1600, by + 700), t_fr, 2.0),
                  _m(tree, "MULTIPLY", (bx - 1600, by + 540), R, 0.34),
                  _m(tree, "MULTIPLY", (bx - 1600, by + 380), depth, 0.52),
                  translation=_vec(tree, (bx - 1300, by + 540), 0.0, R,
                                   _m(tree, "MULTIPLY", (bx - 1600, by + 380),
                                      depth, 0.5)))
    geom = _join(tree, (bx + 600, by),
                 [outer, inner, bottom, head] + braces + [grip])
    sidx = safe_node(tree, "GeometryNodeInputIndex", (bx + 600, by - 700))
    smod = _m(tree, "MODULO", (bx + 600, by - 820), sidx.outputs["Index"], 12.0)
    _finish(tree, gin, gout, geom, (bx + 900, by), BID,
            [("drum_semitone_mod12", smod), ("higgsas_lead", 1.0)])

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Frame Ring", "nodes": ("Cylinder",), "role": "geometry"},
        {"title": "Head + Braces", "nodes": ("head", "Cube"), "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_tabla
# ---------------------------------------------------------------------------

def build_music_tabla(group_name="MEL_music_tabla"):
    """Tabla: a tapered wooden dayan + a kettle bayan, syahi patches, lacing.

    The PAIR is asymmetric by construction: the dayan is a straight wooden taper
    with a flared foot ring, the bayan is a kettle with a shoulder. Both carry a
    raised black syahi disc on the head and a ring of tension laces, and a gatta
    block rank sits between the shells on the floor.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_tabla"
    bx, by = 0, 0

    add_float_param(tree, "Dayan Diameter M", 0.15, 0.09, 0.24)
    add_float_param(tree, "Bayan Diameter M", 0.22, 0.12, 0.34)
    add_float_param(tree, "Dayan Height M", 0.28, 0.14, 0.42)
    add_float_param(tree, "Bayan Height M", 0.24, 0.12, 0.38)
    add_float_param(tree, "Syahi Ratio", 0.42, 0.2, 0.7)
    add_float_param(tree, "Head Thickness M", 0.004, 0.001, 0.015)
    add_int_param(tree, "Lace Count", 12, 6, 24)
    add_float_param(tree, "Rope Radius M", 0.004, 0.0015, 0.01)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    Rd = _m(tree, "MULTIPLY", (bx - 1800, by + 300),
            gin.outputs["Dayan Diameter M"], 0.5)
    Rb = _m(tree, "MULTIPLY", (bx - 1800, by + 140),
            gin.outputs["Bayan Diameter M"], 0.5)
    Hd = gin.outputs["Dayan Height M"]
    Hb = gin.outputs["Bayan Height M"]
    t_head = gin.outputs["Head Thickness M"]
    syahi = gin.outputs["Syahi Ratio"]
    gap = 0.05
    cd = _m(tree, "MULTIPLY", (bx - 1800, by - 20),
            _m(tree, "ADD", (bx - 2000, by - 20), Rd, gap), -1.0)
    cb = _m(tree, "ADD", (bx - 2000, by - 180), Rb, gap)

    # --- dayan: tapered wood shell + flared foot ring
    d_foot_r = _m(tree, "MULTIPLY", (bx - 1800, by - 340), Rd, 0.74)
    dayan = _cone_z(tree, (bx - 1200, by + 300), d_foot_r, Rd, Hd, 0.0,
                    x=cd, verts=32)
    d_foot = _shell_z(tree, (bx - 1200, by + 100),
                      _m(tree, "MULTIPLY", (bx - 1800, by + 100), d_foot_r,
                         1.10),
                      _m(tree, "MULTIPLY", (bx - 1800, by - 60), Hd, 0.09),
                      0.0, x=cd, verts=32)
    d_head = _disc_z(tree, (bx - 1000, by - 100), Rd, t_head, Hd,
                     x=cd, verts=32)
    d_syahi = _disc_z(tree, (bx - 1000, by - 300),
                      _m(tree, "MULTIPLY", (bx - 1800, by - 300), Rd, syahi),
                      _m(tree, "MULTIPLY", (bx - 1800, by - 460), t_head, 2.4),
                      Hd, x=cd, verts=32)
    # laces run down the dayan's cone, seated at its MEAN radius (lane law 2)
    d_lace_top = _m(tree, "MULTIPLY", (bx - 1800, by - 620), Hd, 0.94)
    d_lace_bot = _m(tree, "MULTIPLY", (bx - 1800, by - 780), Hd, 0.12)
    d_laces = _laces(tree, (bx - 700, by + 300), gin.outputs["Lace Count"],
                     _mean_r(tree, (bx - 1800, by + 300), d_foot_r, Rd),
                     gin.outputs["Rope Radius M"],
                     _m(tree, "SUBTRACT", (bx - 1800, by + 140),
                        d_lace_top, d_lace_bot),
                     d_lace_top, d_lace_bot, cx=cd)

    # --- bayan: kettle (two cones meeting at a belly) + head + syahi
    b_lower_h = _m(tree, "MULTIPLY", (bx - 1800, by - 940), Hb, 0.58)
    b_upper_h = _m(tree, "SUBTRACT", (bx - 2000, by - 940), Hb, b_lower_h)
    b_belly = _m(tree, "MULTIPLY", (bx - 1800, by - 1100), Rb, 1.06)
    b_lower_r = _m(tree, "MULTIPLY", (bx - 1800, by - 1260), Rb, 0.46)
    b_upper_r = _m(tree, "MULTIPLY", (bx - 1800, by - 1420), Rb, 0.96)
    bayan = _cone_z(tree, (bx - 1200, by - 300), b_lower_r, b_belly, b_lower_h,
                    0.0, x=cb, verts=32)
    bayan_hi = _cone_z(tree, (bx - 1200, by - 500), b_belly, b_upper_r,
                       b_upper_h, b_lower_h, x=cb, verts=32)
    b_head = _disc_z(tree, (bx - 1000, by - 700), b_upper_r, t_head, Hb,
                     x=cb, verts=32)
    b_syahi = _disc_z(tree, (bx - 1000, by - 900),
                      _m(tree, "MULTIPLY", (bx - 1800, by - 900), b_upper_r,
                         syahi),
                      _m(tree, "MULTIPLY", (bx - 1800, by - 1060), t_head, 2.4),
                      Hb, x=cb, verts=32)
    b_lace_top = _m(tree, "MULTIPLY", (bx - 1800, by - 1580), Hb, 0.94)
    b_lace_bot = _m(tree, "MULTIPLY", (bx - 1800, by - 1740), Hb, 0.12)
    b_laces = _laces(tree, (bx - 700, by - 300), gin.outputs["Lace Count"],
                     _mean_r(tree, (bx - 1800, by - 300), b_belly, b_upper_r),
                     gin.outputs["Rope Radius M"],
                     _m(tree, "SUBTRACT", (bx - 1800, by - 460),
                        b_lace_top, b_lace_bot),
                     b_lace_top, b_lace_bot, cx=cb)

    # --- gatta: a rank of tension blocks on the floor under the bayan. The span
    # is the bayan's own diameter and the block width is 0.7 of the rank pitch,
    # so the blocks read as a ROW of separate wedges — a block as wide as the
    # pitch would merge the whole rank into one slab.
    gatta_span = _m(tree, "MULTIPLY", (bx - 2000, by + 900), Rb, 2.0)
    gatta_pitch = _m(tree, "DIVIDE", (bx - 2000, by + 900), gatta_span,
                     _m(tree, "MAXIMUM", (bx - 2200, by + 900),
                        _m(tree, "SUBTRACT", (bx - 2400, by + 900),
                           gin.outputs["Lace Count"], 1.0), 1.0))
    gatta = _rank_inst(tree, (bx - 500, by + 900), gin.outputs["Lace Count"],
                       _plate(tree, (bx - 1000, by + 900),
                              _m(tree, "MULTIPLY", (bx - 2000, by + 900),
                                 gatta_pitch, 0.70),
                              0.026, 0.034),
                       gatta_span,
                       _m(tree, "SUBTRACT", (bx - 2200, by + 900), cb, Rb),
                       axis="x", y=0.0, z=0.017)

    geom = _join(tree, (bx + 400, by),
                 [dayan, d_foot, d_head, d_syahi, d_laces,
                  bayan, bayan_hi, b_head, b_syahi, b_laces, gatta])
    sidx = safe_node(tree, "GeometryNodeInputIndex", (bx + 400, by - 1900))
    smod = _m(tree, "MODULO", (bx + 400, by - 2020), sidx.outputs["Index"], 12.0)
    _finish(tree, gin, gout, geom, (bx + 700, by), BID,
            [("drum_semitone_mod12", smod), ("higgsas_lead", 1.0)])

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Dayan (wood)", "nodes": ("Cone", "Cylinder"), "role": "geometry"},
        {"title": "Bayan (kettle)", "nodes": ("bayan", "b_belly"), "role": "geometry"},
        {"title": "Syahi + Laces", "nodes": ("syahi", "Circle"), "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

register_builder(
    "MEL_music_djembe", build_music_djembe, "Djembe",
    "Djembe: flared foot, narrow stem, flaring bowl, head ring and a radial "
    "rank of rope laces. Native-only.",
    "music",
)
register_builder(
    "MEL_music_congas", build_music_congas, "Congas",
    "Congas: two barrel shells on a T-stand, each with a head, rim and a "
    "radial lug ring. Native-only.",
    "music",
)
register_builder(
    "MEL_music_bongos", build_music_bongos, "Bongos",
    "Bongos: an asymmetric joined pair (large + small) with a bridge block, "
    "heads, rims and lug rings. Native-only.",
    "music",
)
register_builder(
    "MEL_music_cajon", build_music_cajon, "Cajon",
    "Cajon: a box with a proud tapa plate, a laid-on sound port ring, a rank "
    "of snare wires and four corner feet. Native-only.",
    "music",
)
register_builder(
    "MEL_music_frame_drum", build_music_frame_drum, "Frame Drum",
    "Frame drum: a shallow wide ring with a head, two crossed back braces and "
    "a grip block. Native-only.",
    "music",
)
register_builder(
    "MEL_music_tabla", build_music_tabla, "Tabla",
    "Tabla: a tapered wooden dayan and a kettle bayan, each with a raised "
    "syahi patch and a ring of tension laces, plus a gatta block rank. "
    "Native-only.",
    "music",
)
