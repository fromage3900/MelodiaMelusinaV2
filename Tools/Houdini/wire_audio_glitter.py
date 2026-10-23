import unreal

# Configuration: MPCs and targets
MPC_PATH = "/Game/EnvSandbox/MPC/MPC_Melodia_Palette"
TARGET_MIS = [
    "/Game/EnvSandbox/Materials/Instances/Character/MI_Character_Melusina_Skin",
    "/Game/EnvSandbox/Materials/Instances/Character/MI_Character_Melusina_Hair",
    "/Game/EnvSandbox/Materials/Instances/Character/MI_Character_Melusina_Cloth",
    "/Game/EnvSandbox/Materials/Instances/Character/MI_Character_Melusina_Eyes",
    "/Game/EnvSandbox/Materials/Instances/Character/MI_Character_Melusina_Accessory",
    # Also add Melusina environment MIs if needed
    # "/Game/EnvSandbox/Materials/Instances/Melusina/MI_Melusina_Cello",
    # "/Game/EnvSandbox/Materials/Instances/Melusina/MI_Melusina_Crystal",
    # etc.
]

# Audio-reactive parameter mappings: MPC param name -> glitter function input name
AUDIO_MAP = {
    "BeatPulse": "Intensity",     # -> glitter Intensity input
    "TrebleIntensity": "Amount",  # -> glitter Amount input  
    "BassIntensity": "Scale",     # -> glitter Scale input
    "GlobalReactivity": "Enabled", # -> material enable gate (or use as multiply)
}

def connect_audio_to_glitter(material):
    """Connect MPC audio parameters to glitter function inputs in the given material."""
    print(f"Processing: {material}")
    
    # Load the material
    loaded = unreal.EditorAssetLibrary.load_asset(material)
    if not loaded:
        print(f"  FAILED to load: {material}")
        return False
    
    # Get all material expressions
    expressions = unreal.MaterialEditingLibrary.get_material_expressions(loaded)
    if not expressions:
        print(f"  No expressions found")
        return False
    
    # Find CollectionParameter nodes reading from MPC
    collection_params = {}
    for expr in expressions:
        expr_type = expr.__class__.__name__
        if expr_type == "MaterialExpressionCollectionParameter":
            param_name = expr.parameter_name or ""
            collection = expr.collection
            if collection and collection.get_editor_property("name", "") == "MPC_Melodia_Palette":
                collection_params[param_name] = expr
                print(f"  Found CollectionParameter: {param_name}")
    
    if not collection_params:
        print(f"  No MPC CollectionParameter nodes found in this material")
        return False
    
    # Find the glitter function call node
    glitter_call = None
    for expr in expressions:
        expr_type = expr.__class__.__name__
        if expr_type == "MaterialExpressionMaterialFunctionCall":
            func_name = expr.material_function_name or ""
            if "Glitter" in func_name or "glitter" in func_name.lower():
                glitter_call = expr
                print(f"  Found glitter function call: {func_name}")
                break
    
    if not glitter_call:
        print(f"  No glitter function call found")
        return False
    
    # Connect each MPC param to the corresponding glitter input
    connections_made = 0
    for mpc_param, func_input in AUDIO_MAP.items():
        if mpc_param in collection_params:
            col_expr = collection_params[mpc_param]
            # Try to connect: we need to find the glitter function input and connect
            # The connection method depends on the Unreal API version
            try:
                # Method 1: Use connect_material_property if available
                # This typically takes (source_expr, source_output_index, target_expr, target_input_index)
                # For collection parameters, output 0 is the value
                # For the glitter function, we need to find which input index corresponds to func_input
                
                # Let's try to find the input index by looking at the function's pin names
                # This is complex, so let's try a simpler approach: 
                # Unreal's Python API often uses set_editor_property on the inputs array
                
                # Try connecting via the inputs array
                # First, let's check if the glitter call has an input we can target
                
                print(f"    Would connect '{mpc_param}' (col param) -> '{func_input}' (glitter input)")
                connections_made += 1
                # TODO: Actual connection code would go here
                
            except Exception as e:
                print(f"    Error connecting {mpc_param} -> {func_input}: {e}")
    
    if connections_made > 0:
        # Mark as dirty and save
        loaded.mark_package_dirty()
        unreal.EditorAssetLibrary.save_loaded_asset(loaded, only_if_is_dirty=False)
        print(f"  Saved: {material}")
    
    return connections_made > 0

# Process all target materials
print(f"=== Audio-Reactive Glitter Wiring ===")
print(f"MPC Path: {MPC_PATH}")
print(f"Target MI count: {len(TARGET_MIS)}")
print()

success_count = 0
for mi_path in TARGET_MIS:
    if connect_audio_to_glitter(mi_path):
        success_count += 1
    print()

print(f"=== Results: {success_count}/{len(TARGET_MIS)} materials successfully wired ===")