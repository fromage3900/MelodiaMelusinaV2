import bpy
from .operator import RunCommand, SkipCurrentCommand, MarkCleanMessage, OpenLogWindow
from .i18n.translations.zh_HANS import PANEL_TCTX, OPS_TCTX, PROP_TCTX
from .preference import get_pref
from .icon import Icon


class MCP_PT_Client(bpy.types.Panel):
    bl_label = "Genesis Core"
    bl_idname = "MCP_PT_Client"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Genesis Core"
    bl_translation_context = PANEL_TCTX
    record_count = 0
    direction = 1
    record_width = 16

    @classmethod
    def update_record_count(cls):
        cls.record_count += cls.direction
        if cls.record_count >= (cls.record_width - 1) or cls.record_count <= 0:
            cls.direction *= -1

    def draw(self, context):
        try:
            layout = self.layout
            pref = get_pref()
            mcp_props = bpy.context.scene.mcp_props
            box = layout.box()
            box.column().prop(pref, "tools", expand=True)
            row = box.row(align=True)
            row.prop(mcp_props, "command")
            row.operator(OpenLogWindow.bl_idname, text="", icon="LINENUMBERS_ON", text_ctxt=OPS_TCTX)
            self.show_image_box(box)
            col = box.column()
            # 如果正在执行命令，则禁用命令输入框
            client = pref.get_client_by_name(pref.provider)
            processing = False
            if client and (c := client.get()):
                processing = c.command_processing
            if processing:
                col.label(text="Processing...")
                row = col.row(align=True)
                self.update_record_count()
                # 绘制图标行
                for i in range(self.record_width):
                    if self.record_count - 1 <= i <= self.record_count + 1:
                        row.label(text="", icon="RADIOBUT_ON")
                    else:
                        row.label(text="", icon="RADIOBUT_OFF")
                col = box.column()
            col.scale_y = 2
            col.scale_x = 1.5
            col.enabled = bool(bpy.context.scene.mcp_props.command)
            row = col.row(align=True)
            row.operator(RunCommand.bl_idname, text_ctxt=OPS_TCTX)
            row.operator(SkipCurrentCommand.bl_idname, icon="PAUSE", text="", text_ctxt=OPS_TCTX)
            row.prop(pref, "use_history_message", text="", icon="WORDWRAP_ON", text_ctxt=PROP_TCTX)
            row.operator(MarkCleanMessage.bl_idname, icon="TRASH", text="", text_ctxt=OPS_TCTX)

            box = layout.box()
            pref.draw_ex(box)
        except Exception as e:
            print(e)

    def show_image_box(self, layout: bpy.types.UILayout):
        mcp_props = bpy.context.scene.mcp_props
        row = layout.row(align=True)
        row.template_ID(mcp_props, "image", new="image.new", open="image.open")
        row.prop(mcp_props, "use_viewport_image", text="", icon="RESTRICT_VIEW_OFF", text_ctxt=PROP_TCTX)
        if not mcp_props.image:
            return
        box = layout.box()
        prev: bpy.types.Image = mcp_props.image
        # 显示高清大图
        if not prev:
            return
        if prev.name not in Icon:
            Icon.reg_icon_by_pixel(prev, prev.name)
        icon_id = Icon[prev.name]
        box.template_icon(icon_value=icon_id, scale=12)


clss = [
    MCP_PT_Client,
]

register, unregister = bpy.utils.register_classes_factory(clss)
