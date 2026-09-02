import unreal

ROOT = '/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes'
names = [
    'SM_Coral_Brain', 'SM_Coral_Fan', 'SM_Coral_ReefCluster', 'SM_Coral_Staghorn',
    'SM_Coral_Table', 'SM_Coral_TubeSponges', 'SM_Clutter_PebbleSet', 'SM_Clutter_SeaWeed',
    'SM_Clutter_SpiralShell', 'SM_Clutter_Starfish', 'SM_Kelp_Cluster', 'SM_Kelp_Mid',
    'SM_Kelp_Tall', 'SM_Island_A', 'SM_Island_B', 'SM_Island_C', 'SM_RockChunk_L',
    'SM_RockChunk_M', 'SM_DrownedOrgan', 'SM_Leviathan', 'SM_Flora_Chime', 'SM_Flora_Fern',
    'SM_Flora_Reed',
]

saved = 0
for n in names:
    if unreal.EditorAssetLibrary.save_asset('%s/%s' % (ROOT, n)):
        saved += 1
unreal.log_warning('REEF_MAT_SAVE saved=%d/%d' % (saved, len(names)))