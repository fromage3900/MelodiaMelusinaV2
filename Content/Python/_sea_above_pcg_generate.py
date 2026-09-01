import unreal
import json

# ============================================================
# PHASE 3: Configure PCG volume bounds + run generation
# ============================================================

actors = unreal.EditorLevelLibrary.get_all_level_actors()
pcg_volumes = [a for a in actors if type(a).__name__ == 'PCGVolume']

print(f"PCGVolumes in level: {len(pcg_volumes)}")
for vol in pcg_volumes:
    label = vol.get_actor_label()
    loc = vol.get_actor_location()
    scale = vol.get_actor_scale3d()
    print(f"  {label:40s} @[{loc.x:.0f},{loc.y:.0f},{loc.z:.0f}] scale=[{scale.x:.0f},{scale.y:.0f},{scale.z:.0f}]")
    
    # Check PCG component
    comp = vol.get_component_by_class(unreal.PCGComponent)
    if comp:
        # Check if graph is set
        try:
            inst = comp.get_graph_instance()
            if inst:
                g = inst.get_graph()
                if g:
                    print(f"    Graph: {g.get_name()}")
                else:
                    print(f"    Graph: (no graph)")
            else:
                print(f"    Graph: (no instance)")
        except Exception as e:
            print(f"    Graph: (error: {e})")
        
        # Check if bIsGraphRunning
        try:
            running = comp.get_editor_property("is_graph_running")
            print(f"    Running: {running}")
        except:
            pass
        
        # Check bGenerateAfterBake
        try:
            auto = comp.get_editor_property("auto_generate")
            print(f"    Auto Generate: {auto}")
        except:
            pass

print("\n=== Attempting to run PCG generation ===")

# Try to trigger PCG generation on each volume
for vol in pcg_volumes:
    label = vol.get_actor_label()
    comp = vol.get_component_by_class(unreal.PCGComponent)
    if comp:
        try:
            # Try to generate
            comp.generate(True)
            print(f"  Generated: {label}")
        except Exception as e:
            print(f"  Generate failed {label}: {e}")

print("\n=== PHASE 3 complete ===")
