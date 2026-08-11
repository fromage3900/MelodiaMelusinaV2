import unreal

mpc = unreal.EditorAssetLibrary.load_asset("/Game/EnvSandbox/VFX/MPC/MPC_SakuraDream")
print("Class:", mpc.get_class().get_name())

scalars = mpc.get_editor_property("scalar_parameters")
print("Scalars:", len(scalars) if scalars else 0)
if scalars:
    for s in scalars:
        print("  Scalar param:", s)
        print("  dir:", [a for a in dir(s) if not a.startswith('_')])
        # Try to get all editor properties
        try:
            props = s.get_editor_properties()
            print("  editor properties:", props)
        except:
            pass

vectors = mpc.get_editor_property("vector_parameters")
print("Vectors:", len(vectors) if vectors else 0)
if vectors:
    for v in vectors:
        print("  Vector param:", v)
        print("  dir:", [a for a in dir(v) if not a.startswith('_')])