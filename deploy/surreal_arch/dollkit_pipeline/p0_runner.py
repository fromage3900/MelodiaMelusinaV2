import json, traceback, os

receipt_path = r'C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\p0_restpose_receipt.json'
try:
    exec(compile(open(r'C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\p0_restpose.py').read(),
                 'p0_restpose.py', 'exec'))
    status = 'ok'
    gate = {}
    if os.path.exists(receipt_path):
        gate = json.load(open(receipt_path)).get('gate', {})
    # save derived working file next to canonical
    import bpy
    bpy.ops.wm.save_as_mainfile(
        filepath=r'C:\EnvironmentPortfolio\harp_bow_pipeline\Melusina_DollKit_WIP_20260923.blend')
    marker = {'status': status, 'gate': gate, 'saved_dollkit_wip': True}
except Exception:
    marker = {'status': 'exception', 'trace': traceback.format_exc()[-2000:]}
    try:
        marker['partial_receipt'] = json.load(open(receipt_path))
    except Exception:
        pass
with open(r'C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\p0_done.json', 'w') as f:
    json.dump(marker, f, indent=1)
print('P0_RUNNER_DONE', marker.get('status'))
