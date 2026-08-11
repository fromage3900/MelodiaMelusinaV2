import unreal

mpc_path = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"
mpc = unreal.EditorAssetLibrary.load_asset(mpc_path)
if not mpc:
    print("FAILED: Could not load MPC_Melodia_Palette")
    quit()

print(f"Loaded: {mpc.get_path_name()}")

# Get current scalar parameter names
scalar_names = mpc.get_scalar_parameter_names()
print("Current scalar params:")
for name in scalar_names:
    val = mpc.get_scalar_parameter_default_value(name)
    print(f"  {name}: {val}")

# Get current vector parameter names
vector_names = mpc.get_vector_parameter_names()
print("Current vector params:")
for name in vector_names:
    val = mpc.get_vector_parameter_default_value(name)
    print(f"  {name}: {val}")

# Add CharacterWorldPosition vector parameter if not exists
if "CharacterWorldPosition" not in vector_names:
    # We need to add it via set_editor_property on the vector parameters array
    # This is tricky - let's try to get the vector parameters array and append
    print("CharacterWorldPosition not found - need to add via editor property")
else:
    print("CharacterWorldPosition already exists")

if "ProximityRadius" not in scalar_names:
    print("ProximityRadius not found - need to add")
else:
    print("ProximityRadius already exists")