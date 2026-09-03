
import bpy
from .SimpleParam import SimpleParam
from .Viewer import Viewer

class MatViewer(Viewer):
    def __init__(self, MatName, UIName,UniqueName = None):
        self.simpleParams = {}
        self.IDs = {}
        if UniqueName:
            self.UniqueName = UniqueName
        else:
            self.UniqueName = MatName
        self.MatName = MatName
        self.UIName = UIName

    def findMatsWithMatName(self,obj):
        mats = []
    
        if obj and hasattr(obj.data ,"materials"):
            i = 0
            for m in obj.data.materials:
                if m and self.MatName in m.name:
                    mats.append(m.name)
                    self.IDs[m.name] = i
                i += 1
        return mats

    def Update(self):
        obj = bpy.context.active_object
        self.simpleParams = {}

        scene = bpy.context.scene
        props = scene.Procedural_Gen_Props

        ExProps = getattr(scene,props.OperationsType)

        matNames = self.findMatsWithMatName(obj)

        for matName in matNames:
            material = obj.data.materials.get(matName)
            if material is not None and material.node_tree:
                group = material.node_tree.nodes.get('Group')
                if group is not None:
                    self.simpleParams[matName] = []
                    for socket in group.inputs:  # Iterate over input sockets of the group
                        if socket.type in ['VALUE', 'RGBA', 'VECTOR']:                            
                            # Create a SimpleParam object with the necessary attributes
                            # Here, you might need to adjust the attributes you pass based on what SimpleParam expects
                            self.simpleParams[matName].append(SimpleParam(socket, "default_value", socket.name, socket.identifier, group.node_tree.interface.items_tree))
                            
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
            row = box4.row()
            row.label(text="Mat ID: "+str(self.IDs[k]))
            for p in self.simpleParams[k]:
                if hasattr(p.hostObj, p.paramName):
                    row = box4.column()
                    row.prop(p.hostObj, p.paramName, text=p.UIName)