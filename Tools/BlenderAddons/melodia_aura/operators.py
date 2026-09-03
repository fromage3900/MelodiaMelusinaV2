import bpy
import math
from mathutils import Vector


AURA_PRESETS = {
    'fire': {
        'name': 'Fire Aura',
        'color': (1.0, 0.25, 0.05, 1.0),
        'emission': 8.0,
        'speed': 1.5,
        'turbulence': 2.0,
        'height': 1.5,
        'description': 'Rising orange flames - perfect for fire spells, rage states'
    },
    'ice': {
        'name': 'Ice Aura',
        'color': (0.4, 0.85, 1.0, 1.0),
        'emission': 5.0,
        'speed': 0.7,
        'turbulence': 0.8,
        'height': 1.0,
        'description': 'Slow crystalline mist - ice spells, freeze effects'
    },
    'lightning': {
        'name': 'Lightning Aura',
        'color': (0.9, 0.95, 1.0, 1.0),
        'emission': 12.0,
        'speed': 3.0,
        'turbulence': 4.0,
        'height': 2.0,
        'description': 'Electric crackle - buffs, haste, shock spells'
    },
    'healing': {
        'name': 'Healing Aura',
        'color': (0.4, 1.0, 0.5, 1.0),
        'emission': 4.0,
        'speed': 0.5,
        'turbulence': 0.3,
        'height': 1.2,
        'description': 'Gentle green glow - cure spells, regen, support'
    },
    'dark': {
        'name': 'Dark Aura',
        'color': (0.6, 0.1, 0.8, 1.0),
        'emission': 6.0,
        'speed': 1.0,
        'turbulence': 1.5,
        'height': 1.8,
        'description': 'Ominous purple - curse, doom, void magic'
    },
    'holy': {
        'name': 'Holy Aura',
        'color': (1.0, 0.95, 0.6, 1.0),
        'emission': 7.0,
        'speed': 0.8,
        'turbulence': 0.5,
        'height': 2.0,
        'description': 'Divine light - smite, barrier, judgment'
    },
}


def _create_aura_nodegroup():
    """Create the procedural aura geometry nodes group if it doesn't exist."""
    group_name = "MelodiaAura_EnergyField"
    
    if group_name in bpy.data.node_groups:
        return bpy.data.node_groups[group_name]
    
    ng = bpy.data.node_groups.new(group_name, 'GeometryNodeTree')
    
    # Group inputs
    ng.interface.new_socket(name="Geometry", socket_type='NodeSocketGeometry', in_out='INPUT')
    ng.interface.new_socket(name="Aura Color", socket_type='NodeSocketColor', in_out='INPUT')
    ng.interface.new_socket(name="Intensity", socket_type='NodeSocketFloat', in_out='INPUT')
    ng.interface.new_socket(name="Speed", socket_type='NodeSocketFloat', in_out='INPUT')
    ng.interface.new_socket(name="Turbulence", socket_type='NodeSocketFloat', in_out='INPUT')
    ng.interface.new_socket(name="Height", socket_type='NodeSocketFloat', in_out='INPUT')
    
    # Group output
    ng.interface.new_socket(name="Geometry", socket_type='NodeSocketGeometry', in_out='OUTPUT')
    
    nodes = ng.nodes
    links = ng.links
    
    # Clear default
    nodes.clear()
    
    # Input node
    input_node = nodes.new('NodeGroupInput')
    input_node.location = (-800, 0)
    
    # Output node
    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (800, 0)
    
    # Distribute Points on Faces (for spawning energy particles)
    distribute = nodes.new('GeometryNodeDistributePointsOnFaces')
    distribute.location = (-400, 100)
    # Blender 5.2 uses different input names - use safe access
    if 'Distance Min' in distribute.inputs:
        distribute.inputs['Distance Min'].default_value = 0.08
    if 'Density Max' in distribute.inputs:
        distribute.inputs['Density Max'].default_value = 800
    else:
        distribute.inputs['Density'].default_value = 800
    
    # Instance on Points (place energy ribbons)
    instance = nodes.new('GeometryNodeInstanceOnPoints')
    instance.location = (-100, 100)
    
    # Curve line (the ribbon shape)
    curve_line = nodes.new('GeometryNodePrimitiveCurveLine')
    curve_line.location = (-300, -100)
    curve_line.inputs['Start'].default_value = (0, 0, 0)
    curve_line.inputs['End'].default_value = (0, 0, 1)
    
    # Set curve bevel (give it thickness)
    bevel = nodes.new('GeometryNodeSetCurveBevel')
    bevel.location = (100, 100)
    bevel.inputs['Depth'].default_value = 0.015
    bevel.inputs['Resolution'].default_value = 3
    
    # Turbulence via noise displacement
    noise = nodes.new('ShaderNodeTexNoise')
    noise.location = (-200, -250)
    noise.inputs['Scale'].default_value = 2.0
    noise.inputs['Detail'].default_value = 8.0
    noise.inputs['Roughness'].default_value = 0.6
    
    # Set material (emission)
    set_material = nodes.new('GeometryNodeSetMaterial')
    set_material.location = (400, 100)
    
    # Combine XYZ for displacement
    combine_xyz = nodes.new('ShaderNodeCombineXYZ')
    combine_xyz.location = (0, -200)
    
    # Set curve points (displace ribbon)
    set_curve_pts = nodes.new('GeometryNodeSetCurvePoints')
    set_curve_pts.location = (200, -100)
    
    # Math nodes for turbulence
    math_mult = nodes.new('ShaderNodeMath')
    math_mult.location = (-50, -300)
    math_mult.operation = 'MULTIPLY'
    math_mult.inputs[1].default_value = 0.3
    
    # Link
    links.new(input_node.outputs['Geometry'], distribute.inputs['Mesh'])
    links.new(distribute.outputs['Points'], instance.inputs['Points'])
    links.new(curve_line.outputs['Curve'], instance.inputs['Instance'])
    links.new(instance.outputs['Instances'], bevel.inputs['Curve'])
    links.new(bevel.outputs['Curve'], set_material.inputs['Geometry'])
    links.new(set_material.outputs['Geometry'], output_node.inputs['Geometry'])
    
    return ng


def _create_aura_material(name, color, emission_strength):
    """Create an emission material for the aura."""
    mat_name = "MelodiaAura_{}".format(name)
    if mat_name in bpy.data.materials:
        bpy.data.materials.remove(bpy.data.materials[mat_name])
    
    mat = bpy.data.materials.new(mat_name)
    mat.use_nodes = True
    mat.blend_method = 'BLEND'  # alpha blend
    
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    # Output
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    # Emission shader
    emission = nodes.new('ShaderNodeEmission')
    emission.location = (0, 0)
    emission.inputs['Color'].default_value = color
    emission.inputs['Strength'].default_value = emission_strength
    
    # Color ramp for falloff
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.location = (-300, 0)
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[1].position = 0.6
    
    # Transparency mix
    mix = nodes.new('ShaderNodeMixShader')
    mix.location = (200, 0)
    mix.inputs['Fac'].default_value = 0.5
    
    # Transparent
    transparent = nodes.new('ShaderNodeBsdfTransparent')
    transparent.location = (0, 200)
    transparent.inputs['Color'].default_value = (1, 1, 1, 0)
    
    links.new(emission.outputs['Emission'], mix.inputs[1])
    links.new(transparent.outputs['BSDF'], mix.inputs[2])
    links.new(mix.outputs['Shader'], output.inputs['Surface'])
    
    return mat


class AURA_OT_cast_aura(bpy.types.Operator):
    """Add procedural magic aura around selected objects"""
    bl_idname = "melodia_aura.cast_aura"
    bl_label = "Cast Aura"
    bl_icon = 'SHADERFX'
    bl_options = {'REGISTER', 'UNDO'}
    
    preset: bpy.props.EnumProperty(
        name="Preset",
        items=[
            ('fire', 'Fire', 'Rising flames'),
            ('ice', 'Ice', 'Frozen mist'),
            ('lightning', 'Lightning', 'Electric crackle'),
            ('healing', 'Healing', 'Gentle glow'),
            ('dark', 'Dark', 'Ominous purple'),
            ('holy', 'Holy', 'Divine light'),
        ],
        default='fire'
    )
    
    intensity: bpy.props.FloatProperty(
        name="Intensity",
        default=1.0,
        min=0.1,
        max=5.0,
        description="Glow brightness multiplier"
    )
    
    speed: bpy.props.FloatProperty(
        name="Speed",
        default=1.0,
        min=0.1,
        max=5.0,
        description="Animation speed"
    )
    
    def execute(self, context):
        preset_key = self.preset
        preset = AURA_PRESETS[preset_key]
        
        selected = context.selected_objects
        if not selected:
            self.report({'WARNING'}, "Select at least one object")
            return {'CANCELLED'}
        
        for obj in selected:
            # Skip cameras/lights
            if obj.type in ('CAMERA', 'LIGHT'):
                continue
            
            # Create aura nodegroup
            ng = _create_aura_nodegroup()
            
            # Create material
            color = preset['color']
            mat = _create_aura_material(
                obj.name + '_' + preset_key,
                color,
                preset['emission'] * self.intensity
            )
            
            # Add geometry nodes modifier
            mod_name = "MelodiaAura_{}".format(preset_key)
            mod = obj.modifiers.new(name=mod_name, type='NODES')
            mod.node_group = ng
            
            # Set modifier inputs via identifier
            inputs_to_set = {
                'Aura Color': color,
                'Intensity': preset['emission'] * self.intensity,
                'Speed': preset['speed'] * self.speed,
                'Turbulence': preset['turbulence'],
                'Height': preset['height'],
            }
            for item in ng.interface.items_tree:
                if item.item_type == 'INPUT' and item.name in inputs_to_set:
                    input_id = item.identifier
                    if input_id in mod:
                        mod[input_id] = inputs_to_set[item.name]
        
        self.report({'INFO'}, "Aura cast on {} object(s): {}".format(
            len([o for o in selected if o.type not in ('CAMERA', 'LIGHT')]),
            preset['name']
        ))
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class AURA_OT_remove_aura(bpy.types.Operator):
    """Remove Melodia Aura from selected objects"""
    bl_idname = "melodia_aura.remove_aura"
    bl_label = "Remove Aura"
    bl_icon = 'X'
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        removed = 0
        for obj in context.selected_objects:
            to_remove = [m for m in obj.modifiers if m.name.startswith('MelodiaAura_')]
            for mod in to_remove:
                obj.modifiers.remove(mod)
                removed += 1
        
        self.report({'INFO'}, "Removed {} aura(s)".format(removed))
        return {'FINISHED'}


class AURA_OT_quick_fire(bpy.types.Operator):
    """Quick fire aura (no dialog)"""
    bl_idname = "melodia_aura.quick_fire"
    bl_label = "Quick Fire"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.melodia_aura.cast_aura(preset='fire')
        return {'FINISHED'}


class AURA_OT_quick_ice(bpy.types.Operator):
    """Quick ice aura"""
    bl_idname = "melodia_aura.quick_ice"
    bl_label = "Quick Ice"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.melodia_aura.cast_aura(preset='ice')
        return {'FINISHED'}


class AURA_OT_quick_lightning(bpy.types.Operator):
    """Quick lightning aura"""
    bl_idname = "melodia_aura.quick_lightning"
    bl_label = "Quick Lightning"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.melodia_aura.cast_aura(preset='lightning')
        return {'FINISHED'}


classes = [
    AURA_OT_cast_aura,
    AURA_OT_remove_aura,
    AURA_OT_quick_fire,
    AURA_OT_quick_ice,
    AURA_OT_quick_lightning,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
