import unreal, json
EAL=unreal.EditorAssetLibrary; MEL=unreal.MaterialEditingLibrary

def chain(path, depth=0):
    if not EAL.does_asset_exist(path) or depth>6:
        return []
    asset=EAL.load_asset(path)
    try: parent=asset.get_editor_property('parent')
    except: parent=None
    pp=parent.get_path_name() if parent else None
    sc=[]
    try: sc=[str(n) for n in MEL.get_scalar_parameter_names(asset)]
    except: pass
    row={'path':path,'class':asset.get_class().get_name(),
         'DreamSaturation':'DreamSaturation' in sc,
         'SharedBend':'SharedBend' in sc,
         'MelodiaWindResponse':'MelodiaWindResponse' in sc}
    rows=[row]
    if pp:
        rows += chain(pp, depth+1)
    return rows

# Universal wind-like params
uni=EAL.load_asset('/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal')
usc=[str(n) for n in MEL.get_scalar_parameter_names(uni)]
uwind=[s for s in usc if any(k in s.lower() for k in ('wind','foliage','wpo','sway','bend','ripple'))]
unikki=[s for s in usc if any(k in s for k in ('Dream','Pastel','Nikki','RimPower','RimWidth','Sparkle'))]

# Melodia plant wind at real path
melodia='/Game/Melodia/_PROJECT/04_Materials/Plants/M_MelodiaPlant_Wind'
generic='/Game/Melodia/_PROJECT/04_Materials/Plants/Flowers/MI_Plant_Flower_GenericFlower1'

out={
 'speedtree_chain': chain('/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowSpeedTree_B0_Red'),
 'petal_chain': chain('/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowPetal_B0_Red'),
 'petal_wind_chain': chain('/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowPetal_Wind_B0_Red'),
 'universal_wind_like': uwind,
 'universal_nikki_sample': unikki[:40],
 'melodia_exists': EAL.does_asset_exist(melodia),
 'generic_exists': EAL.does_asset_exist(generic),
}

# Can MelodiaPlant_Wind accept new scalar params via editing library? Check expressions count
if EAL.does_asset_exist(melodia):
    m=EAL.load_asset(melodia)
    sc=[str(n) for n in MEL.get_scalar_parameter_names(m)]
    out['melodia']={'scalars_n':len(sc),'has_MF_hint':[s for s in sc if 'Melodia' in s or 'Nikki' in s or 'Dream' in s][:30]}

# Look for hybrid master already
ar=unreal.AssetRegistryHelpers.get_asset_registry()
hyb=[]
for a in (ar.get_assets_by_path('/Game/EnvSandbox/Materials', True) or []):
    name=str(a.asset_name).lower()
    if ('speedtree' in name or 'plant_wind' in name or 'foliage' in name) and ('nikki' in name or 'toon' in name or 'universal' in name):
        hyb.append(str(a.package_name))
out['hybrid_hits']=hyb[:20]

# Texture param names on Universal vs SpeedTree
try:
    out['uni_tex']=[str(n) for n in MEL.get_texture_parameter_names(uni)][:20]
except: out['uni_tex']=[]
st=EAL.load_asset('/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowSpeedTree_B0_Red')
try:
    out['st_tex']=[str(n) for n in MEL.get_texture_parameter_names(st)][:20]
except: out['st_tex']=[]

print('HYBRID '+json.dumps(out, default=str)[:12000])
