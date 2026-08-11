import bpy
from .Action import Action
from .SimpleParam import SimpleParam
from .JDLCImporter import JDLCImporter

import os

class AddGeoNode(Action):
    def __init__(self, GeoModName, GeoNodeName, UIName,enabeled, liveUpdate = False, liveUpdateParam="", stack = False, AddEmptyMesh = False):
        self.GeoModName = GeoModName
        self.GeoNodeName = GeoNodeName
        self.params = []
        self.UIName = UIName   
        self.enabeled = enabeled
        self.liveUpdate = liveUpdate
        self.liveUpdateParam = liveUpdateParam
        self.Stack = stack
        self.AddEmptyMesh = AddEmptyMesh

    def Execute(self,context):
        if self.AddEmptyMesh:
            bpy.ops.mesh.primitive_plane_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
            
        if context.object is None or context.object.mode != "OBJECT":
            bpy.ops.wm.popup('INVOKE_DEFAULT',ErrMsg = self.UIName + " Has Invalid Input Object!",Sol="Select a mesh")
            return False
        bpy.context.view_layer.update()

        scene = context.scene
        props = scene.Procedural_Gen_Props

        ExProps = getattr(scene,props.OperationsType)
        obj = bpy.context.active_object

        if bpy.data.node_groups.get(self.GeoNodeName) == None:
                JdclImp = JDLCImporter()
                file_path = JdclImp.GetActiveOpPath()+"Resources.blend"
                inner_path = 'NodeTree'
                object_name = self.GeoNodeName
 
                bpy.ops.wm.append(filepath=os.path.join(file_path, inner_path, object_name), directory=os.path.join(file_path, inner_path), filename=object_name)
        if self.Stack:
            mod = obj.modifiers.new(name=self.GeoModName, type="NODES")
        else:
            mod = obj.modifiers.get(self.GeoModName) if obj.modifiers.get(self.GeoModName) != None else obj.modifiers.new(name=self.GeoModName, type="NODES")
        mod.show_viewport = getattr(ExProps,self.enabeled)
        mod.show_render = getattr(ExProps,self.enabeled)
        mod.show_in_editmode = False

        if not mod.node_group:
            mod.node_group = bpy.data.node_groups.get(self.GeoNodeName)
        for i in mod.node_group.interface.items_tree:
            if i.item_type == 'SOCKET':
                if i.in_out == 'INPUT':
                    if i.name == "Geometry":
                        continue
                    elif i.name == "Material":
                        if len(obj.data.materials)>0:
                            mod.__setattr__('["'+i.identifier+'"]',obj.data.materials[0])
                        continue

        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        return True