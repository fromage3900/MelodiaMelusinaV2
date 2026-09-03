"""Brutalist GN Operators - One per generator."""
import bpy
from ..core.gn_framework import BRUTALIST_GN_REGISTRY


def create_generator_operators():
    """Create operator classes for all registered generators."""
    operators = []
    
    for gen_id, gen_class in BRUTALIST_GN_REGISTRY.items():
        # Create unique operator class
        class_name = f"MELOBRUTALIST_OT_create_{gen_id}"
        class_label = f"Create {gen_class.generator_name}"
        
        operator_class = type(
            class_name,
            (bpy.types.Operator,),
            {
                "bl_idname": f"melobrutalist_gn.create_{gen_id}",
                "bl_label": class_label,
                "bl_description": gen_class.description,
                "bl_options": {'REGISTER', 'UNDO'},
                
                "execute": lambda self, context, gc=gen_class: _create_generator(self, context, gc),
            }
        )
        
        operators.append(operator_class)
    
    return operators


def _create_generator(self, context, gen_class):
    """Create the generator object."""
    try:
        obj = gen_class.create_object()
        context.view_layer.objects.active = obj
        obj.select_set(True)
        self.report({'INFO'}, f"Created {gen_class.generator_name}")
        return {'FINISHED'}
    except Exception as e:
        self.report({'ERROR'}, f"Failed to create {gen_class.generator_name}: {str(e)}")
        return {'CANCELLED'}


def register():
    """Register all generator operators."""
    for op_class in create_generator_operators():
        try:
            bpy.utils.register_class(op_class)
        except:
            pass


def unregister():
    """Unregister all generator operators."""
    for op_class in create_generator_operators():
        try:
            bpy.utils.unregister_class(op_class)
        except:
            pass
