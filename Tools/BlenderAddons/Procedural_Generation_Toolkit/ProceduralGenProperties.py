import bpy
from . JDLCImporter import JDLCImporter

from . DataSingleton import DataSingleton

class Procedural_Gen_Properties(bpy.types.PropertyGroup):
    def LoadActivePanel(self,context):
        data = DataSingleton()
        
        if not data.ActiveOperation and  len( data.Operations)>0:
            data.ActiveOperation = data.Operations[0]

        L = list(filter(lambda x: x[0] == self.OperationsType , data.OperationsTypes))
        
        if(len(L)==0):
            return
        
        OpId = L[0][4]

        data.ActiveOperation = data.Operations[OpId]
        data.IsInitialized = True
        data.PrefOpType = self.OperationsType  
    def CreateOperations(self,context):
        JDLCImp = JDLCImporter()

        JDLCImp.Make(context)
        JDLCImp.SetOpTypes()
        self.LoadActivePanel(context)
    def ChangeOperation(self, context):
        data = DataSingleton()

        data.ActiveOperation.ExitOP(data.PrefOpType)
        
        JDLCImp = JDLCImporter()
        JDLCImp.LoadPresets(context)

        OpId = next(filter(lambda x: x[0] == self.OperationsType , data.OperationsTypes))[4]
        data.ActiveOperation = data.Operations[OpId]
        data.PrefOpType = self.OperationsType
    def enumItems(scene, context):
        return DataSingleton().OperationsTypes

#Global props
    OperationsType : bpy.props.EnumProperty(name="Generation Type",items=enumItems,update = ChangeOperation)
    
    MaxInputVertices : bpy.props.IntProperty(name="Max Input Verts",default= 10000000)

    CurrentInputVertices : bpy.props.IntProperty(name="Current Input Verts",default= 0)

    ActiveObj: bpy.props.PointerProperty(type=bpy.types.Object,name='Active Obj',
                                        description='Active Obj')

    PropChangesInProgress : bpy.props.BoolProperty(name="",description = "PropChangesInProgress", default= False)

    
    