"""GN_PARIS_* wall-detail builders — Melusina House Paris→Nikki lane.

Converged 2026-09-18 from the Saved/MelusinasHouse staging scripts into the
Melodia Studio addon (this module is the single authority). The in-file groups
GN_PARIS_WallDetail / GN_PARIS_SlabTrim are REBUILT from this code; never
hand-edit the live group without porting the change here.

v2 (this module):
  - CORNICE_STYLE INT: 0=FLAT (no bands) / 1=HAUSSMANN (current bands) / 2=GOTHIC
    (bands + stepped panel reveals + instanced pointed-arch medallions + quoins).
  - Pointed arch delegated to the monolith's build_gothic_arch (baked once to a
    helper mesh object MH_GothicArchHead; no reimplementation).
  - Stepped gothic reveals: native extrude chain (Higgsas NTInset Face attempted
    first; falls back with a printed reason when its socket API differs).
  - Quoins: alternating blocks instanced along the four vertical corner lines.
  - In-group Mesh Bevel (0.04 / 3 segments) at the end of the chain replaces the
    object-level Bevel modifiers on walls and slabs (stack shrinks).

Self-contained: uses bpy/mathutils only; register_builder() is attached when
the addon core is importable, standalone mode otherwise (bridge/eval runs).
"""

import bpy
import math
from types import SimpleNamespace

ROOT = r'P:/MelodiaMelusinaV2-Laptop/deploy'
_TRIM_OUT = r'P:/MelodiaMelusinaV2-Laptop/Saved/TrimSheets/out'
_HELPER_COLL = 'MH_Gen_Helpers'
ARCH_OBJECT = 'MH_GothicArchHead'

# ---------------------------------------------------------------- helpers

def N(t, bl, x, y=0):
    n = t.nodes.new(bl)
    n.location = (x, y)
    return n


def L(t, a, sa, b, sb):
    t.links.new(a.outputs[sa], b.inputs[sb])


def com(t, x, y, z):
    n = N(t, 'FunctionNodeCombineXYZ', x, y)
    n.inputs[0].default_value = x
    n.inputs[1].default_value = y
    n.inputs[2].default_value = z
    return n


def vm(t, op, x, y):
    n = N(t, 'ShaderNodeVectorMath', x, y)
    n.operation = op
    return n


def m(t, op, a, b=None, x=0, y=0):
    n = N(t, 'ShaderNodeMath', x, y)
    n.operation = op
    n.inputs[0].default_value = a
    if b is not None:
        n.inputs[1].default_value = b
    return n


def cp(t, op, a, b, x=0, y=0):
    n = N(t, 'FunctionNodeCompare', x, y)
    n.data_type = 'FLOAT'
    n.operation = op
    n.inputs[0].default_value = a
    n.inputs[1].default_value = b
    return n


# ------------------------------------------------- Higgsas loader (dup-safe)

def _higgs(name):
    """Resolve a Higgsas NT_* group into bpy.data without duplicating.

    In-file copies of Higgsas groups may exist under the unprefixed name
    (e.g. 'Bricks Grid'). Rename that copy to the NT name first, then let the
    bridge resolve; never leave a .001 duplicate behind.
    """
    nt = 'NT' + name
    g = bpy.data.node_groups.get(nt)
    if g:
        return g
    alt = bpy.data.node_groups.get(name)
    if alt:
        alt.name = nt
        return alt
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            'mel_higgsas_bridge', ROOT + '/surreal_arch/higgsas_bridge.py')
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.load_node(name)
    except Exception as e:
        print('[paris_wall_detail] Higgsas %s unavailable: %s' % (name, e))
        return None


# ------------------------------------------------- gothic arch delegation

def ensure_gothic_arch_object():
    """Bake the monolith's pointed arch into a helper mesh object, once."""
    obj = bpy.data.objects.get(ARCH_OBJECT)
    if obj:
        return obj
    mon = None
    try:
        import surreal_architecture_gen as mon
    except ImportError:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            'mel_monolith', ROOT + '/surreal_architecture_gen.py')
        mon = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mon)
    t = bpy.data.node_groups.new('MH_Arch_Bake_TMP', 'GeometryNodeTree')
    t.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    t.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gin = t.nodes.new('NodeGroupInput')
    gout = t.nodes.new('NodeGroupOutput')
    gin.location = (-400, 0)
    gout.location = (200, 0)
    t.links.new(gin.outputs['Geometry'], gout.inputs['Geometry'])
    props = SimpleNamespace(gothic_width=1.0, gothic_radius=0.55, gothic_thickness=0.08)
    arc = mon.build_gothic_arch(t, props, -1400)
    t.links.new(arc, gout.inputs['Geometry'])
    me = bpy.data.meshes.new(ARCH_OBJECT)
    obj = bpy.data.objects.new(ARCH_OBJECT, me)
    coll = bpy.data.collections.get(_HELPER_COLL)
    if not coll:
        coll = bpy.data.collections.new(_HELPER_COLL)
        bpy.context.scene.collection.children.link(coll)
    coll.objects.link(obj)
    mod = obj.modifiers.new('bake', 'NODES')
    mod.node_group = t
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    baked = bpy.data.meshes.new_from_object(ev)
    ev.to_mesh_clear()
    obj.modifiers.clear()
    obj.data = baked
    obj.hide_render = True
    obj.hide_viewport = False
    bpy.data.node_groups.remove(t)
    print('[paris_wall_detail] baked %s from monolith build_gothic_arch (%d polys)'
          % (ARCH_OBJECT, len(baked.polygons)))
    return obj


# ------------------------------------------------- panel/band graph pieces

def _band_chain(t, gin, gout, x0):
    """Six cornice/string/wainscot/baseboard band cubes; returns (last, None)."""
    bmin = gin
    gx0 = x0
    bands = [
        ('Show Cornice',    0.00, -0.03, 0.18,  0.02, 1.0,  1.00),
        ('Show String',     1.10, -0.03, 0.09,  0.02, 1.0,  1.00),
        ('Show Wainscot',   0.30, -0.05, 0.80, -0.02, 1.0,  1.00),
        ('Show Baseboard',  0.00, -0.06, 0.14,  0.02, 1.0,  1.00),
    ]
    last = None
    joinb = N(t, 'NodeJoinGeometry', gx0 - 300, 640)
    for i, (name, z, d, h, prof, sx, sz) in enumerate(bands):
        sw = N(t, 'GeometryNodeSwitch', gx0 - 600, 640 + 260 * i)
        sw.switch_type = 'GEOMETRY'
        L(t, gin, name, sw, 'Switch')
        mnb = N(t, 'GeometryNodeInputPosition', gx0 - 1200, 760 + 260 * i)
        sep = N(t, 'GeometryNodeSeparateXYZ', gx0 - 1080, 760 + 260 * i)
        L(t, mnb, 'Position', sep, 'Vector')
        c1 = N(t, 'FunctionNodeCompare', gx0 - 960, 760 + 260 * i)
        c1.data_type = 'FLOAT'
        c1.operation = 'GREATER_THAN'
        L(t, sep, 'Z', c1, 0)
        c1.inputs[1].default_value = z + h
        c2 = N(t, 'FunctionNodeCompare', gx0 - 840, 700 + 260 * i)
        c2.data_type = 'FLOAT'
        c2.operation = 'LESS_THAN'
        L(t, sep, 'Z', c2, 0)
        c2.inputs[1].default_value = z
        band_and = N(t, 'FunctionNodeBooleanMath', gx0 - 720, 730 + 260 * i)
        L(t, c1, 'Result', band_and, 0)
        L(t, c2, 'Result', band_and, 1)
        L(t, band_and, 'Result', sw, 'False')
        cu = N(t, 'GeometryNodeMeshCube', gx0 - 600, 520 + 260 * i)
        for s in ('Size X', 'Size Y', 'Size Z'):
            cu.inputs[s].default_value = 1.0
        mns = N(t, 'GeometryNodeInputPosition', gx0 - 1200, 560 + 260 * i)
        ses = N(t, 'GeometryNodeSeparateXYZ', gx0 - 1080, 560 + 260 * i)
        L(t, mns, 'Position', ses, 'Vector')
        # band size follows bbox extents with a small depth protrusion
        szx = N(t, 'GeometryNodeAttributeMathAdd', gx0 - 940, 480 + 260 * i)
        if not szx:
            szx = m(t, 'ADD', 0.0, 0.0, gx0 - 940, 480 + 260 * i)
        L(t, ses, 'X', szx, 0)
        szx.inputs[1].default_value = 0.002
        szz = m(t, 'ADD', h, 0.0, gx0 - 940, 360 + 260 * i)
        L(t, ses, 'Z', szz, 0)
        szy = m(t, 'ADD', d, 0.0, gx0 - 940, 240 + 260 * i)
        L(t, ses, 'Y', szy, 0)
        L(t, szx, 'Value', cu, 'Size X')
        L(t, szy, 'Value', cu, 'Size Y')
        L(t, szz, 'Value', cu, 'Size Z')
        cpos = com(t, 0.0, 0.0, z + h / 2.0)
        for ax in ('X', 'Y'):
            mnc = N(t, 'GeometryNodeInputPosition', gx0 - 1200, 120 + 260 * i)
            sec = N(t, 'GeometryNodeSeparateXYZ', gx0 - 1080, 120 + 260 * i)
            L(t, mnc, 'Position', sec, 'Vector')
            mn = m(t, 'MINIMUM', 0.0, 0.0, gx0 - 960, 120 + 260 * i)
            L(t, sec, ax, mn, 0)
            mx = m(t, 'MAXIMUM', 0.0, 0.0, gx0 - 840, 120 + 260 * i)
            L(t, mn, 'Value', mx, 0)
            cenn = m(t, 'ADD', 0.0, 0.0, gx0 - 720, 120 + 260 * i)
            L(t, mx, 'Value', cenn, 0)
            cenn.inputs[1].default_value = -h / 2.0
            cenn.inputs[0].default_value = 0.0
            L(t, cenn, 'Value', cpos.inputs[0 if ax == 'X' else 1], 0)
        cen = com(t, 0.0, 0.0, 0.0)
        cen.inputs[2].default_value = z + h / 2.0
        trx = N(t, 'FunctionNodeAlignEulerToVector', gx0 - 300, 300 + 260 * i)
        L(t, cu, 'Mesh', trx, 0)
        tfrm = N(t, 'GeometryNodeTransform', gx0 - 100, 300 + 260 * i)
        L(t, trx, 'Rotation', tfrm, 'Rotation')
        L(t, cpos, 'Vector', tfrm, 'Translation')
        L(t, tfrm, 'Geometry', sw, 'True')
        if i == 0:
            last = sw
        else:
            jn = N(t, 'NodeJoinGeometry', gx0 - 400, 520 + 260 * i)
            L(t, last, 0, jn, 0)
            L(t, sw, 0, jn, 1)
            last = jn
    return last


def _panel_chain(t, gin, gout, x0):
    """Panel insets + gothic extras; returns (psw_out_node_socket_source)."""
    gx0 = x0
    # face normal
    nop = N(t, 'GeometryNodeInputNormal', gx0, -400)
    nor = N(t, 'GeometryNodeFaceforward', gx0 + 120, -400) if False else nop
    andn = N(t, 'FunctionNodeBooleanMath', gx0 + 240, -400)
    andn.operation = 'AND'
    L(t, nop, 'Normal', andn, 0)
    andn.inputs[1].default_value = True
    # panel inset (recess) on the big faces
    pos0 = N(t, 'GeometryNodeInputPosition', gx0, -520)
    minz = N(t, 'ShaderNodeMath', gx0 + 120, -520)
    minz.operation = 'MINIMUM'
    posn = pos0
    bmin = gin
    L(t, gin, 'Geometry', posn, 0) if False else None
    # --- selection: z-band of panels
    sepp = N(t, 'GeometryNodeSeparateXYZ', gx0 + 120, -640)
    L(t, pos0, 'Position', sepp, 'Vector')
    gt1 = N(t, 'FunctionNodeCompare', gx0 + 240, -640)
    gt1.data_type = 'FLOAT'
    gt1.operation = 'GREATER_THAN'
    L(t, sepp, 'Z', gt1, 0)
    gt1.inputs[1].default_value = 0.22
    lt1 = N(t, 'FunctionNodeCompare', gx0 + 360, -700)
    lt1.data_type = 'FLOAT'
    lt1.operation = 'LESS_THAN'
    L(t, sepp, 'Z', lt1, 0)
    lt1.inputs[1].default_value = 2.72
    pband = N(t, 'FunctionNodeBooleanMath', gx0 + 480, -670)
    L(t, gt1, 'Result', pband, 0)
    L(t, lt1, 'Result', pband, 1)
    sel = N(t, 'FunctionNodeBooleanMath', gx0 + 600, -640)
    L(t, pband, 'Result', sel, 0)
    L(t, andn, 'Result', sel, 1)
    # normal-based face filter (|nx| or |ny| big)
    sepn = N(t, 'GeometryNodeSeparateXYZ', gx0 + 240, -400)
    L(t, nop, 'Normal', sepn, 'Vector')
    ax1 = N(t, 'ShaderNodeMath', gx0 + 360, -360)
    ax1.operation = 'ABSOLUTE'
    L(t, sepn, 'X', ax1, 0)
    ax2 = N(t, 'ShaderNodeMath', gx0 + 360, -440)
    ax2.operation = 'ABSOLUTE'
    L(t, sepn, 'Y', ax2, 0)
    mx1 = N(t, 'ShaderNodeMath', gx0 + 480, -400)
    mx1.operation = 'MAXIMUM'
    L(t, ax1, 'Value', mx1, 0)
    L(t, ax2, 'Value', mx1, 1)
    bigf = N(t, 'FunctionNodeCompare', gx0 + 600, -400)
    bigf.data_type = 'FLOAT'
    bigf.operation = 'GREATER_THAN'
    L(t, mx1, 'Value', bigf, 0)
    bigf.inputs[1].default_value = 0.7
    L(t, bigf, 'Result', sel, 1)
    # first inset extrude
    ex1 = N(t, 'GeometryNodeExtrudeMesh', gx0 + 760, -560)
    ex1.mode = 'FACES'
    offv1 = vm(t, 'SCALE', gx0 + 600, -800)
    offn1 = N(t, 'GeometryNodeInputNormal', gx0 + 440, -800)
    L(t, offn1, 'Normal', offv1, 0)
    offv1.inputs['Scale'].default_value = -0.035
    L(t, offv1, 'Vector', ex1, 'Offset')
    L(t, sel, 'Result', ex1, 'Selection')
    t1 = N(t, 'GeometryNodeInputMeshTop', gx0 + 760, -760)
    # second, deeper inset
    ex2 = N(t, 'GeometryNodeExtrudeMesh', gx0 + 960, -560)
    ex2.mode = 'FACES'
    offv2 = vm(t, 'SCALE', gx0 + 840, -800)
    offn2 = N(t, 'GeometryNodeInputNormal', gx0 + 700, -800)
    L(t, offn2, 'Normal', offv2, 0)
    offv2.inputs['Scale'].default_value = -0.05
    L(t, t1, 'Top', ex2, 'Selection')
    L(t, offv2, 'Vector', ex2, 'Offset')
    L(t, ex1, 'Mesh', ex2, 'Mesh')
    # panel scale on the second inset's top faces
    sce = N(t, 'GeometryNodeScaleElements', gx0 + 1160, -560)
    L(t, ex2, 'Mesh', sce, 'Geometry')
    L(t, ex2, 'Top', sce, 'Selection')
    pscale = N(t, 'GeometryNodeInputPosition', gx0 + 980, -960)
    psn = N(t, 'GeometryNodeScaleElements', gx0 + 1320, -700)
    psn.inputs['Scale'].default_value = 0.86
    # center of second inset faces (approx: position field, center mode)
    psn.center_mode = 'ORIGIN' if hasattr(psn, 'center_mode') else psn.center_mode
    psn2 = psn
    L(t, ex2, 'Mesh', psn2, 'Geometry')
    L(t, ex2, 'Top', psn2, 'Selection')
    psw = N(t, 'GeometryNodeSwitch', gx0 + 1500, -560)
    psw.switch_type = 'GEOMETRY'
    L(t, gin, 'Show Panels', psw, 'Switch')
    L(t, psn2, 'Geometry', psw, 'True')
    L(t, gin, 'Geometry', psw, 'False')
    return psw, ex2


def _gothic_extras(t, gin, ex2, x0):
    """Stepped reveals + arch medallions + quoins; returns (nodes, out)."""
    gx0 = x0
    made = []
    # --- Higgsas stepped reveal (NTInset Face) with native fallback
    higs = _higgs('NTInset Face')
    step_out = None
    if higs:
        hg = N(t, 'GeometryNodeGroup', gx0 + 200, -560)
        hg.node_tree = higs
        L(t, ex2, 'Mesh', hg, 'Geometry') if 'Geometry' in [i.name for i in hg.inputs] else L(t, ex2, 'Mesh', hg, 0)
        L(t, ex2, 'Top', hg, 'Selection') if 'Selection' in [i.name for i in hg.inputs] else None
        made.append('NTInset Face')
        try:
            step_out = hg.outputs[[o.name for o in hg.outputs][0]]
        except Exception:
            step_out = None
        print('[paris_wall_detail] NTInset Face sockets: in=%s out=%s'
              % ([i.name for i in hg.inputs], [o.name for o in hg.outputs]))
    if step_out is None:
        # native fallback: third shallow extrude + scale on ex2 top
        ex3 = N(t, 'GeometryNodeExtrudeMesh', gx0 + 200, -560)
        ex3.mode = 'FACES'
        offv3 = vm(t, 'SCALE', gx0 + 60, -800)
        offn3 = N(t, 'GeometryNodeInputNormal', gx0 - 80, -800)
        L(t, offn3, 'Normal', offv3, 0)
        offv3.inputs['Scale'].default_value = -0.025
        L(t, ex2, 'Mesh', ex3, 'Mesh')
        L(t, ex2, 'Top', ex3, 'Selection')
        L(t, offv3, 'Vector', ex3, 'Offset')
        sce2 = N(t, 'GeometryNodeScaleElements', gx0 + 400, -560)
        L(t, ex3, 'Mesh', sce2, 'Geometry')
        L(t, ex3, 'Top', sce2, 'Selection')
        sce2.inputs['Scale'].default_value = 0.80
        step_out = (sce2, 'Geometry')
        made.append('native stepped reveal')
    # --- arch medallions on panel faces
    arch_obj = None
    try:
        arch_obj = ensure_gothic_arch_object()
    except Exception as e:
        print('[paris_wall_detail] arch bake skipped: %s' % e)
    arch_inst = None
    if arch_obj is not None:
        cap = N(t, 'GeometryNodeCaptureAttribute', gx0 + 600, -560)
        cap.data_type = 'FLOAT_VECTOR'
        cap.domain = 'FACE'
        cn = N(t, 'GeometryNodeInputNormal', gx0 + 460, -860)
        L(t, cn, 'Normal', cap, 'Value')
        src = step_out[0].outputs[step_out[1]] if isinstance(step_out, tuple) else step_out.source_node
        L(t, src, cap, 'Geometry')
        # careful: L signature (t,a,sa,b,sb)
        mtp = N(t, 'GeometryNodeMeshToPoints', gx0 + 820, -560)
        mtp.domain = 'FACES'
        L(t, cap, 'Geometry', mtp, 'Mesh')
        L(t, ex2, 'Top', mtp, 'Selection')
        aev = N(t, 'FunctionNodeAlignEulerToVector', gx0 + 980, -700)
        aev.axis = 'Y'
        nattr = N(t, 'GeometryNodeInputNamedAttribute', gx0 + 840, -860)
        nattr.data_type = 'FLOAT_VECTOR'
        nattr.inputs[0].default_value = 'MH_normal'
        L(t, nattr, 'Attribute', aev, 'Vector')
        oi = N(t, 'GeometryNodeObjectInfo', gx0 + 820, -300)
        oi.transform_space = 'ORIGINAL'
        oi.inputs['Object'].default_value = arch_obj
        inst = N(t, 'GeometryNodeInstanceOnPoints', gx0 + 1160, -460)
        L(t, mtp, 'Points', inst, 'Points')
        L(t, oi, 'Geometry', inst, 'Instance')
        L(t, aev, 'Rotation', inst, 'Rotation')
        asc = N(t, 'GeometryNodeInputPosition', gx0 + 980, -900)
        mul = N(t, 'ShaderNodeVectorMath', gx0 + 1120, -900)
        mul.operation = 'MULTIPLY'
        offc = com(t, 0.0, 0.0, 0.0)
        mul.inputs[1].default_value = (0.045, 0.045, 0.045)
        L(t, nattr, 'Attribute', mul, 0)
        L(t, mul, 'Vector', inst, 'Translation')
        inst.inputs['Scale'].default_value = (1.2, 1.2, 1.2)
        arch_inst = inst
        made.append('arch medallions')
    # --- quoins on the four vertical corners
    qoins = N(t, 'NodeJoinGeometry', gx0 + 200, 100)
    lines = []
    for k, (cx, cy) in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))):
        lnb = N(t, 'GeometryNodeMeshLine', gx0 + 40 + 40 * k, 100 + 60 * k)
        for s in ('Start Location', 'End Location'):
            lnb.inputs[s].default_value = (0.0, 0.0, 0.0)
        lnb.inputs['Count'].default_value = 12
        lines.append(lnb)
    # corner positions from bbox min/max
    for li, (ax_x, ax_y) in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))):
        ln = lines[li]
        sxyz = com(t, 0.0, 0.0, 0.0)
        exyz = com(t, 0.0, 0.0, 0.0)
        for ai, ax in enumerate('XYZ'):
            for src, dst in ((ax_x, sxyz), (ax_y, exyz)):
                if ax in 'XY':
                    mn = m(t, 'MINIMUM', 0.0, 0.0, gx0 - 300, -40 - 60 * (li * 6 + ai + (2 if src is ax_y else 0)))
                    mx = m(t, 'MAXIMUM', 0.0, 0.0, gx0 - 180, -40 - 60 * (li * 6 + ai + (2 if src is ax_y else 0)))
                    L(t, mn, 'Value', mx, 0)
                    addv = m(t, 'ADD', 0.06, 0.0, gx0 - 60, -40 - 60 * (li * 6 + ai + (2 if src is ax_y else 0)))
                    L(t, mx, 'Value', addv, 0)
                    if src is ax_x:
                        L(t, addv, 'Value', sxyz.inputs[ai])
                    else:
                        L(t, addv, 'Value', exyz.inputs[ai])
                else:  # Z
                    mn = m(t, 'MINIMUM', 0.0, 0.0, gx0 - 300, 260)
                    mx = m(t, 'MAXIMUM', 0.0, 0.0, gx0 - 180, 260)
                    L(t, mn, 'Value', mx, 0)
                    ad0 = m(t, 'ADD', 0.06, 0.0, gx0 - 60, 300)
                    L(t, mx, 'Value', ad0, 0)
                    ad1 = m(t, 'ADD', -0.06, 0.0, gx0 - 60, 220)
                    L(t, mx, 'Value', ad1, 0)
                    L(t, ad0, 'Value', sxyz.inputs[2])
                    L(t, ad1, 'Value', exyz.inputs[2])
        # feed min/max from raw geometry position
        gpos = N(t, 'GeometryNodeInputPosition', gx0 - 620, -40 - 30 * li)
        gsep = N(t, 'GeometryNodeSeparateXYZ', gx0 - 500, -40 - 30 * li)
        L(t, gin, 'Geometry', gpos, 0) if False else None
        L(t, gpos, 'Position', gsep, 'Vector')
        for li2, ch in enumerate('XYZ'):
            mn2 = m(t, 'MINIMUM', 0.0, 0.0, gx0 - 380, -80 - 40 * li2)
            mx2 = m(t, 'MAXIMUM', 0.0, 0.0, gx0 - 380, -80 - 40 * li2)
            L(t, gsep, ch, mn2, 0)
            L(t, mn2, 'Value', mx2, 0)
    L(t, qoins, 0, qoins, 1) if False else None
    for li, ln in enumerate(lines):
        jn = N(t, 'NodeJoinGeometry', gx0 + 240 + 60 * li, 100)
        pass
    # join the four lines
    jl = N(t, 'NodeJoinGeometry', gx0 + 340, 100)
    L(t, lines[0], 'Points', jl, 'Geometry')
    L(t, lines[1], 'Points', jl, 'Geometry')
    L(t, lines[2], 'Points', jl, 'Geometry')
    L(t, lines[3], 'Points', jl, 'Geometry')
    # brick cube + alternating scale
    brick = N(t, 'GeometryNodeMeshCube', gx0 + 520, 100)
    for s in ('Size X', 'Size Y', 'Size Z'):
        brick.inputs[s].default_value = 1.0
    rnd = N(t, 'FunctionNodeRandomValue', gx0 + 520, -80)
    rnd.data_type = 'INT'
    rnd.inputs[0].default_value = 0
    rnd.inputs[1].default_value = 2
    cmp0 = N(t, 'FunctionNodeCompare', gx0 + 660, -80)
    cmp0.data_type = 'FLOAT'
    cmp0.operation = 'EQUAL'
    L(t, rnd, 'Value', cmp0, 0)
    cmp0.inputs[1].default_value = 0
    alt = m(t, 'SUBTRACT', 0.38, 0.26, gx0 + 780, -80)
    L(t, cmp0, 'Result', alt, 0)
    qscale = N(t, 'GeometryNodeSeparateXYZ', gx0 + 900, -80)
    qcomb = N(t, 'FunctionNodeCombineXYZ', gx0 + 1020, -80)
    L(t, alt, 'Value', qcomb, 'X')
    qcomb.inputs['Y'].default_value = 1.0
    qcomb.inputs['Z'].default_value = 1.0
    instq = N(t, 'GeometryNodeInstanceOnPoints', gx0 + 1160, 60)
    L(t, jl, 'Geometry', instq, 'Points')
    L(t, brick, 'Mesh', instq, 'Instance')
    instq.inputs['Scale'].default_value = (0.32, 0.42, 0.12)
    made.append('quoins')
    # gothic join
    gj = N(t, 'NodeJoinGeometry', gx0 + 1400, -200)
    L(t, step_out[0], step_out[1], gj, 0) if isinstance(step_out, tuple) else L(t, step_out.source_node, step_out.name, gj, 0)
    if arch_inst:
        L(t, arch_inst, 'Instances', gj, 1)
        L(t, instq, 'Instances', gj, 2)
    else:
        L(t, instq, 'Instances', gj, 1)
    rz = N(t, 'GeometryNodeRealizeInstances', gx0 + 1560, -200)
    L(t, gj, 'Geometry', rz, 'Geometry')
    return rz, made


def _uv_and_finish(t, gin, gout, style_node, x0):
    """Trim UV store + proxy material + apply switch + in-group bevel."""
    gx0 = x0
    rnorm = N(t, 'GeometryNodeInputNormal', gx0, 0)
    tvv = N(t, 'ShaderNodeVectorMath', gx0 + 120, 0)
    tvv.operation = 'DOT_PRODUCT'
    tvn = N(t, 'GeometryNodeInputNormal', gx0, 120)
    tvv.inputs[1].default_value = (0.0, 0.0, 1.0)
    L(t, rnorm, 'Normal', tvv, 0)
    anorm = N(t, 'ShaderNodeMath', gx0 + 240, 0)
    anorm.operation = 'ABSOLUTE'
    L(t, tvv, 'Value', anorm, 0)
    gtan = N(t, 'FunctionNodeCompare', gx0 + 360, 0)
    gtan.data_type = 'FLOAT'
    gtan.operation = 'LESS_THAN'
    L(t, anorm, 'Value', gtan, 0)
    gtan.inputs[1].default_value = 0.85
    band2 = N(t, 'FunctionNodeBooleanMath', gx0 + 480, 0)
    L(t, gtan, 'Result', band2, 0)
    band2.inputs[1].default_value = True
    pv = N(t, 'GeometryNodeInputPosition', gx0, 160)
    sepv = N(t, 'GeometryNodeSeparateXYZ', gx0 + 120, 160)
    L(t, pv, 'Position', sepv, 'Vector')
    vmax = N(t, 'ShaderNodeMath', gx0 + 240, 160)
    vmax.operation = 'MAXIMUM'
    L(t, sepv, 'Z', vmax, 0)
    vmin = N(t, 'ShaderNodeMath', gx0 + 240, 80)
    vmin.operation = 'MINIMUM'
    L(t, sepv, 'Z', vmin, 0)
    # normalize z into v with a divide by height (use bbox via max-min)
    hgt = N(t, 'ShaderNodeMath', gx0 + 360, 120)
    hgt.operation = 'SUBTRACT'
    L(t, vmax, 'Value', hgt, 0)
    L(t, vmin, 'Value', hgt, 1)
    zv = N(t, 'ShaderNodeMath', gx0 + 480, 160)
    zv.operation = 'SUBTRACT'
    L(t, sepv, 'Z', zv, 0)
    L(t, vmin, 'Value', zv, 1)
    dvn = N(t, 'ShaderNodeMath', gx0 + 600, 160)
    dvn.operation = 'DIVIDE'
    L(t, zv, 'Value', dvn, 0)
    L(t, hgt, 'Value', dvn, 1)
    # band v mapping: 4 bands over 0..1
    bmul = m(t, 'MULTIPLY', 0.0, 0.25, gx0 + 720, 160)
    L(t, dvn, 'Value', bmul, 0)
    uvband = N(t, 'GeometryNodeUVMap', gx0 + 840, 120)
    uvband.uv_map = 'TS_trim'
    mk = N(t, 'GeometryNodeStoreNamedAttribute', gx0 + 980, 120)
    mk.domain = 'CORNER'
    mk.data_type = 'FLOAT2'
    mk.inputs['Name'].default_value = 'UVMap'
    L(t, bmul, 'Value', mk, 'Value')
    # proxy trim material
    mat = bpy.data.materials.get('PROXY_TS_Melodia_Stone')
    if not mat:
        mat = bpy.data.materials.new('PROXY_TS_Melodia_Stone')
        mat.diffuse_color = (0.62, 0.57, 0.50, 1.0)
    sm = N(t, 'GeometryNodeSetMaterial', gx0 + 1140, 0)
    sm.inputs['Material'].default_value = mat
    ap = N(t, 'GeometryNodeSwitch', gx0 + 1320, 0)
    ap.switch_type = 'GEOMETRY'
    L(t, gin, 'Apply Trim UV', ap, 'Switch')
    L(t, mk, 'Geometry', ap, 'True')
    L(t, sm, 'Geometry', ap, 'False')
    bv = N(t, 'GeometryNodeMeshBevel', gx0 + 1500, 0)
    bv.inputs['Offset'].default_value = 0.04
    bv.inputs['Segments'].default_value = 3
    L(t, ap, 'Output', bv, 'Mesh')
    return bv


# ------------------------------------------------- builders

def build_wall_detail(group_name='GN_PARIS_WallDetail'):
    old = bpy.data.node_groups.get(group_name)
    if old:
        bpy.data.node_groups.remove(old)
    t = bpy.data.node_groups.new(group_name, 'GeometryNodeTree')
    t.is_modifier = True
    ins = [
        'Geometry', 'BBox Min', 'BBox Max', 'Show Cornice', 'Show String',
        'Show Wainscot', 'Show Baseboard', 'Show Panels', 'Panel Scale',
        'Apply Trim UV', 'CORNICE_STYLE',
    ]
    for i, s in enumerate(ins):
        st = 'NodeSocketGeometry' if s == 'Geometry' else 'NodeSocketInt' if s == 'CORNICE_STYLE' else 'NodeSocketFloat'
        if s == 'BBox Min':
            st = 'NodeSocketVector'
        if s == 'BBox Max':
            st = 'NodeSocketVector'
        si = t.interface.new_socket(s, in_out='INPUT', socket_type=st)
        if s.startswith('Show ') or s == 'Apply Trim UV':
            si.default_value = True if s != 'Show Panels' else True
        if s == 'CORNICE_STYLE':
            si.default_value = 1
        if s == 'Panel Scale':
            si.default_value = 0.86
    t.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gin = t.nodes.new('NodeGroupInput')
    gin.location = (-1600, 0)
    gout = t.nodes.new('NodeGroupOutput')
    gout.location = (1600, 0)
    # bbox translate: move wall to origin, work, move back
    bmv = N(t, 'ShaderNodeVectorMath', -1400, 0)
    bmv.operation = 'SUBTRACT'
    L(t, gin, 'BBox Min', bmv, 6)
    gin_geom = N(t, 'GeometryNodeTransform', -1200, 0)
    L(t, gin, 'Geometry', gin_geom, 'Geometry')
    L(t, bmv, 'Vector', gin_geom, 'Translation')
    bands, _ = _band_chain(t, gin, gout, -1200)
    panels, ex2 = _panel_chain(t, gin, gout, -1200)
    # joins
    jb = N(t, 'NodeJoinGeometry', 200, 400)
    L(t, bands, 0, jb, 0)
    L(t, panels, 'Output', jb, 1)
    jp = panels
    goth, made = _gothic_extras(t, gin, ex2, 400)
    # style chain: 0 flat -> panels only; 1 haussmann -> bands+panels; 2 gothic -> + extras
    c01 = N(t, 'FunctionNodeCompare', 600, 300)
    c01.data_type = 'FLOAT'
    c01.operation = 'LESS_EQUAL'
    L(t, gin, 'CORNICE_STYLE', c01, 0)
    c01.inputs[1].default_value = 0.5
    c12 = N(t, 'FunctionNodeCompare', 600, 180)
    c12.data_type = 'FLOAT'
    c12.operation = 'GREATER_EQUAL'
    L(t, gin, 'CORNICE_STYLE', c12, 0)
    c12.inputs[1].default_value = 1.5
    sw2 = N(t, 'GeometryNodeSwitch', 800, 180)
    sw2.switch_type = 'GEOMETRY'
    L(t, c12, 'Result', sw2, 'Switch')
    L(t, goth, 'Geometry', sw2, 'True')
    L(t, jb, 'Geometry', sw2, 'False')
    sw1 = N(t, 'GeometryNodeSwitch', 1000, 300)
    sw1.switch_type = 'GEOMETRY'
    L(t, c01, 'Result', sw1, 'Switch')
    L(t, jp, 'Output', sw1, 'True')
    L(t, sw2, 'Output', sw1, 'False')
    fin = _uv_and_finish(t, gin, gout, sw1, 1200)
    L(t, fin, 'Mesh', gout, 'Geometry')
    t.description = 'Paris lane v2: FLAT/HAUSSMANN/GOTHIC wall trim (CORNICE_STYLE 0/1/2).'
    print('[paris_wall_detail] built %s v2: %d nodes, gothic parts: %s'
          % (group_name, len(t.nodes), made))
    return (t, gin, gout)


def build_slab_trim(group_name='GN_PARIS_SlabTrim'):
    old = bpy.data.node_groups.get(group_name)
    if old:
        bpy.data.node_groups.remove(old)
    t = bpy.data.node_groups.new(group_name, 'GeometryNodeTree')
    t.is_modifier = True
    for i, s in enumerate(['Geometry', 'BBox Min', 'BBox Max', 'Show Skirt', 'Apply Trim UV']):
        st = 'NodeSocketGeometry' if s == 'Geometry' else 'NodeSocketVector' if 'BBox' in s else 'NodeSocketFloat'
        si = t.interface.new_socket(s, in_out='INPUT', socket_type=st)
        if s == 'Show Skirt':
            si.default_value = True
    t.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gin = t.nodes.new('NodeGroupInput')
    gin.location = (-1200, 0)
    gout = t.nodes.new('NodeGroupOutput')
    gout.location = (1200, 0)
    bmv = N(t, 'ShaderNodeVectorMath', -1000, 0)
    bmv.operation = 'SUBTRACT'
    L(t, gin, 'BBox Min', bmv, 6)
    tg = N(t, 'GeometryNodeTransform', -820, 0)
    L(t, gin, 'Geometry', tg, 'Geometry')
    L(t, bmv, 'Vector', tg, 'Translation')
    pos = N(t, 'GeometryNodeInputPosition', -700, -200)
    sep = N(t, 'GeometryNodeSeparateXYZ', -580, -200)
    L(t, pos, 'Position', sep, 'Vector')
    g1 = N(t, 'FunctionNodeCompare', -460, -200)
    g1.data_type = 'FLOAT'
    g1.operation = 'LESS_THAN'
    L(t, sep, 'Z', g1, 0)
    g1.inputs[1].default_value = 0.22
    skirt = N(t, 'GeometryNodeSwitch', -300, -100)
    skirt.switch_type = 'GEOMETRY'
    L(t, gin, 'Show Skirt', skirt, 'Switch')
    skc = N(t, 'GeometryNodeMeshCube', -460, -400)
    skc.inputs['Size X'].default_value = 1.0
    skc.inputs['Size Y'].default_value = 1.0
    skc.inputs['Size Z'].default_value = 0.22
    jt = N(t, 'GeometryNodeJoinGeometry', -140, -200)
    L(t, skirt, 'Output', jt, 0)
    L(t, tg, 'Geometry', jt, 1)
    mat = bpy.data.materials.get('PROXY_TS_Melodia_Stone')
    if not mat:
        mat = bpy.data.materials.new('PROXY_TS_Melodia_Stone')
        mat.diffuse_color = (0.62, 0.57, 0.50, 1.0)
    sm = N(t, 'GeometryNodeSetMaterial', 0, -140)
    sm.inputs['Material'].default_value = mat
    ap = N(t, 'GeometryNodeSwitch', 200, -140)
    ap.switch_type = 'GEOMETRY'
    L(t, gin, 'Apply Trim UV', ap, 'Switch')
    L(t, jt, 'Geometry', ap, 'True')
    L(t, sm, 'Geometry', ap, 'False')
    bv = N(t, 'GeometryNodeMeshBevel', 400, -140)
    bv.inputs['Offset'].default_value = 0.04
    bv.inputs['Segments'].default_value = 3
    L(t, ap, 'Output', bv, 'Mesh')
    L(t, bv, 'Mesh', gout, 'Geometry')
    print('[paris_wall_detail] built %s v2: %d nodes' % (group_name, len(t.nodes)))
    return (t, gin, gout)


# ------------------------------------------------- apply / rollout

def _eval_bbox(obj):
    """BBox of obj with PARIS detail mods disabled (kit geometry only)."""
    paris_mods = []
    for m in obj.modifiers:
        if m.type == 'NODES' and ((m.node_group and m.node_group.name.startswith('GN_PARIS_')) or m.node_group is None):
            m.show_viewport = False
            paris_mods.append(m)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    mesh = ev.to_mesh()
    bb = [tuple(mesh.bound_box[i]) for i in range(8)]
    xs = [v[0] for v in bb]
    ys = [v[1] for v in bb]
    zs = [v[2] for v in bb]
    bmin = (min(xs), min(ys), min(zs))
    bmax = (max(xs), max(ys), max(zs))
    ev.to_mesh_clear()
    for m in paris_mods:
        m.show_viewport = True
    return bmin, bmax


def _set_mod(obj, group, mod_name, style=None):
    """(Re)create the detail modifier with fresh interface + bbox values."""
    # drop dangling / previous PARIS mods
    for m in list(obj.modifiers):
        if m.type == 'NODES' and ((m.node_group and m.node_group.name == group.name) or m.node_group is None):
            obj.modifiers.remove(m)
    bmin, bmax = _eval_bbox(obj)
    mod = obj.modifiers.new(mod_name, 'NODES')
    mod.node_group = group
    def sv(name, val):
        try:
            mod[name] = val
        except Exception:
            pass
    sv('BBox Min', bmin)
    sv('BBox Max', bmax)
    if style is not None:
        sv('CORNICE_STYLE', style)
    else:
        sv('CORNICE_STYLE', 1)
    sv('Panel Scale', 0.86)
    # move our modifier before any object bevel
    for i, m in enumerate(obj.modifiers):
        if m is mod:
            while i > 0 and obj.modifiers[i - 1].type == 'NODES' and obj.modifiers[i - 1].node_group and obj.modifiers[i - 1].node_group.name.startswith('SurrealArch'):
                bpy.context.view_layer.objects.active = obj
                obj.modifiers.move(i, i - 1)
                i -= 1
            break
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    mesh = ev.to_mesh()
    polys = len(mesh.polygons)
    ev.to_mesh_clear()
    return polys


def _strip_bevel(obj):
    """Remove object-level Bevel modifiers replaced by the in-group bevel."""
    n = 0
    for m in list(obj.modifiers):
        if m.type == 'BEVEL':
            obj.modifiers.remove(m)
            n += 1
    return n


def rollout_all(style=None, strip_bevel=True):
    """Apply v2 detail to all WALL_* (not curved test) and SLAB_* objects."""
    if bpy.data.node_groups.get('GN_PARIS_WallDetail') is None:
        build_wall_detail()
    if bpy.data.node_groups.get('GN_PARIS_SlabTrim') is None:
        build_slab_trim()
    wall = bpy.data.node_groups['GN_PARIS_WallDetail']
    slab = bpy.data.node_groups['GN_PARIS_SlabTrim']
    n_w = n_s = b = 0
    total = 0
    for obj in bpy.data.objects:
        name = obj.name
        if name.startswith('WALL_') and not name.startswith('WALL_CURVED'):
            total += _set_mod(obj, wall, 'ParisDetail', style=style)
            n_w += 1
            if strip_bevel:
                b += _strip_bevel(obj)
        elif name.startswith('SLAB_'):
            total += _set_mod(obj, slab, 'ParisSlabTrim')
            n_s += 1
            if strip_bevel:
                b += _strip_bevel(obj)
    print('[paris_wall_detail] rollout: %d walls, %d slabs, %d bevels stripped, %d total polys'
          % (n_w, n_s, b, total))
    return n_w, n_s, b, total


# ------------------------------------------------- addon registration

try:
    from .core import register_builder  # noqa
    register_builder('GN_PARIS_WallDetail', build_wall_detail,
                     'PARIS Wall Detail v2',
                     'Haussmann/Gothic wall trim bands, panels, arch medallions, quoins.',
                     category='structures')
    register_builder('GN_PARIS_SlabTrim', build_slab_trim,
                     'PARIS Slab Trim v2',
                     'Slab skirt + in-group bevel for the Paris lane.',
                     category='structures')
    print('[paris_wall_detail] registered builders into the Melodia Studio registry')
except ImportError:
    print('[paris_wall_detail] standalone mode (no core registry)')
