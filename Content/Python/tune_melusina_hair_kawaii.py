"""Tune Melusina hair Kawaii Physics to match Water palette: slower settle, softer snap."""
import json
import unreal

ABP = "/Game/Melodia/Characters/Melusina/Hair/ABP_Melusina_WaterHair"
abp = unreal.load_asset(ABP)
kclass = getattr(unreal, "AnimGraphNode_KawaiiPhysics", None)
nodes = abp.get_nodes_of_class(kclass)
if not nodes:
    print(json.dumps({"ok": False, "error": "no kawaii nodes found"}))
    print("DONE")
    raise SystemExit(0)

node = nodes[0]
rt = node.get_editor_property("node")
before = rt.get_editor_property("physics_settings")

# current values
snapshot = {
    "damping": float(before.damping),
    "stiffness": float(before.stiffness),
    "limit_angle": float(before.limit_angle),
    "radius": float(before.radius),
    "world_damping_location": float(before.world_damping_location),
    "world_damping_rotation": float(before.world_damping_rotation),
}

# new values — gentle water-flow motion, less snap-back
after = {
    "damping": 0.42,
    "stiffness": 0.14,
    "limit_angle": 46.0,
    "radius": 3.5,               # unchanged
    "world_damping_location": 0.60,
    "world_damping_rotation": 0.50,
}

ps = node.get_editor_property("node").get_editor_property("physics_settings")
ps.damping = after["damping"]
ps.stiffness = after["stiffness"]
ps.limit_angle = after["limit_angle"]
ps.radius = after["radius"]
ps.world_damping_location = after["world_damping_location"]
ps.world_damping_rotation = after["world_damping_rotation"]

node.get_editor_property("node").set_editor_property("physics_settings", ps)

unreal.BlueprintEditorLibrary.compile_blueprint(abp)
unreal.EditorAssetLibrary.save_loaded_asset(abp, False)

# verify
nodes2 = abp.get_nodes_of_class(kclass)
verify_before = {}
if nodes2:
    vb = nodes2[0].get_editor_property("node").get_editor_property("physics_settings")
    verify_before = {
        "damping": float(vb.damping),
        "stiffness": float(vb.stiffness),
        "limit_angle": float(vb.limit_angle),
        "radius": float(vb.radius),
        "world_damping_location": float(vb.world_damping_location),
        "world_damping_rotation": float(vb.world_damping_rotation),
    }

print(json.dumps({
    "before": snapshot,
    "after": after,
    "persisted": verify_before,
    "asset": ABP,
}, indent=1))
print("DONE")