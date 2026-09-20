
import unreal, json
MEL = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary

def texmap(path):
    mi = EAL.load_asset(path)
    out = {'path': path, 'parent': mi.get_editor_property('parent').get_path_name() if mi and mi.get_editor_property('parent') else None}
    tex = {}
    if mi:
        for e in (mi.get_editor_property('texture_parameter_values') or []):
            n = str(e.get_editor_property('parameter_info').get_editor_property('name'))
            t = e.get_editor_property('parameter_value')
            tex[n] = t.get_path_name() if t else None
        # available texture param names
        try:
            out['available_tex_params'] = [str(n) for n in MEL.get_texture_parameter_names(mi)]
        except Exception as e:
            out['available_tex_params'] = str(e)
    out['overrides'] = tex
    return out

paths = [
 '/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowSpeedTree_B0_Red',
 '/Game/Melodia/_PROJECT/04_Materials/Plants/Flowers/MI_Plant_Flower_GenericFlower1',
 '/Game/EnvSandbox/Library/FoliageCards/GenericFlower1_Mat',
]
print('TEX', json.dumps([texmap(p) for p in paths], indent=2))
