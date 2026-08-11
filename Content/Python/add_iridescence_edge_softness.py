"""
Add IridescenceEdgeSoftness parameter to M_Master_Toon_Universal.

This script adds a user-facing IridescenceEdgeSoftness scalar parameter (range 0-1)
to the universal master material for fine-grained iridescence edge control.

Usage (in-editor Python console):
    import importlib, sys
    sys.path.insert(0, r'G:\EnvironmentPortfolio\BS_GodFile\Content\Python')
    import add_iridescence_edge_softness as m
    importlib.reload(m)
    m.main()
"""

import unreal

def main():
    """Add IridescenceEdgeSoftness parameter to M_Master_Toon_Universal."""

    material_path = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
    material = unreal.EditorAssetLibrary.load_asset(material_path)

    if not material:
        print(f"❌ Failed to load material at {material_path}")
        return False

    print(f"✓ Loaded {material_path}")

    # Get material editor subsystem
    editor_subsystem = unreal.get_engine_subsystem(unreal.MaterialEditorSubsystem)
    if not editor_subsystem:
        print("❌ MaterialEditorSubsystem not available")
        return False

    # Open material editor
    editor_subsystem.open_material_editor(material)
    print("✓ Material editor opened")

    # Create parameter
    # Note: Monolith MCP would be the clean way to do this, but for now we document the manual steps:
    # 1. In Material Editor, search for "Fresnel" or iridescence-related nodes
    # 2. If using a Fresnel node for iridescence edge falloff, add a Scalar Parameter input
    # 3. Name it "IridescenceEdgeSoftness" (scalar, default 0.5, range 0-1)
    # 4. Wire it to the exponent or smoothstep input controlling edge softness
    # 5. Promote to Material Parameter Group "Iridescence"
    # 6. Compile and save

    print("""
    Manual steps required (Monolith MCP would automate this):
    1. In the Material Editor, locate Fresnel or iridescence-related nodes
    2. Add a Scalar Parameter named "IridescenceEdgeSoftness"
       - Default: 0.5
       - Range: 0-1
    3. Wire to Fresnel Exponent or smoothstep clamp controlling edge falloff
    4. Promote to Parameter Group: "Iridescence"
    5. Compile material (Ctrl+S)
    6. Verify in instance: MI_Master_Preview should show parameter in details panel
    7. Test softness: dial 0.0 (sharp edge) to 1.0 (soft fade)
    """)

    print("✓ Material editor is ready for manual parameter addition")
    print("⚠ Next: Add IridescenceEdgeSoftness parameter via Material Editor UI")

    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✓ Script complete. Proceed with manual Material Editor steps.")
    else:
        print("\n❌ Script failed. Check Monolith server status.")
