import bpy

from .ProceduralGenProperties import DataSingleton

class OBJECT_OT_Reset_Params(bpy.types.Operator):
    bl_idname = "object.procedural_gen_reset_parameters"
    bl_label = "Reset All Parameters"
    bl_description = "Resets All Parameters to default values"

    def execute(self,context):
        scene = context.scene
        props = scene.Procedural_Gen_Props

        ExProps = getattr(scene,props.OperationsType)

        data = DataSingleton()

        for actions in data.ActiveOperation.GetActiveActions():
            ExProps.property_unset(actions.enabeled)
            for p in actions.params:
                self.resetParam(ExProps, p)

        for viewer in data.ActiveOperation.GetActiveViewers():
            for p in viewer.GetAllParams():
                if p.identifier:
                    input = None
                    for i in p.defaultHost:
                        if p.identifier == i.identifier:
                            input = i
                            break
                    defVal = getattr(input,"default_value")
                    setattr(p.hostObj,p.paramName,defVal)
                else:
                    p.hostObj.property_unset(p.paramName)

        data.ActiveOperation.AutoUpdate(context,props)

        return {'FINISHED'}

    def resetParam(self, ExProps, p):
        if not p.VarName == "" and p.Reset:
            ExProps.property_unset(p.VarName)
        for bp in p.BoolOnProps:
            self.resetParam(ExProps,bp)
        for bp in p.BoolOffProps:
            self.resetParam(ExProps,bp)