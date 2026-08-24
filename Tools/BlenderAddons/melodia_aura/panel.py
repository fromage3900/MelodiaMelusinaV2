import bpy


class AURA_PT_panel(bpy.types.Panel):
    """Melodia Aura panel in the 3D View sidebar"""
    bl_label = "Melodia Aura"
    bl_idname = "AURA_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Melodia Aura"

    def draw(self, context):
        layout = self.layout
        
        # Status
        has_aura = any(
            any(m.name.startswith('MelodiaAura_') for m in obj.modifiers)
            for obj in bpy.data.objects
        )
        
        if has_aura:
            layout.label(text="Aura Active", icon='CHECKMARK')
        else:
            layout.label(text="No Aura", icon='INFO')
        
        layout.separator()
        
        # Main cast button
        col = layout.column(align=True)
        col.scale_y = 1.5
        col.operator(
            "melodia_aura.cast_aura",
            text="Cast Aura",
            icon='SHADERFX'
        )
        
        layout.separator()
        
        # Remove
        layout.operator(
            "melodia_aura.remove_aura",
            text="Remove Aura",
            icon='X'
        )
        
        layout.separator()
        
        # Preset info
        col = layout.column(align=True)
        col.label(text="Presets (in dialog):")
        for key, name in [
            ('fire', 'Fire'),
            ('ice', 'Ice'),
            ('lightning', 'Lightning'),
            ('healing', 'Healing'),
            ('dark', 'Dark'),
            ('holy', 'Holy'),
        ]:
            col.label(text="  " + name)


def register():
    bpy.utils.register_class(AURA_PT_panel)


def unregister():
    bpy.utils.unregister_class(AURA_PT_panel)
