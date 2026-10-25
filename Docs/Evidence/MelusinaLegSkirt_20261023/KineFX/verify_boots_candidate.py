"""KineFX roundtrip gate for the duplicate boot weight-only candidate."""
from __future__ import annotations
import collections
import hashlib
import json
import math
import itertools
from pathlib import Path
import numpy as np
import hou

class cKDTree:
    """Tiny spatial hash fallback: Houdini's embedded Python has no SciPy."""
    def __init__(self,positions):
        self.positions=np.array(positions);self.cells=collections.defaultdict(list)
        for i,p in enumerate(positions):self.cells[tuple(int(math.floor(x/1e-5)) for x in p)].append(i)
    def query_ball_point(self,p,r):
        cell=tuple(int(math.floor(x/1e-5)) for x in p);ids=[]
        for offset in itertools.product([-1,0,1],repeat=3):
            ids.extend(self.cells.get(tuple(a+b for a,b in zip(cell,offset)),[]))
        return [i for i in ids if np.linalg.norm(self.positions[i]-p)<=r]
    def query(self,positions):
        d=[];idx=[]
        for p in positions:
            ids=self.query_ball_point(p,2e-5)
            if not ids:ids=range(len(self.positions))
            ids=np.array(list(ids));ds=np.linalg.norm(self.positions[ids]-p,axis=1);j=int(np.argmin(ds))
            d.append(ds[j]);idx.append(ids[j])
        return np.array(d),np.array(idx)

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'SourceExports/SK_Melusina_V2_Boots.fbx'
CAND=HERE/'SK_Melusina_V2_Boots_WeightClean_Candidate.fbx'
def load(path):
    hou.hipFile.clear(suppress_save_prompt=True)
    obj=hou.node('/obj').createNode('geo','verify_boots')
    imp=obj.createNode('kinefx::fbxcharacterimport','fbx_in')
    imp.parm('fbxfile').set(path.as_posix());imp.parm('convertunits').set(1)
    skin,rest=imp.geometry(0),imp.geometry(1)
    names=[str(p.attribValue('name')) for p in rest.points()]
    joints={p.attribValue('name'):{'position':list(p.position()),'matrix':list(p.attribValue('transform')),'parent':None} for p in rest.points()}
    for prim in rest.prims():
        ids=[v.point().number() for v in prim.vertices()]
        for a,b in zip(ids,ids[1:]):joints[names[b]]['parent']=names[a]
    weights=[]
    for p in skin.points():
        raw=p.attribValue('boneCapture')
        weights.append({names[int(raw[i])]:float(raw[i+1]) for i in range(0,len(raw)-1,2) if raw[i]>=0 and raw[i+1]>1e-6})
    positions=[list(p.position()) for p in skin.points()]
    prims=[[v.point().number() for v in p.vertices()] for p in skin.prims()]
    materials=[str(p.attribValue('fbx_material_name')) for p in skin.prims()]
    return {'positions':positions,'weights':weights,'joints':joints,'primitives':prims,'materials':materials}

s,c=load(SOURCE),load(CAND)
report={'schema':'melodia.boots_weight_candidate_roundtrip.v1','source':SOURCE.as_posix(),'candidate':CAND.as_posix(),
        'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(CAND.read_bytes()).hexdigest()}
parent=list(range(len(s['positions'])))
def find(a):
    while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
    return a
def union(a,b):
    a,b=find(a),find(b)
    if a!=b:parent[b]=a
for tri in s['primitives']:
    for i in tri[1:]:union(tri[0],i)
islands=collections.defaultdict(list)
for i in range(len(parent)):islands[find(i)].append(i)
side={}
for ids in islands.values():
    center=np.mean([s['positions'][i] for i in ids],axis=0)
    dl=np.linalg.norm(center-s['joints']['foot_l']['position']);dr=np.linalg.norm(center-s['joints']['foot_r']['position'])
    if abs(dl-dr)<.001:raise RuntimeError('Ambiguous source island')
    for i in ids:side[i]='l' if dl<dr else 'r'
expected=[]
for i,w in enumerate(s['weights']):
    opp='_r' if side[i]=='l' else '_l'
    kept={n:v for n,v in w.items() if 'kilt' not in n and not n.endswith(opp)}
    total=sum(kept.values())
    expected.append({n:v/total for n,v in kept.items()})
tree=cKDTree(s['positions']);dist,nearest=tree.query(c['positions'])
bad=0;max_w_diff=0;source_map=[]
for j,(pos,prs) in enumerate(zip(c['positions'],c['weights'])):
    candidates=tree.query_ball_point(pos,1e-6)
    if not candidates:bad+=1;continue
    errs=[(max((abs(prs.get(n,0)-expected[i].get(n,0)) for n in prs.keys()|expected[i].keys()),default=0),i) for i in candidates]
    err,i=min(errs);source_map.append(i);max_w_diff=max(max_w_diff,err)
    if err>1e-5:bad+=1
q=lambda p:tuple(round(x,5) for x in p)
def faces(d):
    return collections.Counter((tuple(sorted(q(d['positions'][i]) for i in ids)),mat) for ids,mat in zip(d['primitives'],d['materials']))
shared=set(s['joints'])&set(c['joints'])
report['counts']={'source_points':len(s['positions']),'candidate_points':len(c['positions']),'source_primitives':len(s['primitives']),'candidate_primitives':len(c['primitives']),
                  'source_joints':len(s['joints']),'candidate_joints':len(c['joints'])}
report['geometry']={'max_vertex_nearest_distance_mm':float(dist.max()*1000),'triangles_and_materials_equal_at_0_01mm':faces(s)==faces(c),
                    'material_primitive_counts_source':dict(collections.Counter(s['materials'])),'material_primitive_counts_candidate':dict(collections.Counter(c['materials']))}
report['bind']={'unknown_joints':sorted(set(c['joints'])-set(s['joints'])),'missing_joints':sorted(set(s['joints'])-set(c['joints'])),
    'max_joint_position_delta_mm':max(math.dist(s['joints'][n]['position'],c['joints'][n]['position'])*1000 for n in shared),
    'max_matrix_element_delta':max(abs(a-b) for n in shared for a,b in zip(s['joints'][n]['matrix'],c['joints'][n]['matrix'])),
    'hierarchy_changed':[n for n in shared if s['joints'][n]['parent']!=c['joints'][n]['parent']]}
report['weights']={'candidate_vs_expected_mismatching_points':bad,'max_weight_difference':max_w_diff,
    'kilt_weighted_points':sum(any('kilt' in n for n in prs) for prs in c['weights']),
    'opposite_side_weighted_points':sum(any(n.endswith('_r' if side[i]=='l' else '_l') for n in prs) for i,prs in zip(source_map,c['weights'])),
    'more_than_4_influences':sum(len(prs)>4 for prs in c['weights']), 'unweighted_points':sum(not prs for prs in c['weights']),
    'weight_sums_outside_1e_5':sum(abs(sum(prs.values())-1)>1e-5 for prs in c['weights'])}
report['gate']={'same_vertex_count':len(s['positions'])==len(c['positions']), 'same_topology_and_materials':report['geometry']['triangles_and_materials_equal_at_0_01mm'],
    'no_vertex_drift':dist.max()<1e-5,'same_bone_names':not report['bind']['unknown_joints'] and not report['bind']['missing_joints'],
    'same_hierarchy':not report['bind']['hierarchy_changed'],'same_bind_positions':report['bind']['max_joint_position_delta_mm']<.01,
    'same_bind_matrices':report['bind']['max_matrix_element_delta']<1e-4,
    'weights_exactly_requested':bad==0,'kilt_removed':report['weights']['kilt_weighted_points']==0,
    'opposite_side_removed':report['weights']['opposite_side_weighted_points']==0,
    'normalized_and_nonzero':report['weights']['unweighted_points']==0 and report['weights']['weight_sums_outside_1e_5']==0,
    'at_most_4_influences':report['weights']['more_than_4_influences']==0}
report['gate']={k:bool(v) for k,v in report['gate'].items()}
report['passed']=all(report['gate'].values())
(HERE/'boots_candidate_roundtrip.json').write_text(json.dumps(report,indent=1),encoding='utf-8')
(HERE/'boots_candidate_kinefx_data.json').write_text(json.dumps(c),encoding='utf-8')
print(json.dumps(report,indent=1))
