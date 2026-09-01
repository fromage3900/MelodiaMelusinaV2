import unreal
import json

# ============================================================
# FIX 4 SILENT PCG GRAPHS — Assign kitbash meshes to spawners
# ============================================================

# The 4 silent graphs need mesh references in their spawner subgraphs
# We'll use a different approach: replace the graph with one that has meshes

# First, let's check what the ResonanceCathedral graph spawns that WORKS
rc_path = "/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_ResonanceCathedral.PCG_Hero_ResonanceCathedral"
rc = unreal.EditorAssetLibrary.load_asset(rc_path)

if rc:
    nodes = rc.get_editor_property("nodes")
    print(f"ResonanceCathedral nodes: {len(nodes)}")
    
    for i, n in enumerate(nodes):
        node_type = type(n).__name__
        if "Spawner" in node_type or "StaticMesh" in node_type:
            node_name = n.get_name()
            print(f"\n--- {node_name} ({node_type}) ---")
            
            # Try to get mesh
            for prop in ["mesh", "Mesh", "static_mesh", "StaticMesh"]:
                try:
                    val = n.get_editor_property(prop)
                    if val:
                        print(f"  {prop}: {val.get_name() if hasattr(val, 'get_name') else val}")
                except:
                    pass

# Now let's look at the NaveVault graph
print("\n\n=== NaveVault ===")
nv_path = "/Game/EnvSandbox/PCG/Styles/Baroque/PCG_BaroqueNaveVaultEx.PCG_BaroqueNaveVaultEx"
nv = unreal.EditorAssetLibrary.load_asset(nv_path)
if nv:
    nodes = nv.get_editor_property("nodes")
    print(f"Nodes: {len(nodes)}")
    for i, n in enumerate(nodes):
        print(f"  [{i}] {n.get_name()} ({type(n).__name__})")
