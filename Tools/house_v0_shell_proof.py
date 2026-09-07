"""V0 shell convergence proof — greybox kit vs mh6 genome shell via C1 adapter.

Gate rule (Docs/MelodiaStudio/MELUSINA_HOUSE_V7_PLAN.md, V0): the converged
shell must match the stock cell's bbox exactly at the same params, openings
must survive, Depth must be honored. PASS here unlocks rewiring
MEL_city_house_cell onto MEL_mh6_room_shell.

Checks performed:
1. identity  — greybox vs mh6(+adapter, Cornice 0): bbox match within tol,
               base at z=0 (adapter lift applied through its RETURNED socket)
2. guard     — Opening Columns=0 Rows=0 must NOT collapse to a ~112-vert plane
               (PR #96 empty-cutter guard)
3. openings  — 3x2 cutters must ADD rim verts vs the 0x0 solid
4. depth     — Wall Thickness honored: hollow 0.3-thick shell must differ from
               a 2.0-thick one and keep full Y span (PR #96 thin-wall fix)

Run:  blender --background --python Tools/house_v0_shell_proof.py
Out:  console table + Saved/Audit/melusinashouse/v0_proof_last.json
"""
import bpy, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
OUT = os.path.join(REPO, "Saved", "Audit", "melusinashouse", "v0_proof_last.json")
sys.path.insert(0, os.path.join(REPO, "deploy"))
# measure the REPO tree, not the AppData autoload
for _m in [m for m in list(sys.modules) if m == "surreal_arch" or m.startswith("surreal_arch.")]:
    del sys.modules[_m]
import surreal_arch
assert surreal_arch.__file__.replace("\\", "/").startswith(REPO.replace("\\", "/")), \
    f"must load repo copy, got {surreal_arch.__file__}"

from surreal_arch.melodia_gn import core
from surreal_arch.melodia_gn.melodia_house import mh6_shell_adapter

L, W, H, T = 6.0, 4.0, 3.0, 0.3
TOL = 0.05  # meters — adapter compensation is exact; tolerance covers bevel bands


def _value(tree, v, y):
    n = tree.nodes.new("ShaderNodeValue")
    n.location = (-1100, y)
    n.outputs[0].default_value = v
    return n.outputs[0]


def realize(tree_name, configure):
    """Build PROOF tree nesting `tree_name`; `configure(tree, nest)` sets params
    and may RETURN the geometry output socket to wire (adapter lift)."""
    res = core.GROUP_BUILDERS[tree_name]()
    sub = res[0] if isinstance(res, (tuple, list)) else res
    tree = bpy.data.node_groups.new("PROOF_" + tree_name + str(id(configure)), "GeometryNodeTree")
    tree.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    tree.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gin = tree.nodes.new("NodeGroupInput")
    gout = tree.nodes.new("NodeGroupOutput")
    nest = tree.nodes.new("GeometryNodeGroup")
    nest.node_tree = sub
    out_sock = configure(tree, nest)
    if out_sock is None:
        out_sock = next((o for o in nest.outputs if o.type == 'GEOMETRY'), nest.outputs[-1])
    tree.links.new(gin.outputs[0], nest.inputs[0])
    tree.links.new(out_sock, gout.inputs[0])
    me = bpy.data.meshes.new("PROOF")
    ob = bpy.data.objects.new("PROOF", me)
    bpy.context.scene.collection.objects.link(ob)
    mod = ob.modifiers.new("p", 'NODES')
    mod.node_group = tree
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    m2 = ev.to_mesh()
    n = len(m2.vertices) if m2 else 0
    if m2 and n:
        xs = [v.co.x for v in m2.vertices]
        ys = [v.co.y for v in m2.vertices]
        zs = [v.co.z for v in m2.vertices]
        bbox = (round(max(xs)-min(xs), 3), round(max(ys)-min(ys), 3), round(max(zs)-min(zs), 3))
        zmin = round(min(zs), 3)
        ev.to_mesh_clear()
    else:
        bbox = (0, 0, 0)
        zmin = 0.0
    bpy.data.objects.remove(ob)
    return n, bbox, zmin


def cfg_greybox(tree, nest):
    vals = {"Room Length": L, "Room Width": W, "Room Height": H,
            "Wall Thickness": T, "Ceiling": 1}
    for s in nest.inputs:
        if s.name in vals:
            try:
                s.default_value = vals[s.name]
            except Exception:
                pass


def cfg_mh6_via_adapter(tree, nest, thick=T, cols=None, rows=None, cornice=0.0):
    mapping = {"Room Length": _value(tree, L, 0), "Room Width": _value(tree, W, -100),
               "Room Height": _value(tree, H, -200), "Wall Thickness": _value(tree, thick, -300),
               "Cornice Rise": cornice, "Cornice Depth": 0.0}
    out = mh6_shell_adapter(nest, mapping)  # returns the +T-lifted socket
    if cols is not None and "Opening Columns" in nest.inputs:
        nest.inputs["Opening Columns"].default_value = cols
    if rows is not None and "Opening Rows" in nest.inputs:
        nest.inputs["Opening Rows"].default_value = rows
    return out


print("=== V0 SHELL PROOF ===")
vg, bg, zg = realize("MEL_greybox_room_kit", cfg_greybox)
vi, bi, zi = realize("MEL_mh6_room_shell", lambda t, n: cfg_mh6_via_adapter(t, n))
vs, bs, zs = realize("MEL_mh6_room_shell", lambda t, n: cfg_mh6_via_adapter(t, n, cols=0, rows=0))
vo, bo, zo = realize("MEL_mh6_room_shell", lambda t, n: cfg_mh6_via_adapter(t, n, cols=3, rows=2))
vd, bd, zd = realize("MEL_mh6_room_shell", lambda t, n: cfg_mh6_via_adapter(t, n, thick=2.0, cols=0, rows=0))

identity_ok = all(abs(a-b) <= TOL for a, b in zip(bg, bi)) and abs(zg - zi) <= TOL
guard_ok = vs > 1000 and all(abs(a-b) <= TOL for a, b in zip(bg, bs))
openings_ok = vo > vs
depth_ok = vd != vs and abs(bd[1] - bs[1]) <= TOL and vd < vs  # thicker walls consume cavity

for label, v, b, z in (("greybox  ", vg, bg, zg), ("mh6+C1   ", vi, bi, zi),
                       ("mh6 0x0  ", vs, bs, zs), ("mh6 3x2  ", vo, bo, zo),
                       ("mh6 T=2.0", vd, bd, zd)):
    print(f"{label} verts={v:>7} bbox={b} zmin={z}")
checks = dict(identity=identity_ok, empty_cutter_guard=guard_ok,
              openings_survive=openings_ok, depth_honored=depth_ok)
verdict = "PASS" if all(checks.values()) else "FAIL"
print("checks:", checks)
print(f"V0 PROOF: {verdict}")
results = dict(greybox=dict(verts=vg, bbox=list(bg), zmin=zg),
               converged=dict(verts=vi, bbox=list(bi), zmin=zi),
               solid_0x0=dict(verts=vs, bbox=list(bs)),
               opened_3x2=dict(verts=vo, bbox=list(bo)),
               thick_T2=dict(verts=vd, bbox=list(bd)),
               params=dict(L=L, W=W, H=H, T=T, tol=TOL),
               checks=checks, verdict=verdict)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w") as f:
    json.dump(results, f, indent=1)
print("wrote", OUT)
