import unreal

mpc_path = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"
mpc = unreal.EditorAssetLibrary.load_asset(mpc_path)

# Try to get the scalar/vector parameter arrays as editor properties
try:
    scalar_params = mpc.get_editor_property("ScalarParameters")
    print(f"ScalarParameters: {scalar_params}")
    print(f"Type: {type(scalar_params)}")
    if scalar_params:
        for i, p in enumerate(scalar_params):
            print(f"  [{i}] {p.ParameterName}: {p.DefaultValue}")
except Exception as e:
    print(f"Error getting ScalarParameters: {e}")

try:
    vector_params = mpc.get_editor_property("VectorParameters")
    print(f"VectorParameters: {vector_params}")
    print(f"Type: {type(vector_params)}")
    if vector_params:
        for i, p in enumerate(vector_params):
            print(f"  [{i}] {p.ParameterName}: {p.DefaultValue}")
except Exception as e:
    print(f"Error getting VectorParameters: {e}")