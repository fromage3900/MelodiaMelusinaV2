import bpy

from .ProceduralGenProperties import DataSingleton

class OBJECT_OT_Execute_OP(bpy.types.Operator):
    bl_idname = "object.operation_executor"
    bl_label = "Execute All Actions"
    bl_description = "Execute Operation"

    @classmethod
    def poll(cls, context):
        obj = context.object
        scene = context.scene
        props = scene.Procedural_Gen_Props

        data = DataSingleton()

        if( not data.ActiveOperation.CanExeLambda(context) if (data.ActiveOperation.CanExeLambda) else data.ActiveOperation.MaxVert>props.CurrentInputVertices and data.ActiveOperation.MaxVert != 0):
            return False

        if not data.ActiveOperation.InputObjNeeded:
            return True

        if obj is not None:
            if obj.mode == "OBJECT":
                return True

        return False

    def execute(self,context):
        data = DataSingleton()

        scene = context.scene
        props = scene.Procedural_Gen_Props

        if( not data.ActiveOperation.CanExeLambda(context) if (data.ActiveOperation.CanExeLambda) else data.ActiveOperation.MaxVert>props.CurrentInputVertices and data.ActiveOperation.MaxVert != 0):
            return {'FINISHED'}
            
        if data.ActiveOperation != None:
            data.ActiveOperation.Execute(context)
        return {'FINISHED'}