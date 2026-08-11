"""
Geometry Nodes Framework — Core system for creating procedural kawaii assets.

This framework creates, manages, and applies Geometry Nodes setups with
exposed parameters for real-time adjustment.
"""

import bpy
import math
from typing import Dict, Any, Optional


def get_input_socket(input_node, name: str):
    """Resolve a Group Input output socket by name (Blender 4.2–5.1)."""
    try:
        return input_node.outputs[name]
    except (KeyError, TypeError):
        pass
    for sock in input_node.outputs:
        if sock.name == name:
            return sock
    raise KeyError(f"Group Input socket not found: {name}")


def get_output_socket(output_node, name: str = 'Geometry'):
    """Resolve a Group Output input socket by name (Blender 4.2–5.1)."""
    try:
        return output_node.inputs[name]
    except (KeyError, TypeError):
        pass
    for sock in output_node.inputs:
        if sock.name == name:
            return sock
    raise KeyError(f"Group Output socket not found: {name}")


def _iface_has_socket(tree, name: str, in_out: str) -> bool:
    for item in tree.interface.items_tree:
        if getattr(item, 'in_out', None) == in_out and item.name == name:
            return True
    return False


def ensure_geometry_interface(tree, with_input: bool = False):
    """Blender 5.x leaves new GN groups without default Geometry I/O sockets."""
    if with_input and not _iface_has_socket(tree, 'Geometry', 'INPUT'):
        tree.interface.new_socket(
            'Geometry', in_out='INPUT', socket_type='NodeSocketGeometry',
        )
    if not _iface_has_socket(tree, 'Geometry', 'OUTPUT'):
        tree.interface.new_socket(
            'Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry',
        )


def tree_has_geometry_output(tree) -> bool:
    return _iface_has_socket(tree, 'Geometry', 'OUTPUT')


def purge_stale_kawaii_node_groups():
    """Remove pre-fix node groups missing Geometry OUTPUT on the interface."""
    try:
        groups = bpy.data.node_groups
    except (AttributeError, RuntimeError):
        return 0
    stale = [
        ng for ng in groups
        if ng.name.startswith("Kawaii GN - ") and not tree_has_geometry_output(ng)
    ]
    for ng in stale:
        groups.remove(ng)
    return len(stale)


def clear_generator_tree_cache():
    """Drop in-memory tree references so reload/rebuild picks up interface fixes."""
    for gen_cls in KAWAII_GN_REGISTRY.values():
        gen_cls._node_tree = None


def kindchenschema_scale(cuteness: float):
    """Head/body scale factors from 0–1 cuteness (Kindchenschema proportions)."""
    c = max(0.0, min(1.0, cuteness))
    return (1.0 + c * 0.35, 1.0 - c * 0.15)


def ensure_roundness_parameter(tree, default: float = 0.8):
    """Ensure every GN tree exposes Roundness for scene cuteness driving."""
    for item in tree.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT' and item.name == 'Roundness':
            return
    sock = tree.interface.new_socket(
        'Roundness', in_out='INPUT', socket_type='NodeSocketFloat',
    )
    sock.default_value = default


CUTENESS_INPUT_NAMES = frozenset({'Cuteness', 'Roundness', 'Chibi'})


def apply_scene_cuteness_to_object(obj: bpy.types.Object, cuteness: float):
    """Drive Cuteness/Roundness/Chibi GN modifier inputs from scene cuteness_level."""
    if obj is None:
        return
    c = max(0.0, min(1.0, cuteness))
    for mod in obj.modifiers:
        if mod.type != 'NODES' or not mod.node_group:
            continue
        iface = mod.node_group.interface
        for item in iface.items_tree:
            if getattr(item, 'in_out', None) != 'INPUT':
                continue
            if item.name not in CUTENESS_INPUT_NAMES:
                continue
            try:
                mod[item.identifier] = c
            except (TypeError, KeyError, AttributeError):
                pass


class KawaiiGNBase:
    """Base class for all Kawaii Geometry Nodes generators."""
    
    category: str = "base"
    generator_id: str = "base"
    generator_name: str = "Base Generator"
    description: str = ""
    uses_input_geometry: bool = False
    
    # Node tree reference
    _node_tree: Optional[bpy.types.GeometryNodeTree] = None
    
    @classmethod
    def get_node_tree(cls) -> bpy.types.GeometryNodeTree:
        """Get or create the Geometry Nodes tree for this generator."""
        tree_name = f"Kawaii GN - {cls.generator_name}"

        if cls._node_tree and cls._node_tree in bpy.data.node_groups:
            if tree_has_geometry_output(cls._node_tree):
                return cls._node_tree
            bpy.data.node_groups.remove(cls._node_tree)
            cls._node_tree = None

        existing = bpy.data.node_groups.get(tree_name)
        if existing is not None:
            if tree_has_geometry_output(existing):
                cls._node_tree = existing
                return cls._node_tree
            bpy.data.node_groups.remove(existing)

        tree = bpy.data.node_groups.new(name=tree_name, type='GeometryNodeTree')
        cls._node_tree = tree
        cls.build_node_tree(tree)
        return tree
    
    @classmethod
    def build_node_tree(cls, tree: bpy.types.GeometryNodeTree):
        """Build the Geometry Nodes setup. Override in subclasses."""
        ensure_geometry_interface(tree, with_input=cls.uses_input_geometry)

        input_node = tree.nodes.new('NodeGroupInput')
        output_node = tree.nodes.new('NodeGroupOutput')
        input_node.location = (-400, 0)
        output_node.location = (400, 0)

        if cls.uses_input_geometry:
            tree.links.new(
                get_input_socket(input_node, 'Geometry'),
                get_output_socket(output_node, 'Geometry'),
            )

        # Add custom parameters
        cls.add_parameters(tree, input_node, output_node)
        ensure_roundness_parameter(tree)
        
        # Build geometry
        cls.build_geometry(tree, input_node, output_node)
    
    @classmethod
    def add_parameters(cls, tree, input_node, output_node):
        """Add custom parameters to the node tree. Override in subclasses."""
        pass
    
    @classmethod
    def build_geometry(cls, tree, input_node, output_node):
        """Build the actual geometry. Override in subclasses."""
        pass
    
    @classmethod
    def create_object(cls, name: str = None) -> bpy.types.Object:
        """Create a new object with this Geometry Nodes modifier."""
        if name is None:
            name = f"Kawaii_{cls.generator_name}"
        
        # Create mesh object
        mesh = bpy.data.meshes.new(name=f"{name}_mesh")
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(obj)
        
        # Add Geometry Nodes modifier
        modifier = obj.modifiers.new(name="Kawaii GN", type='NODES')
        modifier.node_group = cls.get_node_tree()
        
        return obj
    
    @classmethod
    def apply_to_object(cls, obj: bpy.types.Object):
        """Apply Geometry Nodes modifier to an existing object."""
        modifier = obj.modifiers.new(name="Kawaii GN", type='NODES')
        modifier.node_group = cls.get_node_tree()
        return modifier


# Registry of all generators
KAWAII_GN_REGISTRY: Dict[str, type] = {}


def register_generator(cls):
    """Decorator to register a Kawaii GN generator."""
    KAWAII_GN_REGISTRY[cls.generator_id] = cls
    return cls


def get_generator(gen_id: str) -> Optional[type]:
    """Get a generator by ID."""
    return KAWAII_GN_REGISTRY.get(gen_id)


def list_generators_by_category(category: str = None) -> Dict[str, type]:
    """List generators, optionally filtered by category."""
    if category:
        return {k: v for k, v in KAWAII_GN_REGISTRY.items() if v.category == category}
    return dict(KAWAII_GN_REGISTRY)


def register():
    """Register the framework."""
    pass


def unregister():
    """Unregister the framework."""
    KAWAII_GN_REGISTRY.clear()
