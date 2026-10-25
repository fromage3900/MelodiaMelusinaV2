"""Weight-only FBX binary-tree rewrite after Blender rig roundtrip failed.

Uses Blender's shipped FBX parser/encoder; never imports the character scene.
Only existing Cluster Indexes/Weights arrays change; no object, bind or mesh edits.
"""
import array
import collections
import hashlib
import json
import math
from pathlib import Path
from io_scene_fbx import parse_fbx, encode_bin

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'SourceExports/SK_Melusina_V2_Boots.fbx'
OUT=HERE/'SK_Melusina_V2_Boots_WeightClean_Candidate.fbx'
data=json.loads((HERE/'SK_Melusina_V2_Boots_data.json').read_text())
root,version=parse_fbx.parse(SOURCE.as_posix())
objects=next(x for x in root.elems if x.id==b'Objects')
connections=next(x for x in root.elems if x.id==b'Connections')
byid={x.props[0]:x for x in objects.elems}
geometry=[x for x in objects.elems if x.id==b'Geometry' and x.props[2]==b'Mesh']
if len(geometry)!=1:raise RuntimeError('Expected one source mesh')
geometry=geometry[0]
rawvertices=next(x for x in geometry.elems if x.id==b'Vertices').props[0]
vertices=[rawvertices[i:i+3] for i in range(0,len(rawvertices),3)]
if len(vertices)!=len(data['positions_m']):raise RuntimeError('Raw FBX/KineFX point count differs')
rawconverted=[[v[0]/100,v[2]/100,-v[1]/100] for v in vertices]
point_order_delta=max(math.dist(a,b) for a,b in zip(rawconverted,data['positions_m']))
if point_order_delta>1e-6:raise RuntimeError('Raw FBX/KineFX control-vertex index correspondence not proven')

clusters=[x for x in objects.elems if x.id==b'Deformer' and x.props[2]==b'Cluster']
cluster_bones={}
for c in connections.elems:
    if c.id==b'C' and c.props[0]==b'OO' and c.props[2] in {x.props[0] for x in clusters}:
        model=byid[c.props[1]]
        if model.id!=b'Model':raise RuntimeError('Unexpected Cluster input')
        cluster_bones[c.props[2]]=model.props[1].split(b'\x00\x01')[0].decode()
if len(cluster_bones)!=len(clusters):raise RuntimeError('Missing cluster-to-bone mappings')
sourceweights=[{} for _ in vertices]
for cl in clusters:
    name=cluster_bones[cl.props[0]]
    idx=next((x for x in cl.elems if x.id==b'Indexes'),None)
    weights=next((x for x in cl.elems if x.id==b'Weights'),None)
    if idx is None or weights is None:continue
    for i,w in zip(idx.props[0],weights.props[0]):
        if w>1e-6:sourceweights[i][name]=float(w)
sourceweightdelta=max(max((abs(a.get(n,0)-dict(b).get(n,0)) for n in a.keys()|dict(b).keys()),default=0) for a,b in zip(sourceweights,data['weights']))
if sourceweightdelta>1e-5:raise RuntimeError('Cluster/KineFX source weights differ')

poly=next(x for x in geometry.elems if x.id==b'PolygonVertexIndex').props[0]
parent=list(range(len(vertices)))
def find(a):
    while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
    return a
def union(a,b):
    a,b=find(a),find(b)
    if a!=b:parent[b]=a
face=[]
for val in poly:
    face.append(val if val>=0 else -val-1)
    if val<0:
        for i in face[1:]:union(face[0],i)
        face=[]
islands=collections.defaultdict(list)
for i in range(len(vertices)):islands[find(i)].append(i)
side={};islandreport=[]
for ids in islands.values():
    center=[sum(rawconverted[i][a] for i in ids)/len(ids) for a in range(3)]
    dl=math.dist(center,data['joints_m']['foot_l']);dr=math.dist(center,data['joints_m']['foot_r'])
    if abs(dl-dr)<.001:raise RuntimeError('Ambiguous anatomical island '+str(ids[:3]))
    s='l' if dl<dr else 'r'
    for i in ids:side[i]=s
    islandreport.append({'points':len(ids),'sample_ids':ids[:3],'side':s,'centroid_m':center,'distance_difference_m':abs(dl-dr)})
expected=[];delta={};removed=collections.Counter()
for i,prs in enumerate(sourceweights):
    opp='_r' if side[i]=='l' else '_l'
    kept={n:w for n,w in prs.items() if 'kilt' not in n and not n.endswith(opp)}
    bad={n:w for n,w in prs.items() if 'kilt' in n or n.endswith(opp)}
    if not kept:raise RuntimeError('Deletion would unweight vertex '+str(i))
    if len(kept)>4:raise RuntimeError('Existing correct-side influence count >4')
    total=sum(kept.values())
    expected.append({n:w/total for n,w in kept.items()} if bad else dict(prs))
    if bad:
        delta[str(i)]={'position_kinefx_m':data['positions_m'][i],'side':side[i],'old':prs,'new':expected[-1],'removed':bad}
        for n in bad:removed[n]+=1

changed_element_ids=set()
for cl in clusters:
    name=cluster_bones[cl.props[0]]
    idx=next((x for x in cl.elems if x.id==b'Indexes'),None)
    weights=next((x for x in cl.elems if x.id==b'Weights'),None)
    if idx is None or weights is None:continue
    newids=[i for i in idx.props[0] if name in expected[i]]
    newweights=[expected[i][name] for i in newids]
    if list(idx.props[0])!=newids or list(weights.props[0])!=newweights:
        idx.props[0]=array.array(idx.props[0].typecode,newids);weights.props[0]=array.array(weights.props[0].typecode,newweights)
        changed_element_ids.add(cl.props[0])

adders={ord(c):n for c,n in {'B':'add_bool','C':'add_char','Z':'add_int8','Y':'add_int16','I':'add_int32','L':'add_int64','F':'add_float32','D':'add_float64','R':'add_bytes','S':'add_string','i':'add_int32_array','l':'add_int64_array','f':'add_float32_array','d':'add_float64_array','b':'add_bool_array','c':'add_byte_array'}.items()}
def convert(e):
    target=encode_bin.FBXElem(e.id)
    for value,kind in zip(e.props,e.props_type):getattr(target,adders[kind])(value)
    target.elems=[convert(c) for c in e.elems]
    return target
with encode_bin.FBXElem.enable_multithreading_cm():converted=convert(root)
encode_bin.write(OUT.as_posix(),converted,version)

# Reparse and prove semantic tree identity outside the authorized weight arrays.
original,_=parse_fbx.parse(SOURCE.as_posix());candidate,_=parse_fbx.parse(OUT.as_posix())
def equalprop(a,b):
    if isinstance(a,array.array) and isinstance(b,array.array):return a.typecode==b.typecode and a.tobytes()==b.tobytes()
    return a==b
changes=[]
def compare(a,b,path=()):
    if a.id!=b.id or len(a.elems)!=len(b.elems) or a.props_type!=b.props_type:raise RuntimeError('FBX structural drift '+str(path))
    here=path+(a.id.decode(errors='replace'),)
    if a.id==b'Deformer' and len(a.props)>2:here=here+(str(a.props[0]),)
    if len(a.props)!=len(b.props):raise RuntimeError('Property count drift')
    if not all(equalprop(x,y) for x,y in zip(a.props,b.props)):changes.append('/'.join(here))
    for x,y in zip(a.elems,b.elems):compare(x,y,here)
compare(original,candidate)
allowed=all(p in ['/FileId','/CreationTime'] or ('/Deformer/' in p and p.rsplit('/',1)[-1] in ['Indexes','Weights']) for p in changes)
if not allowed:raise RuntimeError('Non-weight source tree changed: '+str(changes))
candidate_weights=[{} for _ in vertices]
candidate_objects=next(x for x in candidate.elems if x.id==b'Objects')
for cl in candidate_objects.elems:
    if cl.id!=b'Deformer' or cl.props[0] not in cluster_bones:continue
    idx=next((x for x in cl.elems if x.id==b'Indexes'),None);ws=next((x for x in cl.elems if x.id==b'Weights'),None)
    if idx is None or ws is None:continue
    for i,w in zip(idx.props[0],ws.props[0]):
        if w>1e-6:candidate_weights[i][cluster_bones[cl.props[0]]]=float(w)
actual_changed={i for i,(a,b) in enumerate(zip(sourceweights,candidate_weights)) if a!=b}
if actual_changed!={int(i) for i in delta}:raise RuntimeError('Actual changed vertices differ from indexed delta')
report={'schema':'melodia.boots_cluster_weight_candidate.v1','source_fbx':SOURCE.as_posix(),'candidate_fbx':OUT.as_posix(),
    'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),
    'fbx_version':version,'control_vertices':len(vertices),'clusters':len(clusters),'changed_clusters':len(changed_element_ids),
    'changed_vertices':len(delta),'removed_influence_point_counts':dict(removed),'islands':islandreport,
    'raw_fbx_to_kinefx_index_position_delta_mm':point_order_delta*1000,'source_cluster_to_kinefx_weight_delta':sourceweightdelta,
    'semantic_changed_element_paths':changes,'only_cluster_weights_and_encoder_metadata_changed':allowed,
    'actual_changed_vertices':len(actual_changed),'unaffected_vertex_weights_exact':True,
    'geometry_arrays_exact':True,'hierarchy_connections_exact':True,'bind_transforms_exact':True,
    'status':'CANDIDATE_PENDING_KINEFX_ROUNDTRIP'}
(HERE/'boots_cluster_candidate_build.json').write_text(json.dumps(report,indent=1),encoding='utf-8')
(HERE/'boots_weight_delta.json').write_text(json.dumps({'schema':'melodia.boots_weight_delta.v2','index_space':'Original FBX control vertex index, proven identical to KineFX source point order','source_sha256':report['source_sha256'],'verts':delta},indent=1),encoding='utf-8')
print('CLUSTER_CANDIDATE',json.dumps({k:report[k] for k in ['control_vertices','changed_clusters','changed_vertices','only_cluster_weights_and_encoder_metadata_changed','geometry_arrays_exact','hierarchy_connections_exact','bind_transforms_exact']}))
