import unreal
import json
import math
import random

# ============================================================
# HEIGHT-AWARE PLACEMENT - Direct landscape height access
# ============================================================

random.seed(2026)

actors = unreal.EditorLevelLibrary.get_all_level_actors()

# Find landscape
landscape = None
for a in actors:
    if "CanonicalLandscape" in a.get_actor_label():
        landscape = a
        break

if landscape is None:
    print("[FATAL] CanonicalLandscape not found")
    exit()

print(f"Landscape: {landscape.get_actor_label()}")

# Get landscape height using built-in method
# Landscape has GetHeightAtLocation actor method
loc = landscape.get_actor_location()
print(f"Actor location: [{loc.x:.0f},{loc.y:.0f},{loc.z:.0f}]")

# Get bounds
bounds = landscape.get_bounds()
print(f"Bounds: origin=[{bounds.origin.x:.0f},{bounds.origin.y:.0f},{bounds.origin.z:.0f}], extent=[{bounds.extent.x:.0f},{bounds.extent.y:.0f},{bounds.extent.z:.0f}]")

# Min/Max Z
min_z = bounds.origin.z - bounds.extent.z
max_z = bounds.origin.z + bounds.extent.z
print(f"Z range: {min_z:.0f} to {max_z:.0f}")

# Get height at specific points using landscape component data
# Use get_editor_property for heightmap data
heightmap = landscape.get_editor_property("landscape_heightmap")
print(f"Heightmap: {heightmap}")

# Try to get heightmap size
if heightmap:
    size = heightmap.get_editor_property("size")
    print(f"Heightmap size: {size}")
    
    # Get height at specific UV coords
    # Heightmap is a texture, we can sample it
    # But this is complex - let's use a simpler approach
    
# Simpler: use the landscape collision
# Get all landscape components
comps = landscape.get_components_by_class(unreal.LandscapeComponent)
print(f"Landscape components: {len(comps)}")

if len(comps) > 0:
    comp = comps[0]
    # Get section size
    section_size = comp.get_editor_property("section_size")
    print(f"Section size: {section_size}")
    
    # Get component bounds
    comp_bounds = comp.get_bounds()
    print(f"Component bounds: origin=[{comp_bounds.origin.x:.0f},{comp_bounds.origin.y:.0f},{comp_bounds.origin.z:.0f}], extent=[{comp_bounds.extent.x:.0f},{comp_bounds.extent.y:.0f},{comp_bounds.extent.z:.0f}]")
