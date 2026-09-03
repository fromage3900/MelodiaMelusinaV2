"""Parameterize 12 MI_Cosmic instances for Cosmic Orrery."""
from __future__ import annotations

import unreal

COSMIC_INSTANCES = [
    ("MI_Cosmic_AuroraVeil", {"CosmicColor": (0.3, 0.7, 1.0, 1.0), "EmissionStrength": 3.0, "RotationSpeed": 0.15, "SDF_Shape": 2}),
    ("MI_Cosmic_BlueNebulaA", {"CosmicColor": (0.1, 0.3, 0.9, 1.0), "EmissionStrength": 2.5, "RotationSpeed": 0.08, "SDF_Shape": 0}),
    ("MI_Cosmic_BlueNebulaB", {"CosmicColor": (0.0, 0.5, 1.0, 1.0), "EmissionStrength": 2.2, "RotationSpeed": 0.12, "SDF_Shape": 1}),
    ("MI_Cosmic_BlueNebulaC", {"CosmicColor": (0.2, 0.6, 0.8, 1.0), "EmissionStrength": 1.8, "RotationSpeed": 0.10, "SDF_Shape": 0}),
    ("MI_Cosmic_EclipseHalo", {"CosmicColor": (0.8, 0.2, 0.1, 1.0), "EmissionStrength": 4.0, "RotationSpeed": 0.05, "SDF_Shape": 3}),
    ("MI_Cosmic_PurpleNebulaA", {"CosmicColor": (0.6, 0.1, 0.9, 1.0), "EmissionStrength": 2.8, "RotationSpeed": 0.09, "SDF_Shape": 1}),
    ("MI_Cosmic_PurpleNebulaB", {"CosmicColor": (0.4, 0.0, 0.8, 1.0), "EmissionStrength": 2.4, "RotationSpeed": 0.11, "SDF_Shape": 2}),
    ("MI_Cosmic_PurpleNebulaC", {"CosmicColor": (0.5, 0.2, 0.7, 1.0), "EmissionStrength": 2.0, "RotationSpeed": 0.07, "SDF_Shape": 0}),
    ("MI_Cosmic_StarfieldA", {"CosmicColor": (1.0, 1.0, 0.9, 1.0), "EmissionStrength": 1.5, "RotationSpeed": 0.02, "SDF_Shape": 4}),
    ("MI_Cosmic_StarfieldB", {"CosmicColor": (0.9, 0.95, 1.0, 1.0), "EmissionStrength": 1.2, "RotationSpeed": 0.01, "SDF_Shape": 4}),
    ("MI_Cosmic_StarfieldC", {"CosmicColor": (0.85, 0.9, 1.0, 1.0), "EmissionStrength": 1.0, "RotationSpeed": 0.03, "SDF_Shape": 4}),
    ("MI_Cosmic_VoidDeep", {"CosmicColor": (0.02, 0.02, 0.08, 1.0), "EmissionStrength": 0.3, "RotationSpeed": 0.00, "SDF_Shape": 5}),
]

BASE_PATH = "/Game/EnvSandbox/Materials/SDF/Instances/"


def main():
    updated = 0
    for mi_name, params in COSMIC_INSTANCES:
        path = BASE_PATH + mi_name + "." + mi_name
        mi = unreal.load_asset(path)
        if not mi:
            unreal.log_warning(f"[CosmicPolish] Missing: {path}")
            continue

        for param_name, value in params.items():
            try:
                if isinstance(value, tuple):
                    mi.set_editor_property(param_name, unreal.LinearColor(*value))
                else:
                    mi.set_editor_property(param_name, value)
            except Exception as e:
                unreal.log_warning(f"[CosmicPolish] {mi_name}.{param_name} failed: {e}")

        unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=True)
        updated += 1
        unreal.log(f"[CosmicPolish] Updated {mi_name}: {params}")

    unreal.log(f"[CosmicPolish] Complete: {updated}/12 instances parameterized")
    return updated


if __name__ == "__main__":
    main()