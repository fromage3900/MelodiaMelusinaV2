"""
Procedural Material Generator — Creates kawaii pastel materials with shaders.

Generates complete material setups with:
- 8 curated pastel palettes
- Plushie fabric shader (fuzzy, soft)
- Sparkle/magic effects
- Gradient materials
- Subsurface scattering for soft look
"""

import bpy
from typing import Dict, Tuple, Optional


# Curated kawaii color palettes
KAWAII_PALETTES = {
    'pastel_pink': {
        'name': 'Pastel Pink',
        'primary': (1.0, 0.71, 0.76, 1.0),      # Soft pink
        'secondary': (1.0, 0.84, 0.87, 1.0),     # Light pink
        'accent': (1.0, 0.41, 0.51, 1.0),        # Hot pink
        'dark': (0.98, 0.60, 0.68, 1.0),
    },
    'pastel_blue': {
        'name': 'Pastel Blue',
        'primary': (0.68, 0.85, 0.9, 1.0),
        'secondary': (0.80, 0.90, 0.95, 1.0),
        'accent': (0.45, 0.70, 0.85, 1.0),
        'dark': (0.55, 0.75, 0.85, 1.0),
    },
    'pastel_lavender': {
        'name': 'Lavender Dream',
        'primary': (0.79, 0.67, 0.86, 1.0),
        'secondary': (0.88, 0.79, 0.93, 1.0),
        'accent': (0.65, 0.50, 0.75, 1.0),
        'dark': (0.70, 0.58, 0.78, 1.0),
    },
    'pastel_mint': {
        'name': 'Mint Fresh',
        'primary': (0.60, 0.95, 0.77, 1.0),
        'secondary': (0.77, 0.97, 0.86, 1.0),
        'accent': (0.40, 0.85, 0.65, 1.0),
        'dark': (0.50, 0.85, 0.70, 1.0),
    },
    'pastel_peach': {
        'name': 'Peachy',
        'primary': (1.0, 0.80, 0.67, 1.0),
        'secondary': (1.0, 0.88, 0.78, 1.0),
        'accent': (1.0, 0.65, 0.50, 1.0),
        'dark': (0.95, 0.72, 0.60, 1.0),
    },
    'pastel_yellow': {
        'name': 'Sunny',
        'primary': (1.0, 0.93, 0.60, 1.0),
        'secondary': (1.0, 0.96, 0.77, 1.0),
        'accent': (1.0, 0.85, 0.40, 1.0),
        'dark': (0.95, 0.85, 0.55, 1.0),
    },
    'pastel_lilac': {
        'name': 'Lilac',
        'primary': (0.85, 0.75, 0.90, 1.0),
        'secondary': (0.92, 0.85, 0.95, 1.0),
        'accent': (0.75, 0.60, 0.82, 1.0),
        'dark': (0.78, 0.68, 0.85, 1.0),
    },
    'rainbow': {
        'name': 'Rainbow Magic',
        'primary': (1.0, 0.71, 0.76, 1.0),
        'secondary': (0.68, 0.85, 0.9, 1.0),
        'accent': (1.0, 0.93, 0.60, 1.0),
        'dark': (0.79, 0.67, 0.86, 1.0),
    },
}


class KawaiiMaterialGenerator:
    """Generates procedural kawaii materials."""
    
    @staticmethod
    def create_pastel_material(
        name: str,
        palette: str = 'pastel_pink',
        roughness: float = 0.6,
        metallic: float = 0.0,
        subsurface: float = 0.3,
        use_gradient: bool = False,
    ) -> bpy.types.Material:
        """Create a pastel material with PBR nodes."""
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        
        # Clear default nodes
        nodes.clear()
        
        # Get palette colors
        pal = KAWAII_PALETTES.get(palette, KAWAII_PALETTES['pastel_pink'])
        
        # Create nodes
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (600, 0)
        
        principled = nodes.new('ShaderNodeBsdfPrincipled')
        principled.location = (300, 0)
        principled.inputs['Roughness'].default_value = roughness
        principled.inputs['Metallic'].default_value = metallic
        principled.inputs['Subsurface'].default_value = subsurface
        principled.inputs['Subsurface Color'].default_value = pal['primary']
        
        # Color input
        color_node = nodes.new('ShaderNodeRGB')
        color_node.location = (0, 100)
        color_node.outputs['Color'].default_value = pal['primary']
        
        # Optional gradient
        if use_gradient:
            gradient = nodes.new('ShaderNodeTexGradient')
            gradient.location = (-300, 100)
            gradient.gradient_type = 'LINEAR'
            
            mapping = nodes.new('ShaderNodeMapping')
            mapping.location = (-600, 100)
            
            tex_coord = nodes.new('ShaderNodeTexCoord')
            tex_coord.location = (-900, 100)
            
            # Create gradient stops
            gradient_elem = color_node.color_elements
            gradient_elem[0].position = 0.0
            gradient_elem[0].color = pal['secondary']
            new_elem = gradient_elem.new(0.5)
            new_elem.color = pal['primary']
            new_elem = gradient_elem.new(1.0)
            new_elem.color = pal['accent']
            
            links.new(tex_coord.outputs['Generated'], mapping.inputs['Vector'])
            links.new(mapping.outputs['Vector'], gradient.inputs['Vector'])
            links.new(gradient.outputs['Fac'], principled.inputs['Base Color'])
        else:
            links.new(color_node.outputs['Color'], principled.inputs['Base Color'])
        
        links.new(principled.outputs['BSDF'], output.inputs['Surface'])
        
        return mat
    
    @staticmethod
    def create_plushie_fabric(
        name: str,
        palette: str = 'pastel_pink',
        fuzziness: float = 0.8,
    ) -> bpy.types.Material:
        """Create plushie fabric material with fuzzy look."""
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        
        nodes.clear()
        
        pal = KAWAII_PALETTES.get(palette, KAWAII_PALETTES['pastel_pink'])
        
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (800, 0)
        
        # Sheen for fabric look
        principled = nodes.new('ShaderNodeBsdfPrincipled')
        principled.location = (400, 0)
        principled.inputs['Roughness'].default_value = 0.9
        principled.inputs['Sheen'].default_value = fuzziness
        principled.inputs['Sheen Tint'].default_value = 0.5
        principled.inputs['Subsurface'].default_value = 0.5
        principled.inputs['Subsurface Color'].default_value = pal['secondary']
        
        # Noise texture for fuzz
        noise = nodes.new('ShaderNodeTexNoise')
        noise.location = (-200, 100)
        noise.inputs['Scale'].default_value = 15.0
        noise.inputs['Detail'].default_value = 2.0
        noise.inputs['Roughness'].default_value = 0.8
        
        # Bump for texture
        bump = nodes.new('ShaderNodeBump')
        bump.location = (100, 200)
        bump.inputs['Strength'].default_value = 0.3
        
        # Color
        color_node = nodes.new('ShaderNodeRGB')
        color_node.location = (-200, 300)
        color_node.outputs['Color'].default_value = pal['primary']
        
        links.new(color_node.outputs['Color'], principled.inputs['Base Color'])
        links.new(noise.outputs['Fac'], bump.inputs['Height'])
        links.new(bump.outputs['Normal'], principled.inputs['Normal'])
        links.new(principled.outputs['BSDF'], output.inputs['Surface'])
        
        return mat
    
    @staticmethod
    def create_sparkle_material(
        name: str,
        palette: str = 'pastel_yellow',
        intensity: float = 1.0,
    ) -> bpy.types.Material:
        """Create magical sparkle material."""
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        
        nodes.clear()
        
        pal = KAWAII_PALETTES.get(palette, KAWAII_PALETTES['pastel_yellow'])
        
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (800, 0)
        
        # Emissive sparkle
        emission = nodes.new('ShaderNodeEmission')
        emission.location = (400, -100)
        emission.inputs['Strength'].default_value = intensity * 5.0
        
        # Mix with principled
        principled = nodes.new('ShaderNodeBsdfPrincipled')
        principled.location = (400, 100)
        principled.inputs['Roughness'].default_value = 0.3
        principled.inputs['Metallic'].default_value = 0.1
        
        # Mix shader
        mix = nodes.new('ShaderNodeMixShader')
        mix.location = (600, 0)
        mix.inputs['Fac'].default_value = 0.5
        
        # Wave texture for sparkle pattern
        wave = nodes.new('ShaderNodeTexWave')
        wave.location = (-200, 100)
        wave.inputs['Scale'].default_value = 10.0
        
        color_node = nodes.new('ShaderNodeRGB')
        color_node.location = (-200, 300)
        color_node.outputs['Color'].default_value = pal['primary']
        
        links.new(color_node.outputs['Color'], principled.inputs['Base Color'])
        links.new(color_node.outputs['Color'], emission.inputs['Color'])
        links.new(wave.outputs['Fac'], mix.inputs['Fac'])
        links.new(principled.outputs['BSDF'], mix.inputs[1])
        links.new(emission.outputs['Emission'], mix.inputs[2])
        links.new(mix.outputs['Shader'], output.inputs['Surface'])
        
        return mat


def register():
    """Register material generator."""
    pass


def unregister():
    """Unregister material generator."""
    pass
