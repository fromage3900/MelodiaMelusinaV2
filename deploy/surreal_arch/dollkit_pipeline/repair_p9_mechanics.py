"""Repair the existing P9 graph; does not replace the planned Higgsas gear pass.

Run against SurfaceDetail only, with --factory-startup. Never touch hero WIP.
"""
import bpy, json, math, shutil, sys
from pathlib import Path
from mathutils import Vector

BANK = Path('C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/melusina_doll_surface_20260924')
EXPECTED = Path('C:/EnvironmentPortfolio/harp_bow_pipeline/Melusina_DollKit_SurfaceDetail_20260924.blend')
assert Path(bpy.data.filepath) == EXPECTED
hw = bpy.data.objects['MEL_dollkit_clockwork']
ctrl = bpy.data.objects['MEL_dollkit_stations']
ng = hw.modifiers['MEL_clockwork_GN'].node_group
assert hw.data == ctrl.data and len(ctrl.data.vertices) == 14
assert not ng.get('p9_mechanics_repaired'), 'Already repaired; inspect instead of applying twice'
stations = json.loads((BANK.parent/'p9_seating_done.json').read_text())['station_report']
assert len(stations) == 14
for i, s in enumerate(stations):
    assert abs(ctrl.data.attributes['ball_r'].data[i].value * 1000-s['ball_r_mm']) < .01
station_id = ctrl.data.attributes.get('station_id') or ctrl.data.attributes.new('station_id','INT','POINT')
for i, item in enumerate(station_id.data): item.value = i
ctrl['station_labels_json'] = json.dumps([s['label'] for s in stations])

def node(typ, name, x, y):
    n = ng.nodes.new(typ); n.name = name; n.label = name; n.location = (x,y)
    return n
def unlink(sock):
    for l in list(sock.links): ng.links.remove(l)
def material(source, matname, label, x,y):
    n=node('GeometryNodeSetMaterial',label,x,y)
    n.inputs['Material'].default_value=bpy.data.materials[matname]
    ng.links.new(source,n.inputs['Geometry'])
    return n.outputs['Geometry']

instances = {k:ng.nodes[n] for k,n in {'ball':'Instance on Points','ring':'Instance on Points.001','rivet':'Instance on Points.002','gear':'Instance on Points.003','cuff':'Instance on Points.004'}.items()}
assert all(n.bl_idname == 'GeometryNodeInstanceOnPoints' for n in instances.values())
ng.nodes['Compare'].operation = 'LESS_THAN'  # delete non-geared stations, retain the four shoulders/hips
ng.nodes['Compare'].label = 'Remove stations without a gear'
ng.nodes['Align Euler to Vector'].axis = 'Z'
rotate = ng.nodes['Rotate Euler']
assert 'LOCAL' in [e.identifier for e in rotate.bl_rna.properties['space'].enum_items]
rotate.space = 'LOCAL'
rotate.label = 'Spin around each local spindle'

# Template dimensions are unitless; station radius is applied exactly once.
circle=ng.nodes['Curve Circle']; unlink(circle.inputs['Radius'])
circle.inputs['Radius'].default_value=1.0; circle.inputs['Resolution'].default_value=64
profile=ng.nodes['Curve Circle.001']; profile.inputs['Radius'].default_value=.035
profile.inputs['Resolution'].default_value=12
scale=node('ShaderNodeMath','Ring radius from station',-200,-900); scale.operation='MULTIPLY'
ng.links.new(ng.nodes['Math.001'].outputs[0],scale.inputs[0])
ng.links.new(ng.nodes['Named Attribute.006'].outputs['Attribute'],scale.inputs[1])
ng.links.new(scale.outputs[0],instances['ring'].inputs['Scale'])
ng.nodes.remove(ng.nodes['Math.002'])

for role,source,mat,y in [('ball',ng.nodes['UV Sphere'].outputs['Mesh'],'mj_porcelain',0),('ring',ng.nodes['Curve to Mesh'].outputs['Mesh'],'mj_brass',-300),('gear',ng.nodes['Object Info'].outputs['Geometry'],'mj_steel',-600),('cuff',ng.nodes['Cone'].outputs['Mesh'],'mj_brass',-900)]:
    ng.links.new(material(source,mat,'Material '+role,200,y),instances[role].inputs['Instance'])

# Each rivet generator samples one station explicitly. Primitive nodes cannot
# read station fields without a geometry sampling context.
oldr=instances.pop('rivet')
ng.nodes.remove(oldr)
ng.nodes.remove(ng.nodes['Resample Curve'])
ng.nodes.remove(ng.nodes['Ico Sphere'])
g=bpy.data.node_groups.new('MEL_doll_station_rivets','GeometryNodeTree')
g.interface.new_socket(name='Station',in_out='INPUT',socket_type='NodeSocketGeometry')
g.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
def gn(typ,name):
    n=g.nodes.new(typ);n.name=name;n.label=name;return n
gi=gn('NodeGroupInput','Station');go=gn('NodeGroupOutput','Rivets')
def sample(name,datatype='FLOAT'):
    a=gn('GeometryNodeInputNamedAttribute',name);a.data_type=datatype;a.inputs['Name'].default_value=name
    n=gn('GeometryNodeSampleIndex','Sample '+name);n.data_type=datatype;n.domain='POINT';n.inputs['Index'].default_value=0
    g.links.new(gi.outputs['Station'],n.inputs['Geometry']);g.links.new(a.outputs['Attribute'],n.inputs['Value'])
    return n.outputs['Value']
def mul(a,b,name):
    n=gn('ShaderNodeMath',name);n.operation='MULTIPLY';g.links.new(a,n.inputs[0])
    if isinstance(b,(int,float)):n.inputs[1].default_value=b
    else:g.links.new(b,n.inputs[1])
    return n.outputs[0]
radius=mul(sample('ball_r'),sample('ball_scale'),'Ball radius')
rr=mul(radius,sample('ring_proud'),'Rivet orbit radius')
rc=gn('GeometryNodeCurvePrimitiveCircle','Rivet orbit');g.links.new(rr,rc.inputs['Radius'])
res=gn('GeometryNodeResampleCurve','Rivet count');g.links.new(rc.outputs['Curve'],res.inputs['Curve']);g.links.new(sample('rivet_n'),res.inputs['Count'])
ico=gn('GeometryNodeMeshIcoSphere','Rivet head');ico.inputs['Subdivisions'].default_value=2;g.links.new(mul(radius,.035,'Rivet size'),ico.inputs['Radius'])
sm=gn('GeometryNodeSetMaterial','Brass rivets');sm.inputs['Material'].default_value=bpy.data.materials['mj_brass'];g.links.new(ico.outputs['Mesh'],sm.inputs['Geometry'])
ip=gn('GeometryNodeInstanceOnPoints','Rivet heads');g.links.new(res.outputs['Curve'],ip.inputs['Points']);g.links.new(sm.outputs['Geometry'],ip.inputs['Instance'])
real=gn('GeometryNodeRealizeInstances','Realize rivets');g.links.new(ip.outputs['Instances'],real.inputs['Geometry'])
align=gn('FunctionNodeAlignEulerToVector','Station spindle');align.axis='Z';g.links.new(sample('axis','FLOAT_VECTOR'),align.inputs['Vector'])
pos=gn('GeometryNodeInputPosition','Station position');ps=gn('GeometryNodeSampleIndex','Sample center');ps.data_type='FLOAT_VECTOR';ps.domain='POINT';ps.inputs['Index'].default_value=0
g.links.new(gi.outputs['Station'],ps.inputs['Geometry']);g.links.new(pos.outputs[0],ps.inputs['Value'])
trans=gn('GeometryNodeTransform','Seat rivets');g.links.new(real.outputs['Geometry'],trans.inputs['Geometry']);g.links.new(ps.outputs['Value'],trans.inputs['Translation']);g.links.new(align.outputs['Rotation'],trans.inputs['Rotation'])
tag=gn('GeometryNodeStoreNamedAttribute','Station identity');tag.data_type='INT';tag.domain='POINT';tag.inputs['Name'].default_value='station_id';g.links.new(sample('station_id','INT'),tag.inputs['Value']);g.links.new(trans.outputs['Geometry'],tag.inputs['Geometry']);g.links.new(tag.outputs['Geometry'],go.inputs['Geometry'])
for i,n in enumerate(g.nodes):n.location=((i%6)*220,-(i//6)*220)
index=node('GeometryNodeInputIndex','Station index',-1000,-2400)
for i in range(14):
    compare=node('FunctionNodeCompare','Rivets '+stations[i]['label'],-800-i%4*240,-2600-i//4*600);compare.data_type='INT';compare.operation='EQUAL'
    # Typed sockets are selected by identifier/type instead of duplicate display names.
    ai=next(s for s in compare.inputs if s.name=='A' and s.type=='INT')
    bi=next(s for s in compare.inputs if s.name=='B' and s.type=='INT')
    ng.links.new(index.outputs[0],ai);bi.default_value=i
    sep=node('GeometryNodeSeparateGeometry','Select '+stations[i]['label'],compare.location.x+200,compare.location.y);sep.domain='POINT'
    ng.links.new(ng.nodes['Set Position'].outputs['Geometry'],sep.inputs['Geometry']);ng.links.new(compare.outputs[0],sep.inputs['Selection'])
    group=node('GeometryNodeGroup','Rivets at '+stations[i]['label'],sep.location.x+200,sep.location.y);group.node_tree=g
    ng.links.new(sep.outputs['Selection'],group.inputs['Station']);ng.links.new(group.outputs['Geometry'],ng.nodes['Join Geometry'].inputs['Geometry'])

for o in [hw,ctrl]:o.hide_viewport=False;o.hide_set(False)
hw.hide_render=False
for o in bpy.data.objects:
    if o.name.startswith(('MEL_dk2_','MEL_dollkit_ball_','DollBall_')):
        o.hide_render=True;o.hide_viewport=True
        if o.name in bpy.context.view_layer.objects:o.hide_set(True)
# Object Info must evaluate the template even though it is not directly visible.
template=bpy.data.objects['MEL_dk2_gear_template'];template.hide_viewport=False
ng['p9_mechanics_repaired']=True
ng['repair_scope']='gear selection/local spin, ring dimensions, stationed rivets, materials; cuff seating and rig following still open'

# Evaluate branch geometry, including identities and measured ring dimensions.
bev=next(m for m in hw.modifiers if m.type=='BEVEL');bv=bev.show_viewport;bev.show_viewport=False
out=ng.nodes['Group Output'].inputs['Geometry'];original=out.links[0].from_socket
def evaluate(socket,frame):
    ng.links.new(socket,out);bpy.context.scene.frame_set(frame);bpy.context.view_layer.update()
    ev=hw.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    result={'vertices':[tuple(v.co) for v in me.vertices],'faces':len(me.polygons),'materials':[m.name if m else None for m in me.materials],'ids':[a.value for a in me.attributes['station_id'].data] if me.attributes.get('station_id') else []}
    result['used_materials']=sorted({me.materials[p.material_index].name if me.materials[p.material_index] else 'UNASSIGNED' for p in me.polygons})
    ev.to_mesh_clear();return result
real=ng.nodes['Realize Instances']
def branch(socket,frame=0):
    inp=real.inputs['Geometry'];prev=inp.links[0].from_socket;ng.links.new(socket,inp)
    try:return evaluate(real.outputs['Geometry'],frame)
    finally:ng.links.new(prev,inp)
gears0=branch(instances['gear'].outputs['Instances'],0);gears40=branch(instances['gear'].outputs['Instances'],40)
balls0=branch(instances['ball'].outputs['Instances'],0);balls40=branch(instances['ball'].outputs['Instances'],40)
rings=branch(instances['ring'].outputs['Instances'])
gearids=set(gears0['ids']);expectedids={i for i,s in enumerate(stations) if s['label'].startswith(('shoulder_','hip_'))}
assert gearids==expectedids,(gearids,expectedids)
assert gears0['vertices']!=gears40['vertices'] and balls0['vertices']==balls40['vertices']
rivet_measure=[]
for i,s in enumerate(stations):
    output=ng.nodes['Rivets at '+s['label']].outputs['Geometry']
    data=evaluate(output,0)
    axis=Vector(ctrl.data.attributes['axis'].data[i].vector).normalized()
    center=ctrl.data.vertices[i].co+axis*ctrl.data.attributes['ball_off'].data[i].value
    centroid=sum((Vector(p) for p in data['vertices']),Vector())/len(data['vertices'])
    count=round(ctrl.data.attributes['rivet_n'].data[i].value)
    assert len(data['vertices'])==42*count and set(data['ids'])=={i}
    assert (centroid-center).length<.000001,(s['label'],tuple(centroid),tuple(center))
    rivet_measure.append({'station':s['label'],'rivet_count':count,'center_error_mm':(centroid-center).length*1000})
# Exercise one per-station count edit; other station count must remain unchanged.
value=ctrl.data.attributes['rivet_n'].data[2].value
ctrl.data.attributes['rivet_n'].data[2].value=9;ctrl.data.update()
assert len(evaluate(ng.nodes['Rivets at shoulder_l'].outputs['Geometry'],0)['vertices'])==9*42
assert len(evaluate(ng.nodes['Rivets at shoulder_r'].outputs['Geometry'],0)['vertices'])==12*42
ctrl.data.attributes['rivet_n'].data[2].value=value;ctrl.data.update()
for a,b,idx in zip(gears0['vertices'],gears40['vertices'],gears0['ids']):
    axis=Vector(ctrl.data.attributes['axis'].data[idx].vector).normalized()
    assert abs((Vector(a)-Vector(b)).dot(axis))<.000001,'Gear motion drifted off local spindle'
ringmeasure=[]
for i,s in enumerate(stations):
    axis=Vector(ctrl.data.attributes['axis'].data[i].vector).normalized()
    center=ctrl.data.vertices[i].co+axis*ctrl.data.attributes['ball_off'].data[i].value
    radii=[]
    for p,idx in zip(rings['vertices'],rings['ids']):
        if idx==i:
            d=Vector(p)-center;radii.append((d-axis*d.dot(axis)).length)
    r=ctrl.data.attributes['ball_r'].data[i].value;proud=ctrl.data.attributes['ring_proud'].data[i].value
    assert radii and abs(max(radii)-r*proud*1.035)<.0001,(i,radii[:1])
    ringmeasure.append({'station':s['label'],'min_radius_mm':min(radii)*1000,'max_radius_mm':max(radii)*1000,'ball_radius_mm':r*1000})
ng.links.new(original,out);bpy.context.scene.frame_set(0);bev.show_viewport=bv;bpy.context.view_layer.update()
full=evaluate(original,0)
assert full['faces']>0 and set(full['used_materials'])=={'mj_porcelain','mj_brass','mj_steel'}, (full['faces'],full['used_materials'])
report={'status':'PASS_SCOPED_GRAPH_REPAIR','file':str(EXPECTED),'gear_stations':[stations[i]['label'] for i in sorted(gearids)],'gear_vertices_changed':sum(a!=b for a,b in zip(gears0['vertices'],gears40['vertices'])),'ball_vertices_changed':sum(a!=b for a,b in zip(balls0['vertices'],balls40['vertices'])),'ring_measurements':ringmeasure,'rivet_measurements':rivet_measure,'rivet_parameter_isolation':True,'gear_local_spindle_motion':True,'full_vertices':len(full['vertices']),'full_faces':full['faces'],'materials':full['used_materials'],'remaining':['cuff seating','rig-following articulation','Higgsas gear refinement','visual assembly acceptance'],'saved':False}
backup=EXPECTED.with_name(EXPECTED.stem+'_before_GNrepair.blend')
if '--save' in sys.argv:
    assert not backup.exists(),'Preserve prior repair backup; inspect before overwriting'
    shutil.copy2(EXPECTED,backup)
    versions=bpy.context.preferences.filepaths.save_version;bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(EXPECTED))
    bpy.context.preferences.filepaths.save_version=versions
    report['saved']=True;report['backup']=str(backup)
(BANK/'E1_gn_mechanics_repair.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
