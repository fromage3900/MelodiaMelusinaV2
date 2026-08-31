import unreal

# Bind authored Sea Above reef MIs to the ingested reef meshes (0fe7b877 left
# everything on /Engine/EngineMaterials/WorldGridMaterial — geometry only).
# Single-slot meshes, 1:1 mapping by category. No skill-BP class loading.

ROOT_MESH = '/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes'
ROOT_MAT = '/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Materials'

MAP = {
    'SM_Coral_Brain': 'MI_SeaAbove_CoralSkin',
    'SM_Coral_Fan': 'MI_SeaAbove_CoralSkin',
    'SM_Coral_ReefCluster': 'MI_SeaAbove_CoralSkin',
    'SM_Coral_Staghorn': 'MI_SeaAbove_CoralSkin',
    'SM_Coral_Table': 'MI_SeaAbove_CoralSkin',
    'SM_Coral_TubeSponges': 'MI_SeaAbove_CoralSkin',
    'SM_Clutter_PebbleSet': 'MI_SeaAbove_CoralSkin',
    'SM_Clutter_SeaWeed': 'MI_SeaAbove_CoralSkin',
    'SM_Clutter_SpiralShell': 'MI_SeaAbove_CoralSkin',
    'SM_Clutter_Starfish': 'MI_SeaAbove_CoralSkin',
    'SM_Kelp_Cluster': 'MI_SeaAbove_Kelp',
    'SM_Kelp_Mid': 'MI_SeaAbove_Kelp',
    'SM_Kelp_Tall': 'MI_SeaAbove_Kelp',
    'SM_Island_A': 'MI_SeaAbove_Sand',
    'SM_Island_B': 'MI_SeaAbove_Sand',
    'SM_Island_C': 'MI_SeaAbove_Sand',
    'SM_RockChunk_L': 'MI_SeaAbove_WetRock',
    'SM_RockChunk_M': 'MI_SeaAbove_WetRock',
    'SM_DrownedOrgan': 'MI_SeaAbove_Organ_Pipe',
    'SM_Leviathan': 'MI_SeaAbove_Leviathan_Bone',
    'SM_Flora_Chime': 'MI_SeaAbove_CoralSkin',
    'SM_Flora_Fern': 'MI_SeaAbove_CoralSkin',
    'SM_Flora_Reed': 'MI_SeaAbove_CoralSkin',
}

ok = 0
failed = []
for mesh_name, mi_name in MAP.items():
    mesh_path = '%s/%s.%s' % (ROOT_MESH, mesh_name, mesh_name)
    mi_path = '%s/%s.%s' % (ROOT_MAT, mi_name, mi_name)
    try:
        mesh = unreal.load_asset(mesh_path)
        if mesh is None:
            failed.append('%s: not loadable' % mesh_name)
            continue
        mat = unreal.load_asset(mi_path)
        if mat is None:
            failed.append('%s: MI %s not loadable' % (mesh_name, mi_name))
            continue
        if mesh.get_class().get_name() == 'StaticMesh':
            mesh.set_material(0, mat)
        elif mesh.get_class().get_name() == 'SkeletalMesh':
            mesh.set_material(0, mat)
        else:
            failed.append('%s: unexpected class %s' % (mesh_name, mesh.get_class().get_name()))
            continue
        ok += 1
    except Exception as ex:
        failed.append('%s :: %s' % (mesh_name, ex))

unreal.log_warning('REEF_MAT_BIND ok=%d failed=%d' % (ok, len(failed)))
for f in failed[:10]:
    unreal.log_warning('REEF_MAT_FAIL %s' % f)