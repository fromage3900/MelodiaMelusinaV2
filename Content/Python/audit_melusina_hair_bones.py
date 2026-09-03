"""List Melusina hair skeleton chains and current Kawaii root configuration."""
import json
from pathlib import Path
import unreal

OUT = Path(unreal.Paths.project_dir()) / "Saved" / "Audit" / "melusina_hair_bones.json"
MESH = "/Game/Melodia/Characters/Melusina/Hair/SK_MelusinaHair"
ABP = "/Game/Melodia/Characters/Melusina/Hair/ABP_Melusina_WaterHair"
mesh = unreal.load_asset(MESH)
skeleton = mesh.get_editor_property("skeleton") if mesh else None
# UE 5.8 exposes bone names through the reference pose, rather than directly
# on USkeleton. Keep this audit read-only so it is safe to run while artists
# are working in the Editor.
bones = [str(name) for name in skeleton.get_reference_pose().get_bone_names()] if skeleton else []
hair_bones = [name for name in bones if "hair" in name.lower() or "bang" in name.lower() or "tail" in name.lower()]
abp = unreal.load_asset(ABP)
nodes = []
klass = getattr(unreal, "AnimGraphNode_KawaiiPhysics", None)
if abp and klass:
    for graph_node in abp.get_nodes_of_class(klass):
        runtime = graph_node.get_editor_property("node")
        root = runtime.get_editor_property("root_bone")
        nodes.append({
            "node": graph_node.get_name(),
            "root_bone_name": str(root.get_editor_property("bone_name")),
            "root_bone_struct": str(root),
        })
report = {"mesh": MESH, "skeleton": skeleton.get_path_name() if skeleton else "", "bone_count": len(bones), "first_bones": bones[:40], "hair_bones": hair_bones, "kawaii_nodes": nodes}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log("MELUSINA_HAIR_BONE_AUDIT: " + json.dumps({"bone_count": len(bones), "hair_bone_count": len(hair_bones), "roots": [n["root_bone_name"] for n in nodes]}))
