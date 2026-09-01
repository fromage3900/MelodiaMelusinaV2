import unreal
import json
import math

# ============================================================
# PHASE 2: Place purpose-driven PCG volumes
# ============================================================

# Helper to create a PCGVolume with a graph
def create_pcg_volume(graph_path, location, scale, label):
    """Create a PCGVolume with the specified graph."""
    world = unreal.EditorLevelLibrary.get_editor_world()
    
    # Create the volume
    volume = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PCGVolume, unreal.Vector(location[0], location[1], location[2]))
    if volume is None:
        print(f"[FAIL] Could not create PCGVolume: {label}")
        return None
    
    # Set label
    volume.set_actor_label(label)
    
    # Set scale (bounds)
    volume.set_actor_scale3d(unreal.Vector(scale[0], scale[1], scale[2]))
    
    # Set the PCG graph
    comp = volume.get_component_by_class(unreal.PCGComponent)
    if comp:
        graph = unreal.EditorAssetLibrary.load_asset(graph_path)
        if graph:
            comp.set_graph(graph)
            print(f"[OK] {label:40s} -> {graph_path.split('/')[-1]}")
        else:
            print(f"[FAIL] Could not load graph: {graph_path}")
    
    return volume

# Center of Sea Above (water level ~13405)
CX, CY, CZ = 0, 0, 13405

print("\n=== PHASE 2: Placing purpose-driven PCG volumes ===\n")

# 1. ResonanceCathedral - Song-chord pads around the cathedral
# This graph has 6 spawners, one per chord (C, Dm, F, G, Am, E)
# We'll place it to spawn pads in a circle around the nave
create_pcg_volume(
    graph_path="/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_ResonanceCathedral.PCG_Hero_ResonanceCathedral",
    location=(CX, CY, CZ + 500),
    scale=(8000, 8000, 2000),
    label="PCG_ResonanceCathedral"
)

# 2. Baroque NaveVault - Procedural vaulting above the cathedral
create_pcg_volume(
    graph_path="/Game/EnvSandbox/PCG/Styles/Baroque/PCG_BaroqueNaveVaultEx.PCG_BaroqueNaveVaultEx",
    location=(CX, CY, CZ + 3000),
    scale=(5000, 8000, 3000),
    label="PCG_NaveVault"
)

# 3. Baroque Scatter - Kitbash details (altars, buttresses, spires)
create_pcg_volume(
    graph_path="/Game/EnvSandbox/PCG/Styles/Baroque/PCG_Baroque_Scatter.PCG_Baroque_Scatter",
    location=(CX, CY, CZ),
    scale=(10000, 10000, 4000),
    label="PCG_BaroqueScatter"
)

# 4. WaterEdgeScatter - Ocean-cathedral seam details
create_pcg_volume(
    graph_path="/Game/EnvSandbox/PCG/Universal/PCG_WaterEdgeScatter.PCG_WaterEdgeScatter",
    location=(CX, CY, CZ - 500),
    scale=(12000, 12000, 1000),
    label="PCG_WaterEdge"
)

# 5. Colonnade - Pillars flanking the nave
create_pcg_volume(
    graph_path="/Game/EnvSandbox/PCG/Styles/Baroque/PCG_BaroqueColonnade.PCG_BaroqueColonnade",
    location=(CX, CY, CZ + 1000),
    scale=(6000, 6000, 2000),
    label="PCG_Colonnade"
)

# 6. Pilasters - Decorative pillars on walls
create_pcg_volume(
    graph_path="/Game/EnvSandbox/PCG/Styles/Baroque/PCG_BaroquePilasterEx.PCG_BaroquePilasterEx",
    location=(CX, CY, CZ + 1500),
    scale=(5000, 5000, 2000),
    label="PCG_Pilasters"
)

print("\n=== PHASE 2 complete ===\n")
