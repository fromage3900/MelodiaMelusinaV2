import unreal
import json

# ============================================================
# DEEP DIVE: Find mesh refs in NaveVault's StaticMeshSpawner
# ============================================================

# NaveVault
nv_path = "/Game/EnvSandbox/PCG/Styles/Baroque/PCG_BaroqueNaveVaultEx.PCG_BaroqueNaveVaultEx"
nv = unreal.EditorAssetLibrary.load_asset(nv_path)
if nv:
    nodes = nv.get_editor_property("nodes")
    for n in nodes:
        if "Spawner" in n.get_name():
            print(f"=== {n.get_name()} ===")
            # Try all properties
            for prop in dir(n):
                if not prop.startswith("_") and prop not in ["get_name", "get_class", "get_outer", "get_path_name"]:
                    try:
                        val = n.get_editor_property(prop)
                        if val and val != "" and val != 0 and val != False and val != []:
                            print(f"  {prop}: {val}")
                    except:
                        pass

# Also check the ResonanceCathedral's spawner subgraphs
print("\n\n=== RESONANCE CATHEDRAL SPAWNERS ===")
rc_path = "/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_ResonanceCathedral.PCG_Hero_ResonanceCathedral"
rc = unreal.EditorAssetLibrary.load_asset(rc_path)
if rc:
    nodes = rc.get_editor_property("nodes")
    for n in nodes:
        node_name = n.get_name()
        if "Spawner" in node_name:
            print(f"\n--- {node_name} ---")
            # Try to get subgraph
            try:
                sub = n.get_editor_property("graph")
                if sub:
                    sub_nodes = sub.get_editor_property("nodes")
                    print(f"  Subgraph: {sub.get_name()} ({len(sub_nodes)} nodes)")
                    for sn in sub_nodes:
                        print(f"    {sn.get_name()} ({type(sn).__name__})")
                        # Check for mesh
                        for prop in ["mesh", "Mesh", "static_mesh", "StaticMesh"]:
                            try:
                                val = sn.get_editor_property(prop)
                                if val:
                                    print(f"      {prop}: {val.get_name() if hasattr(val, 'get_name') else val}")
                            except:
                                pass
            except:
                pass
