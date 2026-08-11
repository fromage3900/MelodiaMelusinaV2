import unreal, json

out = {}

def desc(o):
    return o.get_path_name() if o else None

# Target mesh + skeleton chain
sk_mel = unreal.load_asset('/Game/Melodia/Characters/Melusina/SK_Melusina')
out['SK_Melusina'] = desc(sk_mel)
out['SK_Melusina.skeleton'] = desc(sk_mel.get_editor_property('skeleton')) if sk_mel else None

src_mesh = unreal.load_asset('/Game/Melodia/Mocap/Source/SK_MocapSource')
out['SK_MocapSource'] = desc(src_mesh)
out['SK_MocapSource.skeleton'] = desc(src_mesh.get_editor_property('skeleton')) if src_mesh else None

# IK rigs — resolve their skeletons via controllers
for label, path in (('src_rig', '/Game/Melodia/Mocap/Source/IK_MocapSource'),
                    ('tgt_rig', '/Game/Melodia/Characters/Melusina/IK_Melusina_Body')):
    rig = unreal.load_asset(path)
    out[label] = desc(rig)
    if rig:
        c = unreal.IKRigController.get_controller(rig)
        try:
            out[label + '.mesh'] = desc(c.get_skeletal_mesh())
        except Exception as e:
            out[label + '.mesh_err'] = str(e)
        try:
            out[label + '.root'] = str(c.get_retarget_root())
            out[label + '.chains'] = [str(ch.chain_name) for ch in c.get_retarget_chains()]
        except Exception as e:
            out[label + '.chain_err'] = str(e)

# Retargeter preview meshes
rtg = unreal.load_asset('/Game/Melodia/Mocap/RTG_Mocap_to_Melusina')
out['RTG'] = desc(rtg)
if rtg:
    rc = unreal.IKRetargeterController.get_controller(rtg)
    out['RTG.src_preview'] = desc(rc.get_preview_mesh(unreal.RetargetSourceOrTarget.SOURCE))
    out['RTG.tgt_preview'] = desc(rc.get_preview_mesh(unreal.RetargetSourceOrTarget.TARGET))
    try:
        out['RTG.src_ikrig'] = desc(rc.get_ik_rig(unreal.RetargetSourceOrTarget.SOURCE))
        out['RTG.tgt_ikrig'] = desc(rc.get_ik_rig(unreal.RetargetSourceOrTarget.TARGET))
    except Exception as e:
        out['RTG.ikrig_err'] = str(e)

with open(r'G:/EnvironmentPortfolio/BS_GodFile/Saved/Melodia/skeleton_diag.json', 'w') as f:
    json.dump(out, f, indent=1)
unreal.log('[SkeletonDiag] wrote ' + json.dumps(out))
