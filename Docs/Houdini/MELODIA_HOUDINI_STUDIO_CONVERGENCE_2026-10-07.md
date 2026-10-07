# Melodia Houdini Studio Convergence Day — 2026-10-07

## Mission

Turn Houdini into a comfortable daily Melodia authoring environment and prove one shared procedural contract across Houdini, Blender, World Compiler / Universe Foundry, and UE 5.8.

**Universe Foundry is the mission envelope for this day.** It should describe and evidence-gate the bounded work, while existing owners still execute it. Where an existing request/manifest schema supports it, generated work should preserve a `mission_ref` (mission id + task id), recipe identity, deterministic seed, input hash, and output/evidence hashes. Do not move creative recipe truth into the mission DAG and do not make Foundry a geometry/runtime authority.

This is **convergence**, not a new framework. Preserve current authorities:
- UE 5.8 remains runtime/gameplay authority.
- World Compiler remains the deterministic world compilation lane.
- Universe Foundry remains the high-level world/mission recipe/orchestration lane.
- Houdini/Hython/HDA is an authoring + processing lane, including live Houdini Engine editor cooks and versioned bakes.
- Blender/GN remains a first-class rapid authoring/lookdev/kit lane.
- Existing audio/cymatic single-writer and World Field Bus rules remain binding.
- Do not create a second compiler, second OSC bridge, second runtime world-state authority, or duplicate chord table.

## Why now

UE/runtime has stabilized enough that the largest leverage is DCC convergence. KineFX/AnimationDoctor proved Houdini can solve production problems rather than remain an isolated experiment. Crystal Cathedral already spans deterministic Hython geometry, a Blender GN interface, PCG song layout, Copernicus look generation, Foundry recipes, and UE assets. It is the best canary.

## Universe Foundry mission envelope — applies to every gate

Before broad DCC edits, establish one deterministic orchestration baseline:

1. Validate + compile the existing authored Universe Foundry World Zero inputs on current `main`.
2. Record the generated mission id, genome hash, delta hash, ready tasks, and mission JSON path.
3. Recompile unchanged inputs and prove the mission id/DAG are identical.
4. For Houdini Foundry/BakeFarm work, use the existing optional `mission_ref` seam where legal so a bake request can point back to the exact Foundry task it satisfies.
5. Require execution evidence to return through the owning lane's manifest/receipt; the mission references evidence, it does not replace that evidence.
6. Keep the Crystal Cathedral as the DCC-convergence canary. **Do not invent a fake Crystal Cathedral world genome merely to make the diagram look cleaner.** If Universe Foundry cannot yet express a generic Cathedral product request through an existing additive seam, use the current Faraway Mother mission for the orchestration canary and keep Cathedral on its real World Compiler/Houdini recipe path. Record the missing generic seam as follow-up instead of widening tomorrow's scope.

The end-to-end invariant for the day is:

```text
same Foundry inputs -> same mission id/DAG
same procedural recipe + seed -> same authored output identity
bounded recipe change -> bounded UE-visible change
restore original inputs -> original deterministic authored state
```

That turns Universe Foundry into the control/evidence plane for the convergence work without creating another generator.

## Gate 0 — Sync and inventory before edits

1. Prove HEAD == origin/main.
2. Read:
   - START_HERE_HOUDINI_2026-10-06.md
   - Docs/Houdini/FoundryDay_2026-09-24/README.md
   - Docs/Houdini/FoundryDay_2026-09-24/03_CRYSTAL_CATHEDRAL_HDA.md
   - Docs/Architecture/AUDIO_REACTIVE_CANON.md
   - Docs/WorldGen/WORLD_COMPILER_CONTRACT.md
   - relevant Universe Foundry contract/docs
3. Inspect existing Houdini shelf/startup/package files before inventing any.
4. Inspect Blender melodia_gn registration/core and current Crystal Cathedral GN stub.
5. Record what exists vs what is proposed. Never mark planned HDAs as built without evidence.
6. Run the Universe Foundry baseline before mutation:
   - validate the current authored World Genome + Delta;
   - compile the mission;
   - `show`/inspect ready tasks;
   - compile again and verify identical mission identity/DAG.
7. Record whether the exact Houdini/World Compiler task needed for tomorrow can already be represented by an existing mission task or `mission_ref`. If not, **do not redesign Foundry at Gate 0**; record the seam and proceed with the existing owner.

STOP if the checkout is stale or current authority docs disagree materially.

## Gate 1 — Melodia Houdini Studio workspace

Goal: make Houdini feel closer to the user's Blender-centered daily workflow without fighting Houdini conventions.

Create a **repo-tracked setup recipe/scripts**, not fragile machine-only preferences. Machine-specific UI preference files should remain local unless SideFX explicitly supports portable packaging.

Desired desktop:
- Large Scene View / Solaris-or-SOP viewport as visual center.
- Network Editor immediately accessible and large enough for procedural work.
- Parameters adjacent to Network Editor.
- Scene Graph / Tree compact, Blender-Outliner-like.
- Geometry Spreadsheet available as a diagnostic tab, not dominant.
- Python Shell / status/evidence pane easy to reveal.
- Animation/KineFX desktop variant with Scene View + Network + Animation Editor/MotionClip tools.
- Optional dual-monitor variant, but laptop/single-monitor layout is the baseline.

Interaction goals:
- familiar orbit/pan framing where safely configurable;
- visible object/node naming and selection state;
- one-click frame selected/home;
- dark uncluttered viewport;
- useful grid/axis/guides, no debug clutter by default;
- quick switch between Beauty, Wire/Topology, Attributes, and KineFX diagnostic views.

Create a small Melodia shelf/toolset with commands that call existing repo scripts rather than duplicating logic:
- Melodia Project / repo-root setup
- Foundry Validate
- Cathedral Canary
- AnimationDoctor
- Bake / Evidence
- Open Evidence Folder
- UE/Houdini Engine handoff helper (authoring only)

Do not hardcode C:, G:, Humber lab paths, usernames, or licence-specific paths. Resolve project root from environment / hip / repo discovery.

Evidence:
- screenshot(s) of default workspace
- screenshot of KineFX workspace
- setup manifest listing installed shelf/tools/packages and whether each is repo-tracked or local

## Gate 2 — Shared Procedural Contract v0.1

Create a small versioned schema for DCC-neutral procedural intent. Prefer JSON + JSON Schema under existing specs/recipes conventions.

Crystal Cathedral canary fields:
- schema/version
- product id
- deterministic seed
- units + coordinate convention
- bays
- arch span
- vault height
- recursion depth
- tracery density
- crystal density
- facet count
- rose mode N/M
- musical reference (canonical progression source, not copied chord data)
- optional resonance/song influence
- output identity/version
- semantic groups/attributes expected from a producer

Classify contract fields:
- EXACT: seed, semantic inputs, units, identity, musical reference
- EQUIVALENT: named architectural regions/groups, bounds intent, material/field semantics
- DCC-SPECIFIC: topology, node graph implementation, preview fidelity

Do **not** require Blender and Houdini to have identical topology.

Add a pure-Python validator usable by both DCCs. It should validate schema and emit a concise manifest. No UE dependency.

Keep orchestration provenance outside the creative recipe itself. The request/output manifest wrapper may carry:
- `mission_ref.mission_id`
- `mission_ref.task_id`
- recipe id/version
- deterministic seed
- canonical input hash
- producer/tool version
- output/evidence hashes

This lets Universe Foundry trace work without making the procedural recipe dependent on Hermes or a particular agent.

## Gate 3 — Crystal Cathedral Houdini adapter

Do not rewrite the Cathedral.

Use the existing geometry authority:
- Tools/Houdini/cathedral/build_fractal_cathedral.py
- Tools/Houdini/cathedral/build_crystal_cathedral.py

Follow the existing HDA promotion plan:
- expose/refactor only the already specified knobs;
- default cook must preserve current deterministic output;
- SongInfluence default = 0;
- add semantic groups/attributes where practical;
- HDA/Python SOP calls the existing builders;
- produce parity evidence.

Baseline six-bay expected proof remains:
- Crystal nave: 2706 verts / 2101 faces
- Crystal rose: 1032 verts / 290 faces
unless current authoritative manifests intentionally changed.

No overwrite of Sea Above owner-authored placement or existing SM_P4 assets.

## Gate 4 — Blender adapter: stop pretending to be a second authority

Current MEL_p4_crystal_cathedral is an interface stub. Preserve Blender as a useful authoring/lookdev peer, but make it consume the same contract.

First implementation may be intentionally lightweight:
- read/validate the shared recipe;
- expose the same semantic controls;
- emit/attach contract metadata;
- build a preview/equivalent representation OR consume a versioned Houdini bake;
- keep Eevee/lookdev and GN iteration fast.

Do not port the entire Houdini cathedral algorithm into GN merely for numerical parity.

Prove:
- same recipe id + seed recognized in both DCCs;
- same semantic parameter values;
- output manifests classify differences correctly.

## Gate 5 — Universe Foundry mission -> Houdini Foundry -> World Compiler bridge

This is the important integration gate. The objective is not merely that the tools can all read the same recipe; it is that a **Foundry mission can dispatch or reference one bounded procedural job, receive its real evidence, and allow the existing World Compiler/UE lane to consume the result without authority drift.**

Audit the existing World Compiler, Universe Foundry, and Houdini Foundry request/manifest contracts first. Extend only at an existing additive seam.

Preferred target flow:

```text
World Genome + exported/fixture World Delta
  -> Tools/universe_foundry.py
  -> deterministic mission.json
  -> Hermes exposes one ready bounded task
  -> Houdini Foundry bake request (mission_ref = mission_id + task_id)
  -> shared Melodia procedural recipe
  -> existing HDA/Hython producer
  -> bake/output manifest + hashes + evidence
  -> World Compiler / existing UE import/PCG lane
  -> World Field Bus / PCG / materials / Niagara consumers
  -> UE runtime proof
  -> evidence receipt closes only that mission task
```

Crystal Cathedral remains the preferred visual DCC canary, but use it inside this flow **only if the existing Foundry contract can represent the request without inventing a fake world or rewriting the mission compiler**. Otherwise:
- use the current Faraway Mother authored genome/mission to prove the Universe Foundry -> mission_ref -> Houdini evidence path;
- use Crystal Cathedral to prove shared recipe/HDA/Blender/World Compiler convergence;
- record the smallest missing generic product-task seam for a later additive Foundry version.

Rules:
- Universe Foundry describes dependencies, ownership, stop conditions, and required proof; it does not generate geometry.
- Hermes dispatches/continues; it does not become implementation authority.
- Jev remains closed-set/bounded judgment only.
- Houdini may emit geometry, PCG points, masks/fields and metadata; it does not become runtime world authority.
- World Compiler remains deterministic world compiler/hand-off authority.
- Live Houdini Engine cooks are editor authoring; shipping runtime consumes baked/versioned results unless a future explicit packaged-HE architecture is approved.
- Runtime/save truth stays in Unreal; fixture deltas cannot satisfy persistence acceptance.
- Reuse the existing audio/cymatic semantics; never add a second MPC/OSC writer.

Minimum live proof:
1. Recompile the baseline Universe Foundry inputs; mission identity is stable.
2. Select one legal ready procedural/Houdini-facing mission task or bind through the existing `mission_ref` request seam.
3. Execute one deterministic Hython/HDA job and emit a manifest that preserves mission/task provenance plus input/output hashes.
4. Existing World Compiler/PCG or UE import lane consumes the bounded result.
5. Change one safe recipe parameter; output identity changes and UE visibly reflects only the bounded change.
6. Restore the original recipe/input; output hash/identity and authored UE state return deterministically.
7. Attach independent evidence; do not allow the producing worker to self-certify mission completion.

No mass world rebuild. No new universe schema merely for tomorrow's demo.

## Gate 6 — Musical Cathedral v0.2

Only after Gates 2–5 work.

Use the canonical song source already owned by the PCG song cathedral. Do not duplicate CHORD_PROGRESS.

Activate a tiny subset of the existing proposed mapping:
- pitch/chord semantics -> RoseMode N/M
- major/minor quality -> bounded facet variation
- station -> bounded crystal density
- resonance -> crystal height + emissive/sparkle metadata

Start with the existing six-station C / Dm / F / G / Am / E proof.

Success is not “music visualization.” Success is:
**one musical semantic change coherently alters authored geometry/metadata and downstream UE presentation through existing authorities.**

## Gate 7 — Evidence and canonization

Required receipts:
- Houdini workspace screenshots
- shared recipe + schema validation PASS
- Hython baseline determinism/parity
- HDA cook evidence if built
- Blender adapter manifest
- World/Universe bridge manifest
- UE editor proof for one bounded live update
- restoration/reproducibility proof
- list of generated vs tracked artifacts

Update authority docs only for things actually proven.

## Muse execution policy

Muse should use bounded workers/subagents only where parallelism is safe:
- Worker A: Houdini workspace/shelf/package inventory + portable setup
- Worker B: shared schema + pure validator
- Worker C: Cathedral HDA adapter/parity
- Worker D: Blender adapter audit
- Worker E: Universe Foundry mission baseline + mission_ref / World Compiler / Houdini Foundry seam audit

Do not let workers independently invent schemas or authorities. The shared contract is merged only after one coordinator compares proposals against current canon.

Frontier reasoning is for architecture/review; deterministic Python/Hython/Blender scripts should perform generation and validation.

## Tomorrow's recommended order

1. Sync + Universe Foundry deterministic mission baseline.
2. Workspace comfort pass.
3. Contract/schema v0.1 + provenance manifest wrapper.
4. Hython baseline reproduction.
5. HDA adapter/parity.
6. Blender contract adapter.
7. Foundry mission_ref -> Houdini evidence -> World Compiler seam proof.
8. One bounded reversible live UE proof.
9. Musical modulation only if everything above is green.

## Stop conditions

Stop and report instead of expanding scope if:
- current main differs from the documented authority;
- exact baseline Cathedral determinism breaks;
- a change requires a second compiler/world-state authority;
- Blender/Houdini parity would require maintaining duplicate geometry algorithms;
- live Houdini Engine would overwrite canonical UE assets/placements;
- a proposed bridge writes directly around World Compiler / Field Bus / audio single-writer rules;
- Muse starts broad world generation before the canary is proven.

## Definition of done

A successful day does **not** require a finished musical universe.

Done means:
1. Houdini opens into a comfortable repeatable Melodia workspace.
2. One DCC-neutral Crystal Cathedral recipe is valid.
3. Houdini and Blender both understand it.
4. Houdini remains the strong procedural producer; Blender remains the fast authoring/lookdev peer.
5. Universe Foundry deterministically emits/replays the orchestration mission, and at least one procedural execution receipt is traceable to an exact mission/task through an existing seam.
6. World Compiler can consume the bounded authored product without a second compiler or runtime authority.
7. UE shows one reversible deterministic live-authoring change, and restoring the original inputs restores the original authored state.
8. No competing authority was introduced.

That is the foundation for later ChoralFlock, Sir Melodious, ecology, Resonance Genome, and the long-term songwriting/creative-world layer.
