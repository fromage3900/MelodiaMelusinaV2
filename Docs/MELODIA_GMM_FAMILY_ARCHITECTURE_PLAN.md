# Melodia Studio + GMM Family Architecture Plan

> Status: **Planning / foundation phase**  
> Owner: shared Blender + Unreal tooling lane  
> Last reviewed: 2026-07-12

## 1. Purpose

Melodia Studio (Blender) and Grandmaster Melodia Melusina (GMM, Unreal) are two application adapters for one project-production family. They should share vocabulary, manifests, validation rules, style identity, and handoff contracts without pretending that Blender Geometry Nodes and Unreal PCG/Blueprint systems are the same runtime.

- **Melodia Studio** is the authoring, geometry-design, kitbash, character, ornament, and presentation side.
- **GMM** is the Unreal integration, gameplay, PCG, material, runtime, audit, and portfolio-capture side.
- **The project contract** is the stable layer between them: versioned JSON manifests, asset-role vocabulary, coordinate rules, provenance, validation reports, and generated handoff artifacts.

The goal is not a large rewrite. The goal is to make both systems start from a small, explicit core and expand through compatible capability modules.

## 2. Current truth

### Blender / Melodia Studio

Implemented or substantially present:

- `deploy/surreal_architecture_gen.py` addon host and `deploy/surreal_arch/` package.
- `deploy/surreal_arch/melodia_gn/` scaffold with primitives, profiles, math, effects, ornaments, music, castle structures, stack, and bake helpers.
- Melodia GN routing in `deploy/surreal_arch/integration.py`.
- Collection-property modifier stack registration and an N-panel stack panel.
- Blender-to-UE `.world.json` export path under `deploy/surreal_world/`.
- Blender 5.1 stage and Live Link documentation.

Still unverified or incomplete:

- Live Blender 5.1 registration and end-to-end GN generation after the latest changes.
- Actual Blender modifier reordering in the stack operator.
- Applying the stack `enabled` flag to viewport/render visibility.
- Baked `melodia_gn_library.blend` availability and load verification.
- Full world-manifest export → Unreal import verification.

### Unreal / GMM

Implemented or substantially present:

- `Content/Python/gmm/` package with game, Melodia, Melusina, PCG, NPC, MCP, and daemon lanes.
- 242 focused GMM unit tests passing when run with `PYTHONPATH=Content/Python`.
- Daemon task runner with smoke gates, staged output, state persistence, and task cycling.
- UE-side PCG standards and style/genome systems.
- Unreal material, capture, portfolio, and audit tooling.
- A working MelodiaCore plugin source tree, although the project currently disables the source-only plugin until it is built.

Still unverified or incomplete:

- A stable GMM core contract mirroring the Blender addon vocabulary.
- A shared manifest schema consumed by both adapters.
- UE import of the Blender world manifest under current project paths.
- GMM-side geometry capability registry and deterministic preview/test stage.
- Daemon runtime cleanup and lifecycle policy for PID files and `_staging/gmm_daemon/`.
- Unreal/MCP live validation in the current environment.

## 3. Target architecture

```text
                         Project Contract Layer
       manifests / roles / style IDs / units / provenance / gates
                              │              │
                 ┌────────────┘              └────────────┐
                 ▼                                         ▼
       Melodia Studio Adapter                       GMM UE Adapter
       Blender 5.1                                   Unreal 5.8
       GN + mesh authoring                            PCG + materials + gameplay
       kitbash + beauty plates                        import + runtime + capture
                 │                                         │
                 └────────────── shared project ───────────┘
                              assets / audits / exports
```

### The contract layer must own

1. **Identity**: project ID, asset ID, family, style, version, source application.
2. **Role vocabulary**: `wall`, `ornament`, `musical_ornament`, `foliage`, `hero`, `ground`, `character`, and other project roles.
3. **Style vocabulary**: stable style IDs such as `NIKKI_FLORAWISH`, `ZEN_SHRINE`, `BAROQUE`, `ESCHER`, and `MELODIA_STAGE`.
4. **Units and transforms**: Blender meters/Z-up to Unreal centimeters/Z-up, with explicit matrix convention and handedness conversion.
5. **Material hints**: semantic material role and optional UE asset path; never rely only on a display name.
6. **Provenance**: source file, generator, builder version, timestamp, git revision, and generated artifact paths.
7. **Validation**: schema version, warnings, errors, counts, and pass/fail criteria.
8. **Capability declarations**: what was authored in Blender, what is expected to be rebuilt or instanced in UE, and what is presentation-only.

## 4. Proposed repository layout

```text
shared/contracts/
  melodia_project_manifest.schema.json
  melodia_style.schema.json
  melodia_asset_roles.json
  coordinate_contract.md

Content/Python/gmm/family/
  contracts.py          # typed IDs, enums, paths, units
  manifest.py           # load/write/validate shared manifests
  registry.py           # capability and adapter registry
  provenance.py         # source and generator metadata
  audit.py              # common report shape and gates
  paths.py              # project-relative path resolution

Content/Python/gmm/melodia/
  adapter.py             # UE-side Melodia capability adapter
  geometry.py            # PCG/mesh capability declarations
  import_manifest.py     # Blender world/asset manifest intake
  preview.py             # deterministic UE test-stage hooks

 deploy/surreal_arch/melodia_gn/
  core.py                # Blender GN primitives and safe node helpers
  registry.py            # Blender capability registry; new file
  manifest.py            # Blender-side export helpers; new file
  stack.py               # Blender modifier stack UI and execution
  bake.py                # GN library generation/load

 deploy/surreal_world/
  export.py              # world manifest producer

 Content/Python/
  import_melodia_manifest.py
  audit_melodia_contract.py
```

The exact folders can be adjusted to match existing conventions, but the responsibilities should remain separated. Runtime adapters should not contain the contract schema itself.

## 5. Core scaffold: first implementation slice

### 5.1 Shared manifest v1

Create a minimal `melodia_project_manifest` contract with these required fields:

```json
{
  "format": "melodia_project_manifest_v1",
  "project_id": "BS_GodFile",
  "asset_id": "ornament_vault_ribs",
  "source": {
    "application": "blender",
    "generator": "melodia_gn",
    "generator_version": "0.1.0",
    "git_revision": "..."
  },
  "style_id": "MELODIA_STAGE",
  "units": "meters",
  "coordinate_system": "blender_z_up",
  "roles": ["musical_ornament", "hero"],
  "instances": [],
  "material_hints": [],
  "validation": {
    "status": "passed",
    "errors": [],
    "warnings": []
  }
}
```

Required design rules:

- Paths inside manifests are project-relative or Unreal asset paths; never machine-specific absolute paths.
- Every producer writes a schema version.
- Consumers reject unknown major versions and warn on unknown minor versions.
- Counts and validation results are generated from the artifact, not manually entered.
- The manifest describes intent and provenance; it does not attempt to serialize Blender or Unreal runtime objects.

### 5.2 Shared role and style registry

Start with a small registry and expand deliberately:

- `wall`
- `floor`
- `roof`
- `ornament`
- `musical_ornament`
- `foliage`
- `ground`
- `hero`
- `character`
- `vfx`

Initial style IDs should map to existing project vocabulary rather than inventing aliases. The registry should support:

- display label
- default material hint
- allowed source applications
- expected export mode (`mesh`, `instance`, `pcg`, `presentation_only`)
- validation requirements

### 5.3 Capability registry

Both adapters should expose capabilities in the same shape:

```text
capability_id
family
source_application
builder/module
input contract
output contract
preview method
validation gate
status: scaffolded | implemented | verified | blocked
```

Initial cross-application capability set:

| Capability | Blender | Unreal | First status |
|---|---|---|---|
| circular array | GN builder | PCG/ISM adapter | scaffolded |
| instance on spline | GN builder | spline/PCG adapter | scaffolded |
| ornament frame | GN builder | mesh/PCG intake | scaffolded |
| musical note head | GN builder | UE mesh/material intake | scaffolded |
| castle tower | GN builder | PCG composition | scaffolded |
| style manifest export | new | new | planned |
| deterministic preview audit | Blender stage | UE test stage | planned |

A capability is not “implemented” until it has a deterministic test fixture and a report proving the output contract.

## 6. Integration workflow

### Blender → Unreal

1. Author or generate geometry in Melodia Studio.
2. Run Blender-side validation.
3. Export a versioned manifest plus mesh/FBX/world artifacts.
4. Place artifacts in a project-relative handoff directory.
5. GMM validates the manifest before importing anything.
6. GMM imports or materializes assets using role/style hints.
7. UE-side validation checks paths, counts, transforms, materials, and PCG/ISM output.
8. Portfolio/capture tooling consumes the same manifest and audit report.

### Unreal → Blender

1. GMM exports a scene/style request manifest containing role targets, style ID, dimensions, and material hints.
2. Melodia Studio consumes the request as an authoring queue.
3. Blender generates or adjusts assets and returns a manifest with provenance.
4. GMM revalidates the returned artifact before import.

### Live Link boundary

Live Link remains an interactive convenience channel, not the source of truth. Durable handoff uses manifests and files. This makes work reproducible when either Blender or Unreal is closed, restarted, or unavailable.

## 7. Validation gates

### Contract gate

- JSON schema validates.
- Major/minor format is supported.
- Required IDs are present and stable.
- No machine-specific absolute paths.

### Geometry gate

- Instance count is within declared range.
- Bounds are nonzero and within expected scale.
- Transform matrix has finite values.
- Mesh/material role references resolve or are explicitly marked unresolved.

### Blender gate

- Addon registers and unregisters cleanly.
- GN group exists and has the expected interface.
- Modifier stack order matches the exported stack order.
- Enabled items affect viewport/render state.
- Exported manifest is readable outside Blender.

### Unreal gate

- Importer accepts the manifest.
- Asset paths resolve or produce explicit actionable errors.
- Imported transforms match expected tolerance.
- PCG/ISM generation is verified in a deterministic test stage.
- Material hints resolve to the intended canonical family.

### Portfolio gate

- Provenance links back to source and generator version.
- Render/capture output references the same asset ID.
- Audit report is generated beside the package.
- A failed validation cannot be reported as a successful handoff.

## 8. Phased delivery plan

### Phase 0 — Documentation and contract lock

- Make this document canonical from `DOC_INDEX.md`.
- Correct stale claims in `AGENTS.md`, `CURRENT_STATE.md`, and `NEXT_HIGHEST_LEVERAGE_TASK.md`.
- Decide the shared handoff root and artifact retention policy.
- Add schema version and status vocabulary before adding more builders.

### Phase 1 — GMM foundation scaffold

- Add `gmm.family` contract, registry, paths, provenance, and audit modules.
- Add unit tests using only standard Python; no `unreal` import at module import time.
- Add a sample manifest fixture and a CLI validator (`Content/Python/validate_melodia_manifest.py`).
- Add an adapter registry with `blender` and `unreal` entries.
- Treat daemon `completed` as a legacy alias for `generated`; application and verification must be recorded separately.

### Phase 2 — Melodia Blender adapter

- Add Blender-side manifest export for one capability: `musical_ornament`.
- Add deterministic GN interface inspection.
- Fix stack modifier ordering and enabled-state behavior before declaring the stack verified.
- Add a Blender smoke script that registers, builds one group, attaches it, exports, and unregisters.

### Phase 3 — GMM UE adapter

- Add `import_melodia_manifest.py` with dry-run mode.
- Resolve role/style material hints through canonical registries.
- Materialize one imported capability in a deterministic UE test stage.
- Write an audit report with imported count, bounds, materials, and unresolved references.

### Phase 4 — Bidirectional project workflow

- Add UE request manifests for geometry/style tasks.
- Add Blender intake queue and completion manifests.
- Connect Live Link as optional interactive feedback, while manifests remain durable truth.
- Add a single project handoff command that validates both sides without starting either application when possible.

### Phase 5 — Capability expansion

Expand one vertical slice at a time:

1. circular array
2. instance on spline
3. ornament frame/panel
4. musical note/staff family
5. castle tower/portico
6. effects and magic modifiers
7. full world composition

Each slice must include Blender builder, GMM adapter, fixture, manifest, audit, and documentation before the next slice begins.

**Update (2026-08-12):** `boolean_difference` and `procedural_window` are now scaffolded/implemented in the Procedural Modeling Toolkit and the `gmm.geometry` contract. They mirror the Blender `GeometryNodeMeshBoolean` DIFFERENCE workflow used by `deploy/surreal_greybox/primitives.py` and are ready for closed-editor build verification.

## 9. Highest-leverage immediate tasks

1. **Create the shared contract package and fixture.** This is the foundation for every future bridge and prevents divergent path/style vocabularies.
2. **Fix the Melodia GN stack correctness issues.** Actual modifier order and enabled-state behavior are prerequisites for trustworthy exports.
3. **Add a pure-Python GMM manifest validator.** It should run outside Unreal and make daemon validation useful even when UE/MCP is offline.
4. **Add a dry-run UE importer.** Validate paths, roles, units, and transforms without mutating the project.
5. **Verify one vertical slice end-to-end.** Use `musical_ornament` because it already has Blender-stage and UE packaging workflows.
6. **Update daemon policy.** Separate generated tick evidence from source deliverables and ensure every daemon reports its last successful validation gate.
7. **Only then expand GMM builders.** Port contracts and test fixtures before porting large amounts of geometry logic.

## 10. Non-goals and guardrails

- Do not make Blender and Unreal share implementation code that depends on `bpy` or `unreal`.
- Do not use Live Link as the only persistence or handoff mechanism.
- Do not port the entire 15k-line Blender addon to Unreal in one pass.
- Do not create per-script role/style aliases without updating the registry.
- Do not mark a capability verified from `py_compile` alone.
- Do not commit daemon tick output or PID files until their retention policy is explicit.
- Keep application-specific art direction and runtime behavior in the owning adapter.

## Canon architecture extension — run and companion contracts

The shared contract layer must add two planned contracts:

- **Expedition run:** seed, doorway ID, room graph, encounter pool, blessings/burdens, Dissonance tier, results, and reward. Same seed must reproduce the declared run.
- **Companion:** role, source/UE asset IDs, control mode, resonance contribution, availability state, and follow/flight/battle validation status.

Planned capabilities are `companion_resonance`, `companion_flight_scout`, `dissonance_profile`, and `recursive_expedition`. Each is unimplemented until it has a deterministic fixture and an Unreal validation report.
