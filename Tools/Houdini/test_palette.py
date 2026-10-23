import unreal

# Try loading the Palette Melusina material
mi_path = '/Game/EnvSandbox/Materials/Masters/M_Palette_Melusina'
mi = unreal.EditorAssetLibrary.load_asset(mi_path)
print(f'Loaded: {mi_path}, class: {type(mi).__name__}')

if mi:
    exprs = unreal.MaterialEditingLibrary.get_material_expressions(mi)
    print(f'Found {len(exprs)} expressions')
    for e in exprs:
        pname = e.parameter_name if hasattr(e, 'parameter_name') else 'N/A'
        pt = type(e).__name__
        inputs = e.inputs if hasattr(e, 'inputs') else 'N/A'
        print(f'  {pt} param="{pname}" inputs={inputs if isinstance(inputs, int) else "?"}')
        if pt == 'MaterialExpressionCollectionParameter':
            col = e.collection if hasattr(e, 'collection') else None
            print(f'    -> Collection: {col}')
            if col:
                print(f'    -> Collection name: {col.get_editor_property("name", "N/A")}')