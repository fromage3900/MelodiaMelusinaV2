import bpy
import os, sys
from pathlib import Path

try:
    _ADDONS_ROOT = Path(__file__).resolve().parent.parent
    if str(_ADDONS_ROOT) not in sys.path:
        sys.path.insert(0, str(_ADDONS_ROOT))
    from melodia_studio import addon_utils as _au
except Exception:
    _au = None


class AURA_PT_panel(bpy.types.Panel):
    """Melodia Aura - spell auras, bespoke Melodia chrome"""
    bl_label = "Melodia Aura"
    bl_idname = "AURA_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Melodia"

    def draw(self, context):
        layout = self.layout
        if _au is not None:
            try:
                _au.draw_melodia_header(layout, "Aura", "Spell Auras  -  Geometry Nodes", icon_key="starlight")
            except Exception:
                layout.label(text="*  MELODIA  -  AURA")
        else:
            layout.label(text="*  MELODIA  -  AURA")

        has_aura = any(
            any(m.name.startswith('MelodiaAura_') for m in obj.modifiers)
            for obj in bpy.data.objects
        )

        box = layout.box()
        if has_aura:
            box.label(text="A U R A   A C T I V E", icon='CHECKMARK')
        else:
            box.label(text="N O   A U R A", icon='INFO')
        if _au is not None:
            try:
                _au.draw_gold_rule(box)
            except Exception:
                pass

        col = layout.column(align=True)
        col.scale_y = 1.6
        if _au is not None:
            try:
                col.operator("melodia_aura.cast_aura", text="Cast Aura", **_au.icon_kwargs("starlight", 'SHADERFX'))
            except Exception:
                col.operator("melodia_aura.cast_aura", text="Cast Aura", icon='SHADERFX')
        else:
            col.operator("melodia_aura.cast_aura", text="Cast Aura", icon='SHADERFX')

        row = layout.row()
        row.scale_y = 1.1
        row.operator("melodia_aura.remove_aura", text="Remove Aura", icon='X')

        box2 = layout.box()
        box2.label(text="P R E S E T S", icon='PRESET')
        for key, name in [
            ('fire', 'Fire  -  rising flames'),
            ('ice', 'Ice  -  crystalline mist'),
            ('lightning', 'Lightning  -  electric crackle'),
            ('healing', 'Healing  -  gentle glow'),
            ('dark', 'Dark  -  void purple'),
            ('holy', 'Holy  -  divine light'),
        ]:
            row = box2.row()
            row.label(text=f"*  {name}")


def register():
    bpy.utils.register_class(AURA_PT_panel)


def unregister():
    bpy.utils.unregister_class(AURA_PT_panel)
