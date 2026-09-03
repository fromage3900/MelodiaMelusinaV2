import unreal

# Inspect existing MPC
mpc = unreal.EditorAssetLibrary.load_asset("/Game/EnvSandbox/VFX/MPC/NPC_SakuraDream")
print("MPC:", mpc)

scalars = mpc.get_editor_property("scalar_parameters")
print("Scalars:", len(scalars) if scalars else 0)
if scalars:
    for s in scalars:
        pi = s.get_editor_property("parameter_info")
        dv = s.get_editor_property("default_value")
        print(f"  {pi.name}: {dv}")

vectors = mpc.get_editor_property("vector_parameters")
print("Vectors:", len(vectors) if vectors else 0)
if vectors:
    for v in vectors:
        pi = v.get_editor_property("parameter_info")
        dv = v.get_editor_property("default_value")
        print(f"  {pi.name}: {dv}")

# Try to add a new scalar parameter
print("\nTrying to add test parameter...")
new_param = unreal.ScalarParameterValue()
pi = unreal.MaterialParameterInfo()
pi.name = "NPC_TestParam"
new_param.set_editor_property("parameter_info", pi)
new_param.set_editor_property("default_value", 42.0)

# Check if we can set scalar_parameters
scalars.append(new_param)
mpc.set_editor_property("scalar_parameters", scalars)
unreal.EditorAssetLibrary.save_asset(mpc.get_path_name())
print("Saved MPC")