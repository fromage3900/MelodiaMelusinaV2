import bpy
from mathutils import Vector
from typing import List
from .common import ToolsPackageBase


class ObjectTools(ToolsPackageBase):
    """
    Object tools for the Blender scene.
    """

    def get_object_info(object_name: str) -> dict:
        """
        Get detailed information about a specific object in the Blender scene.

        Args:
        - object_name: The name of the object to get information about
        """
        obj = bpy.data.objects.get(object_name)
        if not obj:
            raise ValueError(f"Object not found: {object_name}")

        # Basic object info
        obj_info = {
            "name": obj.name,
            "type": obj.type,
            "location": tuple(obj.location),
            "rotation": tuple(obj.rotation_euler),
            "scale": tuple(obj.scale),
            "visible": obj.visible_get(),
            "bound_box": [tuple(obj.matrix_world @ Vector(v)) for v in obj.bound_box],
            "materials": [],
        }

        obj_info["materials"] = [slot.material.name for slot in obj.material_slots if slot.material]

        # Add mesh data if applicable
        if obj.type == "MESH" and obj.data:
            mesh = obj.data
            obj_info["mesh"] = {
                "vertices": len(mesh.vertices),
                "edges": len(mesh.edges),
                "polygons": len(mesh.polygons),
            }

        return obj_info

    def create_object(
        entity_type: str = "CUBE",
        name: str = "New Object",
        location: List[float] = (0, 0, 0),
        rotation: List[float] = (0, 0, 0),
        scale: List[float] = (1, 1, 1),
        align: str = "WORLD",
        major_segments: int = 48,
        minor_segments: int = 12,
        mode: str = "MAJOR_MINOR",
        major_radius: float = 1.0,
        minor_radius: float = 0.25,
        abso_major_rad: float = 1.25,
        abso_minor_rad: float = 0.75,
        generate_uvs: bool = True,
    ) -> dict:
        """
        Create a new object in the Blender scene.

        Args:
        - entity_type: Entity type to create (CUBE, SPHERE, CYLINDER, PLANE, CONE, TORUS, EMPTY, CAMERA, LIGHT)
        - name: Optional name for the object
        - location: Optional [x, y, z] location coordinates
        - rotation: Optional [x, y, z] rotation in radians
        - scale: Optional [x, y, z] scale factors (not used for TORUS)
        - align: How to align the torus ('WORLD', 'VIEW', or 'CURSOR')
        - major_segments: Number of segments for the main ring
        - minor_segments: Number of segments for the cross-section
        - mode: Dimension mode ('MAJOR_MINOR' or 'EXT_INT')
        - major_radius: Radius from the origin to the center of the cross sections
        - minor_radius: Radius of the torus' cross section
        - abso_major_rad: Total exterior radius of the torus
        - abso_minor_rad: Total interior radius of the torus
        - generate_uvs: Whether to generate a default UV map

        Returns:
        A message indicating the created object name.
        """
        old_objects = set(bpy.data.objects)
        # Deselect all objects
        bpy.ops.object.select_all(action="DESELECT")
        if entity_type == "CUBE":
            bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation, scale=scale)
        elif entity_type == "SPHERE":
            bpy.ops.mesh.primitive_uv_sphere_add(location=location, rotation=rotation, scale=scale)
        elif entity_type == "CYLINDER":
            bpy.ops.mesh.primitive_cylinder_add(location=location, rotation=rotation, scale=scale)
        elif entity_type == "PLANE":
            bpy.ops.mesh.primitive_plane_add(location=location, rotation=rotation, scale=scale)
        elif entity_type == "CONE":
            bpy.ops.mesh.primitive_cone_add(location=location, rotation=rotation, scale=scale)
        elif entity_type == "TORUS":
            bpy.ops.mesh.primitive_torus_add(
                align=align,
                location=location,
                rotation=rotation,
                major_segments=major_segments,
                minor_segments=minor_segments,
                mode=mode,
                major_radius=major_radius,
                minor_radius=minor_radius,
                abso_major_rad=abso_major_rad,
                abso_minor_rad=abso_minor_rad,
                generate_uvs=generate_uvs,
            )
        elif entity_type == "EMPTY":
            bpy.ops.object.empty_add(location=location, rotation=rotation, scale=scale)
        elif entity_type == "CAMERA":
            bpy.ops.object.camera_add(location=location, rotation=rotation)
        elif entity_type == "LIGHT":
            bpy.ops.object.light_add(type="POINT", location=location, rotation=rotation, scale=scale)
        else:
            raise ValueError(f"Unsupported entity type: {entity_type}")
        new_objects = set(bpy.data.objects) - old_objects
        if len(new_objects) == 0:
            raise Exception(f"Failed to create entity: {entity_type} {name}")
        # Get the created object
        obj = list(new_objects)[0]
        # Rename the object if a name is provided
        if name:
            obj.name = name

        return {
            "name": obj.name,
            "type": obj.type,
            "location": tuple(obj.location),
            "rotation": tuple(obj.rotation_euler),
            "bound_box": [tuple(obj.matrix_world @ Vector(v)) for v in obj.bound_box],
            "scale": tuple(obj.scale),
        }

    def modify_object(name: str, location: List[float] = None, rotation: List[float] = None, scale: List[float] = None, visible: bool = None) -> dict:
        """
        Modify an existing object in the Blender scene.

        Args:
        - name: Name of the object to modify
        - location: Optional [x, y, z] location coordinates
        - rotation: Optional [x, y, z] rotation in radians
        - scale: Optional [x, y, z] scale factors
        - visible: Optional boolean to set visibility
        """
        # Find the object by name
        obj = bpy.data.objects.get(name)
        if not obj:
            raise ValueError(f"Object not found: {name}")

        obj.location = location or obj.location
        obj.rotation_euler = rotation or obj.rotation_euler
        obj.scale = scale or obj.scale

        if visible is not None:
            obj.hide_viewport = not visible
            obj.hide_render = not visible

        return {
            "name": obj.name,
            "type": obj.type,
            "location": tuple(obj.location),
            "rotation": tuple(obj.rotation_euler),
            "scale": tuple(obj.scale),
            "bound_box": [tuple(obj.matrix_world @ Vector(v)) for v in obj.bound_box],
            "visible": obj.visible_get(),
        }

    def delete_object(object_name: str) -> dict:
        """
        Delete an object from the Blender scene by object name.

        Args:
        - object_name: Name of the object to delete
        """
        obj = bpy.data.objects.get(object_name)
        if not obj:
            raise ValueError(f"Object not found: {object_name}")
        with bpy.context.temp_override(selected_objects=[obj]):
            bpy.ops.object.delete()
        return {"deleted": object_name}
