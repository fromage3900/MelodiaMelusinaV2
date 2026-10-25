"""Measured skirt-chain tip reach and leg influence locations; no source edits."""
import collections
import hashlib
import json
import math
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
data=json.loads((HERE/'SK_Melusina_V2_Skirt_R2_SmoothChains_data.json').read_text())
hier=json.loads((HERE/'skeleton_hierarchy.json').read_text())[2]['joints']
points=np.array(data['positions_m'])
weights=[dict(x) for x in data['weights']]
parent=list(range(len(points)))
def find(a):
    while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
    return a
def union(a,b):
    a,b=find(a),find(b)
    if a!=b:parent[b]=a
for prim in data['primitive_ids']:
    for i in prim[1:]:union(prim[0],i)
islands=collections.defaultdict(list)
for i in range(len(parent)):islands[find(i)].append(i)
groups=sorted(islands.values(),key=len,reverse=True)
layer_of={v:i for i,ids in enumerate(groups) for v in ids}
dominant=[max(w,key=w.get) if w else None for w in weights]

def summarize(ids,head,direction,axis_u,axis_v):
    if not ids:return None
    positions=points[ids]-head
    forward=positions@direction
    u,v=positions@axis_u,positions@axis_v
    radial=np.sqrt(u*u+v*v)
    q=np.quantile(forward,[0,.5,.95,1])*100
    return {'points':len(ids),'forward_cm':dict(zip(['min','p50','p95','max'],q.tolist())),
        'positive_forward_points':int(np.sum(forward>0)),
        'lateral_u_range_cm':[float(u.min()*100),float(u.max()*100)],
        'lateral_v_range_cm':[float(v.min()*100),float(v.max()*100)],
        'lateral_span_u_cm':float(np.ptp(u)*100),'lateral_span_v_cm':float(np.ptp(v)*100),
        'lateral_radial_p95_max_cm':[float(np.quantile(radial,.95)*100),float(radial.max()*100)],
        'furthest_point_index':int(ids[np.argmax(forward)]),'furthest_point_m':points[ids[np.argmax(forward)]].tolist()}

report={'schema':'melodia.skirt_tip_reach.v1','source':'SourceExports/SK_Melusina_V2_Skirt_R2_SmoothChains.fbx',
    'source_sha256':hashlib.sha256((HERE.parent/'SourceExports/SK_Melusina_V2_Skirt_R2_SmoothChains.fbx').read_bytes()).hexdigest(),
    'coordinates':'KineFX imported world metres; Y-up; signed forward uses previous-head to tip-head normalized direction.',
    'axis_scope':'KineFX imported transform row axes; these do not independently certify native UE BoneForwardAxis because FBX import may convert bone axes.',
    'layers':[{'layer':i,'kind':'large_hem_island' if i<3 else 'panel_or_trim_island','points':len(ids),
               'sample_ids':ids[:3],'bounds_m':{'min':points[ids].min(axis=0).tolist(),'max':points[ids].max(axis=0).tolist()}} for i,ids in enumerate(groups)],
    'chains':[]}
for side in ['l','r']:
    for chain in range(1,9):
        name=f'c_kilt_{chain:02d}_04_{side}'
        h=np.array(hier[name]['p']);prev_name=hier[name]['parent'];prev=np.array(hier[prev_name]['p'])
        vector=h-prev;direction=vector/np.linalg.norm(vector)
        # Orthogonal lateral basis: begin with imported local X projected off forward.
        matrix=np.array(hier[name]['transform']).reshape(3,3)
        rowlengths=np.linalg.norm(matrix,axis=1);rows=matrix/rowlengths[:,None]
        axis_u=rows[0]-np.dot(rows[0],direction)*direction;axis_u/=np.linalg.norm(axis_u)
        axis_v=np.cross(direction,axis_u);axis_v/=np.linalg.norm(axis_v)
        row={'tip':name,'previous':prev_name,'head_m':h.tolist(),'previous_head_m':prev.tolist(),
             'head_minus_previous_m':vector.tolist(),'previous_minus_head_m':(-vector).tolist(),
             'forward_unit':direction.tolist(),'last_segment_length_cm':float(np.linalg.norm(vector)*100),
             'imported_matrix_rows':matrix.tolist(),'matrix_axis_scale':rowlengths.tolist(),
             'normalized_matrix_axis_dot_forward':dict(zip(['X','Y','Z'],(rows@direction).tolist())),
             'lateral_basis_u':axis_u.tolist(),'lateral_basis_v':axis_v.tolist(),'sets':{}}
        for label,ids in [('dominant',[i for i,n in enumerate(dominant) if n==name]),
                          ('weight_gt_0_25',[i for i,w in enumerate(weights) if w.get(name,0)>.25])]:
            bylayer=collections.defaultdict(list)
            for i in ids:bylayer[layer_of[i]].append(i)
            row['sets'][label]={'all':summarize(ids,h,direction,axis_u,axis_v),
                'layers':{str(layer):summarize(lids,h,direction,axis_u,axis_v) for layer,lids in sorted(bylayer.items())}}
        report['chains'].append(row)

leg_tokens=('thigh','leg_','foot','toes')
legweights=[{n:w for n,w in prs.items() if any(t in n for t in leg_tokens)} for prs in weights]
legids=[i for i,prs in enumerate(legweights) if any(w>.01 for w in prs.values())]
report['leg_weighted_points']={'selection':'Any individual anatomical leg influence > 0.01 (same 226-point source cohort).',
    'count':len(legids),'layers':[],
    'indexed_cohort':[{'i':i,'layer':layer_of[i],'p_m':points[i].tolist(),'leg_weights':legweights[i],
                       'total_leg_weight':sum(legweights[i].values())} for i in legids]}
report['leg_weighted_points']['height_bands']=[]
for label,ids in [('below_50cm',[i for i in legids if points[i,1]<.5]),
                  ('50_to_75cm',[i for i in legids if .5<=points[i,1]<=.75]),
                  ('above_75cm',[i for i in legids if points[i,1]>.75])]:
    report['leg_weighted_points']['height_bands'].append({'band':label,'count':len(ids),
        'max_total_leg_weight':max((sum(legweights[i].values()) for i in ids),default=0),
        'layers':dict(collections.Counter(layer_of[i] for i in ids))})
for layer,ids in enumerate(groups):
    ids=[i for i in ids if i in legids]
    if not ids:continue
    totals=np.array([sum(legweights[i].values()) for i in ids]);single=np.array([max(legweights[i].values()) for i in ids])
    bybone=collections.Counter()
    for i in ids:
        for n,w in legweights[i].items():
            if w>.01:bybone[n]+=1
    lowest=sorted(ids,key=lambda i:points[i,1])[:5]
    maxid=ids[int(np.argmax(totals))]
    report['leg_weighted_points']['layers'].append({'layer':layer,'island_points':len(groups[layer]),
        'count':len(ids),'y_range_cm':[float(points[ids,1].min()*100),float(points[ids,1].max()*100)],
        'max_single_leg_weight':float(single.max()),'max_total_leg_weight':float(totals.max()),
        'total_leg_weight_p50_p95':np.quantile(totals,[.5,.95]).tolist(),'leg_bones_point_counts':dict(bybone),
        'lowest_samples':[{'i':i,'p_m':points[i].tolist(),'all_weights':weights[i],'total_leg_weight':sum(legweights[i].values())} for i in lowest],
        'max_leg_sample':{'i':maxid,'p_m':points[maxid].tolist(),'weights':weights[maxid]},
        'points_below_y_0_5m':int(np.sum(points[ids,1]<.5)),'points_above_y_0_75m':int(np.sum(points[ids,1]>.75))})

reach=[(row['tip'],row['sets']['dominant']['all']['forward_cm']['p95'],row['sets']['dominant']['all']['forward_cm']['max']) for row in report['chains'] if row['sets']['dominant']['all']]
report['dummy_reach_measurement']={'current_dummy_cm':3.0,'dominant_set_tip_p95_max_cm':reach,
    'global_max_forward_cm':max(x[2] for x in reach), 'max_of_tip_p95_cm':max(x[1] for x in reach),
    'interpretation':'Geometric overhang only. A global dummy length near the largest p95/max covers most/all dominant skin reach if native UE axis is proven; it is not a validated physics tune. Per-tip reach is asymmetric.',
    'maximum_only_is_not_collision_radius':True}
(HERE/'skirt_tip_reach.json').write_text(json.dumps(report,indent=1),encoding='utf-8')
print('TIP_REACH',json.dumps(report['dummy_reach_measurement']))
print('LEG_LAYER_COUNTS',[(x['layer'],x['count'],x['y_range_cm'],x['max_total_leg_weight'],x['points_below_y_0_5m']) for x in report['leg_weighted_points']['layers']])
print('AXIS_DOTS',[(r['tip'],r['normalized_matrix_axis_dot_forward']) for r in report['chains']])
