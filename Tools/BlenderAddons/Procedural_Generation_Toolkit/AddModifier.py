import bpy
from . Action import Action

class AddModifier(Action):
    def __init__(self, modName, modType, UIName,enabeled, liveUpdate = False, liveUpdateParam=""):
        self.modName = modName
        self.modType = modType
        self.UIName = UIName
        self.params = []
        self.enabeled = enabeled
        self.liveUpdate = liveUpdate
        self.liveUpdateParam = liveUpdateParam

    def Execute(self,context):
        if context.object is None or context.object.mode != "OBJECT":
            bpy.ops.wm.popup('INVOKE_DEFAULT',ErrMsg =  self.UIName + " Has Invalid Input Object!",Sol="Select a mesh")
            return False
        scene = context.scene
        props = scene.Procedural_Gen_Props

        ExProps = getattr(scene,props.OperationsType)
        
        obj = bpy.context.active_object
        mod = obj.modifiers.get(self.modName) if obj.modifiers.get(self.modName) != None else obj.modifiers.new(name=self.modName, type=self.modType)
        mod.show_viewport = getattr(ExProps,self.enabeled)
        mod.show_render = getattr(ExProps,self.enabeled)
        mod.show_in_editmode = False
        
        for param in self.params:
            if not param.useArr:
                setattr(mod,param.paramName,getattr(ExProps,param.VarName))
            else:
                arr = getattr(mod,param.paramName)
                arr[param.arrIndex] = getattr(ExProps,param.VarName)
                setattr(mod,param.paramName,arr)
        return True