import unreal

mpc_path = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"
mpc = unreal.EditorAssetLibrary.load_asset(mpc_path)

# Get the arrays
scalar_params = mpc.get_editor_property("ScalarParameters")
vector_params = mpc.get_editor_property("VectorParameters")

print(f"Scalar params count: {len(scalar_params)}")
print(f"Vector params count: {len(vector_params)}")

# Check if CharacterWorldPosition already exists
exists = False
for name in mpc.get_vector_parameter_names():
    if name == "CharacterWorldPosition":
        print("CharacterWorldPosition already exists")
        break
else:
    # Create new vector parameter
    new_vec = unreal.CollectionVectorParameter()
    new_vec.set_editor_property("ParameterName", "CharacterWorldPosition")
    new_vec.set_editor_property("DefaultValue", unreal.LinearColor(0, 0, 0, 1))
    vector_params.append(new_vec)
    print("Added CharacterWorldPosition to vector params")

# Check ProximityRadius
if "ProximityRadius" not in mpc.get_scalar_parameter_names():
    new_scalar = unreal.CollectionScalarParameter()
    new_scalar.set_editor_property("ParameterName", "ProximityRadius")
    new_scalar.set_editor_property("DefaultValue", 1000.0)
    scalar_params = mpc.get_editor_property("ScalarParameters")
    scalar_params.append(new_scalar)
    print("Added ProximityRadius to scalar params")

# Get the arrays again to ensure we have the latest references
scalar_params = mpc.get_editor_property("ScalarParameters")
vector_params = mpc.get_editor_property("VectorParameters")

# Set the arrays back on the MPC
mpc.set_editor_property("ScalarParameters", scalar_params)
mpc.set_editor_property("VectorParameters", vector_params)

# Save
unreal.EditorAssetLibrary.save_asset("/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette")
print("MPC parameters updated and saved")