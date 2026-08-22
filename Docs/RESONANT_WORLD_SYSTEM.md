# Resonant World — Melodia Melusina's answer to Minecraft

**Status:** prototype contract and design spine  
**Owner:** World puzzle / PCG layer  
**Generator:** `Content/Python/resonant_world_generator.py`  
**Version:** `resonant_world_v1`  
**Asset atlas:** `Content/Python/resonant_world_asset_atlas.py`  
**Asset constellation:** `Content/Python/resonant_world_asset_constellation.py`
**Movement composer:** `Content/Python/quantum/resonant_movement_ranker.py`
**Score composer:** `Content/Python/resonant_world_score.py`
**PCG adapter:** `Content/Python/resonant_world_pcg_adapter.py`
**Phrase bridge:** `Content/Python/resonant_world_phrase_bridge.py`
**Wardrobe bridge:** `Content/Python/resonant_world_wardrobe_bridge.py`
**Magic passage compiler:** `Content/Python/resonant_world_magic_passage.py`
**Proof handoff:** `Content/Python/resonant_world_proof_handoff.py`

## The idea

Melodia should not copy Minecraft's surface loop of “break block, place block,
make bigger house.” Its equivalent is:

> Explore a living score, gather fragments of sound, and build places that
> make the world sing back.

The world is made from resonant voxel matter. A voxel has a material, pitch
class, scale degree, voice, timbre, and energy. Terrain is therefore not just
height plus texture: it is a spatial arrangement in a key. The player can
read a place by ear, alter it by building, and leave behind a composition that
changes traversal, weather, creatures, and narrative presentation.

This is still a world-puzzle layer, not a replacement for the TurnBased JRPG
template or QuillScript. A generated landmark may expose a challenge, but the
challenge's canonical completion and reward still go through the existing
narrative adapter and save authority.

## The translation

| Familiar sandbox idea | Resonant World equivalent |
| --- | --- |
| Seed | Score seed: root, mode, tempo, motif, and generator version |
| Block | Resonant voxel: pitch + material + voice + timbre |
| Biome | Harmonic region: a mode degree with its own palette and instrument family |
| Cave / mountain | Register shift: bass-heavy, low-energy, or dissonant space |
| Redstone | Rhythm circuit: pulses, rests, gates, and call-and-response routes |
| Crafting table | Arrangement table: combine tones into a usable phrase or tool |
| Village | Ensemble: NPCs and structures that each carry a voice |
| Mob | Motif creature: behavior follows a repeating rhythmic or melodic cell |
| Nether / End | Dissonant movements: special harmonic rules, not just harder biomes |
| Building | Instrument architecture: adjacency and order produce a score |
| Resource gathering | Recovering lost phrases, timbres, and cadence fragments |
| Map marker | Auditory landmark: a motif that can be recognized before it is seen |
| Multiplayer build | Shared arrangement: players add compatible voices to one place |

## The world grammar

### 1. Score seed

`WorldConfig.from_seed(seed)` derives a stable root note, mode, tempo, meter,
and motif. The same seed always yields the same world profile. A future
authoring layer can pin any of these values for a curated chapter while still
using the same generator.

### 1.5. World movements

The seed also chooses a headline movement. A movement is an authored ecology,
not a generic biome: it binds a world verb, PCG asset families, VFX, water
profiles, wardrobe archetypes, NPC zones, and a small quantum objective vector.
The current library is:

`Petal Cantata · Star Loom · Liquid Cathedral · Cadence Cathedral · Mirage Gala · Dissonant Expanse`

The origin chunk uses the headline movement. Compatible neighbouring movements
are selected by stable coordinates so a world can modulate without losing its
identity. The asset atlas resolves each movement against the real project and
reports logical manifest references separately from promoted Unreal assets.

### 2. Harmonic geography

Every streamed chunk receives a scale degree. The degree chooses a region name,
surface material, timbral family, and local pitch center. The center chunk is
tonic and readable; the surrounding ring introduces the proof landmarks already
present in the PCG system:

`Resonance Cathedral → Arpeggio Bridge → Bell Tree Garden → Xylophone Trail → Crystal Harp Grove`

Farther out, landmarks become sparse and motif-driven. This preserves the
recognition of a designed world without making the infinite field feel like a
random asset scatter.

### 3. Seam-safe streaming

Chunk edges own a shared border signature and a shared traversal anchor. Both
neighboring chunks derive the same anchor from the ordered pair of coordinates,
so a streamed seam does not produce a broken road, melody path, or water-gate
route. This follows the existing 25,600 cm World Partition chunk contract; the
prototype's 16×16 voxel preview maps to 1,600 cm cells for authoring clarity.

### 4. Voids and voices

Vertical position is musical register. Deep material tends toward bass/drone;
the surface carries melody and harmony; silence is a real material state for
air, rests, and unavailable voices. This creates a reason to travel vertically:
the player is moving between parts of an arrangement, not just mining toward a
rarer color.

### 5. Building as composition

Player changes are sparse edits addressed by stable cell ID. Regeneration
recreates the base world, then applies edits. A small arrangement scorer rewards
scale-compatible transitions, preserves room for tension, and never produces a
hard “you failed music” state. A dissonant build is a beautiful dissonance or a
searching phrase; it can become a story or puzzle hook.

The full game version should let a player:

- place a tone block, rest block, sustain block, or conductor block;
- route pulses through gates and call-and-response relays;
- assign a structure's voices to Melusina's current outfit or companion party;
- hear the arrangement change as the player walks through it;
- save only the edits, discovered motifs, and canonical challenge state.

The active wardrobe is a world voicing. Cosmetics remain presentation, forms
declare capabilities, and style axes grade expression; traversal, narrative,
combat, inventory, and save systems remain their existing authorities. A form
can expose a movement verb such as `bloom`, `weave`, `conduct`, `compose`,
`drift`, or `resolve`, but the world layer only requests the response through
the canonical adapters.

## Long-term rules

These rules keep procedural generation from becoming disposable noise.

1. **Motif before noise.** Every region has a recognizable interval cell before
   detail noise is added.
2. **Authored anchors, procedural connective tissue.** Hero landmarks are
   authored PCG grammars; terrain, dressing, and connective routes are seeded.
3. **Variation has a budget.** A distant chunk may vary material, octave,
   ornament, or cadence, but not all of them at once. Players learn the world's
   musical language.
4. **Every generated place has a musical job.** It should introduce, answer,
   modulate, rest, or resolve a phrase.
5. **Discovery is content.** A new motif is a durable collectible and a
   narrative signal, not only a map pin.
6. **The world never invalidates authored progress.** Generator revisions are
   versioned; old chunks can be migrated or held at their prior generator
   version, while canonical completion remains external.
7. **Silence is allowed.** Not every space needs an effect, enemy, or reward.
   Rests make the next sound meaningful.
8. **Quantum is a chooser, not a generator.** It may select between two
   authored movement candidates asynchronously; a deterministic classical
   baseline and persisted result are mandatory.

## Implementation boundary in the current project

| Concern | Owner |
| --- | --- |
| Seed, mode, harmonic region, chunk identity, voxel identity | Resonant World generator |
| Movement identity and asset-family binding | Resonant World generator + asset atlas |
| Existing-asset semantic binding per movement/chunk | `resonant_world_asset_constellation.py` |
| Phrase, call/response, route seam, beat stages, and event voicing | `resonant_world_score.py` |
| Resonant metadata on existing PCG volume/static specs | `resonant_world_pcg_adapter.py` |
| Existing MIDI → stable phrase voxels | `resonant_world_phrase_bridge.py` |
| Cosmetic/Form/Style → authored movement response preview | `resonant_world_wardrobe_bridge.py` |
| Staged magical world response choreography | `resonant_world_magic_passage.py` |
| Pure validation/flattening for the editor proof lane | `resonant_world_proof_handoff.py` |
| Optional movement candidate selection | Async Python quantum service; classical fallback |
| Streaming, PCG graph placement, HLOD/data-layer routing | Existing PCG / World Partition pipeline |
| Beat/bar transport and reactive presentation | `UMelodiaMusicClockSubsystem` + existing palette bus |
| Challenge attempt state | World-challenge Blueprint, transient only |
| Completion, reward, narrative flags, save/load | `UMelodiaNarrativeSubsystem` / JRPG save authority |
| Combat, inventory, turns, damage | TurnBased JRPG template |
| Dialogue and authored consequence | QuillScript |

The generator's manifest intentionally states that narrative, combat, and save
authority are external. That is the seam that lets the sandbox grow for years
without quietly creating a second game underneath the real one.

The wardrobe bridge makes the same seam inspectable. It emits the real
five-piece `MelusinaV2` source records, an existing outfit archetype and
palette, a movement/form request, and the resolved PCG/VFX/water/phrase inputs
as one preview artifact. Its Form layer declares but never grants; it cannot
equip, commit a challenge, or write a save.

The magic passage compiler turns that preview into a four-stage response:
`invocation → unfolding → threshold → release`. Each stage has a musical job,
world verb, PCG query, VFX/water binding, phrase window, NPC zone, and style
axis. It also creates a scene-preview/photo anchor and explicit effect toggles,
so a magical outfit is something the player can compose and photograph rather
than a hidden numerical modifier. The passage remains a read-model; the
existing owners still apply any request.

The score composer is the next granularity down: it turns one movement/chunk
into a 16-beat call/response lane with four music-clock stages. Its event-level
voicing references the constellation's existing music, material, ornament, VFX,
and wardrobe records. The route begins and ends on the generator's shared edge
anchors, so neighboring chunks can stream without inventing a second seam
system. A score ID is a replay key; the composer still does not write a save or
apply traversal.

Passage collection uses the existing `DA_MelodiaCurrencyRegistry` mirror rather
than inventing a Resonant World economy: Petal Cantata exposes Radiant shards,
Star Loom Arcane, Liquid Cathedral Tide, Cadence Cathedral Forte, Mirage Gala
Gale, and Dissonant Expanse Umbral. The passage only declares the affordance;
amounts and grants remain authored by the existing pickup/challenge and wallet
authorities.

`resonant_world_proof_handoff.py` is the safe current-state envelope for the
editor lane. It flattens the five hero inputs and preserves the wardrobe and
passage summaries without importing `unreal`, mutating a map, or claiming that
PIE evidence exists. The eventual one-editor setup can consume this envelope
or the same source plan.

## Build path

### Slice 1 — First Resonance Echo

Use one seed, one 3×3 chunk ring, and the five existing hero grammars. The
player walks from tonic stone into a bridge, bell garden, and harp grove; one
phrase activates one world object; completion goes through the existing
`first_resonance_world_challenge` contract.

### Slice 2 — Instrument architecture

Add note/rest/sustain/conductor blocks and the arrangement scorer. Let the
player build a tiny bridge or shrine whose sound is audible and whose route
changes when the cadence resolves.

### Slice 3 — Living regions

Give each region a small motif creature, weather response, and ensemble NPC.
Keep authored dialogue in QuillScript and use generated motif IDs as the stable
inputs to those authored reactions.

### Slice 4 — Endless movements

Introduce deliberate harmonic travel: a discovered cadence modulates the world
into a new movement. Preserve old edits and discoveries while generating new
regions under the next movement's score seed.

### Slice 5 — Wardrobe modulation

Use the generated `resonant_wardrobe_voicing_sakura_3900.json` as the design
readback for Petal Cantata. Then, after the closed-editor wardrobe build and
catalog/form readback, wire one proven Melusina form through the canonical
narrative/traversal path so the outfit changes one shrine's expression,
PCG/VFX presentation, and route affordance without introducing a second
unlock or save authority.

### Slice 5.5 — Magical passage

Use `resonant_magic_passage_petal_3900.json` as the first ritual: Petal
Cantata germinates, opens flora, draws a petal route, then leaves a bloom rest.
The same four-stage contract is generated for all six movements, so new magic
comes from authored movement content and asset bindings rather than a second
runtime system.

### Slice 6 — Async movement composition

Use `/rank_world_movements` only during world preparation or a controlled
event. Persist the response, expose the baseline/backend/trace in the debug
panel, and compare authoring quality and latency before considering any larger
optimization experiment.

### Slice 7 — Proof-map adapter

Consume `Saved/Audit/resonant_world_pcg_plan_3900.json` from the existing
scale-world proof setup lane. The adapter already emits the existing graph,
profile, Data Layer, HLOD, seam, and interactive ownership fields plus
movement/motif/style metadata. The editor lane should only apply those specs to
the additive proof level and write its normal audit envelope.

## Local verification

From the repository root:

```text
python -m pytest Content/Python/test_resonant_world_generator.py -q
python BS_GodFile/Content/Python/resonant_world_generator.py --seed 3900 --radius 1
python BS_GodFile/Content/Python/resonant_world_asset_atlas.py --output BS_GodFile/Saved/Audit/resonant_world_asset_atlas.json
python BS_GodFile/Content/Python/quantum/resonant_movement_ranker.py --atlas BS_GodFile/Saved/Audit/resonant_world_asset_atlas.json --candidate petal_cantata --candidate star_loom
python BS_GodFile/Content/Python/resonant_world_phrase_bridge.py --midi BS_GodFile/Content/MelodiaIntegration/MIDI/128BPMarpeggiomelody.mid --seed 3900 --output BS_GodFile/Saved/Audit/resonant_world_phrase_128bpm.json
python BS_GodFile/Content/Python/resonant_world_wardrobe_bridge.py --seed 3900 --movement petal_cantata --archetype SakuraDreamer --atlas BS_GodFile/Saved/Audit/resonant_world_asset_atlas.json --phrase BS_GodFile/Saved/Audit/resonant_world_phrase_128bpm.json --output BS_GodFile/Saved/Audit/resonant_wardrobe_voicing_sakura_3900.json
python BS_GodFile/Content/Python/resonant_world_magic_passage.py --seed 3900 --all-movements --atlas BS_GodFile/Saved/Audit/resonant_world_asset_atlas.json --phrase BS_GodFile/Saved/Audit/resonant_world_phrase_128bpm.json --output BS_GodFile/Saved/Audit/resonant_magic_passage_portfolio_3900.json
python BS_GodFile/Content/Python/resonant_world_magic_passage.py --seed 3900 --movement petal_cantata --archetype SakuraDreamer --atlas BS_GodFile/Saved/Audit/resonant_world_asset_atlas.json --phrase BS_GodFile/Saved/Audit/resonant_world_phrase_128bpm.json --output BS_GodFile/Saved/Audit/resonant_magic_passage_petal_3900.json
python BS_GodFile/Content/Python/resonant_world_score.py --seed 3900 --movement petal_cantata --chunk-x 0 --chunk-y 0 --archetype SakuraDreamer
python BS_GodFile/Content/Python/resonant_world_pcg_adapter.py --seed 3900 --radius 1 --atlas BS_GodFile/Saved/Audit/resonant_world_asset_atlas.json --phrase BS_GodFile/Saved/Audit/resonant_world_phrase_128bpm.json --wardrobe BS_GodFile/Saved/Audit/resonant_wardrobe_voicing_sakura_3900.json --magic-passage BS_GodFile/Saved/Audit/resonant_magic_passage_petal_3900.json --output BS_GodFile/Saved/Audit/resonant_world_pcg_plan_3900.json
python BS_GodFile/Content/Python/resonant_world_proof_handoff.py --plan BS_GodFile/Saved/Audit/resonant_world_pcg_plan_3900.json --output BS_GodFile/Saved/Audit/resonant_world_proof_handoff_3900.json
```

The generator, wardrobe bridge, and passage compiler are offline/read-model
tools. The next UE task is for the existing editor-only scale-world setup lane
to apply the validated proof handoff to the additive World Partition level; it
must not write canonical narrative state or invent a new save object.
