import unreal, json
EAL=unreal.EditorAssetLibrary; MEL=unreal.MaterialEditingLibrary
path='/Game/Melodia/_PROJECT/04_Materials/Plants/M_MelodiaPlant_Wind'
m=EAL.load_asset(path)
exprs=[]
try:
    for e in MEL.get_material_expressions(m) or []:
        exprs.append(e.get_class().get_name())
except Exception as ex:
    exprs=['ERR:'+str(ex)]
from collections import Counter
c=Counter(exprs)
# find function calls
fcalls=[]
try:
    for e in MEL.get_material_expressions(m) or []:
        if 'FunctionCall' in e.get_class().get_name():
            try:
                fn=e.get_editor_property('material_function')
                fcalls.append(fn.get_path_name() if fn else None)
            except Exception:
                fcalls.append('?')
except Exception as ex:
    fcalls=[str(ex)]
print('GRAPH', json.dumps({
 'expr_n': len(exprs),
 'top': c.most_common(15),
 'function_calls': fcalls[:30],
 'blend': str(m.get_editor_property('blend_mode')) if m else None,
 'shading': str(m.get_editor_property('shading_model')) if m else None,
}))
