import unreal

# ============================================================
# NS_Uni_WaterMist Niagara System Creation Script
# Run in Unreal Editor: -ExecutePythonScript=C:/EnvironmentPortfolio/BS_GodFile/Content/Python/create_water_mist_niagara.py
# ============================================================

def create_water_mist_niagara():
    """Create NS_Uni_WaterMist Niagara System with ModuleScript for PlayerProximity → ProximitySpawnRateMultiplier"""
    
    system_path = "/Game/Melodia/FX/NS_Uni_WaterMist"
    system_name = "NS_Uni_WaterMist"
    emitter_name = "WaterMist_Emitter"
    module_script_name = "ProximitySpawnRateModule"
    
    # Check if system exists
    if unreal.EditorAssetLibrary.does_asset_exist(system_path):
        print(f"System already exists: {system_path}")
        niagara_system = unreal.EditorAssetLibrary.load_asset(system_path)
    else:
        # Create new Niagara System
        system_factory = unreal.NiagaraSystemFactoryNew()
        niagara_system = unreal.EditorAssetLibrary.create_asset(system_path, system_name, unreal.NiagaraSystem, system_factory)
        print(f"Created new Niagara System: {system_path}")
    
    if not niagara_system:
        print("Failed to create/load Niagara System")
        return
    
    # Create or get the emitter
    emitter = None
    for existing_emitter in niagara_system.get_emitters():
        if existing_emitter.get_name() == emitter_name:
            emitter = existing_emitter
            break
    
    if not emitter:
        emitter = niagara_system.add_emitter(emitter_name)
        print(f"Added emitter: {emitter_name}")
    
    # Get the emitter's update stage
    update_stage = None
    for stage in emitter.get_stages():
        if isinstance(stage, unreal.NiagaraModuleScript) and stage.get_name() == "EmitterUpdate":
            update_stage = stage
            break
    
    if not update_stage:
        # Create a new module script for emitter update
        update_stage = emitter.add_emitter_module_script("EmitterUpdate")
        print(f"Added EmitterUpdate stage")
    
    # Now we need to add a ModuleScript to the EmitterUpdate that reads PlayerProximity
    # This requires creating a custom Module Script
    
    # Create ModuleScript asset
    module_script_path = f"/Game/Melodia/FX/ModuleScripts/{module_script_name}"
    module_script_full_name = f"{module_script_name}_Script"
    
    if unreal.EditorAssetLibrary.does_asset_exist(module_script_path):
        module_script = unreal.EditorAssetLibrary.load_asset(module_script_path)
    else:
        module_script_factory = unreal.NiagaraModuleScriptFactoryNew()
        module_script = unreal.EditorAssetLibrary.create_asset(
            module_script_path, module_script_name, unreal.NiagaraModuleScript, module_script_factory
        )
        print(f"Created ModuleScript: {module_script_path}")
    
    if module_script:
        # Configure the ModuleScript to:
        # 1. Have input: PlayerProximity (float)
        # 2. Have output: ProximitySpawnRateMultiplier (float)
        # 3. Logic: ProximitySpawnRateMultiplier = lerp(0.1, 1.0, PlayerProximity)
        
        # Add input parameter
        input_param = unreal.NiagaraModuleScriptParameterDefinition()
        input_param.name = "PlayerProximity"
        input_param.type_definition = unreal.NiagaraTypeDefinition.get_scalar()
        module_script.add_input(input_param)
        print("Added PlayerProximity input parameter")
        
        # Add output parameter
        output_param = unreal.NiagaraModuleScriptParameterDefinition()
        output_param.name = "ProximitySpawnRateMultiplier"
        output_param.type_definition = unreal.NiagaraTypeDefinition.get_scalar()
        module_script.add_output(output_param)
        print("Added ProximitySpawnRateMultiplier output parameter")
        
        # Set the script content (this is simplified - actual script uses VM bytecode)
        # For Python, we can set the script text for CPU simulation
        script_text = """
// ProximitySpawnRateModule
// Input: PlayerProximity (float, 0.0 = far, 1.0 = near)
// Output: ProximitySpawnRateMultiplier (float)

ProximitySpawnRateMultiplier = lerp(0.1, 1.0, PlayerProximity);
"""
        module_script.set_script_text(script_text)
        print("Set ModuleScript logic")
        
        unreal.EditorAssetLibrary.save_asset(module_script_path)
    
    # Add the ModuleScript to the emitter's update stage
    if update_stage and module_script:
        # This is complex in Python - typically done via the Niagara Editor UI
        # For now, we'll note it needs to be wired in the editor
        print(f"\nNOTE: Manually add '{module_script_name}' to EmitterUpdate stage in Niagara Editor")
        print("Wire: ModuleScript output 'ProximitySpawnRateMultiplier' -> SpawnRate module 'SpawnRateMultiplier'")
    
    # Save the system
    unreal.EditorAssetLibrary.save_asset(system_path)
    print(f"\nSaved Niagara System: {system_path}")
    
    print("\n=== NS_Uni_WaterMist Setup Complete ===")
    print(f"System: {system_path}")
    print(f"Emitter: {emitter_name}")
    print(f"ModuleScript: {module_script_path}")
    print("\nNext Steps in Niagara Editor:")
    print("1. Open NS_Uni_WaterMist")
    print("2. Select EmitterUpdate stage")
    print("3. Add ModuleScript -> ProximitySpawnRateModule")
    print("4. Add SpawnRate module")
    print("5. Wire ProximitySpawnRateMultiplier -> SpawnRate.SpawnRateMultiplier")
    print("6. In the system/emitter user parameters, expose PlayerProximity for external control")

if __name__ == "__main__":
    create_water_mist_niagara()