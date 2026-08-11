"""Finalize 12 MI_Cosmic instances with distinct parameter values for Cosmic Orrery.

Each celestial body gets unique:
- CosmicColor (Vector4) - palette per body
- EmissionStrength (Float) - core vs ring vs orbit
- RotationSpeed (Float) - orbital dynamics
- SDF_Shape (Enum/int) - sphere/torus/helix per body
"""
from __future__ import annotations

import unreal

# 12 MI_Cosmic instances in Content/EnvSandbox/Materials/SDF/Instances/
MI_COSMIC_INSTANCES = [
    ("MI_Cosmic_AuroraVeil",        {"CosmicColor": (0.2, 0.8, 1.0, 1.0), "EmissionStrength": 2.5, "RotationSpeed": 0.3, "SDF_Shape": 0}),   # Sphere
    ("MI_Cosmic_BlueNebulaA",       {"CosmicColor": (0.1, 0.4, 1.0, 1.0), "EmissionStrength": 1.8, "RotationSpeed": 0.5, "SDF_Shape": 1}),   # Torus
    ("MI_Cosmic_BlueNebulaB",       {"CosmicColor": (0.0, 0.6, 0.9, 1.0), "EmissionStrength": 1.5, "RotationSpeed": 0.4, "SDF_Shape": 2}),   # Helix
    ("MI_Cosmic_BlueNebulaC",       {"CosmicColor": (0.3, 0.7, 1.0, 1.0), "EmissionStrength": 2.0, "RotationSpeed": 0.6, "SDF_Shape": 0}),
    ("MI_Cosmic_EclipseHalo",       {"CosmicColor": (0.0, 0.0, 0.0, 1.0), "EmissionStrength": 3.0, "RotationSpeed": 0.2, "SDF_Shape": 3}),   # Ring
    ("MI_Cosmic_PurpleNebulaA",     {"CosmicColor": (0.6, 0.2, 1.0, 1.0), "EmissionStrength": 2.2, "RotationSpeed": 0.4, "SDF_Shape": 1}),
    ("MI_Cosmic_PurpleNebulaB",     {"CosmicColor": (0.8, 0.3, 0.9, 1.0), "EmissionStrength": 1.9, "RotationSpeed": 0.5, "SDF_Shape": 2}),
    ("MI_Cosmic_PurpleNebulaC",     {"CosmicColor": (0.5, 0.1, 0.8, 1.0), "EmissionStrength": 1.6, "RotationSpeed": 0.3, "SDF_Shape": 0}),
    ("MI_Cosmic_StarfieldA",        {"CosmicColor": (1.0, 1.0, 1.0, 1.0), "EmissionStrength": 1.0, "RotationSpeed": 0.1, "SDF_Shape": 4}),   # Points
    ("MI_Cosmic_StarfieldB",        {"CosmicColor": (0.9, 0.9, 1.0, 1.0), "EmissionStrength": 0.8, "RotationSpeed": 0.15, "SDF_Shape": 4}),
    ("MI_Cosmic_StarfieldC",        {"CosmicColor": (1.0, 0.95, 0.9, 1.0), "EmissionStrength": 1.2, "RotationSpeed": 0.08, "SDF_Shape": 4}),
    ("MI_Cosmic_VoidDeep",          {"CosmicColor": (0.02, 0.02, 0.08, 1.0), "EmissionStrength": 0.3, "RotationSpeed": 0.05, "SDF_Shape": 5}),  # Void
]

MASTER_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Cosmic"

def set_instance_params(instance_name: str, params: dict) -> bool:
    """Set scalar/vector parameters on a material instance."""
    path = f"/Game/EnvSandbox/Materials/SDF/Instances/{instance_name}.{instance_name}"
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.log_warning(f"[CosmicPolish] MI not found: {path}")
        return False
    
    mi = unreal.load_asset(path)
    if not mi:
        unreal.log_error(f"[CosmicPolish] Failed to load: {path}")
        return False
    
    for param_name, value in params.items():
        try:
            if isinstance(value, tuple) and len(value) == 4:
                # Vector4
                vec = unreal.LinearColor(*value)
                unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(mi, param_name, vec)
            elif isinstance(value, (int, float)):
                # Scalar
                unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, param_name, float(value))
            else:
                unreal.log_warning(f"[CosmicPolish] Unknown param type for {param_name}: {type(value)}")
        except Exception as e:
            unreal.log_error(f"[CosmicPolish] Failed to set {param_name} on {instance_name}: {e}")
            return False
    
    unreal.log(f"[CosmicPolish] Updated {instance_name}: {params}")
    return True


def main():
    unreal.log("[CosmicPolish] Starting 12 MI_Cosmic parameter finalization...")
    success = 0
    for name, params in MI_COSMIC_INSTANCES:
        if set_instance_params(name, params):
            success += 1
    
    unreal.log(f"[CosmicPolish] Complete: {success}/{len(MI_COSMIC_INSTANCES)} instances updated")
    return success == len(MI_COSMIC_INSTANCES)


if __name__ == "__main__":
    main()