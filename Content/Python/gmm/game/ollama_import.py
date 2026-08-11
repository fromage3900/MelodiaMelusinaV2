"""Ollama Slice Integration — imports procedurally-generated content into game data.

Loads drafts from Imports/Data/ and converts them to the game's dataclass formats.
References existing blessing/artifact IDs for room modifiers.

Usage (headless):
    python -c "import sys; sys.path.insert(0, 'Content/Python'); from gmm.game.ollama_import import main; main()"

Usage (Unreal Editor):
    import sys; sys.path.insert(0, '/Game/Content/Python')
    from gmm.game.ollama_import import main; main()
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from gmm.melodia.enemies import MelodiaEnemyDef, ELEMENTS as ENEMY_ELEMENTS
from gmm.melodia.skills import MelodiaSongSkillRecipe, ELEMENTS as SKILL_ELEMENTS, INSTRUMENTS
from gmm.core.audit import GmmAudit


# Paths
IMPORTS_DIR = Path(__file__).resolve().parents[4] / "Imports" / "Data"
ENEMY_VARIANTS_DIR = IMPORTS_DIR / "EnemyVariants"
CHARTS_DIR = IMPORTS_DIR / "Charts"
ROOM_MODS_DIR = IMPORTS_DIR / "RoomMods"


def load_enemy_variants() -> list[dict]:
    """Load all enemy variant JSON files."""
    variants = []
    if not ENEMY_VARIANTS_DIR.exists():
        return variants
    
    for path in ENEMY_VARIANTS_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("schema") == "FMelodiaEnemyDef-draft-v1":
            variants.append(data)
    
    return variants


def load_charts() -> list[dict]:
    """Load all chart JSON files."""
    charts = []
    if not CHARTS_DIR.exists():
        return charts
    
    for path in CHARTS_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("schema") == "FMelodiaChartNote-draft-v1":
            charts.append(data)
    
    return charts


def load_room_mods() -> list[dict]:
    """Load all room modifier JSON files."""
    mods = []
    if not ROOM_MODS_DIR.exists():
        return mods
    
    for path in ROOM_MODS_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("schema") == "RoomModifier-draft-v1":
            mods.append(data)
    
    return mods


def enemy_variant_to_def(data: dict) -> Optional[MelodiaEnemyDef]:
    """Convert Ollama enemy variant to MelodiaEnemyDef dataclass."""
    # Validate element against the enum
    element = data.get("element", "Forte")
    if element not in ENEMY_ELEMENTS:
        element = "Forte"  # Safe fallback
    
    stats = data.get("stats", {})
    
    return MelodiaEnemyDef(
        enemy_id=data.get("id", "Unknown"),
        display_name=data.get("display_name", "Unknown Slime"),
        max_hp=stats.get("max_hp", 300.0),
        max_toughness=stats.get("toughness", 60.0),
        base_damage=stats.get("base_damage", 15.0),
        speed=stats.get("speed", 80),
        element=element,
        bpm=stats.get("bpm", 120.0),
        display_mesh=data.get("mesh_note", ""),  # Note stored in display_mesh field for now
    )


def chart_to_skill(data: dict) -> Optional[MelodiaSongSkillRecipe]:
    """Convert Ollama chart to MelodiaSongSkillRecipe dataclass.
    
    The chart defines note sequences that become rhythm skills.
    """
    element = data.get("element", "Forte")
    if element not in SKILL_ELEMENTS:
        element = "Forte"
    
    notes = data.get("notes", [])
    pitches = tuple(n.get("pitch", 60) for n in notes if "pitch" in n) or (60,)
    durations = tuple(0.25 for _ in pitches)  # Default quarter note durations
    
    # Derive SP cost from difficulty
    difficulty = data.get("difficulty", 1)
    sp_cost = {1: 1, 2: 2, 3: 3}.get(difficulty, 1)
    
    return MelodiaSongSkillRecipe(
        skill_id=data.get("id", "Unknown"),
        display_name=data.get("skill_name", "Untitled"),
        description=f"A {element}-element rhythm skill (difficulty {difficulty})",
        element=element,
        instrument="MusicBox",  # Default instrument
        mechanic_level=difficulty,
        note_pitches=pitches,
        note_durations=durations,
        sp_cost=sp_cost,
        power_scalar=0.8 + difficulty * 0.4,  # Scale power by difficulty
    )


def room_mod_to_blessing(data: dict) -> Optional[dict]:
    """Convert room modifier to blessing format for integration.
    
    References existing blessing IDs where applicable.
    Room mods are blessing/curse pairs that can be applied to room templates.
    """
    blessing_data = data.get("blessing", {})
    curse_data = data.get("curse", {})
    
    # Map blessing effects to existing blessing types
    effect_text = blessing_data.get("effect_text", "")
    
    # Determine effect type from text references
    effect_type = "passive"
    effect_value = 0.0
    
    if "HP" in effect_text and "+" in effect_text:
        effect_type = "starting_mana"  # Reuse for HP bonuses
        # Extract percentage if possible
        import re
        match = re.search(r'(\d+)%', effect_text)
        if match:
            effect_value = float(match.group(1))
    elif "SP" in effect_text:
        effect_type = "max_sp"
        match = re.search(r'(\d+)%', effect_text)
        if match:
            effect_value = float(match.group(1))
    elif "speed" in effect_text.lower() or "AV" in effect_text:
        effect_type = "passive"
        effect_value = 0.2  # 20% speed bonus default
    elif "toughness" in effect_text.lower():
        effect_type = "passive"
    
    return {
        "blessing_id": f"{data.get('id', 'Mod')}_Blessing",
        "display_name": blessing_data.get("name", "Unknown Blessing"),
        "description": blessing_data.get("effect_text", ""),
        "token_cost": 50,  # Default cost, can be tuned
        "effect_type": effect_type,
        "effect_value": effect_value,
        "effect_str": "",
        "curse": curse_data.get("name", ""),
        "curse_effect": curse_data.get("effect_text", ""),
        "flavor": data.get("flavor", ""),
    }


def generate_enemy_data_table(variants: list[dict]) -> dict:
    """Generate enemy data table JSON for MelodiaEnemies DT."""
    rows = {}
    for v in variants:
        enemy_def = enemy_variant_to_def(v)
        if enemy_def:
            rows[v.get("id", "Unknown")] = {
                "enemy_id": enemy_def.enemy_id,
                "display_name": enemy_def.display_name,
                "max_hp": enemy_def.max_hp,
                "max_toughness": enemy_def.max_toughness,
                "base_damage": enemy_def.base_damage,
                "speed": enemy_def.speed,
                "element": enemy_def.element,
                "bpm": enemy_def.bpm,
            }
    
    return {
        "DataType": "EnemyStats",
        "Rows": rows,
    }


def generate_skill_data_table(charts: list[dict]) -> dict:
    """Generate skill data table JSON for MelodiaSkills DT."""
    rows = {}
    for c in charts:
        skill = chart_to_skill(c)
        if skill:
            rows[c.get("id", "Unknown")] = {
                "skill_id": skill.skill_id,
                "display_name": skill.display_name,
                "element": skill.element,
                "instrument": skill.instrument,
                "mechanic_level": skill.mechanic_level,
                "sp_cost": skill.sp_cost,
                "power_scalar": skill.power_scalar,
                "note_pitches": list(skill.note_pitches),
                "note_durations": list(skill.note_durations),
            }
    
    return {
        "DataType": "SkillData",
        "Rows": rows,
    }


def generate_room_mod_data_table(mods: list[dict]) -> dict:
    """Generate room modifier data table for roguelike system."""
    rows = {}
    for m in mods:
        blessing_data = room_mod_to_blessing(m)
        if blessing_data:
            rows[m.get("id", "Unknown")] = blessing_data
    
    return {
        "DataType": "RoguelikeRoomModifier",
        "Rows": rows,
    }


def save_data_tables() -> dict:
    """Generate and save all data tables."""
    audit = GmmAudit(action="ollama_import.generate_tables")
    
    results = {}
    
    # Generate enemy table
    variants = load_enemy_variants()
    enemy_table = generate_enemy_data_table(variants)
    results["enemy_variants"] = len(variants)
    
    # Generate skill table
    charts = load_charts()
    skill_table = generate_skill_data_table(charts)
    results["charts"] = len(charts)
    
    # Generate room mod table
    mods = load_room_mods()
    mod_table = generate_room_mod_data_table(mods)
    results["room_mods"] = len(mods)
    
    # Save to Content/Melodia/DataStuctures - use relative path from working directory
    base_path = Path("Content") / "Melodia" / "DataStuctures"
    base_path.mkdir(parents=True, exist_ok=True)
    
    (base_path / "DT_MelodySlime_Enemies.json").write_text(
        json.dumps(enemy_table, indent=2), encoding="utf-8"
    )
    (base_path / "DT_MelodySlime_Skills.json").write_text(
        json.dumps(skill_table, indent=2), encoding="utf-8"
    )
    (base_path / "DT_MelodySlime_RoomMods.json").write_text(
        json.dumps(mod_table, indent=2), encoding="utf-8"
    )
    
    audit.ok(results=results, tables_saved=3)
    audit.save("gmm_ollama_import.json")
    
    return audit.to_dict()


def extend_roguelike_blessings(mods: list[dict]) -> dict:
    """Add generated room modifiers as blessings to the roguelike system.
    
    Returns the blessing extensions that can be merged into roguelike.py BLESSINGS.
    """
    extensions = {}
    for m in mods:
        blessing_data = room_mod_to_blessing(m)
        if blessing_data:
            # Create blessing entries that reference the generated modifiers
            extensions[f"RoomMod_{m.get('id', 'Unknown')}"] = {
                "blessing_id": f"RoomMod_{m.get('id', 'Unknown')}",
                "display_name": blessing_data.get("display_name", "Unknown Blessing"),
                "description": blessing_data.get("description", ""),
                "token_cost": blessing_data.get("token_cost", 50),
                "effect_type": blessing_data.get("effect_type", "passive"),
                "effect_value": blessing_data.get("effect_value", 0.0),
                "effect_str": blessing_data.get("effect_str", ""),
            }
    return extensions


def extend_enemy_pool(variants: list[dict]) -> dict:
    """Add generated enemy variants to the enemy pool.
    
    Returns enemy IDs by element for use in room templates.
    """
    enemies_by_element = {e: [] for e in ENEMY_ELEMENTS}
    for v in variants:
        enemy_def = enemy_variant_to_def(v)
        if enemy_def and enemy_def.element in ENEMY_ELEMENTS:
            enemies_by_element[enemy_def.element].append(enemy_def.enemy_id)
    return enemies_by_element


def integrate_all() -> dict:
    """Full integration: generate tables and extend game systems."""
    audit = GmmAudit(action="ollama_import.integrate_all")
    
    variants = load_enemy_variants()
    charts = load_charts()
    mods = load_room_mods()
    
    # Generate data tables
    tables_result = save_data_tables()
    
    # Extend enemy pool
    enemy_pool = extend_enemy_pool(variants)
    
    # Extend blessings
    blessing_ext = extend_roguelike_blessings(mods)
    
    audit.ok(
        enemy_variants=len(variants),
        charts=len(charts),
        room_mods=len(mods),
        enemies_by_element=enemy_pool,
        blessing_extensions=list(blessing_ext.keys()),
    )
    audit.save("gmm_ollama_integration_full.json")
    
    return audit.to_dict()


def main() -> dict:
    """Main entry point for Ollama slice integration."""
    return integrate_all()


if __name__ == "__main__":
    import datetime
    report = main()
    print(json.dumps(report, indent=2, default=str))
    print(f"\nTimestamp: {datetime.datetime.now()}")
