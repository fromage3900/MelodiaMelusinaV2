import bpy, os, sys
from types import SimpleNamespace
REPO = os.getcwd()
sys.path.insert(0, os.path.join(REPO, "deploy", "surreal_greybox"))
sys.path.insert(0, os.path.join(REPO, "deploy"))
for _m in [m for m in list(sys.modules) if m == 'surreal_arch' or m.startswith('surreal_arch.')]:
    del sys.modules[_m]
import primitives, shells
from surreal_arch import zen_kit

class M:
    def _s(self, tree, b, loc):
        try:
            n = tree.nodes.new(b); n.location = loc; return n
        except Exception: return None
    def _l(self, tree, s, d):
        try: tree.links.new(s, d)
        except Exception: pass
    def _gb_box(self, tree, size, xyz, x, y, label="level"):
        c = self._s(tree, "GeometryNodeMeshCube", (x, y))
        if c is None: return None
        try: c.inputs["Size"].default_value = size
        except Exception: pass
        t = self._s(tree, "GeometryNodeTransform", (x+200, y))
        if t is None: return c.outputs["Mesh"]
        try: t.inputs["Translation"].default_value = xyz
        except Exception: pass
        self._l(tree, c.outputs["Mesh"], t.inputs["Geometry"])
        return t.outputs["Geometry"]
    def _gb_trim_mode(self, props):
        return getattr(props, "gb_trim_mode", "RECESS")
    def _gb_trim_depth(self, props, wall_t):
        return max(0.005, getattr(props, "gb_trim_recess", 0.04))
    def _gb_join(self, tree, parts, x, y=0, label="output"):
        parts=[p for p in parts if p is not None]
        if len(parts)<=1: return parts[0] if parts else None
        j = self._s(tree, "GeometryNodeJoinGeometry", (x, y))
        if j is None: return parts[0]
        for p in parts: self._l(tree, p, j.inputs["Geometry"])
        return j.outputs["Geometry"]

M_ = M()
bpy.ops.wm.read_factory_settings(use_empty=True)
def run(name, fn, props):
    tree = bpy.data.node_groups.new(name, "GeometryNodeTree")
    gi = tree.nodes.new("NodeGroupInput"); go = tree.nodes.new("NodeGroupOutput")
    try: tree.interface.new_socket(name="Geometry", socket_type="NodeSocketGeometry", in_out='OUTPUT')
    except Exception: pass
    out = fn(tree, M_, props, 0) if fn.__module__ != 'shells' else fn(tree, props, 0)
    if out is not None:
        try: tree.links.new(out, go.inputs["Geometry"])
        except Exception as e: print(name, "outlink:", str(e)[:80])
    print(f"{name}: nodes={len(tree.nodes)}")
    return tree

p_allee = SimpleNamespace(gb_length=6.0, gb_width=2.6, gb_height=0.32, gb_wall_thick=0.1)
t1 = run("T_ALLEE", zen_kit.build_zen_cherry_allee, p_allee)
p_tea = SimpleNamespace(teahouse_width=5.0, teahouse_depth=4.5, gb_height=2.6, gb_wall_thick=0.14)
t2 = run("T_TEA", zen_kit.build_zen_teahouse, p_tea)
p_gb = SimpleNamespace(gb_length=6.0, gb_width=3.0, gb_height=3.2, gb_wall_thick=0.3, gb_trim_mode="RECESS", gb_trim_recess=0.04)
shells.bind(M_)
t3 = run("T_BEND", shells.build_greybox_corridor_bend, p_gb)
t4 = run("T_TEE", shells.build_greybox_corridor_t, p_gb)
# evaluate
sc = bpy.context.scene
col = bpy.data.collections.new("V"); sc.collection.children.link(col)
dg = bpy.context.evaluated_depsgraph_get()
for oname, t in [("O_ALLEE",t1),("O_TEA",t2),("O_BEND",t3),("O_TEE",t4)]:
    o = bpy.data.objects.new(oname, bpy.data.meshes.new(oname))
    col.objects.link(o)
    md = o.modifiers.new("GN", type='NODES'); md.node_group = t
dg = bpy.context.evaluated_depsgraph_get()
for oname in ["O_ALLEE","O_TEA","O_BEND","O_TEE"]:
    ev = bpy.data.objects[oname].evaluated_get(dg)
    print(f"{oname}: verts={len(ev.data.vertices)} faces={len(ev.data.polygons)}")
