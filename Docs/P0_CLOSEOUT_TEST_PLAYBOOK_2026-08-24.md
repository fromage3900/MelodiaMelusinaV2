# P0 closeout and test playbook — 2026-08-24

## Status: execution-ready plan; P0 remains open

This is the operator playbook for closing the existing First Dream slice with professional,
evidence-grade discipline. It does not authorize feature expansion or claim that live gates pass.
The current authority and gate state remain:

- [Melodia convergence closeout and P0 plan](Handoffs/MELODIA_CONVERGENCE_CLOSEOUT_AND_P0_PLAN_2026-08-24.md)
- [P0 task ledger](P0_TASK_LEDGER.json)
- [Orchestra contract](ORCHESTRA_CONTRACT_2026-08-20.md)

The target experience is one 20–30 minute Morning Preparation → Expedition → Evening Return
loop. QuillScript owns authored narrative. The stock TurnBased JRPG owns battle, party,
inventory, reward, and save. No test fix may create a second authority.

## Definition of done

P0 closes only when one frozen commit proves all of the following:

1. The offline source/contract tier is green with assertion-bearing tests.
2. One editor and one Monolith owner produce live readback from the intended maps and actors.
3. One real-key PIE route proves the eight active gates in `P0_TASK_LEDGER.json`.
4. Victory, Defeat, Fled, and unavailable each produce one typed result and one continuation or
   fail-closed abort.
5. Fresh Slot and Continue preserve choice, quest, outfit, capability, reward journal, encounter
   outcome, and dialogue checkpoint without duplicate effects.
6. The accepted Development package repeats the route outside the editor.
7. Every passing gate links assertions and content hashes; screenshots are supporting context,
   never the oracle.

## High-assurance operating model

| Role | Owns | Must not do |
| --- | --- | --- |
| Baseline coordinator | commit ID, path leases, test order, evidence manifest | edit production content or absorb another lane's failure |
| Editor owner | the single UE process, live readback, PIE, save/restart, package run | launch a second editor/proxy or accept a modal state |
| Source lane | one named blocker and its tests | broaden into economy/song/dungeon expansion |
| Evidence reviewer | assertion report, hashes, proof-tier classification | infer runtime success from source, logs, marker text, or screenshots |

Use one concern per commit. Re-run a lane if its inputs change once. Put it on
`MOVING_BASELINE_HOLD` after a second baseline change. Never repair a failing assertion inside the
evidence recorder; fix the authority seam and run again.

## Proof ladder

| Tier | Required evidence | May advance when |
| --- | --- | --- |
| 0 — source | resolved paths/IDs, deterministic schema and contract checks | every check has at least one real assertion |
| 1 — build | closed-editor compile, UHT/link success, no stale binary substitution | the exact source commit compiles |
| 2 — live readback | Monolith health plus CDO/component/graph/level-instance reads | the intended assets and placed instances are identified |
| 3 — PIE seam | real player input plus before/after canonical-state snapshots | typed state transitions and exactly-once counts pass |
| 4 — restart | save, process exit, new process, Continue, state comparison | no state or reward is lost or duplicated |
| 5 — packaged | accepted Development package, fresh run, Continue run | the same assertions pass without editor-only behavior |

No tier inherits proof from a lower tier. Historical PASS rows remain context for their recorded
August 13–14 baselines only.

## Current offline checkpoint

Run from `C:\EnvironmentPortfolio\BS_GodFile` with `python -B`:

```powershell
python -B Tools/test_melodia_mcp.py
python -B Tools/test_melodia_first_dream_route_contract.py
python -B Tools/test_melodia_progression_contract.py
python -B Tools/test_melodia_chapter_content_package_contract.py
python -B -m unittest discover -s Tools/experience_contract_audit/tests -v
```

Current result:

| Surface | Result | Proof tier |
| --- | --- | --- |
| Melodia MCP | **36/36 PASS** | offline transport/schema only |
| Progression contract | **6 PASS** | offline model only |
| Chapter package contract | **6 PASS** | offline model only |
| Experience contract | **15 PASS** | offline design model only |
| First Dream source route | **FAIL** | malformed three-part flag intent in `MelodiaQuillHarmonyAwakening.qsc` |

The route failure is a stop condition. `UMelodiaNarrativeSubsystem::HandleFlagVerb` requires
`melodia:flag:<FlagId>:<bool>`, while the authored Harmony Awakening source emits a three-part
notification. Fix the canonical source and its materialization path in a dedicated owner-reviewed
lane; do not weaken the test.

## P0 blocker register

| ID | Blocker | Required closure |
| --- | --- | --- |
| P0-NARR-01 | Malformed Harmony Awakening flag notification | canonical QSC/compiler alignment and green route contract |
| P0-QUEST-01 | NPC fallback directly calls Persona quest mutation and legacy `AMelodiaQuestManagerBase` | all shipping quest changes enter Quill → Narrative; prove placed actors use that path |
| P0-QUEST-02 | `UMelodiaOpeningFlowSubsystem` still reaches quarantined QuestManager/save state | migrate consumers, then disable automatic shipping creation before removal |
| P0-NPC-01 | NPC identity is split across rich, minimal, and placeholder definitions | one stable runtime NPC ID read from each placed interaction actor and tied to authored content |
| P0-TXN-01 | reward IDs are consumed before downstream grant/equip acknowledgement | one atomic command returns Applied, AlreadyApplied, or Rejected; failure consumes nothing |
| P0-SAVE-01 | `ScriptCheckpoint` has no production writer; pending encounter/completion guard is transient | persist checkpoint plus stable encounter command/outcome, or explicitly disallow saving mid-encounter |
| P0-ID-01 | progression design IDs differ from live Smoke QSC aliases; unavailable is absent from terminal result rules | one reviewed ID mapping and all four typed outcomes in the current contract |
| P0-OBS-01 | gate recorder permits free-form pass text and evidence envelopes permit empty artifacts | require assertion count > 0, content hashes, state snapshots, and gate-specific oracle fields |
| P0-MCP-01 | Persona MCP reads definitions/allowlists, not canonical runtime quest state or NPC instances | add a read-only canonical-state snapshot before using MCP output as quest proof |
| P0-PACE-01 | older golden-run spec targets 15–20 minutes; current authority targets 20–30 and adds preparation/wardrobe/music payoffs | reconcile the existing test contract in one controlled spec lane |

## Monolith connectivity and truth policy

The Melodia client now sends dotted calls using Monolith's actual MCP envelope:

```text
animation_query.get_abp_info
→ name: animation_query
→ arguments: { action: get_abp_info, params: {...} }
```

The same rule is covered for Blueprint and project queries. Live CDO readers use `asset_path`,
and action payloads with `success:false`, `ok:false`, `error`, or `_error` fail closed instead of
being labelled live evidence.

A read-only status probe on 2026-08-24 reached Monolith `0.20.3`. Re-probe at the start of every
live session and record version, project, editor owner, and exact frozen commit. Connectivity
proves only that the query surface responds.

Do not use these current tools as canonical quest-state proof:

- `melodia_persona_get_quests` reads the allowlist and Persona content-definition CDO.
- `melodia_narrative_get_record` returns an offline/schema projection, not the live saved record.
- `melodia_quest_check_p0` reports synthetic in-process economy test state.

The required read-only runtime snapshot must expose: placed NPC ID, Quill assignment, active and
completed quest IDs, flags, consumed intent/reward IDs, relationship choice, script checkpoint,
pending encounter command ID, typed outcome, and save slot identity.

## NPC and quest acceptance matrix

| Moment | Before assertion | Player action | After assertion | Replay assertion |
| --- | --- | --- | --- | --- |
| Morning preparation | no preparation command consumed | choose Sir or Priestess once | one stable choice ID, distinct modifier/reaction ID, day slot consumed | repeating interaction cannot change or duplicate the command |
| NPC interaction | placed actor has stable NPC ID and authored Quill asset | interact once | Quill advances one checkpoint; no direct Persona/QuestManager mutation | second interaction resumes or presents completed state only |
| Quest accept | quest absent; accept intent absent | authored Quill notification | quest active and exactly one consumed accept intent | reload/repeat is `AlreadyApplied` |
| Encounter result | one pending encounter command | resolve Victory/Defeat/Fled/unavailable | one typed outcome and one Quill continuation/abort | duplicate callback is ignored |
| Quest reward | reward intent absent | acknowledged quest completion transaction | quest state, reward grant, and consumed IDs commit together | failed grant leaves all three unchanged |
| Continue | canonical slot saved at known checkpoint | terminate process and Continue | same NPC/quest/outfit/outcome/checkpoint state | no repeated reward, stat, quest, or world command |

For the first slice, the authored Sir/Priestess preparation choice is still design intent. The
current Priestess branches converge to identical Harmony and quest effects, and Morning currently
offers chirp/listen. Record this as `NEED`, not as implemented choice economy.

## Four-outcome battle matrix

Run each outcome from the same frozen seed and encounter ID. Capture a before and after canonical
record, plus the continuation count.

| Outcome | Expected objective | Reward | Quill behavior |
| --- | --- | --- | --- |
| Victory | completed | one acknowledged reward | resume consequence exactly once |
| Defeat | failed/recoverable | none | resume defeat consequence exactly once |
| Fled | failed/recoverable | none | resume fled consequence exactly once |
| unavailable | no progression command consumed | none | fail closed or present retryable authored branch exactly once |

A rhythm miss may lower grade or modifier; it must never block access to progression.

## Animation and visual evidence policy

`capture_scene_preview` produced identical stale frames for different clips/times during the
Iteration 3 investigation. Therefore:

- Screenshots and video are presentation evidence only.
- Animation state requires active AnimInstance/class, state-machine state, sequence/montage,
  requested variables, and sampled bone/socket transforms.
- Clip motion requires at least three distinct time samples for named contract bones, with a
  non-zero transform delta where motion is expected.
- State transitions require before/after state names and timestamps from the same PIE actor.
- A screenshot hash may confirm artifact identity; it cannot confirm pose, playback, transition,
  or player input.

Do not close an animation, traversal, HUD, or encounter gate from a capture alone.

## Evidence envelope required for every PASS

Every gate record must include:

- stable run ID and command/encounter/intent IDs;
- commit hash, dirty-state manifest, map, save slot, editor and Monolith versions;
- assertion count greater than zero;
- typed before/after state snapshots;
- exact input source (`real_keyboard`, not a direct probe callback);
- artifact paths, SHA-256 hashes, creation timestamps, and producer command;
- result disposition (`Applied`, `AlreadyApplied`, or `Rejected` where transactional);
- one named owner/reviewer and explicit proof tier;
- open unknowns and any HOLD reason.

The recorder must reject zero assertions, marker-only text, empty artifact lists, missing hashes,
and a screenshot without a state oracle.

## Execution order beside the owner

1. **Freeze.** Record `HEAD`, fetched origin relation, short status, active editor owner, Monolith
   version, and exact leased paths. Two identical status snapshots are required.
2. **Make Tier 0 green.** Fix `P0-NARR-01`; run all five offline commands above. Stop on the first
   failure.
3. **Close quest-authority defects.** Remove the NPC/QuestManager mutation bypass, establish one
   NPC identity projection, and implement an acknowledged atomic quest/reward transaction.
4. **Close restart state.** Write/restore the dialogue checkpoint and encounter command/outcome,
   with a documented mid-encounter save policy.
5. **Compile closed-editor.** Build the exact frozen commit. No Live Coding substitution for
   reflected type/schema changes.
6. **Read back live.** Identify the actual placed NPCs, Quill assignments, battle UI writer,
   wardrobe component/loadout, Piano host/adapter, and target route actor.
7. **Run PIE gates.** Execute NPC interaction, wardrobe/Glide, music/world, rhythm/JRPG, and all
   four outcomes with real input and assertion snapshots.
8. **Restart.** Save, exit the process, restart, Continue, compare canonical snapshots, and repeat
   interactions to prove exactly once.
9. **Package.** Build and execute the accepted Development package, then repeat Fresh Slot and
   Continue.
10. **Review and record.** Hash evidence, review each oracle, update the ledger only for the exact
    frozen baseline, and publish claims at the proved tier.

## Stop conditions

Immediately mark HOLD if any of the following occurs:

- a second editor/proxy writer appears;
- the baseline changes twice;
- a modal blocks deterministic input;
- an ID, NPC, placed instance, save slot, or widget identity is inferred rather than read;
- an operation consumes an intent before its downstream effect acknowledges success;
- a gate has zero assertions, empty artifacts, missing hashes, or only screenshots;
- a tool falls back from live state to offline/spec data without changing its proof label;
- a lane proposes a new subsystem to hide a failing existing seam.

## Explicitly deferred

Do not add the four-economy/grief loop, extra song families, economy HUD, economy dungeon,
status-pressure enemy, expanded quest chain, full calendar, NPC schedules, wardrobe breadth,
styling contests, gacha, or additional companions until this playbook's P0 definition of done is
met.
