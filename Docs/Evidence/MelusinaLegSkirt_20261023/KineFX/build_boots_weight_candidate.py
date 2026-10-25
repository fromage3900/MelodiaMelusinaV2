"""Duplicate-only boot weight cleanup, using shirt_legal Blender FBX path."""
import collections
import hashlib
import json
from pathlib import Path
import bpy
from mathutils import Matrix, Vector

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'SourceExports/SK_Melusina_V2_Boots.fbx'
OUT=HERE/'SK_Melusina_V2_Boots_WeightClean_Candidate.fbx'
rep={'schema':'melodia.boots_weight_candidate_build.v1','input_fbx':SOURCE.as_posix(),
     'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'output_fbx':OUT.as_posix(),
     'reuse':'Tools/Houdini/shirt_legal/build_legal_shirt_fbx.py import/export settings'}
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.fbx(filepath=SOURCE.as_posix(),use_anim=False)
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
arms=[o for o in bpy.context.scene.objects if o.type=='ARMATURE']
if len(meshes)!=1 or len(arms)!=1: raise RuntimeError('Expected exactly one boot mesh and one armature')
mesh,arm=meshes[0],arms[0]
rep['source_mesh_object']=mesh.name;rep['source_armature_object']=arm.name
rep['source_vertex_count']=len(mesh.data.vertices);rep['source_polygon_count']=len(mesh.data.polygons)
rep['armature_bone_count']=len(arm.data.bones)
rep['mesh_world_matrix']=[list(r) for r in mesh.matrix_world]
rep['armature_world_matrix']=[list(r) for r in arm.matrix_world]
original_world=[list(mesh.matrix_world@v.co) for v in mesh.data.vertices]
parent=list(range(len(mesh.data.vertices)))
def find(a):
    while parent[a]!=a: parent[a]=parent[parent[a]];a=parent[a]
    return a
def union(a,b):
    a,b=find(a),find(b)
    if a!=b: parent[b]=a
for edge in mesh.data.edges:union(*edge.vertices)
islands=collections.defaultdict(list)
for i in range(len(parent)):islands[find(i)].append(i)
feet={s:arm.matrix_world@arm.data.bones['foot_'+s].head_local for s in ['l','r']}
side_by_id={};island_report=[]
for ids in islands.values():
    c=sum((Vector(original_world[i]) for i in ids),Vector())/len(ids)
    dl,dr=(c-feet['l']).length,(c-feet['r']).length
    # Reject islands within 1 mm of anatomical side ambiguity, rather than guess.
    if abs(dl-dr)<.001:raise RuntimeError('Ambiguous island side: '+str(ids[:3]))
    side='l' if dl<dr else 'r'
    for i in ids:side_by_id[i]=side
    island_report.append({'points':len(ids),'sample_ids':ids[:3],'centroid_world_m':list(c),
                          'side':side,'distance_foot_l_m':dl,'distance_foot_r_m':dr})
delta={};removed_tally=collections.Counter();zero=[];maximum=0
for v in mesh.data.vertices:
    old=[(mesh.vertex_groups[g.group].name,float(g.weight)) for g in v.groups if g.weight>1e-6]
    side=side_by_id[v.index];opp='_r' if side=='l' else '_l'
    keep=[(n,w) for n,w in old if 'kilt' not in n and not n.endswith(opp)]
    removed=[(n,w) for n,w in old if 'kilt' in n or n.endswith(opp)]
    if not removed:continue
    total=sum(w for _,w in keep)
    if total<=1e-6:zero.append(v.index);continue
    new=[(n,w/total) for n,w in keep]
    if len(new)>4:raise RuntimeError('More than four influences after deletion')
    for n,w in removed:
        mesh.vertex_groups[n].remove([v.index]);removed_tally[n]+=1
    for n,w in new:mesh.vertex_groups[n].add([v.index],w,'REPLACE')
    maximum=max(maximum,sum(w for _,w in removed))
    delta[str(v.index)]={'side':side,'position_world_m':original_world[v.index],'old':old,'new':new,'removed':removed}
if zero:raise RuntimeError('Removal would unweight points: '+str(zero))
rep['islands']=island_report;rep['changed_vertex_count']=len(delta)
rep['removed_influence_point_counts']=dict(removed_tally);rep['max_removed_weight']=maximum
rep['ambiguous_islands']=0;rep['unweighted_after']=0
# Exactly the mesh-transform bake from the existing legal-shirt exporter.
mesh.data.transform(mesh.matrix_world);mesh.matrix_world=Matrix.Identity(4)
for o in bpy.context.scene.objects:o.select_set(False)
mesh.select_set(True);arm.select_set(True);bpy.context.view_layer.objects.active=arm
bpy.ops.export_scene.fbx(filepath=OUT.as_posix(),use_selection=True,object_types={'ARMATURE','MESH'},
    use_mesh_modifiers=False,add_leaf_bones=False,bake_anim=False,apply_unit_scale=True,
    apply_scale_options='FBX_SCALE_ALL',use_armature_deform_only=False,mesh_smooth_type='OFF',path_mode='AUTO')
rep['output_sha256']=hashlib.sha256(OUT.read_bytes()).hexdigest();rep['output_bytes']=OUT.stat().st_size
(HERE/'boots_weight_delta.json').write_text(json.dumps({'schema':'melodia.boots_weight_delta.v1','index_space':'Blender imported FBX control vertices; roundtrip verifier matches by position and source weights','source_sha256':rep['source_sha256'],'verts':delta},indent=1),encoding='utf-8')
(HERE/'boots_candidate_build.json').write_text(json.dumps(rep,indent=1),encoding='utf-8')
print('BOOT_CANDIDATE',json.dumps({k:rep[k] for k in ['source_vertex_count','source_polygon_count','armature_bone_count','changed_vertex_count','removed_influence_point_counts','output_bytes']}))
