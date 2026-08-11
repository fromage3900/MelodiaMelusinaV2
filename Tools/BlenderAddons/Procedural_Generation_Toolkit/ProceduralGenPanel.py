import bpy

from .ProceduralGenProperties import DataSingleton
from .Action import Action
from .DropDown import DropDown
   
class OBJECT_PT_Procedural_Gen_Panel(bpy.types.Panel):
    bl_idname = "PGT_PT_procedural_gen_panel"
    bl_label = "PGT"
    bl_category = "PGT"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        props = scene.Procedural_Gen_Props
        data = DataSingleton()

        if not data.IsInitialized:

            props.CreateOperations(context)

        box = layout.box()
        box.label(text="Procedural Generation", icon='GHOST_ENABLED')
        row = box.row()
        row.label(text="Generation Method:")
        row = box.row()    
        row.template_icon_view(props, "OperationsType", show_labels=True, scale=8,scale_popup=6)

        ExProps = getattr(scene,props.OperationsType)
        if data.ActiveOperation != None:
            box2 = box.box()
            for e in data.ActiveOperation.Elements:
                e.Draw(ExProps, box2)
                    
        data = DataSingleton()
        if data.ActiveOperation.InputObjNeeded and data.ActiveOperation.MaxVert != 0:
            row = box.row()    
            row.label(text=("Current Verts: "+str(props.CurrentInputVertices)))
            row = box.row()     
            row.prop(props, "MaxInputVertices")
        
        if len(data.ActiveOperation.GetActiveActions()) > 1:
            row = box.row()   
            row.operator('object.operation_executor')

        box = layout.box()
        row = box.row()
        row.operator('object.procedural_gen_randomize_parameters') 
        row = box.row()
        row.operator('object.procedural_gen_reset_parameters')
        row = box.row()
        row.operator('object.procedural_gen_copy_parameters')  
        row = box.row()
        row.operator('object.procedural_gen_paste_parameters')   
        row = layout.row()
        row.operator('object.duplicate_and_apply_all_mods')


class OBJECT_PT_Presets_Panel(bpy.types.Panel):
    bl_idname = "PGT_PT_preset_panel"
    bl_label = "Presets"
    bl_category = "PGT"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        row = layout.row() 
        row.template_list("PROP_UL_PGTList", "The_List", scene, "PGT_PROP_LIST", scene, "PGTlist_index") 
        row = layout.row()
        row.alignment = 'CENTER'
        row.operator('pgt_list.new_pgtitem',icon='ADD') 
        row.operator('pgt_list.delete_pgtitem',icon='TRASH') 
        row.operator('pgt_list.move_pgtitem',icon='TRIA_UP').direction = 'UP' 
        row.operator('pgt_list.move_pgtitem', icon='TRIA_DOWN').direction = 'DOWN'
        row.operator('pgt_list.load_pgtitem', icon='IMPORT')

class OBJECT_PT_Info_Panel(bpy.types.Panel):
    bl_idname = "PGT_PT_info_panel"
    bl_label = "Info"
    bl_category = "PGT"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout

        row = layout.row()

        box = layout.box()
        
        op = box.operator('wm.url_open', text='Discord', icon='ANTIALIASED')
        op.url = 'https://discord.gg/QGDXP5yQuj'

        row = box.row()
        op = row.operator('wm.url_open', text='YouTube',icon='FILE_MOVIE')
        op.url = 'https://www.youtube.com/@JonasMangelschots'

        row = box.row()
        op = row.operator('wm.url_open', text='Instagram', icon='SCENE')
        op.url = 'https://www.instagram.com/jonasmangelschots/'

        row = box.row()
        op = row.operator('wm.url_open', text='Gumroad', icon='LIBRARY_DATA_DIRECT')
        op.url = 'https://jonasmangelschots.gumroad.com/'

        row = box.row()
        op = row.operator('wm.url_open', text='Blender Market', icon='BLENDER')
        op.url = 'https://blendermarket.com/creators/jonasmangelschots'