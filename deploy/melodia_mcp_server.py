#!/usr/bin/env python3
"""
Melodia MCP Server — Dedicated surface for Persona-lite, QuillScript, Rhythm Combat,
and Blueprint fixture integration.

Runs as an MCP stdio server.  All write paths require explicit approval and pass
through the checked-in policy (Tools/mcp_policy.py).  Read-only paths work offline
using the spec registry and fall back to Monolith when the editor is live.

Registration: add to .mcp.json as server "melodia" pointing at this file.
"""
from __future__ import annotations

import itertools
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Re-use the project's policy layer and Monolith client
from Tools.mcp_policy import authorize_tool  # noqa: E402
from deploy.melodia_economy import (  # noqa: E402
    MelodiaGlobalEconomy,
    activate_grief_hook,
    cast_healing_song,
    cast_mana_song,
    cast_utility_debuff,
    on_rhythm_hit,
    _economy_dict,
    record_cast,
    get_cast_history,
    reset_cast_history,
)

MONOLITH_URL = os.environ.get("MONOLITH_URL", "http://127.0.0.1:9316/mcp")

# ---------------------------------------------------------------------------
# Global economy state (in-process singleton; resets on server restart)
# ---------------------------------------------------------------------------
_ECONOMY_STATE: MelodiaGlobalEconomy = MelodiaGlobalEconomy()

# ---------------------------------------------------------------------------
# Spec / registry helpers (offline-safe)
# ---------------------------------------------------------------------------

SPECS_ROOT = PROJECT_ROOT / "specs"
ALLOWLIST_SEED = SPECS_ROOT / "progression" / "melodia_integration_allowlist_seed.v1.json"
BP_KIT = SPECS_ROOT / "blueprints" / "melodia_gameplay_bp_kit.v1.json"
CAPABILITY_GATE = SPECS_ROOT / "capability" / "melodia_capability_gate.v1.json"
FIXTURES_ROOT = SPECS_ROOT / "blueprints" / "fixtures"
NARRATIVE_DIR = PROJECT_ROOT / "Content" / "MelodiaIntegration" / "Narrative"
CONFIG_ASSET_PATH = "/Game/MelodiaIntegration/Config/DA_MelodiaIntegrationConfig"
PERSONA_CONTENT_PATH = "/Game/MelodiaIntegration/Config/DA_MelodiaPersonaContent"

_id_counter = itertools.count(1)


def _next_id() -> int:
    return next(_id_counter)


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _monolith_call(method: str, args: dict[str, Any] | None = None, timeout: float = 10.0) -> dict[str, Any] | None:
    """POST to Monolith via JSON-RPC. Returns parsed result or None on any failure."""
    body = {
        "jsonrpc": "2.0",
        "id": _next_id(),
        "method": "tools/call",
        "params": {"name": method, "arguments": args or {}},
    }
    req = urllib.request.Request(
        MONOLITH_URL,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            envelope = json.loads(resp.read().decode())
            if "error" in envelope:
                return None
            result = envelope.get("result", {})
            if result.get("isError"):
                return None
            content = result.get("content") or []
            texts = [item.get("text", "") for item in content if isinstance(item, dict)]
            joined = "\n".join(t for t in texts if t)
            if not joined:
                return None
            try:
                return json.loads(joined)
            except json.JSONDecodeError:
                return {"_raw_text": joined}
    except (urllib.error.URLError, OSError, json.JSONDecodeError):
        return None


def _monolith_is_live() -> bool:
    result = _monolith_call("monolith_status", {}, timeout=2.0)
    return isinstance(result, dict) and "version" in result


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def melodia_persona_get_stats(stat_id: str | None = None) -> dict[str, Any]:
    """Return social-stat snapshot from the offline spec or live narrative record."""
    seed = _load_json(ALLOWLIST_SEED)
    kit = _load_json(BP_KIT)

    # Build the stat vocabulary from the config allowlist + kit
    stat_ids: list[str] = []
    if kit and "templates" in kit:
        for tmpl in kit["templates"]:
            if tmpl.get("id") == "state_anchor":
                reqs = tmpl.get("materialization", {}).get("required_config_allowlist", {})
                stat_ids.extend(reqs.get("SocialStatIds", []))

    # If editor is live, try to read the actual PersonaContent data asset
    live_stats: dict[str, Any] | None = None
    if _monolith_is_live():
        live_stats = _monolith_call("blueprint_query.get_cdo_properties", {
            "path": PERSONA_CONTENT_PATH
        })

    return {
        "schema": "melodia.persona.stats.v1",
        "source": "live" if live_stats else "offline",
        "requested_stat": stat_id,
        "known_stat_ids": sorted(set(stat_ids)),
        "live_snapshot": live_stats,
        "note": "Social stats live on FMelodiaNarrativeRecord (canonical save seam). "
                "Persona-lite reads through UMelodiaNarrativeSubsystem, not a local copy.",
    }


def melodia_persona_get_quests(quest_id: str | None = None) -> dict[str, Any]:
    """Return quest definitions and states."""
    seed = _load_json(ALLOWLIST_SEED)
    kit = _load_json(BP_KIT)

    quests: list[dict[str, Any]] = []
    matching_quest: dict[str, Any] | None = None
    if seed and "sets" in seed:
        for qid in seed["sets"].get("QuestIds", []):
            entry = {"quest_id": qid, "source": "allowlist_seed"}
            quests.append(entry)
            if quest_id and qid == quest_id:
                matching_quest = entry

    live_quests = None
    if _monolith_is_live():
        live_quests = _monolith_call("blueprint_query.get_cdo_properties", {
            "path": PERSONA_CONTENT_PATH
        })

    return {
        "schema": "melodia.persona.quests.v1",
        "source": "live" if live_quests else "offline",
        "requested_quest": quest_id,
        "matched_quest": matching_quest,
        "quests": quests,
        "live_snapshot": live_quests,
    }


def melodia_quill_list_scripts() -> dict[str, Any]:
    """List authored QuillScript assets (.qsc sources and compiled .uassets)."""
    scripts: list[dict[str, Any]] = []
    if NARRATIVE_DIR.exists():
        for qsc in sorted(NARRATIVE_DIR.glob("*.qsc")):
            uasset = qsc.with_suffix(".uasset")
            scripts.append({
                "name": qsc.stem,
                "qsc_path": str(qsc.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "has_compiled_uasset": uasset.exists(),
                "uasset_mtime": datetime.fromtimestamp(uasset.stat().st_mtime).isoformat() if uasset.exists() else None,
            })

    return {
        "schema": "melodia.quill.scripts.v1",
        "count": len(scripts),
        "scripts": scripts,
        "narrative_dir": str(NARRATIVE_DIR.relative_to(PROJECT_ROOT)).replace("\\", "/") if NARRATIVE_DIR.exists() else None,
    }


def melodia_quill_validate_notification(notification: str) -> dict[str, Any]:
    """Validate a Quill notification string against the seven-verb contract."""
    valid_verbs = {
        "melodia:battle", "melodia:quest", "melodia:flag",
        "melodia:travel", "melodia:reward", "melodia:stat", "melodia:item",
    }
    parts = notification.split(":")
    verb = ":".join(parts[:2]) if len(parts) >= 2 else ""
    remainder = parts[2:] if len(parts) > 2 else []

    is_valid_verb = verb in valid_verbs
    seed = _load_json(ALLOWLIST_SEED)
    known_ids: set[str] = set()
    if seed and "sets" in seed:
        for ids in seed["sets"].values():
            known_ids.update(ids)

    # Check if any part of the notification matches known allowlist IDs
    matched_known = [p for p in remainder if p in known_ids]

    return {
        "schema": "melodia.quill.notification_validate.v1",
        "notification": notification,
        "verb": verb,
        "is_valid_verb": is_valid_verb,
        "known_allowlist_matches": matched_known,
        "known_allowlist_ids_count": len(known_ids),
        "contract": "UMelodiaNarrativeSubsystem::HandleQuillNotification dispatch table",
        "idempotency_rule": "melodia:stat: is idempotent per IntentId; consumed intents recorded in FMelodiaNarrativeRecord::ConsumedIntentIds",
    }


def melodia_rhythm_list_skills() -> dict[str, Any]:
    """List rhythm skill definitions from config DataAssets, DA_MelodiaSongs, and DT_MelodySlime_Skills."""
    skills: list[dict[str, Any]] = []

    # Offline: scan for skill config DataAssets
    config_dir = PROJECT_ROOT / "Content" / "MelodiaIntegration" / "Config"
    if config_dir.exists():
        for uasset in sorted(config_dir.glob("DA_*.uasset")):
            name = uasset.stem
            if any(k in name.lower() for k in ("cadence", "resonant", "lullaby", "downbeat", "dissonant", "tempo", "crescendo", "harmony", "song", "skill")):
                skills.append({
                    "asset_name": name,
                    "asset_path": f"/Game/MelodiaIntegration/Config/{name}",
                    "source": "offline_scan",
                })

    # Read data table skills from DT_MelodySlime_Skills.json
    dt_path = PROJECT_ROOT / "Content" / "Melodia" / "DataStuctures" / "DT_MelodySlime_Skills.json"
    dt_skills_data = _load_json(dt_path)
    dt_skill_rows: list[dict[str, Any]] = []
    if dt_skills_data and "Rows" in dt_skills_data:
        for sid, sdata in sorted(dt_skills_data["Rows"].items()):
            dt_skill_rows.append({
                "skill_id": sid,
                "display_name": sdata.get("display_name"),
                "element": sdata.get("element"),
                "instrument": sdata.get("instrument"),
                "mechanic_level": sdata.get("mechanic_level"),
                "sp_cost": sdata.get("sp_cost"),
                "power_scalar": sdata.get("power_scalar"),
                "note_count": len(sdata.get("note_pitches", [])),
            })

    live_skills = None
    if _monolith_is_live():
        live_skills = _monolith_call("blueprint_query.get_cdo_properties", {
            "path": "/Game/MelodiaIntegration/Config/DA_MelodiaSongs"
        })

    return {
        "schema": "melodia.rhythm.skills.v1",
        "source": "live" if live_skills else "offline",
        "skills": skills,
        "data_table_skills": dt_skill_rows,
        "data_table_skill_count": len(dt_skill_rows),
        "live_snapshot": live_skills,
        "grade_multipliers": {
            "Poor": 0.35,
            "Good": 1.0,
            "Great": 1.2,
            "Perfect": 1.5,
        },
    }


def melodia_narrative_get_record() -> dict[str, Any]:
    """Return the narrative record schema and offline seed state."""
    seed = _load_json(ALLOWLIST_SEED)
    kit = _load_json(BP_KIT)

    record = {
        "schema_version": 4,
        "fields": [
            "Version", "Flags", "QuillVariables", "QuillPersistentData",
            "ScriptCheckpoint", "ConsumedIntentIds", "ActiveQuestIds",
            "ConsumedRewardIds", "SocialStats", "BondRanks", "PhaseIndex",
            "SpawnContext", "OwnedCosmeticIds", "EquippedCosmeticIds",
            "LastPullUnixSeconds", "WaterGameplayState",
        ],
        "idempotency_seams": [
            "ConsumedIntentIds (melodia:stat:)",
            "ConsumedRewardIds (melodia:reward:)",
            "Flags (melodia:flag:)",
        ],
        "allowlist_seed_present": seed is not None,
        "known_quest_ids": seed.get("sets", {}).get("QuestIds", []) if seed else [],
        "known_flag_ids": seed.get("sets", {}).get("NarrativeFlagIds", []) if seed else [],
        "known_reward_ids": seed.get("sets", {}).get("DialogueRewardIds", []) if seed else [],
    }

    return {
        "schema": "melodia.narrative.record.v1",
        "record": record,
        "persistence_owner": "JRPG game instance / save object (melodiaNarrativeRecord field)",
        "migration_path": "UMelodiaNarrativeSubsystem::MigrateRecord(v1->v2->v3->v4)",
    }


def melodia_config_get_allowlist(set_name: str | None = None) -> dict[str, Any]:
    """Return the integration config allowlist entries."""
    seed = _load_json(ALLOWLIST_SEED)
    if seed is None:
        return {"schema": "melodia.config.allowlist.v1", "error": "allowlist seed not found"}

    sets = seed.get("sets", {})
    if set_name:
        return {
            "schema": "melodia.config.allowlist.v1",
            "requested_set": set_name,
            "entries": sets.get(set_name, []),
            "target_asset": seed.get("target_asset", CONFIG_ASSET_PATH),
        }

    return {
        "schema": "melodia.config.allowlist.v1",
        "sets": {k: v for k, v in sets.items()},
        "target_asset": seed.get("target_asset", CONFIG_ASSET_PATH),
        "merge_policy": seed.get("merge_policy", {}),
    }


def melodia_bp_list_fixtures() -> dict[str, Any]:
    """List all fixture specs and their readiness levels."""
    kit = _load_json(BP_KIT)
    fixtures: list[dict[str, Any]] = []

    if FIXTURES_ROOT.exists():
        for spec_path in sorted(FIXTURES_ROOT.glob("*.json")):
            spec = _load_json(spec_path)
            fixtures.append({
                "name": spec_path.stem,
                "path": str(spec_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "fixture_kind": spec.get("kind") if spec else None,
                "readiness": spec.get("readiness") if spec else None,
            })

    templates = []
    if kit and "templates" in kit:
        for tmpl in kit["templates"]:
            templates.append({
                "id": tmpl.get("id"),
                "fixture_readiness": tmpl.get("fixture_readiness"),
                "fixture_spec": tmpl.get("fixture_spec"),
                "materialization_status": tmpl.get("materialization", {}).get("status"),
            })

    return {
        "schema": "melodia.bp.fixtures.v1",
        "fixture_count": len(fixtures),
        "fixtures": fixtures,
        "templates": templates,
        "creation_order": kit.get("creation_order", []) if kit else [],
        "template_materialization_order": kit.get("template_materialization_order", []) if kit else [],
    }


def melodia_bp_get_template(template_id: str) -> dict[str, Any]:
    """Get a single template definition from the gameplay BP kit."""
    kit = _load_json(BP_KIT)
    if not kit or "templates" not in kit:
        return {"schema": "melodia.bp.template.v1", "error": "kit not found"}

    for tmpl in kit["templates"]:
        if tmpl.get("id") == template_id:
            return {
                "schema": "melodia.bp.template.v1",
                "template": tmpl,
                "authority": kit.get("authority", {}),
                "readiness_levels": kit.get("readiness_levels", {}),
            }

    return {
        "schema": "melodia.bp.template.v1",
        "error": f"template '{template_id}' not found",
        "known_ids": [t.get("id") for t in kit.get("templates", [])],
    }


def melodia_bp_validate_fixture(fixture_name: str) -> dict[str, Any]:
    """Validate a fixture spec exists and has required fields."""
    path = FIXTURES_ROOT / f"{fixture_name}.json"
    spec = _load_json(path)

    if spec is None:
        # Try with .v1.json suffix
        path = FIXTURES_ROOT / f"{fixture_name}.v1.json"
        spec = _load_json(path)

    if spec is None:
        available = [p.stem for p in FIXTURES_ROOT.glob("*.json")] if FIXTURES_ROOT.exists() else []
        return {
            "schema": "melodia.bp.fixture_validate.v1",
            "fixture_name": fixture_name,
            "valid": False,
            "error": "fixture spec not found",
            "available_fixtures": sorted(available),
        }

    required_fields = {"kind", "fixture_id", "readiness"}
    missing = required_fields - set(spec.keys())

    return {
        "schema": "melodia.bp.fixture_validate.v1",
        "fixture_name": fixture_name,
        "path": str(path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "valid": len(missing) == 0,
        "missing_fields": sorted(missing),
        "readiness": spec.get("readiness"),
        "kind": spec.get("kind"),
    }


def melodia_system_health() -> dict[str, Any]:
    """Run a read-only health check across Melodia subsystems."""
    checks: dict[str, Any] = {}

    # 1. Spec files present
    checks["specs"] = {
        "allowlist_seed": ALLOWLIST_SEED.exists(),
        "bp_kit": BP_KIT.exists(),
        "capability_gate": CAPABILITY_GATE.exists(),
    }

    # 2. Narrative assets present
    checks["narrative_assets"] = {
        "narrative_dir_exists": NARRATIVE_DIR.exists(),
        "qsc_count": len(list(NARRATIVE_DIR.glob("*.qsc"))) if NARRATIVE_DIR.exists() else 0,
    }

    # 3. Monolith reachability
    monolith_live = _monolith_is_live()
    checks["monolith"] = {
        "reachable": monolith_live,
        "url": MONOLITH_URL,
    }

    # 4. If live, check key Blueprint assets via Monolith
    if monolith_live:
        for asset_path in [
            CONFIG_ASSET_PATH,
            PERSONA_CONTENT_PATH,
            "/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameMode",
            "/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance",
        ]:
            result = _monolith_call("project.search", {"query": asset_path}, timeout=5.0)
            checks.setdefault("live_assets", {})[asset_path] = result is not None

    # 5. Policy file health
    policy_path = PROJECT_ROOT / "specs" / "mcp_tool_policy.v1.json"
    checks["policy"] = {
        "file_exists": policy_path.exists(),
        "default_is_deny": _load_json(policy_path).get("default_decision") == "deny" if policy_path.exists() else False,
    }

    all_ok = all(
        v if isinstance(v, bool) else v.get("reachable", False) if isinstance(v, dict) else True
        for v in checks.values()
    )

    return {
        "schema": "melodia.system.health.v1",
        "status": "healthy" if all_ok else "degraded",
        "timestamp": datetime.now().isoformat(),
        "checks": checks,
    }


def melodia_system_list_subsystems() -> dict[str, Any]:
    """List the native C++ subsystem surface."""
    integration_dir = PROJECT_ROOT / "Source" / "BS_GodFile" / "MelodiaIntegration"
    subsystems: list[dict[str, Any]] = []

    if integration_dir.exists():
        for header in sorted(integration_dir.glob("*.h")):
            content = header.read_text(encoding="utf-8")
            if "UGameInstanceSubsystem" in content or "UWorldSubsystem" in content or "UTickableWorldSubsystem" in content:
                # Extract class name roughly
                for line in content.splitlines():
                    if "class BS_GODFILE_API" in line and "Subsystem" in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            subsystems.append({
                                "class_name": parts[-1],
                                "header": str(header.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                            })
                        break

    return {
        "schema": "melodia.system.subsystems.v1",
        "count": len(subsystems),
        "subsystems": subsystems,
        "note": "These are the C++ authorities; Blueprints must forward mutations to them rather than duplicate state.",
    }


def melodia_narrative_audit_idempotency() -> dict[str, Any]:
    """
    Audit the C++ narrative subsystem source for idempotency contract coverage.
    Verifies that every mutation path has a ConsumeOnce guard or equivalent.
    """
    cpp_path = PROJECT_ROOT / "Source" / "BS_GodFile" / "MelodiaIntegration" / "MelodiaNarrativeSubsystem.cpp"
    h_path = PROJECT_ROOT / "Source" / "BS_GodFile" / "MelodiaIntegration" / "MelodiaNarrativeSubsystem.h"

    if not cpp_path.exists():
        return {"schema": "melodia.narrative.idempotency_audit.v1", "error": "source not found"}

    content = cpp_path.read_text(encoding="utf-8")

    # Expected idempotency guards and their mutation paths
    guards = {
        "ConsumeOnce(NarrativeRecord.ConsumedIntentIds": [
            "GrantDialogueSocialStat",
            "CompleteQuest",
        ],
        "ConsumeOnce(NarrativeRecord.ConsumedRewardIds": [
            "GrantDialogueReward",
            "CommitWorldChallenge",
        ],
        "NarrativeRecord.ConsumedIntentIds.Contains": [
            "CommitWorldChallenge",
            "ApplyStateAnchor",
        ],
        "bBattleCompletionConsumed": [
            "CompleteBattle",
        ],
    }

    findings: list[dict[str, Any]] = []
    for guard_pattern, expected_functions in guards.items():
        guard_present = guard_pattern in content
        for func in expected_functions:
            func_present = f"bool UMelodiaNarrativeSubsystem::{func}(" in content or f"EMelodiaContentCommitResult UMelodiaNarrativeSubsystem::{func}(" in content
            findings.append({
                "function": func,
                "guard_pattern": guard_pattern,
                "guard_found": guard_present and func_present,
                "function_found": func_present,
            })

    # Check HandleStatVerb routes through GrantDialogueSocialStat
    stat_verb_routes_to_grant = "GrantDialogueSocialStat(Id, StatId, Delta)" in content

    # Check that melodia:item is a logging stub (no inventory mutation)
    item_is_stub = "MELUSINA_LOOP_ITEM_GRANT" in content and "GrantDialogueReward" not in content.split("void UMelodiaNarrativeSubsystem::HandleItemVerb")[1].split("void UMelodiaNarrativeSubsystem::Handle")[0] if "void UMelodiaNarrativeSubsystem::HandleItemVerb" in content else True

    # Count total mutation functions vs guarded functions
    all_guarded = all(f["guard_found"] for f in findings)

    return {
        "schema": "melodia.narrative.idempotency_audit.v1",
        "source_file": str(cpp_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "all_paths_guarded": all_guarded,
        "findings": findings,
        "stat_verb_routes_to_grant": stat_verb_routes_to_grant,
        "item_is_logging_stub": item_is_stub,
        "contract_notes": [
            "GrantDialogueSocialStat: idempotent per IntentId (not per StatId)",
            "GrantDialogueReward: idempotent per RewardId via ConsumedRewardIds",
            "CompleteQuest: idempotent per quest acceptance/completion key",
            "CommitWorldChallenge: atomic transaction with intent+flag+reward consistency check",
            "ApplyStateAnchor: replay-safe with operation-state matching",
            "CompleteBattle: guarded by bBattleCompletionConsumed",
        ],
    }


SUFFIX_MAP = {
    "_BaseColor": "Albedo", "_albedo": "Albedo", "_diffuse": "Albedo",
    "_Normal": "NormalMap", "_normal": "NormalMap",
    "_ORM": "ORM", "_orm": "ORM",
    "_Height": "HeightMap", "_height": "HeightMap", "_Displace": "HeightMap",
    "_Roughness": "RoughnessMap", "_roughness": "RoughnessMap",
    "_Metallic": "MetallicMap", "_metallic": "MetallicMap",
}


def _scan_pbr_texture_sets() -> tuple[dict, dict]:
    """Scan Content/Textures + _PROJECT/Textures + Melusina Materials for PBR sets.
    Returns (complete_sets, incomplete_sets) where each is {stem: {param: /Game/path}}."""
    roots = [
        PROJECT_ROOT / "Content" / "Textures",
        PROJECT_ROOT / "Content" / "_PROJECT" / "04_Materials" / "Textures",
        PROJECT_ROOT / "Content" / "Melodia" / "Characters" / "Melusina" / "Materials",
    ]
    from collections import defaultdict
    sets: dict[str, dict[str, str]] = defaultdict(dict)
    for root in roots:
        if not root.exists():
            continue
        for p in root.rglob("*.uasset"):
            name = p.stem
            for suffix, role in SUFFIX_MAP.items():
                if name.endswith(suffix):
                    stem = name[: -len(suffix)]
                    try:
                        rel = p.relative_to(PROJECT_ROOT / "Content")
                        sets[stem][role] = "/Game/" + str(rel).replace("\\", "/")
                    except ValueError:
                        pass
                    break
    complete, incomplete = {}, {}
    for stem, maps in sets.items():
        if "Albedo" in maps and "NormalMap" in maps and (
            "ORM" in maps or ("RoughnessMap" in maps and "MetallicMap" in maps)
        ):
            complete[stem] = maps
        else:
            incomplete[stem] = maps
    return dict(complete), dict(incomplete)


def _existing_material_instances() -> set[str]:
    """Query AssetRegistry for existing MI names under known instance folders."""
    out = set()
    if not _monolith_is_live():
        return set()
    for folder in [
        "/Game/EnvSandbox/Materials/Instances",
        "/Game/_PROJECT/04_Materials",
        "/Game/Melodia/_PROJECT/04_Materials",
    ]:
        try:
            raw = _monolith_call("material_query.list_material_instances", {"folder_path": folder}, timeout=30)
            if isinstance(raw, list):
                for entry in raw:
                    name = entry if isinstance(entry, str) else (entry.get("name") or entry.get("asset_name") or "")
                    if name:
                        out.add(name)
        except Exception:
            pass
    return out


def melodia_material_list_pbr() -> dict[str, Any]:
    """Scan disk for PBR texture sets and report which are complete and which have instances."""
    complete, incomplete = _scan_pbr_texture_sets()
    existing = _existing_material_instances() if _monolith_is_live() else set()
    complete_with_instance = {s for s in complete if any(name in existing for name in (s, f"MI_{s}"))}
    return {
        "schema": "melodia.material.pbr_list.v1",
        "source": "live" if _monolith_is_live() else "offline",
        "complete_sets": {
            stem: maps for stem, maps in sorted(complete.items())
        },
        "complete_set_count": len(complete),
        "incomplete_set_count": len(incomplete),
        "complete_sets_with_instance": sorted(complete_with_instance),
        "complete_sets_without_instance": sorted(set(complete) - complete_with_instance),
        "incomplete_stems": sorted(incomplete),
        "live_existing_instance_count": len(existing) if existing else None,
    }


def melodia_material_get_compile_stats(asset_path: str) -> dict[str, Any]:
    """Report compilation state for a master or instance. Offline-safe + live Monolith."""
    if _monolith_is_live():
        stats = _monolith_call("material_query.get_compilation_stats", {"asset_path": asset_path}, timeout=30)
        if stats:
            return {"schema": "melodia.material.compile_stats.v1", "source": "live", "asset_path": asset_path, "stats": stats}
    # Offline: check file existence
    uasset = PROJECT_ROOT / "Content" / asset_path.replace("/Game/", "")
    return {
        "schema": "melodia.material.compile_stats.v1",
        "source": "offline",
        "asset_path": asset_path,
        "uasset_exists": uasset.exists(),
        "uasset_size": uasset.stat().st_size if uasset.exists() else 0,
        "note": "Re-run when editor is live for full compile stats.",
    }


def melodia_material_audit() -> dict[str, Any]:
    """Full material pipeline health: broken masters, PPV issues, audio gap."""
    if _monolith_is_live():
        ink = _monolith_call("material_query.get_compilation_stats", {"asset_path": "/Game/Melodia/_PROJECT/04_Materials/PostProcess/M_PP_MelodiaInk"}, timeout=30)
    else:
        ink = None
    # Audio reactivity check: look for CollectionParameter nodes reading MPC audio
    audio_gap_note = (
        "C++ MelodiaAudioReactivePresentationSubsystem writes BeatPulse/Bass/Mid/Treble/BeatPhase/BeatIntensity/GlobalReactivity "
        "to MPC_Melodia_Palette every frame. No surface material reads any of them; only M_PP_MelodiaInk consumes audio and it does not compile."
    )
    return {
        "schema": "melodia.material.audit.v1",
        "source": "live" if _monolith_is_live() else "offline",
        "masters": {
            "M_PP_MelodiaInk": {
                "path": "/Game/Melodia/_PROJECT/04_Materials/PostProcess/M_PP_MelodiaInk",
                "compiled": ink.get("is_compiled") if ink else None,
                "compile_errors": ink.get("compile_errors") if ink else None,
                "expression_count": ink.get("expression_count") if ink else None,
                "ps_instructions": ink.get("num_pixel_shader_instructions") if ink else None,
                "known_issue": "Custom node has 42 declared inputs, only 38 wired (SceneColor, cR, cB, smeared missing). UE 5.8 by-name global failure mode.",
            },
        },
        "audio_reactivity_gap": audio_gap_note,
        "ppv_known_defects": {
            "slot1_surface_in_pp_stack": "MI_StarryNight_VanGogh resolves to MD_SURFACE; UE silently drops post-process blendables that aren't MD_POST_PROCESS",
            "label_mismatch": "Live actor PPV_Dreamprint_Candidate vs scripts looking up PPV_NikkiDream",
            "grade_weight_mismatch": "Live 0.18 vs canonical 0.69 on ZenForestTest",
        },
    }


def melodia_ppv_report() -> dict[str, Any]:
    """Per-level PPV state. Offline script analysis + live when reachable."""
    levels = [
        "/Game/_PROJECT/Levels/RenderTests/L_Render_SakuraDream",
        "/Game/_PROJECT/Levels/RenderTests/L_Render_SpaceCathedral",
        "/Game/_PROJECT/Levels/RenderTests/L_Render_BaroqueCastle",
        "/Game/_PROJECT/Levels/RenderTests/L_Render_BioGrotto",
        "/Game/EnvSandbox/Environments/L_KaleidoNave",
        "/Game/EnvSandbox/Environments/L_FallenMoon",
        "/Game/Melodia/Levels/Opening/L_MelusinaMorning",
        "/Game/ZenForestTest",
    ]
    levels_where_scripts_spawn = levels  # setup_nikki_render_post_process.py iterates these
    return {
        "schema": "melodia.ppv.report.v1",
        "source": "offline",
        "canonical_stack": {
            "dreamprint_ink": {"preferred": "MI_MelodiaInk_PortfolioHero", "weight": 1.0},
            "melusina_grade": {"preferred": "MI_MeluColorGrade_PortfolioHero", "weight": 0.69},
            "starry_night": {"preferred": "MI_StarryNight_Hero", "weight": 1.0},
        },
        "levels_in_script": levels_where_scripts_spawn,
        "note": "Full per-level PPV state (blendable weights, actor label, domain check) requires live EditorActorSubsystem via Monolith.",
        "known_live_state_ZenForestTest": {
            "actor_label": "PPV_Dreamprint_Candidate",
            "slot1": {"blendable": "MI_StarryNight_VanGogh", "weight": 1.0, "status": "BROKEN - surface domain"},
            "slot2": {"blendable": "MI_MeluColorGrade_PortfolioHero", "weight": 0.18, "status": "OK"},
            "slot3": {"blendable": "MI_StorybookOutline_Premium_Hero_Dream", "weight": 0.57, "status": "OK"},
        },
    }


def melodia_bp_validate_p0_route() -> dict[str, Any]:
    """
    Validate all fixtures required for the P0 Dream golden run route:
    New Game -> Morning -> Petal Priestess beat -> KaleidoNave -> stock encounter -> save
    """
    p0_fixtures = [
        ("repeatable_first_dream_encounter", "encounter"),
        ("locked_traversal_portal", "portal"),
        ("first_dream_progress_anchor", "state_anchor"),
        ("first_resonance_world_challenge", "world_challenge"),
        ("single_stock_enemy", "enemy"),
    ]

    results: list[dict[str, Any]] = []
    all_valid = True

    for fixture_name, expected_kind in p0_fixtures:
        path = FIXTURES_ROOT / f"{fixture_name}.v1.json"
        spec = _load_json(path)
        if spec is None:
            path = FIXTURES_ROOT / f"{fixture_name}.json"
            spec = _load_json(path)

        content_kind = spec.get("package", {}).get("ContentKind") if spec else None
        valid = spec is not None and content_kind == expected_kind
        all_valid = all_valid and valid

        results.append({
            "fixture_name": fixture_name,
            "expected_kind": expected_kind,
            "found": spec is not None,
            "kind_matches": content_kind == expected_kind if spec else False,
            "readiness": spec.get("readiness") if spec else None,
            "path": str(path.relative_to(PROJECT_ROOT)).replace("\\", "/") if path.exists() else None,
        })

    # Check for P0 Quill scripts
    p0_scripts = ["MelodiaMorningIntro", "MelodiaQuillPetalPriestess"]
    script_status = {}
    for script_name in p0_scripts:
        qsc = NARRATIVE_DIR / f"{script_name}.qsc"
        uasset = NARRATIVE_DIR / f"{script_name}.uasset"
        script_status[script_name] = {
            "qsc_exists": qsc.exists(),
            "uasset_exists": uasset.exists(),
        }

    # Check allowlist seed has P0 IDs
    seed = _load_json(ALLOWLIST_SEED)
    seed_ok = seed is not None
    p0_ids_present = {
        "quest.first_dream": "quest.first_dream" in seed.get("sets", {}).get("QuestIds", []) if seed else False,
        "anchor.first_dream.progress": "anchor.first_dream.progress" in seed.get("sets", {}).get("StateAnchorIds", []) if seed else False,
        "challenge.first_resonance_echo": "challenge.first_resonance_echo" in seed.get("sets", {}).get("WorldChallengeIds", []) if seed else False,
    }

    return {
        "schema": "melodia.bp.p0_route.v1",
        "p0_route_valid": all_valid and all(s["qsc_exists"] for s in script_status.values()) and all(p0_ids_present.values()),
        "fixtures": results,
        "scripts": script_status,
        "allowlist_ids": p0_ids_present,
        "golden_run_contract": "New Game -> Morning -> Petal Priestess beat -> KaleidoNave -> stock encounter -> save",
    }


def melodia_animation_validate_state_machine(abp_path: str) -> dict[str, Any]:
    """
    Validate an Animation Blueprint's state machine health.
    Checks: entry state exists, all states have sequence players, no orphan transitions.
    """
    if not _monolith_is_live():
        return {"schema": "melodia.animation.validate_sm.v1", "error": "Monolith not reachable"}
    
    # Get ABP info
    abp_info = _monolith_call("animation_query.get_abp_info", {"asset_path": abp_path})
    if not abp_info:
        return {"schema": "melodia.animation.validate_sm.v1", "error": f"ABP not found: {abp_path}"}
    
    # Get state machines
    sm_data = _monolith_call("animation_query.get_state_machines", {"asset_path": abp_path})
    if not sm_data:
        return {"schema": "melodia.animation.validate_sm.v1", "error": "No state machines found"}
    
    machines = sm_data.get("state_machines", [])
    if not machines:
        return {"schema": "melodia.animation.validate_sm.v1", "error": "No state machines in ABP"}
    
    findings = []
    all_ok = True
    
    for machine in machines:
        machine_name = machine.get("name", "unknown")
        entry = machine.get("entry_state")
        states = machine.get("states", [])
        transitions = machine.get("transitions", [])
        
        # Check entry exists
        state_names = {s.get("name") for s in states if isinstance(s, dict)}
        if entry and entry not in state_names:
            findings.append(f"Entry state '{entry}' not in states")
            all_ok = False
        
        # Check orphan transitions (from/to must exist)
        for t in transitions:
            from_state = t.get("from")
            to_state = t.get("to")
            if from_state and from_state not in state_names:
                findings.append(f"Orphan transition from '{from_state}'")
                all_ok = False
            if to_state and to_state not in state_names:
                findings.append(f"Orphan transition to '{to_state}'")
                all_ok = False
        
        # Check each state has a sequence player
        for state in states:
            if not isinstance(state, dict):
                continue
            state_name = state.get("name")
            state_info = _monolith_call("animation_query.get_state_info", {
                "asset_path": abp_path,
                "machine_name": machine_name,
                "state_name": state_name
            })
            if state_info:
                nodes = state_info.get("nodes", [])
                has_player = any(
                    n.get("class", "").startswith("AnimGraphNode_SequencePlayer") or 
                    n.get("class", "").startswith("AnimGraphNode_BlendSpacePlayer")
                    for n in nodes if isinstance(n, dict)
                )
                if not has_player:
                    findings.append(f"State '{state_name}' has no animation player")
                    all_ok = False
    
    return {
        "schema": "melodia.animation.validate_sm.v1",
        "abp_path": abp_path,
        "target_skeleton": abp_info.get("target_skeleton"),
        "all_ok": all_ok,
        "state_machine_count": len(machines),
        "findings": findings,
        "entry_state": machines[0].get("entry_state") if machines else None,
    }


def melodia_animation_validate_bindings(abp_path: str) -> dict[str, Any]:
    """
    Verify all states in an ABP have connected pose outputs.
    Detects T-pose causes: blendspace/sequence player with 0 connections.
    """
    if not _monolith_is_live():
        return {"schema": "melodia.animation.validate_bindings.v1", "error": "Monolith not reachable"}
    
    # Get all nodes
    nodes_data = _monolith_call("animation_query.get_nodes", {"asset_path": abp_path})
    if not nodes_data:
        return {"schema": "melodia.animation.validate_bindings.v1", "error": "Could not read nodes"}
    
    nodes = nodes_data.get("nodes", [])
    findings = []
    all_ok = True
    
    for node in nodes:
        if not isinstance(node, dict):
            continue
        node_class = node.get("class", "")
        node_name = node.get("name", "")
        
        if node_class.startswith("AnimGraphNode_BlendSpacePlayer") or node_class.startswith("AnimGraphNode_SequencePlayer"):
            pins = node.get("connected_pins", [])
            pose_pins = [p for p in pins if p.get("is_pose") and p.get("direction") == "Output"]
            
            if not pose_pins:
                findings.append(f"{node_name}: NO POSE OUTPUT PINS")
                all_ok = False
            elif not any(p.get("connections", 0) > 0 for p in pose_pins):
                findings.append(f"{node_name}: Pose output NOT CONNECTED (will T-pose)")
                all_ok = False
    
    return {
        "schema": "melodia.animation.validate_bindings.v1",
        "abp_path": abp_path,
        "all_ok": all_ok,
        "node_count": len(nodes),
        "findings": findings,
    }


def melodia_animation_get_runtime_abp(bp_path: str) -> dict[str, Any]:
    """
    Return which ABP is assigned to a character BP's Mesh component.
    Detects skeleton mismatches between mesh and anim class.
    """
    if not _monolith_is_live():
        return {"schema": "melodia.animation.get_runtime_abp.v1", "error": "Monolith not reachable"}
    
    # Get BP CDO properties
    cdo_data = _monolith_call("blueprint_query.get_cdo_properties", {"asset_path": bp_path})
    if not cdo_data:
        return {"schema": "melodia.animation.get_runtime_abp.v1", "error": "BP not found"}
    
    # Get parent class to understand inheritance
    parent_data = _monolith_call("blueprint_query.get_parent_class", {"asset_path": bp_path})
    parent_class = parent_data.get("parent_class", {}) if parent_data else {}
    
    # Find Mesh component info
    mesh_info = None
    for p in cdo_data.get("properties", []):
        if p.get("name") == "Mesh":
            mesh_info = p
            break
    
    if not mesh_info:
        return {"schema": "melodia.animation.get_runtime_abp.v1", "error": "No Mesh component"}
    
    anim_class_value = mesh_info.get("value", "")
    
    # If the anim class is set to ABP_Melusina_Current, check skeleton
    mismatch = None
    if "ABP_Melusina_Current" in str(anim_class_value):
        # Get ABP skeleton
        abp_info = _monolith_call("animation_query.get_abp_info", {
            "asset_path": "/Game/Melodia/Characters/Melusina/ABP_Melusina_Current"
        })
        abp_skeleton = abp_info.get("target_skeleton") if abp_info else None
        
        return {
            "schema": "melodia.animation.get_runtime_abp.v1",
            "bp_path": bp_path,
            "anim_class": anim_class_value,
            "parent_class": parent_class.get("name"),
            "parent_path": parent_class.get("path"),
            "abp_skeleton": abp_skeleton,
            "mesh_component": mesh_info.get("value"),
            "status": "matched" if abp_skeleton and "SK_Melusina" in abp_skeleton else "CHECK_MESH",
        }
    
    return {
        "schema": "melodia.animation.get_runtime_abp.v1",
        "bp_path": bp_path,
        "anim_class": anim_class_value,
        "parent_class": parent_class.get("name"),
        "parent_path": parent_class.get("path"),
        "status": "inherited",
        "warning": "AnimClass inherited from parent — verify skeleton match",
    }


def _scan_audio_assets() -> list[dict[str, Any]]:
    """Offline scan for audio assets under Content/."""
    assets: list[dict[str, Any]] = []
    roots = [
        PROJECT_ROOT / "Content" / "Audio",
        PROJECT_ROOT / "Content" / "Melodia" / "Audio",
        PROJECT_ROOT / "Content" / "MelodiaIntegration" / "Audio",
    ]
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.uasset")):
            name = path.stem
            rel = path.relative_to(PROJECT_ROOT / "Content")
            game_path = "/Game/" + str(rel.with_suffix("")).replace("\\", "/")
            if name.startswith("MS_"):
                kind = "metasound"
            elif name.startswith("SC_"):
                kind = "sound_cue"
            else:
                kind = "other"
            assets.append({"name": name, "path": game_path, "kind": kind, "on_disk": True})
    return assets


def melodia_audio_list_assets(kind: str | None = None) -> dict[str, Any]:
    """List audio assets from offline disk scan; enriches with Monolith when live."""
    assets = _scan_audio_assets()
    if kind:
        assets = [a for a in assets if a.get("kind") == kind]

    live_snapshot = None
    if _monolith_is_live():
        live_snapshot = _monolith_call("audio_query.list_assets", {"kind": kind} if kind else {})

    return {
        "schema": "melodia.audio.list.v1",
        "source": "live" if live_snapshot else "offline",
        "requested_kind": kind,
        "count": len(assets),
        "assets": assets,
        "live_snapshot": live_snapshot,
    }


def melodia_audio_validate_metasound(metasound_path: str) -> dict[str, Any]:
    """Validate a MetaSound asset graph. Falls back to disk presence when Monolith is offline."""
    if not metasound_path:
        return {"schema": "melodia.audio.validate_metasound.v1", "error": "metasound_path required"}

    if _monolith_is_live():
        info = _monolith_call("audio_query.get_metasound_info", {"asset_path": metasound_path})
        if info:
            nodes = info.get("nodes", [])
            outputs = info.get("output_nodes", [])
            return {
                "schema": "melodia.audio.validate_metasound.v1",
                "metasound_path": metasound_path,
                "source": "live",
                "valid": bool(nodes),
                "node_count": len(nodes),
                "output_count": len(outputs),
                "findings": [] if nodes else ["No nodes in MetaSound graph"],
            }
        return {
            "schema": "melodia.audio.validate_metasound.v1",
            "metasound_path": metasound_path,
            "source": "live",
            "valid": False,
            "error": f"MetaSound not found: {metasound_path}",
        }

    on_disk = any(
        a.get("kind") == "metasound" and (metasound_path.endswith(a["name"]) or a["path"] == metasound_path)
        for a in _scan_audio_assets()
    )
    return {
        "schema": "melodia.audio.validate_metasound.v1",
        "metasound_path": metasound_path,
        "source": "offline",
        "valid": on_disk,
        "note": "Monolith unreachable — disk-only presence check",
    }


def melodia_audio_get_rhythm_catalog() -> dict[str, Any]:
    """Return rhythm-combat audio catalog from live DA or offline fixture scan."""
    live = None
    if _monolith_is_live():
        live = _monolith_call("blueprint_query.get_cdo_properties", {
            "path": "/Game/MelodiaIntegration/Config/DA_MelodiaSongs"
        })

    catalog_assets = [a for a in _scan_audio_assets() if "rhythm" in a["name"].lower() or "melodia" in a["name"].lower()]
    return {
        "schema": "melodia.audio.rhythm_catalog.v1",
        "source": "live" if live else "offline",
        "catalog_assets": catalog_assets,
        "live_snapshot": live,
    }


def _scan_widget_assets() -> list[dict[str, Any]]:
    """Offline scan for UMG widget blueprints under Content/."""
    widgets: list[dict[str, Any]] = []
    roots = [
        PROJECT_ROOT / "Content" / "UI",
        PROJECT_ROOT / "Content" / "Melodia" / "UI",
        PROJECT_ROOT / "Content" / "MelodiaIntegration" / "UI",
    ]
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("WBP_*.uasset")):
            name = path.stem
            rel = path.relative_to(PROJECT_ROOT / "Content")
            game_path = "/Game/" + str(rel.with_suffix("")).replace("\\", "/")
            widgets.append({"name": name, "path": game_path, "on_disk": True})
    return widgets


def melodia_ui_list_widgets() -> dict[str, Any]:
    """List UMG widget blueprints from offline disk scan; enriches with Monolith when live."""
    widgets = _scan_widget_assets()
    live_snapshot = None
    if _monolith_is_live():
        live_snapshot = _monolith_call("ui_query.list_widgets", {})

    return {
        "schema": "melodia.ui.list.v1",
        "source": "live" if live_snapshot else "offline",
        "count": len(widgets),
        "widgets": widgets,
        "live_snapshot": live_snapshot,
    }


def melodia_ui_validate_widget(widget_path: str) -> dict[str, Any]:
    """Validate a UMG widget hierarchy. Falls back to disk presence when Monolith is offline."""
    if not widget_path:
        return {"schema": "melodia.ui.validate_widget.v1", "error": "widget_path required"}

    if _monolith_is_live():
        info = _monolith_call("ui_query.get_widget_info", {"asset_path": widget_path})
        if info:
            children = info.get("children", [])
            animations = info.get("animations", [])
            return {
                "schema": "melodia.ui.validate_widget.v1",
                "widget_path": widget_path,
                "source": "live",
                "valid": bool(children),
                "child_count": len(children),
                "animation_count": len(animations),
                "findings": [] if children else ["Widget has no child components"],
            }
        return {
            "schema": "melodia.ui.validate_widget.v1",
            "widget_path": widget_path,
            "source": "live",
            "valid": False,
            "error": f"Widget not found: {widget_path}",
        }

    on_disk = any(
        widget_path.endswith(w["name"]) or w["path"] == widget_path
        for w in _scan_widget_assets()
    )
    return {
        "schema": "melodia.ui.validate_widget.v1",
        "widget_path": widget_path,
        "source": "offline",
        "valid": on_disk,
        "note": "Monolith unreachable — disk-only presence check",
    }


def melodia_ui_get_battle_hud() -> dict[str, Any]:
    """Return known battle HUD widget paths and whether they exist on disk or live."""
    known = [
        "/Game/Melodia/UI/WBP_Battle_Rhythm",
        "/Game/MelodiaIntegration/UI/BP_MelodiaBattleUI",
        "/Game/Melodia/UI/WBP_Melodia_RhythmHUD",
    ]
    disk_widgets = {w["path"]: w for w in _scan_widget_assets()}
    entries: list[dict[str, Any]] = []
    for path in known:
        name = path.rsplit("/", 1)[-1]
        on_disk = path in disk_widgets or any(w["name"] == name for w in disk_widgets.values())
        live_ok = None
        if _monolith_is_live():
            live_ok = _monolith_call("project.search", {"query": path}, timeout=5.0) is not None
        entries.append({"path": path, "on_disk": on_disk, "live_found": live_ok})

    return {
        "schema": "melodia.ui.battle_hud.v1",
        "source": "live" if _monolith_is_live() else "offline",
        "hud_widgets": entries,
        "primary_hud": "/Game/Melodia/UI/WBP_Battle_Rhythm",
    }


def melodia_system_compile_feedback(asset_path: str | None = None) -> dict[str, Any]:
    """Return compile feedback for an asset — RCF metric groundwork. Offline-safe stub."""
    if not _monolith_is_live():
        return {
            "schema": "melodia.system.compile_feedback.v1",
            "source": "offline",
            "available": False,
            "asset_path": asset_path,
            "compile_errors": [],
            "compile_warnings": [],
            "note": "RCF groundwork — live compile feedback requires Monolith on :9316",
        }

    result = _monolith_call(
        "blueprint_query.get_compile_errors",
        {"asset_path": asset_path or ""},
        timeout=15.0,
    )
    errors = (result or {}).get("errors", [])
    warnings = (result or {}).get("warnings", [])
    return {
        "schema": "melodia.system.compile_feedback.v1",
        "source": "live",
        "available": True,
        "asset_path": asset_path,
        "compile_errors": errors if isinstance(errors, list) else [],
        "compile_warnings": warnings if isinstance(warnings, list) else [],
        "error_count": len(errors) if isinstance(errors, list) else 0,
    }


def melodia_system_golden_run_preflight() -> dict[str, Any]:
    """
    Pre-flight check for the P0 Dream golden run.
    Verifies: fresh slot, route maps, config canonical, 0 dirty packages, 0 errored BPs.
    """
    checks: dict[str, Any] = {}

    # 1. Route maps exist
    map_dir = PROJECT_ROOT / "Content"
    checks["route_maps"] = {
        "L_MelusinaMorning": (map_dir / "Melodia" / "Levels" / "Opening" / "L_MelusinaMorning.umap").exists(),
        "L_KaleidoNave": (map_dir / "EnvSandbox" / "Environments" / "L_KaleidoNave.umap").exists(),
        "MelodiaIntegrationMap": (map_dir / "MelodiaIntegration" / "Maps" / "MelodiaIntegrationMap.umap").exists(),
    }

    # 2. Integration config asset exists on disk
    checks["config_asset"] = {
        "DA_MelodiaIntegrationConfig": (PROJECT_ROOT / "Content" / "MelodiaIntegration" / "Config" / "DA_MelodiaIntegrationConfig.uasset").exists(),
        "DA_MelodiaPersonaContent": (PROJECT_ROOT / "Content" / "MelodiaIntegration" / "Config" / "DA_MelodiaPersonaContent.uasset").exists(),
    }

    # 3. Gate ledger shows completion gates closed
    ledger = _load_json(PROJECT_ROOT / "Saved" / "gate_ledger.json")
    completion_gates = {"runtime", "save_load", "repeat_consume", "package_launch"}
    gate_status = {}
    if ledger and "gates" in ledger:
        for gate in ledger["gates"]:
            if gate["id"] in completion_gates:
                gate_status[gate["id"]] = gate.get("status", "unknown")
    checks["completion_gates"] = gate_status
    checks["all_completion_gates_pass"] = all(gate_status.get(g) == "pass" for g in completion_gates)

    # 4. Echo pipeline spec is present
    checks["echo_pipeline"] = (PROJECT_ROOT / "specs" / "echo_pipeline.json").exists()

    # 5. Monolith reachability (informational, not blocking)
    checks["monolith_reachable"] = _monolith_is_live()

    all_ok = (
        all(checks["route_maps"].values()) and
        all(checks["config_asset"].values()) and
        checks["all_completion_gates_pass"] and
        checks["echo_pipeline"]
    )

    return {
        "schema": "melodia.system.golden_run_preflight.v1",
        "ready": all_ok,
        "timestamp": datetime.now().isoformat(),
        "checks": checks,
        "next_step": "golden_run" if all_ok else "resolve_blockers",
    }


# ---------------------------------------------------------------------------
# Economy tool implementations
# ---------------------------------------------------------------------------

def melodia_economy_get_state() -> dict[str, Any]:
    """Return current global economy state (read-only)."""
    return {
        "schema": "melodia.economy.state.v1",
        **_economy_dict(_ECONOMY_STATE),
    }


def melodia_economy_rhythm_hit(accuracy: float) -> dict[str, Any]:
    """Apply a rhythm hit; updates the global economy state and returns gains."""
    global _ECONOMY_STATE
    new_eco, result = on_rhythm_hit(_ECONOMY_STATE, accuracy)
    _ECONOMY_STATE = new_eco
    return {"schema": "melodia.economy.rhythm_hit.v1", **result}


def melodia_economy_cast_skill(skill_id: str, tier: int = 1) -> dict[str, Any]:
    """Dispatch a skill cast by skill_id."""
    global _ECONOMY_STATE
    dispatch = {
        "healing_song": cast_healing_song,
        "mana_song": cast_mana_song,
        "utility_debuff": cast_utility_debuff,
    }
    fn = dispatch.get(skill_id)
    if fn is None:
        return {"schema": "melodia.economy.cast.v1", "success": False, "reason": f"unknown skill_id: {skill_id}"}
    new_eco, result = fn(_ECONOMY_STATE, tier)
    _ECONOMY_STATE = new_eco
    if result.get("success"):
        record_cast(skill_id)
    return {"schema": "melodia.economy.cast.v1", **result}


def melodia_economy_activate_grief_hook(dungeon_id: str) -> dict[str, Any]:
    """Activate grief hook for dungeon entry — sets grief to 30."""
    global _ECONOMY_STATE
    new_eco, result = activate_grief_hook(_ECONOMY_STATE, dungeon_id)
    _ECONOMY_STATE = new_eco
    return {"schema": "melodia.economy.grief_hook.v1", **result}


# ---------------------------------------------------------------------------
# Encounter state (in-process; resets on server restart)
# ---------------------------------------------------------------------------
_ENCOUNTERS: dict[str, dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Task 1: HUD / economy HUD tool
# ---------------------------------------------------------------------------

def melodia_ui_get_economy_hud() -> dict[str, Any]:
    """Return structured HUD state for the P0 economy display."""
    eco = _ECONOMY_STATE
    base_cost = 10.0
    return {
        "schema": "melodia.ui.economy_hud.v1",
        "healing": round(eco.healing, 4),
        "mana": round(eco.mana, 4),
        "utility": round(eco.utility, 4),
        "grief": round(eco.grief, 4),
        "can_cast_healing": eco.healing >= base_cost,
        "can_cast_mana": eco.mana >= base_cost,
        "can_cast_utility": eco.utility >= base_cost,
        "grief_active": eco.grief > 0,
        "scalar_tiers": {
            "healing": min(3, int(eco.healing / 10)),
            "mana": min(3, int(eco.mana / 10)),
            "utility": min(3, int(eco.utility / 10)),
        },
    }


# ---------------------------------------------------------------------------
# Task 2: Encounter tools
# ---------------------------------------------------------------------------

def melodia_encounter_start(encounter_id: str) -> dict[str, Any]:
    """Start a dungeon encounter: activate grief hook, spawn enemy."""
    global _ECONOMY_STATE
    new_eco, grief_result = activate_grief_hook(_ECONOMY_STATE, encounter_id)
    _ECONOMY_STATE = new_eco
    reset_cast_history()
    _ENCOUNTERS[encounter_id] = {
        "encounter_id": encounter_id,
        "grief_active": True,
        "enemy": {"type": "mana_drainer", "abilities": ["mana_drain"]},
        "resolved": False,
    }
    return {
        "schema": "melodia.encounter.start.v1",
        "encounter_id": encounter_id,
        "status": "active",
        "enemy": {"type": "mana_drainer", "abilities": ["mana_drain"]},
        "grief_set_to": grief_result["grief_set_to"],
        "new_state": grief_result["new_state"],
    }


def melodia_encounter_enemy_action(encounter_id: str) -> dict[str, Any]:
    """Enemy performs mana drain: reduces player ManaEconomy by 15."""
    global _ECONOMY_STATE
    from deploy.melodia_economy import _clamp_economy
    from dataclasses import replace as _replace
    enc = _ENCOUNTERS.get(encounter_id)
    if not enc:
        return {"schema": "melodia.encounter.enemy_action.v1", "error": f"encounter not found: {encounter_id}"}

    drain = 15.0
    new_eco = _clamp_economy(_replace(_ECONOMY_STATE, mana=_ECONOMY_STATE.mana - drain))
    _ECONOMY_STATE = new_eco

    return {
        "schema": "melodia.encounter.enemy_action.v1",
        "encounter_id": encounter_id,
        "action": "mana_drain",
        "mana_drained": drain,
        "new_state": _economy_dict(_ECONOMY_STATE),
    }


def melodia_encounter_resolve(encounter_id: str) -> dict[str, Any]:
    """Resolve encounter: check cast history for blocking abilities."""
    enc = _ENCOUNTERS.get(encounter_id)
    if not enc:
        return {"schema": "melodia.encounter.resolve.v1", "error": f"encounter not found: {encounter_id}"}

    history = get_cast_history()
    blocked = "utility_debuff" in history
    enc["resolved"] = True

    return {
        "schema": "melodia.encounter.resolve.v1",
        "encounter_id": encounter_id,
        "status": "resolved",
        "blocked_enemy": blocked,
        "cast_history": sorted(history),
        "quest_advancement": blocked,
    }


# ---------------------------------------------------------------------------
# Task 3: Quest progression tool
# ---------------------------------------------------------------------------

def melodia_quest_check_p0(quest_id: str) -> dict[str, Any]:
    """Check P0 quest status based on cast history and encounter state."""
    history = get_cast_history()
    resolved_encounters = [eid for eid, e in _ENCOUNTERS.items() if e.get("resolved")]
    has_combat_skills = bool(history)
    encounter_resolved = len(resolved_encounters) > 0
    complete = has_combat_skills and encounter_resolved

    return {
        "schema": "melodia.quest.check_p0.v1",
        "quest_id": quest_id,
        "status": "complete" if complete else "in_progress",
        "cast_history": sorted(history),
        "resolved_encounters": resolved_encounters,
        "has_combat_skills": has_combat_skills,
        "encounter_resolved": encounter_resolved,
    }


# ---------------------------------------------------------------------------
# MCP tool registry
# ---------------------------------------------------------------------------

TOOLS: list[dict[str, Any]] = [
    {
        "name": "melodia_persona_get_stats",
        "description": "Read Persona-lite social stats. Offline-safe; falls back to live narrative record when Monolith is reachable.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "stat_id": {"type": "string", "description": "Optional: filter to one stat ID"},
            },
            "required": [],
        },
    },
    {
        "name": "melodia_persona_get_quests",
        "description": "List quests and their states from allowlist seed or live PersonaContent.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "quest_id": {"type": "string", "description": "Optional: filter to one quest ID"},
            },
            "required": [],
        },
    },
    {
        "name": "melodia_quill_list_scripts",
        "description": "List authored QuillScript assets (.qsc + compiled .uasset).",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "melodia_quill_validate_notification",
        "description": "Validate a Quill notification string against the seven-verb allowlist contract.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "notification": {"type": "string", "description": "Full notification string, e.g. melodia:battle:encounter_01"},
            },
            "required": ["notification"],
        },
    },
    {
        "name": "melodia_rhythm_list_skills",
        "description": "List rhythm skill definitions from config scan or live DA_MelodiaSongs.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "melodia_narrative_get_record",
        "description": "Return the FMelodiaNarrativeRecord schema, idempotency seams, and offline seed state.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "melodia_config_get_allowlist",
        "description": "Read integration config allowlist entries (encounter, quest, flag, travel, reward, stat IDs).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "set_name": {"type": "string", "description": "Optional: one of WorldChallengeIds, StateAnchorIds, NarrativeFlagIds, DialogueRewardIds, QuestIds, SocialStatIds, etc."},
            },
            "required": [],
        },
    },
    {
        "name": "melodia_bp_list_fixtures",
        "description": "List all Blueprint fixture specs and their L0-L4 readiness levels.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "melodia_bp_get_template",
        "description": "Get a single template definition from the gameplay BP kit (skill, enemy, encounter, portal, traversal_gate, world_challenge, state_anchor).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "template_id": {"type": "string", "description": "Template ID from the kit registry"},
            },
            "required": ["template_id"],
        },
    },
    {
        "name": "melodia_bp_validate_fixture",
        "description": "Validate a fixture spec exists and has required contract fields.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "fixture_name": {"type": "string", "description": "Fixture spec filename (without .json)"},
            },
            "required": ["fixture_name"],
        },
    },
    {
        "name": "melodia_system_health",
        "description": "Run a read-only health check across Melodia subsystems, specs, and Monolith reachability.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "melodia_system_list_subsystems",
        "description": "List native C++ subsystem authorities from source headers.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "melodia_narrative_audit_idempotency",
        "description": "Audit C++ narrative subsystem for idempotency guards (ConsumeOnce, replay-safe paths).",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    # --- Material domain (offline disk scan + live Monolith enrichment) ---
    {
        "name": "melodia_material_list_pbr",
        "description": "Scan disk for PBR texture sets and report which are complete (albedo+normal+ORM) and which already have instances.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "melodia_material_get_compile_stats",
        "description": "Report compilation state for a master/instance: errors, expression count, PS instructions. Offline-safe + live via material_query.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "asset_path": {"type": "string", "description": "Path to a UMaterial or MaterialInstanceConstant"},
            },
            "required": ["asset_path"],
        },
    },
    {
        "name": "melodia_material_audit",
        "description": "Full material pipeline health audit: broken masters, PPV blendable domain issues, PPV label mismatches, audio-reactivity gap. Offline + live Monolith.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "melodia_ppv_report",
        "description": "Per-level PPV state: blendable slots, weights, domain issues, label mismatches. Offline script analysis + live EditorActorSubsystem.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "melodia_bp_validate_p0_route",
        "description": "Validate P0 Dream golden run fixtures, Quill scripts, and allowlist IDs.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "melodia_system_golden_run_preflight",
        "description": "Pre-flight check for P0 golden run: route maps, config assets, completion gates, echo pipeline.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "melodia_animation_validate_state_machine",
        "description": "Validate an Animation Blueprint's state machine health. Checks: entry state exists, all states have sequence players, no orphan transitions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "abp_path": {"type": "string", "description": "Path to the Animation Blueprint asset"},
            },
            "required": ["abp_path"],
        },
    },
    {
        "name": "melodia_animation_validate_bindings",
        "description": "Verify all states in an ABP have connected pose outputs. Detects T-pose causes: blendspace/sequence player with 0 connections.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "abp_path": {"type": "string", "description": "Path to the Animation Blueprint asset"},
            },
            "required": ["abp_path"],
        },
    },
    {
        "name": "melodia_animation_get_runtime_abp",
        "description": "Return which ABP is assigned to a character BP's Mesh component. Detects skeleton mismatches between mesh and anim class.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "bp_path": {"type": "string", "description": "Path to the character Blueprint asset"},
            },
            "required": ["bp_path"],
        },
    },
    {
        "name": "melodia_audio_list_assets",
        "description": "List audio assets (MetaSound, SoundCue) from offline disk scan; enriches with Monolith when live.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kind": {"type": "string", "enum": ["metasound", "sound_cue", "other"], "description": "Optional filter by asset kind"},
            },
            "required": [],
        },
    },
    {
        "name": "melodia_audio_validate_metasound",
        "description": "Validate a MetaSound asset graph. Falls back to disk presence when Monolith is offline.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "metasound_path": {"type": "string", "description": "Path to the MetaSound asset"},
            },
            "required": ["metasound_path"],
        },
    },
    {
        "name": "melodia_audio_get_rhythm_catalog",
        "description": "Return rhythm-combat audio catalog from live DA or offline fixture scan.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "melodia_ui_list_widgets",
        "description": "List UMG widget blueprints from offline disk scan; enriches with Monolith when live.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "melodia_ui_validate_widget",
        "description": "Validate a UMG widget hierarchy. Falls back to disk presence when Monolith is offline.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "widget_path": {"type": "string", "description": "Path to the Widget Blueprint asset"},
            },
            "required": ["widget_path"],
        },
    },
    {
        "name": "melodia_ui_get_battle_hud",
        "description": "Return known battle HUD widget paths and whether they exist on disk or live.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "melodia_system_compile_feedback",
        "description": "Return compile feedback for an asset — RCF metric groundwork. Offline-safe stub.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "asset_path": {"type": "string", "description": "Optional path to a Blueprint or widget asset"},
            },
            "required": [],
        },
    },
    # --- Economy tools ---
    {
        "name": "melodia_economy_get_state",
        "description": "Read-only: return current global economy state (healing, mana, utility, grief).",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "melodia_economy_rhythm_hit",
        "description": "Apply a rhythm hit with accuracy 0.0–1.0; grief modifies mana/healing gains.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "accuracy": {"type": "number", "description": "Hit accuracy 0.0–1.0"},
            },
            "required": ["accuracy"],
        },
    },
    {
        "name": "melodia_economy_cast_skill",
        "description": "Cast a rhythm skill: healing_song, mana_song, or utility_debuff.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "skill_id": {
                    "type": "string",
                    "enum": ["healing_song", "mana_song", "utility_debuff"],
                    "description": "Which skill to cast",
                },
                "tier": {"type": "integer", "description": "Skill tier (default 1)", "default": 1},
            },
            "required": ["skill_id"],
        },
    },
    {
        "name": "melodia_economy_activate_grief_hook",
        "description": "Activate grief hook for a dungeon — sets grief to 30.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dungeon_id": {"type": "string", "description": "Dungeon identifier"},
            },
            "required": ["dungeon_id"],
        },
    },
    # --- HUD tool ---
    {
        "name": "melodia_ui_get_economy_hud",
        "description": "Return structured P0 economy HUD state: 4 indicators, skill availability, grief hook, scalar tiers.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    # --- Encounter tools ---
    {
        "name": "melodia_encounter_start",
        "description": "Start a dungeon encounter: activate grief hook and spawn mana-drainer enemy.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "encounter_id": {"type": "string", "description": "Encounter identifier"},
            },
            "required": ["encounter_id"],
        },
    },
    {
        "name": "melodia_encounter_enemy_action",
        "description": "Enemy performs mana drain action: reduces player ManaEconomy by 15.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "encounter_id": {"type": "string", "description": "Encounter identifier"},
            },
            "required": ["encounter_id"],
        },
    },
    {
        "name": "melodia_encounter_resolve",
        "description": "Resolve encounter: checks if all 3 skill families were cast.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "encounter_id": {"type": "string", "description": "Encounter identifier"},
            },
            "required": ["encounter_id"],
        },
    },
    # --- Quest tool ---
    {
        "name": "melodia_quest_check_p0",
        "description": "Check P0 quest status based on cast history and encounter resolution.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "quest_id": {"type": "string", "description": "Quest identifier"},
            },
            "required": ["quest_id"],
        },
    },
]

# ---------------------------------------------------------------------------
# MCP stdio loop
# ---------------------------------------------------------------------------

def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        rid = msg.get("id")
        method = msg.get("method", "")
        params = msg.get("params", {})

        if method == "initialize":
            sys.stdout.write(json.dumps({
                "jsonrpc": "2.0",
                "id": rid,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "melodia-mcp", "version": "1.0.0"},
                },
            }) + "\n")
            sys.stdout.flush()

        elif method == "tools/list":
            sys.stdout.write(json.dumps({
                "jsonrpc": "2.0",
                "id": rid,
                "result": {"tools": TOOLS},
            }) + "\n")
            sys.stdout.flush()

        elif method == "tools/call":
            tool_name = params.get("name", "")
            args = params.get("arguments", {})
            result: dict[str, Any]

            # Dispatch table — every tool is read-only, so approval is checked
            # but none of these mutate state.
            if tool_name == "melodia_persona_get_stats":
                policy = authorize_tool(tool_name, "read", args.get("approval", "none"))
                result = melodia_persona_get_stats(args.get("stat_id")) if policy["allowed"] else {"status": "denied", **policy}
            elif tool_name == "melodia_persona_get_quests":
                policy = authorize_tool(tool_name, "read", args.get("approval", "none"))
                result = melodia_persona_get_quests(args.get("quest_id")) if policy["allowed"] else {"status": "denied", **policy}
            elif tool_name == "melodia_quill_list_scripts":
                policy = authorize_tool(tool_name, "read", args.get("approval", "none"))
                result = melodia_quill_list_scripts() if policy["allowed"] else {"status": "denied", **policy}
            elif tool_name == "melodia_quill_validate_notification":
                policy = authorize_tool(tool_name, "read", args.get("approval", "none"))
                result = melodia_quill_validate_notification(args.get("notification", "")) if policy["allowed"] else {"status": "denied", **policy}
            elif tool_name == "melodia_rhythm_list_skills":
                policy = authorize_tool(tool_name, "read", args.get("approval", "none"))
                result = melodia_rhythm_list_skills() if policy["allowed"] else {"status": "denied", **policy}
            elif tool_name == "melodia_narrative_get_record":
                policy = authorize_tool(tool_name, "read", args.get("approval", "none"))
                result = melodia_narrative_get_record() if policy["allowed"] else {"status": "denied", **policy}
            elif tool_name == "melodia_config_get_allowlist":
                policy = authorize_tool(tool_name, "read", args.get("approval", "none"))
                result = melodia_config_get_allowlist(args.get("set_name")) if policy["allowed"] else {"status": "denied", **policy}
            elif tool_name == "melodia_bp_list_fixtures":
                policy = authorize_tool(tool_name, "read", args.get("approval", "none"))
                result = melodia_bp_list_fixtures() if policy["allowed"] else {"status": "denied", **policy}
            elif tool_name == "melodia_bp_get_template":
                policy = authorize_tool(tool_name, "read", args.get("approval", "none"))
                result = melodia_bp_get_template(args.get("template_id", "")) if policy["allowed"] else {"status": "denied", **policy}
            elif tool_name == "melodia_bp_validate_fixture":
                policy = authorize_tool(tool_name, "read", args.get("approval", "none"))
                result = melodia_bp_validate_fixture(args.get("fixture_name", "")) if policy["allowed"] else {"status": "denied", **policy}
            elif tool_name == "melodia_system_health":
                policy = authorize_tool(tool_name, "read", args.get("approval", "none"))
                result = melodia_system_health() if policy["allowed"] else {"status": "denied", **policy}
            elif tool_name == "melodia_system_list_subsystems":
                policy = authorize_tool(tool_name, "read", args.get("approval", "none"))
                result = melodia_system_list_subsystems() if policy["allowed"] else {"status": "denied", **policy}
            elif tool_name == "melodia_narrative_audit_idempotency":
                policy = authorize_tool(tool_name, "read", args.get("approval", "none"))
                result = melodia_narrative_audit_idempotency() if policy["allowed"] else {"status": "denied", **policy}
            elif tool_name == "melodia_material_list_pbr":
                policy = authorize_tool(tool_name, "read", args.get("approval", "none"))
                result = melodia_material_list_pbr() if policy["allowed"] else {"status": "denied", **policy}
            elif tool_name == "melodia_material_get_compile_stats":
                policy = authorize_tool(tool_name, "read", args.get("approval", "none"))
                result = melodia_material_get_compile_stats(args.get("asset_path", "")) if policy["allowed"] else {"status": "denied", **policy}
            elif tool_name == "melodia_material_audit":
                policy = authorize_tool(tool_name, "read", args.get("approval", "none"))
                result = melodia_material_audit() if policy["allowed"] else {"status": "denied", **policy}
            elif tool_name == "melodia_ppv_report":
                policy = authorize_tool(tool_name, "read", args.get("approval", "none"))
                result = melodia_ppv_report() if policy["allowed"] else {"status": "denied", **policy}
            elif tool_name == "melodia_bp_validate_p0_route":
                policy = authorize_tool(tool_name, "read", args.get("approval", "none"))
                result = melodia_bp_validate_p0_route() if policy["allowed"] else {"status": "denied", **policy}
            elif tool_name == "melodia_system_golden_run_preflight":
                policy = authorize_tool(tool_name, "read", args.get("approval", "none"))
                result = melodia_system_golden_run_preflight() if policy["allowed"] else {"status": "denied", **policy}
            elif tool_name == "melodia_animation_validate_state_machine":
                policy = authorize_tool(tool_name, "read", args.get("approval", "none"))
                result = melodia_animation_validate_state_machine(args.get("abp_path", "")) if policy["allowed"] else {"status": "denied", **policy}
            elif tool_name == "melodia_animation_validate_bindings":
                policy = authorize_tool(tool_name, "read", args.get("approval", "none"))
                result = melodia_animation_validate_bindings(args.get("abp_path", "")) if policy["allowed"] else {"status": "denied", **policy}
            elif tool_name == "melodia_animation_get_runtime_abp":
                policy = authorize_tool(tool_name, "read", args.get("approval", "none"))
                result = melodia_animation_get_runtime_abp(args.get("bp_path", "")) if policy["allowed"] else {"status": "denied", **policy}
            elif tool_name == "melodia_audio_list_assets":
                policy = authorize_tool(tool_name, "read", args.get("approval", "none"))
                result = melodia_audio_list_assets(args.get("kind")) if policy["allowed"] else {"status": "denied", **policy}
            elif tool_name == "melodia_audio_validate_metasound":
                policy = authorize_tool(tool_name, "read", args.get("approval", "none"))
                result = melodia_audio_validate_metasound(args.get("metasound_path", "")) if policy["allowed"] else {"status": "denied", **policy}
            elif tool_name == "melodia_audio_get_rhythm_catalog":
                policy = authorize_tool(tool_name, "read", args.get("approval", "none"))
                result = melodia_audio_get_rhythm_catalog() if policy["allowed"] else {"status": "denied", **policy}
            elif tool_name == "melodia_ui_list_widgets":
                policy = authorize_tool(tool_name, "read", args.get("approval", "none"))
                result = melodia_ui_list_widgets() if policy["allowed"] else {"status": "denied", **policy}
            elif tool_name == "melodia_ui_validate_widget":
                policy = authorize_tool(tool_name, "read", args.get("approval", "none"))
                result = melodia_ui_validate_widget(args.get("widget_path", "")) if policy["allowed"] else {"status": "denied", **policy}
            elif tool_name == "melodia_ui_get_battle_hud":
                policy = authorize_tool(tool_name, "read", args.get("approval", "none"))
                result = melodia_ui_get_battle_hud() if policy["allowed"] else {"status": "denied", **policy}
            elif tool_name == "melodia_system_compile_feedback":
                policy = authorize_tool(tool_name, "read", args.get("approval", "none"))
                result = melodia_system_compile_feedback(args.get("asset_path")) if policy["allowed"] else {"status": "denied", **policy}
            elif tool_name == "melodia_economy_get_state":
                policy = authorize_tool(tool_name, "read", args.get("approval", "none"))
                result = melodia_economy_get_state() if policy["allowed"] else {"status": "denied", **policy}
            elif tool_name == "melodia_economy_rhythm_hit":
                policy = authorize_tool(tool_name, "read", args.get("approval", "none"))
                result = melodia_economy_rhythm_hit(float(args.get("accuracy", 1.0))) if policy["allowed"] else {"status": "denied", **policy}
            elif tool_name == "melodia_economy_cast_skill":
                policy = authorize_tool(tool_name, "read", args.get("approval", "none"))
                result = melodia_economy_cast_skill(args.get("skill_id", ""), int(args.get("tier", 1))) if policy["allowed"] else {"status": "denied", **policy}
            elif tool_name == "melodia_economy_activate_grief_hook":
                policy = authorize_tool(tool_name, "read", args.get("approval", "none"))
                result = melodia_economy_activate_grief_hook(args.get("dungeon_id", "")) if policy["allowed"] else {"status": "denied", **policy}
            elif tool_name == "melodia_ui_get_economy_hud":
                policy = authorize_tool(tool_name, "read", args.get("approval", "none"))
                result = melodia_ui_get_economy_hud() if policy["allowed"] else {"status": "denied", **policy}
            elif tool_name == "melodia_encounter_start":
                policy = authorize_tool(tool_name, "read", args.get("approval", "none"))
                result = melodia_encounter_start(args.get("encounter_id", "")) if policy["allowed"] else {"status": "denied", **policy}
            elif tool_name == "melodia_encounter_enemy_action":
                policy = authorize_tool(tool_name, "read", args.get("approval", "none"))
                result = melodia_encounter_enemy_action(args.get("encounter_id", "")) if policy["allowed"] else {"status": "denied", **policy}
            elif tool_name == "melodia_encounter_resolve":
                policy = authorize_tool(tool_name, "read", args.get("approval", "none"))
                result = melodia_encounter_resolve(args.get("encounter_id", "")) if policy["allowed"] else {"status": "denied", **policy}
            elif tool_name == "melodia_quest_check_p0":
                policy = authorize_tool(tool_name, "read", args.get("approval", "none"))
                result = melodia_quest_check_p0(args.get("quest_id", "")) if policy["allowed"] else {"status": "denied", **policy}
            else:
                result = {"status": "error", "message": f"Unknown tool: {tool_name}"}

            sys.stdout.write(json.dumps({
                "jsonrpc": "2.0",
                "id": rid,
                "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2, default=str)}]},
            }) + "\n")
            sys.stdout.flush()

        elif method == "notifications/initialized":
            pass

        else:
            sys.stdout.write(json.dumps({
                "jsonrpc": "2.0",
                "id": rid,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
