"""Bake a World Compiler `structures` kit: MEL GN builder slots -> bevelled meshes -> GLB.

Reads the compiler's structures_bake.json (world_recipe.v1 `structures`), realizes each
slot's MEL_* builder with its preset + params, adds the bevel/weighted-normal pass,
and exports one GLB per slot for Interchange import into `kit_ue_path` (no FBX:
automated FBX import crashed the editor twice).

Run:  blender --background --python Tools/bake_structures_kit.py -- Saved/WorldCompiler/morning_rainbow_bloom_3900
Out:  <bundle>/kit/SM_<slot_id>.glb + <bundle>/kit/kit_manifest.json
"""
import bpy, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(REPO, "deploy"))
for _m in [m for m in list(sys.modules) if m == "surreal_arch" or m.startswith("surreal_arch.")]:
    del sys.modules[_m]
import surreal_arch  # noqa: E402  (repo copy, registers every melodia_gn builder)
from surreal_arch.melodia_gn import core, presets  # noqa: E402

BEVEL_WIDTH_M = 0.02
BEVEL_SEGMENTS = 2


def _args() -> str:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not argv:
        raise SystemExit("usage: blender -b --python Tools/bake_structures_kit.py -- <bundle_dir>")
    path = argv[0]
    return path if os.path.isabs(path) else os.path.join(REPO, path)


def _builder_group(builder_id: str):
    res = core.GROUP_BUILDERS[builder_id]()
    return res[0] if isinstance(res, (tuple, list)) else res


def _realize(slot_id: str, slot: dict) -> bpy.types.Object:
    group = _builder_group(slot["builder_id"])
    params = {}
    if slot.get("preset"):
        params.update(presets.export_builder_preset(slot["builder_id"], slot["preset"])["params"])
    params.update(slot.get("params") or {})

    wrap = bpy.data.node_groups.new(f"KIT_{slot_id}", "GeometryNodeTree")
    wrap.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    wrap.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    gin, gout = wrap.nodes.new("NodeGroupInput"), wrap.nodes.new("NodeGroupOutput")
    nest = wrap.nodes.new("GeometryNodeGroup")
    nest.node_tree = group
    applied, missing = {}, []
    for name, value in params.items():
        sock = nest.inputs.get(name)
        if sock is None:
            missing.append(name)
            continue
        sock.default_value = value
        applied[name] = value
    if "Geometry" in nest.inputs:
        wrap.links.new(gin.outputs[0], nest.inputs["Geometry"])
    wrap.links.new(nest.outputs[0], gout.inputs[0])

    mesh = bpy.data.meshes.new(f"SM_{slot_id}")
    obj = bpy.data.objects.new(f"SM_{slot_id}", mesh)
    bpy.context.scene.collection.objects.link(obj)
    mod = obj.modifiers.new("MEL", "NODES")
    mod.node_group = wrap
    bev = obj.modifiers.new("Bevel", "BEVEL")
    bev.width, bev.segments, bev.limit_method, bev.harden_normals = BEVEL_WIDTH_M, BEVEL_SEGMENTS, "ANGLE", True
    obj.modifiers.new("WNormal", "WEIGHTED_NORMAL").keep_sharp = True

    depsgraph = bpy.context.evaluated_depsgraph_get()
    baked = bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph), depsgraph=depsgraph)
    obj.modifiers.clear()
    obj.data = baked
    obj["mel_params_applied"] = json.dumps(applied)
    obj["mel_params_missing"] = json.dumps(missing)
    return obj


def main() -> None:
    bundle = _args()
    bake = json.load(open(os.path.join(bundle, "structures_bake.json"), encoding="utf-8"))
    out_dir = os.path.join(bundle, "kit")
    os.makedirs(out_dir, exist_ok=True)
    report = {"kit_ue_path": bake["kit_ue_path"], "slots": {}}
    for slot_id, slot in bake["slots"].items():
        bpy.ops.wm.read_factory_settings(use_empty=True)
        obj = _realize(slot_id, slot)
        verts, polys = len(obj.data.vertices), len(obj.data.polygons)
        dims = [round(d, 3) for d in obj.dimensions]
        glb = os.path.join(out_dir, f"SM_{slot_id}.glb")
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.export_scene.gltf(filepath=glb, export_format="GLB", use_selection=True, export_apply=True)
        report["slots"][slot_id] = {
            "builder_id": slot["builder_id"], "preset": slot.get("preset", ""),
            "glb": os.path.relpath(glb, REPO).replace("\\", "/"),
            "verts": verts, "polys": polys, "dims_m": dims,
            "params_applied": json.loads(obj["mel_params_applied"]),
            "params_missing": json.loads(obj["mel_params_missing"]),
        }
        print(f"KIT {slot_id}: {slot['builder_id']} {verts}v {polys}f dims {dims} -> {glb}")
    with open(os.path.join(out_dir, "kit_manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
    print("KIT DONE", len(report["slots"]))


main()
