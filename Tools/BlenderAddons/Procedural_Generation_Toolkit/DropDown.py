import bpy

from .Action import Action
from .Viewer import Viewer

class DropDown:
    def __init__(self,UIName,EnumItemsName):
        self.elements = {}
        self.UIName = UIName
        self.EnumItemsName = EnumItemsName

    def AddElements(self,enumName,Actions):
        self.elements[enumName] = Actions

    def Update(self):
        scene = bpy.context.scene
        props = scene.Procedural_Gen_Props

        ExProps = getattr(scene,props.OperationsType)

        elements = self.elements[getattr(ExProps,self.EnumItemsName)]

        for e in elements:
            e.Update()
        return
    def Draw(self, ExProps, box2):
        e=self
        box3 = box2.box()
        row = box3.row()
        row.label(text=e.UIName)
        row = box3.row()
        row.template_icon_view(ExProps, e.EnumItemsName, show_labels=True, scale=8,scale_popup=6)
        elements = e.GetActiveElements()
        for a in elements:
            a.Draw(ExProps, box2)
    def GetActiveElements(self):
        scene = bpy.context.scene
        props = scene.Procedural_Gen_Props

        ExProps = getattr(scene,props.OperationsType)

        return self.elements[getattr(ExProps,self.EnumItemsName)]
    def GetActiveActions(self):
        scene = bpy.context.scene
        props = scene.Procedural_Gen_Props

        ExProps = getattr(scene,props.OperationsType)

        elements = self.elements[getattr(ExProps,self.EnumItemsName)]
        actions = []

        for e in elements:
            if isinstance(e,Action):
                actions.append(e)
            if isinstance(e,DropDown):
                actions = actions + e.GetActiveActions()

        return actions

    def GetActiveViewers(self):
        scene = bpy.context.scene
        props = scene.Procedural_Gen_Props

        ExProps = getattr(scene,props.OperationsType)

        elements = self.elements[getattr(ExProps,self.EnumItemsName)]
        viewers = []

        for e in elements:
            if isinstance(e,Viewer):
                viewers.append(e)
            if isinstance(e,DropDown):
                viewers = viewers + e.GetActiveViewers()

        return viewers