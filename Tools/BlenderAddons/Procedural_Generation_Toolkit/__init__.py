# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
import importlib
from .ProceduralGenProperties import DataSingleton

bl_info = {
    "name" : "Procedural Generation Toolkit",
    "author" : "Jonas Mangelschots",
    "description" : "",
    "blender" : (3, 5, 0),
    "version" : (1, 0, 0),
    "location" : "",
    "warning" : "",
    "category" : "Generic"
}

if "bpy" in locals():
    import importlib
    importlib.reload(OBJECT_OT_Execute_OP)
    importlib.reload(OBJECT_PT_Procedural_Gen_Panel)
    importlib.reload(OBJECT_PT_Presets_Panel)
    importlib.reload(OBJECT_PT_Info_Panel)
    importlib.reload(Procedural_Gen_Properties)
    importlib.reload(OBJECT_OT_Reset_Params)
    importlib.reload(OBJECT_OT_Duplicate_And_Apply_All_Mods_Op)
    importlib.reload(OBJECT_OT_Randomize_Params)
    importlib.reload(OBJECT_OT_Copy_Params)
    importlib.reload(OBJECT_OT_Paste_Params)
    importlib.reload(ACTION_OT_executorpgt)
    importlib.reload(WM_OT_popup)
    importlib.reload(WM_OT_popup)
    importlib.reload(WM_OT_popup)
    importlib.reload(WM_OT_popup)
    importlib.reload(WM_OT_popup)
    importlib.reload(PGT_listI)
    importlib.reload(PROP_UL_PGTList)
    importlib.reload(LIST_OT_DeletePGTItem)
    importlib.reload(LIST_OT_LoadPGTItem)
    importlib.reload(LIST_OT_MovePGTItem)
    importlib.reload(LIST_OT_NewPGTItem)

    JDLCImp = JDLCImporter()
    JDLCImp.Reaload()
else:
    from . OperationExecutor import OBJECT_OT_Execute_OP
    from . ProceduralGenPanel import OBJECT_PT_Procedural_Gen_Panel
    from . ProceduralGenPanel import OBJECT_PT_Presets_Panel
    from . ProceduralGenPanel import OBJECT_PT_Info_Panel

    from . ProceduralGenProperties import Procedural_Gen_Properties
    from . ProceduralGenResetParam import OBJECT_OT_Reset_Params
    from . ApplyAndDuplicate import OBJECT_OT_Duplicate_And_Apply_All_Mods_Op
    from . ProceduralGenPropRandomizer import OBJECT_OT_Randomize_Params
    from . CopyParams import OBJECT_OT_Copy_Params
    from . PasteParams import OBJECT_OT_Paste_Params
    from . JDLCImporter import JDLCImporter
    from . ActionExecutor import ACTION_OT_executorpgt
    from . Popup import WM_OT_popup
    from . PresetList import Regi
    from . PresetList import PGT_listI
    from . PresetList import PROP_UL_PGTList
    from . PresetList import LIST_OT_DeletePGTItem
    from . PresetList import LIST_OT_LoadPGTItem
    from . PresetList import LIST_OT_MovePGTItem
    from . PresetList import LIST_OT_NewPGTItem
    
    JDLCImp = JDLCImporter()
    JDLCImp.Load()
import bpy
from bpy.app.handlers import persistent

classes = (PGT_listI,PROP_UL_PGTList,LIST_OT_NewPGTItem,LIST_OT_DeletePGTItem,LIST_OT_MovePGTItem,LIST_OT_LoadPGTItem,WM_OT_popup,ACTION_OT_executorpgt,OBJECT_OT_Paste_Params,OBJECT_OT_Copy_Params,OBJECT_OT_Execute_OP,OBJECT_PT_Procedural_Gen_Panel,Procedural_Gen_Properties,OBJECT_OT_Reset_Params,OBJECT_OT_Duplicate_And_Apply_All_Mods_Op,OBJECT_OT_Randomize_Params,OBJECT_PT_Presets_Panel,OBJECT_PT_Info_Panel)
classes = classes + JDLCImp.GetClasses()

@persistent
def Update(scene,depsgraph):
    data = DataSingleton()
    if not data.ActiveOperation:
        return
    for E in data.ActiveOperation.Elements:
        E.Update()
    CalculateVerts(scene,depsgraph)

def CalculateVerts(scene,depsgraph):
    props = scene.Procedural_Gen_Props

    if not depsgraph.id_type_updated('MESH') and bpy.context.view_layer.objects.active == props.ActiveObj:
        return

    props.ActiveObj = bpy.context.view_layer.objects.active
    ob = bpy.context.view_layer.objects.active

    if ob and ob.mode == "OBJECT" and ob.type == 'MESH':
        ob = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()) 
        me = ob.to_mesh()

        props.CurrentInputVertices = len(me.vertices) 

@persistent
def load(self):
    scene = bpy.context.scene
    props = scene.Procedural_Gen_Props
    props.LoadActivePanel(bpy.context)   

def register():
    
    if not load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(load)
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.Procedural_Gen_Props = bpy.props.PointerProperty(type = Procedural_Gen_Properties)
    JDLCImp.Register()
    if not Update in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(Update)

    Regi.register()

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    JDLCImp.Unregister()
    del bpy.types.Scene.Procedural_Gen_Props

    if Update in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(Update)
    if load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load)
    bpy.ExPropsGroups = {}
    Regi.unregister()