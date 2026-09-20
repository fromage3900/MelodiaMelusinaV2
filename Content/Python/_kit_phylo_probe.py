import unreal, json
EAL = unreal.EditorAssetLibrary
cands = [
 '/Game/Melodia/WorldCompiler/HeroCorners/PCG_HeroCorner_WestRim',
 '/Game/Melodia/PCG/PCG_Nikki_PhyllotaxisGarden_Walkable',
 '/Game/EnvSandbox/PCG/PCG_Nikki_PhyllotaxisGarden_Walkable',
]
pcg = {p: EAL.does_asset_exist(p) for p in cands}
# list a few atlantis + vehicle mesh paths
atl=[]; veh=[]
for root, bucket in [
 ('/Game/EnvSandbox/Meshes/Atlantis', atl),
 ('/Game/EnvSandbox/Meshes/Atlantis_PivotFixed', atl),
 ('/Game/KitBash_EnchantedVehicles', veh),
 ('/Game/Melodia/Imported/EnchantedVehicles', veh),
]:
    try:
        if EAL.does_directory_exist(root):
            for p in (EAL.list_assets(root, True, False) or [])[:80]:
                if '/SM_' in p or p.rsplit('/',1)[-1].startswith('SM_'):
                    bucket.append(p)
    except Exception as e:
        bucket.append(f'ERR {e}')
print('KIT', json.dumps({'pcg':pcg,'atlantis_n':len(atl),'atlantis':atl[:20],'vehicle_n':len(veh),'vehicle':veh[:20]}, default=str))
