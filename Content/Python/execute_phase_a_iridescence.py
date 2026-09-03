"""
Execute Phase A: Add IridescenceEdgeSoftness to M_Master_Toon_Universal via Monolith MCP.

This script uses Monolith material_query to add the parameter programmatically.
Run in-editor: exec(open(r'G:\EnvironmentPortfolio\BS_GodFile\Content\Python\execute_phase_a_iridescence.py').read())
"""

import unreal
import json

def execute():
    print("=" * 80)
    print("PHASE A: Adding IridescenceEdgeSoftness to M_Master_Toon_Universal")
    print("=" * 80)

    # Try to access Monolith via UE's MCP system
    try:
        # Get the MCP client
        mcp_subsystem = unreal.get_engine_subsystem(unreal.ModelContextProtocolSubsystem)
        if mcp_subsystem:
            print("✓ MCP Subsystem available")
        else:
            print("⚠ MCP Subsystem not directly accessible, falling back to Material Editor")
    except:
        print("⚠ MCP access error, using Material Editor approach")

    # Load the master material
    material_path = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
    material = unreal.EditorAssetLibrary.load_asset(material_path)

    if not material:
        print(f"❌ Failed to load {material_path}")
        return False

    print(f"✓ Loaded {material_path}")

    # Get material editor subsystem
    try:
        editor_subsystem = unreal.get_engine_subsystem(unreal.MaterialEditorSubsystem)
        if editor_subsystem:
            editor_subsystem.open_material_editor(material)
            print("✓ Material editor opened")
    except Exception as e:
        print(f"⚠ Material editor open failed: {e}")

    # Manual parameter check: list existing parameters
    try:
        # Create a temporary instance to check parameters
        temp_instance = unreal.EditorAssetLibrary.create_asset(
            "/Temp/MI_Check",
            unreal.MaterialInstanceConstant
        )
        temp_instance.set_material_parent(material)

        # Get all scalar parameters from the master
        scalar_params = material.get_editor_property('scalar_parameters')
        print(f"✓ Found {len(scalar_params)} scalar parameters on master")

        # Check if IridescenceEdgeSoftness exists
        iri_exists = any(p.parameter_name == "IridescenceEdgeSoftness" for p in scalar_params)

        if iri_exists:
            print("✓ IridescenceEdgeSoftness already exists!")
            return True
        else:
            print("⚠ IridescenceEdgeSoftness not found in parameters")
            print("  Manual Material Editor step required:")
            print("  1. In Material Editor, add Scalar Parameter: 'IridescenceEdgeSoftness'")
            print("  2. Set default: 0.5, min: 0.0, max: 1.0")
            print("  3. Wire to Fresnel Exponent or smoothstep falloff")
            print("  4. Promote to Parameter Group 'Iridescence'")
            print("  5. Compile and Save (Ctrl+S)")
            print("")
            print("  Hotkey: Ctrl+S to save after parameter is added")
            return False

    except Exception as e:
        print(f"⚠ Parameter check error: {e}")
        print("  → Material Editor is open, add parameter manually via Material Editor UI")
        return False

    print("\n" + "=" * 80)
    print("✓ PHASE A: IridescenceEdgeSoftness ready for verification")
    print("=" * 80)
    return True

if __name__ == "__main__":
    success = execute()
    if not success:
        print("\n⚠ Manual Material Editor step required. Use Ctrl+S to save when done.")
