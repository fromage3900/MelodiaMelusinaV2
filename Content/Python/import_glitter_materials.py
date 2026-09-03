#!/usr/bin/env python
"""
Import glitter PBR textures from Copernicus pipeline and create Material Instances on M_Master_Nikki.

Run via Monolith run_python action:
  monolith run_python Content/Python/import_glitter_materials.py

This script:
1. Imports 9 PBR textures per variant from Saved/Audit/copernicus_cymatic/<Variant>/
2. Creates Material Instance Constants on M_Master_Nikki
3. Wires all texture parameters
4. Sets scalar params (Metallic=1.0, Roughness=0.05, Iridescence=0.8, Parallax)
5. Saves all assets

5 variants: GlitterRainbow, GlitterHolographic, GlitterGold, GlitterIridescent, GlitterCrystal
"""

import unreal
import os

PROJECT_ROOT = 'C:/EnvironmentPortfolio/BS_GodFile'
TEXTURE_SRC = f'{PROJECT_ROOT}/Saved/Audit/copernicus_cymatic'
TEXTURE_DST = '/Game/EnvSandbox/Textures/Glitter'
MI_BASE = '/Game/EnvSandbox/Materials/Instances/Glitter'
PARENT_PATH = '/Game/EnvSandbox/Materials/Masters/M_Master_Nikki'

VARIANTS = ['GlitterRainbow', 'GlitterHolographic', 'GlitterGold', 'GlitterIridescent', 'GlitterCrystal']
MAPS = ['BaseColor', 'Normal', 'Roughness', 'Metallic', 'Height', 'Emissive', 'Iridescence', 'ORM', 'Opacity']

# Glitter-specific scalar params
GLITTER_PARAMS = {
    'GlitterRainbow': {'Metallic': 1.0, 'Roughness': 0.05, 'Iridescence': 0.85, 'ParallaxStrength': 0.35, 'ParallaxScale': 0.08, 'ParallaxHeight': 0.12},
    'GlitterHolographic': {'Metallic': 1.0, 'Roughness': 0.03, 'Iridescence': 1.0, 'ParallaxStrength': 0.35, 'ParallaxScale': 0.08, 'ParallaxHeight': 0.12},
    'GlitterGold': {'Metallic': 1.0, 'Roughness': 0.04, 'Iridescence': 0.6, 'ParallaxStrength': 0.35, 'ParallaxScale': 0.08, 'ParallaxHeight': 0.12},
    'GlitterIridescent': {'Metallic': 1.0, 'Roughness': 0.02, 'Iridescence': 1.0, 'ParallaxStrength': 0.35, 'ParallaxScale': 0.08, 'ParallaxHeight': 0.12},
    'GlitterCrystal': {'Metallic': 0.95, 'Roughness': 0.01, 'Iridescence': 0.8, 'ParallaxStrength': 0.35, 'ParallaxScale': 0.08, 'ParallaxHeight': 0.12},
}

def import_texture(src_path, dst_path, dst_name):
    """Import a PNG texture into Unreal."""
    if not os.path.exists(src_path):
        print(f'  MISSING: {src_path}')
        return None
    
    # Check if already exists
    existing = unreal.load_asset(dst_path)
    if existing:
        print(f'  EXISTS: {dst_name}')
        return existing
    
    # Create import task
    task = unreal.AssetImportTask()
    task.set_editor_property('filename', src_path)
    task.set_editor_property('destination_path', os.path.dirname(dst_path).replace('\\', '/'))
    task.set_editor_property('destination_name', dst_name)
    task.set_editor_property('replace_existing', True)
    task.set_editor_property('automated', True)
    task.set_editor_property('save', True)
    
    # Configure texture settings based on map type
    tex_type = dst_name.split('_')[-1] if '_' in dst_name else ''
    
    # Import
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    tools.import_asset_tasks([task])
    
    # Load and configure
    tex = unreal.load_asset(dst_path)
    if tex:
        # Set compression based on type
        if tex_type in ['Normal']:
            tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_NORMALMAP)
        elif tex_type in ['Roughness', 'Metallic', 'Height', 'ORM']:
            tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_GRAYSCALE)
        elif tex_type in ['Emissive', 'Iridescence']:
            tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_DEFAULT)
        elif tex_type in ['Opacity']:
            tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_GRAYSCALE)
        
        # sRGB for color maps
        if tex_type in ['BaseColor', 'Emissive', 'Iridescence']:
            tex.set_editor_property('srgb', True)
        else:
            tex.set_editor_property('srgb', False)
        
        unreal.EditorAssetLibrary.save_loaded_asset(tex)
        print(f'  IMPORTED: {dst_name}')
    
    return tex

def create_material_instance(variant_name):
    """Create a Material Instance Constant for the glitter variant."""
    mi_path = f'{MI_BASE}/{variant_name}'
    
    # Check if exists
    existing = unreal.load_asset(mi_path)
    if existing:
        print(f'{variant_name}: MI already exists, updating textures...')
        mi = existing
    else:
        # Create new MI
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        mi = tools.create_asset(variant_name, MI_BASE, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactory())
        if not mi:
            print(f'{variant_name}: FAILED to create MI')
            return None
        print(f'{variant_name}: MI created')
    
    # Set parent
    parent = unreal.load_asset(PARENT_PATH)
    if parent:
        mi.set_editor_property('parent', parent)
    
    # Import and wire textures
    for m in MAPS:
        src = f'{TEXTURE_SRC}/{variant_name}/T_Cymatic_{variant_name}_{m}.png'
        dst = f'{TEXTURE_DST}/{variant_name}_{m}'
        
        tex = import_texture(src, dst, f'{variant_name}_{m}')
        if tex:
            # Wire to MI
            param_map = {
                'BaseColor': 'BaseColor',
                'Normal': 'Normal',
                'Roughness': 'Roughness',
                'Metallic': 'Metallic',
                'Height': 'Height',
                'Emissive': 'Emissive',
                'Iridescence': 'Iridescence',
                'ORM': 'ORM',
                'Opacity': 'Opacity',
            }
            param_name = param_map.get(m, m)
            try:
                unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(mi, param_name, tex)
                print(f'    Wired {param_name}')
            except Exception as e:
                print(f'    WARN: Could not wire {param_name}: {e}')
    
    # Set scalar params
    params = GLITTER_PARAMS.get(variant_name, {})
    for param_name, value in params.items():
        try:
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, param_name, value)
            print(f'    Scalar {param_name} = {value}')
        except Exception as e:
            print(f'    WARN: Could not set {param_name}: {e}')
    
    # Save
    unreal.EditorAssetLibrary.save_loaded_asset(mi)
    print(f'{variant_name}: SAVED')
    return mi

def main():
    print('=== Glitter Material Import ===')
    print(f'Parent: {PARENT_PATH}')
    print(f'Output: {MI_BASE}')
    print()
    
    # Ensure directories exist
    os.makedirs(f'{PROJECT_ROOT}/Saved/Audit/copernicus_cymatic', exist_ok=True)
    
    for v in VARIANTS:
        print(f'--- {v} ---')
        create_material_instance(v)
        print()
    
    print('=== COMPLETE ===')
    print(f'Created {len(VARIANTS)} glitter Material Instances')
    print(f'Location: {MI_BASE}')

if __name__ == '__main__':
    main()
