import unreal

mpc = unreal.EditorAssetLibrary.load_asset("/Game/EnvSandbox/VFX/MPC/MPC_SakuraDream")

scalars = mpc.get_editor_property("scalar_parameters")
if scalars:
    for i, s in enumerate(scalars):
        print(f"Scalar {i}:")
        print(f"  to_dict: {s.to_dict()}")
        print(f"  to_tuple: {s.to_tuple()}")
        # Try get_editor_properties
        try:
            props = s.get_editor_properties()
            print(f"  editor_props: {props}")
        except Exception as e:
            print(f"  editor_props error: {e}")