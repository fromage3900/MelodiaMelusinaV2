import unreal

mpc_path = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"
mpc = unreal.EditorAssetLibrary.load_asset(mpc_path)

scalar_params = mpc.get_editor_property("ScalarParameters")
vector_params = mpc.get_editor_property("VectorParameters")

# Check the structure of the first scalar parameter
if scalar_params:
    first = scalar_params[0]
    print(f"First scalar param type: {type(first)}")
    print(f"First scalar param dir: {[m for m in dir(first) if not m.startswith('_')]}")

# Check the structure of the first vector parameter
if vector_params:
    first = vector_params[0]
    print(f"First vector param type: {type(first)}")
    print(f"First vector param dir: {[m for m in dir(first) if not m.startswith('_')]}")

# Try to get parameter names via the getter methods
print("\nScalar param names via getter:")
for name in mpc.get_scalar_parameter_names():
    val = mpc.get_scalar_parameter_default_value(name)
    print(f"  {name}: {val}")

print("\nVector param names via getter:")
for name in mpc.get_vector_parameter_names():
    val = mpc.get_vector_parameter_default_value(name)
    print(f"  {name}: {val}")