import bpy
import json


def rounding_dumps(obj, *args, precision=2, **kwargs):
    d1 = json.dumps(obj, *args, **kwargs)
    l1 = json.loads(d1, parse_float=lambda x: round(float(x), precision))
    return json.dumps(l1, *args, **kwargs)


def ensure_material_by_name(obj: bpy.types.Object, mat_name: str):
    """
    保证对象有指定的材质，如果没有则创建它。
    Args:
    - obj: Blender对象
    - mat_name: 材质名称
    """
    if mat_name not in bpy.data.materials:
        mat = bpy.data.materials.new(name=mat_name)
    mat = bpy.data.materials.get(mat_name)
    mat.use_nodes = True
    if mat.name not in obj.data.materials:
        obj.data.materials.append(mat)
    return mat


class NodeTreeUtil:
    @classmethod
    def find_node(cls, nt: bpy.types.NodeTree, cb, filter_cb=None):
        if not nt:
            return None
        for node in filter(filter_cb, nt.nodes):
            if cb(node):
                return node
            if node.type == "GROUP":
                if node := cls.find_node(node.node_tree, cb, filter_cb):
                    return node
        return None

    @classmethod
    def find_nodes(cls, nt: bpy.types.NodeTree, cb, filter_cb=None):
        nodes = []
        if not nt:
            return nodes
        fnodes = filter(filter_cb, nt.nodes)
        for node in fnodes:
            if cb(node):
                nodes.append(node)
            if node.type == "GROUP":
                nodes.extend(cls.find_nodes(node.node_tree, cb, filter_cb))
        return nodes

    @classmethod
    def find_node_by_name(cls, nt: bpy.types.NodeTree, nname, filter_cb=None):
        return cls.find_node(nt, lambda n: n.name == nname, filter_cb)

    @classmethod
    def find_nodes_by_name(cls, nt: bpy.types.NodeTree, nname, filter_cb=None):
        return cls.find_nodes(nt, lambda n: n.name == nname, filter_cb)

    @classmethod
    def find_node_by_label(cls, nt: bpy.types.NodeTree, label, filter_cb=None):
        return cls.find_node(nt, lambda n: n.label == label, filter_cb)

    @classmethod
    def find_nodes_by_label(cls, nt: bpy.types.NodeTree, label, filter_cb=None):
        return cls.find_nodes(nt, lambda n: n.label == label, filter_cb)

    @classmethod
    def find_node_by_type(cls, nt: bpy.types.NodeTree, ntype, filter_cb=None):
        return cls.find_node(nt, lambda n: n.type == ntype, filter_cb)

    @classmethod
    def find_nodes_by_type(cls, nt: bpy.types.NodeTree, ntype, filter_cb=None):
        return cls.find_nodes(nt, lambda n: n.type == ntype, filter_cb)

    @classmethod
    def find_node_by_idname(cls, nt: bpy.types.NodeTree, idname, filter_cb=None):
        return cls.find_node(nt, lambda n: n.bl_idname == idname, filter_cb)

    @classmethod
    def find_nodes_by_idname(cls, nt: bpy.types.NodeTree, idname, filter_cb=None):
        return cls.find_nodes(nt, lambda n: n.bl_idname == idname, filter_cb)
