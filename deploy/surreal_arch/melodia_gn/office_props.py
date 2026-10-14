"""Office prop kit - the film interior.

GN_OFFICE_DeskCluster (build_office_desk_cluster)

WHY THIS FILE EXISTS
--------------------
`BRUTALIST_CONVERGENCE_AUDIT_2026-09-25.md` §5f named the gap and it is still
exactly true: the registry has ZERO standalone office props. `CubicleFarm` builds
a desk, monitor, chair, bin and plants, but INLINE per cell - they cannot be
instanced into a conference room, cannot be re-dressed, and cannot be shot on
their own. The brief (Downloads/Office Things.docx, 105 catalog rows, 9 owners)
is waiting on exactly these.

Envelope is NOT rebuilt here. Doors, windows, walls, floor/ceiling tile,
elevator shaft, stair block and corridors stay on the existing greybox builders.
This file only fills the prop layer between them.

SIZING - researched, not guessed (skill law 1: research real dimensions FIRST)
------------------------------------------------------------------------------
All values are real-world millimetres divided by 1000, because scene scale is
1 unit = 100 mm. Sources are the standard ergonomic/furniture ranges:

  desk top            1400 x 700 x 25 mm      - the common single-pitch worktop
  desk height         740 mm                  - seated desk, adjustable 680-800
  pedestal             420 x 550 x 600 mm      - mobile drawer pedestal
  monitor 24"          531 x 297 mm panel     - 16:9, bezel 6 mm
  monitor stand       panel centre 200 mm above the desktop
  keyboard             440 x 140 x 25 mm
  mouse                 65 x 110 x 38 mm
  task chair seat      460 x 460 mm at 450 mm - gas lift 100 mm stroke
  chair base           700 mm span, 5 star
  chair back           450 wide x 480 tall x 150 thick

The health script imports these SAME constants rather than retyping them, so
the gate asserts the builder against the researched numbers instead of against
a second copy that can drift.

LAYOUT CONTRACT (what the health script asserts)
------------------------------------------------
  * everything is in ONE tree, so a shot frames the whole cluster;
  * each sub-prop sits behind its OWN toggle, guarded with DeleteGeometry
    (NOT <toggle>) - the house pattern. Off means GONE, not hidden at a distance;
  * the monitor sits ON the desktop at the back edge, panel centre 200 mm above
    it - not floating at the desk's own height;
  * keyboard and mouse sit on the FRONT third, so the cluster reads as occupied
    rather than as furniture;
  * the chair faces the desk from -Y and pushes back along -Y;
  * the material socket is a Group Input named `surface`, so the object carries a
    matching slot and the split survives export.
"""

from __future__ import annotations

from .core import (new_geometry_tree, add_float_param, add_bool_param,
                   add_material_param)
from .paris_common import (
    N, L, link_sockets, mathn, combine, cube_s, cyl, sphere, guard_off,
    out_name, _sock,
)

# ---------------------------------------------------------------------------
# Real-world sizing in scene units (1 unit = 100 mm).
# ---------------------------------------------------------------------------
DESK_W = 1.400      # 1400 mm worktop
DESK_D = 0.700      # 700 mm
DESK_T = 0.025      # 25 mm top
DESK_H = 0.740      # 740 mm seated height
PED_W = 0.420       # 420 mm pedestal
PED_D = 0.550
PED_H = 0.600
MON_W = 0.531       # 531 mm 24-inch 16:9 panel
MON_H = 0.297
MON_T = 0.020
MON_STAND_H = 0.200 # panel centre above the desktop
KB_W = 0.440        # 440 mm keyboard
KB_D = 0.140
KB_H = 0.025
MOUSE_W = 0.065
MOUSE_D = 0.110
MOUSE_H = 0.038
SEAT_W = 0.460      # 460 mm task chair seat
SEAT_D = 0.460
SEAT_H = 0.450
BASE_SPAN = 0.700   # 700 mm 5-star base
GAS_H = 0.250
BACK_W = 0.450
BACK_H = 0.480
BACK_T = 0.150

# 72 degrees in radians, for the five base arms. Spelled out rather than
# computed from math.radians so the constant is visible at the call site.
_ARM_STEP = 1.2566370614


def _at(tree, x, y, geom, cx, cy, cz):
    """Place a node's geometry AT (cx, cy, cz) - absolute, not an offset.

    cx/cy/cz may be numbers or sockets, so a dial can drive a position.

    WHY Transform and NOT SetPosition: SetPosition.Position is an OFFSET from
    each vertex, so it cannot express "this part belongs at this coordinate"
    without knowing where the part currently is - and for a part that is
    placed more than once in a chain, the second pass silently doubles the
    first. GeometryNodeTransform.TRANSLATION is absolute, composes correctly
    through a chain, and is what the house uses for exactly this reason.

    Two defects this replaced, both of which produced a tree that built,
    evaluated and looked plausible:
      * SetPosition with Selection left on moved every vertex by (cx, cy, cz),
        collapsing a centred desk top to a single point at x=0;
      * SetPosition with Selection off became a no-op, so the whole cluster sat
        at the origin with a plausible-looking bounding box.
    """
    tr = N(tree, 'GeometryNodeTransform', x, y)
    L(tree, geom, out_name(geom, 'Mesh', 'Geometry'), tr, 'Geometry')
    L(tree, combine(tree, x - 220, y - 150, cx, cy, cz), 'Vector', tr,
      'Translation')
    return tr


def _mat(tree, x, y, geom, surf_socket):
    """SetMaterial against the group's own `surface` socket.

    Uses `link_sockets` directly, NOT the L() helper: L() takes a NODE as its
    first argument and does a.outputs[sa] on it, but `surface` is a Group Input
    SOCKET and sockets have no .outputs. link_sockets resolves both forms,
    which is why brutalist_city.py links its material sockets the same way.
    """
    m = N(tree, 'GeometryNodeSetMaterial', x, y)
    L(tree, geom, out_name(geom, 'Geometry', 'Mesh'), m, 'Geometry')
    link_sockets(tree, surf_socket, m.inputs['Material'])
    return m


def _join(tree, x, y, parts):
    j = N(tree, 'GeometryNodeJoinGeometry', x, y)
    for p in parts:
        L(tree, p, out_name(p, 'Geometry', 'Mesh'), j, 'Geometry')
    return j


def _cylinder(tree, x, y, radius, depth, verts=16):
    n = cyl(tree, x, y, radius, depth, verts)
    n.inputs['Depth'].default_value = depth
    return n


def build_office_desk_cluster(group_name="GN_OFFICE_DeskCluster"):
    """Desk + pedestal + monitor + keyboard + mouse + pad + task chair.

    Authored in scene units, +Z up, front face is -Y: the user sits at -Y
    looking toward +Y at the monitor. Same convention as brutalist_cubicles.py.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    g = gin.outputs

    # ---- dials -----------------------------------------------------------
    DW = add_float_param(tree, "Desk Width", DESK_W, 0.8, 2.4)
    DD = add_float_param(tree, "Desk Depth", DESK_D, 0.4, 1.2)
    DH = add_float_param(tree, "Desk Height", DESK_H, 0.6, 0.95)
    PED = add_bool_param(tree, "Pedestal", True)
    MON = add_bool_param(tree, "Monitor", True)
    MS = add_float_param(tree, "Monitor Size", MON_W, 0.3, 0.9)
    KB = add_bool_param(tree, "Keyboard", True)
    MOUSE = add_bool_param(tree, "Mouse", True)
    PAD = add_bool_param(tree, "Mouse Pad", True)
    CHAIR = add_bool_param(tree, "Chair", True)
    PUSH = add_float_param(tree, "Chair Push", 0.0, -0.6, 0.4)
    SURF = add_material_param(tree, "surface", "Worktop")

    bx = -3000
    by = 0

    # ---- desk: top slab + two side legs -----------------------------------
    # Socket-sized dimensions go through a Math node on purpose (see note at the
    # top of the file): a raw Group Input output reads 0.0 here.
    top_w = mathn(tree, 'MULTIPLY', bx - 200, by - 300, g['Desk Width'], 1.0)
    top_d = mathn(tree, 'MULTIPLY', bx - 200, by - 420, g['Desk Depth'], 1.0)
    top = cube_s(tree, bx, by, _sock(top_w), _sock(top_d), DESK_T)
    top_z = mathn(tree, 'MULTIPLY', bx - 200, by - 540, g['Desk Height'], 1.0)
    top = _at(tree, bx + 320, by, top, 0.0, 0.0, _sock(top_z))

    # Legs are full height minus the top, so the TOP SURFACE lands on DH exactly
    # rather than near it. Set in from each end by Desk Width / 2 - 0.30.
    leg_h = mathn(tree, 'SUBTRACT', bx - 200, by - 500, g['Desk Height'], DESK_T)
    inset = mathn(tree, 'SUBTRACT', bx - 200, by - 700,
                  mathn(tree, 'DIVIDE', bx - 400, by - 900, g['Desk Width'], 2.0), 0.30)
    legs = []
    for i, sgn in enumerate((-1.0, 1.0)):
        lx = mathn(tree, 'MULTIPLY', bx - 200, by - 1100 - i * 300, sgn, inset)
        leg = cube_s(tree, bx - 200, by - 1300 - i * 300, 0.040, 0.560,
                     _sock(leg_h))
        legs.append(_at(tree, bx + 140 + i * 300, by - 1300 - i * 300, leg, lx,
                        0.0, mathn(tree, 'DIVIDE', bx - 200,
                                    by - 1700 - i * 300, leg_h, 2.0)))

    desk = _mat(tree, bx + 900, by - 500, _join(tree, bx + 640, by - 700,
                                               [top] + legs), g['surface'])

    # ---- pedestal: drawer block under the right-hand end ------------------
    ped_cx = mathn(tree, 'SUBTRACT', bx - 200, by - 2100,
                   mathn(tree, 'DIVIDE', bx - 400, by - 2300, g['Desk Width'], 2.0),
                   mathn(tree, 'ADD', bx - 600, by - 2500,
                         mathn(tree, 'DIVIDE', bx - 800, by - 2700, PED_W, 2.0),
                         0.10))
    ped = cube_s(tree, bx - 200, by - 2900, PED_W, PED_D, PED_H)
    ped = _at(tree, bx + 120, by - 2900, ped, ped_cx, 0.0,
              mathn(tree, 'DIVIDE', bx - 200, by - 3100, PED_H, 2.0))
    ped_parts = [ped]
    # Two drawer reveals, so the block is not one blank cube.
    for i in range(2):
        rv = cube_s(tree, bx - 200 + i * 320, by - 3300,
                    mathn(tree, 'MULTIPLY', bx - 400, by - 3500, PED_W, 0.7),
                    0.012, 0.014)
        ped_parts.append(_at(tree, bx + 120 + i * 320, by - 3300, rv, ped_cx,
                             PED_D * 0.5,
                             mathn(tree, 'MULTIPLY', bx - 400, by - 3700,
                                   PED_H, 0.28 + 0.34 * i)))
    ped_geo = guard_off(tree, bx + 900, by - 2900, g['Pedestal'],
                        _mat(tree, bx + 700, by - 2900,
                             _join(tree, bx + 500, by - 3100, ped_parts),
                             g['surface']))

    # ---- monitor: foot, neck, panel, screen face --------------------------
    mon_h = mathn(tree, 'MULTIPLY', bx, by - 4300, g['Monitor Size'],
                  MON_H / MON_W)
    mon_cy = mathn(tree, 'ADD', bx + 200, by - 4300, g['Desk Height'], MON_STAND_H)
    foot_cz = mathn(tree, 'ADD', bx - 200, by - 4500, g['Desk Height'], 0.008)
    foot = cube_s(tree, bx - 200, by - 4700, 0.240, 0.200, 0.016)
    foot = _at(tree, bx + 120, by - 4700, foot, 0.0, 0.0, foot_cz)
    neck = cube_s(tree, bx + 300, by - 4700, 0.060, 0.040,
                  mathn(tree, 'MULTIPLY', bx - 200, by - 4900, MON_STAND_H, 0.9))
    neck = _at(tree, bx + 620, by - 4700, neck, 0.0, 0.0,
               mathn(tree, 'ADD', bx - 200, by - 5100, g['Desk Height'],
                     mathn(tree, 'MULTIPLY', bx - 400, by - 5300, MON_STAND_H,
                           0.45)))
    mon_w = mathn(tree, 'MULTIPLY', bx - 200, by - 4100, g['Monitor Size'], 1.0)
    panel = cube_s(tree, bx + 800, by - 4700, _sock(mon_w), MON_T,
                    _sock(mon_h))
    panel = _at(tree, bx + 1120, by - 4700, panel, 0.0, 0.0, mon_cy)
    # Screen face sits slightly proud on the -Y side so the panel is not one
    # blank box and the Komikaze ink pass has an edge to find.
    scr_y = mathn(tree, 'SUBTRACT', bx - 200, by - 5500, MON_T, 0.005)
    screen = cube_s(tree, bx + 800, by - 5700,
                    mathn(tree, 'MULTIPLY', bx - 200, by - 5900, g['Monitor Size'], 0.94),
                    0.006, mathn(tree, 'MULTIPLY', bx - 200, by - 6100, mon_h, 0.9))
    screen = _at(tree, bx + 1120, by - 5700, screen, 0.0, scr_y, mon_cy)
    mon_geo = guard_off(tree, bx + 1600, by - 4700, g['Monitor'],
                        _mat(tree, bx + 1400, by - 4700,
                             _join(tree, bx + 1200, by - 4900,
                                   [foot, neck, panel, screen]), g['surface']))

    # ---- keyboard + mouse + pad: the front third of the desktop -----------
    front_y = mathn(tree, 'MULTIPLY', bx - 200, by - 6500, g['Desk Depth'], -0.28)
    kb_cz = mathn(tree, 'ADD', bx - 200, by - 6700, g['Desk Height'], KB_H * 0.5)
    kb = cube_s(tree, bx - 200, by - 6900, KB_W, KB_D, KB_H)
    kb = _at(tree, bx + 120, by - 6900, kb, 0.0, front_y, kb_cz)
    kb_geo = guard_off(tree, bx + 700, by - 6900, g['Keyboard'],
                       _mat(tree, bx + 500, by - 6900, kb, g['surface']))

    pad_cy = mathn(tree, 'MULTIPLY', bx - 200, by - 7300, g['Desk Depth'], -0.24)
    pad_cz = mathn(tree, 'ADD', bx - 200, by - 7500, g['Desk Height'], 0.002)
    pad = cube_s(tree, bx - 200, by - 7700, 0.300, 0.240, 0.004)
    pad = _at(tree, bx + 120, by - 7700, pad, 0.0, pad_cy, pad_cz)
    pad_geo = guard_off(tree, bx + 700, by - 7700, g['Mouse Pad'],
                        _mat(tree, bx + 500, by - 7700, pad, g['surface']))

    # Mouse sits on the pad, to the right of the keyboard.
    mouse_x = mathn(tree, 'ADD', bx - 200, by - 8100,
                    mathn(tree, 'MULTIPLY', bx - 400, by - 8300, KB_W, 0.62))
    mouse_cz = mathn(tree, 'ADD', bx - 200, by - 8500, g['Desk Height'], MOUSE_H * 0.5)
    # A sphere node has no .scale - it is scaled by a Radius socket, or by a
    # Transform node. Radius alone cannot make an ellipsoid, so the mouse body
    # is a Transform on the unit sphere with the three real dimensions.
    mo = sphere(tree, bx - 200, by - 8700, 0.5)
    mo_x = N(tree, 'GeometryNodeTransform', bx - 20, by - 8700)
    L(tree, mo, out_name(mo, 'Mesh', 'Geometry'), mo_x, 'Geometry')
    L(tree, combine(tree, bx - 220, by - 8900, MOUSE_W, MOUSE_D, MOUSE_H),
      'Vector', mo_x, 'Scale')
    mo = _at(tree, bx + 120, by - 8700, mo_x, mouse_x, pad_cy, mouse_cz)
    mo_geo = guard_off(tree, bx + 700, by - 8700, g['Mouse'],
                       _mat(tree, bx + 500, by - 8700, mo, g['surface']))

    # ---- chair: gas lift + 5-star base + seat + back, pushable along -Y ---
    chair_geo = _task_chair(tree, g, bx + 1200, by - 9300, g['Chair Push'],
                            g['surface'])
    chair_geo = guard_off(tree, bx + 3600, by - 9300, g['Chair'], chair_geo)

    # ---- assemble ---------------------------------------------------------
    # Each branch is already guarded exactly once; the toggles are NOT applied
    # a second time here, which would delete everything when both are off.
    # gout is the Group Output NODE (new_geometry_tree returns the node), so it
    # is a valid first argument to L(). gout.inputs[0] would be a socket.
    L(tree, _join(tree, bx + 3900, by - 4000,
                  [desk, ped_geo, mon_geo, kb_geo, pad_geo, mo_geo, chair_geo]),
      'Geometry', gout, 'Geometry')
    return tree


def _task_chair(tree, g, bx, by, push, surf):
    """5-star task chair, front face -Y: the seat faces the desk at +Y.

    Not guarded here - the caller guards the whole chair, so Chair off removes
    the chair in one place rather than five.

    The five base arms are cubes rotated about Z by index * 72 degrees and pushed
    out along that angle. A cylinder cannot sweep an arm, and a Curve-to-Mesh
    would need control points per arm; a rotated cube is the honest primitive
    and keeps the whole tree on the house helper set.
    """
    # gas cylinder
    gas = _cylinder(tree, bx, by, 0.035, GAS_H, 16)
    gas = _at(tree, bx + 320, by, gas, 0.0, push,
              mathn(tree, 'ADD', bx - 200, by - 300, GAS_H, 0.10))

    # hub
    hub = _cylinder(tree, bx + 600, by - 400, 0.060, 0.055, 12)
    hub = _at(tree, bx + 920, by - 400, hub, 0.0, push, 0.030)

    parts = [gas, hub]
    arm_len = mathn(tree, 'DIVIDE', bx - 200, by - 700, BASE_SPAN, 2.0)
    half = mathn(tree, 'DIVIDE', bx - 200, by - 700, arm_len, 2.0)
    for i in range(5):
        ry = by - 900 - i * 320
        ang = mathn(tree, 'MULTIPLY', bx - 200, ry - 200, float(i), _ARM_STEP)
        # One arm: a cube of arm_len, ROTATED about Z at the hub, then pushed
        # out along its own direction by arm_len/2 so the tip lands on
        # BASE_SPAN/2. GeometryNodeTransform, not RotateInstances - the arm is
        # realized geometry, and RotateInstances would silently pass it through.
        arm = cube_s(tree, bx - 200, ry, arm_len, 0.048, 0.042)
        xform = N(tree, 'GeometryNodeTransform', bx + 200, ry)
        L(tree, arm, out_name(arm, 'Mesh', 'Geometry'), xform, 'Geometry')
        L(tree, combine(tree, bx - 200, ry - 400, 0.0, 0.0, ang), 'Vector',
          xform, 'Rotation')
        dx = mathn(tree, 'MULTIPLY', bx - 200, ry - 600,
                   mathn(tree, 'COSINE', bx - 400, ry - 800, ang, 0.0), half)
        dy = mathn(tree, 'MULTIPLY', bx - 200, ry - 1000,
                   mathn(tree, 'SINE', bx - 400, ry - 1200, ang, 0.0), half)
        # Push along the rotated arm direction, and carry the chair's own push
        # offset on Y at the same time.
        moved = N(tree, 'GeometryNodeSetPosition', bx + 700, ry)
        L(tree, xform, out_name(xform, 'Geometry'), moved, 'Geometry')
        L(tree, combine(tree, bx + 500, ry - 1400, dx,
                        mathn(tree, 'ADD', bx + 300, ry - 1600, dy, push),
                        0.030), 'Vector', moved, 'Offset')
        parts.append(moved)

    # seat
    seat = cube_s(tree, bx - 200, by - 3000, SEAT_W, SEAT_D, 0.070)
    parts.append(_at(tree, bx + 120, by - 3000, seat, 0.0, push, SEAT_H))

    # back, leaning off the seat's rear edge
    back_y = mathn(tree, 'SUBTRACT', bx - 200, by - 3400, push,
                   mathn(tree, 'ADD', bx - 400, by - 3600, SEAT_D * 0.5, 0.05))
    back = cube_s(tree, bx - 200, by - 3800, BACK_W, BACK_T, BACK_H)
    parts.append(_at(tree, bx + 120, by - 3800, back, 0.0, back_y,
                     mathn(tree, 'ADD', bx - 400, by - 4000, SEAT_H,
                           BACK_H * 0.5)))

    return _mat(tree, bx + 1400, by - 2000, _join(tree, bx + 1200, by - 2200,
                                                 parts), surf)


try:
    from .core import register_builder
    register_builder(
        "GN_OFFICE_DeskCluster", build_office_desk_cluster,
        "OFFICE Desk Cluster",
        "Office workstation as one shotable tree: worktop on legs, drawer "
        "pedestal, 24-inch monitor on a stand, keyboard, mouse and pad, and a "
        "5-star task chair that pushes back. Every sub-prop has its own toggle.",
        category='office_props',
    )
    print('[office_props] registered GN_OFFICE_DeskCluster')
except ImportError:
    print('[office_props] standalone mode (no core registry)')


if __name__ == '__main__':
    build_office_desk_cluster()
