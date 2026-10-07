# Melodia Houdini Studio Convergence Day — 2026-10-07

## Mission

Turn Houdini into a comfortable daily Melodia authoring environment and prove one shared procedural contract across Houdini, Blender, World Compiler / Universe Foundry, and UE 5.8.

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

## Gate 5 — World Compiler / Universe Foundry bridge

This is the important integration gate.

Audit the existing World Compiler and Universe Foundry input contracts first. Extend only at an existing seam.

Target flow:

Universe Foundry mission/recipe
  -> shared Melodia procedural recipe
  -> Houdini HDA/Hython authoring OR Blender adapter
  -> versioned manifest + geometry/field outputs
  -> World Compiler / existing UE import/PCG lane
  -> World Field Bus / PCG / materials / Niagara consumers
  -> UE runtime

Rules:
- Universe Foundry may request a product; it does not become a geometry generator.
- Houdini may emit geometry, PCG points, masks/fields and metadata; it does not become runtime world authority.
- World Compiler remains deterministic compiler/hand-off authority.
- Live Houdini Engine cooks are editor authoring; shipping runtime must consume baked/versioned results unless a future explicit packaged-HE architecture is approved.
- Reuse the existing audio/cymatic semantics; never add a second MPC/OSC writer.

Minimum live proof:
1. Universe/World recipe selects Crystal Cathedral recipe.
2. Houdini Engine or deterministic Hython produces/updates a bounded Cathedral output in editor.
3. Existing World/PCG lane consumes it.
4. Change one safe recipe parameter.
5. UE reflects the update.
6. Restore original recipe; deterministic state returns.

No mass world rebuild.

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
- Worker E: World Compiler / Universe Foundry seam audit

Do not let workers independently invent schemas or authorities. The shared contract is merged only after one coordinator compares proposals against current canon.

Frontier reasoning is for architecture/review; deterministic Python/Hython/Blender scripts should perform generation and validation.

## Tomorrow's recommended order

1. Workspace comfort pass.
2. Contract/schema v0.1.
3. Hython baseline reproduction.
4. HDA adapter/parity.
5. Blender contract adapter.
6. World/Universe seam bridge.
7. One bounded live UE proof.
8. Musical modulation only if everything above is green.

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
5. World Compiler / Universe Foundry can request/consume the bounded product through an existing seam.
6. UE shows one reversible deterministic live-authoring change.
7. No competing authority was introduced.

That is the foundation for later ChoralFlock, Sir Melodious, ecology, Resonance Genome, and the long-term songwriting/creative-world layer.
