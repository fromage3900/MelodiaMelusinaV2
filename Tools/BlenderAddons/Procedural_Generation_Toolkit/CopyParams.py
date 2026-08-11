import bpy

from .ProceduralGenProperties import DataSingleton
import zlib, base64

def CopyParam(outs,p,ExProps):
    if not p.VarName == "":
        PropProps = ExProps.bl_rna.properties[p.VarName]
        if(str(type(PropProps)) != "<class 'bpy.types.PointerProperty'>") and  p.Share:
            PropProps = ExProps.bl_rna.properties[p.VarName]
            if hasattr(PropProps, 'array_length') and PropProps.array_length>1:
                VecotrProp = getattr(ExProps,p.VarName)
                TmpOut = "("
                for i in range(PropProps.array_length):
                    TmpOut = TmpOut + str(VecotrProp[i])+","
                outs = outs + p.VarName+ "*" + TmpOut[0:-1] + ")"+ "\n"
            else:
                outs = outs + p.VarName + "*" + str(getattr(ExProps,p.VarName)) + "\n"
    for bp in p.BoolOnProps:
        outs = CopyParam(outs,bp,ExProps)
    for bp in p.BoolOffProps:
        outs = CopyParam(outs,bp,ExProps)
    return outs
    
def CopySimpleParam(outs,p):
    input = None
    for i in p.defaultHost:
        if p.identifier == i.identifier:
            input = i
            break
    PropProps = input.bl_rna.properties["default_value"]
    if(str(type(PropProps)) != "<class 'bpy.types.PointerProperty'>"):
        if hasattr(PropProps, 'array_length') and PropProps.array_length>1:
            VecotrProp = getattr(p.hostObj,p.paramName)
            TmpOut = "("
            for i in range(PropProps.array_length):
                TmpOut = TmpOut + str(VecotrProp[i])+","
            outs = outs+ p.paramName+ "*" + TmpOut[0:-1] + ")"+ "\n"
        else:
            outs = outs + p.paramName + "*" + str(getattr(p.hostObj,p.paramName)) + "\n"
    return outs

def CopyParams(context):
    scene = context.scene
    props = scene.Procedural_Gen_Props
    ExProps = getattr(scene,props.OperationsType)
    data = DataSingleton()
    outs = ""
    for a in data.ActiveOperation.GetActiveActions():
        outs = outs + a.enabeled + "*" + str(getattr(ExProps,a.enabeled)) + "\n"
        for p in a.params:
            outs = CopyParam(outs,p,ExProps)
    for v in data.ActiveOperation.GetActiveViewers():
        i=0
        for k in v.simpleParams.keys():
            outs = outs +"V"+ "*"+ v.UniqueName+ "*"+ str(i) + "\n"
            for p in v.simpleParams[k]:
                outs = CopySimpleParam(outs,p)
            i += 1
    return base64.b64encode(zlib.compress(outs.encode()))

class OBJECT_OT_Copy_Params(bpy.types.Operator):
    bl_idname = "object.procedural_gen_copy_parameters"
    bl_label = "Copy Seed"
    bl_description = "Copy The Seed Values To Share"

    def execute(self,context):
        t = CopyParams(context)

        bpy.context.window_manager.clipboard = t
        return {'FINISHED'}