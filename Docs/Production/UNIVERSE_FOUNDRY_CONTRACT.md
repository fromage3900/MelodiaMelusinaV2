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

### 7.1 Canonical run (verified 2026-09-22)

```powershell
& "C:/Program Files/Side Effects Software/Houdini 22.0.368/bin/hython.exe" `
  Tools/Houdini/vdm_fabric_mountains/faraway_static_field.py
```

Defaults: `--res 1024 --seed 3900 --mode-n 3 --mode-m 5`, output `Saved/Audit/houdini_faraway_mother/`.

Expected SHA-256 (hython and CPython must both reproduce these byte-for-byte):

| File | SHA-256 |
|---|---|
| `T_FarawayMother_StaticField_RGBA.png` | `c84fc22eba156579f634bdfe93fda88a384e2b6722108c5d0178df7245d6dea7` |
| `T_FarawayMother_StaticField_preview.png` | `e01173f21ee1def0a34a24382b057e82cec06948874709541a14896b8ea4146c` |

Accept a run only if `resonance_field_manifest.json` reports `authority_crosscheck.passes=true` and the hashes above match. A hash change means the Faraway PCG math or the baker changed; re-verify and update this table in the same commit.

Evidence: `Saved/Audit/universe_foundry_hython_canon_20260922.json`.

Known gap: the manifest does not yet record the source game commit SHA (resonance-field spec §5).

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
- runtime Houdini ownership;
- a second OSC semantic bridge;
- a second MPC/audio writer;
- self-certified agent completion.

The Foundry exists to make the existing production spine scale to many worlds without making it less truthful.
