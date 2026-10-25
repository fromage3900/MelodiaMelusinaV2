"""Summarize the measured KineFX import; no source or editor mutations."""
from __future__ import annotations
import collections
import json
import math
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

HERE=Path(__file__).resolve().parent
base=json.loads((HERE/'contact_geometry.json').read_text())
data=[json.loads((HERE/(Path(x['path']).stem+'_data.json')).read_text()) for x in base['files']]

def bands(d):
    values=[sum(w for n,w in p if 'kilt' in n) for p in d['weights']]
    opp=[]
    for pos,prs in zip(d['positions_m'],d['weights']):
        suffix='_r' if pos[0]>.005 else '_l' if pos[0]<-.005 else None
        opp.append(sum(w for n,w in prs if suffix and n.endswith(suffix)))
    return {'kilt_points_any':sum(x>1e-6 for x in values),
            'kilt_points_over_1pct':sum(x>.01 for x in values),'kilt_max_weight':max(values),
            'opposite_side_points_over_1pct':sum(x>.01 for x in opp),'opposite_side_max_weight':max(opp)}

def pt(d,i): return {'index':int(i),'position_m':d['positions_m'][i],'weights':d['weights'][i]}

report={'schema':'melodia.leg_skirt_contact_summary.v1',
        'provenance':[{'file':x['path'],'sha256':x['sha256'],'points':x['points'],'joints':x['joints']} for x in base['files']],
        'axes':'Houdini metres; Y is vertical. UE Z = Houdini Y * 100.',
        'contact_qualification':'Rest/bind geometry evidence only. Runtime poses and collision contact require parent runtime measurements.',
        'body':bands(data[0]),'boots':bands(data[1]),'skirt':bands(data[2])}

body,boots,skirt=data
for label,d in [('body',body),('boots',boots)]:
    p=np.array(d['positions_m'])
    report[label]['lowest_bind_point']=pt(d,int(np.argmin(p[:,1])))
    report[label]['feet']={}
    for side,mask in [('l',p[:,0]>.005),('r',p[:,0]<-.005)]:
        ids=np.flatnonzero(mask & (p[:,1]<.15))
        report[label]['feet'][side]={'lowest_point':pt(d,int(ids[np.argmin(p[ids,1])])),
            'y_quantiles_cm':dict(zip(['min','p01','p05','p50'],(np.quantile(p[ids,1],[0,.01,.05,.5])*100).tolist()))}

report['boots']['bind_min_below_barefoot_cm']=(min(p[1] for p in body['positions_m'])-min(p[1] for p in boots['positions_m']))*100
report['bind_skeleton_comparison']={}
for label,d in [('boots',boots),('skirt',skirt)]:
    used={n for p in d['weights'] for n,w in p if w>1e-6}
    deltas=sorted([(math.dist(body['joints_m'][n],p)*100,n) for n,p in d['joints_m'].items()],reverse=True)
    report['bind_skeleton_comparison'][label]={'names_equal':list(body['joints_m'])==list(d['joints_m']),
        'all_joints_max_pos_delta_cm':deltas[0], 'weighted_joints_max_pos_delta_cm':next(x for x in deltas if x[1] in used),
        'kilt_max_pos_delta_cm':max(x for x in deltas if 'kilt' in x[1]),
        'largest_10_pos_deltas_cm':deltas[:10]}

# Topological islands from the KineFX import. Large boot shells and thin bottom faces
# are separately listed so an ornament cannot be mistaken for the support sole.
report['boots']['contact_islands']=[]
for isl in base['files'][1]['islands']:
    if isl['bounds_m']['min'][1]<-.22:
        report['boots']['contact_islands'].append(isl)
report['skirt']['island_point_counts']=[x['point_count'] for x in base['files'][2]['islands']]
report['skirt']['weighted_bones']=sorted({n for prs in skirt['weights'] for n,w in prs if w>1e-6})
report['skirt']['kilt_bones_present']=sorted(n for n in skirt['joints_m'] if 'kilt' in n)
report['skirt']['leg_bound_points']=sum(any(any(t in n for t in ['thigh','leg_','foot','toes']) and w>.01 for n,w in prs) for prs in skirt['weights'])

# Main hem layers are the three large disconnected islands. Isolated panel shells
# are left distinct; Kawaii chains do not imply independently simulated cloth layers.
prims=skirt['primitive_ids']; parent=list(range(len(skirt['positions_m'])))
def find(a):
    while a!=parent[a]: parent[a]=parent[parent[a]]; a=parent[a]
    return a
def union(a,b):
    a,b=find(a),find(b)
    if a!=b: parent[b]=a
for prim in prims:
    for i in prim[1:]: union(prim[0],i)
islands=collections.defaultdict(list)
for i in range(len(parent)): islands[find(i)].append(i)
groups=sorted(islands.values(),key=len,reverse=True)
sp=np.array(skirt['positions_m'])
report['skirt']['hem_layers']=[]
for i,ids in enumerate(groups[:3]):
    tally=collections.Counter()
    for v in ids:
        for n,w in skirt['weights'][v]: tally[n]+=w
    report['skirt']['hem_layers'].append({'island':i,'points':len(ids),'sample_ids':ids[:3],
        'bind_y_minmax_cm':(np.array([sp[ids,1].min(),sp[ids,1].max()])*100).tolist(),
        'kilt_influence_sum':sum(w for n,w in tally.items() if 'kilt' in n),
        'non_kilt_influence_sum':sum(w for n,w in tally.items() if 'kilt' not in n)})
report['skirt']['hem_pair_nearest_vertex_dist_cm']=[]
for a,b in [(0,1),(0,2),(1,2)]:
    dist,idx=cKDTree(sp[groups[b]]).query(sp[groups[a]])
    coincident=[]
    for ai in np.flatnonzero(dist<1e-7):
        wa=dict(skirt['weights'][groups[a][ai]])
        wb=dict(skirt['weights'][groups[b][idx[ai]]])
        coincident.append(sum(abs(wa.get(n,0)-wb.get(n,0)) for n in wa.keys()|wb.keys()))
    report['skirt']['hem_pair_nearest_vertex_dist_cm'].append({'a':a,'b':b,'min':float(dist.min()*100),'p05':float(np.quantile(dist,.05)*100),'median':float(np.median(dist)*100),
        'coincident_points':len(coincident),'coincident_weights_l1_max':max(coincident,default=0)})

hierarchy_file=HERE/'skeleton_hierarchy.json'
if hierarchy_file.exists():
    hierarchy=json.loads(hierarchy_file.read_text())
    hb=hierarchy[0]['joints']
    report['bind_skeleton_comparison']['boots']['matrix3x3_max_element_delta']=max(abs(a-c) for n,v in hierarchy[1]['joints'].items() for a,c in zip(hb[n]['transform'],v['transform']))
    used={n for prs in skirt['weights'] for n,w in prs if w>1e-6}
    report['bind_skeleton_comparison']['skirt']['weighted_matrix3x3_max_element_delta']=max(abs(a-c) for n,v in hierarchy[2]['joints'].items() if n in used for a,c in zip(hb[n]['transform'],v['transform']))
    chains=[]
    for side in ['l','r']:
        for radial in range(1,9):
            names=[f'c_kilt_{radial:02d}_{row:02d}_{side}' for row in range(1,5)]
            chains.append({'names':names,'parent':hb[names[0]]['parent'],
                           'start_y_cm':hb[names[0]]['p'][1]*100,'tip_y_cm':hb[names[-1]]['p'][1]*100,
                           'chain_length_cm':sum(math.dist(hb[a]['p'],hb[b]['p'])*100 for a,b in zip(names,names[1:]))})
    report['skirt']['radial_chains']=chains
    report['skirt']['root_level_kilt_main_controls']=[n for n,v in hb.items() if n.startswith('c_kilt_main_') and v['parent']=='root']
    report['skirt']['real_radial_chain_count']=len(chains)
    report['skirt']['central_row_chain']=[{'name':n,'parent':hb[n]['parent']} for n in hb if n.startswith('c_kilt_row_')]
    report['ground_reference']={'c_traj_parent':hb['c_traj']['parent'],
        'c_traj_direct_children':[n for n,v in hb.items() if v['parent']=='c_traj'],
        'c_traj_bind_position_m':hb['c_traj']['p'],
        'footwear_plane_caution':'Use true heel/forefoot support; preserve all direct-child world matrices. Fix boot kilt and opposite-leg leakage before final contact measurement. Bind plane differs from source animation plane.'}

# Orthographic scientific plot of the actual bind meshes; black support triangles
# distinguish sole geometry from upper shell, while crimson marks kilt leakage.
fig,axs=plt.subplots(1,3,figsize=(15,6),constrained_layout=True)
bp=np.array(body['positions_m'])*100; fp=np.array(boots['positions_m'])*100
footmask=(bp[:,0]>.005*100)&(bp[:,1]<15)
for ax,dim,title in [(axs[0],2,'Left boot side: actual bind geometry'),(axs[1],0,'Front: both boots and barefoot skin')]:
    mask=fp[:,0]>.5 if dim==2 else np.ones(len(fp),dtype=bool)
    ax.scatter(bp[footmask,dim],bp[footmask,1],s=2,c='#69a7c4',alpha=.65,label='Barefoot skin')
    segments=[]
    for tri in boots['primitive_ids']:
        if mask[tri].all():
            q=fp[tri][:,[dim,1]]
            for j in range(len(q)): segments.append([q[j],q[(j+1)%len(q)]])
    ax.add_collection(LineCollection(segments,colors='#5d6070',linewidths=.25,alpha=.35))
    kw=np.array([sum(w for n,w in prs if 'kilt' in n) for prs in boots['weights']])
    bad=mask & (kw>1e-6)
    ax.scatter(fp[bad,dim],fp[bad,1],s=7,c='#cf3450',label='Kilt-weighted boot vertices')
    ax.axhline(-23.8570645,c='#3c8449',lw=1,linestyle='--',label='Lowest modeled heel')
    ax.set_aspect('equal');ax.autoscale();ax.set_title(title,fontsize=10);ax.set_xlabel(('Depth' if dim==2 else 'Left/right')+' (cm)');ax.set_ylabel('Height (cm)');ax.grid(alpha=.2)
axs[0].legend(fontsize=8)
for i,ids in enumerate(groups[:3]): axs[2].scatter(sp[ids,2]*100,sp[ids,1]*100,s=1,alpha=.45,label=f'Hem island {i}: {len(ids)} points')
axs[2].set_aspect('equal');axs[2].set_title('Skirt hem: three separate geometry layers',fontsize=10);axs[2].set_xlabel('Depth (cm)');axs[2].set_ylabel('Height (cm)');axs[2].legend(fontsize=8);axs[2].grid(alpha=.2)
fig.suptitle('Fresh Unreal exports via KineFX — bind geometry, not runtime contact',fontsize=12)
fig.savefig(HERE/'bind_contact_debug.png',dpi=150);plt.close(fig)
(HERE/'contact_summary.json').write_text(json.dumps(report,indent=1),encoding='utf-8')
print(json.dumps({'boots':report['boots'],'bind_skeleton_comparison':report['bind_skeleton_comparison'],
                  'skirt_hem_layers':report['skirt']['hem_layers'], 'hem_clearance':report['skirt']['hem_pair_nearest_vertex_dist_cm']},indent=1))
