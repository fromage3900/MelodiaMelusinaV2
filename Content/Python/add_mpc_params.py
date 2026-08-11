import unreal

# Add CharacterWorldPosition vector parameter to MPC_Melodia_Palette
mpc_path = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"
mpc = unreal.EditorAssetLibrary.load_asset(mpc_path)
if not mpc:
    print("FAILED: Could not load MPC_Melodia_Palette")
    quit()

print(f"Loaded: {mpc.get_path_name()}")

# Add vector parameter for character world position
# MPC parameters are added via the ScalarParameters and VectorParameters arrays
# In Python, we need to use the appropriate method

# Check current parameters
print("Current scalar params:")
for p in mpc.scalar_parameters:
    print(f"  {p.parameter_name}: {p.default_value}")

print("Current vector params:")
for p in mpc.vector_parameters:
    print(f"  {p.parameter_name}: {p.default_value}")

# Add CharacterWorldPosition vector parameter if not exists
param_exists = False
for p in mpc.vector_parameters:
    if p.parameter_name == "CharacterWorldPosition":
        param_exists = True
        print("CharacterWorldPosition already exists")
        break

if not param_exists:
    # Add vector parameter
    new_param = unreal.MaterialParameterCollectionVectorParameter()
    new_param.parameter_name = "CharacterWorldPosition"
    new_param.default_value = unreal.Vector(0, 0, 0)
    mpc.vector_parameters.append(new_param)
    print("Added CharacterWorldPosition vector parameter")

# Also add ProximityRadius scalar if not exists
param_exists = False
for p in mpc.scalar_parameters:
    if p.parameter_name == "ProximityRadius":
        param_exists = True
        break

if not param_exists:
    new_param = unreal.MaterialParameterCollectionScalarParameter()
    new_param.parameter_name = "ProximityRadius"
    new_param.default_value = 1000.0
    mpc.scalar_parameters.append(new_param)
    print("Added ProximityRadius scalar parameter")

# Save
unreal.EditorAssetLibrary.save_asset("/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette")
print("MPC_Melodia_Palette updated and saved")