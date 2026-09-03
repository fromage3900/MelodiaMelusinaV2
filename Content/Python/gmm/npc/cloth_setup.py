"""NPC Cloth Setup — configures cloth simulation per outfit piece for mobile/PC."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from pathlib import Path


@dataclass
class ClothConfig:
    """Cloth configuration for a single outfit piece."""
    piece_name: str
    archetype: str

    # Mobile config (distance constraints only)
    mobile_enabled: bool = True
    mobile_solver: str = "DistanceConstraint"  # or "VRMSpringBone"
    mobile_chains: int = 2
    mobile_iterations: int = 4
    mobile_stiffness: float = 0.8
    mobile_damping: float = 0.5

    # PC config (full Chaos Cloth)
    pc_enabled: bool = True
    pc_solver: str = "Chaos"
    pc_iterations: int = 12
    pc_self_collision: bool = True
    pc_wind_field: bool = False
    pc_stiffness: float = 0.6
    pc_damping: float = 0.3

    # Common
    gravity_scale: float = 1.0
    collision_radius: float = 2.0
    tether_strength: float = 0.5


# ──────────────────────────────────────────────────────────────────────
# PRESET CONFIGS PER OUTFIT PIECE
# ──────────────────────────────────────────────────────────────────────

CLOTH_PRESETS = {
    # Sakura Dreamer
    "kimono_sleeve_top": ClothConfig(
        piece_name="kimono_sleeve_top",
        archetype="SakuraDreamer",
        mobile_enabled=False,  # Baked animation on mobile
        mobile_solver="BakedAnim",
        pc_enabled=True,
        pc_solver="Chaos",
        pc_iterations=8,
        pc_self_collision=False,
    ),
    "hakama_skirt": ClothConfig(
        piece_name="hakama_skirt",
        archetype="SakuraDreamer",
        mobile_enabled=True,
        mobile_solver="DistanceConstraint",
        mobile_chains=2,
        mobile_iterations=4,
        mobile_stiffness=0.85,
        pc_enabled=True,
        pc_solver="Chaos",
        pc_iterations=12,
        pc_self_collision=True,
        pc_stiffness=0.7,
    ),
    "petal_hair_ribbon": ClothConfig(
        piece_name="petal_hair_ribbon",
        archetype="SakuraDreamer",
        mobile_enabled=True,
        mobile_solver="VRMSpringBone",
        mobile_stiffness=0.8,
        pc_enabled=True,
        pc_solver="VRMSpringBone",
        pc_stiffness=0.6,
    ),
    "falling_petal_accessory": ClothConfig(
        piece_name="falling_petal_accessory",
        archetype="SakuraDreamer",
        mobile_enabled=False,
        pc_enabled=True,
        pc_solver="NiagaraParticles",
    ),

    # Cosmic Weaver
    "stellar_cape": ClothConfig(
        piece_name="stellar_cape",
        archetype="CosmicWeaver",
        mobile_enabled=True,
        mobile_solver="DistanceConstraint",
        mobile_chains=3,
        mobile_iterations=4,
        mobile_stiffness=0.75,
        pc_enabled=True,
        pc_solver="Chaos",
        pc_iterations=16,
        pc_wind_field=True,
        pc_self_collision=True,
        pc_stiffness=0.5,
    ),
    "constellation_corset": ClothConfig(
        piece_name="constellation_corset",
        archetype="CosmicWeaver",
        mobile_enabled=False,
        pc_enabled=False,
    ),
    "orbital_hair_ornaments": ClothConfig(
        piece_name="orbital_hair_ornaments",
        archetype="CosmicWeaver",
        mobile_enabled=True,
        mobile_solver="VRMSpringBone",
        mobile_stiffness=0.9,
        pc_enabled=True,
        pc_solver="VRMSpringBone",
        pc_stiffness=0.7,
    ),
    "cosmic_gloves": ClothConfig(
        piece_name="cosmic_gloves",
        archetype="CosmicWeaver",
        mobile_enabled=False,
        pc_enabled=False,
    ),

    # Mirage Dancer
    "asymmetric_gradient_dress": ClothConfig(
        piece_name="asymmetric_gradient_dress",
        archetype="MirageDancer",
        mobile_enabled=True,
        mobile_solver="DistanceConstraint",
        mobile_chains=2,
        mobile_iterations=4,
        mobile_stiffness=0.8,
        pc_enabled=True,
        pc_solver="Chaos",
        pc_iterations=12,
        pc_self_collision=True,
        pc_stiffness=0.65,
    ),
    "wind_torn_scarf": ClothConfig(
        piece_name="wind_torn_scarf",
        archetype="MirageDancer",
        mobile_enabled=True,
        mobile_solver="VRMSpringBone",
        mobile_stiffness=0.5,
        pc_enabled=True,
        pc_solver="Chaos",
        pc_iterations=10,
        pc_wind_field=True,
        pc_stiffness=0.4,
    ),
    "ankle_bells": ClothConfig(
        piece_name="ankle_bells",
        archetype="MirageDancer",
        mobile_enabled=False,
        pc_enabled=False,
    ),
    "trailing_ribbons": ClothConfig(
        piece_name="trailing_ribbons",
        archetype="MirageDancer",
        mobile_enabled=True,
        mobile_solver="VRMSpringBone",
        mobile_stiffness=0.4,
        mobile_chains=4,
        pc_enabled=True,
        pc_solver="Chaos",
        pc_iterations=14,
        pc_wind_field=True,
        pc_stiffness=0.3,
    ),
}


def get_cloth_config(piece_name: str) -> ClothConfig | None:
    """Get cloth config for an outfit piece."""
    return CLOTH_PRESETS.get(piece_name)


def validate_cloth_config(config: ClothConfig) -> list[str]:
    """Return configuration errors without requiring Unreal or VRM4U."""
    errors: list[str] = []
    if not config.piece_name.strip():
        errors.append("piece_name must not be empty")
    if not config.archetype.strip():
        errors.append("archetype must not be empty")
    mobile_solvers = {"DistanceConstraint", "VRMSpringBone", "BakedAnim", "NiagaraParticles"}
    pc_solvers = {"Chaos", "VRMSpringBone", "NiagaraParticles"}
    if config.mobile_enabled and config.mobile_solver not in mobile_solvers:
        errors.append(f"unsupported mobile_solver: {config.mobile_solver}")
    if config.pc_enabled and config.pc_solver not in pc_solvers:
        errors.append(f"unsupported pc_solver: {config.pc_solver}")
    if config.mobile_chains < 0:
        errors.append("mobile_chains must not be negative")
    if config.mobile_iterations < 1:
        errors.append("mobile_iterations must be at least 1")
    if config.pc_iterations < 1:
        errors.append("pc_iterations must be at least 1")
    for name, value in (
        ("mobile_stiffness", config.mobile_stiffness),
        ("mobile_damping", config.mobile_damping),
        ("pc_stiffness", config.pc_stiffness),
        ("pc_damping", config.pc_damping),
        ("tether_strength", config.tether_strength),
    ):
        if not 0.0 <= value <= 1.0:
            errors.append(f"{name} must be between 0 and 1")
    if config.gravity_scale < 0.0:
        errors.append("gravity_scale must not be negative")
    if config.collision_radius < 0.0:
        errors.append("collision_radius must not be negative")
    return errors


def validate_all_cloth_presets() -> dict[str, list[str]]:
    """Validate every checked-in preset, keyed by outfit piece."""
    return {
        name: errors
        for name, config in CLOTH_PRESETS.items()
        if (errors := validate_cloth_config(config))
    }


def apply_cloth_to_skeletal_mesh(mesh_path: str, config: ClothConfig) -> bool:
    """Apply cloth configuration to a skeletal mesh asset in Unreal."""
    try:
        import unreal
    except ImportError:
        return False

    sk = unreal.EditorAssetLibrary.load_asset(mesh_path)
    if not sk:
        return False

    # Get or create PhysicsAsset
    physics_asset = sk.get_editor_property("physics_asset")
    if not physics_asset:
        # Create new PhysicsAsset
        physics_asset = unreal.PhysicsAssetFactoryNew().create_asset(
            f"{mesh_path}_PhysicsAsset",
            "/Game/NPCs/PhysicsAssets",
        )
        sk.set_editor_property("physics_asset", physics_asset)

    # Configure cloth bodies based on solver type
    if config.mobile_solver == "DistanceConstraint":
        _setup_distance_constraint_cloth(physics_asset, config)
    elif config.mobile_solver == "VRMSpringBone":
        _setup_vrm_spring_bone(physics_asset, config)
    elif config.mobile_solver == "BakedAnim":
        _disable_cloth(physics_asset)
    elif config.mobile_solver == "NiagaraParticles":
        _setup_particle_cloth(physics_asset, config)

    # PC Chaos Cloth setup
    if config.pc_enabled and config.pc_solver == "Chaos":
        _setup_chaos_cloth(physics_asset, config)

    unreal.EditorAssetLibrary.save_asset(physics_asset.get_path_name())
    return True


def _setup_distance_constraint_cloth(physics_asset, config: ClothConfig):
    """Setup simple distance constraint cloth for mobile."""
    # This would create constraint chains along skirt/bone hierarchy
    pass


def _setup_vrm_spring_bone(physics_asset, config: ClothConfig):
    """Setup VRM Spring Bone (uses VRM4U's spring bone system)."""
    # VRM4U handles this automatically on import
    pass


def _disable_cloth(physics_asset):
    """Disable cloth simulation."""
    pass


def _setup_particle_cloth(physics_asset, config: ClothConfig):
    """Setup Niagara particle-based cloth."""
    pass


def _setup_chaos_cloth(physics_asset, config: ClothConfig):
    """Setup full Chaos Cloth for PC."""
    pass


def generate_cloth_configs_json(output_path: Path = None) -> str:
    """Generate JSON of all cloth configs for pipeline."""
    import json
    if output_path is None:
        output_path = Path(__file__).parent / "cloth_configs.json"

    data = {}
    for name, config in CLOTH_PRESETS.items():
        data[name] = {
            "piece_name": config.piece_name,
            "archetype": config.archetype,
            "mobile": {
                "enabled": config.mobile_enabled,
                "solver": config.mobile_solver,
                "chains": config.mobile_chains,
                "iterations": config.mobile_iterations,
                "stiffness": config.mobile_stiffness,
                "damping": config.mobile_damping,
            },
            "pc": {
                "enabled": config.pc_enabled,
                "solver": config.pc_solver,
                "iterations": config.pc_iterations,
                "self_collision": config.pc_self_collision,
                "wind_field": config.pc_wind_field,
                "stiffness": config.pc_stiffness,
                "damping": config.pc_damping,
            },
            "common": {
                "gravity_scale": config.gravity_scale,
                "collision_radius": config.collision_radius,
                "tether_strength": config.tether_strength,
            },
        }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return str(output_path)


if __name__ == "__main__":
    path = generate_cloth_configs_json()
    print(f"Generated cloth configs: {path}")