import unreal

mpc_path = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"
mpc = unreal.EditorAssetLibrary.load_asset(mpc_path)
if not mpc:
    print("FAILED: Could not load MPC_Melodia_Palette")
    quit()

print(f"Loaded: {mpc.get_path_name()}")
print(f"Type: {type(mpc)}")
print(f"Dir: {[m for m in dir(mpc) if not m.startswith('_')]}")

# Check for parameter-related methods/attributes
for attr in dir(mpc):
    if 'param' in attr.lower() or 'scalar' in attr.lower() or 'vector' in attr.lower():
        print(f"  Found: {attr}")