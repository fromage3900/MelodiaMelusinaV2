import unreal

# Create a Niagara system with a module script to drive ProximitySpawnRateMultiplier from MPC PlayerProximity
system_path = "/Game/EnvSandbox/VFX/Systems/Universal/NS_WaterProximityDriver"
emitter_name = "ProximityDriver"

# Create the system
system = unreal.NiagaraSystemFactory().factory_create_new(system_path)
if not system:
    print("Failed to create system")
    quit()

# Add emitter
emitter = system.add_emitter(emitter_name)

# Add module script to emitter update stage
# Note: This is a simplified approach - in practice we'd add a ModuleScript module

# Save
unreal.EditorAssetLibrary.save_asset(system_path)
print(f"Created {system_path}")

# Now add a Module Script to the existing NS_Uni_WaterMist
# The SpawnRate module on WaterMist emitter has its SpawnRate bound to ProximitySpawnRateMultiplier
# We need a module script in emitter_update stage that reads MPC_Melodia_Palette.PlayerProximity
# and sets ProximitySpawnRateMultiplier = 1.0 + (1.0 - PlayerProximity) * 4.0

print("Niagara MPC drive setup would require custom module script")
print("This is best done via editor or custom module script creation")