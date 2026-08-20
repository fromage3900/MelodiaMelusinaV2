#!/usr/bin/env python3
"""
Active Content Generation & Live MCP Ingestion Tool for Melodia / Melusina.

Generates:
1. JRPG Rhythm Combat Skills adhering to Melodia schema (beat timings, damage multipliers, resonance types, SP costs).
2. Generic Narrative Quests adhering to Persona/Narrative schema (quest IDs, objectives, rewards, idempotency flags).
3. Ingests skills into Content/Melodia/DataStuctures/DT_MelodySlime_Skills.json.
4. Ingests quests into specs/progression/melodia_integration_allowlist_seed.v1.json.
5. Ingests blueprint fixture specs into specs/blueprints/fixtures/.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
PYTHON_PATH = PROJECT_ROOT / "Content" / "Python"
if str(PYTHON_PATH) not in sys.path:
    sys.path.insert(0, str(PYTHON_PATH))

CHARTS_DIR = PROJECT_ROOT / "Imports" / "Data" / "Charts"
DIALOGUE_DIR = PROJECT_ROOT / "Imports" / "Data" / "Dialogue"
NARRATIVE_DIR = PROJECT_ROOT / "Content" / "MelodiaIntegration" / "Narrative"
FIXTURES_DIR = PROJECT_ROOT / "specs" / "blueprints" / "fixtures"
ALLOWLIST_SEED = PROJECT_ROOT / "specs" / "progression" / "melodia_integration_allowlist_seed.v1.json"
DT_SKILLS_PATH = PROJECT_ROOT / "Content" / "Melodia" / "DataStuctures" / "DT_MelodySlime_Skills.json"


# ---------------------------------------------------------------------------
# 1. Rhythm Skill Generator (Melodia Rhythm Combat Schema)
# ---------------------------------------------------------------------------

NEW_SKILLS = [
    {
        "id": "Chart_Forte_CadenceStrike",
        "skill_name": "Cadence Strike",
        "element": "Forte",
        "instrument": "Keyboards",
        "difficulty": 2,
        "sp_cost": 2,
        "power_scalar": 2.8,
        "cooldown_turns": 1,
        "resonance_type": "Forte",
        "notes": [
            {"lane": 0, "beat": 0.0, "pitch": 72},
            {"lane": 1, "beat": 0.5, "pitch": 76},
            {"lane": 2, "beat": 0.75, "pitch": 79},
            {"lane": 3, "beat": 1.0, "pitch": 84},
            {"lane": 0, "beat": 1.5, "pitch": 72},
            {"lane": 2, "beat": 2.0, "pitch": 76},
            {"lane": 1, "beat": 2.25, "pitch": 79},
            {"lane": 3, "beat": 2.5, "pitch": 84},
            {"lane": 0, "beat": 3.0, "pitch": 72},
            {"lane": 1, "beat": 3.5, "pitch": 76},
            {"lane": 2, "beat": 3.75, "pitch": 79},
            {"lane": 3, "beat": 4.0, "pitch": 84},
        ],
        "schema": "FMelodiaChartNote-draft-v1"
    },
    {
        "id": "Chart_Radiant_LullabyMend",
        "skill_name": "Lullaby Mend",
        "element": "Radiant",
        "instrument": "MusicBox",
        "difficulty": 2,
        "sp_cost": 2,
        "power_scalar": 2.0,
        "cooldown_turns": 2,
        "resonance_type": "Radiant",
        "notes": [
            {"lane": 0, "beat": 0.0, "pitch": 64},
            {"lane": 1, "beat": 0.5, "pitch": 67},
            {"lane": 2, "beat": 1.0, "pitch": 72},
            {"lane": 3, "beat": 1.5, "pitch": 76},
            {"lane": 1, "beat": 2.0, "pitch": 72},
            {"lane": 0, "beat": 2.5, "pitch": 67},
            {"lane": 2, "beat": 3.0, "pitch": 76},
            {"lane": 3, "beat": 3.5, "pitch": 79},
            {"lane": 1, "beat": 4.0, "pitch": 72},
            {"lane": 0, "beat": 4.5, "pitch": 84},
        ],
        "schema": "FMelodiaChartNote-draft-v1"
    },
    {
        "id": "Chart_Umbral_DissonantSilence",
        "skill_name": "Dissonant Silence",
        "element": "Umbral",
        "instrument": "Violin",
        "difficulty": 3,
        "sp_cost": 3,
        "power_scalar": 3.5,
        "cooldown_turns": 2,
        "resonance_type": "Umbral",
        "notes": [
            {"lane": 0, "beat": 0.0, "pitch": 60},
            {"lane": 1, "beat": 0.25, "pitch": 63},
            {"lane": 2, "beat": 0.5, "pitch": 67},
            {"lane": 3, "beat": 0.75, "pitch": 70},
            {"lane": 0, "beat": 1.0, "pitch": 73},
            {"lane": 1, "beat": 1.5, "pitch": 67},
            {"lane": 2, "beat": 1.75, "pitch": 70},
            {"lane": 3, "beat": 2.0, "pitch": 75},
            {"lane": 1, "beat": 2.5, "pitch": 70},
            {"lane": 0, "beat": 2.75, "pitch": 67},
            {"lane": 2, "beat": 3.0, "pitch": 78},
            {"lane": 3, "beat": 3.25, "pitch": 82},
            {"lane": 1, "beat": 3.5, "pitch": 75},
            {"lane": 0, "beat": 4.0, "pitch": 84},
        ],
        "schema": "FMelodiaChartNote-draft-v1"
    },
    {
        "id": "Chart_Arcane_CosmicResonance",
        "skill_name": "Cosmic Resonance",
        "element": "Arcane",
        "instrument": "MusicBox",
        "difficulty": 3,
        "sp_cost": 3,
        "power_scalar": 3.5,
        "cooldown_turns": 1,
        "resonance_type": "Arcane",
        "notes": [
            {"lane": 0, "beat": 0.0, "pitch": 60},
            {"lane": 1, "beat": 0.25, "pitch": 64},
            {"lane": 2, "beat": 0.5, "pitch": 67},
            {"lane": 3, "beat": 0.75, "pitch": 72},
            {"lane": 0, "beat": 1.0, "pitch": 76},
            {"lane": 2, "beat": 1.25, "pitch": 84},
            {"lane": 1, "beat": 1.5, "pitch": 76},
            {"lane": 3, "beat": 1.75, "pitch": 79},
            {"lane": 0, "beat": 2.0, "pitch": 84},
            {"lane": 1, "beat": 2.25, "pitch": 72},
            {"lane": 2, "beat": 2.5, "pitch": 76},
            {"lane": 3, "beat": 2.75, "pitch": 84},
            {"lane": 0, "beat": 3.0, "pitch": 67},
            {"lane": 1, "beat": 3.25, "pitch": 72},
            {"lane": 2, "beat": 3.5, "pitch": 79},
            {"lane": 3, "beat": 4.0, "pitch": 84},
        ],
        "schema": "FMelodiaChartNote-draft-v1"
    },
    {
        "id": "Chart_Tide_AbyssalSong",
        "skill_name": "Abyssal Song",
        "element": "Tide",
        "instrument": "Drums",
        "difficulty": 2,
        "sp_cost": 2,
        "power_scalar": 2.6,
        "cooldown_turns": 1,
        "resonance_type": "Tide",
        "notes": [
            {"lane": 0, "beat": 0.0, "pitch": 36},
            {"lane": 1, "beat": 0.5, "pitch": 48},
            {"lane": 2, "beat": 0.75, "pitch": 60},
            {"lane": 3, "beat": 1.25, "pitch": 48},
            {"lane": 0, "beat": 1.75, "pitch": 36},
            {"lane": 1, "beat": 2.25, "pitch": 48},
            {"lane": 2, "beat": 2.5, "pitch": 60},
            {"lane": 3, "beat": 3.0, "pitch": 72},
            {"lane": 0, "beat": 3.5, "pitch": 48},
            {"lane": 1, "beat": 3.75, "pitch": 60},
            {"lane": 2, "beat": 4.0, "pitch": 48},
            {"lane": 3, "beat": 4.5, "pitch": 36},
        ],
        "schema": "FMelodiaChartNote-draft-v1"
    },
    {
        "id": "Chart_Stone_TerraFirma",
        "skill_name": "Terra Firma",
        "element": "Stone",
        "instrument": "Drums",
        "difficulty": 1,
        "sp_cost": 1,
        "power_scalar": 1.5,
        "cooldown_turns": 0,
        "resonance_type": "Stone",
        "notes": [
            {"lane": 0, "beat": 0.0, "pitch": 40},
            {"lane": 1, "beat": 0.5, "pitch": 48},
            {"lane": 2, "beat": 1.0, "pitch": 52},
            {"lane": 3, "beat": 1.5, "pitch": 60},
            {"lane": 0, "beat": 2.0, "pitch": 40},
            {"lane": 1, "beat": 2.5, "pitch": 48},
            {"lane": 2, "beat": 3.0, "pitch": 52},
            {"lane": 3, "beat": 3.5, "pitch": 60},
        ],
        "schema": "FMelodiaChartNote-draft-v1"
    },
    {
        "id": "Chart_Gale_StormChase",
        "skill_name": "Storm Chase",
        "element": "Gale",
        "instrument": "Violin",
        "difficulty": 2,
        "sp_cost": 2,
        "power_scalar": 2.5,
        "cooldown_turns": 1,
        "resonance_type": "Gale",
        "notes": [
            {"lane": 0, "beat": 0.0, "pitch": 79},
            {"lane": 1, "beat": 0.25, "pitch": 84},
            {"lane": 2, "beat": 0.5, "pitch": 79},
            {"lane": 3, "beat": 0.75, "pitch": 88},
            {"lane": 0, "beat": 1.0, "pitch": 79},
            {"lane": 1, "beat": 1.25, "pitch": 91},
            {"lane": 2, "beat": 1.5, "pitch": 84},
            {"lane": 3, "beat": 1.75, "pitch": 79},
            {"lane": 0, "beat": 2.0, "pitch": 88},
            {"lane": 1, "beat": 2.5, "pitch": 84},
            {"lane": 2, "beat": 3.0, "pitch": 91},
            {"lane": 3, "beat": 3.5, "pitch": 84},
        ],
        "schema": "FMelodiaChartNote-draft-v1"
    },
]


# ---------------------------------------------------------------------------
# 2. Generic Narrative Quests & Narrative Beats
# ---------------------------------------------------------------------------

NEW_QUESTS = [
    {
        "quest_id": "quest.harmony_awakening",
        "display_name": "Harmony Awakening",
        "description": "Attune to the dawn resonance in the Morning grove and awaken Melusina's inner harmony.",
        "objectives": [
            "Listen to the morning echo with Sir Melodious",
            "Harmonize the resonant cadence in the Morning grove",
            "Unlock the first resonance path to KaleidoNave",
        ],
        "stat_requirements": {"Harmony": 1},
        "rewards": {
            "reward_id": "reward.harmony_awakening",
            "xp": 150,
            "gold": 50,
            "social_stat": {"stat": "Harmony", "delta": 2},
        },
        "idempotency": {
            "intent_id": "intent.quest.harmony_awakening",
            "completion_flag": "quest.harmony_awakening.completed",
        },
    },
    {
        "quest_id": "quest.echoes_of_resonance",
        "display_name": "Echoes of Resonance",
        "description": "Investigate the resonant vibrations echoing across the KaleidoNave cathedral.",
        "objectives": [
            "Explore the resonant cathedral in KaleidoNave",
            "Purify the dissonant note with a 3-hit rhythm combo",
            "Report the cleansed frequency to Petal Priestess",
        ],
        "stat_requirements": {"Tempo": 2},
        "rewards": {
            "reward_id": "reward.echoes_of_resonance",
            "xp": 250,
            "gold": 100,
            "social_stat": {"stat": "Tempo", "delta": 2},
        },
        "idempotency": {
            "intent_id": "intent.quest.echoes_of_resonance",
            "completion_flag": "quest.echoes_of_resonance.completed",
        },
    },
    {
        "quest_id": "quest.twilight_overture",
        "display_name": "Twilight Overture",
        "description": "Perform the twilight overture with the Dreamstate choir to stabilize the boundary rift.",
        "objectives": [
            "Collect 3 starlight resonance fragments",
            "Execute the 4-part polyphonic cadence",
            "Seal the twilight gate with the purified melody",
        ],
        "stat_requirements": {"Timbre": 2},
        "rewards": {
            "reward_id": "reward.twilight_overture",
            "xp": 400,
            "gold": 200,
            "social_stat": {"stat": "Timbre", "delta": 2},
        },
        "idempotency": {
            "intent_id": "intent.quest.twilight_overture",
            "completion_flag": "quest.twilight_overture.completed",
        },
    },
]


def generate_skill_charts() -> list[str]:
    """Write generated chart drafts into Imports/Data/Charts/."""
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    generated_files = []
    for skill in NEW_SKILLS:
        target_path = CHARTS_DIR / f"{skill['id']}.json"
        target_path.write_text(json.dumps(skill, indent=2), encoding="utf-8")
        generated_files.append(str(target_path))
    return generated_files


def generate_narrative_scripts() -> list[str]:
    """Write authored QuillScript (.qsc) and dialogue beats for new quests."""
    DIALOGUE_DIR.mkdir(parents=True, exist_ok=True)
    NARRATIVE_DIR.mkdir(parents=True, exist_ok=True)
    created = []

    # Write VN dialogue beats
    for q in NEW_QUESTS:
        qid = q["quest_id"].replace("quest.", "")
        md_path = DIALOGUE_DIR / f"Quest_{qid}.md"
        md_content = f"""# {q['display_name']} ({q['quest_id']})

[SIR MELODIOUS]: Melusina, the dawn chorus is trembling with a new melody.
[MELUSINA]: I can hear it, Sir. The cadence is gentle, but it asks for an answer.
[SIR MELODIOUS]: Then take your time, tune your heart, and let every note find its place.
[MELUSINA]: [Nods gently] I will listen first, and sing when the echo is ready.
"""
        md_path.write_text(md_content, encoding="utf-8")
        created.append(str(md_path))

    # Write QuillScript narrative asset
    qsc_path = NARRATIVE_DIR / "MelodiaQuillHarmonyAwakening.qsc"
    qsc_content = """@ Start

? if: {quest.harmony_awakening.completed} == on

  - Petal Priestess
    The morning cadence is clear now. Your harmony echoes across the entire nave.

? else:

  - Petal Priestess
    Melusina, the dawn resonance is awaiting your voice.

  - Sir Melodious
    Remember, young melody-weaver: every note carries its own weight. Let it breathe.

  * Answer with the dawn melody. | -> Harmonize
  * Listen quietly to the resonance first. | -> Listen

? endif

$ End

<@> Harmonize

- Melusina
  I hear the cadence. I will harmonize with the morning.

$ Notify melodia:stat:intent.quest.harmony_awakening:melodia_harmony:2
$ Notify melodia:quest:quest.harmony_awakening
$ Notify melodia:reward:reward.harmony_awakening
$ Notify melodia:flag:quest.harmony_awakening.completed
$ End

<@> Listen

- Melusina
  I will listen first. The answer can come when the echo has made room for it.

$ Notify melodia:quest:quest.harmony_awakening
$ End
"""
    qsc_path.write_text(qsc_content, encoding="utf-8")
    created.append(str(qsc_path))
    return created


def update_allowlist_seed() -> dict:
    """Ingest new quest IDs, reward IDs, and narrative flag IDs into allowlist seed."""
    if not ALLOWLIST_SEED.exists():
        raise FileNotFoundError(f"Allowlist seed not found at {ALLOWLIST_SEED}")

    data = json.loads(ALLOWLIST_SEED.read_text(encoding="utf-8"))
    sets = data.setdefault("sets", {})

    quest_ids = sets.setdefault("QuestIds", [])
    narrative_flags = sets.setdefault("NarrativeFlagIds", [])
    dialogue_rewards = sets.setdefault("DialogueRewardIds", [])

    for q in NEW_QUESTS:
        qid = q["quest_id"]
        if qid not in quest_ids:
            quest_ids.append(qid)

        flag_id = q["idempotency"]["completion_flag"]
        if flag_id not in narrative_flags:
            narrative_flags.append(flag_id)

        reward_id = q["rewards"]["reward_id"]
        if reward_id not in dialogue_rewards:
            dialogue_rewards.append(reward_id)

    ALLOWLIST_SEED.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def create_fixture_specs() -> list[str]:
    """Create / update blueprint fixture specifications in specs/blueprints/fixtures/."""
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    created = []

    # Update existing fixture files to ensure top-level readiness is populated
    for fixture_path in FIXTURES_DIR.glob("*.json"):
        try:
            fdata = json.loads(fixture_path.read_text(encoding="utf-8"))
            changed = False
            if "readiness" not in fdata and "readiness_level" in fdata:
                fdata["readiness"] = fdata["readiness_level"]
                changed = True
            elif "readiness" not in fdata:
                fdata["readiness"] = "L1"
                changed = True
            if changed:
                fixture_path.write_text(json.dumps(fdata, indent=2), encoding="utf-8")
        except Exception:
            pass

    # Create new skill fixture: cadence_strike_resonance_skill.v1.json
    cadence_fixture = {
        "schema_version": "1.0",
        "kind": "melodia_content_fixture",
        "fixture_id": "cadence_strike_resonance_skill",
        "status": "contract_spec_only",
        "readiness": "L1",
        "readiness_level": "L1",
        "owner": "Melodia gameplay integration",
        "shared_contract": "specs/blueprints/melodia_content_package.v1.json",
        "package": {
            "PackageId": "melodia.skill.cadence_strike",
            "DefinitionVersion": "1.0",
            "ContentKind": "skill",
            "DisplayName": "Cadence Strike",
            "Tags": ["fixture", "single_target", "rhythm_combat", "forte_resonance"],
            "CapabilityGateContract": "specs/capability/melodia_capability_gate.v1.json",
            "UnlockConditions": ["fixture_always_unlocked"],
            "RequiredNarrativePhase": "first_dream",
            "RequiredRegion": "dreamstate",
            "RequiredTraversalState": "none",
            "AllowedContexts": ["battle_session", "skill_fixture"],
            "BlockedContexts": ["cutscene", "menu", "travel"],
            "ContextPolicy": "fail_closed_and_report_block_reason",
            "ModeSet": ["target_select", "execute", "result"],
            "EnterPolicy": "accept_one_valid_single_target",
            "UpdatePolicy": "hold_target_selection_without_mutating_stock_state",
            "ExitPolicy": "release_target_and_return_stock_result",
            "InterruptPolicy": "cancel_without_cost_or_reward",
            "ResetPolicy": "clear_target_and_restore_fixture_state",
            "VariantSet": ["cadence_strike_default"],
            "EquippedVariantId": "cadence_strike_default",
            "FallbackVariantId": "cadence_strike_default",
            "AnimationProfile": "optional_fixture_animation",
            "VfxProfile": "optional_fixture_vfx",
            "AudioProfile": "optional_fixture_audio",
            "UiPresentation": "skill_fixture_prompt",
            "PreviewPolicy": "show_target_and_cost_before_commit",
            "EffectTogglePolicy": "presentation_only",
            "UnavailableVariantPolicy": "use_fallback_and_keep_execution_valid",
            "EvolutionStage": 0,
            "UpgradeConditions": [],
            "EffectOverrides": [],
            "IdlePresentation": "none",
            "CanonicalStateKey": "melodia.fixture.skill.cadence_strike",
            "IdempotencyKey": "skill.cadence_strike.request_id",
            "SaveWritePolicy": "no_direct_write",
            "MigrationVersion": 1,
            "FixtureMap": "/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap",
            "FixtureRoute": "single_target_skill_entry_and_reset",
            "ExpectedEvidence": "compile_graph_path_runtime_failure_reset",
            "ReadinessLevel": "L1"
        },
        "blueprint": {
            "planned_asset": "/Game/MelodiaIntegration/Blueprints/BP_MelodiaSkill_CadenceStrike",
            "parent_template": "/Game/MelodiaIntegration/Blueprints/BP_MelodiaSkill_Base",
            "runtime_authority": "stock_turn_based_jrpg_session",
            "definition_asset": "/Game/MelodiaIntegration/Definitions/DA_MelodiaSkill_CadenceStrike"
        },
        "deterministic_fixture": {
            "fixture_map": "/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap",
            "entry_route": ["spawn_player", "open_skill_fixture", "select_one_target", "request_stock_execution"],
            "reset_route": ["cancel_or_complete", "clear_target", "restore_stock_session_fixture"],
            "cost": {"resource_id": "skill_points", "amount": 2},
            "cooldown": {"turns": 1, "status": "native_cooldown_contract_pending", "owner": "UMelodiaBattleSession"},
            "target_rules": {"count": 1, "requires_valid_stock_target": True},
            "damage_multipliers": {"Poor": 0.35, "Good": 1.0, "Great": 1.2, "Perfect": 1.5},
            "beat_timings": {"bpm": 128.0, "intro_beats": 1.0, "active_beats": 4.0, "outro_beats": 1.0},
            "resonance_type": "Forte",
            "execution_rule": "request_umelodia_battle_session_and_stock_execution_only",
            "result_tags": ["fixture_skill_requested", "fixture_skill_result_observed"]
        },
        "failure_routes": [
            "invalid_target_does_not_spend_cost",
            "blocked_context_returns_reason_without_execution",
            "cancel_returns_without_cost_or_reward",
            "duplicate_request_id_is_replay_safe"
        ],
        "evidence_required": [
            "definition_path_resolves",
            "blueprint_compiles_without_forbidden_authority",
            "graph_export_contains_target_cost_cooldown_and_stock_request",
            "valid_target_produces_one_stock_result",
            "invalid_target_and_cancel_are_side_effect_free",
            "cooldown_authority_is_present_before_l2_promotion",
            "reset_restores_fixture_state",
            "fresh_evidence_envelope_records_request_id_and_fingerprint"
        ]
    }

    f1_path = FIXTURES_DIR / "cadence_strike_resonance_skill.v1.json"
    f1_path.write_text(json.dumps(cadence_fixture, indent=2), encoding="utf-8")
    created.append(str(f1_path))

    # Create new skill fixture: lullaby_mend_resonance_skill.v1.json
    lullaby_fixture = {
        "schema_version": "1.0",
        "kind": "melodia_content_fixture",
        "fixture_id": "lullaby_mend_resonance_skill",
        "status": "contract_spec_only",
        "readiness": "L1",
        "readiness_level": "L1",
        "owner": "Melodia gameplay integration",
        "shared_contract": "specs/blueprints/melodia_content_package.v1.json",
        "package": {
            "PackageId": "melodia.skill.lullaby_mend",
            "DefinitionVersion": "1.0",
            "ContentKind": "skill",
            "DisplayName": "Lullaby Mend",
            "Tags": ["fixture", "single_target", "heal_support", "radiant_resonance"],
            "CapabilityGateContract": "specs/capability/melodia_capability_gate.v1.json",
            "UnlockConditions": ["fixture_always_unlocked"],
            "RequiredNarrativePhase": "first_dream",
            "RequiredRegion": "dreamstate",
            "RequiredTraversalState": "none",
            "AllowedContexts": ["battle_session", "skill_fixture"],
            "BlockedContexts": ["cutscene", "menu", "travel"],
            "ContextPolicy": "fail_closed_and_report_block_reason",
            "ModeSet": ["target_select", "execute", "result"],
            "EnterPolicy": "accept_one_valid_ally_target",
            "UpdatePolicy": "hold_target_selection_without_mutating_stock_state",
            "ExitPolicy": "release_target_and_return_stock_result",
            "InterruptPolicy": "cancel_without_cost_or_reward",
            "ResetPolicy": "clear_target_and_restore_fixture_state",
            "VariantSet": ["lullaby_mend_default"],
            "EquippedVariantId": "lullaby_mend_default",
            "FallbackVariantId": "lullaby_mend_default",
            "AnimationProfile": "optional_fixture_animation",
            "VfxProfile": "optional_fixture_vfx",
            "AudioProfile": "optional_fixture_audio",
            "UiPresentation": "skill_fixture_prompt",
            "PreviewPolicy": "show_target_and_cost_before_commit",
            "EffectTogglePolicy": "presentation_only",
            "UnavailableVariantPolicy": "use_fallback_and_keep_execution_valid",
            "EvolutionStage": 0,
            "UpgradeConditions": [],
            "EffectOverrides": [],
            "IdlePresentation": "none",
            "CanonicalStateKey": "melodia.fixture.skill.lullaby_mend",
            "IdempotencyKey": "skill.lullaby_mend.request_id",
            "SaveWritePolicy": "no_direct_write",
            "MigrationVersion": 1,
            "FixtureMap": "/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap",
            "FixtureRoute": "single_target_skill_entry_and_reset",
            "ExpectedEvidence": "compile_graph_path_runtime_failure_reset",
            "ReadinessLevel": "L1"
        },
        "blueprint": {
            "planned_asset": "/Game/MelodiaIntegration/Blueprints/BP_MelodiaSkill_LullabyMend",
            "parent_template": "/Game/MelodiaIntegration/Blueprints/BP_MelodiaSkill_Base",
            "runtime_authority": "stock_turn_based_jrpg_session",
            "definition_asset": "/Game/MelodiaIntegration/Definitions/DA_MelodiaSkill_LullabyMend"
        },
        "deterministic_fixture": {
            "fixture_map": "/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap",
            "entry_route": ["spawn_player", "open_skill_fixture", "select_one_target", "request_stock_execution"],
            "reset_route": ["cancel_or_complete", "clear_target", "restore_stock_session_fixture"],
            "cost": {"resource_id": "skill_points", "amount": 2},
            "cooldown": {"turns": 2, "status": "native_cooldown_contract_pending", "owner": "UMelodiaBattleSession"},
            "target_rules": {"count": 1, "requires_valid_stock_target": True},
            "damage_multipliers": {"Poor": 0.35, "Good": 1.0, "Great": 1.2, "Perfect": 1.5},
            "beat_timings": {"bpm": 112.0, "intro_beats": 1.0, "active_beats": 4.5, "outro_beats": 1.0},
            "resonance_type": "Radiant",
            "execution_rule": "request_umelodia_battle_session_and_stock_execution_only",
            "result_tags": ["fixture_skill_requested", "fixture_skill_result_observed"]
        },
        "failure_routes": [
            "invalid_target_does_not_spend_cost",
            "blocked_context_returns_reason_without_execution",
            "cancel_returns_without_cost_or_reward",
            "duplicate_request_id_is_replay_safe"
        ],
        "evidence_required": [
            "definition_path_resolves",
            "blueprint_compiles_without_forbidden_authority",
            "graph_export_contains_target_cost_cooldown_and_stock_request",
            "valid_target_produces_one_stock_result",
            "invalid_target_and_cancel_are_side_effect_free",
            "cooldown_authority_is_present_before_l2_promotion",
            "reset_restores_fixture_state",
            "fresh_evidence_envelope_records_request_id_and_fingerprint"
        ]
    }

    f2_path = FIXTURES_DIR / "lullaby_mend_resonance_skill.v1.json"
    f2_path.write_text(json.dumps(lullaby_fixture, indent=2), encoding="utf-8")
    created.append(str(f2_path))
    return created


def ingest_data_tables() -> dict:
    """Run ollama_import to serialize all charts into DT_MelodySlime_Skills.json."""
    from gmm.game.ollama_import import save_data_tables
    return save_data_tables()


def main() -> int:
    print("=== Step 1: Generating Rhythm Skill Charts ===")
    charts = generate_skill_charts()
    print(f"Generated {len(charts)} rhythm skill charts in Imports/Data/Charts/")

    print("\n=== Step 2: Generating Narrative Quests & Beats ===")
    narrative_files = generate_narrative_scripts()
    print(f"Generated {len(narrative_files)} narrative script files")

    print("\n=== Step 3: Ingesting Quests into Allowlist Seed ===")
    seed = update_allowlist_seed()
    print(f"Updated allowlist seed. Quest IDs count: {len(seed.get('sets', {}).get('QuestIds', []))}")

    print("\n=== Step 4: Ingesting / Updating Blueprint Fixtures ===")
    fixtures = create_fixture_specs()
    print(f"Created/Updated fixture specifications: {len(fixtures)} new fixtures")

    print("\n=== Step 5: Ingesting Data Tables via ollama_import ===")
    dt_result = ingest_data_tables()
    print(f"Data tables updated successfully: {dt_result}")

    print("\n=== Content Generation and Live Ingestion Complete ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
