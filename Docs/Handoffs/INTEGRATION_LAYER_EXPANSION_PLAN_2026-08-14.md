# Melodia integration-layer expansion plan — 2026-08-14

This is the execution handoff for the repository, Unreal/T3D, Ollama, AWS, and
JCODE/MCP integration surfaces. It is intentionally evidence-led: an open or
held gate stays open or held until the required owner/session proof exists.

## Current truth

- Repository: `feature/repo-lockin-20260813`, HEAD observed at this refresh as
  `1c417c2991e471e3a49cf29aeec8d7ca194323a9`; the checkout is user-owned and
  continues to change during editor work.
- The worktree is materially dirty, including user-owned Unreal assets and editor
  state. No reset, clean, bulk asset rewrite, or force-push is authorized by this plan.
- Runtime is owner-verified PASS from 2026-08-13.
- `save_load` is now PASS in `Saved/Echo/state.txt`. The proof uses the correct
  `/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap`, `BP_SavePoint_2`, a full
  editor-process restart, and the canonical `HandleContinueClicked` load route.
  Evidence: `Saved/Integration/evidence/save_load_2026-08-14_restart_pass.json`.
- `repeat_consume` is now PASS: live Priestess Quill execution, a pre-notify
  canonical save checkpoint, `ResumeScript`, and a second restore/replay left
  `melodia_harmony=1` and each consumed intent exactly once. Evidence:
  `Saved/Integration/evidence/repeat_consume_2026-08-14_live_resume_pass.json`.
- `package_build` and `package_launch` are now PASS. The fresh Development
  archive mounted the IoStore package, loaded the real Melodia main menu, and
  passed the outside-editor Gauntlet Project run. Evidence:
  `Saved/Integration/evidence/package_build_2026-08-14_pass.json` and
  `Saved/Integration/evidence/package_launch_2026-08-14_pass.json`.
- The live static chain recorded FAIL on 2026-08-14 because two material baselines
  drifted; graph reachability, live Blueprint path, Blueprint sweep, and UI lint passed.
- A historical live `t3d_safe_wire` probe committed, compiled, saved, asserted, and
  re-exported successfully. Its manifest is under `Saved/T3D/`, but it predates the
  request-derived postcondition repair and has no `steps.postcondition` record. It
  therefore cannot close the current T3D gate; the `inject` and `blueprint_compile`
  ledger rows must be re-recorded from a fresh probe using the repaired code and the
  explicit `nodes`/`expected_postconditions` in `specs/t3d/live_probe_print.json`.
- Ollama health is PASS for `hermes3:latest`, `deepseek-r1:14b`, and
  `qwen2.5-coder:7b`; the health script and fleet preflight are now part of the
  contract gate.
- BuildGraph XML parses and UE 5.8 `RunUAT BuildGraph -ListOnly` succeeds. The
  real `ValidateContracts`, isolated `CookPackage`, isolated `Gauntlet`, and
  local `ManifestOnly` targets pass. The local Horde `CreateArtifact` node is
  opt-in and remains unrun without `UE_HORDE_STREAMID`; the GitHub artifact lane
  is the supported non-Horde publication path. Evidence is
  `Saved/Integration/evidence/buildgraph_pipeline_2026-08-14_pass.json`.
- The `ValidateContracts` node now also runs `test_melodia_content_fixtures.py` and
  `test_melodia_bp_readiness.py`, plus `test_t3d_request_contract.py`, so the gameplay
  BP registry, L0/L1 inventory, and explicit T3D request schema are part of the same
  contract gate. The graph XML parsed and all six constituent
  scripts passed directly in this session; a fresh full RunUAT/BuildGraph invocation
  remains deferred until the existing editor/UAT ownership is resolved.
- `Tools/run_contract_tests.py` closes the prior CI collection gap: it explicitly
  invokes 16 offline assertion suites, requires a non-empty success marker from each,
  and fails if the fixed coverage floor drops. It is wired into both `echo_gates.yml`
  and `BuildGraph/MelodiaBuildGraph.xml`; the local run is 17/17, including the
  explicit Skill bridge, native-adapter, and registry/fixture parity checks.
- AWS publication is HOLD by design: the publisher is plan-only by default, the
  local machine has no AWS CLI/credentials, and no remote write occurred. The
  workflow now skips OIDC for plan-only runs and requires an explicit role only
  for confirmed publication.
- The worktree remains materially dirty with user-owned Unreal assets and
  generated integration changes. Do not reset, clean, or bulk-rewrite it. The
  earlier save/load, repeat-consume, and package holds remain historical context
  only; the current ledger is four completion gates PASS.

## Execution order

### 1. Owner/editor closeout lane — one editor, one writer

Run the documented procedures in `Docs/ECHO/campaign_02_save_round_trip.md` and
`Docs/ECHO/campaign_03_package_launch.md` with the current owner/editor session.

1. Save/load: completed. The save was written from
   `/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap`; after a full editor
   restart, `HandleContinueClicked` loaded that map through the GameInstance
   transaction with no fatal, assertion, or load-refusal markers.
2. Repeat-consume: completed. The live checkpoint/resume sequence observed the
   authored stat and quest intents once and preserved that result on replay.
3. Package: completed. The fresh archive launched outside the editor and passed
   the editor and walk Morning → KaleidoNave → Quill dialogue → battle start.
4. Record only observed passes through `Tools/echo_run.py record ... pass`; attach
   The packaged Gauntlet Project test passed; the current package evidence is not
   the stale staged executable.
   the save path, restart boundary, authored beat/IntentId, packaged build path,
   and screenshots/logs to evidence envelopes.

The owner decision is now limited to whether to supply AWS/Horde credentials and
whether to approve the two material baseline drifts. Do not treat static drift as
clean until those two graphs receive owner review.

### 2. Static baseline repair lane

Investigate the two material drifts before changing baselines:

- `M_Master_Simple_Universal`: 32,305 → 33,784 bytes; 25 → 26 nodes.
- `M_Master_Toon_Landscape_HeightBlend`: 427,468 → 450,364 bytes; 290 → 304 nodes.

Use exported graphs and owner intent to decide whether each is an authored change or
regression. Update a baseline only after a clean graph diff and explicit review; do
not “fix” the gate by accepting unknown drift.

### 3. Reproducible build lane

Use `BuildGraph/MelodiaBuildGraph.xml` through
`deploy/BuildGraph/Invoke-MelodiaBuildGraph.ps1`:

`ValidateContracts → CookPackage → Gauntlet → PublishArtifact`

The graph emits `melodia_artifact_manifest.json` with SHA-256 file hashes. The
outer runner uses `-NoMutex` and isolates nested UAT stdout/stderr so BuildGraph
does not saturate its event parser. `ValidateContracts`, isolated `CookPackage`,
isolated `Gauntlet`, and local `ManifestOnly` pass. Horde `CreateArtifact` is
opt-in and requires `UE_HORDE_STREAMID`; the non-Horde manifest/archive path is
the supported local and GitHub artifact boundary. The previous cook failure is
boundary: no stage, pak, archive, Gauntlet, or publish claim may be emitted. Epic’s
BuildGraph model is deliberately followed here: XML nodes express dependencies and
outputs, while `RunUnreal`/Gauntlet owns packaged runtime validation.

Current status correction: the historical cook-failure sentence above is retained
for audit history; the current archive, Gauntlet, and manifest evidence all pass.

### 4. AWS artifact lane

Run `.github/workflows/melodia_aws_publish.yml` manually on a labeled UE 5.8 runner.
Use GitHub OIDC into a narrowly scoped IAM role; require an explicit S3 bucket,
versioned prefix, and customer-managed KMS key. The publisher uses `aws s3 cp --recursive`
with no delete semantics. The default workflow mode is plan-only; a human must set
`confirm_publish=true` after inspecting the build evidence.

Plan-only runs no longer configure AWS credentials. Confirmed runs validate a role ARN,
assume it through OIDC, require SSE-KMS, and emit an evidence envelope. No local AWS
account, role, bucket, or KMS write has been performed in this session. The dry-run
envelope is `Saved/Integration/evidence/aws_artifact_publish_plan_2026-08-14_hold.json`.

### 5. Agent/JCODE lane

Use `.jcode/melodia_permissions.json` and `specs/mcp_tool_policy.v1.json` as the
coordination contract:

- max six workers; no recursive spawning;
- one writer for the Unreal editor surface;
- Monolith is authoritative for graph reads and mutation readback;
- `Tools/t3d_safe_wire.py` is the approved Blueprint mutation path;
- raw `ue_editor_command` is denied;
- owner approval is required for shared generated-content evolution;
- `Content/_PROJECT/**`, Sakura composition, and bulk `.uasset/.umap` churn remain
  red-lane/default-deny.

The in-repo bridge is registered in both `.mcp.json` and `.jcode/mcp.json`; run
`python Tools/validate_mcp_registration.py` to verify registration and policy
coverage after config changes. The sidecar audit still recommends centralizing
path canonicalization, writer ownership, correlation IDs, and evidence emission
behind one middleware before broadening mutation surfaces. Current proof is
`Saved/Integration/evidence/mcp_registration_2026-08-14_pass.json`.

## Evidence and acceptance criteria

Each lane produces a `melodia.evidence_envelope.v1` artifact. A release candidate is
not complete until the ledger-backed completion set is:

`runtime PASS + save_load PASS + repeat_consume PASS + package_launch PASS`

Current ledger result: all four completion gates are PASS as of 2026-08-14.
Static material drift still prevents a clean-baseline claim until the two graphs
receive owner review.

Static baseline failure blocks “clean” claims even if runtime is playable. The live
T3D probe, Ollama checks, contract tests, and BuildGraph validation are supporting
evidence for the completed integration foundation; they are not open completion
gates. The remaining work is the player-facing Core P0 golden run and owner review
of the two material drifts.

## Reference review applied

- [Epic BuildGraph](https://dev.epicgames.com/documentation/en-us/unreal-engine/buildgraph-for-unreal-engine)
  and [BuildGraph tasks](https://dev.epicgames.com/documentation/en-us/unreal-engine/buildgraph-script-tasks-reference-for-unreal-engine)
  informed the dependency graph and artifact boundary.
- [Epic Gauntlet](https://dev.epicgames.com/documentation/unreal-engine/running-gauntlet-tests-in-unreal-engine)
  informed the packaged runtime test stage.
- [Allar UE5 style guide](https://github.com/Allar/ue5-style-guide) informed the
  recommendation to keep naming, ownership, and asset scope consistent.
- [Official MCP servers](https://github.com/modelcontextprotocol/servers) informed
  explicit tool declaration and deny-by-default mutation policy.
- [Ollama API](https://github.com/ollama/ollama/blob/main/docs/api.md) informed local
  model discovery, digest recording, and health preflight.
- [AWS CDK](https://github.com/aws/aws-cdk) and AWS CodePipeline’s
  [QUEUED execution guidance](https://docs.aws.amazon.com/codepipeline/latest/userguide/execution-modes.html)
  informed the future infrastructure/pipeline lane; the current artifact publisher
  remains deliberately smaller and manual until the owner supplies the AWS account,
  role, bucket, and KMS details.
