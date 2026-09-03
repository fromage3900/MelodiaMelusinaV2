from .ProceduralGenProperties import DataSingleton

import bpy

class ACTION_OT_executorpgt(bpy.types.Operator):
    bl_idname = "action.executorpgt"
    bl_label = "Execute"
    bl_description = "Execute Action"

    ActionName : bpy.props.StringProperty(default="")
    #@classmethod
    #def poll(cls, context):
    #    obj = context.object
    #    scene = context.scene
    #    props = scene.Procedural_Gen_Props
##
    #    ExProps = getattr(scene,props.OperationsType)
##
    #    data = DataSingleton()
    #    for action in data.ActiveOperation.actions:
    #        if action.UIName == cls.ActionName:
    #            if not action.needImputMesh:
    #                return True
##
    #            if(action.MaxVert<props.CurrentInputVertices and action.MaxVert != 0):
    #                return False
##
    #            if obj is not None:
    #                if obj.mode == "OBJECT":
    #                    return True
##
    #    return False
    def execute(self, context):
        data = DataSingleton()
        for action in data.ActiveOperation.GetActiveActions():
            if action.UIName == self.ActionName:
                action.Execute(context)
        return {'FINISHED'}