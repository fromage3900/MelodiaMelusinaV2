# Core P0 Dream Slice — Current Handoff

**Date:** 2026-08-14  
**Status:** Ready for the owner’s golden-run playtest  
**Scope authority:** `_VERTICAL_SLICE_SCOPE.md` and the First Dream playtest contract

The machine-readable execution contract is
`specs/p0/core_p0_dream_golden_run.v1.json`. It is an owner-run checklist and
evidence schema, not a claim that the golden run has passed.

## Executive finding

The integration foundation is complete. The four release-facing evidence gates are
PASS:

| Gate | Result | Evidence |
|---|---|---|
| `runtime` | PASS | `Saved/Echo/state.txt` and the 2026-08-13 owner-verified session |
| `save_load` | PASS | `Saved/Integration/evidence/save_load_2026-08-14_restart_pass.json` |
| `repeat_consume` | PASS | `Saved/Integration/evidence/repeat_consume_2026-08-14_live_resume_pass.json` |
| `package_launch` | PASS | `Saved/Integration/evidence/package_launch_2026-08-14_pass.json` |

This means the next P0 is no longer “prove that the subsystems can talk.” It is to
prove that the player-facing dream slice feels coherent, readable, and repeatable in
one clean run.

## Map authority — do not conflate the two maps

The correction that matters for the next pass is:

- **Canonical integration proof map:**
  `/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap`

  This is the authority for `BP_SavePoint_2`, canonical slot writes, full process
  restart, `AOrreryMainMenuGameMode::HandleContinueClicked`, Quill resume, and
  repeat-consume verification. Use it for deterministic integration checkpoints.

- **Player-facing dream route:**
  `/Game/Melodia/Levels/Opening/L_MelusinaMorning` →
  `/Game/EnvSandbox/Environments/L_KaleidoNave`

  Dreamstate content was merged into KaleidoNave. `L_Melodia_Dreamstate` is not a
  live route leg. This route is where the emotional and presentation slice is judged.

The integration proof map is not a substitute for the player-facing route, and the
player-facing route is not a substitute for the canonical persistence proof map.

## Findings by lane

### Runtime, Quill, and persistence

- The live authored script is `/Game/MelodiaIntegration/Narrative/MelodiaQuillPetalPriestess`.
- The first authored notification was observed as
  `melodia:stat:priestess_first_echo:melodia_harmony:1`.
- Quest acceptance was observed as `melodia:quest:melodia_q_echo_01`.
- The pre-notify checkpoint contained no consumed intent IDs and a serialized
  `QuillPersistentData` payload.
- `ResumeScript` emitted the authored notification once and produced
  `melodia_harmony=1`.
- A second restore/replay did not duplicate the social stat or consumed IDs.
- The exact live evidence is in the repeat-consume envelope; this is now a regression
  guard, not an open completion gate.

### Packaging and BuildGraph

- A fresh Development package launched outside the editor and passed the packaged
  Gauntlet Project run.
- BuildGraph XML parsing, contract validation, isolated CookPackage, isolated
  Gauntlet, and local ManifestOnly all pass.
- Horde `CreateArtifact` is intentionally opt-in and remains unrun because no
  `UE_HORDE_STREAMID` is configured. The GitHub artifact lane is the supported
  publication boundary for now.
- The stale staged executable and historical cook-failure records remain useful for
  audit history, but they are not current package status.

### T3D, Ollama, and agent integration

- The T3D pure-logic suite passes 42/42. The existing live probe envelope is
  historical and predates the request-derived postcondition repair; it is not fresh
  evidence for the current `inject`/`blueprint_compile` rows. Re-run it before using
  the mutation path for production BP authoring.
- Ollama health passed for `qwen2.5-coder:7b`, `hermes3:latest`, and
  `deepseek-r1:14b`.
- `agent_bridge` is registered in both `.mcp.json` and `.jcode/mcp.json`.
- MCP registration/policy validation passes: bridge tools are covered, default deny
  remains active, and raw Unreal editor commands are denied.
- The next tooling improvement is central middleware for path canonicalization,
  one-writer ownership, approvals, bounded payloads, correlation IDs, and evidence
  envelopes. Do not broaden mutation surfaces before that middleware exists.

### Static and material baseline

The live static pass was not clean because two material graphs drifted from baseline:

- `M_Master_Simple_Universal`: 32,305 → 33,784 bytes; 25 → 26 nodes.
- `M_Master_Toon_Landscape_HeightBlend`: 427,468 → 450,364 bytes; 290 → 304 nodes.

These are P1 review items, not reasons to reopen the four runtime gates. Do not accept
the drift into baseline until an owner confirms whether each change is intentional.

### AWS publication

The AWS lane is correctly held by design. The plan-only run passed manifest presence,
immutable-prefix, no-delete, SSE-KMS metadata, and no-remote-write checks. Confirmed
publication still needs the owner’s role, bucket, prefix, KMS, and approval choices.

## Next P0 execution slice

Run one clean golden pass with one editor writer and a fresh slot:

1. Start through the normal New Game flow.
2. Enter `L_MelusinaMorning` and trigger the authored Petal Priestess/Quill beat.
3. Confirm the choice reads correctly and converges to the single Harmony intent.
4. Follow the authored departure into the merged Dreamstate presentation in
   `L_KaleidoNave`.
5. Complete one stock encounter and exercise the typed result path.
6. Continue through the authored consequence and save through the normal authority.
7. Exit the editor process, restart it, and use the canonical Continue path.
8. Confirm map/spawn context, Harmony, quest state, encounter completion, and reward
   idempotence.

Use `/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap` whenever the run needs a
deterministic persistence/replay checkpoint or a regression reproduction. Keep the
player-facing route on Morning → KaleidoNave.

## P0 exit criteria

The Core P0 dream slice is ready to expand only when:

- one owner can complete the route without an editor modal, stale map, or duplicate
  writer;
- the Quill beat is visible, readable, and advances exactly once per action;
- the encounter has one clear typed result and returns control to the authored route;
- save/restart/Continue preserves context and does not duplicate Harmony, quest, or
  reward state;
- the same run is repeatable from a fresh slot; and
- no new system is required to explain a failure before the route is fun.

## Explicitly not next

Do not expand into a second combat framework, roguelike generation, broad wardrobe or
party systems, AWS remote publication, or Horde provisioning before the golden run is
accepted. Static material drift review and MCP middleware hardening can proceed as
parallel P1 lanes, but they do not replace the P0 playtest.

## Primary references

- `_VERTICAL_SLICE_SCOPE.md`
- `Docs/FIRST_DREAM_20_MINUTE_PLAYTEST_2026-08-01.md`
- `Docs/Handoffs/INTEGRATION_LAYER_EXPANSION_PLAN_2026-08-14.md`
- `_TASK_QUEUE.md`
- `Saved/Integration/evidence/repeat_consume_2026-08-14_live_resume_pass.json`
- `Saved/Integration/evidence/save_load_2026-08-14_restart_pass.json`
- `Saved/Integration/evidence/package_launch_2026-08-14_pass.json`
