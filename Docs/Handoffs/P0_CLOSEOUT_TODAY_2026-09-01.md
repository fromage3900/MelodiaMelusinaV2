# P0 closeout today — 2026-09-01

## Decision

P0 gameplay proof is complete in `Docs/P0_TASK_LEDGER.json`, but P0 is not yet shipping-certified.
Closeout today consists of reconciling the Echo ledger, producing a current package, and completing
one uninterrupted packaged golden run. Do not add systems or fold Shorewake asset rebinding,
Starskiff polish, jellyfish, materials, P1, or P2 work into this run.

## Reconciled state

The September 1 task ledger records all active gameplay/static gates PASS:

- `battle_integration_map`
- `hud_single_writer`
- `rhythm_owner`
- `rhythm_grade_to_result`
- `wardrobe_equip_roundtrip`
- `wardrobe_gameplay_hook`
- `music_world_key`
- `static_gates`

The evidence for the three newest passes is the September 1 focused-viewport run and full editor
restart recorded in:

- `Docs/Evidence/P0_EXPLORATION_WARDROBE_GLIDE_PORTAL_PROBE_2026-08-31.md`
- `Docs/P0_TASK_LEDGER.json`
- `Saved/Audit/p0_real_input_run/`

`Saved/gate_ledger.json` is behind that evidence. Consequently `python Tools/echo_run.py status`
still reports `wardrobe_equip_roundtrip` and `wardrobe_gameplay_hook` OPEN and
`music_world_key` FAIL. This is ledger drift, not a request to rebuild those systems.

The last `package_launch` PASS is 2026-08-14 and is historical only. No recent document records a
current BuildCookRun plus packaged golden run.

## Today’s execution order

1. Preflight the single editor: exactly one `UnrealEditor`, exactly one listener on 9316, zero dirty
   packages, and zero errored Blueprints. If dirty or errored, capture and stop; do not save
   unrelated packages.
2. Re-read the September 1 evidence files above, then record the three missing current rows through
   the normal gate recorder:
   - `wardrobe_equip_roundtrip pass`
   - `wardrobe_gameplay_hook pass`
   - `music_world_key pass`
3. Regenerate the gate report and require `echo_run status` to agree with
   `Docs/P0_TASK_LEDGER.json`. Do not hand-edit a generated report.
4. Run the focused pre-package checks against the current editor/build:
   - `Melodia.Wardrobe` — 6/6
   - `Melodia.P0` — 4/4
   - `Melodia.Quest.Shorewake` — 1/1
   - `Melodia.Melusina.Traversal.CapabilityContract` — 1/1
   - `python -m unittest Content.Python.Tests.test_qsc_allowlist_contract` — 4/4
   - `python Tools/echo_run.py run static_gates` — 5/5
5. Close the editor cleanly and run a current Win64 package. Use the project’s established
   BuildCookRun/package harness and include the four P0 maps. Do not promote the August 14 archive.
6. Launch the new package outside the editor and perform one uninterrupted 20–30 minute golden run:
   - Quill dialogue starts the allowlisted encounter.
   - One real-key rhythm grade changes the stock JRPG result.
   - The typed battle result resumes Quill exactly once.
   - The music node completes once and replay is idempotent.
   - The First Resonance reward equips the accessory and unlocks Glide.
   - Save, exit the process, relaunch, load, and confirm outfit/material restoration.
   - The portal changes from locked to `Continue exploring [F]` and interaction succeeds.
7. Save a machine-readable assertion report beside captures/logs. Record fresh
   `package_build`/`package_launch` rows only after the package and golden run pass.
8. Mark P0 closed only when the task ledger, Echo ledger/report, and packaged evidence all agree.

## Hard stop conditions

- More than one editor or more than one 9316 listener.
- `MODAL_OPEN` in the log: resolve the modal; do not kill the editor.
- Any dirty unrelated package.
- Any focused test or static gate failure.
- Any package cook, launch, real-input, save/restart/load, exactly-once, or visible-route failure.

On failure, preserve the report/log/captures, record FAIL, and stop. Do not modify gameplay or
Blueprints to make the run pass.

## Explicitly outside today’s P0 closeout

- Importing or assigning `SK_ShorewakeDress_Melusina465.fbx`.
- Replacing the current Shorewake dress/skeleton or changing wardrobe catalog rows.
- Starskiff expansion or polish.
- Jellyfish, Sea Above lookdev, material, Niagara, Houdini, or cymatics work.
- The incomplete six-pass animation/fun review from 2026-08-29.
- P1/P2/P3 roadmap work and post-P0 economy expansion.

Those items remain valid follow-up work, but none is required to certify the integrated First Dream
P0 loop described by the active gate contracts.

## Execution result — 2026-09-01 18:20 EDT

- Preflight PASS: one responsive editor/Monolith surface on 9316, zero dirty packages, zero errored
  Blueprints.
- Echo ledger reconciled: `wardrobe_equip_roundtrip`, `wardrobe_gameplay_hook`, and
  `music_world_key` recorded PASS from the existing September 1 evidence; the generated report now
  agrees with the task ledger.
- Focused editor tests PASS: Wardrobe 6/6, P0 4/4, Shorewake 1/1, traversal capability 1/1.
- QSC allowlist contract PASS: 4/4.
- Static chain BLOCKED: two separate `python Tools/echo_run.py run static_gates` attempts emitted
  only the chain header and no stage result while the editor remained responsive. The first was
  stopped after more than four minutes; the second reproduced the silence and was stopped after the
  final bounded window. No new `MODAL_OPEN`, no asset mutation, and no PASS/FAIL envelope was
  produced.
- Packaging and the packaged golden run were not started because the required current static result
  was unavailable. This is a HOLD, not a shipping pass.
- Final safety read found eight newly dirty, unrelated Cathedral Houdini static-mesh packages under
  `/Game/EnvSandbox/Meshes/Cathedral_Houdini/`. They were absent at preflight and were not saved or
  modified by this closeout lane. Their presence independently triggers the dirty-package hard stop.

## Golden-run request follow-up

The golden-run preflight was executed after ledger reconciliation:

- `Tools/verify_p0_offline.py`: 12/12 PASS.
- `melodia_system_golden_run_preflight`: `ready=true`; all three route maps and both config assets
  present; four legacy completion gates PASS; Echo present; Monolith reachable.
- Package inventory: newest executable remains dated 2026-08-14.

The full golden run was not claimed. Its machine-readable contract has
`status=owner_run_required`, requires a fresh-slot player-facing Morning → KaleidoNave playthrough,
and explicitly forbids substituting integration-map probes or historical package evidence. The
eight unrelated dirty Cathedral packages also prevented a safe editor shutdown for a current
package build. Evidence envelope:
`Docs/Evidence/P0_GOLDEN_RUN_ATTEMPT_2026-09-01.json`.
