import unreal

mpc_path = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"
mpc = unreal.EditorAssetLibrary.load_asset(mpc_path)

# Get the base parameter collection (the actual parameter data)
base = mpc.get_base_parameter_collection()
if not base:
    print("FAILED: Could not get base parameter collection")
    quit()

print(f"Base collection: {base.get_path_name()}")
print(f"Base type: {type(base)}")
print(f"Base dir: {[m for m in dir(base) if not m.startswith('_')]}")

# Check for scalar/vector parameter arrays on base
for attr in dir(base):
    if 'param' in attr.lower() or 'scalar' in attr.lower() or 'vector' in attr.lower():
        print(f"  Found on base: {attr}")