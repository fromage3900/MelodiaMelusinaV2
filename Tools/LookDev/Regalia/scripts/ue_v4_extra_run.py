"""fromage-side runner (NOT RUN YET): python ue_v4_extra_run.py eyebrows_import|earrings_import|earrings_abp|attach_level|check
python stages exec ue_v4_extra_write.py in the editor; earrings_abp drives Monolith animation actions (KawaiiPhysics nodes)."""
import sys, json
sys.path.insert(0, r"C:\EnvironmentPortfolio\BS_GodFile\Tools\Audio")
from monolith_client import MonolithClient
S = r"C:\EnvironmentPortfolio\_lookdev_work\regalia_v2\scripts"
E = r"C:\EnvironmentPortfolio\_lookdev_work\regalia_v2\ue_export_v4"
DST_R = "/Game/Melodia/Characters/Melusina/Regalia_v4"
SK = DST_R + "/SK_Regalia_v4_Earrings"; ABP = DST_R + "/ABP_Regalia_Earrings_v4"
stage = sys.argv[1]; mc = MonolithClient(timeout=900)
def A(action, **kw):
    r = mc.query("animation_query", action, **kw); print("  ", action, str(r)[:600]); return r
def J(r):
    try: return json.loads(r)
    except Exception: return {}
if stage in ("eyebrows_import", "earrings_import", "attach_level"):
    print(mc.run_python('STAGE = "%s"\nexec(open(r"%s\\ue_v4_extra_write.py").read())' % (stage, S), timeout=900)[:4000])
elif stage == "earrings_abp":
    KS = json.load(open(E + r"\earrings_physics\SK_Regalia_v4_Earrings_sidecar.json"))["kawaii_suggest"]
    info = J(A("get_skeletal_mesh_info", asset_path=SK)); skel = info.get("skeleton") or (SK + "_Skeleton")
    if not J(A("get_abp_info", asset_path=ABP)).get("skeleton"):
        A("create_anim_blueprint", asset_path=ABP, skeleton_path=skel)
    ids = {}
    for key, cls, x in (("l2c", "LocalToComponentSpace", 0), ("kL", "/Script/KawaiiPhysicsEd.AnimGraphNode_KawaiiPhysics", 300),
                        ("kR", "/Script/KawaiiPhysicsEd.AnimGraphNode_KawaiiPhysics", 600), ("c2l", "ComponentToLocalSpace", 900)):
        kw = {"node_type": cls} if not cls.startswith("/") else {"node_class": cls}
        r = J(A("add_anim_graph_node", asset_path=ABP, graph_name="AnimGraph", position_x=x, position_y=0, **kw))
        ids[key] = r.get("node_id") or r.get("node_name") or r.get("name")
    for k, root in (("kL", "ear_L_root"), ("kR", "ear_R_root")):
        for pth, val in (("RootBone.BoneName", root), ("PhysicsSettings.Damping", KS["damping"]), ("PhysicsSettings.Stiffness", KS["stiffness"]),
                         ("PhysicsSettings.WorldDampingLocation", KS["world_damping_location"]), ("PhysicsSettings.WorldDampingRotation", KS["world_damping_rotation"]),
                         ("PhysicsSettings.Radius", KS["radius_cm"]), ("PhysicsSettings.LimitAngle", KS["limit_angle_deg"]),
                         ("Gravity", "(X=0,Y=0,Z=-981)"), ("bUseWorldSpaceGravity", "True")):
            A("set_anim_graph_node_property", asset_path=ABP, node_id=ids[k], property_path=pth, value=str(val), graph_name="AnimGraph")
    nodes = J(A("get_nodes", asset_path=ABP)); root = next((n.get("name") for n in nodes.get("nodes", []) if "Root" in str(n.get("class", n.get("name", "")))), "AnimGraphNode_Root_0")
    for s, sp, t, tp in ((ids["l2c"], "ComponentPose", ids["kL"], "ComponentPose"), (ids["kL"], "Pose", ids["kR"], "ComponentPose"),
                         (ids["kR"], "Pose", ids["c2l"], "ComponentPose"), (ids["c2l"], "Pose", root, "Result")):
        A("connect_anim_graph_pins", asset_path=ABP, source_node=s, source_pin=sp, target_node=t, target_pin=tp, graph_name="AnimGraph")
    print(mc.run_python('import unreal\np="%s"\nassert p.startswith("%s/")\nunreal.EditorAssetLibrary.save_asset(p, only_if_is_dirty=False)\nprint("saved", p)' % (ABP, DST_R))[:400])
elif stage == "check":   # read-only
    KS = json.load(open(E + r"\earrings_physics\SK_Regalia_v4_Earrings_sidecar.json"))
    r = J(A("get_bone_ref_pose", asset_path=SK)); print(json.dumps(r)[:1500]); print("expected", {b: v["head_ue_bcm"] for b, v in KS["bones"].items()})
    A("get_abp_info", asset_path=ABP)
