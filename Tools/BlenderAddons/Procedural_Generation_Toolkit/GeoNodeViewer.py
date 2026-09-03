
import bpy
from .SimpleParam import SimpleParam
from .Viewer import Viewer

class GeoNodeViewer(Viewer):
    def __init__(self, GeoModName, GeoNodeName, UIName,UniqueName=None):
        self.simpleParams = {}
        if UniqueName:
            self.UniqueName = UniqueName
        else:
            self.UniqueName = GeoModName
        self.GeoModName = GeoModName
        self.GeoNodeName = GeoNodeName
        self.UIName = UIName
        return

    def findGeoNodesWithMatName(self,obj):
        GeoNodes = []
    
        if obj and hasattr(obj ,"modifiers"):
            for m in obj.modifiers:
                if m and self.GeoModName in m.name:
                    GeoNodes.append(m.name)
        return GeoNodes

    def Update(self):
        obj = bpy.context.active_object

        self.simpleParams = {}
        modNames = self.findGeoNodesWithMatName(obj)
        for modName in modNames:
            mod = obj.modifiers.get(modName)
            self.simpleParams[modName] = []
            for i in mod.node_group.interface.items_tree:
                if i.item_type == 'SOCKET':
                    if i.in_out == 'INPUT':
                        if i.name == "Geometry" or i.name == "Material":
                            continue
                        self.simpleParams[modName].append(SimpleParam(mod,'["'+i.identifier+'"]',i.name,i.identifier,mod.node_group.interface.items_tree))

    def Draw(self, ExProps, box2):
        if len(self.simpleParams.keys()) == 0:
            return
        box3 = box2.box()
        row = box3.row()
        row.label(text=self.UIName)
        for k in self.simpleParams.keys():
            box4 = box3.box()
            row = box4.row()
            row.label(text="Name: "+k)

            for p in self.simpleParams[k]:
                if hasattr(p.hostObj, p.paramName):
                    row = box4.column()
                    row.prop(p.hostObj, p.paramName, text=p.UIName)
