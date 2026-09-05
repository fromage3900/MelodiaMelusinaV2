"""Import Gaea weightmap textures into the Landscape's PAINT layers.

The material multiplies each Gaea mask by LandscapeLayerSample(<layer>), so an
unpainted layer makes its mask contribute nothing -- the mask can only subtract
coverage, never add it. Importing the weightmaps as textures (which the earlier
script did) is therefore only half the pipeline; this is the other half.
"""
import unreal

RT_PATH = "/Game/EnvSandbox/Temp/RT_GaeaWeight"
BLIT_MAT = "/Game/EnvSandbox/Temp/M_GaeaWeightBlit"
TEX_DIR = "/Game/Gaea/Glacier/Textures/"
RES = 1009  # 16 components x 63 quads + 1

PAIRS = [
    ("W_Glacier_Water", "Water"),
    ("W_Glacier_Rock", "Rock"),
    ("W_Glacier_Snow", "Snow"),
]


def _rt():
    rt = unreal.load_asset(RT_PATH)
    if rt is None:
        at = unreal.AssetToolsHelpers.get_asset_tools()
        rt = at.create_asset("RT_GaeaWeight", "/Game/EnvSandbox/Temp",
                             unreal.TextureRenderTarget2D,
                             unreal.TextureRenderTargetFactoryNew())
    rt.set_editor_property("size_x", RES)
    rt.set_editor_property("size_y", RES)
    rt.set_editor_property("render_target_format",
                           unreal.TextureRenderTargetFormat.RTF_RGBA8)
    return rt


def sample(landscape, layers, stride=16):
    comps = list(landscape.get_components_by_class(unreal.LandscapeComponent))
    sel = [comps[i] for i in range(0, len(comps), stride)]
    out = {}
    for L in layers:
        vals = []
        for c in sel:
            o = c.get_world_location()
            for dx, dy in ((0, 0), (2000, 2000), (-2000, -2000)):
                try:
                    vals.append(c.editor_get_paint_layer_weight_by_name_at_location(
                        unreal.Vector(o.x + dx, o.y + dy, o.z), L))
                except Exception:
                    pass
        out[L] = (len(vals), sum(1 for v in vals if v > 0.001),
                  max(vals) if vals else -1,
                  sum(vals) / len(vals) if vals else -1)
    return out


def report(tag, landscape, layers):
    print(f"  [{tag}]")
    for L, (n, nz, mx, mean) in sample(landscape, layers).items():
        print(f"     {L:<6} n={n} nonzero={nz} max={mx:.4f} mean={mean:.4f}")


def run(pairs=PAIRS):
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = ues.get_editor_world()
    ls = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Landscape)[0]

    layers = [p[1] for p in pairs]
    report("before", ls, layers)

    rt = _rt()
    mat = unreal.load_asset(BLIT_MAT)
    mid = unreal.MaterialEditingLibrary.create_material_instance_dynamic(mat) \
        if hasattr(unreal.MaterialEditingLibrary, "create_material_instance_dynamic") \
        else unreal.MaterialLibrary.create_dynamic_material_instance(world, mat)

    for tex_name, layer in pairs:
        tex = unreal.load_asset(TEX_DIR + tex_name)
        if tex is None:
            print(f"  MISSING texture {tex_name}")
            continue
        mid.set_texture_parameter_value("Tex", tex)
        unreal.RenderingLibrary.clear_render_target2d(world, rt)
        unreal.RenderingLibrary.draw_material_to_render_target(world, rt, mid)
        try:
            ls.landscape_import_weightmap_from_render_target(rt, layer)
            print(f"  imported {tex_name} -> paint layer '{layer}'")
        except Exception as e:
            print(f"  FAILED {tex_name} -> '{layer}': {e}")

    report("after", ls, layers)
