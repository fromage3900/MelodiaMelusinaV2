#!/usr/bin/env python3
"""
Test suite for the Melodia MCP server.

Run standalone (no pytest required):
    python Tools/test_melodia_mcp.py

Or via the contract runner:
    python Tools/run_contract_tests.py

This suite validates:
- Server can be imported and tool registry is consistent with the schema spec
- All tools return structured output matching their declared schema
- Offline operations work without Monolith or the editor
- Policy entries exist for every declared tool
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Tools.mcp_policy import load_policy

SPECS_ROOT = PROJECT_ROOT / "specs"
MCP_TOOLS_SPEC = SPECS_ROOT / "mcp" / "melodia_mcp_tools.v1.json"
MCP_POLICY = SPECS_ROOT / "mcp_tool_policy.v1.json"
SERVER_PATH = PROJECT_ROOT / "deploy" / "melodia_mcp_server.py"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_server_imports() -> None:
    """The server module must import without errors."""
    import deploy.melodia_mcp_server as server  # noqa: F401
    assert hasattr(server, "TOOLS")
    assert hasattr(server, "main")
    assert len(server.TOOLS) > 0


def test_tool_registry_matches_schema_spec() -> None:
    """Every tool in the server registry must be documented in the schema spec."""
    spec = _load_json(MCP_TOOLS_SPEC)
    import deploy.melodia_mcp_server as server

    registered_names = {t["name"] for t in server.TOOLS}
    spec_names = set(spec.get("tools", {}).keys())

    missing_in_spec = registered_names - spec_names
    missing_in_server = spec_names - registered_names

    assert not missing_in_spec, f"Tools missing in schema spec: {missing_in_spec}"
    assert not missing_in_server, f"Tools missing in server registry: {missing_in_server}"


def test_every_tool_has_policy_entry() -> None:
    """Every registered tool must have a policy entry."""
    policy = load_policy()
    import deploy.melodia_mcp_server as server

    registered_names = {t["name"] for t in server.TOOLS}
    policy_tools = set(policy.get("tools", {}).keys())

    missing = registered_names - policy_tools
    assert not missing, f"Tools missing in policy: {missing}"


def test_policy_default_is_deny() -> None:
    """The policy must default to deny for unlisted tools."""
    policy = load_policy()
    assert policy.get("default_decision") == "deny"


def test_melodia_tools_are_read_only() -> None:
    """No melodia tool in v1 should declare mutating operations."""
    spec = _load_json(MCP_TOOLS_SPEC)
    for name, entry in spec.get("tools", {}).items():
        if not name.startswith("melodia_"):
            continue
        assert entry.get("mutates") is False, f"{name} must not mutate in v1"
        assert entry.get("approval_required") == "none", f"{name} read-only approval should be none"


def test_offline_tools_run_without_monolith() -> None:
    """Core read-only tools must return valid output when Monolith is unreachable."""
    import deploy.melodia_mcp_server as server

    # These should all work offline
    result = server.melodia_quill_list_scripts()
    assert result["schema"] == "melodia.quill.scripts.v1"
    assert isinstance(result["scripts"], list)

    result = server.melodia_narrative_get_record()
    assert result["schema"] == "melodia.narrative.record.v1"
    assert "record" in result

    result = server.melodia_config_get_allowlist()
    assert result["schema"] == "melodia.config.allowlist.v1"
    assert "sets" in result or "entries" in result

    result = server.melodia_bp_list_fixtures()
    assert result["schema"] == "melodia.bp.fixtures.v1"
    assert isinstance(result["fixtures"], list)

    result = server.melodia_system_list_subsystems()
    assert result["schema"] == "melodia.system.subsystems.v1"
    assert isinstance(result["subsystems"], list)


def test_monolith_call_routes_bare_and_dotted_tools() -> None:
    """Dotted calls must target the namespace tool and nest action params."""
    import deploy.melodia_mcp_server as server

    captured: list[dict] = []

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self) -> bytes:
            envelope = {
                "result": {
                    "content": [{"type": "text", "text": '{"ok": true}'}],
                    "isError": False,
                }
            }
            return json.dumps(envelope).encode("utf-8")

    def fake_urlopen(request, timeout):
        del timeout
        captured.append(json.loads(request.data.decode("utf-8")))
        return FakeResponse()

    with patch.object(server.urllib.request, "urlopen", side_effect=fake_urlopen):
        assert server._monolith_call("monolith_status", {"verbose": True}) == {"ok": True}
        assert server._monolith_call(
            "animation_query.get_abp_info", {"asset_path": "/Game/Test/ABP_Test"}
        ) == {"ok": True}
        assert server._monolith_call(
            "blueprint_query.get_cdo_properties", {"asset_path": "/Game/Test/BP_Test"}
        ) == {"ok": True}
        assert server._monolith_call("project_query.search", {"query": "NPC"}) == {
            "ok": True
        }

    assert captured[0]["params"] == {
        "name": "monolith_status",
        "arguments": {"verbose": True},
    }
    assert captured[1]["params"] == {
        "name": "animation_query",
        "arguments": {
            "action": "get_abp_info",
            "params": {"asset_path": "/Game/Test/ABP_Test"},
        },
    }
    assert captured[2]["params"] == {
        "name": "blueprint_query",
        "arguments": {
            "action": "get_cdo_properties",
            "params": {"asset_path": "/Game/Test/BP_Test"},
        },
    }
    assert captured[3]["params"] == {
        "name": "project_query",
        "arguments": {"action": "search", "params": {"query": "NPC"}},
    }


def test_live_cdo_reads_use_canonical_asset_path_parameter() -> None:
    """Every live CDO reader must use Monolith's asset_path schema."""
    import deploy.melodia_mcp_server as server

    calls: list[tuple[str, dict]] = []

    def fake_monolith_call(method, args=None, timeout=10.0):
        del timeout
        calls.append((method, args or {}))
        return {"properties": []}

    with patch.object(server, "_monolith_is_live", return_value=True), patch.object(
        server, "_monolith_call", side_effect=fake_monolith_call
    ):
        assert server.melodia_persona_get_stats()["source"] == "live"
        assert server.melodia_persona_get_quests()["source"] == "live"
        assert server.melodia_rhythm_list_skills()["source"] == "live"
        assert server.melodia_audio_get_rhythm_catalog()["source"] == "live"

    assert calls == [
        (
            "blueprint_query.get_cdo_properties",
            {"asset_path": server.PERSONA_CONTENT_PATH},
        ),
        (
            "blueprint_query.get_cdo_properties",
            {"asset_path": server.PERSONA_CONTENT_PATH},
        ),
        (
            "blueprint_query.get_cdo_properties",
            {"asset_path": "/Game/MelodiaIntegration/Config/DA_MelodiaSongs"},
        ),
        (
            "blueprint_query.get_cdo_properties",
            {"asset_path": "/Game/MelodiaIntegration/Config/DA_MelodiaSongs"},
        ),
    ]


def test_monolith_call_rejects_failed_action_payloads() -> None:
    """A transport-successful action failure must not be treated as live data."""
    import deploy.melodia_mcp_server as server

    class FakeFailureResponse:
        def __init__(self, payload):
            self.payload = payload

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self) -> bytes:
            envelope = {
                "result": {
                    "content": [
                        {"type": "text", "text": json.dumps(self.payload)}
                    ],
                    "isError": False,
                }
            }
            return json.dumps(envelope).encode("utf-8")

    for payload in (
        {"success": False},
        {"ok": False},
        {"error": "invalid action parameters"},
        {"_error": "editor unavailable"},
    ):
        with patch.object(
            server.urllib.request,
            "urlopen",
            return_value=FakeFailureResponse(payload),
        ):
            assert server._monolith_call("project_query.search", {"query": "NPC"}) is None


def test_quill_notification_validation() -> None:
    """The notification validator must correctly classify valid and invalid verbs."""
    import deploy.melodia_mcp_server as server

    valid = server.melodia_quill_validate_notification("melodia:battle:encounter_01")
    assert valid["is_valid_verb"] is True
    assert valid["verb"] == "melodia:battle"

    invalid = server.melodia_quill_validate_notification("melodia:hack:encounter_01")
    assert invalid["is_valid_verb"] is False

    stat = server.melodia_quill_validate_notification("melodia:stat:intent_01:harmony:2")
    assert stat["is_valid_verb"] is True
    assert stat["verb"] == "melodia:stat"


def test_fixture_validation() -> None:
    """Fixture validation must find existing specs and reject unknown ones."""
    import deploy.melodia_mcp_server as server

    # A known fixture should validate
    result = server.melodia_bp_validate_fixture("first_resonance_world_challenge")
    assert result["schema"] == "melodia.bp.fixture_validate.v1"

    # An unknown fixture should fail gracefully
    result = server.melodia_bp_validate_fixture("nonexistent_fixture_xyz")
    assert result["valid"] is False
    assert "available_fixtures" in result


def _mcp_config_path() -> Path:
    for candidate in (PROJECT_ROOT / ".mcp.json", PROJECT_ROOT.parent / ".mcp.json"):
        if candidate.is_file():
            return candidate
    return PROJECT_ROOT / ".mcp.json"


def test_server_registered_in_mcp_config() -> None:
    """The melodia server must be registered in .mcp.json."""
    mcp_config = _load_json(_mcp_config_path())
    servers = mcp_config.get("mcpServers", {})
    assert "melodia" in servers, "melodia server not registered in .mcp.json"
    melodia = servers["melodia"]
    assert "melodia_mcp_server.py" in melodia.get("args", [])[0]


def test_bp_template_lookup() -> None:
    """Template lookup must return the correct template or a clear error."""
    import deploy.melodia_mcp_server as server

    result = server.melodia_bp_get_template("world_challenge")
    assert result["schema"] == "melodia.bp.template.v1"
    assert "template" in result

    result = server.melodia_bp_get_template("nonexistent")
    assert result["schema"] == "melodia.bp.template.v1"
    assert "error" in result




def test_narrative_idempotency_audit() -> None:
    """The idempotency audit must return findings for all guarded paths."""
    import deploy.melodia_mcp_server as server
    result = server.melodia_narrative_audit_idempotency()
    assert result["schema"] == "melodia.narrative.idempotency_audit.v1"
    assert "findings" in result
    assert isinstance(result["findings"], list)
    assert "all_paths_guarded" in result
    assert "item_is_logging_stub" in result


def test_p0_route_validation() -> None:
    """P0 route validation must check fixtures, scripts, and allowlist IDs."""
    import deploy.melodia_mcp_server as server
    result = server.melodia_bp_validate_p0_route()
    assert result["schema"] == "melodia.bp.p0_route.v1"
    assert "fixtures" in result
    assert "scripts" in result
    assert "allowlist_ids" in result
    assert isinstance(result["fixtures"], list)
    assert len(result["fixtures"]) == 5


def test_golden_run_preflight() -> None:
    """Pre-flight must return a ready flag and checks dict."""
    import deploy.melodia_mcp_server as server
    result = server.melodia_system_golden_run_preflight()
    assert result["schema"] == "melodia.system.golden_run_preflight.v1"
    assert "ready" in result
    assert "checks" in result
    assert "next_step" in result
    assert result["next_step"] in ("golden_run", "resolve_blockers")


def test_resonant_world_tools_are_offline_safe() -> None:
    """Resonant World atlas, compiler, handoff, and validation calls are read-only."""
    import deploy.melodia_mcp_server as server

    atlas = server.melodia_resonant_world_get_atlas()
    assert atlas["schema"] == "melodia.resonant_world.atlas.v1"
    assert atlas["ok"] is True
    assert "petal_cantata" in atlas["movement_ids"]

    passage = server.melodia_resonant_world_compile_passage(
        3900, "petal_cantata", "SakuraDreamer"
    )
    assert passage["schema"] == "melodia.resonant_world.passage.v1"
    assert passage["ok"] is True
    assert passage["passage_count"] == 1
    assert passage["passages"][0]["collection_affordance"]["currency_id"] == "Radiant"
    assert passage["materialization"]["writes_project_state"] is False

    handoff = server.melodia_resonant_world_get_handoff("all")
    assert handoff["schema"] == "melodia.resonant_world.handoff.v1"
    assert handoff["ok"] is True
    assert handoff["proof_artifact"]["editor_apply_performed"] is False

    offline_bundle = server.melodia_resonant_world_get_offline_bundle()
    assert offline_bundle["schema"] == "melodia.resonant_world.offline_bundle.v1"
    assert offline_bundle["ok"] is True
    assert offline_bundle["world"]["score_count"] == 6
    assert offline_bundle["ue_import_plan"]["apply"]["performed"] is False
    assert offline_bundle["materialization"]["writes_project_state"] is False

    validation = server.melodia_resonant_world_validate()
    assert validation["schema"] == "melodia.resonant_world.validate.v1"
    assert validation["ok"] is True
    assert validation["materialization"]["writes_project_state"] is False


def test_resonant_world_constellation_is_offline_safe() -> None:
    """Asset constellation binds existing files while preserving runtime boundaries."""
    import deploy.melodia_mcp_server as server

    result = server.melodia_resonant_world_get_constellation(
        3900, "petal_cantata", 0, 0, "SakuraDreamer"
    )
    assert result["schema"] == "melodia.resonant_world.constellation.v1"
    assert result["ok"] is True
    assert result["coverage"]["required_role_coverage"] == 1.0
    assert result["quantum_setup"]["candidate_movements"]
    assert len(result["quantum_setup"]["candidate_movements"]) == 2
    assert result["quantum_setup"]["quantum_is_selector_not_generator"] is True
    assert result["magical_moment"]["style_layer"]["appearance_is_separate_from_capability"] is True
    assert result["verification"]["echo"]["authority"] == "ledger_only"
    assert result["verification"]["pie"]["read_model_is_not_pie_proof"] is True
    assert result["runtime_boundary"]["does_not_apply_traversal"] is True
    assert result["materialization"]["writes_project_state"] is False


def test_resonant_world_score_is_offline_safe() -> None:
    """Score composition exposes a replayable phrase without runtime mutation."""
    import deploy.melodia_mcp_server as server

    result = server.melodia_resonant_world_get_score(
        3900, "petal_cantata", 0, 0, "SakuraDreamer"
    )
    assert result["schema"] == "melodia.resonant_world.score.v1"
    assert result["ok"] is True
    assert result["score_id"]
    assert result["motif"]["grammar_id"] == "petal_fan"
    assert len(result["events"]) == 16
    assert len(result["stages"]) == 4
    assert result["events"][0]["phase"] == "call"
    assert result["events"][8]["phase"] == "response"
    assert len(result["quantum_setup"]["candidate_movements"]) == 2
    assert result["runtime_boundary"]["does_not_apply_traversal"] is True
    assert result["materialization"]["writes_project_state"] is False


def test_resonant_world_chronicle_is_read_only_and_replayable() -> None:
    """Chronicle projection preserves memory while leaving save authority elsewhere."""
    import deploy.melodia_mcp_server as server

    result = server.melodia_resonant_world_project_chronicle(
        3900,
        "petal_cantata",
        0,
        0,
        [
            {"sequence": 0, "event_type": "discovery", "chunk": [0, 0], "payload": {"movement_id": "star_loom"}},
            {"sequence": 1, "event_type": "movement_attuned", "chunk": [1, 0], "payload": {"movement_id": "star_loom"}},
            {"sequence": 2, "event_type": "voxel_edit", "chunk": [0, 0], "payload": {"cell": [1, 2, 3], "material_id": "note_block", "pitch_class": 4, "timbre": "harp"}},
            {"sequence": 3, "event_type": "voxel_remove", "chunk": [0, 0], "payload": {"cell": [1, 2, 3]}},
        ],
    )
    assert result["schema"] == "melodia.resonant_world.chronicle.v1"
    assert result["ok"] is True
    assert result["chronicle_id"]
    assert result["projection"]["attuned_movement_id"] == "star_loom"
    assert result["projection"]["voxel_edits"][0]["material_id"] == "air"
    assert result["persistence"]["writes_save"] is False
    assert result["runtime_boundary"]["does_not_apply_unreal"] is True
    assert result["materialization"]["writes_project_state"] is False


def test_resonant_world_capture_manifest_is_evidence_gated() -> None:
    """Capture contracts expose real evidence without promoting debug frames."""
    import deploy.melodia_mcp_server as server

    result = server.melodia_resonant_world_get_capture_manifest(3900, "all", 0, 0)
    assert result["schema"] == "melodia.resonant_world.capture_manifest.v1"
    assert result["ok"] is True
    assert len(result["targets"]) == 4
    assert result["verification"]["clean_approved_count"] == 0
    assert result["verification"]["clean_capture_pending_count"] == 4
    assert result["render_map_contract"]["namespace"] == "/Game/_PROJECT/Levels/RenderTests/"
    assert result["runtime_boundary"]["does_not_touch_gameplay_maps"] is True
    assert result["runtime_boundary"]["does_not_publish_webfront"] is True
    assert result["materialization"]["writes_project_state"] is False
    sakura = next(item for item in result["targets"] if item["target_id"] == "niagara_sakura_ambience")
    assert sakura["status"] == "observed_candidates_not_publishable"
    raw = next(
        item for item in sakura["observed_candidates"]
        if item["filename"] == "L_Render_SakuraDream_beauty_raw.png"
    )
    assert raw["verdict"] == "rejected_runtime_evidence"
    assert "black/checker" in raw["note"]


def test_animation_validate_state_machine_schema() -> None:
    """Animation state machine validation must declare correct schema."""
    import deploy.melodia_mcp_server as server
    # Test with a known ABP path (will fail without Monolith, but schema should be correct)
    result = server.melodia_animation_validate_state_machine(
        "/Game/Melodia/Characters/Melusina/ABP_Melusina_Current"
    )
    assert "schema" in result
    assert "melodia.animation.validate_sm" in result["schema"]


def test_animation_validate_bindings_schema() -> None:
    """Animation binding validation must declare correct schema."""
    import deploy.melodia_mcp_server as server
    result = server.melodia_animation_validate_bindings(
        "/Game/Melodia/Characters/Melusina/ABP_Melusina_Current"
    )
    assert "schema" in result
    assert "melodia.animation.validate_bindings" in result["schema"]


def test_animation_get_runtime_abp_schema() -> None:
    """Runtime ABP query must declare correct schema."""
    import deploy.melodia_mcp_server as server
    result = server.melodia_animation_get_runtime_abp(
        "/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter"
    )
    assert "schema" in result
    assert "melodia.animation.get_runtime_abp" in result["schema"]


def test_audio_list_assets_schema() -> None:
    """Audio list must declare correct schema and work offline."""
    import deploy.melodia_mcp_server as server
    result = server.melodia_audio_list_assets()
    assert result["schema"] == "melodia.audio.list.v1"
    assert isinstance(result["assets"], list)


def test_audio_validate_metasound_schema() -> None:
    """MetaSound validation must declare correct schema."""
    import deploy.melodia_mcp_server as server
    result = server.melodia_audio_validate_metasound("/Game/Audio/MetaSounds/MS_Melodia_HarmonicSynth")
    assert result["schema"] == "melodia.audio.validate_metasound.v1"
    assert "valid" in result


def test_ui_list_widgets_schema() -> None:
    """UI widget list must declare correct schema and work offline."""
    import deploy.melodia_mcp_server as server
    result = server.melodia_ui_list_widgets()
    assert result["schema"] == "melodia.ui.list.v1"
    assert isinstance(result["widgets"], list)


def test_ui_get_battle_hud_schema() -> None:
    """Battle HUD query must declare correct schema."""
    import deploy.melodia_mcp_server as server
    result = server.melodia_ui_get_battle_hud()
    assert result["schema"] == "melodia.ui.battle_hud.v1"
    assert "hud_widgets" in result
    assert "primary_hud" in result


def test_compile_feedback_schema() -> None:
    """Compile feedback must declare correct schema and work offline."""
    import deploy.melodia_mcp_server as server
    result = server.melodia_system_compile_feedback()
    assert result["schema"] == "melodia.system.compile_feedback.v1"
    assert "available" in result


def test_economy_hud_schema() -> None:
    """Economy HUD must return flat economy keys, castability flags, grief_active, and scalar tiers."""
    import deploy.melodia_mcp_server as server
    result = server.melodia_ui_get_economy_hud()
    assert result["schema"] == "melodia.ui.economy_hud.v1"
    for key in ("healing", "mana", "utility", "grief"):
        assert key in result
    for key in ("can_cast_healing", "can_cast_mana", "can_cast_utility", "grief_active"):
        assert key in result
    assert "scalar_tiers" in result
    for key in ("healing", "mana", "utility"):
        assert key in result["scalar_tiers"]


def test_encounter_start_schema() -> None:
    """Encounter start must activate grief and return enemy data."""
    import deploy.melodia_mcp_server as server
    result = server.melodia_encounter_start("test_enc")
    assert result["schema"] == "melodia.encounter.start.v1"
    assert result["status"] == "active"
    assert result["enemy"]["type"] == "mana_drainer"
    assert "mana_drain" in result["enemy"]["abilities"]
    assert result["grief_set_to"] == 30.0


def test_encounter_enemy_action_schema() -> None:
    """Enemy action must drain mana and return economy state."""
    import deploy.melodia_mcp_server as server
    server.melodia_encounter_start("test_drain_enc")
    result = server.melodia_encounter_enemy_action("test_drain_enc")
    assert result["schema"] == "melodia.encounter.enemy_action.v1"
    assert result["mana_drained"] == 15.0
    assert "new_state" in result


def test_encounter_resolve_schema() -> None:
    """Encounter resolve must check cast history and return resolved status."""
    import deploy.melodia_mcp_server as server
    server.melodia_encounter_start("test_resolve_enc")
    result = server.melodia_encounter_resolve("test_resolve_enc")
    assert result["schema"] == "melodia.encounter.resolve.v1"
    assert result["status"] == "resolved"
    assert "blocked_enemy" in result
    assert "cast_history" in result
    assert "quest_advancement" in result


def test_quest_check_p0_schema() -> None:
    """Quest check must return status and cast history."""
    import deploy.melodia_mcp_server as server
    result = server.melodia_quest_check_p0("p0_vertical_slice")
    assert result["schema"] == "melodia.quest.check_p0.v1"
    assert result["quest_id"] == "p0_vertical_slice"
    assert result["status"] in ("complete", "in_progress")
    for key in ("cast_history", "resolved_encounters", "has_combat_skills", "encounter_resolved"):
        assert key in result


def test_economy_rhythm_and_cast_mcp() -> None:
    """Rhythm hits bank resources, then three P0 songs succeed via MCP handlers."""
    import deploy.melodia_mcp_server as server
    from deploy.melodia_economy import MelodiaGlobalEconomy

    server._ECONOMY_STATE = MelodiaGlobalEconomy()
    hook = server.melodia_economy_activate_grief_hook("p0_dungeon_mcp_test")
    assert hook.get("success", True) is not False
    for _ in range(40):
        hit = server.melodia_economy_rhythm_hit(0.95)
        assert hit["schema"] == "melodia.economy.rhythm_hit.v1"
    for skill in ("healing_song", "mana_song", "utility_debuff"):
        cast = server.melodia_economy_cast_skill(skill, 1)
        assert cast["schema"] == "melodia.economy.cast.v1"
        assert cast.get("success") is True, cast


def test_p0_vertical_slice_mcp_chain() -> None:
    """Full P0 MCP chain: encounter start -> bank -> casts -> enemy -> resolve -> quest."""
    import deploy.melodia_mcp_server as server
    from deploy.melodia_economy import MelodiaGlobalEconomy

    enc_id = "p0_chain_test"
    server._ECONOMY_STATE = MelodiaGlobalEconomy()
    start = server.melodia_encounter_start(enc_id)
    assert start["schema"] == "melodia.encounter.start.v1"
    for _ in range(40):
        assert "error" not in server.melodia_economy_rhythm_hit(0.9)
    for skill in ("healing_song", "mana_song", "utility_debuff"):
        assert server.melodia_economy_cast_skill(skill, 1).get("success") is True
    drain = server.melodia_encounter_enemy_action(enc_id)
    assert drain["schema"] == "melodia.encounter.enemy_action.v1"
    resolved = server.melodia_encounter_resolve(enc_id)
    assert resolved["schema"] == "melodia.encounter.resolve.v1"
    assert resolved.get("blocked_enemy") is True
    quest = server.melodia_quest_check_p0("p0_vertical_slice")
    assert quest["schema"] == "melodia.quest.check_p0.v1"
    assert "healing_song" in quest.get("cast_history", [])
    assert quest.get("has_combat_skills") is True
    assert quest.get("encounter_resolved") is True


def run_all() -> int:
    """Run every test and report results."""
    tests = [
        test_server_imports,
        test_tool_registry_matches_schema_spec,
        test_every_tool_has_policy_entry,
        test_policy_default_is_deny,
        test_melodia_tools_are_read_only,
        test_offline_tools_run_without_monolith,
        test_monolith_call_routes_bare_and_dotted_tools,
        test_live_cdo_reads_use_canonical_asset_path_parameter,
        test_monolith_call_rejects_failed_action_payloads,
        test_quill_notification_validation,
        test_fixture_validation,
        test_server_registered_in_mcp_config,
        test_bp_template_lookup,
        test_narrative_idempotency_audit,
        test_p0_route_validation,
        test_golden_run_preflight,
        test_resonant_world_tools_are_offline_safe,
        test_resonant_world_constellation_is_offline_safe,
        test_resonant_world_score_is_offline_safe,
        test_resonant_world_chronicle_is_read_only_and_replayable,
        test_resonant_world_capture_manifest_is_evidence_gated,
        test_animation_validate_state_machine_schema,
        test_animation_validate_bindings_schema,
        test_animation_get_runtime_abp_schema,
        test_audio_list_assets_schema,
        test_audio_validate_metasound_schema,
        test_ui_list_widgets_schema,
        test_ui_get_battle_hud_schema,
        test_compile_feedback_schema,
        test_economy_hud_schema,
        test_encounter_start_schema,
        test_encounter_enemy_action_schema,
        test_encounter_resolve_schema,
        test_quest_check_p0_schema,
        test_economy_rhythm_and_cast_mcp,
        test_p0_vertical_slice_mcp_chain,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS  {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL  {test.__name__}: {e}")
            failed += 1

    print(f"\n{passed}/{len(tests)} passed, {failed}/{len(tests)} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(run_all())
