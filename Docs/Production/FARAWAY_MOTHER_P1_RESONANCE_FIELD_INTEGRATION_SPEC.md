# Faraway Mother P1 Resonance-Field Integration Spec

**Status:** durable production integration spec; **not proof of implementation**  
**Target:** `/Game/EnvSandbox/Monoliths/FarawayMother/Prototype/LV_FarawayMother_Prototype`  
**Game/runtime authority:** `fromage3900/MelodiaMelusinaV2`  
**TouchDesigner implementation:** `fromage3900/MelodiaTouchDesigner`  
**Primary P1 gate:** `Docs/P1_TASK_LEDGER.json -> FARAWAY_MOTHER_P1_PRESENT`

## 1. Goal

Complete the P1 Faraway Mother slice by converging the systems that already exist instead of adding another framework.

The intended result is one player-facing musical event in which the same Faraway Mother field is visible across the level:

```text
authoritative UE musical/game state
        |
        | existing semantic OSC :9000
        v
TouchDesigner / Embody
  interprets the live musical state
  over the Faraway Mother static field
        |
        | presentation-only OUT_SHOW_FIELD
        v
Unreal
  fabric WPO / material response
  + seam/particle response
  + Heart Gate / route presentation
```

Houdini/Hython provides the deterministic **static spatial substrate**. TouchDesigner provides the **live presentation modulation**. Unreal remains the only gameplay/world-state authority.

The memorable P1 image is:

> A successful Heart Gate phrase causes one coherent standing-wave seam to propagate across the draped fabric landscape: the mountain pleats breathe, the seam particles find the same nodal corridor, and the Heart Gate/path presentation resolves along that field. The field is mathematically aligned across Hython, TD, PCG and UE rather than approximated independently in each system.

## 2. What already exists — do not rebuild it

### Unreal / game repo

Use the existing systems and paths:

- Faraway Mother level: `LV_FarawayMother_Prototype`.
- PCG architecture: `Docs/PCG/FARAWAY_MOTHER_PCG_SYSTEM_ARCHITECTURE.md`.
- Deterministic field/biome generator: `Tools/PCG/build_faraway_mother_pcg_ecosystem.py`.
- Generated manifest: `specs/pcg/faraway_mother_pcg_manifest.v1.json`.
- Faraway Mother level staging: `Content/Python/faraway_mother_pcg_assembly.py`.
- Existing cymatic material staging/audit: `Content/Python/melodia_faraway_mother_cymatic_integration.py`.
- Existing World Field channels: `WorldField.Tension`, `WorldField.Resonance`, `WorldField.Moisture`, `WorldField.FilterFlow`.
- Existing Chladni basis in the Faraway Mother PCG generator: mode `(3,5)`.
- Existing Heart Gate challenge: `challenge.mother_heart_gate`.
- Existing semantic music lane / PhraseBus: UDP `:9000`.
- Existing audio/cymatic presentation owners: `UMelodiaAudioReactivePresentationSubsystem`, `UMelodiaCymaticsSubsystem`, `UMelodiaCymaticsWriterSubsystem`, `MPC_Melodia_Palette`, `MPC_Cymatics_Driver`.
- Existing World Compiler remains the authored world-composition authority. This work must not become a second compiler.

### Houdini / Hython

Use and extend the current families:

- `Tools/Houdini/vdm_fabric_mountains/vdm_fabric_baker.py`.
- `Docs/Houdini/FARAWAY_MOTHER_DRAPE_SPEC_2026-09-01.md`.
- `Tools/Houdini/copernicus/`.
- `Tools/Houdini/copernicus/copernicus_cymatic_parallax.py`.

Hython is an **offline deterministic forge** for geometry, masks, field textures and manifests. It does not mutate the live UE world and does not become runtime authority.

### TouchDesigner repo

The TD side already defines the exact conceptual slot needed here:

- Embody/Envoy is the canonical TD tooling surface.
- `/project1/performance/scenes/world_field` is the intended field scene.
- Scene outputs already include `OUT_FIELD`.
- Stable show output already names `OUT_SHOW_FIELD`.
- Existing semantic input is reused; no second OSC listener.
- Spout is explicitly optional until the UE receive side is proven.

Do not vendor TD content into the game repo.

## 3. The actual missing proof

Most of the architecture already exists. The missing proof is narrowly:

> **Can one deterministic Faraway Mother spatial field be authored offline, modulated live in TD, returned to Unreal as a presentation-only texture, and sampled coherently by multiple UE consumers?**

The first decisive runtime canary is therefore:

```text
TD OUT_SHOW_FIELD -> UE texture/render target -> debug plane
```

Only after that succeeds should the field feed multiple world consumers.

No work in this spec may be called LIVE PROVEN until that return path and the selected UE consumers are observed in PIE.

## 4. Field ownership model

There are two related but distinct field layers.

### 4.1 Static authored field — Hython / PCG source

This is deterministic spatial data tied to Faraway Mother geography.

Recommended first field pack:

`T_FarawayMother_StaticField_RGBA.exr`

- **R = WorldField.Tension** — normalized 0..1.
- **G = WorldField.ResonanceBase** — normalized standing-wave magnitude / nodal response derived from the existing `(3,5)` Chladni basis.
- **B = WorldField.Moisture** — normalized 0..1.
- **A = ResonantSeamWay mask** — 1 on/near the nodal corridor, 0 away from it.

Optional second pack when needed:

`T_FarawayMother_FilterFlow_RG.exr`

- **R/G = normalized FilterFlow vector** in world XY.
- B/A remain reserved until a real consumer needs them.

The static pack is **source presentation data**, not save/gameplay state.

### 4.2 Live presentation field — TouchDesigner

TD receives the static field plus the existing semantic music state and produces a visual interpretation:

`OUT_SHOW_FIELD` RGBA:

- **R = VisualResonance** — where resonance is visibly active now.
- **G = VisualTensionDelta** — presentation modulation around the authored tension field.
- **B = VisualPhaseFlow** — beat/motif-phase motion used for directional shimmer/trails.
- **A = ActiveMask** — valid/active presentation region, decaying safely to zero when signal is absent.

These values are **presentation-only**. TD never writes `WorldField.Tension` as gameplay truth, never unlocks traversal, never marks harmony valid, and never writes save state.

## 5. Coordinate contract

The field must be spatially aligned once, then reused everywhere.

Faraway Mother current bounds from the PCG generator:

```text
world X: -400000 .. +400000 uu
world Y: -400000 .. +400000 uu
field UV: 0 .. 1
```

Mapping:

```text
U = saturate((WorldX + 400000) / 800000)
V = saturate((WorldY + 400000) / 800000)
```

Hython, TD debug previews, UE material sampling and Niagara sampling must all use the same bounds/orientation.

The first field manifest written by Hython must record:

- schema/version string local to the manifest;
- source game commit SHA;
- Houdini version;
- seed;
- Chladni `ModeN/ModeM`;
- world bounds;
- resolution;
- channel meanings;
- output paths;
- hashes;
- generation timestamp;
- whether the cook was real Hython or dry-run/scaffold.

Recommended evidence location:

`Saved/Audit/houdini_faraway_mother/resonance_field_manifest.json`

Do not create a new durable schema file until the canary proves this manifest needs to become a reusable contract.

## 6. Hython work — static field and drape substrate

### 6.1 First principle

Do **not** reimplement Faraway Mother field mathematics in a second private script if the existing generator can be reused.

Prefer importing/reusing the pure-Python functions in:

`Tools/PCG/build_faraway_mother_pcg_ecosystem.py`

especially:

- `evaluate_chladni()`;
- `evaluate_tension()`;
- existing bounds and biome definitions.

This keeps the Hython rasterized field mathematically consistent with the PCG manifest.

### 6.2 Required Hython outputs

Minimum P1 field canary:

1. rasterize the static RGBA field pack at 1024²;
2. write a manifest with hashes and coordinate contract;
3. generate a debug contact sheet/preview showing R/G/B/A;
4. verify the ResonantSeamWay alpha mask intersects the same nodal corridors used by the PCG manifest.

Then, only if needed for the hero slice:

5. validate/fix the existing VDM fabric baker against the current Houdini license/tool availability;
6. produce one hero ridge/pleat source or VDM that consumes the same tension/resonance basis;
7. preserve Nanite/LOD/material import contracts already documented for Faraway Mother.

The Hython task is complete when another process can consume the outputs without reopening Houdini.

### 6.3 Candidate command sequence

```powershell
python Tools/PCG/build_faraway_mother_pcg_ecosystem.py --points-per-biome 30
python Tools/PCG/build_faraway_mother_pcg_ecosystem.py --verify

# Actual Hython command is to be finalized by Muse after auditing the current tool.
# Extend the existing vdm_fabric_mountains family rather than creating a second Faraway framework.
& "<Houdini22>/bin/hython.exe" Tools/Houdini/vdm_fabric_mountains/<bounded_field_tool>.py
```

If the current `vdm_fabric_baker.py` cannot truthfully produce the required outputs, fix or extend that family and record the limitation. Do not claim its existing scaffold comments prove a successful cook.

## 7. TouchDesigner work — live Faraway Mother field

Gemini works in **`fromage3900/MelodiaTouchDesigner`**, not the game repo.

### 7.1 Extend the existing scene

Use:

`/project1/performance/scenes/world_field`

Do not create another root show system.

The scene should consume:

- current `semantic_bus`;
- static Faraway field texture(s);
- reset;
- deterministic seed.

At minimum, map:

- `beat_phase` / `beat_pulse` -> phase motion and pulse strength;
- `amplitude` -> field strength;
- `harmony_tension` -> presentation tension delta;
- `harmony_resolved` -> coherent-field transition;
- `world_response_strength` -> total world-scale visibility.

The scene must emit:

- `OUT_MAIN`;
- `OUT_ALPHA`;
- `OUT_FIELD`;
- `OUT_DEBUG`.

The show output must expose the field through the existing `OUT_SHOW_FIELD` name.

### 7.2 Fail-soft behavior

If OSC disappears or the semantic state is invalid:

1. hold briefly only if already visually stable;
2. decay `ActiveMask` and dynamic channels toward zero;
3. keep the static field preview available in debug;
4. never jump to maximum intensity;
5. reset feedback deterministically.

### 7.3 Deterministic replay

Build/extend a replay fixture that emits the same semantic channel names as live mode.

The P1 test replay should include:

1. QUIET;
2. rising ROOT;
3. INTERVAL/tension;
4. successful RESOLUTION;
5. WORLD response;
6. AFTERIMAGE decay.

This lets TD prove the field before live PIE is available and makes visual regressions reproducible.

## 8. Unreal runtime return path

### 8.1 Gate zero — prove the receiver

Before changing production materials, prove:

```text
TD OUT_SHOW_FIELD
    -> chosen local GPU/image transport
    -> UE texture/render target
    -> debug plane/material in LV_FarawayMother_Prototype
```

Preferred first route is the existing Spout direction **only if a compatible UE receive path is actually present/proven**.

If no receiver exists:

- record that fact;
- choose the smallest reversible receive solution;
- do not silently introduce a large runtime dependency;
- keep the Hython static field + TD replay work valid even if the live return path is parked.

A transport choice is not accepted until it is visibly proven in the actual project.

### 8.2 Alignment proof

Render a diagnostic field with:

- corner markers;
- central cross;
- one known ResonantSeamWay stripe.

Verify those markers land at the expected world coordinates in UE.

Do not proceed to artistic consumers while the field is mirrored, rotated or offset.

### 8.3 P1 artistic consumers

After receiver + alignment pass, wire the same live field into **three bounded consumers**.

1. **Fabric mountain material/WPO**
   - extend the existing Faraway fabric/WPO material path;
   - use VisualResonance / VisualTensionDelta for small-to-medium presentation modulation;
   - Hython-authored geometry/VDM remains the structural source;
   - do not create unstable kilometer-scale runtime deformation that changes collision/gameplay truth.

2. **Seam / atmospheric Niagara**
   - audit for an existing Faraway-compatible Niagara system first;
   - sample the same field so particles accumulate/follow the ResonantSeamWay rather than using an unrelated noise field;
   - a new scoped Niagara System is acceptable only if no existing consumer fits; no new Niagara framework.

3. **Heart Gate / route presentation**
   - the Heart Gate challenge remains authoritative in UE;
   - when UE reports the existing successful world-response state, the TD field may visually resolve along the seam corridor;
   - the TD field never unlocks the gate or grants the mantle;
   - field absence must degrade to the normal UE presentation without blocking gameplay.

## 9. P1 hero beat

The target proof is one short authored sequence:

```text
Player enters ResonantSeamWay
-> authored Faraway static field already defines the nodal corridor
-> Heart Gate rhythm challenge begins
-> UE remains authoritative for rhythm/harmony
-> live semantic state goes to TD on :9000
-> TD modulates the static field
-> successful resolution produces coherent OUT_SHOW_FIELD
-> UE receives the field
-> fabric pleats/emissive respond
-> seam particles trace the same corridor
-> Heart Gate/path presentation resolves
-> TD afterimage decays
-> gameplay remains valid if TD is disconnected
```

This proves the actual thesis:

> **Fabric is Geography; music changes how that geography is perceived, not who owns the game state.**

## 10. Execution order

### Phase A — read-only convergence audit

Before mutation, verify exact current paths/assets in both repos.

Output should be a concise task/PR note, not another handoff document.

Questions:

- Does the PCG manifest currently generate and validate?
- Which Faraway material master/function currently owns fabric WPO?
- Which Niagara consumer is safest?
- Is there any UE-side Spout/TouchEngine/other field receiver already installed but undocumented?
- Does `/project1/performance/scenes/world_field` already exist in the live TD graph or only in the design contract?
- Which static field format can both TD and UE ingest without conversion churn?
- Does the current Houdini license permit the desired real cook/export?

### Phase B — Hython static field proof

- generate field pack + manifest + preview;
- verify against PCG nodal positions;
- no Unreal mutation yet.

### Phase C — TD deterministic field proof

- import/pin the static field in the TD repo;
- build/finish the existing `world_field` scene;
- replay QUIET -> WORLD -> AFTERIMAGE;
- capture `OUT_FIELD` + `OUT_DEBUG`;
- no claim of UE integration yet.

### Phase D — UE return-path canary

- one editor;
- one chosen writer;
- prove field receive on a debug plane;
- prove coordinate alignment;
- record failure/latency/FPS honestly.

### Phase E — three-consumer hero slice

- fabric;
- Niagara;
- Heart Gate/path presentation.

### Phase F — PIE evidence and degradation

Prove both:

1. TD connected: coherent field response.
2. TD disconnected: gameplay remains correct and presentation fails soft.

Only then may `CURRENT_STATE.md` be updated with a live proof claim.

## 11. Muse mission — game repo + Hython + UE integration lead

**Repository:** `fromage3900/MelodiaMelusinaV2`

### Mission

Converge the existing Faraway Mother PCG, Hython and UE presentation lanes into one field-consumption path without adding a second world compiler, audio writer, gameplay authority or editor bridge.

### Required behavior

1. Read:
   - `AGENTS.md`;
   - `CURRENT_STATE.md`;
   - `Docs/Production/AGENT_PRODUCTION_PLAYBOOK.md`;
   - `Docs/PCG/FARAWAY_MOTHER_PCG_SYSTEM_ARCHITECTURE.md`;
   - this spec;
   - `Docs/Houdini/FARAWAY_MOTHER_DRAPE_SPEC_2026-09-01.md`;
   - `Docs/TouchDesigner/MELODIA_TD_AE_CROSS_REPO_CONTRACT_2026-09-08.md`.

2. Perform the Phase A audit before writes.

3. For Hython:
   - reuse the current Faraway PCG field math;
   - extend the existing `Tools/Houdini/vdm_fabric_mountains/` / Copernicus families;
   - emit deterministic field texture(s), manifest and preview;
   - record real vs scaffold/dry-run state;
   - do not mutate UE from Hython.

4. For UE:
   - identify/prove the smallest reversible TD field receiver;
   - use one editor and one mutation writer;
   - use `scene_context_cycle` around spatial edits;
   - prove alignment on a debug target before production consumers;
   - wire the field into exactly the three P1 consumers in §8.3;
   - preserve existing MPC/audio writers and Heart Gate gameplay ownership.

5. Evidence:
   - Hython manifest + hashes;
   - static-field channel preview;
   - TD-field receiver screenshot;
   - coordinate-alignment screenshot;
   - PIE before/resolution/afterimage stills or short capture;
   - TD-disconnected fallback proof;
   - exact commit SHAs and field transport used.

### Muse stop conditions

Stop and report rather than inventing a parallel system if:

- no reversible TD->UE texture route can be made to work;
- current material ownership cannot be identified;
- a proposed change requires a second MPC/audio/world-state writer;
- the Hython output is still a scaffold and cannot produce truthful files.

A parked return-path canary is preferable to fake integration proof.

## 12. Gemini mission — TouchDesigner / Embody field lead

**Repository:** `fromage3900/MelodiaTouchDesigner`

### Mission

Finish the existing TD `world_field` concept as a deterministic, inspectable, fail-soft visual instrument for Faraway Mother. Do not change gameplay semantics and do not create another OSC bridge.

### Required behavior

1. Read:
   - repo `AGENTS.md`;
   - `docs/MELODIA_SHOW_SYSTEM_ARCHITECTURE_2026-09-08.md`;
   - game-side cross-repo contract;
   - this spec / supplied field manifest.

2. Use Embody/Envoy and TDN rules:
   - prefer `.tdn` for externalized networks;
   - use Envoy for live state;
   - batch repetitive operations;
   - check errors after each group;
   - do not edit `externalizations.tsv`.

3. Extend the existing performance architecture:
   - use existing semantic input;
   - use/finish `/project1/performance/scenes/world_field`;
   - do not add a second OSC listener;
   - expose `OUT_FIELD` and existing `OUT_SHOW_FIELD`.

4. Ingest the static Faraway field pack as presentation source data.

5. Build deterministic live modulation using existing semantic channels.

6. Implement the replay sequence in §7.3 and capture:
   - QUIET;
   - tension/interference;
   - RESOLUTION;
   - WORLD;
   - AFTERIMAGE;
   - debug channel view.

7. When Muse proves the UE receive method:
   - expose the field through that transport;
   - keep transport-specific nodes localized to output;
   - preserve a transport-independent `OUT_SHOW_FIELD`.

8. Evidence:
   - TDN diff;
   - zero cook errors in the touched network;
   - field channel debug capture;
   - FPS/cook-time snapshot;
   - replay capture;
   - TD commit SHA;
   - sender/output name actually used.

### Gemini stop conditions

Do not:

- change UE gameplay meanings;
- decide harmony validity;
- add another show-state authority;
- replace Embody/Envoy;
- create a second OSC listener just to make the task easier;
- hard-code workstation-only absolute paths into reusable TD logic.

## 13. Cross-agent handshake

Muse and Gemini coordinate through **small artifacts**, not source-tree copying.

Game repo provides:

- static field image(s);
- Hython manifest;
- semantic meaning / channel names;
- world bounds;
- chosen receive transport once proven.

TD repo provides:

- `OUT_SHOW_FIELD`;
- debug output;
- replay proof;
- output/sender name;
- TD commit SHA.

For each proof take, record both repository SHAs.

Neither agent should modify the other repo unless explicitly assigned to do so.

## 14. Acceptance criteria

The P1 field integration is successful when all of the following are true:

- [ ] Faraway PCG manifest validates.
- [ ] Hython produces a real deterministic static field pack and manifest.
- [ ] Static field visually matches PCG nodal/seam placement.
- [ ] TD world-field scene consumes the static pack and existing semantic bus.
- [ ] TD replay is deterministic and fail-soft.
- [ ] `OUT_SHOW_FIELD` is visibly received in UE.
- [ ] UE field orientation/alignment is proven.
- [ ] Fabric, Niagara and Heart Gate/path presentation sample the same field.
- [ ] Heart Gate gameplay truth remains UE-owned.
- [ ] No second MPC writer, World Compiler, PhraseBus, OSC semantic bridge or Niagara framework was introduced.
- [ ] TD disconnected state leaves gameplay functional.
- [ ] Evidence records both repo SHAs and the real field transport.
- [ ] Only after live proof, `CURRENT_STATE.md` is updated.

## 15. Non-goals

This task is **not**:

- a new gameplay system;
- a new save/progression authority;
- a replacement for the World Compiler;
- a replacement for `MPC_Melodia_Palette` / `MPC_Cymatics_Driver`;
- a replacement for Embody/Envoy;
- a reason to rebuild Faraway Mother from scratch;
- a reason to make runtime collision depend on TD;
- a reason to make Houdini cook during gameplay;
- a giant TouchEngine/Spout framework before one field canary works.

## 16. Definition of done for this spec

The highest-value outcome is intentionally small:

> **One Heart Gate resolution visibly drives one shared field through Faraway Mother's fabric, particles and route presentation, with the same spatial topology authored by Hython and interpreted by TD, while Unreal remains fully playable with TD turned off.**
