"""NPC LOD Generator — creates 3 LODs with bone culling for mobile optimization."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json


@dataclass
class LODConfig:
    """LOD configuration for an NPC."""
    lod_index: int
    screen_size: float
    target_triangles: int
    max_bones: int
    bone_culling: list[str] = None  # Bones to remove at this LOD
    cloth_enabled: bool = True
    morph_targets: bool = True

    def __post_init__(self):
        if self.bone_culling is None:
            self.bone_culling = []


# ──────────────────────────────────────────────────────────────────────
# LOD PRESETS PER ARCHETYPE
# ──────────────────────────────────────────────────────────────────────

# Common bone names to cull at each LOD (standard humanoid + VRM extras)
FINGER_BONES = [
    "thumb_01_l", "thumb_02_l", "thumb_03_l", "index_01_l", "index_02_l", "index_03_l",
    "middle_01_l", "middle_02_l", "middle_03_l", "ring_01_l", "ring_02_l", "ring_03_l",
    "pinky_01_l", "pinky_02_l", "pinky_03_l",
    "thumb_01_r", "thumb_02_r", "thumb_03_r", "index_01_r", "index_02_r", "index_03_r",
    "middle_01_r", "middle_02_r", "middle_03_r", "ring_01_r", "ring_02_r", "ring_03_r",
    "pinky_01_r", "pinky_02_r", "pinky_03_r",
]

TOE_BONES = ["toes_l", "toes_r"]

FACIAL_BONES = [
    "eye_l", "eye_r", "eyelid_up_l", "eyelid_low_l", "eyelid_up_r", "eyelid_low_r",
    "brow_l", "brow_r", "mouth", "jaw", "cheek_l", "cheek_r",
    "iris_l", "iris_r",
]

VRM_EXTRA_BONES = [
    "hair_", "skirt_", "cape_", "ribbon_", "scarf_", "tail_", "ear_", "accessory_",
]


LOD_PRESETS = {
    "LOD0": LODConfig(
        lod_index=0,
        screen_size=1.0,
        target_triangles=18000,
        max_bones=60,
        bone_culling=[],
        cloth_enabled=True,
        morph_targets=True,
    ),
    "LOD1": LODConfig(
        lod_index=1,
        screen_size=0.5,
        target_triangles=8000,
        max_bones=40,
        bone_culling=FINGER_BONES + TOE_BONES,
        cloth_enabled=True,
        morph_targets=True,
    ),
    "LOD2": LODConfig(
        lod_index=2,
        screen_size=0.25,
        target_triangles=3000,
        max_bones=28,
        bone_culling=FINGER_BONES + TOE_BONES + FACIAL_BONES + VRM_EXTRA_BONES,
        cloth_enabled=False,
        morph_targets=False,
    ),
}


def get_lod_config(archetype: str = None) -> dict[str, LODConfig]:
    """Get LOD configs (same for all archetypes, can customize per-archetype)."""
    return LOD_PRESETS


def generate_lod_setup_python(mesh_path: str, archetype: str = None) -> str:
    """Generate Python script to run in Unreal Editor for LOD setup."""
    lod_configs = get_lod_config(archetype)

    script = f'''
# Auto-generated LOD setup for {mesh_path}
# Run in Unreal Editor Python Console

import unreal

mesh_path = "{mesh_path}"
sk = unreal.EditorAssetLibrary.load_asset(mesh_path)
if not sk:
    print("Mesh not found!")
else:
    # Enable LODs
    sk.set_editor_property("number_of_lods", 3)

    # LOD settings
    lod_settings = [
'''

    for lod_name, config in lod_configs.items():
        script += f'''        {{
            "lod_index": {config.lod_index},
            "screen_size": {config.screen_size},
            "reduction_settings": {{
                "base_lod_model": {config.lod_index - 1 if config.lod_index > 0 else 0},
                "reduction_type": "Triangles",
                "target_triangles": {config.target_triangles},
                "max_deviation": 0.0,
                "silhouette_importance": 0.5,
                "texture_importance": 0.5,
                "shading_importance": 0.5,
                "skin_importance": 1.0,
            }},
            "bone_culling": {config.bone_culling},
            "cloth_enabled": {str(config.cloth_enabled).lower()},
            "morph_targets": {str(config.morph_targets).lower()},
        }},
'''

    script += '''    ]

    # Apply LOD reduction (requires SkeletalMeshEditor subsystem)
    for lod in lod_settings:
        print(f"Configuring {lod['lod_index']}: {lod['target_triangles']} tris, {lod['max_bones']} bones")
        # Note: Full LOD generation requires SkeletalMeshEditor or commandlet
        # This is a template - run via commandlet for production

    print("LOD setup template generated. Run via commandlet for actual reduction.")
'''

    return script


def export_lod_configs(output_path: Path = None) -> str:
    """Export LOD configs as JSON."""
    import json
    if output_path is None:
        output_path = Path(__file__).parent / "lod_configs.json"

    data = {}
    for name, config in LOD_PRESETS.items():
        data[name] = {
            "lod_index": config.lod_index,
            "screen_size": config.screen_size,
            "target_triangles": config.target_triangles,
            "max_bones": config.max_bones,
            "bone_culling": config.bone_culling,
            "cloth_enabled": config.cloth_enabled,
            "morph_targets": config.morph_targets,
        }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return str(output_path)


def calculate_bone_reduction_plan(mesh_path: str) -> dict:
    """Analyze skeletal mesh and calculate bone reduction plan for each LOD."""
    try:
        import unreal
    except ImportError:
        return {"error": "Not in Unreal environment"}

    sk = unreal.EditorAssetLibrary.load_asset(mesh_path)
    if not sk:
        return {"error": f"Mesh not found: {mesh_path}"}

    skeleton = sk.get_editor_property("skeleton")
    if not skeleton:
        return {"error": "No skeleton found"}

    all_bones = skeleton.get_bone_names()
    total_bones = len(all_bones)

    # Categorize bones
    categories = {
        "core": [],      # pelvis, spine, neck, head, clavicle, upperarm, thigh
        "fingers": [],   # all finger bones
        "toes": [],      # toe bones
        "facial": [],    # eye, brow, mouth, jaw
        "vrm_extra": [], # hair, skirt, cape, ribbon, tail, ear, accessory
    }

    for bone in all_bones:
        bone_lower = bone.lower()
        if any(f in bone_lower for f in ["finger", "thumb", "index", "middle", "ring", "pinky"]):
            categories["fingers"].append(bone)
        elif "toe" in bone_lower:
            categories["toes"].append(bone)
        elif any(f in bone_lower for f in ["eye", "eyelid", "brow", "mouth", "jaw", "cheek", "iris"]):
            categories["facial"].append(bone)
        elif any(f in bone_lower for f in ["hair", "skirt", "cape", "ribbon", "scarf", "tail", "ear", "accessory"]):
            categories["vrm_extra"].append(bone)
        else:
            categories["core"].append(bone)

    plan = {
        "mesh": mesh_path,
        "total_bones": total_bones,
        "categories": {k: len(v) for k, v in categories.items()},
        "lod_plan": {
            "LOD0": {
                "target_bones": 60,
                "keep": ["core"],
                "remove": [],
            },
            "LOD1": {
                "target_bones": 40,
                "keep": ["core"],
                "remove": ["fingers", "toes"],
            },
            "LOD2": {
                "target_bones": 28,
                "keep": ["core"],
                "remove": ["fingers", "toes", "facial", "vrm_extra"],
            },
        },
    }

    return plan


if __name__ == "__main__":
    path = export_lod_configs()
    print(f"Exported LOD configs: {path}")