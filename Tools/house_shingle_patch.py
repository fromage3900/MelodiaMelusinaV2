"""GN_MH_04 shingle patch proof — 2x2 m, UV-space rows, Sample UV Surface.

Plan ss 6: 0-1 UV grid, Index row/col math, alternate-row 0.5 offset,
Sample UV Surface for Position+Normal, align, InstanceOnPoints tile
variants, scale 0.95-1.05. Tile 0.28 x 0.36, overlap 40%.
Expected: cols=7 rows=9, 63 instances.
"""
import bpy
import os

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.unit_settings.system = 'METRIC'
col = bpy.data.collections.new("MH_GN_OUTPUT")
sc.collection.children.link(col)

mesh = bpy.data.meshes.new("MH_ShinglePatch")
obj = bpy.data.objects.new("MH_ShinglePatch", mesh)
col.objects.link(obj)
mod = obj.modifiers.new("GN", type='NODES')
tree = bpy.data.node_groups.new("GN_MH_04_ScallopShingles_patch", "GeometryNodeTree")
mod.node_group = tree
nodes = tree.nodes
links = tree.links


def add(bid, loc):
    try:
        n = nodes.new(bid)
        n.location = loc
        return n
    except Exception as e:
        print(f"SKIP {bid}: {e}")
        return None


def sdef(n, key, val):
    try:
        n.inputs[key].default_value = val
    except Exception as e:
        print(f"def {key}: {e}")


gin = add("NodeGroupInput", (-800, 0))
gout = add("NodeGroupOutput", (2600, 0))
try:
    tree.interface.new_socket(name="Geometry", socket_type="NodeSocketGeometry", in_out='OUTPUT')
except Exception as e:
    print(f"sock: {e}")

# Roof plane 2x2 m (Grid) with default UVs
grid = add("GeometryNodeMeshGrid", (0, 300))
sdef(grid, "Size X", 2.0)
sdef(grid, "Size Y", 2.0)
sdef(grid, "Vertices X", 3)
sdef(grid, "Vertices Y", 3)

# UV point lattice: Grid 7 x 9 in 0..1 (position doubles as sample UV)
COLS, ROWS = 7, 9
uvg = add("GeometryNodeMeshGrid", (0, -200))
sdef(uvg, "Size X", 1.0)
sdef(uvg, "Size Y", 1.0)
sdef(uvg, "Vertices X", COLS)
sdef(uvg, "Vertices Y", ROWS)

# Tile variant: squashed UV sphere (scallop proxy), 3 scales via 3 instances?
tile = add("GeometryNodeMeshUVSphere", (0, -600))
try:
    tile.inputs["Segments"].default_value = 8
    tile.inputs["Rings"].default_value = 4
    tile.inputs["Radius"].default_value = 0.14
except Exception as e:
    print(f"tile: {e}")
tscale = add("GeometryNodeTransform", (200, -600))
try:
    tscale.inputs["Scale"].default_value = (1.0, 1.3, 0.35)
except Exception as e:
    print(f"tscale: {e}")
try:
    links.new(tile.outputs["Mesh"], tscale.inputs["Geometry"])
except Exception as e:
    print(f"tile link: {e}")

# Sample UV Surface: roof mesh + UV from lattice positions
samp = add("GeometryNodeSampleUVSurface", (600, -100))
# feed: Mesh <- roof grid, Sample UV <- lattice position attribute
pos = add("GeometryNodeInputPosition", (300, -300))
try:
    links.new(grid.outputs["Mesh"], samp.inputs["Mesh"])
    links.new(pos.outputs["Position"], samp.inputs["Sample UV"])
except Exception as e:
    print(f"samp link: {e}")

# Realize the sampled positions onto lattice points via Set Position
# (lattice Mesh -> Points? use Mesh to Points first)
m2p = add("GeometryNodeMeshToPoints", (600, -400))
try:
    links.new(uvg.outputs["Mesh"], m2p.inputs["Mesh"])
except Exception as e:
    print(f"m2p: {e}")
setp = add("GeometryNodeSetPosition", (1000, -300))
try:
    links.new(m2p.outputs["Points"], setp.inputs["Geometry"])
    # Sampled Value -> Position
    links.new(samp.outputs["Value"], setp.inputs["Position"])
except Exception as e:
    print(f"setp: {e}")

# Instance tiles on points
inst = add("GeometryNodeInstanceOnPoints", (1400, -300))
try:
    links.new(setp.outputs["Geometry"], inst.inputs["Points"])
    links.new(tscale.outputs["Geometry"], inst.inputs["Instance"])
except Exception as e:
    print(f"inst: {e}")

# Join roof + instances for one output
join = add("GeometryNodeJoinGeometry", (2000, -100))
try:
    links.new(grid.outputs["Mesh"], join.inputs["Geometry"])
    links.new(inst.outputs["Instances"], join.inputs["Geometry"])
    links.new(join.outputs["Geometry"], gout.inputs["Geometry"])
except Exception as e:
    print(f"out: {e}")

os.makedirs("Saved/MelusinasHouse", exist_ok=True)
bpy.ops.wm.save_mainfile(filepath="Saved/MelusinasHouse/House_ShinglePatch.blend")
print(f"PATCH: nodes={len(tree.nodes)} expect_instances={COLS*ROWS}")
