import unreal

print("=== HAIR DIAGNOSTIC ===\n")
eal = unreal.EditorAssetLibrary
ar = unreal.AssetRegistryHelpers.get_asset_registry()

# 1. Check if exploration character has UMelodiaHairComponent
print("--- Exploration Character (BP_MelusinaJRPGCharacter) ---")
char_bp = eal.load_asset("/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter")
if char_bp:
    cd = char_bp.get_class().get_default_object()
    print(f"  Default object: {cd.get_class().get_name()}")
    all_comps = cd.get_components()
    for c in all_comps:
        cn = str(c.get_class().get_name())
        if "Hair" in cn or "hair" in cn.lower() or "Skeletal" in cn or "Mesh" in cn or "Water" in cn.lower():
            mn = c.get_name()
            print(f"  Component: {mn} ({cn})")
else:
    print("  NOT FOUND")

# 2. Check hair mesh bone data
print("\n--- Hair Mesh (SK_MelusinaHair) ---")
hair_sk = eal.load_asset("/Game/Melodia/Characters/Melusina/Hair/SK_MelusinaHair")
if hair_sk:
    ref = hair_sk.get_editor_property("ref_skeleton")
    nb = ref.get_num()
    root_name = ref.get_bone_name(0).to_string()
    root_transform = ref.get_ref_bone_pose()[0]
    print(f"  Bones: {nb}")
    print(f"  Root bone: {root_name}")
    print(f"  Root transform: {str(root_transform)}")
else:
    print("  NOT FOUND")

# 3. Check body mesh for head_x bone
print("\n--- Body Mesh (SK_Melusina) ---")
body_sk = eal.load_asset("/Game/Melodia/Characters/Melusina/Hair/SK_Melusina")
if body_sk:
    ref = body_sk.get_editor_property("ref_skeleton")
    nb = ref.get_num()
    head_idx = ref.find_bone_index("head_x")
    print(f"  Bones: {nb}")
    if head_idx >= 0:
        head_transform = ref.get_ref_bone_pose()[head_idx]
        print(f"  head_x index: {head_idx}")
        print(f"  head_x transform: {str(head_transform.to_string())}")
    else:
        print("  head_x: NOT FOUND in skeleton")
else:
    print("  NOT FOUND")

print("\nDONE")