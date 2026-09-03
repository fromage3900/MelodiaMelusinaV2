import bpy

class OBJECT_OT_Duplicate_And_Apply_All_Mods_Op(bpy.types.Operator):
    bl_idname = "object.duplicate_and_apply_all_mods"
    bl_label = "Apply All Mods And Duplicate"
    bl_description = "Apply all modifiers of selected object"

    @classmethod
    def poll(cls, context):
        obj = context.object

        if obj is not None:
            if obj.mode == "OBJECT":
                return True

        return False
    
    def execute(self, context):
        
        for obj in bpy.context.selected_objects:

                bpy.context.view_layer.objects.active = obj

                ob = obj #getting the object we want.
                dg = bpy.context.evaluated_depsgraph_get() #getting the dependency graph
        
                ob = ob.evaluated_get(dg) #this gives us the evaluated version of the object. Aka with all modifiers and deformations applied.
                me = ob.to_mesh() #turn it into the mesh data block we want.

                new_object = bpy.data.objects.new(ob.name+'Copy',me.copy())
                new_object.location = ob.location
                new_object.rotation_euler = ob.rotation_euler
                new_object.scale = ob.scale

                new_object.data.materials.clear()

                bpy.context.scene.collection.objects.link(new_object)
                bpy.ops.object.select_all(action='DESELECT')
                new_object.select_set(True)
                bpy.context.view_layer.objects.active = new_object
                for m in ob.data.materials:
                    new_object.data.materials.append(m.copy())
        bpy.context.view_layer.update()
        return {'FINISHED'}

    