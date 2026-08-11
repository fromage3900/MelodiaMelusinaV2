"""MPC_SakuraDream Extension — adds NPC-specific parameters to the existing Material Parameter Collection.

Run in Unreal Editor Python Console:
    import gmm.npc.mpc_extension as mpc_ext
    mpc_ext.extend_mpc_sakura_dream()
    mpc_ext.create_archetype_mpcs()
"""
from __future__ import annotations

try:
    import unreal
except ImportError:
    unreal = None


MPC_SAKURA_DREAM_PATH = "/Game/EnvSandbox/VFX/MPC/NPC_SakuraDream"
NPC_GLOBAL_MPC_PATH = "/Game/NPCs/Materials/MPC_NPC_Global"
ARCHETYPE_MPC_BASE = "/Game/NPCs/Materials/MPC_NPC_"

# NPC-specific parameters to add to MPC_SakuraDream
NPC_MPC_PARAMS = {
    # Scalar parameters
    "scalar": [
        "NPC_DreamIntensity",
        "NPC_WindStrength", 
        "NPC_GlowIntensity",
        "NPC_BattleMode",       # 0 = exploration, 1 = battle
        "NPC_TimeOfDay",        # 0-24 hour
        "NPC_WeatherFactor",    # 0-1
    ],
    # Vector parameters
    "vector": [
        "NPC_ColorShift",       # R,G,B,A = color shift override
        "NPC_EmissiveColor",    # Emissive tint for battle/photo
        "NPC_RimColor",         # Rim light color
    ]
}

# Archetype-specific default values
ARCHETYPE_DEFAULTS = {
    "SakuraDreamer": {
        "NPC_DreamIntensity": 1.2,
        "NPC_WindStrength": 0.8,
        "NPC_GlowIntensity": 0.2,
        "NPC_ColorShift": (0.839, 0.663, 0.690, 0.3),   # Sakura pink
        "NPC_EmissiveColor": (1.0, 0.9, 0.95, 0.0),
        "NPC_RimColor": (1.0, 0.7, 0.78, 0.8),
    },
    "CosmicWeaver": {
        "NPC_DreamIntensity": 1.5,
        "NPC_WindStrength": 0.5,
        "NPC_GlowIntensity": 0.5,
        "NPC_ColorShift": (0.235, 0.361, 0.620, 0.4),   # Astral blue
        "NPC_EmissiveColor": (0.43, 0.35, 0.65, 0.15),
        "NPC_RimColor": (0.66, 0.60, 0.82, 0.9),
    },
    "MirageDancer": {
        "NPC_DreamIntensity": 1.0,
        "NPC_WindStrength": 1.5,
        "NPC_GlowIntensity": 0.3,
        "NPC_ColorShift": (0.541, 0.663, 0.839, 0.25),   # Aurora blue
        "NPC_EmissiveColor": (0.79, 0.66, 0.42, 0.08),
        "NPC_RimColor": (0.87, 0.78, 0.61, 0.9),
    }
}


def extend_mpc_sakura_dream() -> dict:
    """Add NPC parameters to existing MPC_SakuraDream."""
    if unreal is None:
        return {"error": "Not in Unreal environment"}

    mpc = unreal.EditorAssetLibrary.load_asset(MPC_SAKURA_DREAM_PATH)
    if not mpc:
        return {"error": f"MPC not found: {MPC_SAKURA_DREAM_PATH}"}

    result = {"added_scalar": [], "added_vector": [], "skipped": []}

    # Add scalar parameters
    existing_scalars = {p.parameter_name for p in (mpc.get_editor_property("scalar_parameters") or [])}
    for param_name in NPC_MPC_PARAMS["scalar"]:
        if param_name not in existing_scalars:
            new_param = unreal.ScalarParameterValue()
            new_param.parameter_name = param_name
            new_param.default_value = 1.0 if "Intensity" in param_name or "Strength" in param_name else 0.0
            mpc.scalar_parameters.append(new_param)
            result["added_scalar"].append(param_name)
        else:
            result["skipped"].append(f"scalar:{param_name}")

    # Add vector parameters
    existing_vectors = {p.parameter_name for p in (mpc.get_editor_property("vector_parameters") or [])}
    for param_name in NPC_MPC_PARAMS["vector"]:
        if param_name not in existing_vectors:
            new_param = unreal.VectorParameterValue()
            new_param.parameter_name = param_name
            new_param.default_value = unreal.LinearColor(1.0, 1.0, 1.0, 1.0)
            mpc.vector_parameters.append(new_param)
            result["added_vector"].append(param_name)
        else:
            result["skipped"].append(f"vector:{param_name}")

    unreal.EditorAssetLibrary.save_asset(MPC_SAKURA_DREAM_PATH)
    return result


def create_archetype_mpcs() -> dict:
    """Create per-archetype MPCs that override global NPC params."""
    if unreal is None:
        return {"error": "Not in Unreal environment"}

    results = {}
    
    for archetype, defaults in ARCHETYPE_DEFAULTS.items():
        mpc_path = f"{ARCHETYPE_MPC_BASE}{archetype}"
        
        if unreal.EditorAssetLibrary.does_asset_exist(mpc_path):
            mpc = unreal.EditorAssetLibrary.load_asset(mpc_path)
        else:
            factory = unreal.MaterialParameterCollectionFactoryNew()
            mpc = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
                f"MPC_NPC_{archetype}",
                "/Game/NPCs/Materials",
                unreal.MaterialParameterCollection,
                factory
            )
        
        if not mpc:
            results[archetype] = {"error": "Failed to create/load MPC"}
            continue

        # Set scalar defaults
        scalars = mpc.get_editor_property("scalar_parameters") or []
        for name, value in defaults.items():
            if name in NPC_MPC_PARAMS["scalar"]:
                found = False
                for p in scalars:
                    if p.parameter_name == name:
                        p.default_value = value
                        found = True
                        break
                if not found:
                    new_p = unreal.ScalarParameterValue()
                    new_p.parameter_name = name
                    new_p.default_value = value
                    scalars.append(new_p)
        
        mpc.set_editor_property("scalar_parameters", scalars)

        # Set vector defaults
        vectors = mpc.get_editor_property("vector_parameters") or []
        for name, value in defaults.items():
            if name in NPC_MPC_PARAMS["vector"]:
                found = False
                for p in vectors:
                    if p.parameter_name == name:
                        p.default_value = unreal.LinearColor(*value)
                        found = True
                        break
                if not found:
                    new_p = unreal.VectorParameterValue()
                    new_p.parameter_name = name
                    new_p.default_value = unreal.LinearColor(*value)
                    vectors.append(new_p)
        
        mpc.set_editor_property("vector_parameters", vectors)
        
        unreal.EditorAssetLibrary.save_asset(mpc_path)
        results[archetype] = {"path": mpc_path, "params_set": len(defaults)}

    return results


def create_global_npc_mpc() -> dict:
    """Create global NPC MPC that all archetypes inherit from."""
    if unreal is None:
        return {"error": "Not in Unreal environment"}

    if unreal.EditorAssetLibrary.does_asset_exist(NPC_GLOBAL_MPC_PATH):
        mpc = unreal.EditorAssetLibrary.load_asset(NPC_GLOBAL_MPC_PATH)
    else:
        factory = unreal.MaterialParameterCollectionFactoryNew()
        mpc = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "MPC_NPC_Global",
            "/Game/NPCs/Materials",
            unreal.MaterialParameterCollection,
            factory
        )

    if not mpc:
        return {"error": "Failed to create global MPC"}

    # Add all NPC params with neutral defaults
    scalars = mpc.get_editor_property("scalar_parameters") or []
    for name in NPC_MPC_PARAMS["scalar"]:
        if not any(p.parameter_name == name for p in scalars):
            new_p = unreal.ScalarParameterValue()
            new_p.parameter_name = name
            new_p.default_value = 1.0 if "Intensity" in name or "Strength" in name else 0.0
            scalars.append(new_p)
    mpc.set_editor_property("scalar_parameters", scalars)

    vectors = mpc.get_editor_property("vector_parameters") or []
    for name in NPC_MPC_PARAMS["vector"]:
        if not any(p.parameter_name == name for p in vectors):
            new_p = unreal.VectorParameterValue()
            new_p.parameter_name = name
            new_p.default_value = unreal.LinearColor(1.0, 1.0, 1.0, 1.0)
            vectors.append(new_p)
    mpc.set_editor_property("vector_parameters", vectors)

    unreal.EditorAssetLibrary.save_asset(NPC_GLOBAL_MPC_PATH)
    return {"path": NPC_GLOBAL_MPC_PATH, "scalars": len(NPC_MPC_PARAMS["scalar"]), "vectors": len(NPC_MPC_PARAMS["vector"])}


def bind_npc_material_to_mpc(npc_bp_path: str, archetype: str) -> bool:
    """Bind an NPC Blueprint's materials to use the archetype MPC."""
    if unreal is None:
        return False

    bp = unreal.EditorAssetLibrary.load_asset(npc_bp_path)
    if not bp:
        return False

    # This would be done in the Blueprint's Construction Script
    # Here we just verify the MPC exists
    mpc_path = f"{ARCHETYPE_MPC_BASE}{archetype}"
    mpc = unreal.EditorAssetLibrary.load_asset(mpc_path)
    return mpc is not None


if __name__ == "__main__":
    if unreal:
        print("Extending MPC_SakuraDream...")
        result1 = extend_mpc_sakura_dream()
        print(f"  Added scalars: {result1.get('added_scalar', [])}")
        print(f"  Added vectors: {result1.get('added_vector', [])}")

        print("Creating global NPC MPC...")
        result2 = create_global_npc_mpc()
        print(f"  {result2}")

        print("Creating archetype MPCs...")
        result3 = create_archetype_mpcs()
        for arch, res in result3.items():
            print(f"  {arch}: {res}")

        print("Done!")
    else:
        print("MPC Extension Module - Run in Unreal Editor Python Console")