"""P4 wave 9 — electronic / studio lane: synthesizer, drum machine, turntable,
mixer, sequencer, sampler.

Gap audit first (repo-wide grep over `deploy/surreal_arch/` + the live registry +
`Tools/registry_baseline.json`, 2026-10-04): the music lane owns 666 ids but NOT
ONE of the six below existed anywhere (grep count 0 each, 0 in the baseline):

    synthesizer, drum machine, turntable, mixer, sequencer, sampler

The nearest neighbours are all architecture or effects, not devices: the
electronic gap list in `Saved/Audit/music_gn_expansion_plan.md` (P4) named
`MEL_music_synthesizer`, `MEL_music_drum_machine`, `MEL_music_turntable`,
`MEL_music_mixer` as "similar to baroque_organ / timpani / waveform_wall /
eq_bars" — those are a walkable pipe FACADE, a struck drum, a wave wall and an
aesthetic bar ring, none of which is a studio device. `MEL_aest_mus_eq_bars` is
a ring of decorative bars around a silhouette (built at `radius = 1.8*scale`,
`aesthetic_fx.py`), not a console.

Design rules (same as music_wind_reed_brass / music_wind_folk /
music_percussion_kit / music_keyboard_kit):
  - Native-only. These are plates, discs, collars and arches that 5.2 primitives
    express exactly; a Higgsas subtree here would be decoration, not a lead.
    Every builder still stores `higgsas_lead` (1.0 = native) so the family gate
    and the instruments gate read the lane uniformly.
  - The wave-6 origin-explicit helpers are REUSED, never re-authored: `_cone_x` /
    `_cone_z` take the BASE (`MeshCone`'s origin is its base), `_cyl_x` /
    `_cyl_z` / `_cyl_y` take the CENTRE (`MeshCylinder`'s origin is its centre).
  - The wave-8 keybed (`_keyboard`, the mod-7 black subset law) is REUSED where a
    device has keys, never re-derived.
  - Placement is applied ONCE, in the rank's own points (`_rank_inst` places a
    rank ONLY by its points; there is no second translate to double with).
  - A rank's Start/Offset are always CombineXYZ (a bare float on MeshLine.Offset
    broadcasts to (v, v, v) and silently puts the rank on the wrong axis).
  - A primitive `Size` component is never left at LITERAL ZERO (the castle-merlon
    zero-width-slab class): every `_plate` links all three components.
  - Zero `MeshBoolean` in the lane: a cutter that touches the mesh's own boundary
    emits ZERO geometry with no error and no `link_failures` entry. Panel detail
    is a laid-on plate or collar, never a cut.
  - Every device sits ON the floor (realized min_z >= -0.01): protos that stand
    are `_cyl_z`-centred with the centre computed as bottom + length/2.

Lane identity per builder (each distinct from its closest neighbour by OWN
anatomy, not by a parameter):

    MEL_music_synthesizer  modular rack: module plates on the panel face + a
                           patch-JACK collar rank + a rank of arched PATCH
                           CABLES (Quadratic Bezier -> Curve to Mesh) + keybed.
                           The cables are the instrument.
    MEL_music_drum_machine desktop box: 4x4 PAD grid (rows x columns) + a
                           16-step LED row + rotary knobs + transport row.
    MEL_music_turntable    plinth on four feet + PLATTER disc + slipmat + label
                           + a TONEARM (pivot, tube, headshell, counterweight) +
                           pitch fader + start/stop.
    MEL_music_mixer        frame on side panels + a channel STRIP rank + a FADER
                           rank sharing the same Strip Count (each strip carries
                           its fader) + a VU meter row + an XLR bank.
    MEL_music_sequencer    flat case + TWO step-button rows split from Step Count
                           by the sheng law (FLOOR + SUBTRACT) + an LED bar +
                           transport row.
    MEL_music_sampler      19" 2U rack unit: two RACK EARS + front panel +
                           display bezel + a DATA WHEEL disc + a pad grid +
                           a button row.

Builders:
    MEL_music_synthesizer   rack, modules, jacks, cables, keybed
    MEL_music_drum_machine  case, 4x4 pads, step LEDs, knobs, transport
    MEL_music_turntable     feet, plinth, platter, slipmat, tonearm, fader
    MEL_music_mixer         panels, console, strips, faders, knobs, meters, XLR
    MEL_music_sequencer     case, two step rows, LED bar, transport
    MEL_music_sampler       feet, body, ears, panel, display, wheel, pads
"""

from __future__ import annotations

from .core import (
    safe_node, link_sockets, label_tree, new_geometry_tree, add_float_param,
    add_int_param, add_bool_param, register_builder, sock,
)
from .music_string_kit import _finish
from .music_wind_reed_brass import (
    _vec, _cyl_x, _cyl_z, _join, _rank_inst, _half_span,
)
from .music_keyboard_kit import _m, _cyl_y, _keyboard, _plate


# ---------------------------------------------------------------------------
# Lane-local laws
# ---------------------------------------------------------------------------

def _elec_attrs(tree, loc):
    """The electronic lane's attribute pair: a lane tag + the native lead flag.

    `electron_semitone_mod12` follows the per-lane tag convention the instrument
    lanes already use (`wind_semitone_mod12`, `key_semitone_mod12`,
    `note_semitone_mod12`, `tone_semitone_mod12`), so a convergence consumer
    reads every device in this lane uniformly.
    """
    bx, by = loc
    idx = safe_node(tree, "GeometryNodeInputIndex", (bx, by))
    mod = _m(tree, "MODULO", (bx, by - 140), idx.outputs["Index"] if idx else None, 12.0)
    return [("electron_semitone_mod12", mod), ("higgsas_lead", 1.0)]


def _grid_rank(tree, loc, cols_sock, rows_sock, proto, span_x_sock, span_y_sock,
               cx=0.0, cy=0.0, z=0.0, pad_frac=0.74):
    """A pads grid: a COLUMN rank instanced on a ROW rank.

    Two separate count params drive the two ranks — never one count applied
    twice (the `MEL_music_sheng` class, where a 17-pipe setting produced 34
    pipes because both ranks read the same socket). The column rank is built at
    y = 0 and the row rank does all the Y placement, so no position is applied
    twice either.
    """
    bx, by = loc
    col_span = span_x_sock
    row = _rank_inst(tree, (bx - 400, by), cols_sock, proto, col_span,
                     _m(tree, "ADD", (bx - 600, by - 140), cx,
                        _half_span(tree, (bx - 600, by + 140), col_span)),
                     axis="x", y=0.0, z=z)
    if row is None:
        return None
    return _rank_inst(tree, (bx + 400, by), rows_sock, row, span_y_sock,
                      _m(tree, "ADD", (bx + 200, by - 140), cy,
                         _half_span(tree, (bx + 200, by + 140), span_y_sock)),
                      axis="y", x=0.0, z=0.0)


def _cable_arch(tree, loc, span_sock, lift_sock, radius_sock, res=16):
    """One arched patch cable: a Quadratic Bezier swept with a circle profile.

    The arch's own origin is its midpoint on the panel plane, so a rank places
    it by its centre. Returns a geometry socket, or None.
    """
    bx, by = loc
    bz = safe_node(tree, "GeometryNodeCurveQuadraticBezier", (bx, by))
    if bz is None:
        return None
    try:
        bz.inputs["Resolution"].default_value = res
    except Exception:
        pass
    half = _m(tree, "MULTIPLY", (bx - 400, by - 140), span_sock, -0.5)
    link_sockets(tree, _vec(tree, (bx - 200, by - 140), half, 0.0, 0.0),
                 bz.inputs["Start"])
    link_sockets(tree, _vec(tree, (bx - 200, by - 280), 0.0, 0.0, lift_sock),
                 bz.inputs["Middle"])
    link_sockets(tree, _vec(tree, (bx - 200, by - 420),
                            _m(tree, "MULTIPLY", (bx - 400, by - 420),
                               span_sock, 0.5), 0.0, 0.0),
                 bz.inputs["End"])
    prof = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx, by - 560))
    if prof is None:
        return None
    try:
        prof.inputs["Resolution"].default_value = 8
    except Exception:
        pass
    link_sockets(tree, radius_sock, prof.inputs["Radius"])
    c2m = safe_node(tree, "GeometryNodeCurveToMesh", (bx + 300, by))
    if c2m is None:
        return None
    link_sockets(tree, bz.outputs["Curve"], sock(c2m, "Curve"))
    link_sockets(tree, prof.outputs["Curve"], sock(c2m, "Profile Curve"))
    return c2m.outputs["Mesh"]


# ---------------------------------------------------------------------------
# MEL_music_synthesizer
# ---------------------------------------------------------------------------

def build_music_synthesizer(group_name="MEL_music_synthesizer"):
    """Modular synthesizer: rack cabinet on cheek panels, Module Count module
    plates on the panel face, a patch-jack collar rank, a rank of arched patch
    cables, and a keybed on a shelf in front.

    The patch CABLES are the instrument's identity: a modular synth without a
    patched cable arch is a rack of blank panels, and the gate asserts the
    Bezier -> Curve to Mesh chain that produces them.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_synthesizer"
    bx, by = 0, 0

    add_float_param(tree, "Rack Width M", 1.10, 0.6, 1.6)
    add_float_param(tree, "Rack Height M", 0.62, 0.30, 1.00)
    add_float_param(tree, "Rack Depth M", 0.30, 0.15, 0.50)
    add_float_param(tree, "Stand Height M", 0.72, 0.30, 0.95)
    add_int_param(tree, "Module Count", 4, 2, 8)
    add_int_param(tree, "Jack Count", 6, 2, 12)
    add_int_param(tree, "Cable Count", 3, 1, 8)
    add_float_param(tree, "Cable Radius M", 0.006, 0.002, 0.020)
    add_int_param(tree, "White Key Count", 25, 12, 49)
    add_float_param(tree, "Key Depth M", 0.11, 0.05, 0.20)
    add_float_param(tree, "Key Height M", 0.020, 0.008, 0.045)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    W = gin.outputs["Rack Width M"]
    H = gin.outputs["Rack Height M"]
    D = gin.outputs["Rack Depth M"]
    SH = gin.outputs["Stand Height M"]
    CR = gin.outputs["Cable Radius M"]
    KD = gin.outputs["Key Depth M"]
    KH = gin.outputs["Key Height M"]

    half_w = _m(tree, "MULTIPLY", (bx - 2400, by - 200), W, 0.5)
    half_d = _m(tree, "MULTIPLY", (bx - 2400, by - 340), D, 0.5)
    case_mid = _m(tree, "ADD", (bx - 2400, by - 480), SH,
                  _m(tree, "MULTIPLY", (bx - 2600, by - 480), H, 0.5))
    case_top = _m(tree, "ADD", (bx - 2400, by - 620), SH, H)
    panel_y = _m(tree, "SUBTRACT", (bx - 2400, by - 760),
                 _m(tree, "MULTIPLY", (bx - 2600, by - 760), half_d, -1.0), 0.012)

    case = _plate(tree, (bx - 1600, by), W, D, H,
                  translation=_vec(tree, (bx - 1600, by - 200), 0.0, 0.0, case_mid))

    # cheek panels carrying the rack + a back rail
    cheeks = []
    for i, sx in enumerate((-1.0, 1.0)):
        cheeks.append(_plate(
            tree, (bx - 1400 - i * 200, by - 900),
            0.035, _m(tree, "MULTIPLY", (bx - 1600 - i * 200, by - 900), D, 0.92),
            SH,
            translation=_vec(tree, (bx - 1600 - i * 200, by - 1040),
                             _m(tree, "MULTIPLY", (bx - 1800 - i * 200, by - 1040),
                                half_w, sx * 0.96),
                             0.0, _m(tree, "MULTIPLY", (bx - 1800 - i * 200, by - 1180),
                                     SH, 0.5))))
    rail = _plate(tree, (bx - 1000, by - 1400),
                  _m(tree, "MULTIPLY", (bx - 1200, by - 1400), W, 0.94),
                  0.022, _m(tree, "MULTIPLY", (bx - 1200, by - 1540), SH, 0.07),
                  translation=_vec(tree, (bx - 1200, by - 1540), 0.0,
                                   _m(tree, "SUBTRACT", (bx - 1400, by - 1540),
                                      half_d, 0.022),
                                   _m(tree, "MULTIPLY", (bx - 1400, by - 1680),
                                      SH, 0.88)))

    # module plates on the panel face
    mod_span = _m(tree, "MULTIPLY", (bx - 2200, by - 1800), W, 0.86)
    mod_w = _m(tree, "DIVIDE", (bx - 2200, by - 1940),
               _m(tree, "MULTIPLY", (bx - 2400, by - 1940), mod_span, 0.72),
               gin.outputs["Module Count"])
    module = _plate(tree, (bx - 1600, by - 1800), mod_w, 0.020,
                    _m(tree, "MULTIPLY", (bx - 1800, by - 1800), H, 0.78))
    mods = _rank_inst(tree, (bx - 800, by - 1800), gin.outputs["Module Count"],
                      module, mod_span,
                      _half_span(tree, (bx - 1000, by - 1800), mod_span),
                      axis="x", y=panel_y,
                      z=_m(tree, "ADD", (bx - 1000, by - 1800), case_mid,
                           _m(tree, "MULTIPLY", (bx - 1200, by - 1800), H, 0.06)))

    # patch-jack collars on the lower half of the panel
    jack_span = _m(tree, "MULTIPLY", (bx - 2200, by - 2200), W, 0.70)
    jack = _cyl_y(tree, (bx - 1600, by - 2200),
                  _m(tree, "MULTIPLY", (bx - 1800, by - 2200), CR, 1.6),
                  0.018, 0.0, verts=12)
    jacks = _rank_inst(tree, (bx - 800, by - 2200), gin.outputs["Jack Count"],
                       jack, jack_span,
                       _half_span(tree, (bx - 1000, by - 2200), jack_span),
                       axis="x", y=panel_y,
                       z=_m(tree, "SUBTRACT", (bx - 1000, by - 2200), case_mid,
                            _m(tree, "MULTIPLY", (bx - 1200, by - 2200), H, 0.24)))

    # a rank of arched patch cables, arching out of the panel
    cable_span = _m(tree, "MULTIPLY", (bx - 2200, by - 2600), W, 0.30)
    arch = _cable_arch(tree, (bx - 1600, by - 2600), cable_span,
                       _m(tree, "MULTIPLY", (bx - 1800, by - 2600), H, 0.42), CR)
    rank_span = _m(tree, "MULTIPLY", (bx - 2200, by - 3200), W, 0.34)
    cables = None
    if arch is not None:
        cables = _rank_inst(
            tree, (bx - 800, by - 3200), gin.outputs["Cable Count"], arch,
            rank_span, _half_span(tree, (bx - 1000, by - 3200), rank_span),
            axis="x",
            y=_m(tree, "SUBTRACT", (bx - 1000, by - 3200), panel_y, 0.020),
            z=_m(tree, "ADD", (bx - 1000, by - 3200), case_mid,
                 _m(tree, "MULTIPLY", (bx - 1200, by - 3200), H, 0.30)))

    # keybed shelf in front of the rack
    shelf = _plate(tree, (bx - 1000, by - 3600),
                   _m(tree, "MULTIPLY", (bx - 1200, by - 3600), W, 0.94),
                   _m(tree, "MULTIPLY", (bx - 1200, by - 3740), KD, 1.5), 0.022,
                   translation=_vec(tree, (bx - 1200, by - 3740), 0.0,
                                    _m(tree, "SUBTRACT", (bx - 1400, by - 3740),
                                       _m(tree, "MULTIPLY", (bx - 1400, by - 3880),
                                          half_d, -1.0),
                                       _m(tree, "MULTIPLY", (bx - 1400, by - 4020),
                                          KD, 0.75)),
                                    _m(tree, "SUBTRACT", (bx - 1400, by - 4160),
                                       SH, 0.011)))
    kb = _keyboard(tree, (bx - 400, by - 3600), gin.outputs["White Key Count"],
                   _m(tree, "MULTIPLY", (bx - 800, by - 3600), W, 0.90),
                   None, KD, KH, SH,
                   _m(tree, "SUBTRACT", (bx - 800, by - 3740),
                      _m(tree, "MULTIPLY", (bx - 800, by - 3880), half_d, -1.0),
                      _m(tree, "MULTIPLY", (bx - 1000, by - 4020), KD, 0.50)))

    geom = _join(tree, (bx + 400, by),
                 [case, rail, mods, jacks, cables, shelf, kb] + cheeks)

    _finish(tree, gin, gout, geom, (bx + 600, by), BID,
            _elec_attrs(tree, (bx + 400, by - 300)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Rack + Cheeks", "nodes": ("Cube", "Transform"), "role": "geometry"},
        {"title": "Modules + Jacks", "nodes": ("Cube", "Cylinder", "Mesh Line"), "role": "instance"},
        {"title": "Patch Cables", "nodes": ("Quadratic Bezier", "Curve to Mesh"), "role": "geometry"},
        {"title": "Keybed", "nodes": ("Cube", "Instance on Points"), "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_drum_machine
# ---------------------------------------------------------------------------

def build_music_drum_machine(group_name="MEL_music_drum_machine"):
    """Drum machine: desktop case, a 4x4 pad grid, a step-LED row, two rotary
    knobs and a transport row.

    The PAD GRID and the STEP LED ROW are what make it a drum machine: the pads
    are a rows x columns rank pair (two separate count params, never one count
    applied twice) and the LEDs are a rank on the front lip.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_drum_machine"
    bx, by = 0, 0

    add_float_param(tree, "Case Width M", 0.34, 0.20, 0.60)
    add_float_param(tree, "Case Depth M", 0.26, 0.15, 0.45)
    add_float_param(tree, "Case Height M", 0.070, 0.030, 0.14)
    add_int_param(tree, "Pad Columns", 4, 2, 8)
    add_int_param(tree, "Pad Rows", 4, 2, 8)
    add_float_param(tree, "Pad Size M", 0.045, 0.015, 0.090)
    add_float_param(tree, "Pad Height M", 0.012, 0.004, 0.030)
    add_int_param(tree, "Step Count", 16, 4, 32)
    add_int_param(tree, "Knob Count", 2, 1, 6)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    W = gin.outputs["Case Width M"]
    D = gin.outputs["Case Depth M"]
    H = gin.outputs["Case Height M"]
    PS = gin.outputs["Pad Size M"]
    PH = gin.outputs["Pad Height M"]

    half_w = _m(tree, "MULTIPLY", (bx - 2400, by - 200), W, 0.5)
    half_d = _m(tree, "MULTIPLY", (bx - 2400, by - 340), D, 0.5)

    case = _plate(tree, (bx - 1600, by), W, D, H,
                  translation=_vec(tree, (bx - 1600, by - 200), 0.0, 0.0,
                                   _m(tree, "MULTIPLY", (bx - 1800, by - 200), H, 0.5)))
    pad_top = _m(tree, "ADD", (bx - 2400, by - 480), H,
                 _m(tree, "MULTIPLY", (bx - 2600, by - 480), PH, 0.5))

    # 4x4 pad grid: column rank instanced on a row rank
    pad = _plate(tree, (bx - 1600, by - 600), PS, PS, PH)
    pads = _grid_rank(
        tree, (bx - 800, by - 600), gin.outputs["Pad Columns"],
        gin.outputs["Pad Rows"], pad,
        _m(tree, "MULTIPLY", (bx - 1000, by - 600), W, 0.62),
        _m(tree, "MULTIPLY", (bx - 1000, by - 740), D, 0.40),
        cy=_m(tree, "MULTIPLY", (bx - 1000, by - 880), D, 0.10), z=pad_top)

    # step LEDs on the front lip
    led_span = _m(tree, "MULTIPLY", (bx - 2400, by - 1000), W, 0.80)
    led = _cyl_y(tree, (bx - 1600, by - 1000), 0.0065, 0.012, 0.0, verts=12)
    leds = _rank_inst(tree, (bx - 800, by - 1000), gin.outputs["Step Count"],
                      led, led_span,
                      _half_span(tree, (bx - 1000, by - 1000), led_span),
                      axis="x",
                      y=_m(tree, "MULTIPLY", (bx - 1000, by - 1000), half_d, -0.92),
                      z=_m(tree, "ADD", (bx - 1000, by - 1000), H, 0.0065))

    # rotary knobs on the right of the front strip. The front strip sits at
    # y = -0.65*half_d, CLEAR of the pad grid: at -0.28*half_d the knobs and the
    # transport buttons landed inside the pads' own footprint (pads reach
    # y = -0.0485 at this size) and interpenetrated them — a defect neither the
    # vert/face/degen/diag envelope nor a per-part bbox probe can see, because
    # every part is individually well-formed.
    knob_span = _m(tree, "MULTIPLY", (bx - 2400, by - 1200), W, 0.20)
    knob = _cyl_z(tree, (bx - 1600, by - 1200), 0.014, 0.020, 0.0, verts=16)
    knobs = _rank_inst(tree, (bx - 800, by - 1200), gin.outputs["Knob Count"],
                       knob, knob_span,
                       _m(tree, "ADD", (bx - 1000, by - 1200),
                          _m(tree, "MULTIPLY", (bx - 1200, by - 1200), W, 0.16),
                          _half_span(tree, (bx - 1000, by - 1340), knob_span)),
                       axis="x",
                       y=_m(tree, "MULTIPLY", (bx - 1000, by - 1200), half_d, -0.65),
                       z=_m(tree, "ADD", (bx - 1000, by - 1200), H, 0.010))

    # transport row on the left of the front strip (same clear band as the knobs)
    transport = []
    for i, fx in enumerate((-0.30, -0.18, -0.06)):
        transport.append(_plate(
            tree, (bx - 1200 - i * 200, by - 1600),
            0.036, 0.024, 0.008,
            translation=_vec(tree, (bx - 1400 - i * 200, by - 1600),
                             _m(tree, "MULTIPLY", (bx - 1600 - i * 200, by - 1600),
                                half_w, fx),
                             _m(tree, "MULTIPLY", (bx - 1600 - i * 200, by - 1740),
                                half_d, -0.65),
                             _m(tree, "ADD", (bx - 1600 - i * 200, by - 1880),
                                H, 0.004))))

    geom = _join(tree, (bx + 400, by), [case, pads, leds, knobs] + transport)

    _finish(tree, gin, gout, geom, (bx + 600, by), BID,
            _elec_attrs(tree, (bx + 400, by - 300)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Case", "nodes": ("Cube", "Transform"), "role": "geometry"},
        {"title": "Pad Grid", "nodes": ("Cube", "Mesh Line", "Instance on Points"), "role": "instance"},
        {"title": "Step LEDs + Knobs", "nodes": ("Cylinder", "Mesh Line"), "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_turntable
# ---------------------------------------------------------------------------

def build_music_turntable(group_name="MEL_music_turntable"):
    """DJ turntable: plinth on four feet, platter + slipmat + label discs, a
    tonearm (pivot, tube, headshell, counterweight), a pitch fader and a
    start/stop button.

    The PLATTER + TONEARM pair is the instrument; the gate asserts the platter
    disc traces to `Platter Radius M` and the tonearm tube's Depth to
    `Tonearm Length M` (a deck whose arm is a stub is not a turntable).
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_turntable"
    bx, by = 0, 0

    add_float_param(tree, "Plinth Width M", 0.45, 0.30, 0.70)
    add_float_param(tree, "Plinth Depth M", 0.36, 0.25, 0.60)
    add_float_param(tree, "Plinth Height M", 0.090, 0.040, 0.18)
    add_float_param(tree, "Foot Height M", 0.030, 0.010, 0.080)
    add_float_param(tree, "Platter Radius M", 0.160, 0.080, 0.240)
    add_float_param(tree, "Platter Height M", 0.022, 0.008, 0.050)
    add_float_param(tree, "Tonearm Length M", 0.230, 0.120, 0.340)
    add_float_param(tree, "Tonearm Radius M", 0.009, 0.004, 0.020)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    W = gin.outputs["Plinth Width M"]
    D = gin.outputs["Plinth Depth M"]
    PH = gin.outputs["Plinth Height M"]
    FH = gin.outputs["Foot Height M"]
    PR = gin.outputs["Platter Radius M"]
    PTH = gin.outputs["Platter Height M"]
    TL = gin.outputs["Tonearm Length M"]
    TR = gin.outputs["Tonearm Radius M"]

    half_w = _m(tree, "MULTIPLY", (bx - 2400, by - 200), W, 0.5)
    half_d = _m(tree, "MULTIPLY", (bx - 2400, by - 340), D, 0.5)
    top = _m(tree, "ADD", (bx - 2400, by - 480), FH, PH)
    deck_x = _m(tree, "MULTIPLY", (bx - 2400, by - 620), W, -0.10)
    arm_x = _m(tree, "MULTIPLY", (bx - 2400, by - 760), W, 0.30)
    arm_y = _m(tree, "MULTIPLY", (bx - 2400, by - 900), D, -0.30)
    arm_z = _m(tree, "ADD", (bx - 2400, by - 1040), top, 0.038)

    # four feet
    feet = []
    for i, (sx, sy) in enumerate(((-1.0, -1.0), (1.0, -1.0), (-1.0, 1.0), (1.0, 1.0))):
        feet.append(_cyl_z(tree, (bx - 1400 - i * 200, by - 1200),
                           0.012, FH,
                           _m(tree, "MULTIPLY", (bx - 1600 - i * 200, by - 1200),
                              FH, 0.5),
                           x=_m(tree, "MULTIPLY", (bx - 1600 - i * 200, by - 1340),
                                half_w, sx * 0.82),
                           y=_m(tree, "MULTIPLY", (bx - 1600 - i * 200, by - 1480),
                                half_d, sy * 0.82),
                           verts=12))

    plinth = _plate(tree, (bx - 1600, by), W, D, PH,
                    translation=_vec(tree, (bx - 1600, by - 200), 0.0, 0.0,
                                     _m(tree, "ADD", (bx - 1800, by - 200), FH,
                                        _m(tree, "MULTIPLY", (bx - 2000, by - 200),
                                           PH, 0.5))))

    # platter + slipmat + label
    platter = _cyl_z(tree, (bx - 1200, by - 1800), PR, PTH,
                     _m(tree, "ADD", (bx - 1400, by - 1800), top,
                        _m(tree, "MULTIPLY", (bx - 1600, by - 1800), PTH, 0.5)),
                     x=deck_x, verts=48)
    slipmat = _cyl_z(tree, (bx - 1200, by - 2000),
                     _m(tree, "MULTIPLY", (bx - 1400, by - 2000), PR, 0.97), 0.005,
                     _m(tree, "ADD", (bx - 1400, by - 2000), top,
                        _m(tree, "ADD", (bx - 1600, by - 2000), PTH, 0.0025)),
                     x=deck_x, verts=48)
    label = _cyl_z(tree, (bx - 1200, by - 2200),
                   _m(tree, "MULTIPLY", (bx - 1400, by - 2200), PR, 0.26), 0.007,
                   _m(tree, "ADD", (bx - 1400, by - 2200), top,
                      _m(tree, "ADD", (bx - 1600, by - 2200), PTH, 0.006)),
                   x=deck_x, verts=32)

    # tonearm: pivot post, tube, headshell, counterweight.
    # Probed per-part: the pivot post sits at +0.30 W with the tube running
    # toward -X for its whole length, so the tube spans x [-0.095, 0.135] and
    # the headshell lands at x -0.095 — both INSIDE the platter's [-0.205, 0.115]
    # and at y -0.108 against the platter's [-0.16, 0.16]. The arm really does
    # swing over the record, which is the thing to prove: a pivot with the tube
    # pointing the other way would read as a stub sticking off the deck.
    pivot = _cyl_z(tree, (bx - 1200, by - 2400), 0.017, 0.040,
                   _m(tree, "ADD", (bx - 1400, by - 2400), top, 0.020),
                   x=arm_x, y=arm_y, verts=16)
    arm = _cyl_x(tree, (bx - 1200, by - 2600), TR, TL,
                 _m(tree, "SUBTRACT", (bx - 1400, by - 2600), arm_x,
                    _m(tree, "MULTIPLY", (bx - 1600, by - 2600), TL, 0.5)),
                 y=arm_y, z=arm_z)
    headshell = _plate(tree, (bx - 1200, by - 2800), 0.030, 0.020, 0.014,
                       translation=_vec(tree, (bx - 1400, by - 2800),
                                        _m(tree, "SUBTRACT", (bx - 1600, by - 2800),
                                           arm_x, TL),
                                        arm_y,
                                        _m(tree, "SUBTRACT", (bx - 1600, by - 2940),
                                           arm_z, 0.006)))
    weight = _cyl_x(tree, (bx - 1200, by - 3100), 0.016, 0.028,
                    _m(tree, "ADD", (bx - 1400, by - 3100), arm_x, 0.030),
                    y=arm_y, z=arm_z)

    # pitch fader + cap, start/stop
    slot = _plate(tree, (bx - 1000, by - 3400), 0.014, 0.110, 0.006,
                  translation=_vec(tree, (bx - 1200, by - 3400),
                                   _m(tree, "MULTIPLY", (bx - 1400, by - 3400),
                                      half_w, 0.80),
                                   _m(tree, "MULTIPLY", (bx - 1400, by - 3540),
                                      half_d, 0.52),
                                   _m(tree, "ADD", (bx - 1400, by - 3680), top, 0.003)))
    fader = _plate(tree, (bx - 1000, by - 3900), 0.020, 0.022, 0.012,
                   translation=_vec(tree, (bx - 1200, by - 3900),
                                    _m(tree, "MULTIPLY", (bx - 1400, by - 3900),
                                       half_w, 0.80),
                                    _m(tree, "MULTIPLY", (bx - 1400, by - 4040),
                                       half_d, 0.22),
                                    _m(tree, "ADD", (bx - 1400, by - 4180), top, 0.010)))
    startstop = _plate(tree, (bx - 1000, by - 4400), 0.048, 0.032, 0.010,
                       translation=_vec(tree, (bx - 1200, by - 4400),
                                        _m(tree, "MULTIPLY", (bx - 1400, by - 4400),
                                           half_w, 0.68),
                                        _m(tree, "MULTIPLY", (bx - 1400, by - 4540),
                                           half_d, 0.84),
                                        _m(tree, "ADD", (bx - 1400, by - 4680),
                                           top, 0.005)))

    geom = _join(tree, (bx + 400, by),
                 [plinth, platter, slipmat, label, pivot, arm, headshell,
                  weight, slot, fader, startstop] + feet)

    _finish(tree, gin, gout, geom, (bx + 600, by), BID,
            _elec_attrs(tree, (bx + 400, by - 300)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Feet + Plinth", "nodes": ("Cylinder", "Cube"), "role": "geometry"},
        {"title": "Platter + Slipmat", "nodes": ("Cylinder", "Transform"), "role": "geometry"},
        {"title": "Tonearm", "nodes": ("Cylinder", "Cube"), "role": "geometry"},
        {"title": "Fader + Start/Stop", "nodes": ("Cube", "Transform"), "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_mixer
# ---------------------------------------------------------------------------

def build_music_mixer(group_name="MEL_music_mixer"):
    """Mixing console: frame on two side panels, a channel STRIP rank, a FADER
    rank, a knob rank, a VU meter row and an XLR bank.

    The strips and the faders SHARE `Strip Count` — that is the console law
    (each strip carries exactly one fader), and it is the opposite of the sheng
    double-count defect, where one count meaning "total" was applied to two rows
    that each produced the full set. The gate asserts the strip rank and the
    fader rank both trace to `Strip Count`.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_mixer"
    bx, by = 0, 0

    add_float_param(tree, "Console Width M", 0.90, 0.50, 1.40)
    add_float_param(tree, "Console Depth M", 0.50, 0.25, 0.80)
    add_float_param(tree, "Console Height M", 0.14, 0.06, 0.30)
    add_float_param(tree, "Stand Height M", 0.62, 0.35, 0.95)
    add_int_param(tree, "Strip Count", 12, 4, 32)
    add_int_param(tree, "Meter Count", 2, 1, 8)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    W = gin.outputs["Console Width M"]
    D = gin.outputs["Console Depth M"]
    H = gin.outputs["Console Height M"]
    SH = gin.outputs["Stand Height M"]

    half_w = _m(tree, "MULTIPLY", (bx - 2400, by - 200), W, 0.5)
    half_d = _m(tree, "MULTIPLY", (bx - 2400, by - 340), D, 0.5)
    top = _m(tree, "ADD", (bx - 2400, by - 480), SH, H)
    strip_span = _m(tree, "MULTIPLY", (bx - 2400, by - 620), W, 0.86)

    panels = []
    for i, sx in enumerate((-1.0, 1.0)):
        panels.append(_plate(
            tree, (bx - 1400 - i * 200, by - 800),
            0.040, _m(tree, "MULTIPLY", (bx - 1600 - i * 200, by - 800), D, 0.90),
            SH,
            translation=_vec(tree, (bx - 1600 - i * 200, by - 940),
                             _m(tree, "MULTIPLY", (bx - 1800 - i * 200, by - 940),
                                half_w, sx * 0.96),
                             0.0,
                             _m(tree, "MULTIPLY", (bx - 1800 - i * 200, by - 1080),
                                SH, 0.5))))

    console = _plate(tree, (bx - 1600, by), W, D, H,
                     translation=_vec(tree, (bx - 1600, by - 200), 0.0, 0.0,
                                      _m(tree, "ADD", (bx - 1800, by - 200), SH,
                                         _m(tree, "MULTIPLY", (bx - 2000, by - 200),
                                            H, 0.5))))

    # channel strips standing on the console top
    strip_w = _m(tree, "DIVIDE", (bx - 2400, by - 1200),
                 _m(tree, "MULTIPLY", (bx - 2600, by - 1200), strip_span, 0.72),
                 gin.outputs["Strip Count"])
    strip = _plate(tree, (bx - 1600, by - 1200), strip_w, 0.018,
                   _m(tree, "MULTIPLY", (bx - 1800, by - 1200), H, 1.55))
    strips = _rank_inst(tree, (bx - 800, by - 1200), gin.outputs["Strip Count"],
                        strip, strip_span,
                        _half_span(tree, (bx - 1000, by - 1200), strip_span),
                        axis="x",
                        y=_m(tree, "MULTIPLY", (bx - 1000, by - 1200), D, 0.12),
                        z=_m(tree, "ADD", (bx - 1000, by - 1200), top,
                             _m(tree, "MULTIPLY", (bx - 1200, by - 1200), H, 0.78)))

    # one fader per strip (same count — the console law)
    fader = _plate(tree, (bx - 1600, by - 1600), 0.013, 0.028, 0.010)
    faders = _rank_inst(tree, (bx - 800, by - 1600), gin.outputs["Strip Count"],
                        fader, strip_span,
                        _half_span(tree, (bx - 1000, by - 1600), strip_span),
                        axis="x",
                        y=_m(tree, "MULTIPLY", (bx - 1000, by - 1600), D, -0.12),
                        z=_m(tree, "ADD", (bx - 1000, by - 1600), top, 0.005))

    # one knob per strip, above the fader
    knob = _cyl_z(tree, (bx - 1600, by - 2000), 0.008, 0.016, 0.0, verts=12)
    knobs = _rank_inst(tree, (bx - 800, by - 2000), gin.outputs["Strip Count"],
                       knob, strip_span,
                       _half_span(tree, (bx - 1000, by - 2000), strip_span),
                       axis="x",
                       y=_m(tree, "MULTIPLY", (bx - 1000, by - 2000), D, -0.30),
                       z=_m(tree, "ADD", (bx - 1000, by - 2000), top, 0.008))

    # VU meter row along the back
    meter_span = _m(tree, "MULTIPLY", (bx - 2400, by - 2400), W, 0.50)
    meter = _plate(tree, (bx - 1600, by - 2400), 0.018, 0.014,
                   _m(tree, "MULTIPLY", (bx - 1800, by - 2400), H, 0.20))
    meters = _rank_inst(tree, (bx - 800, by - 2400), gin.outputs["Meter Count"],
                        meter, meter_span,
                        _half_span(tree, (bx - 1000, by - 2400), meter_span),
                        axis="x",
                        y=_m(tree, "MULTIPLY", (bx - 1000, by - 2400), D, 0.44),
                        z=_m(tree, "ADD", (bx - 1000, by - 2400), top,
                             _m(tree, "MULTIPLY", (bx - 1200, by - 2400), H, 0.14)))

    # XLR bank on the back face
    xlr = _cyl_y(tree, (bx - 1600, by - 2800), 0.010, 0.020, 0.0, verts=12)
    xlrs = _rank_inst(tree, (bx - 800, by - 2800), gin.outputs["Strip Count"],
                      xlr, strip_span,
                      _half_span(tree, (bx - 1000, by - 2800), strip_span),
                      axis="x",
                      y=_m(tree, "ADD", (bx - 1000, by - 2800), half_d, 0.010),
                      z=_m(tree, "SUBTRACT", (bx - 1000, by - 2800),
                           _m(tree, "ADD", (bx - 1200, by - 2800), SH,
                              _m(tree, "MULTIPLY", (bx - 1400, by - 2800), H, 0.5)),
                           _m(tree, "MULTIPLY", (bx - 1200, by - 2800), H, 0.10)))

    geom = _join(tree, (bx + 400, by),
                 [console, strips, faders, knobs, meters, xlrs] + panels)

    _finish(tree, gin, gout, geom, (bx + 600, by), BID,
            _elec_attrs(tree, (bx + 400, by - 300)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Panels + Console", "nodes": ("Cube", "Transform"), "role": "geometry"},
        {"title": "Channel Strips + Faders", "nodes": ("Cube", "Mesh Line", "Instance on Points"), "role": "instance"},
        {"title": "Knobs + Meters + XLR", "nodes": ("Cylinder", "Cube"), "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_sequencer
# ---------------------------------------------------------------------------

def build_music_sequencer(group_name="MEL_music_sequencer"):
    """Step sequencer: flat case, TWO step-button rows split from `Step Count`,
    an LED bar and a transport row.

    `Step Count` is the TOTAL number of steps and is SPLIT across the two rows
    with the sheng law — `front = floor(n/2 + 0.5)`, `back = n - front` — so a
    16-step setting produces 16 buttons, not 32. Neither row is fed the raw
    group input; the gate asserts both.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_sequencer"
    bx, by = 0, 0

    add_float_param(tree, "Case Width M", 0.42, 0.24, 0.70)
    add_float_param(tree, "Case Depth M", 0.22, 0.14, 0.40)
    add_float_param(tree, "Case Height M", 0.070, 0.030, 0.14)
    add_int_param(tree, "Step Count", 16, 4, 32)
    add_float_param(tree, "Step Size M", 0.024, 0.010, 0.050)
    add_float_param(tree, "Step Height M", 0.011, 0.004, 0.028)
    add_int_param(tree, "Led Count", 16, 4, 32)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    W = gin.outputs["Case Width M"]
    D = gin.outputs["Case Depth M"]
    H = gin.outputs["Case Height M"]
    SS = gin.outputs["Step Size M"]
    STH = gin.outputs["Step Height M"]
    N = gin.outputs["Step Count"]

    half_w = _m(tree, "MULTIPLY", (bx - 2400, by - 200), W, 0.5)
    half_d = _m(tree, "MULTIPLY", (bx - 2400, by - 340), D, 0.5)

    case = _plate(tree, (bx - 1600, by), W, D, H,
                  translation=_vec(tree, (bx - 1600, by - 200), 0.0, 0.0,
                                   _m(tree, "MULTIPLY", (bx - 1800, by - 200), H, 0.5)))
    step_z = _m(tree, "ADD", (bx - 2400, by - 480), H,
                _m(tree, "MULTIPLY", (bx - 2600, by - 480), STH, 0.5))

    # Step Count SPLIT across the two rows (FLOOR + SUBTRACT), never applied twice
    front = _m(tree, "FLOOR", (bx - 2400, by - 620),
               _m(tree, "ADD", (bx - 2600, by - 620),
                  _m(tree, "MULTIPLY", (bx - 2800, by - 620), N, 0.5), 0.5))
    back = _m(tree, "SUBTRACT", (bx - 2400, by - 760), N, front)

    step = _plate(tree, (bx - 1600, by - 900), SS, SS, STH)
    row_span = _m(tree, "MULTIPLY", (bx - 2400, by - 1040), W, 0.80)
    rows = []
    for i, (cnt, fy) in enumerate(((front, 0.25), (back, -0.25))):
        rows.append(_rank_inst(
            tree, (bx - 800, by - 1200 - i * 400), cnt, step, row_span,
            _half_span(tree, (bx - 1000, by - 1200 - i * 400), row_span),
            axis="x",
            y=_m(tree, "MULTIPLY", (bx - 1000, by - 1200 - i * 400), D, fy),
            z=step_z))

    # LED bar on the back lip
    led_span = _m(tree, "MULTIPLY", (bx - 2400, by - 2200), W, 0.86)
    led = _cyl_y(tree, (bx - 1600, by - 2200), 0.0045, 0.009, 0.0, verts=10)
    leds = _rank_inst(tree, (bx - 800, by - 2200), gin.outputs["Led Count"],
                      led, led_span,
                      _half_span(tree, (bx - 1000, by - 2200), led_span),
                      axis="x",
                      y=_m(tree, "MULTIPLY", (bx - 1000, by - 2200), half_d, 0.86),
                      z=_m(tree, "ADD", (bx - 1000, by - 2200), H, 0.0045))

    # transport row on the front lip
    transport = []
    for i, fx in enumerate((-0.30, -0.18, -0.06)):
        transport.append(_plate(
            tree, (bx - 1200 - i * 200, by - 2800),
            0.034, 0.024, 0.009,
            translation=_vec(tree, (bx - 1400 - i * 200, by - 2800),
                             _m(tree, "MULTIPLY", (bx - 1600 - i * 200, by - 2800),
                                half_w, fx),
                             _m(tree, "MULTIPLY", (bx - 1600 - i * 200, by - 2940),
                                half_d, -0.86),
                             _m(tree, "ADD", (bx - 1600 - i * 200, by - 3080),
                                H, 0.0045))))

    geom = _join(tree, (bx + 400, by), [case, leds] + rows + transport)

    _finish(tree, gin, gout, geom, (bx + 600, by), BID,
            _elec_attrs(tree, (bx + 400, by - 300)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Case", "nodes": ("Cube", "Transform"), "role": "geometry"},
        {"title": "Step Rows (split)", "nodes": ("Cube", "Mesh Line", "Instance on Points"), "role": "instance"},
        {"title": "LED Bar + Transport", "nodes": ("Cylinder", "Cube"), "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_sampler
# ---------------------------------------------------------------------------

def build_music_sampler(group_name="MEL_music_sampler"):
    """19" 2U rack sampler: two rack EARS, front panel, display bezel, a DATA
    WHEEL disc, a pad grid on the top face and a button row.

    The rack EARS and the DATA WHEEL are the identity — a rack unit is mounted
    by its ears and edited by its wheel, and the gate asserts both (two cubes
    whose Size X is a literal ear thickness and whose Size Z traces to
    `Rack Height M`; a disc whose Radius traces to `Wheel Radius M`).
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_sampler"
    bx, by = 0, 0

    add_float_param(tree, "Rack Width M", 0.483, 0.30, 0.70)
    add_float_param(tree, "Rack Height M", 0.088, 0.040, 0.18)
    add_float_param(tree, "Rack Depth M", 0.300, 0.15, 0.55)
    add_float_param(tree, "Foot Height M", 0.020, 0.005, 0.060)
    add_int_param(tree, "Pad Columns", 4, 2, 8)
    add_int_param(tree, "Pad Rows", 4, 2, 8)
    add_float_param(tree, "Pad Size M", 0.028, 0.010, 0.060)
    add_float_param(tree, "Display Width M", 0.160, 0.06, 0.30)
    add_float_param(tree, "Wheel Radius M", 0.035, 0.015, 0.070)
    add_int_param(tree, "Button Count", 4, 2, 10)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    W = gin.outputs["Rack Width M"]
    RH = gin.outputs["Rack Height M"]
    D = gin.outputs["Rack Depth M"]
    FH = gin.outputs["Foot Height M"]
    PS = gin.outputs["Pad Size M"]
    DW = gin.outputs["Display Width M"]
    WR = gin.outputs["Wheel Radius M"]

    half_w = _m(tree, "MULTIPLY", (bx - 2400, by - 200), W, 0.5)
    half_d = _m(tree, "MULTIPLY", (bx - 2400, by - 340), D, 0.5)
    mid_z = _m(tree, "ADD", (bx - 2400, by - 480), FH,
               _m(tree, "MULTIPLY", (bx - 2600, by - 480), RH, 0.5))
    top = _m(tree, "ADD", (bx - 2400, by - 620), FH, RH)
    front_y = _m(tree, "SUBTRACT", (bx - 2400, by - 760),
                 _m(tree, "MULTIPLY", (bx - 2600, by - 760), half_d, -1.0), 0.006)

    feet = []
    for i, (sx, sy) in enumerate(((-1.0, -1.0), (1.0, -1.0), (-1.0, 1.0), (1.0, 1.0))):
        feet.append(_cyl_z(tree, (bx - 1400 - i * 200, by - 900),
                           0.010, FH,
                           _m(tree, "MULTIPLY", (bx - 1600 - i * 200, by - 900),
                              FH, 0.5),
                           x=_m(tree, "MULTIPLY", (bx - 1600 - i * 200, by - 1040),
                                half_w, sx * 0.86),
                           y=_m(tree, "MULTIPLY", (bx - 1600 - i * 200, by - 1180),
                                half_d, sy * 0.80),
                           verts=12))

    body = _plate(tree, (bx - 1600, by), W, D, RH,
                  translation=_vec(tree, (bx - 1600, by - 200), 0.0, 0.0, mid_z))

    # rack ears — Size X a literal ear thickness, Size Z driven by Rack Height M
    ears = []
    for i, sx in enumerate((-1.0, 1.0)):
        ears.append(_plate(
            tree, (bx - 1400 - i * 200, by - 1400),
            0.024, _m(tree, "MULTIPLY", (bx - 1600 - i * 200, by - 1400), D, 0.60),
            _m(tree, "MULTIPLY", (bx - 1600 - i * 200, by - 1540), RH, 1.16),
            translation=_vec(tree, (bx - 1600 - i * 200, by - 1680),
                             _m(tree, "ADD", (bx - 1800 - i * 200, by - 1680),
                                half_w,
                                _m(tree, "MULTIPLY", (bx - 1800 - i * 200, by - 1820),
                                   sx, 0.012)),
                             0.0, mid_z)))

    panel = _plate(tree, (bx - 1200, by - 2000),
                   _m(tree, "MULTIPLY", (bx - 1400, by - 2000), W, 0.98),
                   0.012,
                   _m(tree, "MULTIPLY", (bx - 1400, by - 2140), RH, 0.84),
                   translation=_vec(tree, (bx - 1400, by - 2140), 0.0, front_y, mid_z))

    display = _plate(tree, (bx - 1200, by - 2400), DW, 0.014,
                     _m(tree, "MULTIPLY", (bx - 1400, by - 2400), RH, 0.46),
                     translation=_vec(tree, (bx - 1400, by - 2400),
                                      _m(tree, "MULTIPLY", (bx - 1600, by - 2400),
                                         half_w, -0.48),
                                      _m(tree, "SUBTRACT", (bx - 1600, by - 2540),
                                         front_y, 0.008),
                                      _m(tree, "ADD", (bx - 1600, by - 2680), FH,
                                         _m(tree, "MULTIPLY", (bx - 1800, by - 2680),
                                            RH, 0.62))))

    wheel = _cyl_y(tree, (bx - 1200, by - 2900), WR, 0.018,
                   _m(tree, "SUBTRACT", (bx - 1400, by - 2900), front_y, 0.008),
                   x=_m(tree, "MULTIPLY", (bx - 1400, by - 2900), half_w, 0.62),
                   z=_m(tree, "ADD", (bx - 1400, by - 2900), FH,
                        _m(tree, "MULTIPLY", (bx - 1600, by - 2900), RH, 0.55)),
                   verts=32)

    # pad grid on the top face, offset to the left of centre
    pad = _plate(tree, (bx - 1400, by - 3200), PS, PS,
                 _m(tree, "MULTIPLY", (bx - 1600, by - 3200), RH, 0.12))
    pads = _grid_rank(
        tree, (bx - 800, by - 3200), gin.outputs["Pad Columns"],
        gin.outputs["Pad Rows"], pad,
        _m(tree, "MULTIPLY", (bx - 1000, by - 3200), W, 0.32),
        _m(tree, "MULTIPLY", (bx - 1000, by - 3340), D, 0.28),
        cx=_m(tree, "MULTIPLY", (bx - 1000, by - 3480), W, -0.16),
        z=_m(tree, "ADD", (bx - 1000, by - 3480), top,
             _m(tree, "MULTIPLY", (bx - 1200, by - 3480), RH, 0.06)))

    # button row under the display
    btn_span = _m(tree, "MULTIPLY", (bx - 2400, by - 3600), W, 0.30)
    button = _plate(tree, (bx - 1400, by - 3600), 0.018, 0.014, 0.016)
    buttons = _rank_inst(
        tree, (bx - 800, by - 3600), gin.outputs["Button Count"], button,
        btn_span,
        _m(tree, "ADD", (bx - 1000, by - 3600),
           _m(tree, "MULTIPLY", (bx - 1200, by - 3600), half_w, -0.60),
           _half_span(tree, (bx - 1000, by - 3740), btn_span)),
        axis="x",
        y=_m(tree, "SUBTRACT", (bx - 1000, by - 3600), front_y, 0.012),
        z=_m(tree, "ADD", (bx - 1000, by - 3600), FH,
             _m(tree, "MULTIPLY", (bx - 1200, by - 3600), RH, 0.26)))

    geom = _join(tree, (bx + 400, by),
                 [body, panel, display, wheel, pads, buttons] + ears + feet)

    _finish(tree, gin, gout, geom, (bx + 600, by), BID,
            _elec_attrs(tree, (bx + 400, by - 300)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Body + Rack Ears", "nodes": ("Cube", "Cylinder"), "role": "geometry"},
        {"title": "Panel + Display + Wheel", "nodes": ("Cube", "Cylinder"), "role": "geometry"},
        {"title": "Pad Grid + Buttons", "nodes": ("Cube", "Mesh Line", "Instance on Points"), "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

register_builder(
    "MEL_music_synthesizer", build_music_synthesizer, "Synthesizer",
    "Modular rack: cheek panels + module plates + patch-jack collars + a rank "
    "of arched patch cables + keybed. Native-only.", category="music")

register_builder(
    "MEL_music_drum_machine", build_music_drum_machine, "Drum Machine",
    "Desktop case + 4x4 pad grid + 16-step LED row + rotary knobs + transport "
    "row. Native-only.", category="music")

register_builder(
    "MEL_music_turntable", build_music_turntable, "Turntable",
    "Plinth on four feet + platter + slipmat + label + tonearm (pivot, tube, "
    "headshell, counterweight) + pitch fader + start/stop. Native-only.",
    category="music")

register_builder(
    "MEL_music_mixer", build_music_mixer, "Mixing Console",
    "Frame on side panels + channel strip rank + one fader per strip + knob "
    "rank + VU meter row + XLR bank. Native-only.", category="music")

register_builder(
    "MEL_music_sequencer", build_music_sequencer, "Step Sequencer",
    "Flat case + two step-button rows split from Step Count (FLOOR + SUBTRACT) "
    "+ LED bar + transport row. Native-only.", category="music")

register_builder(
    "MEL_music_sampler", build_music_sampler, "Rack Sampler",
    "19\" 2U rack unit: rack ears + front panel + display bezel + data wheel "
    "disc + pad grid + button row. Native-only.", category="music")
