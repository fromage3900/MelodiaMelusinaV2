# Melodia Universe Foundry Contract

**Purpose:** durable contract for compiling a world-scale production mission from a compact World Genome plus an exported World Delta.  
**Status authority:** `CURRENT_STATE.md` remains the only statement of what is proven/live.  
**Runtime authority:** existing Unreal gameplay/save owners.  
**World authoring authority:** existing World Compiler / PCG contracts.  
**Mission dispatch:** Hermes.  
**Bounded judgment:** Jev.  

Universe Foundry is **not** a second world generator, save system, agent framework, or runtime. It is a deterministic mission compiler above the existing Melodia production spine.

## 1. Shape

```text
human intent
    |
    v
World Genome + exported World Delta
    |
    v
Tools/universe_foundry.py
    |
    | deterministic typed mission DAG
    v
Hermes
    |
    +--> Jev closed-set decision(s)
    +--> World Compiler / PCG data author
    +--> Hython forge
    +--> TouchDesigner / Embody specialist
    +--> Unreal specialist
    +--> independent verification / Echo
```

No layer above the existing owner is allowed to mutate that owner's state directly.

## 2. Inputs

### World Genome

Schema:

`specs/universe/world_genome.v1.schema.json`

A genome carries the compact authored identity needed to reconstruct and reason about a world:

- world id + deterministic seed;
- level path;
- musical identity;
- emotional arc;
- spatial bounds;
- field basis;
- current canonical content inputs;
- Jev decision points as **closed authored candidate sets**;
- acceptance proofs required before the world is considered complete.

World Zero:

`specs/universe/faraway_mother.world_genome.v1.json`

### World Delta

Schema:

`specs/universe/world_delta.v1.schema.json`

The Foundry does **not** own persistent game state.

A real production delta must be exported from the canonical Unreal gameplay/save owner and set:

```json
"source_authority": "game-save-export",
"non_authoritative_fixture": false
```

Fixtures are allowed for orchestration/replay development but can never satisfy persistence acceptance.

Committed fixture:

`specs/universe/faraway_mother.resolved_demo.world_delta.v1.json`

It is deliberately marked non-authoritative.

## 3. Mission compiler

Entry point:

`Tools/universe_foundry.py`

Validate:

```powershell
python Tools/universe_foundry.py validate ^
  --genome specs/universe/faraway_mother.world_genome.v1.json ^
  --delta specs/universe/faraway_mother.resolved_demo.world_delta.v1.json
```

Compile:

```powershell
python Tools/universe_foundry.py compile ^
  --genome specs/universe/faraway_mother.world_genome.v1.json ^
  --delta specs/universe/faraway_mother.resolved_demo.world_delta.v1.json
```

Default output:

`Saved/UniverseFoundry/<world_id>/<mission_id>/mission.json`

The mission id is content-addressed from the canonical JSON hashes of the genome and delta. Identical inputs produce the same mission id and DAG.

Schema:

`specs/universe/universe_mission.v1.schema.json`

The mission is ephemeral/generated production data, not a second task/status ledger.

## 4. Hermes contract

Hermes owns dispatch and continuity, not implementation.

For each ready mission task Hermes should:

1. read the task's smallest relevant context;
2. route it to the named specialist/existing tool lane;
3. preserve branch/head and evidence requirements;
4. wait for the task's real evidence;
5. expose only the newly-unblocked tasks;
6. never accept a producing agent's self-certification.

The mission DAG is allowed to describe work. Completion still belongs to existing Melodia evidence/Echo rules.

## 5. Jev contract

Jev tasks contain:

- a decision id;
- a question;
- an explicit candidate set;
- `closed_set=true`.

Jev may select one candidate and return source/confidence/distribution.

Jev may not:

- invent a new candidate;
- invent gameplay ids or asset paths;
- mutate Unreal;
- write World Compiler data;
- execute Hython;
- become a second PhraseBus or save owner.

The selected decision becomes context for the specialist that already owns the resulting work.

## 5b. External creative-sidecar audit pattern

External generative systems such as world models may be used as **non-authoritative ideation sidecars** only.

They sit outside the deterministic Foundry mission:

```text
Hermes/Luna bounded experiment packet
    |
    v
Jev preflight closed-set audit
    |
    v
external creative sidecar
    |
    v
captured artifacts / observations
    |
    v
Hermes/Luna authored closed candidates
    |
    v
Jev result selection
    |
    v
owner approval
    |
    v
existing World Compiler / Hython / PCG / UE owner
```

For these experiments:

- preflight candidates should normally include `PROCEED` and a hold/reject option;
- result candidates must be authored from captured evidence before Jev sees them;
- include `PARK_<SYSTEM>` when "none of these are worth carrying forward" is a legitimate outcome;
- Jev may select and audit but may not synthesize a new creative candidate;
- the external system may not write World Genome, World Delta, mission DAG, save state, or Unreal content directly;
- the producing system's output is evidence/ideation, never acceptance.

## 6. Faraway Mother World Zero

Faraway Mother is the v0.1 vertical slice because it already has:

- a real level;
- deterministic PCG/Chladni/tension math;
- PCG manifest tooling;
- Hython/Houdini fabric families;
- Heart Gate gameplay identity;
- a documented TD `world_field` target;
- a P1 resonance-field convergence spec.

The Foundry mission currently drives these phases:

```text
A  validate genome + delta
B  Jev closed-set direction
C  World Compiler / PCG authored data
D  Hython static field
E  TD world-field replay
F  UE field receiver/alignment canary
G  fabric + Niagara + Heart Gate presentation
H  real exported-delta persistence/regeneration proof
I  independent acceptance
```

If a Faraway World Compiler recipe is absent, the mission emits an explicit **data-authoring task** to create one through the existing World Compiler contract. It does not create another compiler.

## 7. Hython static-field canary

Entry point:

`Tools/Houdini/vdm_fabric_mountains/faraway_static_field.py`

It is designed for hython (or compatible Python with numpy + Pillow) and imports/cross-checks the current Faraway PCG math before writing output.

Output:

- `T_FarawayMother_StaticField_RGBA.png`;
- `T_FarawayMother_StaticField_preview.png`;
- `resonance_field_manifest.json`.

Channels:

- R = `WorldField.Tension`;
- G = `WorldField.ResonanceBase`;
- B = `WorldField.Moisture`;
- A = `ResonantSeamWayMask`.

The baker is offline source-data tooling. It never imports Unreal.

## 8. Player-history rule

The target long-term property is:

> same genome + same accepted player delta = same reconstructed world state.

The Foundry must never infer or fabricate a player consequence.

A real player-caused change enters the Foundry only after the canonical runtime exports it.

That lets specialist agents propose authored consequences around a real history while keeping the universe reproducible.

## 9. Tests

`Tools/test_universe_foundry.py` covers:

- fixture validation;
- deterministic mission compilation;
- Jev closed-set/no-mutation behavior;
- missing-recipe routing through existing World Compiler data authoring;
- fixture rejection as persistence proof;
- world-id mismatch rejection;
- mission dependency/authority validation.

Run:

```powershell
python Tools/test_universe_foundry.py
```

## 10. Non-negotiable authority rules

Never use Universe Foundry to introduce:

- a second World Compiler;
- a second save authority;
- Jev or Hermes editor mutation;
- Houdini ownership in shipping builds (live Houdini Engine cooking in the editor is canonical authoring; see `Docs/Architecture/AUDIO_REACTIVE_CANON.md` §7);
- a second OSC semantic bridge;
- a second MPC/audio writer;
- self-certified agent completion.

The Foundry exists to make the existing production spine scale to many worlds without making it less truthful.
