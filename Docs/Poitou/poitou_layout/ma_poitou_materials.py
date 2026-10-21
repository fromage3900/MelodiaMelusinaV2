# ma_poitou_materials.py  -  Material Artist -> TAL handoff (MelodiaMelusina / Poitou)
# Run ONLY by the Technical Art Lead, inside the Unreal 5.8 editor (Python).
# Idempotent: existing assets are SKIPPED, never overwritten. No level / landscape changes.
# Nothing is saved unless SAVE is flipped to True. Does not reload packages.
# Palette = proposals (palette_and_master_MA.md v2), pending reference board.
import unreal

SAVE = False          # TAL: set True to save the assets this script CREATED (only those)
ROOT = "/Game/EnvSandbox/Poitou/Materials"
LAYERINFO_DIR = ROOT + "/LayerInfo"
LANDSCAPE_MAT = "M_Poitou_Landscape"
TOON_PARENT = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"

# Landscape layers: names EXACTLY = Houdini mask channels (export/mask_<channel>_1009.png)
# (channel, sRGB hex albedo, roughness)
LANDSCAPE_LAYERS = [
    ("wet_meadow_grass",        "#68735D", 0.90),  # board 6/5 meadow green
    ("canal_banks",             "#555D38", 0.85),  # board 1 damp bank grass/mud
    ("village_buildings",       "#A08F6C", 0.80),  # board 3 trodden earth / limestone gravel
    ("ruin_rise",               "#9A9384", 0.85),  # board 4/7A weathered limestone
    ("tree_rows_poplar_ash",    "#44513E", 0.92),  # board 6 shaded understory
    ("mist_marsh_reeds",        "#93A179", 0.80),  # board 6 pale reed green
    ("mist_volume",             "#7E8770", 0.88),  # neutral marsh ground (channel is atmosphere-driven)
    ("water",                   "#2F3A2C", 0.30),  # canal bed / wet mud under water plane
]

# MIs of the toon universal master. Values set ONLY if param exists on parent.
MIS = {
    "MI_Poitou_LimeWash":  {"vec": {"BaseTint": "#E6DFCC", "MossColor": "#5F6B3B", "MistColor": "#DCE3E4"}, "scal": {"Roughness": 0.88}},
    "MI_Poitou_Tile":      {"vec": {"BaseTint": "#C07A57", "MossColor": "#5F6B3B", "MistColor": "#DCE3E4"}, "scal": {"Roughness": 0.80}},
    "MI_Poitou_Slate":     {"vec": {"BaseTint": "#4E555C", "MossColor": "#5F6B3B", "MistColor": "#DCE3E4"}, "scal": {"Roughness": 0.55}},
    "MI_Poitou_Oak":       {"vec": {"BaseTint": "#A58A66", "MossColor": "#5F6B3B", "MistColor": "#DCE3E4"}, "scal": {"Roughness": 0.80}},
    "MI_Poitou_Tar":       {"vec": {"BaseTint": "#26221E", "MistColor": "#DCE3E4"},                         "scal": {"Roughness": 0.65}},
    "MI_Poitou_RuinStone": {"vec": {"BaseTint": "#9A9384", "MossColor": "#5F6B3B", "MistColor": "#DCE3E4"}, "scal": {"Roughness": 0.85}},
}
# Shared morning-dawn look (applied to every MI if params exist; strengths left at parent defaults)
SHARED_VEC = {"DawnLowColor": "#AAB8AF", "DawnHighColor": "#EAEFF6", "DreamRimColor": "#DCE3E4"}

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
log, created = [], []

def srgb_to_linear(hexs):
    h = hexs.lstrip("#")
    def c(v):
        v = int(v, 16) / 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return unreal.LinearColor(c(h[0:2]), c(h[2:4]), c(h[4:6]), 1.0)

def path(d, n): return "%s/%s" % (d, n)

# ---------------- (a) landscape material ----------------
def build_landscape_material():
    p = path(ROOT, LANDSCAPE_MAT)
    if EAL.does_asset_exist(p):
        log.append("SKIP exists: " + p); return
    mat = TOOLS.create_asset(LANDSCAPE_MAT, ROOT, unreal.Material, unreal.MaterialFactoryNew())
    if not mat:
        log.append("FAIL create " + p); return
    created.append(mat)
    def make_blend(y, values):
        lb = MEL.create_material_expression(mat, unreal.MaterialExpressionLandscapeLayerBlend, -600, y)
        inputs = []
        for name, val in values:
            li = unreal.LayerBlendInput()
            li.set_editor_property("layer_name", name)
            li.set_editor_property("blend_type", unreal.LandscapeLayerBlendType.LB_WEIGHT_BLEND)
            li.set_editor_property("preview_weight", 1.0 if name == LANDSCAPE_LAYERS[0][0] else 0.0)
            li.set_editor_property("const_layer_input", val)   # constant per-layer value, no texture
            inputs.append(li)
        lb.set_editor_property("layers", inputs)
        return lb
    col = make_blend(0,   [(n, unreal.Vector(*[getattr(srgb_to_linear(h), k) for k in "rgb"])) for n, h, r in LANDSCAPE_LAYERS])
    rgh = make_blend(400, [(n, unreal.Vector(r, r, r)) for n, h, r in LANDSCAPE_LAYERS])
    # Roughness: Vector -> take R via ComponentMask
    mask = MEL.create_material_expression(mat, unreal.MaterialExpressionComponentMask, -300, 400)
    mask.set_editor_property("r", True); mask.set_editor_property("g", False)
    mask.set_editor_property("b", False); mask.set_editor_property("a", False)
    MEL.connect_material_expressions(rgh, "", mask, "")
    ok1 = MEL.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
    ok2 = MEL.connect_material_property(mask, "", unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.recompile_material(mat)
    log.append("CREATED %s (layers=%s, basecolor=%s, roughness=%s)" % (p, [l[0] for l in LANDSCAPE_LAYERS], ok1, ok2))

# ---------------- (b) layer info objects ----------------
def build_layer_infos():
    for name, _, _ in LANDSCAPE_LAYERS:
        an = "LI_Poitou_" + name
        p = path(LAYERINFO_DIR, an)
        if EAL.does_asset_exist(p):
            log.append("SKIP exists: " + p); continue
        try:
            li = TOOLS.create_asset(an, LAYERINFO_DIR, unreal.LandscapeLayerInfoObject, None)
        except Exception as e:
            li = None; log.append("LayerInfo create error %s: %s" % (an, e))
        if not li:
            log.append("NOTE: could not create %s via Python; create from Landscape > Paint (Weight-Blended Layer, name '%s')" % (an, name)); continue
        created.append(li)
        set_ok = False
        for prop in ("layer_name", "LayerName"):
            try:
                li.set_editor_property(prop, name); set_ok = True; break
            except Exception:
                pass
        if not set_ok:
            try:
                li.set_layer_name(name, False); set_ok = True   # newer API, if present
            except Exception as e:
                log.append("WARN %s: layer_name not settable from Python (%s); set it manually to '%s'" % (an, e, name))
        log.append("CREATED %s (layer_name set=%s)" % (p, set_ok))

# ---------------- (c) toon MIs ----------------
def build_mis():
    parent = unreal.load_asset(TOON_PARENT)
    if not parent:
        log.append("FAIL: parent not found " + TOON_PARENT); return
    vnames = set(str(n) for n in MEL.get_vector_parameter_names(parent))
    snames = set(str(n) for n in MEL.get_scalar_parameter_names(parent))
    for mi_name, spec in MIS.items():
        p = path(ROOT, mi_name)
        if EAL.does_asset_exist(p):
            log.append("SKIP exists: " + p); continue
        mi = TOOLS.create_asset(mi_name, ROOT, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        if not mi:
            log.append("FAIL create " + p); continue
        created.append(mi)
        MEL.set_material_instance_parent(mi, parent)
        done, skipped = [], []
        vec = dict(SHARED_VEC); vec.update(spec.get("vec", {}))
        for k, hx in vec.items():
            if k in vnames:
                MEL.set_material_instance_vector_parameter_value(mi, k, srgb_to_linear(hx)); done.append("%s=%s" % (k, hx))
            else:
                skipped.append(k)
        for k, v in spec.get("scal", {}).items():
            if k in snames:
                MEL.set_material_instance_scalar_parameter_value(mi, k, v); done.append("%s=%s" % (k, v))
            else:
                skipped.append(k)
        MEL.update_material_instance(mi)
        log.append("CREATED %s set[%s] missing[%s]" % (p, ", ".join(done), ", ".join(skipped)))

for step in (build_landscape_material, build_layer_infos, build_mis):
    try:
        step()
    except Exception as e:
        log.append("ERROR in %s: %s" % (step.__name__, e))

if SAVE:
    for a in created:
        EAL.save_loaded_asset(a, only_if_is_dirty=False)
    log.append("SAVED %d created assets" % len(created))
else:
    log.append("NOT SAVED (SAVE=False). %d assets created in memory." % len(created))
log.append("No landscape assignment, no level changes performed.")
print("\n".join(["[ma_poitou_materials] " + l for l in log]))
