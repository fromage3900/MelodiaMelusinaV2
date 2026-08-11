"""
Brutalist Geometry Nodes Framework
===================================
Base class for all Melodia Brutalist GeoNodes generators.
"""

import bpy
from typing import Dict, Optional


class BrutalistGNBase:
    """Base class for Brutalist Geometry Nodes generators."""
    
    category: str = "base"
    generator_id: str = "base"
    generator_name: str = "Base Generator"
    description: str = ""
    
    _node_tree: Optional[bpy.types.GeometryNodeTree] = None
    
    @classmethod
    def get_node_tree(cls) -> bpy.types.GeometryNodeTree:
        if cls._node_tree and cls._node_tree in bpy.data.node_groups:
            return cls._node_tree
        
        tree = bpy.data.node_groups.new(
            name=f"Brutalist GN - {cls.generator_name}",
            type='GeometryNodeTree'
        )
        cls._node_tree = tree
        
        input_node = tree.nodes.new('NodeGroupInput')
        output_node = tree.nodes.new('NodeGroupOutput')
        input_node.location = (-400, 0)
        output_node.location = (400, 0)
        
        cls.build_node_tree(tree, input_node, output_node)
        
        return tree
    
    @classmethod
    def build_node_tree(cls, tree, input_node, output_node):
        cls.add_parameters(tree, input_node, output_node)
        cls.build_geometry(tree, input_node, output_node)
    
    @classmethod
    def add_parameters(cls, tree, input_node, output_node):
        pass
    
    @classmethod
    def build_geometry(cls, tree, input_node, output_node):
        pass
    
    @classmethod
    def create_object(cls, name: str = None) -> bpy.types.Object:
        if name is None:
            name = f"Brutalist_{cls.generator_name}"
        
        mesh = bpy.data.meshes.new(name=f"{name}_mesh")
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(obj)
        
        modifier = obj.modifiers.new(name="Brutalist GN", type='NODES')
        modifier.node_group = cls.get_node_tree()
        
        return obj


BRUTALIST_GN_REGISTRY: Dict[str, type] = {}


def register_generator(cls):
    BRUTALIST_GN_REGISTRY[cls.generator_id] = cls
    return cls


def get_generator(gen_id: str) -> Optional[type]:
    return BRUTALIST_GN_REGISTRY.get(gen_id)


def list_generators_by_category(category: str = None) -> Dict[str, type]:
    if category:
        return {k: v for k, v in BRUTALIST_GN_REGISTRY.items() if v.category == category}
    return dict(BRUTALIST_GN_REGISTRY)


def register(): pass
def unregister(): BRUTALIST_GN_REGISTRY.clear()
