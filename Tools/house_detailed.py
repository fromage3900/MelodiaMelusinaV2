import bpy
import os

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.unit_settings.system = 'METRIC'
bpy.context.scene.unit_settings.length_unit = 'METERS'

print("=== BUILDING DETAILED HOUSE ===")

house_col = bpy.data.collections.new("House_Detailed")
bpy.context.scene.collection.children.link(house_col)

# === FOUNDATION ===
fnd_mesh = bpy.data.meshes.new("Foundation")
fnd_obj = bpy.data.objects.new("Foundation", fnd_mesh)
house_col.objects.link(fnd_obj)

mod = fnd_obj.modifiers.new("GN", type='NODES')
tree = bpy.data.node_groups.new("GN_Foundation", "GeometryNodeTree")
mod.node_group = tree

inp = tree.nodes.new("NodeGroupInput")
inp.location = (-600, 0)
outp = tree.nodes.new("NodeGroupOutput")
outp.location = (600, 0)

tree.interface.new_socket(name="Width", socket_type="NodeSocketFloat", in_out='INPUT').default_value = 13.2
tree.interface.new_socket(name="Depth", socket_type="NodeSocketFloat", in_out='INPUT').default_value = 9.8
tree.interface.new_socket(name="Height", socket_type="NodeSocketFloat", in_out='INPUT').default_value = 0.45
tree.interface.new_socket(name="Geometry", socket_type="NodeSocketGeometry", in_out='OUTPUT')

cube = tree.nodes.new("GeometryNodeMeshCube")
cube.inputs["Size"].default_value = (13.2, 9.8, 0.45)

trans = tree.nodes.new("GeometryNodeTransform")
trans.inputs["Translation"].default_value = (6.6, 4.9, 0.225)

tree.links.new(cube.outputs["Mesh"], trans.inputs["Geometry"])
tree.links.new(trans.outputs["Geometry"], outp.inputs["Geometry"])

print("Foundation: 13.2 x 9.8 x 0.45")

# === MAIN WALL (concave facade) ===
wall_mesh = bpy.data.meshes.new("Main_Wall")
wall_obj = bpy.data.objects.new("Main_Wall", wall_mesh)
house_col.objects.link(wall_obj)

mod2 = wall_obj.modifiers.new("GN", type='NODES')
tree2 = bpy.data.node_groups.new("GN_MainWall", "GeometryNodeTree")
mod2.node_group = tree2

inp2 = tree2.nodes.new("NodeGroupInput")
inp2.location = (-600, 0)
outp2 = tree2.nodes.new("NodeGroupOutput")
outp2.location = (600, 0)

tree2.interface.new_socket(name="Width", socket_type="NodeSocketFloat", in_out='INPUT').default_value = 13.2
tree2.interface.new_socket(name="Height", socket_type="NodeSocketFloat", in_out='INPUT').default_value = 3.42
tree2.interface.new_socket(name="Thickness", socket_type="NodeSocketFloat", in_out='INPUT').default_value = 0.30
tree2.interface.new_socket(name="WaveAmp", socket_type="NodeSocketFloat", in_out='INPUT').default_value = 0.65
tree2.interface.new_socket(name="Geometry", socket_type="NodeSocketGeometry", in_out='OUTPUT')

# Wall = box + displace for wave
wall_cube = tree2.nodes.new("GeometryNodeMeshCube")
wall_cube.inputs["Size"].default_value = (13.2, 0.30, 3.42)

wall_trans = tree2.nodes.new("GeometryNodeTransform")
wall_trans.inputs["Translation"].default_value = (6.6, 0.15, 1.71)

tree2.links.new(wall_cube.outputs["Mesh"], wall_trans.inputs["Geometry"])
tree2.links.new(wall_trans.outputs["Geometry"], outp2.inputs["Geometry"])

print("Main_Wall: 13.2 x 3.42 x 0.30")

# === SIDE WALLS ===
for side in ['Left', 'Right']:
    x = 0.15 if side == 'Left' else 13.05
    wall_side_mesh = bpy.data.meshes.new(f"Wall_{side}")
    wall_side_obj = bpy.data.objects.new(f"Wall_{side}", wall_side_mesh)
    wall_side_obj.location = (x, 4.9, 1.71)
    house_col.objects.link(wall_side_obj)
    
    m = wall_side_obj.modifiers.new("GN", type='NODES')
    t = bpy.data.node_groups.new(f"GN_Wall_{side}", "GeometryNodeTree")
    m.node_group = t
    
    inp_t = t.nodes.new("NodeGroupInput")
    outp_t = t.nodes.new("NodeGroupOutput")
    t.interface.new_socket(name="Geometry", socket_type="NodeSocketGeometry", in_out='OUTPUT')
    
    c = t.nodes.new("GeometryNodeMeshCube")
    c.inputs["Size"].default_value = (0.30, 9.8, 3.42)
    
    tr = t.nodes.new("GeometryNodeTransform")
    
    t.links.new(c.outputs["Mesh"], tr.inputs["Geometry"])
    t.links.new(tr.outputs["Geometry"], outp_t.inputs["Geometry"])

print("Side walls: Left, Right")

# === BACK WALL ===
back_mesh = bpy.data.meshes.new("Wall_Back")
back_obj = bpy.data.objects.new("Wall_Back", back_mesh)
back_obj.location = (6.6, 9.65, 1.71)
house_col.objects.link(back_obj)

m = back_obj.modifiers.new("GN", type='NODES')
t = bpy.data.node_groups.new("GN_Wall_Back", "GeometryNodeTree")
m.node_group = t

inp_t = t.nodes.new("NodeGroupInput")
outp_t = t.nodes.new("NodeGroupOutput")
t.interface.new_socket(name="Geometry", socket_type="NodeSocketGeometry", in_out='OUTPUT')

c = t.nodes.new("GeometryNodeMeshCube")
c.inputs["Size"].default_value = (13.2, 0.30, 3.42)

tr = t.nodes.new("GeometryNodeTransform")

t.links.new(c.outputs["Mesh"], tr.inputs["Geometry"])
t.links.new(tr.outputs["Geometry"], outp_t.inputs["Geometry"])

print("Wall_Back: 13.2 x 0.30 x 3.42")

# === ROOF (peaked) ===
roof_mesh = bpy.data.meshes.new("Roof_Main")
roof_obj = bpy.data.objects.new("Roof_Main", roof_mesh)
roof_obj.location = (0, 0, 3.42)
house_col.objects.link(roof_obj)

m = roof_obj.modifiers.new("GN", type='NODES')
t = bpy.data.node_groups.new("GN_Roof", "GeometryNodeTree")
m.node_group = t

inp_t = t.nodes.new("NodeGroupInput")
outp_t = t.nodes.new("NodeGroupOutput")
t.interface.new_socket(name="Rise", socket_type="NodeSocketFloat", in_out='INPUT').default_value = 2.55
t.interface.new_socket(name="Overhang", socket_type="NodeSocketFloat", in_out='INPUT').default_value = 0.58
t.interface.new_socket(name="Geometry", socket_type="NodeSocketGeometry", in_out='OUTPUT')

# Use mesh cone for peaked roof (4 sides = pyramid)
roof_cone = t.nodes.new("GeometryNodeMeshCone")
roof_cone.inputs["Radius Bottom"].default_value = 7.5
roof_cone.inputs["Radius Top"].default_value = 0.0
roof_cone.inputs["Depth"].default_value = 2.55
roof_cone.inputs["Vertices"].default_value = 4

roof_trans = t.nodes.new("GeometryNodeTransform")
roof_trans.inputs["Translation"].default_value = (6.6, 4.9, 1.275)
roof_trans.inputs["Rotation"].default_value = (0, 0, 0.785)  # 45 deg

t.links.new(roof_cone.outputs["Mesh"], roof_trans.inputs["Geometry"])
t.links.new(roof_trans.outputs["Geometry"], outp_t.inputs["Geometry"])

print("Roof_Main: 4-sided cone, rise=2.55")

# === TOWER ===
tower_mesh = bpy.data.meshes.new("Tower")
tower_obj = bpy.data.objects.new("Tower", tower_mesh)
tower_obj.location = (4.5, 7.5, 0)
house_col.objects.link(tower_obj)

m = tower_obj.modifiers.new("GN", type='NODES')
t = bpy.data.node_groups.new("GN_Tower", "GeometryNodeTree")
m.node_group = t

inp_t = t.nodes.new("NodeGroupInput")
outp_t = t.nodes.new("NodeGroupOutput")
t.interface.new_socket(name="Height", socket_type="NodeSocketFloat", in_out='INPUT').default_value = 10.5
t.interface.new_socket(name="Radius", socket_type="NodeSocketFloat", in_out='INPUT').default_value = 0.9
t.interface.new_socket(name="Geometry", socket_type="NodeSocketGeometry", in_out='OUTPUT')

cyl = t.nodes.new("GeometryNodeMeshCylinder")
cyl.inputs["Radius"].default_value = 0.9
cyl.inputs["Depth"].default_value = 10.5
cyl.inputs["Vertices"].default_value = 16

t.links.new(cyl.outputs["Mesh"], outp_t.inputs["Geometry"])

print("Tower: cylinder 16v, h=10.5")

# === TOWER DOME ===
dome_mesh = bpy.data.meshes.new("Tower_Dome")
dome_obj = bpy.data.objects.new("Tower_Dome", dome_mesh)
dome_obj.location = (4.5, 7.5, 10.5)
house_col.objects.link(dome_obj)

m = dome_obj.modifiers.new("GN", type='NODES')
t = bpy.data.node_groups.new("GN_Dome", "GeometryNodeTree")
m.node_group = t

inp_t = t.nodes.new("NodeGroupInput")
outp_t = t.nodes.new("NodeGroupOutput")
t.interface.new_socket(name="Geometry", socket_type="NodeSocketGeometry", in_out='OUTPUT')

# Half sphere = uv sphere with limited arcs
dome_sphere = t.nodes.new("GeometryNodeMeshIcoSphere")
dome_sphere.inputs["Radius"].default_value = 0.9
dome_sphere.inputs["Subdivisions"].default_value = 2

t.links.new(dome_sphere.outputs["Mesh"], outp_t.inputs["Geometry"])

print("Tower_Dome: icosphere r=0.9")

# === COLUMNS (8 total) ===
col_positions = [(1.5, 1.0), (3.3, 1.0), (5.1, 1.0), (6.9, 1.0),
                 (1.5, 8.8), (3.3, 8.8), (5.1, 8.8), (6.9, 8.8)]

for i, (x, y) in enumerate(col_positions):
    col_mesh = bpy.data.meshes.new(f"Column_{i}")
    col_obj = bpy.data.objects.new(f"Column_{i}", col_mesh)
    col_obj.location = (x, y, 0)
    house_col.objects.link(col_obj)
    
    m = col_obj.modifiers.new("GN", type='NODES')
    t = bpy.data.node_groups.new(f"GN_Col_{i}", "GeometryNodeTree")
    m.node_group = t
    
    inp_t = t.nodes.new("NodeGroupInput")
    outp_t = t.nodes.new("NodeGroupOutput")
    t.interface.new_socket(name="Geometry", socket_type="NodeSocketGeometry", in_out='OUTPUT')
    
    c = t.nodes.new("GeometryNodeMeshCylinder")
    c.inputs["Radius"].default_value = 0.12
    c.inputs["Depth"].default_value = 3.42
    c.inputs["Vertices"].default_value = 12
    
    t.links.new(c.outputs["Mesh"], outp_t.inputs["Geometry"])

print(f"Columns: {len(col_positions)} cylinders 12v")

# === PORCH FLOOR ===
porch_mesh = bpy.data.meshes.new("Porch_Floor")
porch_obj = bpy.data.objects.new("Porch_Floor", porch_mesh)
porch_obj.location = (4.0, 1.0, 0.45)
house_col.objects.link(porch_obj)

m = porch_obj.modifiers.new("GN", type='NODES')
t = bpy.data.node_groups.new("GN_Porch", "GeometryNodeTree")
m.node_group = t

inp_t = t.nodes.new("NodeGroupInput")
outp_t = t.nodes.new("NodeGroupOutput")
t.interface.new_socket(name="Geometry", socket_type="NodeSocketGeometry", in_out='OUTPUT')

c = t.nodes.new("GeometryNodeMeshCube")
c.inputs["Size"].default_value = (5.0, 1.8, 0.1)

tr = t.nodes.new("GeometryNodeTransform")

t.links.new(c.outputs["Mesh"], tr.inputs["Geometry"])
t.links.new(tr.outputs["Geometry"], outp_t.inputs["Geometry"])

print("Porch_Floor: 5.0 x 1.8 x 0.1")

# === MATERIALS ===
mat_pearl = bpy.data.materials.new("M_PearlPlaster")
mat_pearl.use_nodes = True
mat_pearl.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.969, 0.839, 0.906, 1.0)
mat_pearl.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.4

mat_blue = bpy.data.materials.new("M_RoofBlue")
mat_blue.use_nodes = True
mat_blue.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.431, 0.541, 0.686, 1.0)
mat_blue.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.2
mat_blue.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 0.8

mat_gold = bpy.data.materials.new("M_GoldBrass")
mat_gold.use_nodes = True
mat_gold.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.776, 0.631, 0.353, 1.0)
mat_gold.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 0.9

mat_stone = bpy.data.materials.new("M_Stone")
mat_stone.use_nodes = True
mat_stone.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.69, 0.66, 0.61, 1.0)
mat_stone.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.8

# Assign
for name in ["Foundation", "Main_Wall", "Wall_Left", "Wall_Right", "Wall_Back", "Tower"]:
    obj = house_col.objects.get(name)
    if obj: obj.data.materials.append(mat_pearl)

for name in ["Roof_Main", "Tower_Dome"]:
    obj = house_col.objects.get(name)
    if obj: obj.data.materials.append(mat_blue)

for i in range(8):
    obj = house_col.objects.get(f"Column_{i}")
    if obj: obj.data.materials.append(mat_gold)

porch_obj.data.materials.append(mat_stone)

os.makedirs("Saved/MelusinasHouse", exist_ok=True)
bpy.ops.wm.save_mainfile(filepath="Saved/MelusinasHouse/House_Detailed.blend")

print("\n=== DETAILED HOUSE COMPLETE ===")
print(f"Objects: {len(house_col.objects)}")
for obj in house_col.objects:
    print(f"  {obj.name}")
print(f"Saved: Saved/MelusinasHouse/House_Detailed.blend")
