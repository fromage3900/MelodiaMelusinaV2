"""Shared helpers for the PARIS (Maison Impossible) builder family.

The family outgrew copy-and-patch preamble: paris_escher_ladder,
paris_fountain_loop and paris_daynight_facade each carry their own historical
copy of these helpers; new modules (mansard, penrose arch, metamorphosis
frieze) import from here instead.  Same functions, one implementation - a fix
to a helper now lands once instead of five times.

House conventions preserved:
  * `L(node, out_name, node, in_name)` links; `mathn`/`booln` swallow a bad
    operation name in try/except (that is WHY health scripts census ops);
  * `cube_s` routes socket-driven Size components through CombineXYZ (a vector
    socket cannot be linked per component);
  * `out_name` probes with `.get()` because `in` on a bpy collection raises;
  * optional geometry uses the NOT + DeleteGeometry pattern (no hidden stubs).
"""

from __future__ import annotations

import math

from .core import safe_node, link_sockets

TAU = math.pi * 2.0
HALF_PI = math.pi * 0.5


def _sock(val, prefer=None):
    """Resolve `val` to a SOCKET: nodes have `.outputs` and resolve to their
    `prefer` output (or output 0); sockets pass through untouched.

    House bug class this kills: passing a NODE (e.g. a CombineXYZ) where a
    socket is expected - NodeLinks.new then fails and the link is silently
    dropped (recorded, build still green)."""
    if hasattr(val, 'outputs'):
        try:
            if prefer:
                s = val.outputs.get(prefer)
                if s is not None:
                    return s
        except Exception:
            pass
        try:
            return val.outputs[0]
        except Exception:
            return val
    return val


def N(t, bl, x=0, y=0):
    return safe_node(t, bl, (x, y))


def L(t, a, sa, b, sb):
    """Link node output `sa` to node input `sb` (name or index, house style)."""
    link_sockets(t, a.outputs[sa], b.inputs[sb])


def mathn(t, op, x, y, a=None, b=None):
    n = N(t, 'ShaderNodeMath', x, y)
    try:
        n.operation = op
    except Exception:
        pass
    for idx, val in ((0, a), (1, b)):
        if val is None:
            continue
        if isinstance(val, (int, float)):
            n.inputs[idx].default_value = val
        else:
            link_sockets(t, _sock(val), n.inputs[idx])
    return n


def booln(t, op, x, y, a=None):
    n = N(t, 'FunctionNodeBooleanMath', x, y)
    try:
        n.operation = op
    except Exception:
        pass
    if a is not None:
        if isinstance(a, bool):
            n.inputs[0].default_value = a
        else:
            link_sockets(t, _sock(a), n.inputs[0])
    return n


def combine(t, x, y, a=None, b=None, c=None):
    n = N(t, 'ShaderNodeCombineXYZ', x, y)
    for comp, val in (('X', a), ('Y', b), ('Z', c)):
        if val is None:
            continue
        if isinstance(val, (int, float)):
            n.inputs[comp].default_value = val
        else:
            link_sockets(t, _sock(val), n.inputs[comp])
    return n


def xform(t, x, y, src, sname='Mesh', trans=None, rot=None, scale=None):
    """Transform node. trans/rot/scale: number-tuple or SOCKET."""
    n = N(t, 'GeometryNodeTransform', x, y)
    link_sockets(t, src.outputs[sname], n.inputs['Geometry'])
    for key, val in (('Translation', trans), ('Rotation', rot), ('Scale', scale)):
        if val is None:
            continue
        if isinstance(val, (tuple, list)):
            n.inputs[key].default_value = tuple(val)
        else:
            link_sockets(t, _sock(val, 'Vector'), n.inputs[key])
    return n


def cyl(t, x, y, radius, depth, verts=24):
    n = N(t, 'GeometryNodeMeshCylinder', x, y)
    for key, val in (('Radius', radius), ('Depth', depth)):
        if isinstance(val, (int, float)):
            n.inputs[key].default_value = float(val)
        else:
            link_sockets(t, _sock(val), n.inputs[key])
    n.inputs['Vertices'].default_value = verts
    return n


def cone(t, x, y, r_bottom, r_top, depth, verts=24):
    """Mesh cone, centred on origin (translate +depth/2 to sit its base at z=0).
    Socket names verified against aesthetic_fx.py usage in this addon."""
    n = N(t, 'GeometryNodeMeshCone', x, y)
    for key, val in (('Radius Bottom', r_bottom), ('Radius Top', r_top),
                     ('Depth', depth)):
        if isinstance(val, (int, float)):
            n.inputs[key].default_value = float(val)
        else:
            link_sockets(t, _sock(val), n.inputs[key])
    n.inputs['Vertices'].default_value = verts
    return n


def sphere(t, x, y, radius):
    n = N(t, 'GeometryNodeMeshUVSphere', x, y)
    if isinstance(radius, (int, float)):
        n.inputs['Radius'].default_value = float(radius)
    else:
        link_sockets(t, _sock(radius), n.inputs['Radius'])
    n.inputs['Segments'].default_value = 12
    n.inputs['Rings'].default_value = 8
    return n


def cube_s(t, x, y, sx=None, sy=None, sz=None, base=(0.1, 0.1, 0.1)):
    """Cube whose Size components may be numbers or SOCKETS.  A vector input
    socket cannot be linked per-component, so socket components route through
    a CombineXYZ and the whole vector is linked to Size."""
    n = N(t, 'GeometryNodeMeshCube', x, y)
    vals = (sx, sy, sz)
    if any(v is not None and not isinstance(v, (int, float)) for v in vals):
        comb = N(t, 'ShaderNodeCombineXYZ', x - 220, y)
        for comp, bval, val in zip(('X', 'Y', 'Z'), base, vals):
            if val is None:
                comb.inputs[comp].default_value = float(bval)
            elif isinstance(val, (int, float)):
                comb.inputs[comp].default_value = float(val)
            else:
                link_sockets(t, _sock(val), comb.inputs[comp])
        link_sockets(t, comb.outputs['Vector'], n.inputs['Size'])
    else:
        n.inputs['Size'].default_value = base
        for i, val in enumerate(vals):
            if val is not None:
                n.inputs['Size'].default_value[i] = val
    return n


def ring_points(t, x, y, count, radius, zpos):
    """Points evenly around a circle, count from a SOCKET.

    MeshLine (zero offset) gives `count` points at the origin; a SetPosition
    OFFSET then places point `i` at angle i * (TAU/count) on the circle:
    (cos*r, sin*r, z).  count / radius / z may each be number or socket.
    Returns (set_position_node, angle_socket) - callers that need per-instance
    orientation reuse the angle chain.
    """
    line = N(t, 'GeometryNodeMeshLine', x, y)
    try:
        line.mode = 'OFFSET'
    except Exception:
        pass
    if isinstance(count, (int, float)):
        line.inputs['Count'].default_value = int(count)
    else:
        link_sockets(t, count, line.inputs['Count'])
    line.inputs['Offset'].default_value = (0.0, 0.0, 0.0)

    idx = N(t, 'GeometryNodeInputIndex', x, y + 140)
    step = mathn(t, 'DIVIDE', x + 200, y + 140, TAU, count)
    ang = mathn(t, 'MULTIPLY', x + 340, y + 140, idx.outputs['Index'],
                step.outputs[0])
    cosn = mathn(t, 'COSINE', x + 480, y + 200, ang.outputs[0])
    sinn = mathn(t, 'SINE', x + 480, y + 60, ang.outputs[0])
    rx = mathn(t, 'MULTIPLY', x + 620, y + 200, cosn.outputs[0], radius)
    ry = mathn(t, 'MULTIPLY', x + 620, y + 60, sinn.outputs[0], radius)
    off = combine(t, x + 760, y + 140, rx.outputs[0], ry.outputs[0], zpos)
    sp = N(t, 'GeometryNodeSetPosition', x + 900, y + 140)
    L(t, line, 'Mesh', sp, 'Geometry')
    L(t, off, 'Vector', sp, 'Offset')
    return sp, ang.outputs[0]


def gn_line(t, gin, x, y, count, start, offset):
    """MeshLine in OFFSET mode - the house line pattern.

    count: int, math-node, or the NAME of a group-input param (str).
    start / offset: CombineXYZ nodes (always vectors - a bare float linked to
    a vector socket broadcasts to (v, v, v), which silently puts lines on the
    wrong axis)."""
    line = N(t, 'GeometryNodeMeshLine', x, y)
    try:
        line.mode = 'OFFSET'
    except Exception:
        pass
    if isinstance(count, int):
        line.inputs['Count'].default_value = count
    elif isinstance(count, str):
        L(t, gin, count, line, 'Count')
    else:
        link_sockets(t, _sock(count), line.inputs['Count'])
    link_sockets(t, _sock(start, 'Vector'), line.inputs['Start Location'])
    link_sockets(t, _sock(offset, 'Vector'), line.inputs['Offset'])
    return line


def out_name(node, *names):
    """First existing output socket name on `node` (bpy collections raise
    KeyError on `in`, so probe with .get())."""
    for nm in names:
        try:
            if node.outputs.get(nm) is not None:
                return nm
        except Exception:
            pass
    return names[0]


def inst_realize(t, x, y, points, template, sname='Mesh', rot=None, scale=None,
                 trans=None):
    """Instance `template` on points and realize. rot/scale/trans: number
    tuple, socket, or None.  Points may carry 'Geometry' (SetPosition) or
    'Mesh' (MeshLine) outputs."""
    inst = N(t, 'GeometryNodeInstanceOnPoints', x, y)
    L(t, points, out_name(points, 'Geometry', 'Mesh', 'Points'), inst, 'Points')
    L(t, template, sname, inst, 'Instance')
    for key, val in (('Rotation', rot), ('Scale', scale)):
        if val is None:
            continue
        if isinstance(val, (tuple, list)):
            inst.inputs[key].default_value = tuple(val)
        else:
            link_sockets(t, _sock(val, 'Vector'), inst.inputs[key])
    out = inst
    if trans is not None:
        tr = N(t, 'GeometryNodeTranslateInstances', x + 140, y - 160)
        L(t, inst, 'Instances', tr, 'Instances')
        if isinstance(trans, (tuple, list)):
            tr.inputs['Translation'].default_value = tuple(trans)
        else:
            link_sockets(t, _sock(trans, 'Vector'), tr.inputs['Translation'])
        out = tr
    real = N(t, 'GeometryNodeRealizeInstances', x + 300, y)
    L(t, out, 'Instances', real, 'Geometry')
    return real


def not_less(t, x, y, const_k, socket):
    """True when the socket is <= const_k (slot const_k is OUT of range).
    LESS_THAN + NOT - both proven ops in this house."""
    lt = mathn(t, 'LESS_THAN', x, y, const_k, socket)
    return booln(t, 'NOT', x + 140, y, lt.outputs[0])


def vmath(t, op, x, y, a=None, b=None):
    n = N(t, 'ShaderNodeVectorMath', x, y)
    try:
        n.operation = op
    except Exception:
        pass
    for idx, val in ((0, a), (1, b)):
        if val is None:
            continue
        if isinstance(val, (tuple, list)):
            n.inputs[idx].default_value = tuple(val)
        else:
            link_sockets(t, val, n.inputs[idx])
    return n


def guard_off(t, x, y, toggle_socket, geom_node, sname='Geometry'):
    """Optional-geometry house pattern: DeleteGeometry on NOT <toggle>."""
    not_t = booln(t, 'NOT', x, y, toggle_socket)
    d = N(t, 'GeometryNodeDeleteGeometry', x + 160, y - 140)
    L(t, geom_node, sname, d, 'Geometry')
    L(t, not_t, 0, d, 'Selection')
    return d
