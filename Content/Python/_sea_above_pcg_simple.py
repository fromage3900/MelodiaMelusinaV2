import unreal
import json

# Simpler: query what the existing PCG volumes contain
world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.EditorLevelLibrary.get_all_level_actors()
pcg_volumes = [a for a in actors if type(a).__name__ == 'PCGVolume']

print(f"PCGVolumes in level: {len(pcg_volumes)}")
for vol in pcg_volumes:
    label = vol.get_actor_label()
    loc = vol.get_actor_location()
    # Get scale
    scale = vol.get_actor_scale3d()
    print(f"  {label:50s} @[{loc.x:.0f},{loc.y:.0f},{loc.z:.0f}] scale=[{scale.x:.0f},{scale.y:.0f},{scale.z:.0f}]")
    
    # Get components
    comps = vol.get_components_by_class(unreal.PCGComponent)
    for comp in comps:
        # Check if graph is set
        print(f"    PCGComponent: {comp.get_name()}")
        # Try getting graph instance
        try:
            inst = comp.get_graph_instance()
            if inst:
                g = inst.get_graph()
                if g:
                    print(f"      Graph: {g.get_name()}")
                else:
                    print(f"      Graph: (no graph)")
            else:
                print(f"      Graph: (no instance)")
        except Exception as e:
            print(f"      Graph error: {e}")

# Also check PCGWorldActor
print("\n=== PCGWorldActor ===")
pcg_world_actors = [a for a in actors if type(a).__name__ == 'PCGWorldActor']
for w in pcg_world_actors:
    print(f"  {w.get_actor_label()}")

# List all available PCG graph assets
print("\n=== Available PCG Graphs (Baroque/Arch) ===")
baroque_graphs = unreal.EditorAssetLibrary.list_assets("/Game/EnvSandbox/PCG/Styles/Baroque/")
for g in sorted(baroque_graphs):
    print(f"  {g}")

print("\n=== Available PCG Graphs (Hero) ===")
hero_graphs = unreal.EditorAssetLibrary.list_assets("/Game/EnvSandbox/PCG/Musical/Hero/")
for g in sorted(hero_graphs):
    print(f"  {g}")

print("\n=== Available PCG Graphs (Universal) ===")
universal_graphs = unreal.EditorAssetLibrary.list_assets("/Game/EnvSandbox/PCG/Universal/")
for g in sorted(universal_graphs):
    print(f"  {g}")
