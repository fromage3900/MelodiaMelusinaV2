import unreal

mpc = unreal.EditorAssetLibrary.load_asset("/Game/EnvSandbox/VFX/MPC/NPC_SakuraDream")
print("Class:", mpc.get_class().get_name())

scalars = mpc.get_editor_property("scalar_parameters")
print("Scalars:", len(scalars) if scalars else 0)
if scalars:
    for s in scalars:
        pi = s.get_editor_property("parameter_info")
        dv = s.get_editor_property("default_value")
        print("  {}: {}".format(pi.name, dv))

vectors = mpc.get_editor_property("vector_parameters")
print("Vectors:", len(vectors) if vectors else 0)
if vectors:
    for v in vectors:
        pi = v.get_editor_property("parameter_info")
        dv = v.get_editor_property("default_value")
        print("  {}: {}".format(pi.name, dv))