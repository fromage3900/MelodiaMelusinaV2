
from .Action import Action
from .DropDown import DropDown
from .Viewer import Viewer

import bpy

class Operation():
    def __init__(self, OperationName,InputObjNeeded=True, maxVert = 0, CanExeLambda = None,ExitLambda=None):
        self.name = OperationName
        self.MaxVert = maxVert
        self.InputObjNeeded = InputObjNeeded
        self.Elements = []
        self.AutoUpdateBind = []
        self.CanExeLambda = CanExeLambda
        self.ExitLambda = ExitLambda

    def BindToAutoUpdate(self,bind):
        self.AutoUpdateBind.append(bind)

    def AddAction(self,action):
        self.Elements.append(action)

    def AddDropDown(self,d):
        self.Elements.append(d)

    def AddViewer(self,v):
        self.Elements.append(v)

    def GetActiveViewers(self):
        viewers = []
        for e in self.Elements:
            if isinstance(e,Viewer):
                viewers.append(e)
            if isinstance(e,DropDown):
                viewers = viewers + e.GetActiveViewers()
        return viewers

    def ExitOP(self,prefOpType):
        if self.ExitLambda:
            self.ExitLambda(prefOpType)

    def GetActiveActions(self):
        actions = []
        for e in self.Elements:
            if isinstance(e,Action):
                actions.append(e)
            if isinstance(e,DropDown):
                actions = actions + e.GetActiveActions()
        return actions

    def Execute(self,context):
        if self.CanExeLambda:
            CanExe,errString,sol = self.CanExeLambda(context)
            if not CanExe:
                bpy.ops.wm.popup('INVOKE_DEFAULT',ErrMsg = errString,Sol=sol)
                return False

        scene = context.scene
        props = scene.Procedural_Gen_Props

        ExProps = getattr(scene,props.OperationsType)

        for action in self.GetActiveActions():
            if not getattr(ExProps,action.enabeled):
                continue
            if not action.Execute(context):
                return False
        return True

    def AutoUpdate(self,context,Props):
        for AUB in self.AutoUpdateBind:
            AUB(context)
        scene = context.scene
        
        ExProps = getattr(scene,Props.OperationsType)

        for action in self.GetActiveActions():
            if action.liveUpdate and getattr(ExProps,action.liveUpdateParam):
                if not action.Execute(context,True):
                    return False
        return True