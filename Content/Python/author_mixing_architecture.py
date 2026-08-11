"""Author the Melodia mixing architecture: SoundClasses + Submixes.

Replicates the proven ElectricDreamsEnv structure (SCLASS_Main/Amb/Mus +
SUBMIX_Main/Sfx/Mus/Amb) with a Voice class added for dialogue-over-BGM
ducking later.

Tree:
  /Game/Melodia/Audio/Mix/
    SoundClasses/SCL_Master, SCL_Music, SCL_SFX, SCL_Voice, SCL_Ambience
    Submixes/SUBMIX_Music, SUBMIX_SFX, SUBMIX_Voice, SUBMIX_Ambience
"""
import unreal

MIX_ROOT = "/Game/Melodia/Audio/Mix"
SC_DIR = f"{MIX_ROOT}/SoundClasses"
SM_DIR = f"{MIX_ROOT}/Submixes"

# SoundClass -> parent name (None = Master)
SC_TREE = {
    "SCL_Master": None,
    "SCL_Music": "SCL_Master",
    "SCL_SFX": "SCL_Master",
    "SCL_Voice": "SCL_Master",
    "SCL_Ambience": "SCL_Master",
}

# Submix -> parent (None = Master)
SM_TREE = {
    "SUBMIX_Music": None,
    "SUBMIX_SFX": None,
    "SUBMIX_Voice": None,
    "SUBMIX_Ambience": None,
}

tools = unreal.AssetToolsHelpers.get_asset_tools()


def ensure_dir(p):
    if not unreal.EditorAssetLibrary.does_directory_exist(p):
        unreal.EditorAssetLibrary.make_directory(p)


def make_asset(name, folder, factory, asset_class):
    path = f"{folder}/{name}.{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.EditorAssetLibrary.load_asset(path)
    a = tools.create_asset(name, folder, asset_class, factory)
    if a:
        unreal.EditorAssetLibrary.save_loaded_asset(a, only_if_is_dirty=False)
    return a


ensure_dir(MIX_ROOT)
ensure_dir(SC_DIR)
ensure_dir(SM_DIR)

# --- SoundClasses ---
sc_assets = {}
for name, parent in SC_TREE.items():
    sc = make_asset(name, SC_DIR, unreal.SoundClassFactory(), unreal.SoundClass)
    if not sc:
        print(f"FAIL_SC {name}")
        continue
    sc_assets[name] = sc
    if parent and parent in sc_assets:
        try:
            sc.set_editor_property("parent", sc_assets[parent])
        except Exception:
            try:
                sc.set_editor_property("parent_sound_class", sc_assets[parent])
            except Exception as e2:
                print(f"WARN_SC_PARENT {name}: {e2}")
        unreal.EditorAssetLibrary.save_loaded_asset(sc, only_if_is_dirty=False)
    print(f"SC {name} parent={parent}")

# --- Submixes ---
sm_assets = {}
for name in SM_TREE:
    sm = make_asset(name, SM_DIR, unreal.SoundSubmixFactory(), unreal.SoundSubmix)
    if not sm:
        print(f"FAIL_SM {name}")
        continue
    sm_assets[name] = sm
    print(f"SM {name}")

print("MIX_AUTHORED")
try:
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
except Exception:
    pass
