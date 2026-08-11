"""Scrub leftover MooaToon MSM_Toon (enum 16, invalid in stock UE 5.8) from the
converted Substrate Toon masters: reset the legacy ShadingModel to DefaultLit.

Substrate drives shading via the Front Material (Toon BSDF), so the legacy field is
vestigial — this only silences the 'invalid enum value 16' load warning + cleans data.

Headless:
  UnrealEditor-Cmd.exe BS_GodFile.uproject ^
    -ExecutePythonScript=".../scrub_legacy_shadingmodel.py" -unattended -nosplash -nullrhi
"""
import time
import unreal

time.sleep(15)  # cmd runs before asset registry OnFilesLoaded

ROOT = "/Game/EnvSandbox/Materials/Masters"
MASTERS = [
    "M_SDF_TrueParallax", "M_SDF_GildedStucco", "M_SDF_GildedFiligree", "M_SDF_Baroque",
    "M_SDF_OrnamentLayer", "M_SDF_OrnamentLayer_Enhanced", "M_SDF_GothicArchitecture",
    "M_SDF_GothicArchitecture_Enhanced", "M_SDF_RoseWindow", "M_SDF_RayMarch_Gothic",
    "M_HybridStone_SDF", "M_SDF_ReliefPanel", "M_SDF_FiligreeRim", "M_SDF_GothicTracery",
    "M_SDF_HybridStone", "M_SDF_ParallaxPulse", "M_Toon_SDF",
]

fixed, skipped, failed = [], [], []
for name in MASTERS:
    m = unreal.load_asset(f"{ROOT}/{name}")
    if not m:
        skipped.append(name)
        continue
    try:
        m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    except Exception as e:
        failed.append(f"{name}: set {e}")
        continue
    try:
        unreal.MaterialEditingLibrary.recompile_material(m)
    except Exception:
        pass
    try:
        unreal.EditorAssetLibrary.save_loaded_asset(m)
        fixed.append(name)
    except Exception as e:
        failed.append(f"{name}: save {e}")

unreal.log(f"[Scrub] fixed={len(fixed)} skipped={len(skipped)} failed={len(failed)}")
for x in failed:
    unreal.log_warning(f"[Scrub] {x}")
print(f"SCRUB_RESULT fixed={fixed} | failed={failed} | skipped={skipped}")
