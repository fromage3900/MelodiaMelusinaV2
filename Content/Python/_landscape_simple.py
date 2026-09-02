import unreal

# Simpler: Get landscape Z at point using line trace
actors = unreal.EditorLevelLibrary.get_all_level_actors()

# Find landscape
landscape = None
for a in actors:
    if "CanonicalLandscape" in a.get_actor_label():
        landscape = a
        break

print(f"Landscape Z: {landscape.get_actor_location().z:.0f}")

# Get landscape component for collision data
comps = landscape.get_components_by_class(unreal.LandscapeComponent)
print(f"Components: {len(comps)}")

if comps:
    comp = comps[0]
    # Get section base
    base = comp.get_editor_property("section_base")
    print(f"Section base: {base}")
    
    # Get section size
    size = comp.get_editor_property("section_size")
    print(f"Section size: {size}")
    
    # Get subsections
    subsections = comp.get_editor_property("subsection_size")
    print(f"Subsection size: {subsections}")
    
    # Try to get height data from component
    height_data = comp.get_editor_property("height_data")
    print(f"Height data: {height_data}")
    
    # Get landscape heightmap
    heightmap = comp.get_editor_property("heightmap_texture")
    if heightmap:
        print(f"Heightmap texture: {heightmap.get_name()}")
        
        # Get size
        size = heightmap.get_editor_property("size")
        print(f"Heightmap size: {size}")
        
        # Sample height at UV
        # Heightmap is a texture, we can get data
        # But this requires C++ access
        # Let's use a simpler approach - just get the Z from the actor
        pass
    
    # Get component bounds
    origin = comp.get_editor_property("bounds_origin")
    extent = comp.get_editor_property("bounds_extent")
    print(f"Bounds: origin=[{origin.x:.0f},{origin.y:.0f},{origin.z:.0f}], extent=[{extent.x:.0f},{extent.y:.0f},{extent.z:.0f}]")
    
    # Min/max Z
    min_z = origin.z - extent.z
    max_z = origin.z + extent.z
    print(f"Z range: {min_z:.0f} to {max_z:.0f}")
