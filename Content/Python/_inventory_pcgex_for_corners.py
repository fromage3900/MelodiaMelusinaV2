import unreal, json
EAL=unreal.EditorAssetLibrary
ar=unreal.AssetRegistryHelpers.get_asset_registry()
graphs=[]
for root in ('/Game/EnvSandbox/PCG','/Game/Melodia','/Game/EnvSandbox'):
  try: assets=ar.get_assets_by_path(root, True) or []
  except: assets=[]
  for a in assets:
    cls=str(a.asset_class_path.asset_name)
    if cls not in ('PCGGraph','PCGGraphInterface','PCGGraphInstance'): continue
    p=str(a.package_name); n=str(a.asset_name)
    low=(p+'/'+n).lower()
    tag='other'
    if 'pcgex' in low or 'ex_' in low: tag='pcgex'
    if any(k in low for k in ('meadow','flower','bloom','foliage','flora','grass')): tag='flora'
    if any(k in low for k in ('dress','prop','ornament','scatter','rock','bush')): tag='dress'
    if any(k in low for k in ('hero','corner','mandala','memory','morning','opening','melusina')): tag='hero_morning'
    if any(k in low for k in ('path','walk','spline','bridge','rail')): tag='path'
    if any(k in low for k in ('water','pond','shore','mist')): tag='water'
    graphs.append({'name':n,'path':p,'class':cls,'tag':tag})

# Also inspect HeroCorner graphs node makeup if loadable
hero_paths=[
 '/Game/Melodia/WorldCompiler/HeroCorners/PCG_HeroCorner_WestRim',
 '/Game/Melodia/WorldCompiler/HeroCorners/PCG_HeroCorner_EastBank',
 '/Game/Melodia/WorldCompiler/HeroCorners/PCG_HeroCorner_NorthDress',
 '/Game/Melodia/WorldCompiler/PCG_WorldCompiler_PointField',
]
hero_info={}
for hp in hero_paths:
  g=EAL.load_asset(hp)
  if not g:
    hero_info[hp]={'missing':True}; continue
  nodes=[]
  try:
    for n in g.get_editor_property('nodes') or []:
      nodes.append(n.get_class().get_name() if hasattr(n,'get_class') else str(type(n)))
  except Exception as e:
    # try get_nodes
    try:
      for n in g.get_nodes():
        sn=n.get_settings() if hasattr(n,'get_settings') else None
        nodes.append(sn.get_class().get_name() if sn else n.get_class().get_name())
    except Exception as e2:
      nodes=['ERR:'+str(e2)[:100]]
  from collections import Counter
  hero_info[hp.split('/')[-1]]={'node_n':len(nodes),'classes':Counter(nodes).most_common(20)}

# Categorize inventory
by={}
for g in graphs:
  by.setdefault(g['tag'],[]).append(g['path']+'/'+g['name'] if not g['path'].endswith(g['name']) else g['path'])

# dedupe paths
inv={}
for tag, lst in by.items():
  uniq=sorted(set(lst))
  inv[tag]=uniq[:50]
  inv[tag+'_n']=len(uniq)

print('PCG_INV', json.dumps({'inventory':inv,'hero_graphs':hero_info,'total_graphs':len(graphs)}, default=str)[:14000])
