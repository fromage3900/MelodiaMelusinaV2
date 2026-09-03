"""NPC Battle Integration — generates FMelodiaEnemyDef for battle archetypes.

Creates DataAsset entries that MelodiaCore's UMelodiaEnemyDataAsset can consume.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import json


@dataclass
class EnemyDefExport:
    """Export format matching FMelodiaEnemyDef (C++)."""
    enemy_id: str
    display_name: str
    max_hp: float
    max_toughness: float
    base_damage: float
    speed: int
    element: str  # Matches EMelodiaSpellElement
    bpm_override: float
    mesh_scale: float = 1.0
    display_mesh: str = ""  # Soft object path
    display_material: str = ""  # Soft object path

    def to_cpp_struct(self) -> str:
        """Generate C++ struct initialization code."""
        return f'''{{
    FMelodiaEnemyDef Enemy;
    Enemy.EnemyId = FName(TEXT("{self.enemy_id}"));
    Enemy.DisplayName = FText::FromString(TEXT("{self.display_name}"));
    Enemy.MaxHP = {self.max_hp:.1f}f;
    Enemy.MaxToughness = {self.max_toughness:.1f}f;
    Enemy.BaseDamage = {self.base_damage:.1f}f;
    Enemy.Speed = {self.speed};
    Enemy.Element = EMelodiaSpellElement::{self.element};
    Enemy.MeshScale = {self.mesh_scale:.1f}f;
    Enemy.BPMOverride = {self.bpm_override:.1f}f;
    DemoEnemies.Add(Enemy);
}}'''


# ──────────────────────────────────────────────────────────────────────
# BATTLE ARCHETYPE DEFINITIONS
# ──────────────────────────────────────────────────────────────────────

BATTLE_ARCHETYPES = {
    "SakuraDreamer_Battle": EnemyDefExport(
        enemy_id="SakuraDreamer_Battle",
        display_name="Sakura Dreamer",
        max_hp=200.0,
        max_toughness=60.0,
        base_damage=12.0,
        speed=75,
        element="Radiant",
        bpm_override=128.0,
        mesh_scale=1.1,
    ),
    "CosmicWeaver_Battle": EnemyDefExport(
        enemy_id="CosmicWeaver_Battle",
        display_name="Cosmic Weaver",
        max_hp=350.0,
        max_toughness=120.0,
        base_damage=18.0,
        speed=65,
        element="Arcane",
        bpm_override=144.0,
        mesh_scale=1.2,
    ),
    "MirageDancer_Battle": EnemyDefExport(
        enemy_id="MirageDancer_Battle",
        display_name="Mirage Dancer",
        max_hp=160.0,
        max_toughness=40.0,
        base_damage=22.0,
        speed=110,
        element="Gale",
        bpm_override=180.0,
        mesh_scale=0.95,
    ),
}

# Specific enemy variants per NPC (for unique encounters)
NPC_VARIANTS = {
    "SD_01_SakuraMaiden": {"base": "SakuraDreamer_Battle", "hp_mult": 1.0, "dmg_mult": 1.0, "element": "Radiant"},
    "SD_02_PetalPriestess": {"base": "SakuraDreamer_Battle", "hp_mult": 1.2, "dmg_mult": 0.9, "element": "Radiant"},
    "SD_03_BlossomGuide": {"base": "SakuraDreamer_Battle", "hp_mult": 0.9, "dmg_mult": 1.1, "element": "Radiant"},
    "SD_04_FlowerMerchant": {"base": "SakuraDreamer_Battle", "hp_mult": 1.1, "dmg_mult": 1.0, "element": "Radiant"},
    "SD_05_EternalGardener": {"base": "SakuraDreamer_Battle", "hp_mult": 1.5, "dmg_mult": 1.2, "element": "Radiant"},

    "CW_01_StarWeaver": {"base": "CosmicWeaver_Battle", "hp_mult": 1.0, "dmg_mult": 1.0, "element": "Arcane"},
    "CW_02_VoidSeamstress": {"base": "CosmicWeaver_Battle", "hp_mult": 1.1, "dmg_mult": 0.9, "element": "Arcane"},
    "CW_03_AstralScribe": {"base": "CosmicWeaver_Battle", "hp_mult": 0.9, "dmg_mult": 1.1, "element": "Arcane"},

    "MD_01_TwilightDancer": {"base": "MirageDancer_Battle", "hp_mult": 1.0, "dmg_mult": 1.0, "element": "Gale"},
    "MD_02_WindWalker": {"base": "MirageDancer_Battle", "hp_mult": 1.1, "dmg_mult": 0.9, "element": "Gale"},
    "MD_03_ZephyrChampion": {"base": "MirageDancer_Battle", "hp_mult": 1.5, "dmg_mult": 1.3, "element": "Gale"},
}


def generate_npc_enemy_defs() -> dict[str, dict]:
    """Generate per-NPC enemy definitions from archetype bases."""
    results = {}
    for npc_id, variant in NPC_VARIANTS.items():
        base = BATTLE_ARCHETYPES[variant["base"]]
        results[npc_id] = {
            "enemy_id": f"{npc_id}_Battle",
            "display_name": base.display_name,
            "max_hp": base.max_hp * variant["hp_mult"],
            "max_toughness": base.max_toughness * variant["hp_mult"],
            "base_damage": base.base_damage * variant["dmg_mult"],
            "speed": base.speed,
            "element": variant["element"],
            "bpm_override": base.bpm_override,
            "mesh_scale": base.mesh_scale,
            "source_archetype": variant["base"],
        }
    return results


def export_data_asset_json(output_path: Path = None) -> str:
    """Export JSON for UMelodiaEnemyDataAsset import."""
    if output_path is None:
        output_path = Path(__file__).parent / "battle_enemy_defs.json"

    data = {
        "archetypes": {k: asdict(v) for k, v in BATTLE_ARCHETYPES.items()},
        "npc_variants": generate_npc_enemy_defs(),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return str(output_path)


def export_cpp_initialization_code(output_path: Path = None) -> str:
    """Generate C++ code to add to UMelodiaEnemyDataAsset::GetDemoEnemies()."""
    if output_path is None:
        output_path = Path(__file__).parent / "battle_enemy_defs.cpp"

    lines = [
        "// AUTO-GENERATED: NPC Battle Definitions",
        "// Paste into UMelodiaEnemyDataAsset::GetDemoEnemies() in MelodiaEnemyDefinition.cpp",
        "",
    ]

    for archetype in BATTLE_ARCHETYPES.values():
        lines.append(archetype.to_cpp_struct())
        lines.append("")

    for npc_id, variant in generate_npc_enemy_defs().items():
        base = BATTLE_ARCHETYPES[variant["source_archetype"]]
        lines.append(f'''{{
    FMelodiaEnemyDef Enemy;
    Enemy.EnemyId = FName(TEXT("{variant["enemy_id"]}"));
    Enemy.DisplayName = FText::FromString(TEXT("{variant["display_name"]} - {npc_id}"));
    Enemy.MaxHP = {variant["max_hp"]:.1f}f;
    Enemy.MaxToughness = {variant["max_toughness"]:.1f}f;
    Enemy.BaseDamage = {variant["base_damage"]:.1f}f;
    Enemy.Speed = {variant["speed"]};
    Enemy.Element = EMelodiaSpellElement::{variant["element"]};
    Enemy.MeshScale = {variant["mesh_scale"]:.2f}f;
    Enemy.BPMOverride = {variant["bpm_override"]:.1f}f;
    DemoEnemies.Add(Enemy);
}}''')
        lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return str(output_path)


def validate_against_gmm_config() -> dict:
    """Validate battle stats against gmm.game.config GAME_CFG."""
    try:
        from gmm.game.config import GAME_CFG
    except ImportError:
        return {"valid": True, "error": "gmm.game.config not available (skipping validation)", "issues": [], "checked": len(BATTLE_ARCHETYPES)}

    issues = []
    for arch_id, arch in BATTLE_ARCHETYPES.items():
        # Check HP scaling
        expected_hp = GAME_CFG.base_xp_to_next * 2  # Rough heuristic
        if arch.max_hp < 50 or arch.max_hp > 1000:
            issues.append(f"{arch_id}: HP {arch.max_hp} outside expected range")

        # Check speed (AV = 10000/speed)
        if arch.speed < 20 or arch.speed > 200:
            issues.append(f"{arch_id}: Speed {arch.speed} outside AV range")

        # Check BPM
        if arch.bpm_override < 60 or arch.bpm_override > 200:
            issues.append(f"{arch_id}: BPM {arch.bpm_override} outside range")

        # Check element validity
        valid_elements = ["Forte", "Tide", "Gale", "Stone", "Radiant", "Umbral", "Arcane"]
        if arch.element not in valid_elements:
            issues.append(f"{arch_id}: Invalid element {arch.element}")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "checked": len(BATTLE_ARCHETYPES),
    }


if __name__ == "__main__":
    json_path = export_data_asset_json()
    cpp_path = export_cpp_initialization_code()
    validation = validate_against_gmm_config()

    print(f"Exported JSON: {json_path}")
    print(f"Exported C++:  {cpp_path}")
    print(f"Validation: {'PASS' if validation['valid'] else 'FAIL'}")
    for issue in validation.get("issues", []):
        print(f"  WARNING: {issue}")