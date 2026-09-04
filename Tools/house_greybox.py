"""Melusina's House — built on the real deploy/surreal_greybox kit.

Uses rect_room_shell, build_greybox_tower, build_greybox_pillar_hall,
and build_greybox_corridor via a lightweight monolith shim.
Plan: melusinashouseplan.md (13.2m wide, 9.8m deep, 3.42m wall).
"""
import bpy
import os
import sys
from types import SimpleNamespace

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GB = os.path.join(REPO, "deploy", "surreal_greybox")
if GB not in sys.path:
    sys.path.insert(0, GB)

import primitives
import shells
import facades
import towers

print("=== HOUSE GREYBOX BUILD ===")


class ShimMonolith:
    """Minimal monolith: safe node creation, linking, color tags,
    plus the gb_* primitives the kit builders call."""

    def _safe_node(self, tree, bl_idname, loc=(0, 0)):
        try:
            n = tree.nodes.new(bl_idname)
            n.location = loc
            return n
        except Exception:
            return None

    def _link(self, tree, src, dst):
        try:
            tree.links.new(src, dst)
        except Exception:
            pass

    def color_node(self, node, key):
        pass

    def _gb_box(self, tree, size, loc_xyz, x, y, label="level"):
        cube = self._safe_node(tree, "GeometryNodeMeshCube", (x, y))
        if cube is None:
            return None
        try:
            cube.inputs["Size"].default_value = size
        except Exception:
            pass
        tr = self._safe_node(tree, "GeometryNodeTransform", (x + 200, y))
        if tr is None:
            return cube.outputs["Mesh"]
        try:
            tr.inputs["Translation"].default_value = loc_xyz
        except Exception:
            pass
        self._link(tree, cube.outputs["Mesh"], tr.inputs["Geometry"])
        return tr.outputs["Geometry"]

    def _gb_join(self, tree, parts, x, y=0, label="output"):
        parts = [p for p in parts if p is not None]
        if not parts:
            return None
        if len(parts) == 1:
            return parts[0]
        join = self._safe_node(tree, "GeometryNodeJoinGeometry", (x, y))
        if join is None:
            return parts[0]
        for p in parts:
            self._link(tree, p, join.inputs["Geometry"])
        return join.outputs["Mesh"]

    def _gb_bool_diff(self, tree, base_geom, cutters, x, y=0):
        cutters = [c for c in cutters if c is not None]
        if base_geom is None or not cutters:
            return base_geom
        boolean = self._safe_node(tree, "GeometryNodeMeshBoolean", (x, y))
        if boolean is None:
            return base_geom
        try:
            boolean.operation = "DIFFERENCE"
        except Exception:
            pass
        try:
            self._link(tree, base_geom, boolean.inputs["Mesh 1"])
            for c in cutters:
                self._link(tree, c, boolean.inputs["Mesh 2"])
        except Exception:
            return base_geom
        try:
            return boolean.outputs["Mesh"]
        except Exception:
            return base_geom

    def _gb_trim_mode(self, props):
        return getattr(props, "gb_trim_mode", "RECESS")

    def _gb_trim_depth(self, props, wall_t):
        return max(0.005, getattr(props, "gb_trim_recess", 0.04))


M = ShimMonolith()
for mod in (primitives, shells, facades, towers):
    mod.bind(M)
primitives.attach_to_monolith(M)
print("Greybox kit bound: primitives, shells, facades, towers")

# --- Scene setup per plan: metric, collections ---
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.unit_settings.system = 'METRIC'
bpy.context.scene.unit_settings.length_unit = 'METERS'

for cname in ("MH_GUIDES", "MH_SOURCE_KIT", "MH_GN_OUTPUT",
              "MH_MATERIALS", "MH_LIGHTING"):
    col = bpy.data.collections.new(cname)
    bpy.context.scene.collection.children.link(col)

out_col = bpy.data.collections.get("MH_GN_OUTPUT")

# --- Plan dimensions ---
W, D, H, T = 13.2, 9.8, 3.42, 0.30

main_props = SimpleNamespace(
    gb_width=W, gb_depth=D, gb_height=H, gb_wall_thick=T,
    gb_door_height=2.35, gb_door_width=1.15,
    gb_window_width=0.8, gb_window_height=0.8,
    gb_window_sill=1.0, gb_windows_enabled=True,
    gb_window_count_ns=3, gb_window_count_ew=2,
    gb_window_has_mullion=True, gb_window_glazing=True,
    gb_ceiling=False, gb_trim_mode="RECESS", gb_trim_recess=0.04,
)


def make_obj(name, tree_name):
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    out_col.objects.link(obj)
    mod = obj.modifiers.new("GN", type='NODES')
    tree = bpy.data.node_groups.new(tree_name, "GeometryNodeTree")
    mod.node_group = tree
    inp = tree.nodes.new("NodeGroupInput")
    inp.location = (-600, 0)
    outp = tree.nodes.new("NodeGroupOutput")
    outp.location = (2200, 0)
    tree.interface.new_socket(
        name="Geometry", socket_type="NodeSocketGeometry", in_out='OUTPUT')
    return obj, tree, outp


# GN_MH_02 main room shell with real door/window openings
obj, tree, outp = make_obj("MH_MainShell", "GN_MH_02_CurvedWallShell")
parts = shells.rect_room_shell(tree, main_props, W, D, H, T, 0, 0)
joined = M._gb_join(tree, parts, 1600, 0)
if joined is not None:
    tree.links.new(joined, outp.inputs["Geometry"])
print(f"MainShell: {len(parts)} parts with door/window cutters")

# GN_MH_06 tower
tower_props = SimpleNamespace(
    gb_floors=3, gb_height=3.4, gb_width=1.8, gb_depth=1.8,
    gb_wall_thick=0.30, gb_door_width=1.15, gb_door_height=2.35,
)
tobj, ttree, toutp = make_obj("MH_Tower", "GN_MH_06_TowerChimney")
tower_out = towers.build_greybox_tower(ttree, tower_props, 0)
if tower_out is not None:
    ttree.links.new(tower_out, toutp.inputs["Geometry"])
tobj.location = (4.5, 7.5, 0)
print("Tower: 3 floors with window cutters at (4.5, 7.5)")

# GN_MH_01 porch as pillar hall
porch_props = SimpleNamespace(
    gb_cols_x=4, gb_cols_y=2, gb_spacing=1.7, gb_height=3.42,
    gb_wall_thick=0.30, gb_leg_thick=0.12,
)
pobj, ptree, poutp = make_obj("MH_Porch", "GN_MH_01_FoundationPorch")
porch_out = facades.build_greybox_pillar_hall(ptree, porch_props, 0)
if porch_out is not None:
    ptree.links.new(porch_out, poutp.inputs["Geometry"])
pobj.location = (4.0, 0.9, 0.45)
print("Porch: 4x2 pillar hall")

# GN_MH_11 interior corridor shell
corr_props = SimpleNamespace(
    gb_corridor_profile="DOUBLE", gb_corridor_length=6.0,
    gb_height=3.0, gb_wall_thick=0.25, gb_ceiling=True,
    gb_corridor_rib_mode="INSET", gb_trim_mode="RECESS",
    gb_trim_recess=0.04, gb_junction_column=True,
)
cobj, ctree, coutp = make_obj("MH_Interior", "GN_MH_11_InteriorShell")
corr_out = shells.build_greybox_corridor(ctree, corr_props, 0)
if corr_out is not None:
    ctree.links.new(corr_out, coutp.inputs["Geometry"])
cobj.location = (6.6, 4.9, 0.45)
print("Interior: double corridor with ribs + wainscot")

# --- Plan palette materials ---
def make_mat(name, color, rough=0.5, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    return m

mat_plaster = make_mat("M_MH_PearlPlaster_Pink", (0.968, 0.839, 0.905, 1.0), 0.6)
mat_roof = make_mat("M_MH_Roof_IridescentBlue", (0.431, 0.541, 0.686, 1.0), 0.25, 0.7)
mat_brass = make_mat("M_MH_GoldBrass", (0.776, 0.631, 0.353, 1.0), 0.35, 0.9)
mat_wood = make_mat("M_MH_WoodWarm", (0.45, 0.30, 0.18, 1.0), 0.7)
mat_glass = make_mat("M_MH_AquaGlass", (0.55, 0.80, 0.85, 1.0), 0.1, 0.2)

obj.data.materials.append(mat_plaster)
tobj.data.materials.append(mat_plaster)
pobj.data.materials.append(mat_wood)
cobj.data.materials.append(mat_plaster)

os.makedirs("Saved/MelusinasHouse", exist_ok=True)
bpy.ops.wm.save_mainfile(filepath="Saved/MelusinasHouse/House_Greybox.blend")

print("\n=== GREYBOX HOUSE COMPLETE ===")
for o in out_col.objects:
    print(f"  {o.name}")
print("Saved: Saved/MelusinasHouse/House_Greybox.blend")
