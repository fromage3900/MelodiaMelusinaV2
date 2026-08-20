import sys
sys.path.insert(0, r'C:\EnvironmentPortfolio\BS_GodFile\Content\Python')

from gmm.npc import vrm4u_import
import unreal

print('VRM4U available:', unreal is not None)

results = vrm4u_import.import_all_vrms()

print(f'\nImport Results: {len(results)} models')
print('=' * 60)

for r in results:
    if r.success:
        print(f'  ✓ {r.source_id}: SUCCESS - {r.bone_count} bones, {r.morph_target_count} morphs')
        print(f'    SkeletalMesh: {r.skeletal_mesh}')
        print(f'    IK humanoid: {r.ik_rig_humanoid}')
        print(f'    IK mannequin: {r.ik_rig_mannequin}')
        print(f'    Retargeter: {r.retargeter_mannequin}')
        print(f'    Pose face: {r.pose_asset_face}')
        print(f'    Materials: {len(r.materials)} slots')
    else:
        print(f'  ✗ {r.source_id}: FAILED - {r.error}')

# Save audit
import json
from pathlib import Path
audit_path = Path(r'Saved/Audit/gmm_npc_vrm_import.json')
audit_path.parent.mkdir(parents=True, exist_ok=True)
with open(audit_path, 'w', encoding='utf-8') as f:
    json.dump([asdict(r) for r in results], f, indent=2)
print(f'\nAudit saved to: {audit_path}')