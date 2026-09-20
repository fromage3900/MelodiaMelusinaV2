import unreal, json
from collections import Counter
EAL=unreal.EditorAssetLibrary

CANDIDATES = [
  '/Game/EnvSandbox/PCG/Universal/PCG_MeadowBloom',
  '/Game/EnvSandbox/PCG/Universal/PCG_MeadowFalloff',
  '/Game/EnvSandbox/PCG/Universal/PCG_RockScatter',
  '/Game/EnvSandbox/PCG/Universal/PCG_Universal_RockScatter',
  '/Game/EnvSandbox/PCG/Universal/PCG_OrnamentalDetail',
  '/Game/EnvSandbox/PCG/Universal/PCG_PathScatter',
  '/Game/EnvSandbox/PCG/Universal/PCG_BlossomPath',
  '/Game/EnvSandbox/PCG/Universal/PCG_WaterEdgeScatter',
  '/Game/EnvSandbox/PCG/Styles/WP/PCG_WP_SakuraDream_MeadowBloom',
  '/Game/EnvSandbox/PCG/Styles/WP/PCG_WP_SakuraDream_BlossomPath',
  '/Game/EnvSandbox/PCG/Styles/Sakura/PCG_Nikki_MandalaBloom',
  '/Game/EnvSandbox/PCG/Styles/Sakura/PCG_Nikki_PhyllotaxisGarden_Walkable',
  '/Game/Melodia/PCG/PCG_Morning_MemoryDressing',
  '/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_BellTreeGarden',
  '/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_CrystalHarpGrove',
  '/Game/EnvSandbox/PCG/Styles/Escher/PCG_EscherFloatingIslandEx',
  '/Game/EnvSandbox/PCG/Styles/Escher/PCG_EscherDecks',
  '/Game/Melodia/WorldCompiler/PCG_WorldCompiler_PointField',
  '/Game/Melodia/WorldCompiler/HeroCorners/PCG_HeroCorner_WestRim',
  '/Game/Melodia/WorldCompiler/HeroCorners/PCG_HeroCorner_EastBank',
  '/Game/Melodia/WorldCompiler/HeroCorners/PCG_HeroCorner_NorthDress',
]

def inspect(path):
  g=EAL.load_asset(path)
  if not g: return {'missing':True}
  nodes=[]
  settings_names=[]
  try:
    for n in (g.get_editor_property('nodes') or []):
      nodes.append(n.get_class().get_name())
      try:
        s=n.get_settings()
        if s: settings_names.append(s.get_class().get_name())
      except Exception:
        try:
          s=n.get_editor_property('settings_interface')
          if s: settings_names.append(s.get_class().get_name())
        except Exception:
          pass
  except Exception as e:
    return {'error':str(e)[:120]}
  pcgex=[s for s in settings_names if 'PCGEx' in s or 'PcgEx' in s]
  return {
    'node_n': len(nodes),
    'settings_n': len(settings_names),
    'uses_pcgex': len(pcgex)>0,
    'pcgex': sorted(set(pcgex))[:25],
    'top_settings': Counter(settings_names).most_common(12),
  }

out={p.split('/')[-1]: inspect(p) for p in CANDIDATES}
print('CAND', json.dumps(out, default=str)[:14000])
