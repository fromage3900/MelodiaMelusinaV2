import bpy

class WM_OT_popup(bpy.types.Operator):
    bl_label= "Warning"
    bl_idname="wm.popup"

    ErrMsg : bpy.props.StringProperty(default="")
    Sol : bpy.props.StringProperty(default="")

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout

        layout.label(text=self.ErrMsg)
        layout.row().label(text=self.Sol)

