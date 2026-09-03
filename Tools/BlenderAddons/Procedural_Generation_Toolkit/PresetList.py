import bpy 
from bpy.props import StringProperty, IntProperty, CollectionProperty
from bpy.types import PropertyGroup, UIList, Operator
from . PasteParams import PasteParams
from . CopyParams import CopyParams
from . JDLCImporter import JDLCImporter

class PGT_listI(PropertyGroup):
    def savePresets(self,context):
        self.name = self.name.replace(',', ' ')
        JDCL = JDLCImporter()
        JDCL.SavePresets(context)
    """Group of properties representing an item in the list""" 
    name: StringProperty( name="", description="This is a parameter preset", default="Untitled",update=savePresets) 
    seed: StringProperty( name="ParamSeed", description="", default="") 
    
class PROP_UL_PGTList(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index): 
        # We could write some code to decide which icon to use here... 
        custom_icon = 'FUND' 

        # Make sure your code supports all 3 layout types 
        if self.layout_type in {'DEFAULT', 'COMPACT'}: 
            layout.prop(item,"name", icon = custom_icon, emboss=False) 
        elif self.layout_type in {'GRID'}: 
            layout.alignment = 'CENTER' 
            layout.label(text="", icon = custom_icon) 
            
class LIST_OT_NewPGTItem(Operator): 
    """Add Preset""" 
    bl_idname = "pgt_list.new_pgtitem" 
    bl_label = "" 

    def execute(self, context): 
        item = context.scene.PGT_PROP_LIST.add()
        item.seed = CopyParams(context).decode("utf-8")  

        JDCL = JDLCImporter()
        JDCL.SavePresets(context)
        
        return{'FINISHED'} 
        
class LIST_OT_DeletePGTItem(Operator): 
    """Delete Preset""" 
    bl_idname = "pgt_list.delete_pgtitem" 
    bl_label = "" 
    
    @classmethod 
    def poll(cls, context): 
        return context.scene.PGT_PROP_LIST 

    def execute(self, context): 
        PGT_PROP_LIST = context.scene.PGT_PROP_LIST 
        index = context.scene.PGTlist_index 
        PGT_PROP_LIST.remove(index) 
        context.scene.PGTlist_index = min(max(0, index - 1), len(PGT_PROP_LIST) - 1) 

        JDCL = JDLCImporter()
        JDCL.SavePresets(context)

        return{'FINISHED'} 
class LIST_OT_MovePGTItem(Operator): 
    """Move an item in the list"""
    bl_idname = "pgt_list.move_pgtitem" 
    bl_label = "" 
    direction: bpy.props.EnumProperty(items=(('UP', 'Up', ""), ('DOWN', 'Down', ""),)) 
    
    @classmethod 
    def poll(cls, context): 
        return context.scene.PGT_PROP_LIST 

    def move_index(self): 
        """ Move index of an item render queue while clamping it. """ 
        index = bpy.context.scene.PGTlist_index 
        list_length = len(bpy.context.scene.PGT_PROP_LIST) - 1 
        # (index starts at 0) 
        new_index = index + (-1 if self.direction == 'UP' else 1) 
        bpy.context.scene.PGTlist_index = max(0, min(new_index, list_length)) 

    def execute(self, context): 
        PGT_PROP_LIST = context.scene.PGT_PROP_LIST 
        index = context.scene.PGTlist_index 
        neighbor = index + (-1 if self.direction == 'UP' else 1) 
        PGT_PROP_LIST.move(neighbor, index) 
        self.move_index() 
#
        JDCL = JDLCImporter()
        JDCL.SavePresets(context)
        return{'FINISHED'}
class LIST_OT_LoadPGTItem(Operator): 
    """Load Preset""" 
    bl_idname = "pgt_list.load_pgtitem" 
    bl_label = "" 
    
    @classmethod 
    def poll(cls, context): 
        return context.scene.PGT_PROP_LIST 

    def execute(self, context): 
        PGT_PROP_LIST = context.scene.PGT_PROP_LIST 
        index = context.scene.PGTlist_index 
        PasteParams(context,PGT_PROP_LIST[index].seed)
        return{'FINISHED'}

class Regi():
    def __init__(self):
        return        
    def register(): 
        bpy.types.Scene.PGT_PROP_LIST = CollectionProperty(type = PGT_listI)
        bpy.types.Scene.PGTlist_index = IntProperty(name = "Index for PGT_PROP_LIST", default = 0) 

    def unregister(): 
        del bpy.types.Scene.PGT_PROP_LIST 
        del bpy.types.Scene.PGTlist_index 
