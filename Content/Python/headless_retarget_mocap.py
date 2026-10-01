"""Headless mocap retarget — run with the editor CLOSED, no modals.

Prefer Tools/run_headless_mocap_retarget.ps1 from the repo root. Manual example:

    & 'C:\\Program Files\\Epic Games\\UE_5.8\\Engine\\Binaries\\Win64\\UnrealEditor-Cmd.exe' `
      '<repo>\\BS_GodFile.uproject' `
      -run=pythonscript -script='<repo>/Content/Python/headless_retarget_mocap.py' `
      -unattended -nop4 -nosplash

Retargets every A_Src_* clip in /Game/Melodia/Mocap/Source/Anims onto SK_Melusina_V2_Body via
RTG_Mocap_to_Melusina_Current (canonical, targets IK_Melusina_Body_Current), writes A_Mocap_*
into the Melusina Animations/Mocap folder, saves each, and writes a validity report to
Saved/Melodia/retarget_report.json. Existing output clips are preserved by default;
call main(overwrite_existing=True) only for an explicitly approved replacement.

Both V1 (SK_Melusina) and V2 (SK_Melusina_V2_*) meshes bind SK_Melusina_Skeleton, so every
clip this script produces plays on V2 via leader pose with zero re-retargeting.

Why headless: the interactive batch retarget pops a per-clip "Duplicating animation | Cancel"
modal that severs the Monolith MCP socket and (when the editor is under concurrent access or
crash-recovered) silently cancels, producing 0 or null-skeleton assets. -run=pythonscript has
no Slate modals, so the batch runs clean.
"""
import unreal, json, os

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
RTG = '/Game/Melodia/Mocap/Retarget/RTG_Mocap_to_Melusina_Current'
SRC_MESH = '/Game/Melodia/Mocap/Source/SK_MocapSource'
TGT_MESH = '/Game/Melodia/Characters/Melusina/Outfits/V2/SK_Melusina_V2_Body'
SRC_DIR = '/Game/Melodia/Mocap/Source/Anims'
OUT_DIR = '/Game/Melodia/Characters/Melusina/Animations/Mocap'
REPORT = os.path.join(_PROJECT_ROOT, 'Saved', 'Melodia', 'retarget_report.json')


def main(overwrite_existing=False):
    rtg = unreal.load_asset(RTG)
    sm = unreal.load_asset(SRC_MESH)
    tm = unreal.load_asset(TGT_MESH)

    tgt_skel = unreal.load_asset('/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton')
    if not all((rtg, sm, tm, tgt_skel)):
        raise RuntimeError('Retarget assets are missing; no clips written')
    if tm.get_editor_property('skeleton') != tgt_skel:
        raise RuntimeError('V2 body is not bound to the canonical skeleton; no clips written')
    # Use the reviewed mappings without rebinding/saving the hero mesh or remapping the rig.

    src_paths = [a.split('.')[0] for a in unreal.EditorAssetLibrary.list_assets(SRC_DIR, False, False)]
    report = []
    for sp in src_paths:
        name = sp.split('/')[-1]
        try:
            source = unreal.load_asset(sp)
            if not isinstance(source, unreal.AnimSequence) or source.get_editor_property('skeleton') != sm.get_editor_property('skeleton'):
                raise RuntimeError('Source clip does not use SK_MocapSource\'s skeleton; no clip written')
            ad = unreal.EditorAssetLibrary.find_asset_data(sp)
            inp = unreal.IKRetargetBatchOperationInputs()
            inp.set_editor_property('assets_to_retarget', [ad])
            inp.set_editor_property('source_mesh', sm)
            inp.set_editor_property('target_mesh', tm)
            inp.set_editor_property('ik_retarget_asset', rtg)
            inp.set_editor_property('target_path', OUT_DIR)
            inp.set_editor_property('search', 'A_Src_')
            inp.set_editor_property('replace', 'A_Mocap_')
            inp.set_editor_property('overwrite_existing_files', overwrite_existing)
            inp.set_editor_property('use_source_path', False)
            created = unreal.IKRetargetBatchOperation().run_batch_retarget(inp) or []
            entry = {'src': name, 'created': [str(c.package_name) for c in created], 'ok': False, 'skeleton': None}
            for c in created:
                obj = unreal.AssetRegistryHelpers.get_asset(c)
                if obj:
                    unreal.EditorAssetLibrary.save_loaded_asset(obj)
                    sk = obj.get_editor_property('skeleton')
                    entry['skeleton'] = sk.get_name() if sk else None
                    entry['ok'] = sk == tgt_skel
            report.append(entry)
        except Exception as exc:
            report.append({'src': name, 'error': str(exc), 'ok': False})

    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, 'w') as fh:
        json.dump(report, fh, indent=1)
    ok = sum(1 for r in report if r.get('ok'))
    unreal.log(f'[HeadlessRetarget] {ok}/{len(report)} clips retargeted with valid skeleton')


main()
