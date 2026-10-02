"""Bake high-quality geometry variants with packed UVs for Choral Sheep.

Takes the sculpted high-poly mesh and bakes normal/AO/curvature/ID/height
maps onto the low-poly target. Generates packed UVs for 12 pitch-class
variants. Exports FBX with proper UVs for UE.

Run headless:
    blender -b --factory-startup --python choral_sheep_bake_variants.py -- \
        <S5c_blend> <out_dir> [--variants 12] [--resolution 2048]

Output:
    - <out_dir>/variants/<variant_name>.fbx  (12 FBX files)
    - <out_dir>/textures/<variant_name>_Normal.png
    - <out_dir>/textures/<variant_name>_AO.png
    - <out_dir>/textures/<variant_name>_Curvature.png
    - <out_dir>/textures/<variant_name>_ID.png
    - <out_dir>/textures/<variant_name>_Height.png
    - <out_dir>/bake_manifest.json
"""

import argparse
import json
import os
import sys

import bpy
import bmesh

# Pitch-class variant names
PITCH_CLASSES = [
    "C", "Cs", "D", "Ds", "E", "F", "Fs", "G", "Gs", "A", "As", "B"
]

# Bake maps to generate
BAKE_MAPS = [
    {"name": "Normal", "suffix": "_Normal", "engine": "NORMAL"},
    {"name": "AmbientOcclusion", "suffix": "_AO", "engine": "AO"},
    {"name": "Curvature", "suffix": "_Curvature", "engine": "CURVATURE"},
    {"name": "ID", "suffix": "_ID", "engine": "MATERIAL_ID"},
    {"name": "Height", "suffix": "_Height", "engine": "HEIGHT"},
]


def log(msg):
    print(f"[sheep-bake] {msg}", flush=True)


def load_blend(blend_path):
    """Load the S5c blend file and return key objects."""
    bpy.ops.wm.open_mainfile(filepath=blend_path)
    
    high = bpy.data.objects.get("sheephighpolydone")
    low = bpy.data.objects.get("Skin_Sheep_ZSpheres2")
    hd = bpy.data.objects.get("MrSheepFinal_HD")
    base = bpy.data.objects.get("MrSheepFinal")
    wool_cards = bpy.data.objects.get("Wool_Cards")
    wool_shell = bpy.data.objects.get("Wool_Shell")
    
    if not high or not low:
        raise RuntimeError("Missing high/low mesh objects")
    
    log(f"Loaded: high={high.name}({len(high.data.vertices)}v) "
        f"low={low.name}({len(low.data.vertices)}v)")
    
    return {
        "high": high,
        "low": low,
        "hd": hd,
        "base": base,
        "wool_cards": wool_cards,
        "wool_shell": wool_shell,
    }


def setup_collections():
    """Ensure HIGH and LOW collections exist."""
    for name in ("ChoralSheep_HIGH", "ChoralSheep_LOW"):
        if name not in bpy.data.collections:
            bpy.data.collections.new(name)
    return bpy.data.collections["ChoralSheep_HIGH"], bpy.data.collections["ChoralSheep_LOW"]


def generate_packed_uvs(mesh_obj, variant_name, resolution=2048):
    """Generate packed UVs for a variant using Blender's UV packer."""
    # Enter edit mode
    bpy.context.view_layer.objects.active = mesh_obj
    bpy.ops.object.select_all(action='DESELECT')
    mesh_obj.select_set(True)
    
    # Ensure we have a UV layer
    if not mesh_obj.data.uv_layers:
        mesh_obj.data.uv_layers.new(name="UVMap")
    
    # Select all faces
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    
    # Smart UV project for initial layout
    bpy.ops.uv.smart_project(
        angle_limit=1.15192,  # 66 degrees
        island_margin=0.02,
        area_weight=0.0,
        correct_aspect=True,
        scale_to_bounds=True,
    )
    
    # Pack islands
    bpy.ops.uv.pack_islands(
        margin=0.02,
        rotate=True,
    )
    
    bpy.ops.object.mode_set(mode='OBJECT')
    
    log(f"  UVs packed for {variant_name}: {len(mesh_obj.data.uv_layers[0].data)} loops")


def bake_map(high_obj, low_obj, map_type, out_path, resolution=2048):
    """Bake a single map from high to low using Blender 5.2 API."""
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.render.resolution_x = resolution
    scene.render.resolution_y = resolution
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.image_settings.color_depth = '16'
    
    # Select high and low
    bpy.ops.object.select_all(action='DESELECT')
    high_obj.select_set(True)
    low_obj.select_set(True)
    bpy.context.view_layer.objects.active = low_obj
    
    # Create image
    img = bpy.data.images.new(
        name=f"{low_obj.name}_{map_type}",
        width=resolution,
        height=resolution,
        alpha=False,
    )
    img.filepath_raw = out_path
    img.file_format = 'PNG'
    
    # Assign image to low mesh's active material
    if low_obj.data.materials:
        mat = low_obj.data.materials[0]
        if mat.use_nodes:
            bsdf = mat.node_tree.nodes.get("Principled BSDF")
            if bsdf:
                img_node = mat.node_tree.nodes.new("ShaderNodeTexImage")
                img_node.image = img
                img_node.location = (-300, 300)
                mat.node_tree.links.new(img_node.outputs["Color"], bsdf.inputs["Base Color"])
    
    # Bake using Blender 5.2 API
    bpy.ops.object.bake(
        type=map_type,
        use_selected_to_active=True,
        save_mode='EXTERNAL',
        filepath=out_path,
        margin=16,
    )
    
    img.save()
    log(f"  Baked {map_type} -> {os.path.basename(out_path)}")
    
    # Clean up image node
    if low_obj.data.materials:
        mat = low_obj.data.materials[0]
        if mat.use_nodes:
            for node in mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image == img:
                    mat.node_tree.nodes.remove(node)
                    break


def export_variant_fbx(mesh_obj, out_path, variant_name):
    """Export a variant FBX with proper UVs."""
    bpy.ops.object.select_all(action='DESELECT')
    mesh_obj.select_set(True)
    bpy.context.view_layer.objects.active = mesh_obj
    
    # Ensure UVs are active
    if mesh_obj.data.uv_layers:
        mesh_obj.data.uv_layers[0].active = True
        mesh_obj.data.uv_layers[0].active_render = True
    
    bpy.ops.export_scene.fbx(
        filepath=out_path,
        use_selection=True,
        object_types={'MESH'},
        add_leaf_bones=False,
        primary_bone_axis='Y',
        secondary_bone_axis='X',
        armature_nodetype='NULL',
        bake_anim=False,
        apply_unit_scale=True,
        global_scale=1.0,
    )
    log(f"  Exported {variant_name} -> {os.path.basename(out_path)}")


def create_variant_material(base_mat, variant_name, pitch_index):
    """Create a variant material with pitch-class tint."""
    mat = base_mat.copy()
    mat.name = f"MI_ChoralSheep_Coat_{variant_name}"
    
    if mat.use_nodes:
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            # Set base color based on pitch class
            hue = (pitch_index / 12.0) * 0.8  # 0-0.8 range (red to violet)
            saturation = 0.38
            value = 0.85
            
            # HSV to RGB
            import colorsys
            r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
            bsdf.inputs["Base Color"].default_value = (r, g, b, 1.0)
            
            # Set roughness
            if "Roughness" in bsdf.inputs:
                bsdf.inputs["Roughness"].default_value = 0.65
    
    return mat


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("blend_path")
    parser.add_argument("out_dir")
    parser.add_argument("--variants", type=int, default=12)
    parser.add_argument("--resolution", type=int, default=2048)
    args = parser.parse_args(argv)
    
    blend_path = args.blend_path
    out_dir = args.out_dir
    num_variants = min(args.variants, 12)
    resolution = args.resolution
    
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(os.path.join(out_dir, "variants"), exist_ok=True)
    os.makedirs(os.path.join(out_dir, "textures"), exist_ok=True)
    
    log(f"Loading {blend_path}")
    objs = load_blend(blend_path)
    high = objs["high"]
    low = objs["low"]
    hd = objs["hd"]
    base = objs["base"]
    wool_cards = objs["wool_cards"]
    wool_shell = objs["wool_shell"]
    
    hi_col, lo_col = setup_collections()
    
    # Ensure high is in HIGH collection
    if high.name not in hi_col.objects:
        hi_col.objects.link(high)
    if low.name not in lo_col.objects:
        lo_col.objects.link(low)
    
    # Get base material
    base_mat = low.data.materials[0] if low.data.materials else None
    
    manifest = {
        "schema": "melodia.choral_sheep.bake_variants.v1",
        "source_blend": os.path.basename(blend_path),
        "high_mesh": high.name,
        "low_mesh": low.name,
        "resolution": resolution,
        "variants": [],
    }
    
    for i in range(num_variants):
        variant_name = PITCH_CLASSES[i]
        log(f"Processing variant {variant_name} ({i+1}/{num_variants})")
        
        # Create variant material
        if base_mat:
            variant_mat = create_variant_material(base_mat, variant_name, i)
            low.data.materials.clear()
            low.data.materials.append(variant_mat)
        
        # Generate packed UVs
        generate_packed_uvs(low, variant_name, resolution)
        
        # Bake maps
        for bake_map in BAKE_MAPS:
            out_path = os.path.join(
                out_dir, "textures",
                f"{variant_name}{bake_map['suffix']}.png"
            )
            try:
                bake_map(high, low, bake_map["engine"], out_path, resolution)
            except Exception as e:
                log(f"  WARNING: Failed to bake {bake_map['name']}: {e}")
        
        # Export variant FBX
        variant_fbx = os.path.join(out_dir, "variants", f"{variant_name}.fbx")
        export_variant_fbx(low, variant_fbx, variant_name)
        
        manifest["variants"].append({
            "name": variant_name,
            "semitone": i,
            "fbx": f"variants/{variant_name}.fbx",
            "textures": {
                "normal": f"textures/{variant_name}_Normal.png",
                "ao": f"textures/{variant_name}_AO.png",
                "curvature": f"textures/{variant_name}_Curvature.png",
                "id": f"textures/{variant_name}_ID.png",
                "height": f"textures/{variant_name}_Height.png",
            }
        })
    
    # Write manifest
    manifest_path = os.path.join(out_dir, "bake_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    log(f"Manifest -> {manifest_path}")
    
    log("DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
