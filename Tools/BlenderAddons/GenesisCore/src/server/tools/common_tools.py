import bpy
import traceback
from .common import ToolsPackageBase


class CommonTools(ToolsPackageBase):
    """
    Common tools for Blender.
    """

    def get_simple_info() -> dict:
        """Get basic Blender information"""
        return {"blender_version": bpy.app.version, "scene_name": bpy.context.scene.name, "object_count": len(bpy.context.scene.objects)}

    def get_scene_info() -> dict:
        """Get information about the current Blender scene"""
        try:
            print("Getting scene info...")
            # Simplify the scene info to reduce data size
            scene_info = {
                "name": bpy.context.scene.name,
                "object_count": len(bpy.context.scene.objects),
                "objects": [],
                "materials_count": len(bpy.data.materials),
            }

            # Collect minimal object information (limit to first 10 objects)
            for obj in bpy.context.scene.objects:
                obj_info = {
                    "name": obj.name,
                    "type": obj.type,
                    "location": tuple(obj.location),
                }
                scene_info["objects"].append(obj_info)

            print(f"Scene info collected: {len(scene_info['objects'])} objects")
            return scene_info
        except Exception as e:
            print(f"Error in get_scene_info: {str(e)}")
            traceback.print_exc()
            return {"error": str(e)}

    def get_active_object_name() -> dict:
        """
        Get the name of active object in the Blender scene.
        """
        obj = bpy.context.view_layer.objects.active
        if not obj:
            raise ValueError("No active object found")
        return {"name": obj.name}

    def get_selected_objects_names() -> dict:
        """
        Get the names of selected objects in the Blender scene.
        """
        return {"names": [obj.name for obj in bpy.context.selected_objects]}

    def execute_blender_code(code: str) -> dict:
        """
        Execute arbitrary Blender's Python Api code in Blender.

        Args:
        - code: The Python code to execute
        """
        # This is powerful but potentially dangerous - use with caution
        try:
            # Create a local namespace for execution
            namespace = {"bpy": bpy}
            exec(code, namespace)
            return {"executed": True}
        except Exception as e:
            raise Exception(f"Code execution error: {str(e)}")
