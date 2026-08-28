# Rider + Junie Unreal workflow — 2026-08-28

Status: canonical workflow hardening plan for Rider/Junie-assisted development.

Read first: [`AGENTS.md`](../AGENTS.md) and [`Docs/AGENT_LANES.md`](AGENT_LANES.md). Existing owner locks, STOP sentinels, editor serialization, and single-git-writer rules still outrank this document.

## Why this exists

Recent Melodia work shows strong verification, handoff, and fail-closed habits, but also three recurring risks:

1. machine-specific paths can leak back into otherwise portable tooling;
2. offline proxy checks can be described too strongly as live Unreal proof;
3. large AI-assisted commits can mix tooling, configuration, generated/LFS content, UI, and gameplay changes into one rollback unit.

Rider + Junie should become the standard entry point into the existing Melodia validation system, not a parallel workflow with separate assumptions.

## Mandatory commit train

Run these as isolated commits. Do not fold feature growth into commits 1–5.

### 1. `fix(tooling): restore portable repo discovery across UE and Blender tools`

- Remove hard-coded workstation roots from current tooling.
- Resolve the repo from `__file__` or an explicit `MELODIA_REPO_ROOT` override.
- Fail clearly when expected project markers are missing.
- Do not assume a drive letter, Windows username, or one workstation layout.

Success: the same command can run from Rider/Junie on the primary PC, a second PC, WSL where supported, and a future Perforce workspace without source edits.

### 2. `test(tooling): restore fail-closed worldgen verification contracts`

- Reuse shared verification predicates/contracts instead of ad-hoc success text.
- Required failures must produce a non-zero exit status.
- Machine-readable reports must distinguish `PASS`, `EXPECTED_FAIL`, `SKIPPED`, and `FAIL`.
- A partial result such as `24/25` must not exit successfully unless the missing check is explicitly classified as expected or skipped.

Success: Junie can trust process status and report data without interpreting optimistic console prose.

### 3. `test(ue5): separate offline asset validation from live Unreal import proof`

Offline validation may prove:

- FBX exists and parses;
- UCX naming/collision data is present;
- expected scale/import settings are generated;
- source/output manifests are valid.

Only live Unreal validation may claim:

- the asset imported successfully in Unreal;
- resulting `UStaticMesh` state is correct;
- collision, bounds, material slots, destination package, or editor behavior are correct.

Prefer Unreal Automation Tests/Specs for the live proof. Test assets must be isolated and cleaned up or rolled back.

Success: documentation and commit messages never call an offline proxy check a live UE import pass.

### 4. `chore(rider): add shared Melodia run and verification configurations`

Create/version shared Rider run configurations for the canonical operations, for example:

- Melodia — UE Editor
- Melodia — Build Editor
- Melodia — UE Automation Tests
- Melodia — Worldgen Verify
- Melodia — Musical GN Verify
- Melodia — FBX Export Validate
- Melodia — Blender Studio Tests
- Melodia — Full P0 Verify

Use before-launch steps where practical so build/verify sequences are reproducible from Rider rather than remembered manually.

Success: a fresh checkout has obvious, versioned entry points for the core verification paths.

### 5. `chore(junie): codify Melodia agent boundaries and proof requirements`

Add/maintain Junie project guidance so every task inherits the same project rules. At minimum:

- never modify human-owned hero/environment assets unless explicitly requested;
- never infer Unreal references solely from Asset Registry results — search C++ hard-coded package paths and `FSoftObjectPath` usage too;
- never claim live UE verification from an offline proxy test;
- never hard-code workstation paths;
- generated files belong only in declared generated/audit locations;
- a task is incomplete when required verification fails;
- avoid unrelated changes in one task/commit;
- prefer surgical edits and isolated commits;
- obey `AGENTS.md`, STOP sentinels, owner locks, and the one-editor/one-git-writer rules.

Success: a new Junie session does not need the operator to restate basic Melodia safety and proof policy.

### 6. `docs(workflow): define atomic AI-assisted commit lanes`

This document is the initial policy record. Keep future AI-assisted commits inside one semantic lane whenever possible.

## Atomic commit lanes

Use these boundaries by default:

| Lane | Contains | Must not silently include |
|---|---|---|
| `feat(musical)` | one musical/runtime behavior or builder family | editor config, bulk assets, unrelated UI cleanup |
| `feat(content)` | generated/imported content and LFS asset updates | tooling behavior changes |
| `feat(ue)` | Unreal integration/runtime changes | Blender pipeline refactors or bulk art changes |
| `fix(tooling)` | tooling bug/portability/safety fix | gameplay feature expansion |
| `test(...)` | verification, fixtures, automation specs | unrelated production behavior |
| `chore(rider)` | Rider project/run/debug configuration | source feature work |
| `chore(junie)` | Junie guidance/configuration | gameplay or content work |
| `docs(...)` | handoff, evidence, policy, plans | hidden source/config mutations |

If one task naturally spans several lanes, stop at the boundary, verify, commit, then continue in the next commit.

## Rider + Junie execution loop

Canonical loop:

1. Read the task, relevant owner locks, and current plan/handoff.
2. Use Rider navigation/usages/call hierarchy to map the affected surface before edits.
3. Give Junie a narrowly scoped objective with explicit success criteria and forbidden surfaces.
4. Edit only the intended lane.
5. Build or run the smallest meaningful verification.
6. Run the canonical lane verification from Rider/shared commands.
7. Review the full diff before staging; generated/LFS changes require deliberate inspection.
8. Commit one semantic unit with evidence in the message when useful.
9. Only then begin the next lane.

Junie should not be asked to “finish everything” across unrelated systems in one unchecked patch. High iteration speed comes from many verified small loops, not one enormous diff.

## Proof language

Use precise proof levels:

- **static/offline validated** — structure/configuration/file contract checked without Unreal;
- **tool-runtime validated** — Blender/Python/tool process actually executed;
- **UE editor validated** — Unreal Editor imported/executed/inspected the result;
- **PIE validated** — behavior observed in Play In Editor;
- **owner validated** — owner explicitly confirmed the result; do not reopen unless asked.

Do not promote one level to another in commit messages or handoffs.

## Review gate before commit

Before an AI-assisted commit, verify:

- the diff belongs to one lane;
- no new absolute workstation paths were introduced;
- no generated/LFS churn is unexplained;
- required tests actually fail closed;
- offline checks are labelled offline;
- Unreal claims have Unreal evidence;
- owner-authored assets and STOP-sentinel surfaces were not touched without authority;
- the commit can be reverted without unwinding unrelated work.

## Immediate priority

The next implementation work should follow this order:

1. portable path cleanup;
2. fail-closed contract cleanup;
3. true live Unreal import test separation;
4. shared Rider run configurations;
5. Junie project guidance;
6. resume feature growth after the workflow is reproducible.

This ordering is deliberate: it hardens the development loop first so later convergence/gameplay work gains speed without sacrificing reliability.
