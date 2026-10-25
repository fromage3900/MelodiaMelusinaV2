"""Persist the proven necklace frame through its existing construction owner."""
from pathlib import Path
import json,sys,shutil,hashlib,copy
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[2]
sys.path.insert(0,str(REPO/'Tools/animation'))
from repair_loop_seam import checked_call,python_result
asset='/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter'
disk=REPO/'Content/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter.uasset'
canary=json.loads((HERE/'necklace_attachment_canary.json').read_text())
retained=json.loads((HERE/'necklace_canary_retention.json').read_text())
assert retained['retained_socket']=='spine_03_x' and not retained['errors']
report={'asset':asset,'scope':'necklace construction socket and its component bind transform only',
        'file_sha256_before':hashlib.sha256(disk.read_bytes()).hexdigest(),'passed':False}
def call(action,**args):return checked_call('blueprint',{'action':action,'asset_path':asset,**args})
def fp():return call('get_graph_fingerprint',graph_name='UserConstructionScript',mode='topology+defaults')
snapshot_code="""import unreal,json
bp=unreal.load_asset(%r);ss=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem);rows={}
for h in ss.k2_gather_subobject_data_for_blueprint(bp):
 d=unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h);o=unreal.SubobjectDataBlueprintFunctionLibrary.get_object(d)
 if not isinstance(o,unreal.SceneComponent):continue
 t=o.get_relative_transform();v=t.translation;q=t.rotation;s=t.scale3d
 rows[o.get_name()]={'location':[round(x,7) for x in [v.x,v.y,v.z]],'quat':[round(x,7) for x in [q.x,q.y,q.z,q.w]],'scale':[round(x,7) for x in [s.x,s.y,s.z]]}
print(json.dumps(rows))
"""%asset
try:
 state=python_result("import unreal,json\ne=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)\nprint(json.dumps({'pie':bool(e.get_game_world()),'world':e.get_editor_world().get_path_name()}))")
 assert not state['pie']
 dirty=checked_call('editor',{'action':'list_dirty_packages'})
 assert not any(p['package']==asset for p in dirty['dirty_packages']),'canonical pawn already dirty'
 backup=HERE/'BP_MelusinaJRPGCharacter_before_necklace.uasset'
 assert not backup.exists(),'backup already exists; no repeated mutation'
 shutil.copy2(disk,backup)
 before_components=python_result(snapshot_code);report['components_before']=before_components
 graph=call('export_graph',graph_name='UserConstructionScript')
 (HERE/'necklace_construction_before.json').write_text(json.dumps(graph,indent=2))
 a,b=fp(),fp();assert a['fingerprint']==b['fingerprint']
 call('save_asset');c=fp();assert a['fingerprint']==c['fingerprint']
 report['stable_before_fingerprints']=[x['fingerprint'] for x in [a,b,c]]
 expected=copy.deepcopy(graph)
 node=next(n for n in expected['nodes'] if n['id']=='K2Node_CallFunction_2')
 assert 'K2Node_VariableGet_3.Regalia_v4_Necklace' in next(p for p in node['pins'] if p['name']=='self')['connected_to']
 pin=next(p for p in node['pins'] if p['name']=='SocketName');assert pin['default_value']=='neck_x'
 pin['default_value']='spine_03_x'
 call('set_pin_default',graph_name='UserConstructionScript',node_id=node['id'],pin_name='SocketName',value='spine_03_x')
 tx=canary['candidate_relative']
 report['template_edit']=python_result("""import unreal,json
bp=unreal.load_asset(%r);ss=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem);found={}
for h in ss.k2_gather_subobject_data_for_blueprint(bp):
 d=unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h);o=unreal.SubobjectDataBlueprintFunctionLibrary.get_object(d)
 if o and o.get_name()=='Regalia_v4_Necklace_GEN_VARIABLE':found[o.get_path_name()]=o
assert len(found)==1
o=next(iter(found.values()));tx=%r
o.set_editor_property('relative_location',unreal.Vector(*tx['location']))
o.set_editor_property('relative_rotation',unreal.Quat(*tx['quat_xyzw']).rotator())
o.set_editor_property('relative_scale3d',unreal.Vector(*tx['scale']))
print(json.dumps({'template':o.get_path_name(),'relative':str(o.get_relative_transform())}))
"""%(asset,tx))
 report['compile']=call('compile_blueprint')
 assert report['compile']['error_count']==0 and report['compile']['warning_count']==0,report['compile']
 report['graph_assertion']=call('assert_graph_matches',graph_name='UserConstructionScript',mode='exact',spec=expected)
 assert report['graph_assertion']['matched'],report['graph_assertion']
 after_components=python_result(snapshot_code);report['components_after']=after_components
 target='Regalia_v4_Necklace_GEN_VARIABLE'
 assert set(before_components)==set(after_components)
 assert all(before_components[k]==after_components[k] for k in before_components if k!=target),'another component changed'
 for key,expected_values in [('location',tx['location']),('quat',tx['quat_xyzw']),('scale',tx['scale'])]:
  assert max(abs(x-y) for x,y in zip(after_components[target][key],expected_values))<2e-6,(key,after_components[target])
 report['other_component_defaults_unchanged']=True
 report['after_fingerprint']=fp()
 call('save_asset')
 report['file_sha256_after']=hashlib.sha256(disk.read_bytes()).hexdigest()
 report['passed']=True
except Exception as exc:
 report['error']=str(exc)
finally:
 (HERE/'necklace_persisted_fix.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if not k.startswith('components_')},indent=2))
sys.exit(0 if report['passed'] else 1)
