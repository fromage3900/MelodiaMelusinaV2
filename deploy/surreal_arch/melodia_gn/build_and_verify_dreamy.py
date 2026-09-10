"""Build all 6 dreamy architecture GN groups, save, and verify."""
import sys
import os
import types
import importlib.util
import bpy

deploy_dir = r'P:/MelodiaMelusinaV2-Laptop/deploy'
surreal_arch_dir = os.path.join(deploy_dir, 'surreal_arch')
gn_dir = os.path.join(surreal_arch_dir, 'melodia_gn')

# Save the file when we're done
SAVE_FILE = r"P:/MelodiaMelusinaV2-Laptop/Saved/MelusinasHouse/DreamyArchitectureGN.blend"

# Set up package manually
package = types.ModuleType("melodia_gn")
package.__path__ = [gn_dir]
sys.modules["melodia_gn"] = package
sa_package = types.ModuleType("surreal_arch")
sa_package.__path__ = [surreal_arch_dir]
sys.modules["surreal_arch"] = sa_package

# Load core
spec = importlib.util.spec_from_file_location("melodia_gn.core", os.path.join(gn_dir, "core.py"))
core = importlib.util.module_from_spec(spec)
sys.modules["melodia_gn.core"] = core
spec.loader.exec_module(core)

# Load builder modules
def load_module(name, file):
    path = os.path.join(gn_dir, file)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

modules = {}
for name, file in [
    ("primitives", "primitives.py"),
    ("dreamy_gothic_arch", "dreamy_gothic_arch.py"),
    ("rose_window", "rose_window.py"),
    ("curved_wall", "curved_wall.py"),
    ("ornament_strip", "ornament_strip.py"),
    ("gold_light_strip", "gold_light_strip.py"),
    ("barrel_vault_kit", "barrel_vault_kit.py"),
]:
    modules[name] = load_module(f"melodia_gn.{name}", file)
    print(f"Loaded module: {name}")

# Build all GN groups
builders = {
    "MEL_circular_array": modules["primitives"].build_circular_array,
    "MEL_dreamy_gothic_arch": modules["dreamy_gothic_arch"].build_dreamy_gothic_arch,
    "MEL_rose_window_small": modules["rose_window"].build_rose_window_small,
    "MEL_curved_wall": modules["curved_wall"].build_curved_wall,
    "MEL_gold_ornament_strip": modules["ornament_strip"].build_gold_ornament_strip,
    "MEL_gold_light_strip": modules["gold_light_strip"].build_gold_light_strip,
    "MEL_barrel_vault_ceiling": modules["barrel_vault_kit"].build_barrel_vault_ceiling,
}

print("\n=== Building GN groups ===")
results = {}
for gn_name, build_fn in builders.items():
    # Remove existing if present
    if gn_name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[gn_name])
    
    try:
        tree = build_fn(gn_name)
        if tree is not None:
            tree.name = gn_name
            n_nodes = len(tree.nodes)
            n_links = len(tree.links)
            results[gn_name] = (n_nodes, n_links, "OK")
            print(f"  BUILT: {gn_name} — {n_nodes} nodes, {n_links} links")
        else:
            results[gn_name] = (0, 0, "FAILED: returned None")
            print(f"  FAILED: {gn_name} — returned None")
    except Exception as e:
        import traceback
        traceback.print_exc()
        results[gn_name] = (0, 0, f"ERROR: {e}")
        print(f"  ERROR: {gn_name} — {e}")

# Summary
print("\n=== BUILD SUMMARY ===")
success_count = sum(1 for r in results.values() if r[2] == "OK")
failed_count = len(results) - success_count
for name, (n_nodes, n_links, status) in sorted(results.items()):
    print(f"  {name}: {status}")
print(f"\n{success_count}/{len(results)} GN groups built successfully")

# Verify all trees exist
print("\n=== VERIFICATION ===")
expected_trees = [
    "MEL_dreamy_gothic_arch",
    "MEL_rose_window_small",
    "MEL_curved_wall",
    "MEL_gold_ornament_strip",
    "MEL_gold_light_strip",
    "MEL_barrel_vault_ceiling",
]

all_ok = True
for tree_name in expected_trees:
    if tree_name in bpy.data.node_groups:
        ng = bpy.data.node_groups[tree_name]
        n_nodes = len(ng.nodes)
        n_links = len(ng.links)
        print(f"  {tree_name}: OK — {n_nodes} nodes, {n_links} links")
    else:
        print(f"  {tree_name}: MISSING")
        all_ok = False

# Check for missing/unresolved nodes
print("\n=== NODE TYPE CHECK ===")
for tree_name in expected_trees:
    if tree_name in bpy.data.node_groups:
        ng = bpy.data.node_groups[tree_name]
        for node in ng.nodes:
            if hasattr(node, 'bl_idname'):
                if node.bl_idname.startswith("NODETYPE_") or "MISSING" in node.bl_idname:
                    print(f"  {tree_name}: WARNING — missing node: {node.name} ({node.bl_idname})")

# Test instantiation on a cube
print("\n=== Instantiation Test ===")
if "TestCube" in bpy.data.objects:
    bpy.data.objects.remove(bpy.data.objects["TestCube"])
bpy.ops.mesh.primitive_cube_add(size=2)
test_obj = bpy.context.active_object
test_obj.name = "TestCube"

for tree_name in expected_trees:
    if tree_name not in bpy.data.node_groups:
        continue
    
    for mod in list(test_obj.modifiers):
        if mod.type == 'NODE_TREE':
            test_obj.modifiers.remove(mod)
    
    mod = test_obj.modifiers.new(f"GN_{tree_name}", type='NODES')
    mod.node_group = bpy.data.node_groups[tree_name]
    
    try:
        bpy.context.view_layer.update()
        print(f"  {tree_name}: modifier attached OK")
    except Exception as e:
        print(f"  {tree_name}: UPDATE ERROR — {e}")

# Save the file with all GN groups
print(f"\n=== Saving to {SAVE_FILE} ===")
os.makedirs(os.path.dirname(SAVE_FILE), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=SAVE_FILE)
print("File saved.")

# Clean up test cube
if "TestCube" in bpy.data.objects:
    bpy.data.objects.remove(bpy.data.objects["TestCube"])

if all_ok:
    print("\nAll 6 dreamy architecture GN groups built, verified, and saved.")
else:
    print("\nSome GN groups need attention.")
    sys.exit(1)
