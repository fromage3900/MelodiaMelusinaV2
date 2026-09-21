"""GN_PARIS_* wall-detail builders — Melusina House Paris→Nikki lane.

Converged 2026-09-18 from Saved/MelusinasHouse/paris_phaseBC_build.py into the
Melodia Studio addon. This module is the single authority for
GN_PARIS_WallDetail / GN_PARIS_SlabTrim; the in-file groups are REBUILT from
here. Never hand-edit the live group without porting the change back.

v2 additions over the staged version:
  - CORNICE_STYLE INT: 0=FLAT (panels only) / 1=HAUSSMANN (staged look) /
    2=GOTHIC (bands + stepped reveals + pointed-arch medallions + quoins).
  - Pointed arch delegated to the monolith build_gothic_arch, baked once into
    helper object MH_GothicArchHead (no reimplementation).
  - Higgsas NTInset Face probed for the gothic step reveal (native extrude
    fallback, socket info printed).
  - In-group Mesh Bevel (0.04 / 3) replaces object-level Bevel modifiers on
    walls and slabs (stack shrinks by one).
  - FIX vs staged script: band z placement compared the offset float against
    the marker string ('maxz'), so cornice/string bands were anchored to BBox
    Min (buried below the wall). Corrected to check the marker index.

Self-contained (bpy/mathutils only) so bridge/eval runs can spec-load it;
register_builder() is attached when the addon core is importable.
"""

from pathlib import Path

import bpy
from mathutils import Vector

DEPLOY_ROOT = Path(__file__).resolve().parents[2]
_HELPER_COLL = 'MH_Gen_Helpers'
ARCH_OBJECT = 'MH_GothicArchHead'

# ---------------------------------------------------------------- helpers

def N(t, bl, x=0, y=0):
    n = t.nodes.new(bl)
    n.location = (x, y)
    return n


def L(t, a, sa, b, sb):
    t.links.new(a.outputs[sa], b.inputs[sb])


def mathn(t, op, x, y, a=None, b=None):
    n = N(t, 'ShaderNodeMath', x, y)
    n.operation = op
    if a is not None:
        n.inputs[0].default_value = a
    if b is not None:
        n.inputs[1].default_value = b
    return n


def vmath(t, op, x, y):
    n = N(t, 'ShaderNodeVectorMath', x, y)
    n.operation = op
    return n


def comp(t, x, y, op='GREATER_THAN', b=0.0):
    n = N(t, 'FunctionNodeCompare', x, y)
    n.data_type = 'FLOAT'
    n.operation = op
    n.inputs[1].default_value = b
    return n


def mapr(t, x, y, f0, f1, t0, t1):
    n = N(t, 'ShaderNodeMapRange', x, y)
    n.clamp = True
    n.inputs['From Min'].default_value = f0
    n.inputs['From Max'].default_value = f1
    n.inputs['To Min'].default_value = t0
    n.inputs['To Max'].default_value = t1
    return n


def fswitch(t, x, y):
    n = N(t, 'GeometryNodeSwitch', x, y)
    n.input_type = 'FLOAT'
    return n


def gswitch(t, x, y):
    n = N(t, 'GeometryNodeSwitch', x, y)
    n.input_type = 'GEOMETRY'
    return n


def sock(t, name, stype, default=None, in_out='INPUT'):
    it = t.interface.new_socket(name, in_out=in_out, socket_type=stype)
    if default is not None:
        try:
            it.default_value = default
        except Exception:
            pass
    return it


def _trim_mat():
    mat = bpy.data.materials.get('PROXY_TS_Melodia_Stone')
    if not mat:
        mat = bpy.data.materials.new('PROXY_TS_Melodia_Stone')
        mat.diffuse_color = (0.62, 0.57, 0.50, 1.0)
    return mat


# ------------------------------------------------- Higgsas loader (dup-safe)

def _higgs(name):
    """Resolve a Higgsas NT_* group without leaving .001 duplicates."""
    nt = 'NT' + name
    g = bpy.data.node_groups.get(nt)
    if g:
        return g
    alt = bpy.data.node_groups.get(name)
    if alt:
        alt.name = nt
        return alt
    try:
        from .. import higgsas_bridge as _hb
        return _hb.load_node(name)
    except Exception:
        pass
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            'mel_higgsas_bridge', str(DEPLOY_ROOT / 'surreal_arch' / 'higgsas_bridge.py'))
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
    try:
        import surreal_architecture_gen as mon
    except ImportError:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            'mel_monolith', str(DEPLOY_ROOT / 'surreal_architecture_gen.py'))
        mon = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mon)
    t = bpy.data.node_groups.new('MH_Arch_Bake_TMP', 'GeometryNodeTree')
    sock(t, 'Geometry', 'NodeSocketGeometry')
    sock(t, 'Geometry', 'NodeSocketGeometry', in_out='OUTPUT')
    gin = t.nodes.new('NodeGroupInput')
    gout = t.nodes.new('NodeGroupOutput')
    gin.location = (-400, 0)
    gout.location = (200, 0)
    t.links.new(gin.outputs['Geometry'], gout.inputs['Geometry'])
    from types import SimpleNamespace
    props = SimpleNamespace(gothic_width=1.0, gothic_radius=0.55,
                            gothic_thickness=0.08)
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
    bpy.context.view_layer.update()
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


# ------------------------------------------------- WallDetail v2 builder

def build_wall_detail(group_name='GN_PARIS_WallDetail'):
    old = bpy.data.node_groups.get(group_name)
    if old:
        try:
            bpy.data.node_groups.remove(old)
        except Exception:
            pass
    t = bpy.data.node_groups.new(group_name, 'GeometryNodeTree')
    t.is_modifier = True
    sock(t, 'Geometry', 'NodeSocketGeometry')
    sock(t, 'BBox Min', 'NodeSocketVector', (0, 0, 0))
    sock(t, 'BBox Max', 'NodeSocketVector', (2, 0.3, 3))
    sock(t, 'Show Cornice', 'NodeSocketBool', True)
    sock(t, 'Show String', 'NodeSocketBool', True)
    sock(t, 'Show Wainscot', 'NodeSocketBool', True)
    sock(t, 'Show Baseboard', 'NodeSocketBool', True)
    sock(t, 'Show Panels', 'NodeSocketBool', True)
    sock(t, 'Panel Scale', 'NodeSocketFloat', 0.86)
    sock(t, 'Apply Trim UV', 'NodeSocketBool', True)
    sock(t, 'CORNICE_STYLE', 'NodeSocketInt', 1)
    sock(t, 'Geometry', 'NodeSocketGeometry', in_out='OUTPUT')
    gin = N(t, 'NodeGroupInput', -1700, 0)
    gout = N(t, 'NodeGroupOutput', 2300, 0)

    # --- bbox decomposition (mesh-local: Bounding Box node on the input
    # geometry, NOT world-space BBox inputs — walls sit at non-identity
    # local transforms; trim must be computed in the mesh's own space)
    bbo = N(t, 'GeometryNodeBoundBox', -1650, 0)
    L(t, gin, 'Geometry', bbo, 'Geometry')
    bmin = N(t, 'ShaderNodeSeparateXYZ', -1500, 300)
    L(t, bbo, 'Min', bmin, 0)
    bmax = N(t, 'ShaderNodeSeparateXYZ', -1500, -300)
    L(t, bbo, 'Max', bmax, 0)
    W = mathn(t, 'SUBTRACT', -1300, 340); L(t, bmax, 'X', W, 0); L(t, bmin, 'X', W, 1)
    D = mathn(t, 'SUBTRACT', -1300, 260); L(t, bmax, 'Y', D, 0); L(t, bmin, 'Y', D, 1)
    H = mathn(t, 'SUBTRACT', -1300, 180); L(t, bmax, 'Z', H, 0); L(t, bmin, 'Z', H, 1)
    cxa = mathn(t, 'ADD', -1400, 100); L(t, bmax, 'X', cxa, 0); L(t, bmin, 'X', cxa, 1)
    cx = mathn(t, 'DIVIDE', -1280, 100); cx.inputs[1].default_value = 2.0; L(t, cxa, 0, cx, 0)
    cya = mathn(t, 'ADD', -1400, 20); L(t, bmax, 'Y', cya, 0); L(t, bmin, 'Y', cya, 1)
    cy = mathn(t, 'DIVIDE', -1280, 20); cy.inputs[1].default_value = 2.0; L(t, cya, 0, cy, 0)

    def cube_at(x0, y0, dx, dy, dz, zc_expr):
        """dx/dy added to W/D; dz constant height; zc_expr = (marker, offset)."""
        sx = mathn(t, 'ADD', x0, y0 + 240); L(t, W, 0, sx, 0); sx.inputs[1].default_value = dx
        sy = mathn(t, 'ADD', x0, y0 + 160); L(t, D, 0, sy, 0); sy.inputs[1].default_value = dy
        size = N(t, 'ShaderNodeCombineXYZ', x0 + 160, y0 + 200)
        L(t, sx, 0, size, 'X'); L(t, sy, 0, size, 'Y'); size.inputs['Z'].default_value = dz
        cub = N(t, 'GeometryNodeMeshCube', x0 + 320, y0 + 200)
        L(t, size, 'Vector', cub, 'Size')
        pz = mathn(t, 'ADD', x0, y0 + 60)
        if zc_expr[0] == 'maxz':
            L(t, bmax, 'Z', pz, 0)
        else:
            L(t, bmin, 'Z', pz, 0)
        pz.inputs[1].default_value = zc_expr[1]
        pos = N(t, 'ShaderNodeCombineXYZ', x0 + 160, y0 + 60)
        L(t, cx, 0, pos, 'X'); L(t, cy, 0, pos, 'Y'); L(t, pz, 0, pos, 'Z')
        tr = N(t, 'GeometryNodeTransform', x0 + 480, y0 + 120)
        L(t, cub, 'Mesh', tr, 'Geometry'); L(t, pos, 'Vector', tr, 'Translation')
        return tr

    specs = [
        ('Show Cornice',   -1050,  520, 0.10, 0.10, 0.06, ('maxz', -0.03)),
        ('Show Cornice',   -1050,  340, 0.24, 0.24, 0.15, ('maxz', -0.135)),
        ('Show Cornice',   -1050,  160, 0.08, 0.08, 0.09, ('maxz', -0.255)),
        ('Show String',    -1050,  -20, 0.14, 0.14, 0.07, ('maxz', -0.335)),
        ('Show Wainscot',  -1050, -200, 0.10, 0.10, 0.05, ('minz', 0.755)),
        ('Show Baseboard', -1050, -380, 0.10, 0.10, 0.18, ('minz', 0.09)),
    ]
    jband = N(t, 'GeometryNodeJoinGeometry', -100, 700)
    for toggle, x0, y0, dx, dy, dz, zc in specs:
        tr = cube_at(x0, y0, dx, dy, dz, zc)
        sw = gswitch(t, -640, y0 + 700)
        L(t, gin, toggle, sw, 'Switch')
        L(t, tr, 'Geometry', sw, 'True')
        t.links.new(sw.outputs[0], jband.inputs['Geometry'])

    # --- panel insets on the wall body (verbatim staged)
    pos_n = N(t, 'GeometryNodeInputPosition', -1500, -700)
    nor_n = N(t, 'GeometryNodeInputNormal', -1500, -900)
    pos_s = N(t, 'ShaderNodeSeparateXYZ', -1340, -700); L(t, pos_n, 'Position', pos_s, 0)
    nor_s = N(t, 'ShaderNodeSeparateXYZ', -1340, -900); L(t, nor_n, 'Normal', nor_s, 0)
    area = N(t, 'GeometryNodeInputMeshFaceArea', -1500, -1050)
    big = comp(t, -1180, -1050, 'GREATER_THAN', 0.5); L(t, area, 0, big, 0)
    nzabs = mathn(t, 'ABSOLUTE', -1180, -900); L(t, nor_s, 'Z', nzabs, 0)
    flat = comp(t, -1020, -900, 'LESS_THAN', 0.2); L(t, nzabs, 0, flat, 0)
    andn = N(t, 'FunctionNodeBooleanMath', -860, -950)
    andn.operation = 'AND'
    L(t, big, 0, andn, 0); L(t, flat, 0, andn, 1)
    ex1 = N(t, 'GeometryNodeExtrudeMesh', -700, -950)
    ex1.inputs['Individual'].default_value = True
    ex1.inputs['Offset Scale'].default_value = 0.0
    L(t, gin, 'Geometry', ex1, 'Mesh'); L(t, andn, 0, ex1, 'Selection')
    sce = N(t, 'GeometryNodeScaleElements', -520, -950)
    sce.inputs['Scale Mode'].default_value = 'Uniform'
    L(t, ex1, 'Mesh', sce, 'Geometry'); L(t, ex1, 'Top', sce, 'Selection')
    L(t, gin, 'Panel Scale', sce, 'Scale'); L(t, pos_n, 'Position', sce, 'Center')
    offv = vmath(t, 'MULTIPLY', -520, -1150); L(t, nor_n, 'Normal', offv, 0)
    offc = N(t, 'ShaderNodeCombineXYZ', -700, -1200)
    offc.inputs['X'].default_value = -0.05
    offc.inputs['Y'].default_value = -0.05
    offc.inputs['Z'].default_value = -0.05
    L(t, offc, 'Vector', offv, 1)
    ex2 = N(t, 'GeometryNodeExtrudeMesh', -340, -1000)
    ex2.inputs['Individual'].default_value = True
    L(t, sce, 'Geometry', ex2, 'Mesh'); L(t, ex1, 'Top', ex2, 'Selection')
    L(t, offv, 'Vector', ex2, 'Offset'); ex2.inputs['Offset Scale'].default_value = 1.0
    psw = gswitch(t, -160, -900)
    L(t, gin, 'Show Panels', psw, 'Switch')
    L(t, ex2, 'Mesh', psw, 'True'); L(t, gin, 'Geometry', psw, 'False')
    jpan = N(t, 'GeometryNodeJoinGeometry', 40, -900)
    t.links.new(psw.outputs[0], jpan.inputs['Geometry'])
    jall = N(t, 'GeometryNodeJoinGeometry', 200, 0)
    # Bevel ONLY the band cubes (clean boxes): the panel chain carries
    # in-place duplicates whose degenerate edges spike the bevel (~3m
    # strays + 14x vert inflation when the wall is kit-fed).
    bvlb = N(t, 'GeometryNodeMeshBevel', 120, 260)
    bvlb.inputs['Offset'].default_value = 0.04
    bvlb.inputs['Segments'].default_value = 3
    L(t, jband, 'Geometry', bvlb, 'Mesh')
    L(t, bvlb, 'Mesh', jall, 'Geometry')
    t.links.new(jpan.outputs[0], jall.inputs['Geometry'])

    # --- v2 gothic branch: stepped reveal + arch medallions + quoins
    made = []
    goth_geo = _gothic_branch(t, gin, ex2, pos_n, nor_n, W, D, cx, cy,
                              bmin, bmax, made)

    # --- style chain: 0=FLAT(panels) 1=HAUSSMANN(bands+panels) 2=GOTHIC
    c01 = comp(t, 400, 300, 'LESS_EQUAL', 0.5); L(t, gin, 'CORNICE_STYLE', c01, 0)
    c12 = comp(t, 400, 180, 'GREATER_EQUAL', 1.5); L(t, gin, 'CORNICE_STYLE', c12, 0)
    swB = gswitch(t, 600, 180)
    L(t, c12, 0, swB, 'Switch')
    L(t, goth_geo, 'Geometry', swB, 'True'); L(t, jall, 'Geometry', swB, 'False')
    swA = gswitch(t, 760, 300)
    L(t, c01, 0, swA, 'Switch')
    L(t, jpan, 'Geometry', swA, 'True'); L(t, swB, 'Output', swA, 'False')

    # --- UV band authoring (verbatim staged; input = styled geometry)
    zr = mathn(t, 'DIVIDE', 900, 700)
    sub = mathn(t, 'SUBTRACT', 740, 700); L(t, pos_s, 'Z', sub, 0); L(t, bmin, 'Z', sub, 1)
    L(t, sub, 0, zr, 0); L(t, H, 0, zr, 1)
    corn_lo = mathn(t, 'SUBTRACT', 740, 560)
    fr = mathn(t, 'DIVIDE', 580, 560); fr.inputs[1].default_value = 0.37
    L(t, H, 0, fr, 0); corn_lo.inputs[0].default_value = 1.0; L(t, fr, 0, corn_lo, 1)
    bb_hi = mathn(t, 'DIVIDE', 580, 480); bb_hi.inputs[0].default_value = 0.18; L(t, H, 0, bb_hi, 1)
    wa_hi = mathn(t, 'DIVIDE', 580, 400); wa_hi.inputs[0].default_value = 0.73; L(t, H, 0, wa_hi, 1)
    v_corn = mapr(t, 1080, 620, 0, 1, 0.689, 0.811); L(t, zr, 0, v_corn, 'Value')
    L(t, corn_lo, 0, v_corn, 'From Min'); v_corn.inputs['From Max'].default_value = 1.0
    v_panel = mapr(t, 1080, 500, 0, 1, 0.282, 0.686); L(t, zr, 0, v_panel, 'Value')
    L(t, wa_hi, 0, v_panel, 'From Min'); L(t, corn_lo, 0, v_panel, 'From Max')
    v_wa = mapr(t, 1080, 380, 0, 1, 0.189, 0.279); L(t, zr, 0, v_wa, 'Value')
    L(t, bb_hi, 0, v_wa, 'From Min'); L(t, wa_hi, 0, v_wa, 'From Max')
    v_bb = mapr(t, 1080, 260, 0, 1, 0.044, 0.186); L(t, zr, 0, v_bb, 'Value')
    v_bb.inputs['From Min'].default_value = 0.0; L(t, bb_hi, 0, v_bb, 'From Max')
    m_corn = comp(t, 1080, 160, 'GREATER_THAN', 0.0); L(t, zr, 0, m_corn, 0); L(t, corn_lo, 0, m_corn, 1)
    m_bb = comp(t, 1080, 60, 'LESS_THAN', 0.0); L(t, zr, 0, m_bb, 0); L(t, bb_hi, 0, m_bb, 1)
    m_wa = comp(t, 1080, -40, 'LESS_THAN', 0.0); L(t, zr, 0, m_wa, 0); L(t, wa_hi, 0, m_wa, 1)
    s1 = fswitch(t, 1260, 400); L(t, m_wa, 0, s1, 'Switch')
    L(t, v_panel, 0, s1, 'False'); L(t, v_wa, 0, s1, 'True')
    s2 = fswitch(t, 1400, 400); L(t, m_bb, 0, s2, 'Switch')
    L(t, s1, 0, s2, 'False'); L(t, v_bb, 0, s2, 'True')
    s3 = fswitch(t, 1540, 400); L(t, m_corn, 0, s3, 'Switch')
    L(t, s2, 0, s3, 'False'); L(t, v_corn, 0, s3, 'True')
    nz = N(t, 'ShaderNodeSeparateXYZ', 900, -300); L(t, nor_n, 'Normal', nz, 0)
    is_top = comp(t, 1080, -300, 'GREATER_THAN', 0.6); L(t, nz, 'Z', is_top, 0)
    is_bot = comp(t, 1080, -420, 'LESS_THAN', -0.6); L(t, nz, 'Z', is_bot, 0)
    v_ledge = mathn(t, 'ADD', 1080, -540); v_ledge.inputs[0].default_value = 0.02; v_ledge.inputs[1].default_value = 0.0
    v_half = mathn(t, 'ADD', 1080, -640); v_half.inputs[0].default_value = 0.5; v_half.inputs[1].default_value = 0.0
    s4 = fswitch(t, 1680, 400); L(t, is_top, 0, s4, 'Switch'); L(t, s3, 0, s4, 'False'); L(t, v_ledge, 0, s4, 'True')
    s5 = fswitch(t, 1820, 400); L(t, is_bot, 0, s5, 'Switch'); L(t, s4, 0, s5, 'False'); L(t, v_half, 0, s5, 'True')
    nxabs = mathn(t, 'ABSOLUTE', 900, -200); L(t, nor_s, 'X', nxabs, 0)
    nyabs = mathn(t, 'ABSOLUTE', 900, -300); L(t, nor_s, 'Y', nyabs, 0)
    usel = comp(t, 1080, -200, 'GREATER_EQUAL', 0.0); L(t, nxabs, 0, usel, 0); L(t, nyabs, 0, usel, 1)
    ux_d = mathn(t, 'DIVIDE', 1080, -740); L(t, pos_s, 'X', ux_d, 0); ux_d.inputs[1].default_value = 3.4
    ux = mathn(t, 'WRAP', 1240, -740); ux.inputs[1].default_value = 0.0; ux.inputs[2].default_value = 1.0
    L(t, ux_d, 0, ux, 0)
    uy_d = mathn(t, 'DIVIDE', 1080, -860); L(t, pos_s, 'Y', uy_d, 0); uy_d.inputs[1].default_value = 3.4
    uy = mathn(t, 'WRAP', 1240, -860); uy.inputs[1].default_value = 0.0; uy.inputs[2].default_value = 1.0
    L(t, uy_d, 0, uy, 0)
    usw = fswitch(t, 1400, -800); L(t, usel, 0, usw, 'Switch')
    L(t, uy, 0, usw, 'False'); L(t, ux, 0, usw, 'True')
    uv = N(t, 'ShaderNodeCombineXYZ', 1960, 200); L(t, usw, 0, uv, 'X'); L(t, s5, 0, uv, 'Y')
    store = N(t, 'GeometryNodeStoreNamedAttribute', 2100, 200)
    store.data_type = 'FLOAT2'; store.domain = 'CORNER'
    store.inputs['Name'].default_value = 'UVMap'
    L(t, swA, 'Output', store, 'Geometry'); L(t, uv, 'Vector', store, 'Value')
    setmat = N(t, 'GeometryNodeSetMaterial', 2240, 200)
    setmat.inputs['Material'].default_value = _trim_mat()
    L(t, store, 'Geometry', setmat, 'Geometry')
    appl = gswitch(t, 2040, -300)
    L(t, gin, 'Apply Trim UV', appl, 'Switch')
    L(t, store, 'Geometry', appl, 'False'); L(t, setmat, 'Geometry', appl, 'True')
    # No end-of-chain bevel: the realized gothic stream spikes and the
    # panel chain degenerates spike too; bands are beveled at their join.
    L(t, appl, 'Output', gout, 'Geometry')
    t.description = ('Paris lane v2: FLAT/HAUSSMANN/GOTHIC via CORNICE_STYLE '
                     '0/1/2; in-group bevel; arch medallions + quoins (gothic).')
    print('[paris_wall_detail] built %s v2: %d nodes; gothic parts: %s'
          % (group_name, len(t.nodes), made))
    return (t, gin, gout)


def _gothic_branch(t, gin, ex2, pos_n, nor_n, W, D, cx, cy, bmin, bmax, made):
    """Stepped reveals + arch medallions + quoins for CORNICE_STYLE=2."""
    # stepped reveal: third shallow extrude + slight scale on ex2 top
    ex3 = N(t, 'GeometryNodeExtrudeMesh', -160, -1150)
    ex3.inputs['Individual'].default_value = True
    offv3 = vmath(t, 'MULTIPLY', -320, -1300)
    L(t, nor_n, 'Normal', offv3, 0)
    offc3 = N(t, 'ShaderNodeCombineXYZ', -500, -1350)
    offc3.inputs['X'].default_value = -0.025
    offc3.inputs['Y'].default_value = -0.025
    offc3.inputs['Z'].default_value = -0.025
    L(t, offc3, 'Vector', offv3, 1)
    L(t, ex2, 'Mesh', ex3, 'Mesh'); L(t, ex2, 'Top', ex3, 'Selection')
    L(t, offv3, 'Vector', ex3, 'Offset'); ex3.inputs['Offset Scale'].default_value = 1.0
    sce2 = N(t, 'GeometryNodeScaleElements', 20, -1150)
    sce2.inputs['Scale Mode'].default_value = 'Uniform'
    L(t, ex3, 'Mesh', sce2, 'Geometry'); L(t, ex3, 'Top', sce2, 'Selection')
    sce2.inputs['Scale'].default_value = 0.82
    L(t, pos_n, 'Position', sce2, 'Center')
    made.append('stepped-reveal')

    # Higgsas probe (informational; native extrude is the wired engine)
    higs = _higgs('NTInset Face')
    if higs:
        made.append('NTInset Face available')
        try:
            names = [i.name for i in higs.interface.items_tree
                     if getattr(i, 'in_out', 'INPUT') == 'INPUT']
            print('[paris_wall_detail] NTInset Face inputs: %s' % names[:10])
        except Exception:
            pass

    # arch medallions: one instance per stepped panel face
    try:
        arch_obj = ensure_gothic_arch_object()
    except Exception as e:
        print('[paris_wall_detail] arch bake skipped: %s' % e)
        arch_obj = None
    arch_inst = None
    if arch_obj is not None:
        mtp = N(t, 'GeometryNodeMeshToPoints', 200, -1250)
        if hasattr(mtp, 'mode'):
            mtp.mode = 'FACES'
        elif hasattr(mtp, 'domain'):
            mtp.domain = 'FACES'
        elif mtp.inputs.get('Domain') is not None:
            mtp.inputs['Domain'].default_value = 'FACES'
        else:
            print('[paris_wall_detail] MeshToPoints: no domain control; using points fallback')
        L(t, sce2, 'Geometry', mtp, 'Mesh')
        L(t, ex3, 'Top', mtp, 'Selection')
        bigx = comp(t, 200, -1450, 'GREATER_THAN', 0.0)
        L(t, W, 0, bigx, 0); L(t, D, 0, bigx, 1)
        rz0 = mathn(t, 'ADD', 360, -1490, 0.0, 0.0)
        rz1 = mathn(t, 'ADD', 360, -1570, 1.5708, 0.0)
        rsw = fswitch(t, 520, -1500); L(t, bigx, 0, rsw, 'Switch')
        L(t, rz1, 0, rsw, 'False'); L(t, rz0, 0, rsw, 'True')
        rrz = N(t, 'ShaderNodeCombineXYZ', 660, -1500); L(t, rsw, 0, rrz, 'Z')
        # Medallion fit filter: the arch is 1.392 long (1.16 x 1.2); drop
        # points whose arch would overhang the wall ends (the X +0.50
        # overshoot on GOTHIC walls).
        cxb = mathn(t, 'ADD', 40, -1650); L(t, bmin, 'X', cxb, 0); L(t, bmax, 'X', cxb, 1)
        cxb2 = mathn(t, 'DIVIDE', 200, -1650); cxb2.inputs[1].default_value = 2.0; L(t, cxb, 0, cxb2, 0)
        halfw = mathn(t, 'SUBTRACT', 40, -1720); L(t, bmax, 'X', halfw, 0); L(t, bmin, 'X', halfw, 1)
        halfw2 = mathn(t, 'DIVIDE', 200, -1720); halfw2.inputs[1].default_value = 2.0; L(t, halfw, 0, halfw2, 0)
        thr = mathn(t, 'SUBTRACT', 360, -1680); thr.inputs[1].default_value = 0.716; L(t, halfw2, 0, thr, 0)
        ppos = N(t, 'ShaderNodeSeparateXYZ', 40, -1580); L(t, pos_n, 'Position', ppos, 0)
        dxp = mathn(t, 'SUBTRACT', 200, -1580); L(t, ppos, 'X', dxp, 0); L(t, cxb2, 0, dxp, 1)
        adx = mathn(t, 'ABSOLUTE', 360, -1580); L(t, dxp, 0, adx, 0)
        gtfit = comp(t, 520, -1580, 'GREATER_THAN', 0.0); L(t, adx, 0, gtfit, 0); L(t, thr, 0, gtfit, 1)
        delp = N(t, 'GeometryNodeDeleteGeometry', 700, -1400)
        # 5.2: Delete Geometry has NO Domain/Mode INPUT sockets (they are node
        # properties) and the defaults are domain=POINT mode=ALL — exactly the
        # semantics needed, so no assignment at all. Writing
        # delp.inputs['Domain'] raised KeyError and killed the build mid-chain
        # (the saved blend held a 99-node unwired partial, 2026-09-20).
        L(t, mtp, 'Points', delp, 'Geometry'); L(t, gtfit, 0, delp, 'Selection')
        oi = N(t, 'GeometryNodeObjectInfo', 200, -1550)
        oi.transform_space = 'ORIGINAL'
        oi.inputs['Object'].default_value = arch_obj
        inst = N(t, 'GeometryNodeInstanceOnPoints', 820, -1300)
        L(t, delp, 'Geometry', inst, 'Points')
        L(t, oi, 'Geometry', inst, 'Instance')
        L(t, rrz, 'Vector', inst, 'Rotation')
        inst.inputs['Scale'].default_value = (1.2, 1.2, 1.2)
        arch_inst = inst
        made.append('arch-medallions')

    # quoins on the four vertical corners
    jl = N(t, 'GeometryNodeJoinGeometry', 200, 300)
    corners = ((bmin, 'X', bmin, 'Y'), (bmax, 'X', bmin, 'Y'),
               (bmax, 'X', bmax, 'Y'), (bmin, 'X', bmax, 'Y'))
    for k, (sx_node, sx_ax, sy_node, sy_ax) in enumerate(corners):
        lnb = N(t, 'GeometryNodeMeshLine', 40, 300 + 90 * k)
        lnb.inputs['Count'].default_value = 12
        sxyz = N(t, 'ShaderNodeCombineXYZ', -160, 300 + 90 * k)
        L(t, sx_node, sx_ax, sxyz, 'X'); L(t, sy_node, sy_ax, sxyz, 'Y')
        z0 = mathn(t, 'ADD', -320, 300 + 90 * k)
        L(t, bmin, 'Z', z0, 0); z0.inputs[1].default_value = 0.06
        z1 = mathn(t, 'ADD', -320, 240 + 90 * k)
        L(t, bmax, 'Z', z1, 0); z1.inputs[1].default_value = -0.06
        L(t, z0, 0, sxyz, 'Z')
        # 5.2 lesson: MeshLine mode enum assignments are unreliable here
        # (END_POINTS silently failed -> mode stayed OFFSET, and the full
        # end-start delta wired into Offset staircased 12 points 32m up).
        # Use OFFSET semantics explicitly: Offset = per-step translation,
        # step = (z1 - z0) / (count - 1) so points span z0..z1 exactly.
        dzz = mathn(t, 'SUBTRACT', -320, 180 + 90 * k)
        L(t, z1, 0, dzz, 0); L(t, z0, 0, dzz, 1)
        qst = mathn(t, 'DIVIDE', -320, 120 + 90 * k)
        L(t, dzz, 0, qst, 0); qst.inputs[1].default_value = 11.0
        ozz = N(t, 'ShaderNodeCombineXYZ', -160, 120 + 90 * k)
        L(t, qst, 0, ozz, 'Z')
        L(t, sxyz, 'Vector', lnb, 'Start Location')
        L(t, ozz, 'Vector', lnb, 'Offset')
        t.links.new(lnb.outputs[0], jl.inputs['Geometry'])
    brick = N(t, 'GeometryNodeMeshCube', 360, 340)
    syz = mathn(t, 'ADD', 200, 380); L(t, D, 0, syz, 0); syz.inputs[1].default_value = 0.12
    bsz = N(t, 'ShaderNodeCombineXYZ', 520, 380)
    bsz.inputs['X'].default_value = 0.32
    L(t, syz, 0, bsz, 'Y')
    bsz.inputs['Z'].default_value = 0.12
    L(t, bsz, 'Vector', brick, 'Size')
    instq = N(t, 'GeometryNodeInstanceOnPoints', 560, 340)
    L(t, jl, 'Geometry', instq, 'Points')
    L(t, brick, 'Mesh', instq, 'Instance')
    instq.inputs['Scale'].default_value = (1.0, 1.0, 1.0)
    made.append('quoins')

    # gothic join + realize
    jg = N(t, 'GeometryNodeJoinGeometry', 1000, -400)
    t.links.new(sce2.outputs['Geometry'], jg.inputs['Geometry'])
    t.links.new(instq.outputs['Instances'], jg.inputs['Geometry'])
    if arch_inst is not None:
        t.links.new(arch_inst.outputs['Instances'], jg.inputs['Geometry'])
    gswp = gswitch(t, 1180, -400)
    L(t, gin, 'Show Panels', gswp, 'Switch')
    L(t, jg, 'Geometry', gswp, 'True')
    gonly = N(t, 'GeometryNodeJoinGeometry', 1000, -200)
    t.links.new(instq.outputs['Instances'], gonly.inputs['Geometry'])
    L(t, gonly, 'Geometry', gswp, 'False')
    rz = N(t, 'GeometryNodeRealizeInstances', 1340, -400)
    L(t, gswp, 'Output', rz, 'Geometry')
    return rz


# ------------------------------------------------- SlabTrim v2 builder

def build_slab_trim(group_name='GN_PARIS_SlabTrim'):
    old = bpy.data.node_groups.get(group_name)
    if old:
        try:
            bpy.data.node_groups.remove(old)
        except Exception:
            pass
    t = bpy.data.node_groups.new(group_name, 'GeometryNodeTree')
    t.is_modifier = True
    sock(t, 'Geometry', 'NodeSocketGeometry')
    sock(t, 'BBox Min', 'NodeSocketVector', (0, 0, 0))
    sock(t, 'BBox Max', 'NodeSocketVector', (6, 4, 0.2))
    sock(t, 'Apply Trim UV', 'NodeSocketBool', True)
    sock(t, 'Geometry', 'NodeSocketGeometry', in_out='OUTPUT')
    gin2 = N(t, 'NodeGroupInput', -1500, 0)
    gout2 = N(t, 'NodeGroupOutput', 1200, 0)
    bbo2 = N(t, 'GeometryNodeBoundBox', -1420, 0); L(t, gin2, 'Geometry', bbo2, 'Geometry')
    bmin2 = N(t, 'ShaderNodeSeparateXYZ', -1300, 300); L(t, bbo2, 'Min', bmin2, 0)
    bmax2 = N(t, 'ShaderNodeSeparateXYZ', -1300, -300); L(t, bbo2, 'Max', bmax2, 0)
    pos2 = N(t, 'GeometryNodeInputPosition', -1300, 0)
    nor2 = N(t, 'GeometryNodeInputNormal', -1300, -500)
    pos2s = N(t, 'ShaderNodeSeparateXYZ', -1140, 0); L(t, pos2, 'Position', pos2s, 0)
    nor2s = N(t, 'ShaderNodeSeparateXYZ', -1140, -500); L(t, nor2, 'Normal', nor2s, 0)
    Hs = mathn(t, 'SUBTRACT', -980, -200); L(t, bmax2, 'Z', Hs, 0); L(t, bmin2, 'Z', Hs, 1)
    zr2 = mathn(t, 'DIVIDE', -820, -100)
    sb = mathn(t, 'SUBTRACT', -980, -100); L(t, pos2s, 'Z', sb, 0); L(t, bmin2, 'Z', sb, 1)
    L(t, sb, 0, zr2, 0); L(t, Hs, 0, zr2, 1)
    v_side = mapr(t, -640, -100, 0, 1, 0.044, 0.186); L(t, zr2, 0, v_side, 'Value')
    nz2 = N(t, 'ShaderNodeSeparateXYZ', -980, -500); L(t, nor2, 'Normal', nz2, 0)
    top2 = comp(t, -640, -400, 'GREATER_THAN', 0.6); L(t, nz2, 'Z', top2, 0)
    bot2 = comp(t, -640, -560, 'LESS_THAN', -0.6); L(t, nz2, 'Z', bot2, 0)
    vl2 = mathn(t, 'ADD', -640, -700); vl2.inputs[0].default_value = 0.02; vl2.inputs[1].default_value = 0.0
    vh2 = mathn(t, 'ADD', -640, -800); vh2.inputs[0].default_value = 0.5; vh2.inputs[1].default_value = 0.0
    sw2a = fswitch(t, -440, -300); L(t, top2, 0, sw2a, 'Switch')
    L(t, v_side, 0, sw2a, 'False'); L(t, vl2, 0, sw2a, 'True')
    sw2b = fswitch(t, -280, -300); L(t, bot2, 0, sw2b, 'Switch')
    L(t, sw2a, 0, sw2b, 'False'); L(t, vh2, 0, sw2b, 'True')
    ax2 = mathn(t, 'ABSOLUTE', -980, -620); L(t, nor2s, 'X', ax2, 0)
    ay2 = mathn(t, 'ABSOLUTE', -980, -720); L(t, nor2s, 'Y', ay2, 0)
    us2 = comp(t, -640, -660, 'GREATER_EQUAL', 0.0); L(t, ax2, 0, us2, 0); L(t, ay2, 0, us2, 1)
    ux2d = mathn(t, 'DIVIDE', -640, -900); L(t, pos2s, 'X', ux2d, 0); ux2d.inputs[1].default_value = 3.4
    ux2 = mathn(t, 'WRAP', -480, -900); ux2.inputs[1].default_value = 0.0; ux2.inputs[2].default_value = 1.0
    L(t, ux2d, 0, ux2, 0)
    uy2d = mathn(t, 'DIVIDE', -640, -1020); L(t, pos2s, 'Y', uy2d, 0); uy2d.inputs[1].default_value = 3.4
    uy2 = mathn(t, 'WRAP', -480, -1020); uy2.inputs[1].default_value = 0.0; uy2.inputs[2].default_value = 1.0
    L(t, uy2d, 0, uy2, 0)
    usw2 = fswitch(t, -320, -960); L(t, us2, 0, usw2, 'Switch')
    L(t, uy2, 0, usw2, 'False'); L(t, ux2, 0, usw2, 'True')
    uv2 = N(t, 'ShaderNodeCombineXYZ', -120, -100); L(t, usw2, 0, uv2, 'X'); L(t, sw2b, 0, uv2, 'Y')
    st2 = N(t, 'GeometryNodeStoreNamedAttribute', 40, 0)
    st2.data_type = 'FLOAT2'; st2.domain = 'CORNER'; st2.inputs['Name'].default_value = 'UVMap'
    L(t, gin2, 'Geometry', st2, 'Geometry'); L(t, uv2, 'Vector', st2, 'Value')
    sm2 = N(t, 'GeometryNodeSetMaterial', 200, 0); sm2.inputs['Material'].default_value = _trim_mat()
    L(t, st2, 'Geometry', sm2, 'Geometry')
    ap2 = gswitch(t, 360, 200); L(t, gin2, 'Apply Trim UV', ap2, 'Switch')
    L(t, st2, 'Geometry', ap2, 'False'); L(t, sm2, 'Geometry', ap2, 'True')
    bvl = N(t, 'GeometryNodeMeshBevel', 560, 200)
    bvl.inputs['Offset'].default_value = 0.04
    bvl.inputs['Segments'].default_value = 3
    L(t, ap2, 'Output', bvl, 'Mesh')
    L(t, bvl, 'Mesh', gout2, 'Geometry')
    print('[paris_wall_detail] built %s v2: %d nodes' % (group_name, len(t.nodes)))
    return (t, gin2, gout2)


# ------------------------------------------------- apply / rollout

def _eval_bbox(obj):
    """World-space BBox of obj with PARIS detail mods disabled (kit only)."""
    paris_mods = []
    for m in obj.modifiers:
        if m.type == 'NODES' and ((m.node_group and m.node_group.name.startswith('GN_PARIS_'))
                                  or m.node_group is None):
            m.show_viewport = False
            paris_mods.append(m)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for c in ev.bound_box:
        w = ev.matrix_world @ Vector(c)
        lo.x = min(lo.x, w.x); lo.y = min(lo.y, w.y); lo.z = min(lo.z, w.z)
        hi.x = max(hi.x, w.x); hi.y = max(hi.y, w.y); hi.z = max(hi.z, w.z)
    for m in paris_mods:
        m.show_viewport = True
    return (lo.x, lo.y, lo.z), (hi.x, hi.y, hi.z)


def _set_mod(obj, group, mod_name, style=None):
    """(Re)create the detail modifier with fresh interface + bbox values."""
    for m in list(obj.modifiers):
        if m.type == 'NODES' and ((m.node_group and m.node_group.name == group.name)
                                  or m.node_group is None):
            obj.modifiers.remove(m)
    bmin, bmax = _eval_bbox(obj)
    mod = obj.modifiers.new(mod_name, 'NODES')
    mod.node_group = group
    idmap = {i.name: i.identifier for i in group.interface.items_tree
             if i.in_out == 'INPUT' and i.socket_type != 'NodeSocketGeometry'}
    mod.properties.inputs[idmap['BBox Min']]['value'] = bmin
    mod.properties.inputs[idmap['BBox Max']]['value'] = bmax
    if 'CORNICE_STYLE' in idmap:
        mod.properties.inputs[idmap['CORNICE_STYLE']]['value'] = int(style if style is not None else 1)
    obj.update_tag()
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


def _group_ok(name):
    """A rebuilt group is only usable once its Group Output is wired."""
    g = bpy.data.node_groups.get(name)
    if not g:
        return False
    go = next((n for n in g.nodes if n.bl_idname == 'NodeGroupOutput'), None)
    return (go is not None and 'Geometry' in go.inputs
            and go.inputs['Geometry'].is_linked)


def rollout_all(style=None, strip_bevel=True):
    """Apply v2 detail to all WALL_* (not the curved test) and SLAB_* objects."""
    if not _group_ok('GN_PARIS_WallDetail'):
        build_wall_detail()
    if not _group_ok('GN_PARIS_SlabTrim'):
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
                     'Haussmann/Gothic wall trim: bands, panels, arch medallions, quoins.',
                     category='structures')
    register_builder('GN_PARIS_SlabTrim', build_slab_trim,
                     'PARIS Slab Trim v2',
                     'Slab trim UV + in-group bevel for the Paris lane.',
                     category='structures')
    print('[paris_wall_detail] registered builders into the Melodia Studio registry')
except ImportError:
    print('[paris_wall_detail] standalone mode (no core registry)')
