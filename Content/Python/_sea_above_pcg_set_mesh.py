import unreal
import json

# ============================================================
# TRY SETTING MESH ON PCG SPAWNERS
# ============================================================

# Load the NaveVault graph
nv_path = "/Game/EnvSandbox/PCG/Styles/Baroque/PCG_BaroqueNaveVaultEx.PCG_BaroqueNaveVaultEx"
nv = unreal.EditorAssetLibrary.load_asset(nv_path)

if nv:
    nodes = nv.get_editor_property("nodes")
    for n in nodes:
        if "Spawner" in n.get_name():
            print(f"=== {n.get_name()} ===")
            
            # Try to set mesh
            mesh = unreal.EditorAssetLibrary.load_asset("/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_VaultBay.SM_Cathedral_VaultBay")
            if mesh:
                try:
                    n.set_editor_property("mesh", mesh)
                    print(f"  Set mesh: {mesh.get_name()}")
                except Exception as e:
                    print(f"  Failed to set mesh: {e}")
                    
                # Try alternative property names
                for prop_name in ["Mesh", "static_mesh", "StaticMesh", "asset", "Asset"]:
                    try:
                        n.set_editor_property(prop_name, mesh)
                        print(f"  Set {prop_name}: {mesh.get_name()}")
                    except:
                        pass

# Also try the ResonanceCathedral spawner subgraphs
print("\n=== RESONANCE CATHEDRAL ===")
rc_path = "/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_ResonanceCathedral.PCG_Hero_ResonanceCathedral"
rc = unreal.EditorAssetLibrary.load_asset(rc_path)
if rc:
    nodes = rc.get_editor_property("nodes")
    for n in nodes:
        node_name = n.get_name()
        if "Spawner" in node_name:
            print(f"\n--- {node_name} ---")
            try:
                sub = n.get_editor_property("graph")
                if sub:
                    sub_nodes = sub.get_editor_property("nodes")
                    for sn in sub_nodes:
                        if "Spawner" in sn.get_name():
                            print(f"  Sub-spawner: {sn.get_name()}")
                            mesh = unreal.EditorAssetLibrary.load_asset("/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_VaultBay.SM_Cathedral_VaultBay")
                            if mesh:
                                try:
                                    sn.set_editor_property("mesh", mesh)
                                    print(f"    Set mesh: {mesh.get_name()}")
                                except Exception as e:
                                    print(f"    Failed: {e}")
            except:
                pass
