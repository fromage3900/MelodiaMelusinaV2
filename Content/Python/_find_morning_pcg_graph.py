import unreal, json
EAL=unreal.EditorAssetLibrary
ar=unreal.AssetRegistryHelpers.get_asset_registry()
hits=[]
for root in ('/Game/EnvSandbox/PCG','/Game/Melodia','/Game/EnvSandbox'):
  try: assets=ar.get_assets_by_path(root, True) or []
  except: assets=[]
  for a in assets:
    if str(a.asset_class_path.asset_name) not in ('PCGGraph','PCGGraphInterface'): continue
    n=str(a.asset_name).lower(); p=str(a.package_name)
    if any(k in n or k in p.lower() for k in ('morning','rainbow','melusina','opening','bloom','flower')):
      hits.append(p)
print('GRAPHS', json.dumps(hits[:40]))
# try read graph from field via reflection
svc=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
field=next((a for a in svc.get_all_level_actors() if a.get_actor_label()=='WC_morning_rainbow_bloom_Field'),None)
info={}
if field:
  comp=field.get_component_by_class(unreal.PCGComponent)
  for prop in ('graph','Graph','graph_instance','GraphInstance','template_graph'):
    try:
      v=comp.get_editor_property(prop)
      info[prop]=v.get_path_name() if hasattr(v,'get_path_name') else str(v)[:120]
    except Exception as e:
      info[prop]='ERR:'+str(e)[:80]
  if hasattr(comp,'get_graph'):
    try:
      g=comp.get_graph(); info['get_graph']=g.get_path_name() if g else None
    except Exception as e:
      info['get_graph']=str(e)[:80]
print('FIELD', json.dumps(info))
