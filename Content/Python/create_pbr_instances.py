"""Create MIs for 12 complete PBR texture sets that have zero instances.

Each set has: Albedo/BaseColor + Normal + Roughness + Metallic (± Height/ORM)
Parent: M_Master_Toon_Universal (same as arch toon — keeps pipeline consistent)
Target folder: Content/EnvSandbox/Materials/Instances/Environment/Stylized/

This is separate from arch-toon MI creation (mesh slot assignment).
These are standalone texture sets that need MIs to be usable in the editor.
"""
import unreal

PARENT = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
MI_ROOT = "/Game/EnvSandbox/Materials/Instances/Environment/Stylized"

# Map PBR stem names to texture file name patterns
# Format: stem -> {param_name: texture_path_pattern}
# We need to find the actual texture paths on disk

def find_texture_stems():
    """Scan for texture assets matching the 12 complete PBR stems."""
    stems = [
        "T_FloralBrickGrayScale",
        "ZenTrim_Base4K", "ZenTrim_ColourShift", "ZenTrim_CrackedToHell",
        "ZenTrim_FlowersLIttleBit", "ZenTrim_FlowersLOTS", "ZenTrim_FlowersMid", "ZenTrim_Wet",
        "basetrim", "concretetrim",
        "landscape_grass", "landscapegrayscale",
    ]
    
    results = {}
    for root in ["/Game/Textures", "/Game/EnvSandbox/Textures", "/Game/Content/Textures"]:
        if not unreal.EditorAssetLibrary.does_directory_exist(root):
            continue
        for asset_path in unreal.EditorAssetLibrary.list_assets(root, recursive=True):
            # list_assets returns /Game/Package.Asset — strip suffix for matching
            asset_name = asset_path.split("/")[-1].split(".")[-1]
            for stem in stems:
                if stem.lower() in asset_name.lower():
                    if stem not in results:
                        results[stem] = []
                    results[stem].append(asset_path)
    return results

# Texture parameter name mapping for the master material
# We need to discover these from the parent
def get_parent_params():
    parent = unreal.load_asset(PARENT)
    if not parent:
        print("FATAL: parent not found")
        return None
    
    tex_names = unreal.MaterialEditingLibrary.get_texture_parameter_names(parent)
    sca_names = unreal.MaterialEditingLibrary.get_scalar_parameter_names(parent)
    vec_names = unreal.MaterialEditingLibrary.get_vector_parameter_names(parent)
    
    print(f"Parent texture params: {tex_names}")
    print(f"Parent scalar params: {sca_names}")
    print(f"Parent vector params: {vec_names}")
    
    return {
        "texture": tex_names,
        "scalar": sca_names,
        "vector": vec_names,
    }

def create_mi_for_stem(stem, texture_map, parent_params, mi_dir):
    """Create a material instance for a PBR stem with given textures."""
    mi_name = f"MI_{stem}"
    path = f"{mi_dir}/{mi_name}"
    
    # Check existing
    existing = unreal.load_asset(path)
    if existing:
        print(f"  {mi_name}: already exists at {path}")
        return "existing"
    
    # Create
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.MaterialInstanceConstantFactoryNew()
    mi = tools.create_asset(mi_name, mi_dir, unreal.MaterialInstanceConstant, factory)
    
    if not mi:
        print(f"  {mi_name}: creation FAILED")
        return "create_failed"
    
    # Set parent — load fresh
    parent_obj = unreal.load_asset(PARENT)
    if not parent_obj:
        print(f"  {mi_name}: parent not found {PARENT}")
        return "parent_missing"
    mi.set_editor_property("parent", parent_obj)
    
    # Set texture parameters
    for param_name, tex_path in texture_map.items():
        tex = unreal.load_asset(tex_path)
        if tex:
            # Try to set via MEL
            success = unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
                mi, param_name, tex
            )
            if success:
                print(f"  {mi_name}: set {param_name} = {tex_path.split('/')[-1]}")
            else:
                print(f"  {mi_name}: FAILED to set {param_name} (MEL returned False)")
        else:
            print(f"  {mi_name}: texture not found: {tex_path}")
    
    # Set sensible scalar defaults
    for nm, val in [("Roughness", 0.7), ("Metallic", 0.0), ("TextureWeight", 0.85)]:
        if nm in parent_params.get("scalar", []):
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, nm, val)
    
    # ShadowDream params
    for nm, val in [("ShadowDreamStrength", 0.55)]:
        if nm in parent_params.get("scalar", []):
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, nm, val)
    
    for nm, val in [("ShadowDreamTint", unreal.LinearColor(0.545, 0.627, 0.843, 1.0)),  # soft blue
                    ("ShadowFlowerColor", unreal.LinearColor(0.912, 0.627, 0.749, 1.0))]:  # soft pink
        if nm in parent_params.get("vector", []):
            unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(mi, nm, val)
    
    # Save
    saved = unreal.EditorAssetLibrary.save_loaded_asset(mi)
    if saved:
        print(f"  {mi_name}: created + saved OK")
        return "created"
    else:
        print(f"  {mi_name}: save FAILED")
        return "save_failed"

def main():
    print("=" * 60)
    print("PBR INSTANCE CREATION — 12 complete sets with 0 instances")
    print("=" * 60)
    
    # Ensure directory
    if not unreal.EditorAssetLibrary.does_directory_exist(MI_ROOT):
        unreal.EditorAssetLibrary.make_directory(MI_ROOT)
        print(f"Created: {MI_ROOT}")
    
    # Get parent params
    parent_params = get_parent_params()
    if not parent_params:
        return
    
    # Find textures
    print("\n=== Finding texture sets ===")
    tex_map = find_texture_stems()
    
    created = 0
    existing = 0
    failed = 0
    
    for stem, textures in sorted(tex_map.items()):
        if not textures:
            print(f"\n  {stem}: NO TEXTURES FOUND on disk")
            failed += 1
            continue
        
        print(f"\n  {stem}: {len(textures)} texture files found")
        
        # Build param map: figure out which texture goes to which param
        # Heuristic: match by name suffix (BaseColor, Normal, Roughness, Metallic, Height)
        param_map = {}
        for tex_path in textures:
            # /Game/.../Package.Object -> Object
            tex_name = tex_path.split("/")[-1].split(".")[-1].lower()
            
            # Determine param name from texture file name
            assigned = False
            for ext in ["_basecolor", "_base_color", "_base", "_bc"]:
                if tex_name.endswith(ext):
                    param_map["BaseColor"] = tex_path
                    assigned = True
                    break
            if not assigned:
                for ext in ["_normal", "_norm", "_nrm"]:
                    if tex_name.endswith(ext):
                        param_map["Normal"] = tex_path
                        assigned = True
                        break
            if not assigned:
                for ext in ["_roughness", "_rough", "_rgh"]:
                    if tex_name.endswith(ext):
                        param_map["Roughness"] = tex_path
                        assigned = True
                        break
            if not assigned:
                for ext in ["_metallic", "_metal", "_mtl"]:
                    if tex_name.endswith(ext):
                        param_map["Metallic"] = tex_path
                        assigned = True
                        break
            if not assigned:
                for ext in ["_height", "_hgt", "_disp"]:
                    if tex_name.endswith(ext):
                        param_map["Height"] = tex_path
                        assigned = True
                        break
        
        print(f"    Mapped: {list(param_map.keys())}")
        
        result = create_mi_for_stem(stem, param_map, parent_params, MI_ROOT)
        if result == "created":
            created += 1
        elif result == "existing":
            existing += 1
        else:
            failed += 1
    
    print(f"\n=== Results: created={created}, existing={existing}, failed={failed} ===")

if __name__ == "__main__":
    main()
