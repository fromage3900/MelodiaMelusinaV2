"""Additive offline terminal support proposal from existing measured KineFX data.

Creates only diagnostic JSON/OBJ/figure artifacts beside this script. This is
not a skeleton export, cloth simulator, recapture or production import tool.
"""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent
PINNED_FBX='40356ebc1521e5420737c13a4cfc4d487be4a7650478cedbd2cb68c3817923ea'
SOURCES=[HERE.parent/'SourceExports/SK_Melusina_V2_Skirt_R2_SmoothChains.fbx',
         HERE/'skirt_tip_reach.json', HERE/'skeleton_hierarchy.json',
         HERE/'SK_Melusina_V2_Skirt_R2_SmoothChains_data.json']
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
previous_candidate_path=HERE/'skirt_terminal_support_proxy_candidate.json'
previous_candidate=json.loads(previous_candidate_path.read_text(encoding='utf-8')) if previous_candidate_path.exists() else None
previous_obj_hash=sha(HERE/'skirt_terminal_support_proxy_candidate.obj') if (HERE/'skirt_terminal_support_proxy_candidate.obj').exists() else None
before={p.name:sha(p) for p in SOURCES}
if before[SOURCES[0].name]!=PINNED_FBX:raise RuntimeError('Fresh source FBX pin changed; stop rather than use stale reach')
reach=json.loads(SOURCES[1].read_text(encoding='utf-8'))
hierarchy=json.loads(SOURCES[2].read_text(encoding='utf-8'))[2]['joints']
skin=json.loads(SOURCES[3].read_text(encoding='utf-8'))
if reach['source_sha256']!=PINNED_FBX or len(hierarchy)!=465 or len(skin['positions_m'])!=30509:
    raise RuntimeError('Source evidence identity/count mismatch')

candidate={'schema':'melodia.skirt_terminal_support_proxy.v1',
    'authority':'DIAGNOSTIC_CANDIDATE_ONLY',
    'source_pins':before,'coordinate_system':{'units':'metres','up':'Y','source':'Existing KineFX FBX Character Import, convertunits=1'},
    'canonical_joint_count':len(hierarchy),'canonical_joint_changes':0,
    'virtual_terminal_count':16,'skinning_weight_changes':0,'mesh_vertex_changes':0,
    'selection':'For each terminal, max(p95 dominant-tip vertices, p95 vertices with tip weight >0.25). Maximum support envelope uses max of both sets.',
    'selection_cohorts':{'dominant':'Tip bone has the largest source skin weight at that vertex.',
                         'weight_gt_0_25':'Tip bone source skin weight is strictly >0.25.',
                         'candidate_estimator':'Maximum of the two separately computed signed forward p95 values; not a pooled percentile.',
                         'envelope_estimator':'Maximum of both signed forward maxima.'},
    'purpose':'Visualize measured missing longitudinal terminal support; reviewable proposal before any native Kawaii or skeleton changes.',
    'is_physics_tuning':False,'is_ue_importable_skeleton':False,'collision_radius_m':None,
    'axial_endpoints_are_surface_contacts':False,
    'axial_projection_limitation':'Endpoints lie on measured bone longitudinal axes, not necessarily on the cloth surface. Lateral skin offsets can place the axial endpoint outside the silhouette. Nearest surface distances are measured; these lines are not collision bounds.',
    'layer_policy':'Preserve all29 topology islands and shared64 radial bones. The three large hem islands remain on one radial rig; coincident seams are intentional.',
    'native_axis_status':'UNVERIFIED. KineFX imported normalized matrix +Y aligns with head-minus-previous. Do not copy this axis enum into Unreal without native reference-pose readback.',
    'production_gates_pending':[
        'Native Unreal reference-pose bone forward-axis readback for all16 last bones.',
        'Owner review of candidate endpoint reach and silhouette on the fully dressed hero.',
        'One-owner Kawaii integration with actual body/leg collision primitives and temporal stability measurements.',
        'Walk/run/turn/stop, crouch/steps/slopes and combat real-input runtime captures, plus restart/readback.',
        'If actual joints are added: shared USkeleton/body/wardrobe leader-pose compatibility, retarget and LOD/bone-reduction checks.',
        'Target-platform frame cost, skinning influence, animation budget and packaged proof.'
    ],'terminals':[]}
for row in reach['chains']:
    bone=row['tip'];head=np.array(row['head_m']);forward=np.array(row['forward_unit'])
    if bone not in hierarchy or row['previous']!=hierarchy[bone]['parent']:
        raise RuntimeError('Terminal parent evidence differs')
    if np.linalg.norm(head-np.array(hierarchy[bone]['p']))>1e-8 or abs(np.linalg.norm(forward)-1)>1e-8:
        raise RuntimeError('Invalid head/direction evidence')
    dom=row['sets']['dominant']['all'];quarter=row['sets']['weight_gt_0_25']['all']
    length_cm=max(dom['forward_cm']['p95'],quarter['forward_cm']['p95'])
    max_cm=max(dom['forward_cm']['max'],quarter['forward_cm']['max'])
    if not 3<length_cm<=max_cm<30:raise RuntimeError('Unexpected reach; review instead of extrapolating')
    virtual='DIAG_terminal_'+bone.removeprefix('c_kilt_')
    candidate['terminals'].append({'name':virtual,'existing_parent_tip':bone,'existing_previous':row['previous'],
        'head_m':head.tolist(),'forward_unit':forward.tolist(),
        'candidate_p95_length_cm':length_cm,'measured_max_length_cm':max_cm,
        'candidate_endpoint_m':(head+forward*length_cm/100).tolist(),
        'maximum_envelope_endpoint_m':(head+forward*max_cm/100).tolist(),
        'current_3cm_endpoint_m':(head+forward*.03).tolist(),
        'dominant_vertex_count':dom['points'],'weight_gt_0_25_vertex_count':quarter['points'],
        'dominant_forward_cm':dom['forward_cm'],'weight_gt_0_25_forward_cm':quarter['forward_cm'],
        'lateral_span_u_cm':dom['lateral_span_u_cm'],'lateral_span_v_cm':dom['lateral_span_v_cm'],
        'imported_axis_dot_forward':row['normalized_matrix_axis_dot_forward'],
        'layer_reach':{k:{'points':v['points'],'p95_cm':v['forward_cm']['p95'],'max_cm':v['forward_cm']['max']}
                       for k,v in row['sets']['weight_gt_0_25']['layers'].items()},
        'weighted_to_candidate':False})
skinpoints=np.array(skin['positions_m'])
for t in candidate['terminals']:
    p=np.array(t['candidate_endpoint_m']);distances=np.linalg.norm(skinpoints-p,axis=1);i=int(np.argmin(distances))
    t['candidate_endpoint_to_nearest_skin_cm']=float(distances[i]*100)
    t['nearest_skin_point']={'i':i,'p_m':skinpoints[i].tolist()}
candidate['max_endpoint_to_nearest_skin_cm']=max(t['candidate_endpoint_to_nearest_skin_cm'] for t in candidate['terminals'])
candidate['candidate_length_range_cm']=[min(t['candidate_p95_length_cm'] for t in candidate['terminals']),max(t['candidate_p95_length_cm'] for t in candidate['terminals'])]
candidate['maximum_measured_reach_cm']=max(t['measured_max_length_cm'] for t in candidate['terminals'])
candidate['dominant_only_p95_max_cm']=max(t['dominant_forward_cm']['p95'] for t in candidate['terminals'])
candidate['weight_gt_0_25_only_p95_max_cm']=max(t['weight_gt_0_25_forward_cm']['p95'] for t in candidate['terminals'])

# Optional native body readback supersedes the original imported-axis caveat.
# Keep this evidence separate from the10 source preservation gates and from
# runtime dynamics. The body response hash is linked by the verification JSON.
native_paths=[HERE/'native_body_tip_reference.json',HERE/'native_tip_axis_verification.json']
native_before={p.name:sha(p) for p in native_paths if p.exists()}
native_evidence={'status':'UNVERIFIED','passed':False,'scope':'NATIVE_REFERENCE_POSE_ONLY',
                 'runtime_dynamics_proven':False,'input_hashes':native_before,'gates':{}}
if all(p.exists() for p in native_paths):
    native_body=json.loads(native_paths[0].read_text(encoding='utf-8'))
    native_check=json.loads(native_paths[1].read_text(encoding='utf-8'))
    rows={r['name']:r for r in native_check.get('terminals',[])}
    native_bones={r['name']:r for r in native_body.get('bones',[])}
    expected_tips={t['existing_parent_tip'] for t in candidate['terminals']}
    axis_gates={
        'body_response_hash_matches_verification':native_check.get('source_sha256')==native_before[native_paths[0].name],
        'exact_body_asset_and_skeletal_mesh_source':native_body.get('asset_path')=='/Game/Melodia/Characters/Melusina/Outfits/V2/SK_Melusina_V2_Body' and native_body.get('source_type')=='SkeletalMesh' and native_body.get('bone_count')==465,
        'all16_tip_rows_resolved':len(rows)==16 and set(rows)==expected_tips and expected_tips.issubset(native_bones),
        'all16_native_parents_match_proposal':all(rows.get(t['existing_parent_tip'],{}).get('parent')==t['existing_previous'] and native_bones.get(t['existing_parent_tip'],{}).get('parent_name')==t['existing_previous'] for t in candidate['terminals']),
        'all16_native_minus_y_aligned':all(rows.get(n,{}).get('axis_angle_degrees',{}).get('Y_Negative',180)<.001 for n in expected_tips),
        'all16_current_native_x_is_transverse':all(abs(rows.get(n,{}).get('axis_angle_degrees',{}).get('X_Positive',0)-90)<.001 for n in expected_tips),
        'native_verification_passed':native_check.get('passed') is True and all(native_check.get('gates',{}).values())}
    axis_gates={k:bool(v) for k,v in axis_gates.items()}
    native_evidence.update({'passed':all(axis_gates.values()),'gates':axis_gates,
        'status':'VERIFIED_NATIVE_REFERENCE_POSE_ONLY' if all(axis_gates.values()) else 'NATIVE_EVIDENCE_FAILED',
        'asset_path':native_body.get('asset_path'),'source_api':native_check.get('source_api'),
        'source_schema':native_check.get('schema'),'production_baseline_axis':native_check.get('production_baseline_axis'),
        'measured_terminal_axis':native_check.get('measured_terminal_axis'),
        'native_x_angle_range_degrees':native_check.get('native_x_angle_range_degrees'),
        'native_minus_y_angle_max_degrees':native_check.get('native_minus_y_angle_max_degrees')})
    if native_evidence['passed']:
        candidate['native_axis_status']='VERIFIED_NATIVE_REFERENCE_POSE_ONLY: all16 terminals align Y_Negative; current X_Positive is transverse. Runtime Kawaii dynamics remain pending.'
        candidate['production_gates_pending'][0]='Integrate the verified native Y_Negative axis into one bounded Kawaii candidate and prove runtime behavior; reference-pose axis proof alone does not certify dynamics.'
        for t in candidate['terminals']:
            r=rows[t['existing_parent_tip']]
            t['native_body_axis_evidence']={'best_axis':r['best_axis'],'component_head_cm':r['component_head_cm'],
                'parent_component_head_cm':r['parent_component_head_cm'],'chain_direction':r['chain_direction'],
                'component_axes':r['component_axes'],'axis_angle_degrees':r['axis_angle_degrees'],
                'axis_dot_chain':r['axis_dot_chain'],'proof_scope':'NATIVE_REFERENCE_POSE_ONLY'}
candidate['native_axis_evidence']=native_evidence

# A named wire proxy is sufficient to inspect in any DCC. Existing chain curves,
# current3cm stubs, p95 extensions and measured maxima are separate OBJ groups.
obj=['# Melusina DIAGNOSTIC terminal support proxy; not a production skeletal mesh.',
     '# Units: metres. Up: +Y. Source character geometry is not included or edited.']
obj_positions=[];obj_lines=[]
def line(name,a,b):
    obj.append('g '+name)
    for p in (a,b):obj.append('v '+' '.join(f'{float(v):.10f}' for v in p));obj_positions.append(list(map(float,p)))
    i=len(obj_positions)-1;obj.append(f'l {i} {i+1}');obj_lines.append([i,i+1])
def marker(name,center,radius=.003):
    c=np.array(center)
    for axis in range(3):
        d=np.zeros(3);d[axis]=radius;line(name+f'_axis{axis}',c-d,c+d)
for t in candidate['terminals']:
    line('EXISTING_last_segment_'+t['existing_parent_tip'],hierarchy[t['existing_previous']]['p'],t['head_m'])
    line('CURRENT_3cm_'+t['name'],t['head_m'],t['current_3cm_endpoint_m'])
    line('CANDIDATE_p95_'+t['name'],t['head_m'],t['candidate_endpoint_m'])
    line('MEASURED_max_'+t['name'],t['candidate_endpoint_m'],t['maximum_envelope_endpoint_m'])
    marker('CANDIDATE_endpoint_'+t['name'],t['candidate_endpoint_m'])
    marker('MAX_envelope_'+t['name'],t['maximum_envelope_endpoint_m'],.002)
obj_path=HERE/'skirt_terminal_support_proxy_candidate.obj'
obj_path.write_text('\n'.join(obj)+'\n',encoding='utf-8')

# Technical-art figure: orthographic evidence, not a rendered production pose.
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9})
fig,axs=plt.subplots(1,3,figsize=(15,7),gridspec_kw={'width_ratios':[1,1,.85]},constrained_layout=True)
fig.patch.set_facecolor('#111722')
for ax in axs:ax.set_facecolor('#111722');ax.tick_params(colors='#b9c6d8');ax.spines[['right','top']].set_visible(False)
for ax in axs:
    for spine in ax.spines.values():spine.set_color('#495366')
    ax.xaxis.label.set_color('#b9c6d8');ax.yaxis.label.set_color('#b9c6d8');ax.title.set_color('#e7edf6')
positions=np.array(skin['positions_m'])*100
for ax,horizontal,title in [(axs[0],0,'FRONT  /  existing rig + endpoint proposal'),(axs[1],2,'PROFILE  /  measured support reach')]:
    # Fixed stride merely reduces plot overdraw; no geometry is modified.
    ax.scatter(positions[::7,horizontal],positions[::7,1],s=.45,c='#46556e',alpha=.28,rasterized=True)
    for side in ['l','r']:
        for chain in range(1,9):
            chainpts=np.array([hierarchy[f'c_kilt_{chain:02d}_{row:02d}_{side}']['p'] for row in range(1,5)])*100
            ax.plot(chainpts[:,horizontal],chainpts[:,1],c='#7c91b5',lw=.65,alpha=.6)
    for t in candidate['terminals']:
        h=np.array(t['head_m'])*100;p=np.array(t['candidate_endpoint_m'])*100;m=np.array(t['maximum_envelope_endpoint_m'])*100;c=np.array(t['current_3cm_endpoint_m'])*100
        ax.plot([h[horizontal],p[horizontal]],[h[1],p[1]],c='#53d1d7',lw=1.4)
        ax.plot([h[horizontal],c[horizontal]],[h[1],c[1]],c='#f5b45b',lw=2.3)
        ax.plot([p[horizontal],m[horizontal]],[p[1],m[1]],c='#d57a9b',lw=1,ls=':')
        ax.scatter(p[horizontal],p[1],s=10,c='#53d1d7',edgecolors='none')
    ax.set_aspect('equal');ax.set_title(title,fontsize=10,pad=16);ax.set_xlabel(('Left / right' if horizontal==0 else 'Depth')+' (cm)');ax.set_ylabel('Height (cm)');ax.grid(alpha=.1,color='#b9c6d8')
ax=axs[2];labels=[t['existing_parent_tip'].removeprefix('c_kilt_').removesuffix('_l').removesuffix('_r')+' '+t['existing_parent_tip'][-1].upper() for t in candidate['terminals']]
values=[t['candidate_p95_length_cm'] for t in candidate['terminals']];maximum=[t['measured_max_length_cm'] for t in candidate['terminals']]
ax.barh(range(16),values,color='#53d1d7',alpha=.8,height=.6)
ax.scatter(maximum,range(16),c='#d57a9b',s=15,zorder=3,label='Measured maximum')
ax.axvline(3,c='#f5b45b',lw=1.3,label='Current 3 cm')
ax.set_yticks(range(16),labels);ax.invert_yaxis();ax.set_xlabel('Tip-forward distance (cm)');ax.set_title('16 TERMINALS  /  max(dominant p95, >0.25 p95)',fontsize=9,pad=16);ax.grid(axis='x',alpha=.1,color='#b9c6d8')
leg=ax.legend(loc='lower right',fontsize=8,facecolor='#111722',edgecolor='#495366')
for text in leg.get_texts():text.set_color('#dbe6f4')
fig.suptitle('MELUSINA  /  SKIRT TERMINAL SUPPORT STUDY',color='#e7edf6',fontsize=18,fontweight='bold')
axis_caption='Native UE ref pose: Y Negative (16/16); X Positive transverse; runtime dynamics pending' if native_evidence['passed'] else 'KineFX +Y observed; native Unreal axis unverified'
fig.supxlabel('AXIAL PROXY, NOT COLLISION BOUNDS  •  0 canonical bone / vertex / weight changes  •  '+axis_caption,color='#b9c6d8',fontsize=9)
fig.savefig(HERE/'skirt_terminal_support_proxy_breakdown.png',dpi=180,facecolor=fig.get_facecolor())
fig.savefig(HERE/'skirt_terminal_support_proxy_breakdown.svg',facecolor=fig.get_facecolor())
plt.close(fig)

after={p.name:sha(p) for p in SOURCES}
native_after={p.name:sha(p) for p in native_paths if p.exists()}
native_evidence['input_hashes_after']=native_after
native_evidence['input_hashes_unchanged']=native_before==native_after
geometry_keys=['name','existing_parent_tip','existing_previous','head_m','forward_unit','candidate_p95_length_cm',
               'measured_max_length_cm','candidate_endpoint_m','maximum_envelope_endpoint_m','current_3cm_endpoint_m']
geometry_payload=lambda c:[{k:t[k] for k in geometry_keys} for t in c['terminals']]
regeneration={'prior_artifacts_present':previous_candidate is not None,
    'prior_obj_sha256':previous_obj_hash,'regenerated_obj_sha256':sha(obj_path),
    'same_obj_geometry':previous_obj_hash is None or previous_obj_hash==sha(obj_path),
    'same_terminal_geometry_and_lengths':previous_candidate is None or geometry_payload(previous_candidate)==geometry_payload(candidate)}
if not regeneration['same_obj_geometry'] or not regeneration['same_terminal_geometry_and_lengths']:
    raise RuntimeError('Native evidence update unexpectedly changed candidate geometry or lengths')
gates={'pinned_source_fbx':before[SOURCES[0].name]==PINNED_FBX,
    'all_source_inputs_hash_unchanged':before==after,
    'canonical465_joint_names_and_transforms_untouched':before[SOURCES[2].name]==after[SOURCES[2].name],
    'skirt30509_vertices_and_weights_untouched':before[SOURCES[3].name]==after[SOURCES[3].name],
    'exactly16_unique_virtual_terminals':len(candidate['terminals'])==16 and len({t['name'] for t in candidate['terminals']})==16,
    'all_existing_tip_parents_resolve':all(t['existing_parent_tip'] in hierarchy for t in candidate['terminals']),
    'all_lengths_positive_and_within_measured_max':all(0<t['candidate_p95_length_cm']<=t['measured_max_length_cm'] for t in candidate['terminals']),
    'all_endpoints_follow_measured_unit_direction':all(np.linalg.norm((np.array(t['candidate_endpoint_m'])-t['head_m'])-np.array(t['forward_unit'])*t['candidate_p95_length_cm']/100)<1e-10 for t in candidate['terminals']),
    'proxy_obj_finite_geometry':all(math.isfinite(x) for p in obj_positions for x in p),
    'no_production_skeleton_or_weights_created':candidate['canonical_joint_changes']==candidate['skinning_weight_changes']==0}
gates={k:bool(v) for k,v in gates.items()}
candidate_path=HERE/'skirt_terminal_support_proxy_candidate.json'
candidate_path.write_text(json.dumps(candidate,indent=1),encoding='utf-8')
checks={'schema':'melodia.skirt_terminal_support_proxy_gate.v1','passed':all(gates.values()),'gates':gates,
    'input_hashes_before':before,'input_hashes_after':after,
    'artifact_hashes':{p.name:sha(p) for p in [candidate_path,obj_path,HERE/'skirt_terminal_support_proxy_breakdown.png',HERE/'skirt_terminal_support_proxy_breakdown.svg']},
    'proxy_geometry':{'vertices':len(obj_positions),'lines':len(obj_lines)},
    'native_axis_evidence':native_evidence,'regeneration_preservation':regeneration,
    'proof_scope':'OFFLINE_SOURCE_AND_DIAGNOSTIC_ARTIFACT_ONLY',
    'runtime_certification':False,'portfolio_final_acceptance':False}
(HERE/'skirt_terminal_support_proxy_gate.json').write_text(json.dumps(checks,indent=1),encoding='utf-8')
print(json.dumps({'passed':checks['passed'],'gates':gates,'terminal_length_range_cm':candidate['candidate_length_range_cm'],
    'maximum_measured_reach_cm':candidate['maximum_measured_reach_cm'],'proxy_geometry':checks['proxy_geometry']},indent=1))
