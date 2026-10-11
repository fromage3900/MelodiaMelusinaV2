import unreal, re
EAL=unreal.EditorAssetLibrary; B='/Game/Melodia/PCG/MassiveBiome/'
ar=unreal.AssetRegistryHelpers.get_asset_registry()
P={str(a.asset_name):str(a.package_name) for a in ar.get_assets_by_path('/Game/Megascans/3D_Plants',recursive=True)}
E='/Game/EnvSandbox/Meshes/'
P.update({'Tree01_Art':E+'Environment/Tree01_Art','Tree02_Art':E+'Environment/Tree02_Art','Tree03_Art':E+'Environment/Tree03_Art','Tree04_Art':E+'Environment/Tree04_Art',
 'Bush01_Art':E+'Environment/Bush01_Art','Bush04_Art':E+'Environment/Bush04_Art','Bush08_Art':E+'Environment/Bush08_Art',
 'SM_ATL_Palace_TreeA':E+'Atlantis_PivotFixed/SM_ATL_Palace_TreeA','SM_ATL_Palace_TreeC':E+'Atlantis_PivotFixed/SM_ATL_Palace_TreeC','SM_ATL_Palace_TreeF':E+'Atlantis_PivotFixed/SM_ATL_Palace_TreeF'})
def entry(proto,mesh,w,smin,smax):
    t=proto.export_text()
    t=re.sub(r'Mesh_14_[0-9A-F]+="[^"]*"', lambda m: m.group(0).split('=')[0]+'="/Script/Engine.StaticMesh\'%s.%s\'"'%(P[mesh],mesh), t)
    t=re.sub(r'(Weight_13_[0-9A-F]+)=[0-9.]+', r'\1=%f'%w, t)
    t=re.sub(r'(ObjectScaleMin_23_[0-9A-F]+)=\(X=[^)]*\)', r'\1=(X=%f,Y=%f,Z=%f)'%(smin,smin,smin), t)
    t=re.sub(r'(ObjectScaleMax_24_[0-9A-F]+)=\(X=[^)]*\)', r'\1=(X=%f,Y=%f,Z=%f)'%(smax,smax,smax), t)
    e=proto.copy(); e.import_text(t); return e
for name in ('DA_Melodia_DistantForest','DA_Melodia_IslandGrove'):
    if not EAL.does_asset_exist(B+name): print('dup',name,EAL.duplicate_asset(B+'DA_Melodia_MorningBiome',B+name))
src=unreal.load_asset(B+'DA_Melodia_MorningBiome'); proto=src.get_editor_property('Bushes')[0]
# --- DistantForest (restored as it was: see session dump 2026-10-10)
df=unreal.load_asset(B+'DA_Melodia_DistantForest')
df.set_editor_property('Trees',[entry(proto,*s) for s in [('Tree01_Art',2,1,1.8),('Tree02_Art',2,1,1.8),('Tree03_Art',2,1,1.8),('Tree04_Art',2,1,1.8),('SM_ATL_Palace_TreeA',1,1.2,2),('SM_ATL_Palace_TreeC',1,1.2,2),('SM_ATL_Palace_TreeF',1,1.2,2)]])
df.set_editor_property('Bushes',[entry(proto,*s) for s in [('Tree01_Art',2,1,1.8),('Tree02_Art',2,1,1.8),('Tree03_Art',2,1,1.8),('Bush01_Art',0.4,0.8,1.4),('Bush04_Art',0.4,0.8,1.4),('Bush08_Art',0.4,0.8,1.4)]])
print('DistantForest saved',EAL.save_asset(B+'DA_Melodia_DistantForest',only_if_is_dirty=False))
# --- IslandGrove (Megascans only)
ig=unreal.load_asset(B+'DA_Melodia_IslandGrove')
ig.set_editor_property('Trees',[entry(proto,*s) for s in [('SM_EuropeanHornbeam_Forest_01',2,0.45,0.7),('SM_EuropeanHornbeam_Forest_02',2,0.45,0.7),('SM_EuropeanHornbeam_Forest_03',2,0.4,0.65),('SM_EuropeanHornbeam_Sapling_01',3,1.6,2.6),('SM_EuropeanHornbeam_Sapling_02',3,1.6,2.6),('SM_EuropeanHornbeam_Sapling_03',2,1.6,2.4),('SM_DragonTree_01',1,3.0,4.0)]])
ig.set_editor_property('Bushes',[entry(proto,*s) for s in [('SM_EuropeanHornbeam_Forest_01',2,0.45,0.7),('SM_EuropeanHornbeam_Forest_02',2,0.45,0.7),('SM_EuropeanHornbeam_Forest_03',1,0.4,0.65),('SM_EuropeanHornbeam_Sapling_01',3,1.6,2.6),('SM_EuropeanHornbeam_Sapling_02',3,1.6,2.6),('SM_DragonTree_01',1,3.0,4.0),('SM_Elderberry_01',2,2.0,3.0),('SM_Elderberry_02',2,2.0,3.0)]])
print('IslandGrove saved',EAL.save_asset(B+'DA_Melodia_IslandGrove',only_if_is_dirty=False))
for n,d in (('DistantForest',df),('IslandGrove',ig)): print(n,'trees',len(d.get_editor_property('Trees')),'bushes',len(d.get_editor_property('Bushes')),'flowers',len(d.get_editor_property('Flowers')))
EAL=unreal.EditorAssetLibrary; B='/Game/Melodia/PCG/MassiveBiome/'
g=unreal.load_asset(B+'PCG_Biome_IslandGrove')
for n in g.get_editor_property('nodes'):
    st=n.get_settings()
    if st is None: continue
    cn=st.get_class().get_name()
    if cn=='PCGCreateAttributeSetSettings':
        a=st.get_editor_property('attribute_types'); t=a.export_text()
        if 'DA_Melodia_DistantForest' in t:
            a.import_text(t.replace('/Game/Melodia/PCG/MassiveBiome/DA_Melodia_DistantForest.DA_Melodia_DistantForest','/Game/Melodia/PCG/MassiveBiome/DA_Melodia_IslandGrove.DA_Melodia_IslandGrove').replace('/Game/Melodia/PCG/MassiveBiome/DA_Melodia_DistantForest','/Game/Melodia/PCG/MassiveBiome/DA_Melodia_IslandGrove')); st.set_editor_property('attribute_types',a); print('DA repointed')
    elif cn=='PCGAddAttributeSettings':
        tgt=st.get_editor_property('output_target').export_text()
        a=st.get_editor_property('attribute_types'); t=a.export_text()
        if 'Thin_Bushes' in tgt:
            a.import_text(re.sub(r'(Float|Double)Value=0\.\d+', lambda m: m.group(1)+'Value=0.050000', t, count=1)); st.set_editor_property('attribute_types',a); print('Thin_Bushes -> 0.05', re.findall(r'(?:Float|Double)Value=([0-9.]+)',a.export_text())[:2])
        if 'Cell_Bushes' in tgt:
            a.import_text(t.replace('X=700.000000,Y=700.000000','X=400.000000,Y=400.000000')); st.set_editor_property('attribute_types',a); print('Cell_Bushes -> 400')
print('graph saved',EAL.save_asset(B+'PCG_Biome_IslandGrove',only_if_is_dirty=False))
