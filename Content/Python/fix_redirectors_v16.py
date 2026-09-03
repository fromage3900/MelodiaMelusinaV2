import unreal

def fix_all_redirectors():
    # Search the entire Content root
    all_assets = unreal.EditorAssetLibrary.list_assets('/', recursive=True, include_folder=False)
    unreal.log('Total assets scanned: {}'.format(len(all_assets)))
    
    redirectors = []
    for p in all_assets:
        try:
            ad = unreal.EditorAssetLibrary.find_asset_data(p)
            cls_name = str(ad.asset_class)
            if cls_name == 'ObjectRedirector':
                redirectors.append(p)
        except:
            pass
    
    unreal.log('Redirectors found: {}'.format(len(redirectors)))
    
    for r in redirectors:
        unreal.log('  {}'.format(r))
    
    if not redirectors:
        unreal.log('No redirectors to fix')
        return
    
    # Try asset tools fixup
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    for fn_name in ['fix_up_redirectors', 'fixup_referencers', 'fix_up_referencers']:
        fn = getattr(asset_tools, fn_name, None)
        if fn:
            unreal.log('Trying {}...'.format(fn_name))
            try:
                fn(redirectors)
                unreal.log('{} succeeded!'.format(fn_name))
                return
            except Exception as ex:
                unreal.log('{} failed: {}'.format(fn_name, str(ex)))
    
    # Plan B: delete redirectors directly
    unreal.log('Plan B: deleting redirectors...')
    for r in redirectors:
        try:
            unreal.EditorAssetLibrary.delete_asset(r)
            unreal.log('  Deleted: {}'.format(r))
        except Exception as ex:
            unreal.log('  Failed to delete {}: {}'.format(r, str(ex)))
    
    unreal.log('DONE')

fix_all_redirectors()
