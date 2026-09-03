import bpy

from .ProceduralGenProperties import DataSingleton
from .ProceduralGenProperties import Procedural_Gen_Properties

import random

class OBJECT_OT_Randomize_Params(bpy.types.Operator):
    bl_idname = "object.procedural_gen_randomize_parameters"
    bl_label = "Randomize All Parameters"
    bl_description = "Randomize All Parameters"

    def execute(self,context):
        scene = context.scene
        props = scene.Procedural_Gen_Props

        ExProps = getattr(scene,props.OperationsType)

        props.PropChangesInProgress = True
        data = DataSingleton()
        for action in data.ActiveOperation.GetActiveActions():
            for p in action.params:
                self.Randomize(ExProps, p)
        for viewer in data.ActiveOperation.GetActiveViewers():
            for p in viewer.GetAllParams():
                self.RandomizeSimple(p)
        props.PropChangesInProgress = False
        data.ActiveOperation.AutoUpdate(context,props)

        return {'FINISHED'}
    def RandomizeSimple(self,p):
        if p.defaultHost:
            input = None
            for i in p.defaultHost:
                if p.identifier == i.identifier:
                    input = i
                    break

            PropProps = input.bl_rna.properties["default_value"]
            soft_min = 0
            soft_max = 1
            if hasattr(input,"min_value"):
                soft_min = getattr(input,"min_value")
                soft_max = getattr(input,"max_value")

            if(str(type(PropProps)) == "<class 'bpy.types.FloatProperty'>"):
                if PropProps.array_length>1:
                    List = []
                    for i in range(PropProps.array_length):
                        List.append(random.uniform(soft_min, soft_max))
                    setattr(p.hostObj,p.paramName,List)
                else:
                    setattr(p.hostObj,p.paramName,random.uniform(soft_min, soft_max))
            elif str(type(PropProps)) == "<class 'bpy.types.IntProperty'>":
                setattr(p.hostObj,p.paramName,random.randint(soft_min, soft_max))
            elif str(type(PropProps)) == "<class 'bpy.types.BoolProperty'>":
                setattr(p.hostObj,p.paramName,random.getrandbits(1))
            elif str(type(PropProps)) == "<class 'bpy.types.EnumProperty'>":
                setattr(p.hostObj,p.paramName,PropProps.enum_items[random.randrange(0,len(PropProps.enum_items))].identifier)

    def Randomize(self, ExProps, p):
        if p.ShowInUI and p.Randomize and not p.VarName == "":
            PropProps = ExProps.bl_rna.properties[p.VarName]
            if(str(type(PropProps)) == "<class 'bpy.types.FloatProperty'>"):
                if PropProps.array_length>1:
                    List = []
                    for i in range(PropProps.array_length):
                        List.append(random.uniform(PropProps.soft_min, PropProps.soft_max))
                    setattr(ExProps,p.VarName,List)
                else:
                    setattr(ExProps,p.VarName,random.uniform(PropProps.soft_min, PropProps.soft_max))
            elif str(type(PropProps)) == "<class 'bpy.types.IntProperty'>":
                setattr(ExProps,p.VarName,random.randint(PropProps.soft_min, PropProps.soft_max))
            elif str(type(PropProps)) == "<class 'bpy.types.BoolProperty'>":
                setattr(ExProps,p.VarName,random.getrandbits(1))
            elif str(type(PropProps)) == "<class 'bpy.types.EnumProperty'>":
                setattr(ExProps,p.VarName,PropProps.enum_items[random.randrange(0,len(PropProps.enum_items))].identifier)
        for bp in p.BoolOnProps:
            self.Randomize(ExProps,bp)
        for bp in p.BoolOffProps:
            self.Randomize(ExProps,bp)