# ma_poitou_horizon.py  -  Material Artist -> TAL handoff (Poitou horizon / far band MIs)
# Run ONLY by TAL in the Unreal 5.8 editor. Idempotent: skips existing assets.
# Sets params only if they exist on the parent. No reload, no level changes. SAVE=False default.
import unreal

SAVE = False
ROOT = "/Game/EnvSandbox/Poitou/Materials"
TOON_PARENT = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
FADE_HEX = "#DCE3E4"   # P_Mist_Tint

# Param names verified read-only on M_Master_Toon_Universal (2026-10-20):
#   vectors: BaseTint, AtmosphericFadeColor, MistColor
#   scalars: MistStrength, DistanceFadeStrength (no 'AtmosphericFadeStrength' exists)
MIS = {
    "MI_Poitou_Poplar_Band1": {"BaseTint": "#68735D", "MistStrength": 0.20, "DistanceFadeStrength": 0.20},
    "MI_Poitou_Poplar_Band2": {"BaseTint": "#8E9A8C", "MistStrength": 0.45, "DistanceFadeStrength": 0.45},
    "MI_Poitou_Poplar_Band3": {"BaseTint": "#B9C4C6", "MistStrength": 0.70, "DistanceFadeStrength": 0.70},
    "MI_Poitou_FarStone":     {"BaseTint": "#B4B2A8", "MistStrength": 0.45, "DistanceFadeStrength": 0.45},
}
SHARED = {"AtmosphericFadeColor": FADE_HEX, "MistColor": FADE_HEX}

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

def run():
    parent = unreal.load_asset(TOON_PARENT)
    if not parent:
        log.append("FAIL: parent not found " + TOON_PARENT); return
    vnames = set(str(n) for n in MEL.get_vector_parameter_names(parent))
    snames = set(str(n) for n in MEL.get_scalar_parameter_names(parent))
    for name, spec in MIS.items():
        p = "%s/%s" % (ROOT, name)
        if EAL.does_asset_exist(p):
            log.append("SKIP exists: " + p); continue
        mi = TOOLS.create_asset(name, ROOT, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        if not mi:
            log.append("FAIL create " + p); continue
        created.append(mi)
        MEL.set_material_instance_parent(mi, parent)
        params = dict(SHARED); params.update(spec)
        done, missing = [], []
        for k, v in params.items():
            if isinstance(v, str):
                if k in vnames:
                    MEL.set_material_instance_vector_parameter_value(mi, k, srgb_to_linear(v)); done.append("%s=%s" % (k, v))
                else:
                    missing.append(k)
            else:
                if k in snames:
                    MEL.set_material_instance_scalar_parameter_value(mi, k, float(v)); done.append("%s=%s" % (k, v))
                else:
                    missing.append(k)
        MEL.update_material_instance(mi)
        log.append("CREATED %s set[%s] missing[%s]" % (p, ", ".join(done), ", ".join(missing)))

try:
    run()
except Exception as e:
    log.append("ERROR: %s" % e)

if SAVE:
    for a in created:
        EAL.save_loaded_asset(a, only_if_is_dirty=False)
    log.append("SAVED %d created assets" % len(created))
else:
    log.append("NOT SAVED (SAVE=False). %d assets created in memory." % len(created))
print("\n".join("[ma_poitou_horizon] " + l for l in log))
