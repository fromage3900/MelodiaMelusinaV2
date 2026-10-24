# Melodia Agent Production Playbook

**Purpose:** canonical workflow reference for AI agents and human collaborators using the current Melodia production spine.  
**Status authority:** `CURRENT_STATE.md` remains the only status authority. This file explains **how to work** with proven tools; it must not be used to infer that a proof gate is complete.

## 0. Start here: use the production spine, do not invent another one

Before changing anything:

1. Read `AGENTS.md`.
2. Read the relevant row in `CURRENT_STATE.md`.
3. Identify the existing owner seam.
4. Use the workflow below that already owns the task.
5. Produce evidence at the same layer you changed.
6. Update `CURRENT_STATE.md` in the same PR only when project status actually changes.

Default assumption: **Melodia already has enough architecture to author content.** A new compiler, save owner, editor bridge, mocap importer, material framework, PCG scatter system, or automation surface is a defect unless a concrete blocker proves the current one cannot express the task.

---

## 1. Task router

| Task | Canonical first choice | Do not replace with |
|---|---|---|
| Procedural world / biome / dressing | World Compiler recipe -> CLI compile -> UE driver | ad-hoc scatter Python, a second PCG graph framework, direct actor spam |\n| Universe-scale mission / persistent world evolution | `Tools/universe_foundry.py` genome+exported-delta -> Hermes mission DAG -> existing owners | second World Compiler, AI-authored save truth, agent swarm mutating editors directly |
| Houdini geometry/material batch work | Hython under `Tools/Houdini/` | runtime UE authority, untracked one-off shelf tools |
| Rokoko / Melusina mocap | Blender retarget/export -> guarded UE importer | raw FBX drag/drop, alternate skeleton import lane |
| UE C++ / reflected API | JetBrains Rider + closed-editor UBT where required | blind text edits followed only by Live Coding |
| Focused native/editor automation test | RiderLink against the single intended editor session | bespoke one-off test bridge when RiderLink can run the test |
| Native/shader static analysis | Qodana via tracked `qodana.yaml` (`QDJB`) | ad-hoc linter setup that bypasses the project profile |
| Bounded judgment / orchestration | Jev with explicit candidates + criteria + provenance | unconstrained planner inventing new authorities or mutating the editor directly |
| Blueprint/editor mutation | one Unreal Editor + Monolith | multiple editors, competing MCP writers, persistent Python world refs |
| Audio-reactive world presentation | existing PhraseBus / MPC / cymatics consumers | second OSC semantic bus or second MPC writer |
| Blender procedural authoring | Melodia Studio 2.132.0 / GN source | copied legacy addon trees or stale laptop install as authority |
| VFX / Niagara authoring | Monolith `niagara_query` + `Tools/verify_niagara_surface.py` + `Tools/niagara_ecosystem_audit.py` | hand-rolled T3D Niagara injection (`t3d_niagara_injector.py`, retired), second VFX writer, editing the plugin for WISHLIST items without a content block |

---

# 2. World Compiler — default worldbuilding path

The World Compiler is the canonical content compiler for authored procedural world slices.

### Source of truth

- contract: `Docs/WorldGen/WORLD_COMPILER_CONTRACT.md`
- compiler: `Tools/world_compiler.py`
- UE driver: `Tools/world_compiler_ue_driver.py`
- editor consumer: `Content/Python/world_compiler_ue.py`
- editor panel: `Content/Python/world_compiler_panel.py`
- recipe schema: `specs/schemas/world_recipe.v1.schema.json`
- bundle schema: `specs/schemas/world_compiler_bundle.v1.schema.json`
- regression tests: `Tools/test_world_compiler.py`

### Golden workflow

```powershell
# 1. validate authored data
python Tools/world_compiler.py validate recipes/<recipe>.v1.json

# 2. offline compile
python Tools/world_compiler.py compile recipes/<recipe>.v1.json

# 3. inspect the generated bundle
python Tools/world_compiler.py show Saved/WorldCompiler/<recipe>_<seed>

# 4. run offline regression tests when the compiler/schema changed
python Tools/test_world_compiler.py

# 5. with ONE Unreal Editor already open, apply the bundle
python Tools/world_compiler_ue_driver.py Saved/WorldCompiler/<recipe>_<seed>

# common authored presentation passes
python Tools/world_compiler_ue_driver.py Saved/WorldCompiler/<recipe>_<seed> --fx
python Tools/world_compiler_ue_driver.py Saved/WorldCompiler/<recipe>_<seed> --lookdev
```

For spatial edits, run the existing scene-context cycle **before and after** the mutation:

- `Content/Python/scene_context_cycle.py`
- `Content/Python/scene_context_snapshot.py`

### Authority boundary

`Tools/world_compiler.py` is an offline compiler. It must not import `unreal`, own runtime truth, write MPC state, or become an editor automation server.

The UE lane consumes the compiled bundle. The PCG graph is data-driven; species/material/band choices belong in the table/recipe, not duplicated into per-species Python graph construction.

### Expansion rule

New place = new recipe/data first.

Extend compiler code only when the existing schema cannot represent a proven authored requirement. Prefer a schema/version extension over a parallel compiler.

### World Compiler anti-patterns

Never:

- create a second compiler inside an Editor Utility Widget;
- create per-species PCG graphs when the attribute-driven template can express the result;
- place thousands of `new_object` ISMs from Python as a substitute for PCG;
- write directly to `MPC_Melodia_Palette` or `MPC_Cymatics_Driver`;
- silently edit material masters per biome;
- call an offline compile "LIVE PROVEN";
- skip save/reload and visual-consumer evidence for a runtime claim.

---

# 3. Hython / Houdini — deterministic DCC forge, not runtime authority

Houdini is a production source lane for deterministic geometry, Copernicus textures, cloth/shape processing, caches, and procedural variants.

### Current verified executable family

The committed Houdini tools target the installed Houdini 22.0.368 family, commonly:

```text
C:\Program Files\Side Effects Software\Houdini 22.0.368\bin\hython.exe
```

Do not hardcode that path into new reusable tools. Resolve from environment/config where possible and record the actual Houdini version in evidence.

### Canonical locations

- Houdini tools: `Tools/Houdini/`
- Copernicus: `Tools/Houdini/copernicus/`
- Houdini Engine smoke contract: `Docs/WorldGen/HOUDINI_ENGINE_SMOKE_SPEC_2026-08-27.md`
- creative pipeline caveats: `Docs/Production/HOUDINI_CREATIVE_PIPELINE_REFERENCE_2026-08-28.md`
- MCP server: `deploy/houdini_mcp_server.py`

### Hython pattern

```powershell
# use the real Houdini Python runtime, not system Python
& "C:\Program Files\Side Effects Software\Houdini 22.0.368\bin\hython.exe" Tools/Houdini/<lane>/<tool>.py
```

Every production Hython tool should:

- accept deterministic inputs;
- use an explicit seed where randomness exists;
- write a machine-readable manifest/report;
- record version, seed, inputs, outputs and parameters;
- fail non-zero on invalid output;
- write into an intentional handoff/evidence location;
- keep UE/editor mutation out of the Hython process.

### Useful existing families

Use and extend these before making a new family:

- Copernicus texture/material generation: `Tools/Houdini/copernicus/`
- Sea Above / reef / cloth geometry: `Tools/Houdini/sea_above_reef/`
- VDM fabric: `Tools/Houdini/vdm_fabric_mountains/`
- procedural cathedral studies: `Tools/Houdini/cathedral/`

### Export/licensing caveat

Do not assume FBX/Alembic/Houdini Engine entitlement from source presence. Older verified sessions documented Apprentice restrictions on FBX/Alembic ROPs and used File SOP writes successfully. Probe the current license/session before choosing an export route, and record the route that actually cooked.

A successful Hython cook proves DCC output. It does **not** prove Unreal integration until the resulting asset/bundle is imported/applied and validated in UE.

### Houdini + World Compiler relationship

Use Hython to forge source assets, masks, textures, fields or deterministic variants. Use the World Compiler to author/place/compose the runtime world slice.

Do not turn Houdini Engine into a second live world compiler overlay.

---

# 4. Rokoko -> Melusina — guarded animation lane

The canonical Melusina mocap path is now:

```text
Rokoko Studio Vision take
  -> Blender retarget / repair
  -> root-motion FBX against the Melusina target rig
  -> Content/Python/import_rokoko_mocap_batch.py
  -> SK_Melusina_Skeleton
  -> ABP / state binding
  -> live PIE pose / movement evidence
```

Reference evidence:
`Docs/Handoffs/ROKOKO_MELUSINA_ANIM_EVIDENCE_2026-09-22.md`

### Guarded importer

Use:

`Content/Python/import_rokoko_mocap_batch.py`

The importer intentionally validates:

- target skeleton;
- animation-only FBX import;
- Melusina skeleton identity;
- the centimetre-scale spine probe;
- root motion enablement;
- a JSON import report.

Do not bypass it with manual drag/drop for production clips.

### Known landed clip evidence

The 2026-09-22 evidence lane landed five guarded clips including:

- WalkElegant — measured 54 cm/s;
- GlideForward — measured 217 cm/s;
- BowKneelAim — measured 55 cm/s;
- BowDraw v1/v2 — effectively in-place.

Treat those speeds as measured properties of those exact takes, not universal controller speeds.

### Binding rule

Retarget/import success is not equivalent to runtime use.

After import:

1. verify skeleton and sequence;
2. bind through the existing animation/state owner;
3. account for measured root speed when movement state speed differs;
4. compile/validate the ABP or state binding;
5. exercise the actual runtime actor in PIE;
6. capture machine-readable evidence.

### Critical editor safety

Do **not** hold PIE `UWorld` references across repeated `run_python` calls. The 2026-09-22 session hit a world-memory-leak fatal in that pattern.

Use Monolith `pie_*` C++ actions / `pie_call_function` for repeated PIE interaction instead of persistent Python world references.

### Animation anti-patterns

Never:

- import a second Melusina skeleton to make one clip work;
- normalize scale by eye after import;
- infer locomotion speed from an in-place root-locked clip;
- wire a blendspace sample without checking duplicate/dead nodes;
- call an asset-preview capture runtime evidence;
- delete imported cleanup debris without owner approval when deletion is not already in scope.

---

# 5. JetBrains Rider + UE 5.8 — canonical C++ workflow

Detailed runbook:
`Docs/Production/RIDER_UE58_CANONICAL_WORKFLOW.md`

Rider is the primary C++ reasoning, navigation, debugger and test surface. Unreal remains the runtime/asset authority.

### Use Rider first for

- Find Usages across reflected C++ and Blueprint references;
- `UCLASS` / `UFUNCTION` / `UPROPERTY` navigation and Blueprint usage discovery;
- inspection of module/reflection dependencies;
- Unreal-aware IWYU/include cleanup;
- native debugger breakpoints in the existing owner seam;
- automation-test navigation/execution with RiderLink when a single editor session is appropriate;
- `.usf` / `.ush` shader editing;
- `TRACE_CPUPROFILER_EVENT_SCOPE` instrumentation and Unreal Insights follow-through.

### Closed-editor build rule

Close Unreal and use a real Development Editor build after changes that affect:

- reflected declarations;
- module registration;
- Build.cs dependencies;
- shader-directory registration;
- generated headers;
- plugin/module load topology;
- changes for which Live Coding cannot safely reconstruct type/module state.

Live Coding is a convenience for compatible function-body iteration, not proof that a reflected/module change is valid.

### Rider evidence rule

Rider inspection is excellent discovery evidence. Runtime behavior still requires UE-side proof.

"Rider finds a Blueprint reference" proves discoverability/reachability, not that the gameplay path executed.

---

# 6. Always-available decision and engineering services

These are canonical surfaces, not occasional experiments:

### Jev

Use [`JEV_CANONICAL_WORKFLOW.md`](JEV_CANONICAL_WORKFLOW.md) whenever the missing ingredient is judgment rather than deterministic validation.

Jev should receive a bounded state packet, authored candidate set and explicit criteria. Preserve the selected option, `source=jev-live`, confidence/distribution and reason. The relevant owner then executes the choice and deterministic evidence verifies it.

### RiderLink

RiderLink is the preferred focused live-editor bridge for native automation tests when one healthy editor session is the intended context. Use the test already defined in source; do not create another RPC/test harness merely because an agent cannot find the RiderLink path.

RiderLink proves the focused test. Process-death/relaunch, real player input and packaged behavior remain separate acceptance classes.

### Qodana

The tracked `qodana.yaml` is the canonical static-analysis configuration:

- `ide: QDJB`;
- `qodana.recommended`;
- project-owned C++/shader scope with generated/vendor/plugin exclusions;
- repository failure thresholds.

Run the configured Qodana gate as a normal pre-review layer for relevant native/shader changes. Do not replace it with a new analyzer profile unless the tracked configuration itself is the task.

Qodana is static evidence, not runtime evidence.

---

# 7. One editor, one mutation surface

For editor-mutating work:

- one Unreal Editor instance;
- Monolith on the canonical endpoint;
- one writer at a time;
- inspect before mutate;
- mutate narrowly;
- compile/assert/save;
- read back the result.

Do not start a second editor because the first is inconvenient. Do not run two MCP mutation surfaces on the same project.

For graph edits, preserve the established Recipe 15 shape:

```text
fingerprint -> mutate -> compile -> assert -> save
```

For spatial edits:

```text
scene_context_cycle.begin()
-> inspect
-> bounded change
-> scene_context_cycle.end()
-> compare / falsify
-> owner viewport judgment
```

---

# 8. Evidence ladder — say exactly what was proven

Use these labels carefully:

### SOURCE / TOOL PROVEN
The script/source/importer/compiler works offline or structurally.

### EDITOR PROVEN
The asset/graph/table exists and reads back correctly in the editor.

### LIVE PIE PROVEN
The intended actor/system executes in PIE with assertions/receipts and no disqualifying runtime errors.

### RESTART PROVEN
State survives an actual editor process exit/relaunch.

### PACKAGED PROVEN
The behavior survives packaged executable execution/restart.

Never promote a claim above its evidence.

Screenshots are presentation evidence unless paired with assertions that prove the behavior being claimed.

---

# 9. Agent handoff contract

When handing work to another agent, provide:

- repo + exact branch/head;
- current status authority: `CURRENT_STATE.md`;
- the canonical owner seam;
- exact entry tool/command;
- explicit files allowed to change;
- explicit files/systems forbidden;
- expected evidence;
- stop condition;
- whether deletion is authorized;
- whether editor mutation is authorized.

Do not send an agent a vague mission like "improve procedural generation." Send it a bounded existing lane such as:

> Author a new World Compiler recipe using the current schema; do not change compiler code unless validation proves the schema cannot express the authored requirement. Compile offline, apply through the existing UE driver, run scene-context before/after, and attach the proof JSON.

---

# 10. Fast recipes

## A. New musical environment slice

1. Inspect `CURRENT_STATE.md` + World Compiler contract.
2. Create/modify `recipes/<slice>.v1.json`.
3. Validate.
4. Compile.
5. Run `Tools/test_world_compiler.py` if compiler/schema changed.
6. Begin scene-context cycle.
7. Apply with the existing UE driver.
8. End scene-context cycle.
9. Save/reload/count/capture.
10. Update status only if the evidence rung changed.

## B. New Houdini-generated environment asset

1. Search `Tools/Houdini/` for the nearest existing family.
2. Extend it rather than making an isolated scratch script.
3. Run with Hython.
4. Produce deterministic manifest.
5. Promote the resulting curated asset through the normal UE import/content lane.
6. Place/compose via authored World Compiler/PCG/level workflow.
7. Prove in UE.

## C. New Rokoko take

1. Retarget to the established Melusina target rig.
2. Export root-motion FBX without duplicate `root` node naming.
3. Put it in the expected audit/re-export lane.
4. Run the guarded importer.
5. Check the import JSON and centimetre probe.
6. Bind into the existing state/ABP owner.
7. Match rate scale to measured motion if needed.
8. PIE proof.

## D. UE C++ change

1. Find the existing owner seam in Rider.
2. Search usages / Blueprint references before adding API.
3. Ask Jev only if a bounded implementation/test strategy decision remains ambiguous.
4. Make the smallest native change.
5. Run the tracked Qodana profile on the relevant native/shader scope.
6. Close editor for reflected/module changes and build Development Editor.
7. Use RiderLink for the smallest focused live-editor automation test when appropriate.
8. Execute the required UE runtime proof.
9. Add restart/packaged evidence when the acceptance gate requires it.
10. Attach logs/receipts and update `CURRENT_STATE.md` only when status changed.

---

# 11. VFX / Niagara - Monolith Niagara lane

The gap here is not missing actions: the plugin registers **129** Niagara
actions and the project uses ~22 of them across ~42 scripts. The gap is
discoverability, governance and reliability:

- Read `Docs/AGENT_MCP_SURFACES.md` (Niagara section) for the grouped
  representative list; the full list is `monolith_discover(namespace="niagara")`.
- `specs/mcp_tool_policy.v1.json` declares all 129 as
  `niagara_query.<action>` (reads `none`, mutations `editor`); default is
  `deny`, so an undeclared action is refused.
- Verify the surface before and after any change:
  `python Tools/verify_niagara_surface.py` (static) and
  `python Tools/verify_niagara_surface.py --live` (one editor, :9316).
- Ecosystem-level audit of shipped systems:
  `python Tools/niagara_ecosystem_audit.py [--contract]`.
- Reliability limits that are NOT fixed by this lane:
  `preview_system` renders black for mist-type systems; the driver divide-by-
  zero in `CURRENT_STATE.md` (line ~1959); five renderer bindings report
  `ok:false / materials_bound:0`. These are separate, content-driven fixes.
- Do NOT fork the plugin for WISHLIST items (stateless-emitter authoring,
  GPU read-back, scalar-field DI bulk fill) unless a real asset requires it;
  fix docs/policy/verifier first, then one concrete blocker at a time.
- Niagara promotion to the capability surface requires PIE-proven visual
  evidence; the SDF-vs-NS split remains an owner decision.

# 12. Things agents should stop doing

- rebuilding already-proven systems because an old handoff says "TODO";
- treating old branches as authority;
- creating a new Python framework when a canonical tool exists;
- using stale counts from historical docs as current state;
- confusing DCC success with game-runtime success;
- using manual FBX import instead of the guarded Rokoko importer;
- using Houdini as a runtime world authority;
- using Live Coding as proof of reflected/module changes;
- skipping World Compiler recipes and hand-placing procedural content in code;
- adding a second save/combat/UI/audio/world compiler owner;
- writing a new status document instead of updating `CURRENT_STATE.md`.

The productive default is now:

**author content -> use canonical tools -> verify at the correct evidence rung -> ship -> stop.**
