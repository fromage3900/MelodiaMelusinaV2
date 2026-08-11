import bpy

def InnerDisplayProp(row,ExProps, box3, p):
    if p.Column:
        row = box3.column()
        if p.CustomUICode:
            p.UILambda(row,ExProps,p)
        else:                         
            row.prop(ExProps,  p.VarName,slider=p.slider,expand=p.expand,toggle=p.toggle)
    elif p.ShowInUI:
        if p.UseLable:
            row = box3.row()                           
            row.label(text=p.Lable)
        if not p.SkipNewRow:
            row = box3.row()
        if p.CustomUICode:
            p.UILambda(row,ExProps,p) 
        else:                          
            row.prop(ExProps,  p.VarName,slider=p.slider,expand=p.expand,toggle=p.toggle)
    return row
def DisplayProp(row,ExProps, box3, p):
    if p.UseBoolDropdown:
        row = InnerDisplayProp(row,ExProps, box3, p)
        if getattr(ExProps,p.VarName):
            for pb in p.BoolOnProps:
                row = DisplayProp(row,ExProps, box3, pb)
        else:
            for pb in p.BoolOffProps:
                row = DisplayProp(row,ExProps, box3, pb)
    else:
        row = InnerDisplayProp(row,ExProps, box3, p)
    return row


class Action:
    def __init__(self,UIName,enabeled,needInputMesh = True, liveUpdate = False, liveUpdateParam="",  maxVert = 0,CanExeLambda = None):
        self.params = []
        self.actions = []
        self.UIName = UIName
        self.maxVert = maxVert
        self.needInputMesh = needInputMesh
        self.enabeled = enabeled
        self.liveUpdate = liveUpdate
        self.liveUpdateParam = liveUpdateParam
        self.CanExeLambda = CanExeLambda

    def Draw(self, ExProps, box2):
        a = self
        box3 = box2.box()
        row = box3.row()
        row.label(text=a.UIName)

        if a.liveUpdate:
            row.prop(ExProps, a.liveUpdateParam)

        row.prop(ExProps,  a.enabeled)

        if not getattr(ExProps,a.enabeled):
            return

        for p in a.params:
            row = DisplayProp(row,ExProps, box3, p)

        row = box3.row()
        op = row.operator('action.executorpgt')
        op.ActionName = a.UIName

    def Update(self):
        return

    def AddParam(self, param):
        self.params.append(param)

    def GetParamByName(self, name):
        return next(filter(lambda x :  x[0] == name, self.params)[1],None)

    def AddAction(self,action):
        self.actions.append(action)

    def Execute(self,context, liveUpdate = False):
        if self.CanExeLambda:
            CanExe,errString,sol = self.CanExeLambda(context)
            if not CanExe:
                bpy.ops.wm.popup('INVOKE_DEFAULT',ErrMsg = errString,Sol=sol)
                return False
        if self.needInputMesh:
            if context.object is not None:
                if  context.object.mode == "OBJECT":
                    for action in self.actions:
                        action(self,context,liveUpdate)
                    return True
        else:
            for action in self.actions:
                action(self,context,liveUpdate)
            return True
        bpy.ops.wm.popup('INVOKE_DEFAULT',ErrMsg = self.UIName + " Has Invalid Input Object!",Sol="Select a mesh")
        return False
