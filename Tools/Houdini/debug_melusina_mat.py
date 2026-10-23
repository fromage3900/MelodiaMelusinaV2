import hou, os, json

# Try loading the Melusina master from the most common path
paths_to_try = [
    '/Game/EnvSandbox/Materials/Masters/M_Melusina',
    '/Game/Melodia/_PROJECT/04_Materials/M_Melusina',
    '/Game/_PROJECT/04_Materials/M_Melusina',
]

for mp in paths_to_try:
    try:
        m = hou.AssetLibrary.load_asset(mp)
        if m:
            print(f'SUCCESS: {mp}')
            exprs = hou.MaterialEditingLibrary.get_material_expressions(m)
            if exprs:
                for e in exprs:
                    pname = e.get_editor_property('parameter_name', '') or '(no name)'
                    inputs = e.get_editor_property('inputs', [])
                    print(f'  Expression: {type(e).__name__} param="{pname}" inputs={len(inputs)}')
                    # Check if it's a CollectionParameter
                    if type(e).__name__ == 'MaterialExpressionCollectionParameter':
                        col = e.get_editor_property('collection', None)
                        pname2 = e.get_editor_property('parameter_name', '')
                        print(f'    -> Collection: {col}, param_name: {pname2}')
            else:
                print('  No expressions')
        else:
            print(f'FAILED: {mp}')
    except Exception as ex:
        print(f'ERROR {mp}: {ex}')