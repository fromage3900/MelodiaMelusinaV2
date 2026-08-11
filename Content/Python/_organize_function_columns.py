import unreal
import json

lib = unreal.MaterialEditingLibrary
ast = unreal.EditorAssetLibrary

CUTE_FUNC_NAMES = {
    'MF_MeluPaintBase': 'Melu Paint Base ~ the canvas',
    'MF_MeluPaletteColors': 'Melu Palette ~ pick a color, any color',
    'MF_MeluSparkle': 'Melu Sparkle ~ tiny glitter factory',
    'MF_MeluTemporalJitter': 'Melu Jitter ~ wibbly wobbly timey wimey',
    'MF_MeluTriplanar': 'Melu Triplanar ~ no UVs, no problem',
    'MF_AnimeSkinWrap': 'Anime Skin Wrap ~ smooth cel shading',
    'MF_AudioReactiveBlend': 'Audio Reactive Blend ~ dance to the beat',
    'MF_CurvatureOrnament': 'Curvature Ornament ~ edges get the bling',
    'MF_GildingOverlay': 'Gilding Overlay ~ everything but gold',
    'MF_Impressionist_BrushStroke': 'Brush Stroke ~ paint by numbers',
    'MF_Impressionist_Impasto': 'Impasto ~ thicc paint',
    'MF_Impressionist_InkPool': 'Ink Pool ~ puddles of pigment',
    'MF_Impressionist_Temporal': 'Temporal Shimmer ~ living canvas',
    'MF_InkAccumulation': 'Ink Accumulation ~ where the shadows pool',
    'MF_LandscapeHeightCompete': 'Height Compete ~ layers fight, height wins',
    'MF_MapComposite': 'Map Composite ~ texture mixer',
    'MF_MeshBlend_Activator_Index_1': 'Mesh Blend Activator ~ pick a layer',
    'MF_RealParallax': 'Real Parallax ~ fake depth, real magic',
    'MF_SDF_BandRelief': 'Band Relief ~ raised ring carving',
    'MF_SpaceParallax': 'Space Parallax ~ cosmic depth trick',
    'MF_UVTransform': 'UV Transform ~ scoot, scale, spin',
    'MF_VertexPaintBlend': 'Vertex Paint Blend ~ 4-channel mixer',
    'MF_WaterDepthColor': 'Water Depth Color ~ shallow to deep',
    'MF_WaterFoam': 'Water Foam ~ bubbly bits',
    'MF_WaterShorelineFade': 'Shoreline Fade ~ where land meets sea',
}

GROUP_EMOJI_PREFIX = '✦ '  # a small sparkly star, cute but safe across fonts

def pgroup(e):
    try:
        g = e.get_editor_property('group')
    except Exception:
        return None
    if g is None:
        return None
    s = str(g).strip()
    if not s or s == 'None':
        return None
    return s

def organize_function(fn_path):
    fn = unreal.load_asset(fn_path)
    if fn is None:
        return {'path': fn_path, 'error': 'not found'}

    exprs = lib.get_material_function_expressions(fn)
    # clear any pre-existing comment boxes from a prior partial run
    for e in list(exprs):
        if e.get_class().get_name() == 'MaterialExpressionComment':
            lib.delete_material_expression_in_function(fn, e)
    exprs = [e for e in exprs if e.get_class().get_name() != 'MaterialExpressionComment']

    if not exprs:
        return {'path': fn_path, 'skipped': 'empty'}

    short_name = fn_path.split('/')[-1]
    cute_whole = CUTE_FUNC_NAMES.get(short_name, short_name)

    # bucket by param group for grouped params; everything else -> one "whole function" bucket
    buckets = {}
    for e in exprs:
        g = pgroup(e)
        if g:
            buckets.setdefault(GROUP_EMOJI_PREFIX + str(g), []).append(e)
        else:
            buckets.setdefault(cute_whole, []).append(e)

    pad = 80
    manifest_entries = []
    for label, items in buckets.items():
        xs = [e.get_editor_property('material_expression_editor_x') for e in items]
        ys = [e.get_editor_property('material_expression_editor_y') for e in items]
        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)
        box_x = int(minx - pad)
        box_y = int(miny - pad - 50)
        box_w = int(max(maxx - minx + 320, 260))
        box_h = int(max(maxy - miny + 320, 220))

        comment = lib.create_material_expression_in_function(fn, unreal.MaterialExpressionComment, box_x, box_y)
        comment.set_editor_property('text', label)
        comment.set_editor_property('comment_color', unreal.LinearColor(0.55, 0.45, 0.78, 1.0))
        manifest_entries.append({
            'asset_path': fn_path,
            'expression_name': comment.get_name(),
            'size_x': box_w,
            'size_y': box_h,
            'label': label,
        })

    ast.save_loaded_asset(fn)
    return {'path': fn_path, 'bucket_count': len(buckets), 'manifest': manifest_entries}


PATHS = [
    '/Game/_PROJECT/04_Materials/Functions/MF_MeluPaintBase',
    '/Game/_PROJECT/04_Materials/Functions/MF_MeluPaletteColors',
    '/Game/_PROJECT/04_Materials/Functions/MF_MeluSparkle',
    '/Game/_PROJECT/04_Materials/Functions/MF_MeluTemporalJitter',
    '/Game/_PROJECT/04_Materials/Functions/MF_MeluTriplanar',
    '/Game/EnvSandbox/Materials/Functions/MF_AnimeSkinWrap',
    '/Game/EnvSandbox/Materials/Functions/MF_AudioReactiveBlend',
    '/Game/EnvSandbox/Materials/Functions/MF_CurvatureOrnament',
    '/Game/EnvSandbox/Materials/Functions/MF_GildingOverlay',
    '/Game/EnvSandbox/Materials/Functions/MF_Impressionist_BrushStroke',
    '/Game/EnvSandbox/Materials/Functions/MF_Impressionist_Impasto',
    '/Game/EnvSandbox/Materials/Functions/MF_Impressionist_InkPool',
    '/Game/EnvSandbox/Materials/Functions/MF_Impressionist_Temporal',
    '/Game/EnvSandbox/Materials/Functions/MF_InkAccumulation',
    '/Game/EnvSandbox/Materials/Functions/MF_Itto',
    '/Game/EnvSandbox/Materials/Functions/MF_LandscapeHeightCompete',
    '/Game/EnvSandbox/Materials/Functions/MF_Madoka',
    '/Game/EnvSandbox/Materials/Functions/MF_MapComposite',
    '/Game/EnvSandbox/Materials/Functions/MF_MeshBlend_Activator_Index_1',
    '/Game/EnvSandbox/Materials/Functions/MF_NikkiDreamGrade',
    '/Game/EnvSandbox/Materials/Functions/MF_RealParallax',
    '/Game/EnvSandbox/Materials/Functions/MF_SDF_BandRelief',
    '/Game/EnvSandbox/Materials/Functions/MF_SpaceParallax',
    '/Game/EnvSandbox/Materials/Functions/MF_UVTransform',
    '/Game/EnvSandbox/Materials/Functions/MF_VertexPaintBlend',
    '/Game/EnvSandbox/Materials/Functions/MF_WaterDepthColor',
    '/Game/EnvSandbox/Materials/Functions/MF_WaterFoam',
    '/Game/EnvSandbox/Materials/Functions/MF_WaterShorelineFade',
]

all_manifest = []
results = []
for p in PATHS:
    r = organize_function(p)
    results.append({'path': p, 'bucket_count': r.get('bucket_count'), 'error': r.get('error'), 'skipped': r.get('skipped')})
    if 'manifest' in r:
        all_manifest.extend(r['manifest'])

with open('G:/EnvironmentPortfolio/BS_GodFile/Saved/function_comment_manifest.json', 'w') as f:
    json.dump(all_manifest, f, indent=2)

print('TOTAL FUNCTIONS PROCESSED:', len(results))
print('TOTAL COMMENT BOXES NEEDING SIZE:', len(all_manifest))
for r in results:
    print(r)
