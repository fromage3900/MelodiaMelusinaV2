"""GN_MH_03_RoofRibbon — the hero roof. One builder, three ribbon trees.

Shape: unit grid 25x13, normalized whale-back profile from ShaderNodeMath
(body sine + eave curl + end lift + asymmetry skew), Set Position,
Transform scale to Width/Depth, Extrude thickness, Bevel, Shade Smooth.
Params baked as tree interface defaults per roof (5.2 headless cannot set
per-object modifier inputs; topology identical across the three trees).

Plan ss 5: center largest, wing offset, porch lower/sheltering.
"""
import bpy
import os

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.unit_settings.system = 'METRIC'
col = bpy.data.collections.new("MH_GN_OUTPUT")
sc.collection.children.link(col)


def build_ribbon(tree_name, vals):
    tree = bpy.data.node_groups.new(tree_name, "GeometryNodeTree")
    nodes = tree.nodes
    links = tree.links
    for name in ["Roof Width", "Roof Depth", "Roof Rise", "Eave Curl",
                 "End Lift", "Thickness", "Asymmetry"]:
        try:
            s = tree.interface.new_socket(name=name, socket_type="NodeSocketFloat", in_out='INPUT')
            s.default_value = vals[name]
        except Exception as e:
            print(f"param {name}: {e}")
    try:
        tree.interface.new_socket(name="Geometry", socket_type="NodeSocketGeometry", in_out='OUTPUT')
    except Exception as e:
        print(f"out sock: {e}")

    def add(bid, loc):
        try:
            n = nodes.new(bid)
            n.location = loc
            return n
        except Exception as e:
            print(f"SKIP {bid}: {e}")
            return None

    def math(op, loc, v2=None):
        n = add("ShaderNodeMath", loc)
        if n is None:
            return None
        try:
            n.operation = op
        except Exception as e:
            print(f"math op {op}: {e}")
        if v2 is not None:
            try:
                n.inputs[1].default_value = v2
            except Exception:
                pass
        return n

    def use_param(math_node, input_idx, param_name):
        """Drive a math input from the group interface socket."""
        gin_node = nodes.get("Group Input")
        try:
            links.new(gin_node.outputs[param_name], math_node.inputs[input_idx])
        except Exception as e:
            print(f"plink {param_name}: {e}; baking {vals[param_name]}")
            try:
                math_node.inputs[input_idx].default_value = vals[param_name]
            except Exception:
                pass

    gin = add("NodeGroupInput", (-900, 0))
    gin.name = "Group Input"
    gout = add("NodeGroupOutput", (2500, 0))
    grid = add("GeometryNodeMeshGrid", (-700, 200))
    for k, v in (("Size X", 1.0), ("Size Y", 1.0), ("Vertices X", 25), ("Vertices Y", 13)):
        try:
            grid.inputs[k].default_value = v
        except Exception:
            pass

    pos = add("GeometryNodeInputPosition", (-700, -200))
    sep = add("ShaderNodeSeparateXYZ", (-500, -200))
    links.new(pos.outputs["Position"], sep.inputs["Vector"])

    u = math('ADD', (-300, 100), 0.5); links.new(sep.outputs["X"], u.inputs[0])
    v = math('ADD', (-300, -100), 0.5); links.new(sep.outputs["Y"], v.inputs[0])

    piu = math('MULTIPLY', (-100, 200), 3.14159); links.new(u.outputs["Value"], piu.inputs[0])
    sinu = math('SINE', (100, 200)); links.new(piu.outputs["Value"], sinu.inputs[0])
    powu = math('POWER', (300, 200), 1.3); links.new(sinu.outputs["Value"], powu.inputs[0])
    body = math('MULTIPLY', (500, 200)); links.new(powu.outputs["Value"], body.inputs[0])
    use_param(body, 1, "Roof Rise")

    vm = math('SUBTRACT', (-100, -100), 0.5); links.new(v.outputs["Value"], vm.inputs[0])
    av = math('ABSOLUTE', (100, -100)); links.new(vm.outputs["Value"], av.inputs[0])
    e2 = math('MULTIPLY', (300, -100), 2.0); links.new(av.outputs["Value"], e2.inputs[0])
    e3 = math('POWER', (500, -100), 2.0); links.new(e2.outputs["Value"], e3.inputs[0])
    eave = math('MULTIPLY', (700, -100)); links.new(e3.outputs["Value"], eave.inputs[0])
    use_param(eave, 1, "Eave Curl")

    um = math('SUBTRACT', (-100, 0), 0.5); links.new(u.outputs["Value"], um.inputs[0])
    au = math('ABSOLUTE', (100, 0)); links.new(um.outputs["Value"], au.inputs[0])
    n2 = math('MULTIPLY', (300, 0), 2.0); links.new(au.outputs["Value"], n2.inputs[0])
    n3 = math('POWER', (500, 0), 3.0); links.new(n2.outputs["Value"], n3.inputs[0])
    ends = math('MULTIPLY', (700, 0)); links.new(n3.outputs["Value"], ends.inputs[0])
    use_param(ends, 1, "End Lift")

    am = math('MULTIPLY', (100, -300)); links.new(um.outputs["Value"], am.inputs[0]); links.new(v.outputs["Value"], am.inputs[1])
    am2 = math('MULTIPLY', (500, -300)); links.new(am.outputs["Value"], am2.inputs[0])
    use_param(am2, 1, "Asymmetry")
    am3 = math('MULTIPLY', (700, -300)); links.new(am2.outputs["Value"], am3.inputs[0])
    use_param(am3, 1, "Roof Rise")
    am4 = math('MULTIPLY', (900, -300), 0.5); links.new(am3.outputs["Value"], am4.inputs[0])

    z1 = math('ADD', (900, 100)); links.new(body.outputs["Value"], z1.inputs[0]); links.new(eave.outputs["Value"], z1.inputs[1])
    z2 = math('ADD', (1100, 100)); links.new(z1.outputs["Value"], z2.inputs[0]); links.new(ends.outputs["Value"], z2.inputs[1])
    z3 = math('ADD', (1300, 100)); links.new(z2.outputs["Value"], z3.inputs[0]); links.new(am4.outputs["Value"], z3.inputs[1])

    comb = add("ShaderNodeCombineXYZ", (1500, 0))
    links.new(sep.outputs["X"], comb.inputs["X"])
    links.new(sep.outputs["Y"], comb.inputs["Y"])
    links.new(z3.outputs["Value"], comb.inputs["Z"])

    setp = add("GeometryNodeSetPosition", (1700, 200))
    links.new(grid.outputs["Mesh"], setp.inputs["Geometry"])
    links.new(comb.outputs["Vector"], setp.inputs["Position"])

    tr = add("GeometryNodeTransform", (1900, 200))
    links.new(setp.outputs["Geometry"], tr.inputs["Geometry"])
    scomb = add("ShaderNodeCombineXYZ", (1700, -200))
    use_param(scomb, 0, "Roof Width")
    use_param(scomb, 1, "Roof Depth")
    scomb.inputs["Z"].default_value = 1.0
    links.new(scomb.outputs["Vector"], tr.inputs["Scale"])

    ext = add("GeometryNodeExtrudeMesh", (2100, 200))
    links.new(tr.outputs["Geometry"], ext.inputs["Mesh"])
    try:
        ext.inputs["Selection"].default_value = True
    except Exception:
        pass
    try:
        links.new(gin.outputs["Thickness"], ext.inputs["Offset"])
    except Exception as e:
        print(f"thickness link: {e}")
        try:
            ext.inputs["Offset"].default_value = vals["Thickness"]
        except Exception:
            pass

    bev = add("GeometryNodeMeshBevel", (2250, 200))
    try:
        bev.inputs["Offset"].default_value = 0.03
    except Exception as e:
        print(f"bev: {e}")
    links.new(ext.outputs["Mesh"], bev.inputs["Mesh"])

    smooth = add("GeometryNodeSetShadeSmooth", (2400, 200))
    links.new(bev.outputs["Mesh"], smooth.inputs["Mesh"])
    links.new(smooth.outputs["Mesh"], gout.inputs["Geometry"])
    print(f"BUILT {tree_name}: nodes={len(tree.nodes)}")
    return tree


ROOFS = [
    ("GN_MH_03_RoofMain", "Roof_Main",
     {"Roof Width": 9.0, "Roof Depth": 6.0, "Roof Rise": 2.55, "Eave Curl": 0.45,
      "End Lift": 0.65, "Thickness": 0.12, "Asymmetry": 0.25}, (0, 0, 3.42)),
    ("GN_MH_03_RoofWing", "Roof_Wing",
     {"Roof Width": 6.0, "Roof Depth": 4.5, "Roof Rise": 1.9, "Eave Curl": 0.4,
      "End Lift": 0.55, "Thickness": 0.10, "Asymmetry": -0.3}, (-2.5, -1.0, 3.1)),
    ("GN_MH_03_RoofPorch", "Roof_Porch",
     {"Roof Width": 4.5, "Roof Depth": 2.4, "Roof Rise": 1.1, "Eave Curl": 0.35,
      "End Lift": 0.45, "Thickness": 0.08, "Asymmetry": 0.15}, (1.0, 4.6, 2.9)),
]
for tree_name, obj_name, vals, loc in ROOFS:
    tree = build_ribbon(tree_name, vals)
    m = bpy.data.meshes.new(obj_name)
    o = bpy.data.objects.new(obj_name, m)
    col.objects.link(o)
    md = o.modifiers.new("GN", type='NODES')
    md.node_group = tree
    o.location = loc

os.makedirs("Saved/MelusinasHouse", exist_ok=True)
bpy.ops.wm.save_mainfile(filepath="Saved/MelusinasHouse/House_RoofRibbon_v2.blend")
print("Saved: Saved/MelusinasHouse/House_RoofRibbon_v2.blend")
