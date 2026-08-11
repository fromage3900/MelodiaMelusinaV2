"""Add V3 CelSteps to PortfolioHero grade profile."""
import unreal
MEL = unreal.MaterialEditingLibrary

profiles = [
    ("GameplayStandard", "/Game/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles/MI_MeluColorGrade_GameplayStandard", {
        "CelSteps": 0.0,
        "DynamicContrast": 0.0,
        "SelectiveStrength": 0.0,
    }),
    ("Narrative", "/Game/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles/MI_MeluColorGrade_Narrative", {
        "CelSteps": 0.0,
        "DynamicContrast": 0.1,
        "SelectiveStrength": 0.0,
    }),
    ("PortfolioHero", "/Game/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles/MI_MeluColorGrade_PortfolioHero", {
        "CelSteps": 4.0,
        "DynamicContrast": 0.15,
        "SelectiveStrength": 0.0,
    }),
]

for name, path, params in profiles:
    mi = unreal.load_asset(path)
    if not mi:
        print(f"{name}: NOT FOUND")
        continue
    count = 0
    for pname, pval in params.items():
        try:
            MEL.set_material_instance_scalar_parameter_value(mi, pname, pval)
            count += 1
        except Exception as ex:
            print(f"  {pname}: {str(ex)[:60]}")
    unreal.EditorAssetLibrary.save_asset(path)
    print(f"{name}: {count} V3 params set")
