import bpy
from .Action import Action
from .SimpleParam import SimpleParam
from .JDLCImporter import JDLCImporter

import os
class AddMat(Action):
    def __init__(self, MatName, UIName,enabeled,IDParamName,LinkedGeoNodeName=None):
        self.MatName = MatName
        self.params = []
        self.UIName = UIName   
        self.enabeled = enabeled
        self.liveUpdate = False
        self.liveUpdateParam =""
        self.IDParamName = IDParamName
        self.LinkedGeoNodeName = LinkedGeoNodeName

    def findMatWithMatNameName(self,obj,ID):
        if hasattr(obj.data ,"materials") and len(obj.data.materials)>ID:
            m = obj.data.materials[ID]
            if m and self.MatName in m.name:
                return m.name
                
    def Execute(self,context):
        if context.object is None or context.object.mode != "OBJECT":
            bpy.ops.wm.popup('INVOKE_DEFAULT',ErrMsg =  self.UIName + " Has Invalid Input Object!",Sol="Select a mesh")
            return False
        scene = context.scene
        props = scene.Procedural_Gen_Props

        ExProps = getattr(scene,props.OperationsType)

        obj = bpy.context.active_object

        if bpy.data.materials.get(self.MatName) == None:
            JdclImp = JDLCImporter()
            file_path = JdclImp.GetActiveOpPath()+"Resources.blend"
            inner_path = 'Material'
            object_name = self.MatName

            bpy.ops.wm.append(filepath=os.path.join(file_path, inner_path, object_name), directory=os.path.join(file_path, inner_path), filename=object_name)
        
        matName = self.findMatWithMatNameName(obj,getattr(ExProps,self.IDParamName))

        if not matName:
            ID = getattr(ExProps,self.IDParamName)

            newMat = bpy.data.materials.get(self.MatName).copy()

            if len(obj.material_slots) <= ID:
                # If there are not enough slots, create a new one and assign the material
                obj.data.materials.append(newMat)
                setattr(ExProps, self.IDParamName, len(obj.data.materials) - 1)
            else:
                # Replace the material in the existing slot
                obj.material_slots[ID].material = newMat
    
            matName = newMat.name

        obj.select_set(True)
        if self.LinkedGeoNodeName:
            GeoNodes = []

            if obj and hasattr(obj ,"modifiers"):
                for m in obj.modifiers:
                    if m and self.LinkedGeoNodeName in m.name:
                        GeoNodes.append(m)

            for mod in GeoNodes:
                for i in mod.node_group.interface.items_tree:
                    if i.item_type == 'SOCKET':
                        if i.in_out == 'INPUT':
                            if i.name == "Geometry":
                                continue
                            elif i.name == "Material":
                                mod.__setattr__('["'+i.identifier+'"]',newMat)
        
        bpy.context.view_layer.objects.active = obj
        return True