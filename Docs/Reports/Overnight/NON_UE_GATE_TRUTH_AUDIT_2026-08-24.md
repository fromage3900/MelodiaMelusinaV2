# Non-UE Gate Truth Audit — 2026-08-24

## Verdict

**HOLD.** The inventory reconciles at **121 files**, but the current offline shared contract run is **19/20** and GMM discovery is **FAIL** after running 268 tests. Unsafe candidates remain HOLD; no editor, network, build, or dependency install was used.

## What was actually run

- `python.exe -B Tools/run_contract_tests.py --json` — return 1; 19 pass, 1 fail; floor 20.
- `python.exe -B -m unittest discover -s Content/Python/gmm/tests -p test_*.py -v` — return 1; errors=6.
- Inventory results: PASS 19, FAIL/grouped FAIL 27, HOLD_UNSAFE 22, NOT_RUN 53.

Both commands ran in bounded subprocesses with `-B`. Tests were discovered with `pathlib` and `ast`; no test module was imported for inventory.

## Pytest coverage truth

From BS_GodFile, pyproject.toml limits pytest to Content/Python and deploy with test_*.py and *_test.py. It excludes Tools, Docs/T3D_Baseline, _TouchDesigner, plugin tests, and root-level tests. From the parent EnvironmentPortfolio directory, ../pytest.ini instead limits collection to wix/tests and tests, excluding BS_GodFile. No pytest collection was launched because this audit discovers by AST/text and the selected interpreter reports pytest unavailable during GMM discovery.

- `pyproject.toml:44` — `testpaths = ["Content/Python", "deploy"]`
- `pyproject.toml:45` — `python_files = ["test_*.py", "*_test.py"]`
- `../pytest.ini:2` — `testpaths = wix/tests tests`
- `../pytest.ini:3` — `pythonpath = wix/tests BS_GodFile/Plugins/UEBlueprintMCP/Python .`
- `../pytest.ini:4` — `norecursedirs = BS_GodFile/Plugins/UEBlueprintMCP/Python/venv _to_delete_* node_modules .agents my-site-clean`

## Shared runner failures

- `Tools/test_melodia_content_fixtures.py` — C:\EnvironmentPortfolio\BS_GodFile\specs\blueprints\fixtures\universal_melody_token.v1.json

## GMM discovery failures

- **environment** — pytest dependency is unavailable.
- **harness** — gmm package discovery does not expose VERSION.
- **harness** — gmm.core discovery does not expose GmmAudit.

## Weak oracle evidence

- `Content/Python/gmm/tests/test_save_manager.py:151` — **repeated_operation_without_state_comparison**: `sm2 = SaveManager(save_dir=self.tmp)`
- `Content/Python/gmm/tests/test_save_manager.py:152` — **repeated_operation_without_state_comparison**: `p2 = MelodiaPlayerState()`
- `Tools/MaterialMaker/test_material_maker_api.py:26` — **marker_only_success**: `print(f"[OK] Found potential Material Maker path: {path}")`
- `Tools/bedrock_model_test.py:31` — **marker_only_success**: `print(f"OK: {p}", file=sys.stderr, flush=True)`
- `Tools/run_contract_tests.py:42` — **marker_text_plus_returncode** for `Tools/test_t3d_request_contract.py`: `Suite("Tools/test_t3d_request_contract.py", re.compile(r"validated T3D request schema")),`
- `Tools/run_contract_tests.py:43` — **marker_text_plus_returncode** for `Tools/test_melodia_content_fixtures.py`: `Suite("Tools/test_melodia_content_fixtures.py", re.compile(r"validated \d+ Melodia fixture specs")),`
- `Tools/run_contract_tests.py:44` — **marker_text_plus_returncode** for `Tools/test_melodia_bp_readiness.py`: `Suite("Tools/test_melodia_bp_readiness.py", re.compile(r"validated Blueprint readiness inventory")),`
- `Tools/run_contract_tests.py:45` — **marker_text_plus_returncode** for `Tools/test_melodia_bp_materialization_preflight.py`: `Suite("Tools/test_melodia_bp_materialization_preflight.py", re.compile(r"validated materialization preflight")),`
- `Tools/run_contract_tests.py:46` — **marker_text_plus_returncode** for `Tools/test_melodia_skill_bridge_contract.py`: `Suite("Tools/test_melodia_skill_bridge_contract.py", re.compile(r"validated skill bridge contract")),`
- `Tools/run_contract_tests.py:47` — **marker_text_plus_returncode** for `Tools/test_melodia_native_adapter_contract.py`: `Suite("Tools/test_melodia_native_adapter_contract.py", re.compile(r"validated native adapter contract surfaces")),`
- `Tools/run_contract_tests.py:48` — **marker_text_plus_returncode** for `Tools/test_melodia_bp_registry_contract.py`: `Suite("Tools/test_melodia_bp_registry_contract.py", re.compile(r"validated BP registry/fixture parity")),`
- `Tools/run_contract_tests.py:49` — **marker_text_plus_returncode** for `Tools/test_melodia_blessing_burden_contract.py`: `Suite("Tools/test_melodia_blessing_burden_contract.py", re.compile(r"validated Blessing/Burden contract")),`
- `Tools/run_contract_tests.py:50` — **marker_text_plus_returncode** for `Tools/test_melodia_wardrobe_transaction_contract.py`: `Suite("Tools/test_melodia_wardrobe_transaction_contract.py", re.compile(r"validated Melodia wardrobe transaction contract")),`
- `Tools/run_contract_tests.py:51` — **marker_text_plus_returncode** for `Tools/test_melusina_skin_topology_contract.py`: `Suite("Tools/test_melusina_skin_topology_contract.py", re.compile(r"validated Melusina skin topology contract")),`
- `Tools/run_contract_tests.py:52` — **marker_text_plus_returncode** for `Tools/test_melodia_package_launch_contract.py`: `Suite("Tools/test_melodia_package_launch_contract.py", re.compile(r"validated Melusina package-launch montage contract")),`
- `Tools/run_contract_tests.py:53` — **marker_text_plus_returncode** for `Tools/test_mcp_policy.py`: `Suite("Tools/test_mcp_policy.py", re.compile(r"mcp-policy-tests:\s+\d+/\d+ passed")),`
- `Tools/run_contract_tests.py:54` — **marker_text_plus_returncode** for `Tools/test_mcp_registration.py`: `Suite("Tools/test_mcp_registration.py", re.compile(r"validated checked-in MCP registration policy")),`
- `Tools/run_contract_tests.py:55` — **uncaptured_test_count_marker** for `Tools/test_evidence_envelope.py`: `Suite("Tools/test_evidence_envelope.py", re.compile(r"Ran\s+\d+ tests.*\bOK\b", re.S)),`
- `Tools/run_contract_tests.py:56` — **uncaptured_test_count_marker** for `Tools/test_ollama_health.py`: `Suite("Tools/test_ollama_health.py", re.compile(r"Ran\s+\d+ tests.*\bOK\b", re.S)),`
- `Tools/run_contract_tests.py:58` — **marker_text_plus_returncode** for `Tools/test_melusina_anim_unit_guard.py`: `Suite("Tools/test_melusina_anim_unit_guard.py", re.compile(r'"ok"\s*:\s*true')),`
- `Tools/test_melodia_mcp.py:105` — **broad_or_assertion**: `assert "sets" in result or "entries" in result`
- `Tools/test_melodia_progression_contract.py:330` — **repeated_operation_without_state_comparison**: `replay = projection.complete_objective(objective_id)`
- `Tools/test_melodia_progression_contract.py:356` — **repeated_operation_without_state_comparison**: `replay = projection.complete_objective("objective.first_dream.face_echo", "complete")`
- `Tools/test_melodia_wardrobe_catalog_contract.py:128` — **broad_or_assertion**: `assert rarity in rarities or rarity.casefold() in deferred, (path, rarity)`
- `Tools/test_melody_slime_datatables_contract.py:44` — **broad_or_assertion**: `assert f" {field}" in header or f"\t{field}" in header, field`
- `Tools/test_p0_economy_mcp.py:36` — **echo_based_broad_or_assertion**: `assert "enemy_mana_drained" in cast or after.get("utility", 0) <= before.get("utility", 0) or cast.get("skill") == "utility_debuff"`
- `Tools/test_p0_economy_mcp.py:52` — **repeated_operation_without_state_comparison**: `r2 = server.melodia_encounter_resolve(eid)`
- `_TouchDesigner/grandmaster_melodia/scripts/test_create.py:10` — **marker_only_success**: `print('Test 1 OK (with name):', x)`
- `_TouchDesigner/grandmaster_melodia/scripts/test_create2.py:38` — **marker_only_success**: `print('  OK:', op_name)`
- `test_vrm_import.py:14` — **marker_only_success**: `print("OK VRM4U import module loaded successfully")`
- `Tools/test_melusina_skin_topology_contract.py` runtime output — **zero_test_success_output**.

## Fix queue (ownership, not fixes)

### Harness

- `gmm_unittest_discovery` — gmm package discovery does not expose VERSION
- `gmm_unittest_discovery` — gmm.core discovery does not expose GmmAudit

### Oracle

- `Content/Python/gmm/tests/test_save_manager.py:151` — repeated_operation_without_state_comparison
- `Content/Python/gmm/tests/test_save_manager.py:152` — repeated_operation_without_state_comparison
- `Tools/MaterialMaker/test_material_maker_api.py:26` — marker_only_success
- `Tools/bedrock_model_test.py:31` — marker_only_success
- `Tools/run_contract_tests.py:42 (Tools/test_t3d_request_contract.py)` — marker_text_plus_returncode
- `Tools/run_contract_tests.py:43 (Tools/test_melodia_content_fixtures.py)` — marker_text_plus_returncode
- `Tools/run_contract_tests.py:44 (Tools/test_melodia_bp_readiness.py)` — marker_text_plus_returncode
- `Tools/run_contract_tests.py:45 (Tools/test_melodia_bp_materialization_preflight.py)` — marker_text_plus_returncode
- `Tools/run_contract_tests.py:46 (Tools/test_melodia_skill_bridge_contract.py)` — marker_text_plus_returncode
- `Tools/run_contract_tests.py:47 (Tools/test_melodia_native_adapter_contract.py)` — marker_text_plus_returncode
- `Tools/run_contract_tests.py:48 (Tools/test_melodia_bp_registry_contract.py)` — marker_text_plus_returncode
- `Tools/run_contract_tests.py:49 (Tools/test_melodia_blessing_burden_contract.py)` — marker_text_plus_returncode
- `Tools/run_contract_tests.py:50 (Tools/test_melodia_wardrobe_transaction_contract.py)` — marker_text_plus_returncode
- `Tools/run_contract_tests.py:51 (Tools/test_melusina_skin_topology_contract.py)` — marker_text_plus_returncode
- `Tools/run_contract_tests.py:52 (Tools/test_melodia_package_launch_contract.py)` — marker_text_plus_returncode
- `Tools/run_contract_tests.py:53 (Tools/test_mcp_policy.py)` — marker_text_plus_returncode
- `Tools/run_contract_tests.py:54 (Tools/test_mcp_registration.py)` — marker_text_plus_returncode
- `Tools/run_contract_tests.py:55 (Tools/test_evidence_envelope.py)` — uncaptured_test_count_marker
- `Tools/run_contract_tests.py:56 (Tools/test_ollama_health.py)` — uncaptured_test_count_marker
- `Tools/run_contract_tests.py:58 (Tools/test_melusina_anim_unit_guard.py)` — marker_text_plus_returncode
- `Tools/test_melodia_mcp.py:105` — broad_or_assertion
- `Tools/test_melodia_progression_contract.py:330` — repeated_operation_without_state_comparison
- `Tools/test_melodia_progression_contract.py:356` — repeated_operation_without_state_comparison
- `Tools/test_melodia_wardrobe_catalog_contract.py:128` — broad_or_assertion
- `Tools/test_melody_slime_datatables_contract.py:44` — broad_or_assertion
- `Tools/test_melusina_skin_topology_contract.py` — zero_test_success_output
- `Tools/test_p0_economy_mcp.py:36` — echo_based_broad_or_assertion
- `Tools/test_p0_economy_mcp.py:52` — repeated_operation_without_state_comparison
- `_TouchDesigner/grandmaster_melodia/scripts/test_create.py:10` — marker_only_success
- `_TouchDesigner/grandmaster_melodia/scripts/test_create2.py:38` — marker_only_success
- `test_vrm_import.py:14` — marker_only_success

### Production

- `Tools/test_melodia_content_fixtures.py` — C:\EnvironmentPortfolio\BS_GodFile\specs\blueprints\fixtures\universal_melody_token.v1.json

### Environment

- `gmm_unittest_discovery` — pytest dependency is unavailable

## Acceptance reconciliation

- Discovered paths: 121
- Unique inventory entries: 121
- Reconciled: `true`
- Exclusions: installed environments/site-packages, `.claude` worktrees, generated `_stub_*` packages, build/Saved output, and `__init__.py` package markers.
- Runnable entries missing command/timeout/result: 0
- Unsafe HOLD entries launched: 0
- Unsafe execution policy: `HOLD_UNSAFE`

Machine-readable evidence: `specs/testing/non_ue_gate_inventory.v1.json` and `Saved/Audit/non_ue_gate_truth_20260824.json`.
