import bpy
import traceback
from uuid import uuid4
from typing import List
from .common import ToolsPackageBase
from ..utils import ensure_material_by_name, NodeTreeUtil


class MaterialTools(ToolsPackageBase):
    """
    Material tools for Blender.
    """

    def set_material(object_name: str, material_name: str = None, color: List[float] = None) -> dict:
        """
        Set or create a material for an object.

        Args:
        - object_name: Name of the object to apply the material to
        - material_name: Optional name of the material to use or create
        - color: Optional [R, G, B] color values (0.0-1.0)
        """
        try:
            # Get the object
            obj = bpy.data.objects.get(object_name)
            if not obj:
                raise ValueError(f"Object not found: {object_name}")

            material_name = material_name or f"{object_name}_{uuid4().hex}"

            # Make sure object can accept materials
            if not hasattr(obj, "data") or not hasattr(obj.data, "materials"):
                raise ValueError(f"Object {object_name} cannot accept materials")

            mat = ensure_material_by_name(obj, material_name)
            # Get or create Principled BSDF
            principled = mat.node_tree.nodes.get("Principled BSDF")
            if not principled:
                principled = mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
                principled.name = "Principled BSDF"
                # Get or create Material Output
                output = NodeTreeUtil.find_node_by_type(mat.node_tree, "OUTPUT_MATERIAL")
                if not output:
                    output = mat.node_tree.nodes.new("ShaderNodeOutputMaterial")
                    output.name = "Material Output"
                mat.node_tree.links.new(principled.outputs[0], output.inputs[0])
            color = color or (1, 1, 1, 1)
            color = color if len(color) == 4 else (*color, 1.0)
            # Set color if provided
            if color and len(color) >= 3:
                principled.inputs["Base Color"].default_value = color
                print(f"Set material color to {color}")

            # Assign material to object if not already assigned
            if not obj.data.materials:
                obj.data.materials.append(mat)
            else:
                # Only modify first material slot
                obj.data.materials[0] = mat
            print(f"Assigned material {mat.name} to object {object_name}")
            return {"status": "success", "object": object_name, "material": mat.name, "color": color if color else None}
        except Exception as e:
            print(f"Error in set_material: {str(e)}")
            traceback.print_exc()
            return {"status": "error", "message": str(e), "object": object_name, "material": material_name if "material_name" in locals() else None}
