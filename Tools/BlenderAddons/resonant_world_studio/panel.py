"""Panel that reports measured facts, not claims."""

import bpy
import json


class RW_PT_main(bpy.types.Panel):
    bl_label = "Resonant World"
    bl_idname = "RW_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Resonant World"

    def draw(self, context):
        layout = self.layout
        props = context.scene.resonant_world

        box = layout.box()
        box.label(text="Source", icon='FILE_SOUND')
        box.prop(props, "midi", text="")

        box = layout.box()
        box.label(text="Mapping", icon='MESH_GRID')
        box.prop(props, "preset", text="")
        box.prop(props, "style", text="")
        box.prop(props, "eye_level")
        box.prop(props, "with_melusina")

        col = layout.column(align=True)
        col.scale_y = 1.5
        col.operator("resonant_world.build", icon='MOD_BUILD')
        row = layout.row(align=True)
        row.operator("resonant_world.clear", icon='TRASH')
        row.operator("resonant_world.export_report", icon='EXPORT')


class RW_PT_metrics(bpy.types.Panel):
    """Measured traversability. These are computed from the heightfield --
    graph metrics, not in-engine playtest proof."""

    bl_label = "Measured"
    bl_idname = "RW_PT_metrics"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Resonant World"
    bl_parent_id = "RW_PT_main"

    def draw(self, context):
        layout = self.layout
        raw = context.scene.resonant_world.report_json
        if not raw:
            layout.label(text="No level built yet", icon='INFO')
            return

        try:
            data = json.loads(raw)
        except Exception:
            layout.label(text="Report unreadable", icon='ERROR')
            return

        foot = data.get("footprint", [0, 0])
        walk = data.get("walkable_fraction", 0.0)
        region = data.get("largest_region_fraction", 0.0)

        col = layout.column(align=True)
        col.label(text="%s -> %s" % (data.get("midi", "?"),
                                     data.get("preset", "?")))

        grid = layout.grid_flow(columns=2, even_columns=True, align=True)
        grid.label(text="Footprint")
        grid.label(text="%d x %d cells" % (foot[0], foot[1]))
        grid.label(text="Aspect")
        grid.label(text="%.2f : 1" % data.get("aspect_ratio", 0))
        grid.label(text="Height")
        grid.label(text="%d units" % data.get("height_span", 0))
        grid.label(text="Walkable")
        grid.label(text="%.1f%% of edges" % (walk * 100))
        grid.label(text="Connected")
        grid.label(text="%.0f%% one region" % (region * 100))
        grid.label(text="Voxels")
        grid.label(text="%d" % data.get("voxels", 0))
        grid.label(text="Triangles")
        grid.label(text="%d" % data.get("faces", 0))
        grid.label(text="Props")
        grid.label(text="%d" % data.get("props", 0))

        layout.separator()
        icon = 'CHECKMARK' if walk >= 0.9 and region >= 0.99 else 'ERROR'
        layout.label(text="Graph metrics, not playtest proof", icon=icon)


CLASSES = (RW_PT_main, RW_PT_metrics)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
