# Technical Data Flow — Melodia Melusina

**Last Updated:** 2026-10-01
**Scope:** stable runtime/state lifecycle for an evergreen single-player game  
**World-building contract:** [`Docs/WorldBuilding/WORLD_BUILDING_SOURCE_OF_TRUTH.md`](Docs/WorldBuilding/WORLD_BUILDING_SOURCE_OF_TRUTH.md)

---

## 1. Core lifecycle

Melodia no longer defines every Chapter by one identical six-phase sequence. The reusable data contract is instead:

```text
AUTHORED INTENT / WORLD ACTION
        ↓
appropriate runtime owner
        ↓
optional rhythm execution
        ↓
Wardrobe / Convergence interpretation
        ↓
world / combat / narrative consequence
        ↓
canonical durable fact
        ↓
save / restart / restore
```

The C++ ownership diagram is the same lifecycle read as layers:

```text
Data definitions
        ↓
Core C++ systems
        ↓
Gameplay rules
        ↓
Blueprint assembly (events call into code; Blueprints read structured data)
        ↓
Content (systems drive visuals)
        ↓
Player experience
        ↓
Persistence (results are saved)
```

Different content tiers can enter and leave this flow at different points.

---

## 2. Major data owners

### Narrative / progression
`UMelodiaNarrativeSubsystem` + QuillScript own durable narrative facts:

- quest/objective state;
- flags;
- stable intent consumption;
- reward consumption;
- checkpoints;
- authored consequences.

Repeated processing of the same stable intent must remain idempotent.

### TurnBased JRPG / Phoenix
Owns combat/gameplay facts it already controls:

- turn order;
- target selection;
- action resolution;
- party HP/MP/stats;
- inventory;
- terminal battle results;
- stock gameplay save state.

### Rhythm
Melodia rhythm receives an authored/selected action context and returns execution quality/performance data. It may influence result interpretation but does not directly create an independent combat transaction.

### Wardrobe
Wardrobe owns owned/equipped outfit state. Equipped identity can expose traversal capability and feed Convergence interpretation.

### Melusina runtime character and presentation
`/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter` is the canonical exploration
character, selected by the integration game mode on configured route maps. **Ultimate** names this
existing role, not a new class. The Blueprint composes the established locomotion/Rokoko animation,
wardrobe, traversal, and Niagara presentation owners. Universe Foundry compiles authored content
for existing gameplay contracts; it is not a pawn-side runtime manager.

`/Game/Experiments/MelodiaJRPG/BP_MelusinaSwordsman_Presentation` is a distinct battle
presentation actor. Older `BP_Melusina` character roots are reversible deprecation candidates,
pending fresh referencer checks. The six skill Blueprints and room-shell actor retain their own
content roles. The full inventory and live-proof boundary are in `CURRENT_STATE.md`.

### Starskiff
Starskiff owns vehicle/traversal runtime state. Only stable long-term facts should enter canonical persistence; transient transforms/velocities should normally be rebuilt from checkpoints/authoring state.

---

## 2.25 FLOW / SEQUENCE migration contract — owner-directed target

The October 1 gameplay goal is to test whether Melodia's player-facing combat/exploration presentation should converge on two modes while preserving the existing authority rules.

```text
FLOW
canonical Melusina pawn
  → traversal / dodge / WaveHarp realtime input
  → world encounter interaction
  → authoritative shared damage/effect resolution
  → same encounter HP
  → continued world control

SEQUENCE
same encounter
  → deliberate EnterSequence
  → existing Melodia rhythm session
  → timing / grade
  → typed effect request
  → the same authoritative damage/effect resolution
  → same encounter HP
  → ExitSequence
  → FLOW

encounter completion
  → existing typed narrative result
  → exactly-once consequence / reward / checkpoint
```

The word **shared** is load-bearing. The migration must discover or extract one canonical damage/effect calculation boundary that both stock battle and realtime world interaction can use. A FLOW attack may not carry a copied damage formula, and a SEQUENCE phrase may not accept a synthetic final number as production proof.

Until that seam is proven in runtime, Phoenix / TurnBased JRPG remains the production combat authority. FLOW/SEQUENCE is therefore a **candidate data-flow evolution**, not permission to fork party, HP, inventory, save, targeting, rhythm, or narrative ownership. PR #367 demonstrates the intended presentation/session shape but leaves the production resolver-to-world-target seam open; it is reference only.

Promotion evidence must show the canonical pawn, real input, target identity, HP before/after, the authoritative resolved value, exactly one application, no duplicate encounter actor, and successful return to ordinary control. A FLOW → SEQUENCE → FLOW claim additionally needs exactly one rhythm session/effect request and the same target/HP across the transition.

### Convergence
Convergence reads durable/authoritative inputs and derives relationship state or authored response. Derived values should be recomputable unless there is a specific reason they must become durable facts.

### Audio / cymatic presentation routing

Presentation signals use one writer per MPC surface:

```text
audio / gameplay / approved external source semantics
        ↓
UMelodiaAudioReactivePresentationSubsystem
        ↓
MPC_Melodia_Palette        (source/audio-reactivity surface)
        ↓
UMelodiaCymaticsSubsystem  (read-only evaluator)
        ↓
UMelodiaCymaticsWriterSubsystem
        ↓
MPC_Cymatics_Driver        (derived cymatic presentation surface)
        ↓
materials / Niagara / water / other read-only consumers
```

Hard rules:

- `UMelodiaAudioReactivePresentationSubsystem` is the continuous writer for `MPC_Melodia_Palette`;
- `UMelodiaCymaticsWriterSubsystem` is the sole writer for `MPC_Cymatics_Driver`;
- `UMelodiaCymaticsSubsystem` evaluates/reads the source surface and does not become another MPC writer;
- new source semantics such as wind direction/strength belong upstream of the driver and must preserve this single-writer chain;
- `WorldField.ResonanceN/M` and `WorldField.Tension` are field/bus semantics, not names to invent as MPC parameters.

---

## 2.5 Production authoring ingress

These are content/tool ingress paths into the runtime owners above. They do not create new runtime authorities.

### Compiled world content

```text
authored recipe / curated source assets
        ↓
Tools/world_compiler.py validate + compile
        ↓
Saved/WorldCompiler/<recipe>_<seed> bundle
        ↓
Tools/world_compiler_ue_driver.py / Content/Python/world_compiler_ue.py
        ↓
DataTable + existing data-driven PCG + materials/Niagara
        ↓
existing gameplay/audio/world signals
        ↓
PIE / reload / packaged evidence as required
```

The compiler stays offline and never writes gameplay truth or MPC state.

### Houdini / Hython source generation

```text
deterministic Hython tool under Tools/Houdini/
        ↓
manifested mesh / texture / field / cache output
        ↓
curated UE import or World Compiler input
        ↓
existing PCG/material/level consumer
        ↓
UE proof
```

A Hython cook is SOURCE/TOOL evidence. It is not a live Unreal proof and Houdini Engine is not a second world compiler.

### Rokoko / Melusina animation

```text
Rokoko Studio Vision take
        ↓
Blender retarget / repair
        ↓
root-motion FBX
        ↓
Content/Python/import_rokoko_mocap_batch.py
        ↓
SK_Melusina_Skeleton + existing ABP/state owner
        ↓
PIE actor/movement proof
```

The guarded importer validates skeleton identity and centimetre scale. Import success alone does not prove the clip is bound or playing correctly.

### Native C++ / Rider

```text
Rider owner/usages discovery
        ↓
smallest change in existing native owner
        ↓
closed-editor Development Editor build when reflection/module topology changed
        ↓
focused automation
        ↓
single-editor PIE/runtime proof
        ↓
restart / packaged proof when the acceptance gate requires it
```

Rider inspection and tests reduce uncertainty; Unreal remains runtime authority.

---

## 3. Example: combat Chapter

This is an authoring pattern, not a requirement to build another combat framework. A new boss or
encounter supplies authored Quill intent, Phoenix skill data, rhythm phrase data, consequence and
reward/checkpoint content around this flow.

```text
Quill/world encounter intent
        ↓
Phoenix command selection
        ↓
Melodia rhythm session
        ↓
grade / phrase quality
        ↓
Outfit + Convergence interpret execution
        ↓
Phoenix resolves authoritative action/result
        ↓
Quill receives terminal consequence once
        ↓
reward/checkpoint fact persisted
```

The current simple grade multipliers remain a baseline implementation. Future outfit/Convergence mechanics can change interpretation without bypassing the selected Phoenix action.

---

## 4. Example: non-combat Reverie

```text
Quill start
  ↓
exploration / interaction
  ↓
optional music phrase
  ↓
world-state consequence
  ↓
chapter/reverie checkpoint
  ↓
canonical save
```

No battle subsystem is required simply because the content is called a Chapter.

---

## 5. Example: Monolith Event

```text
durable chapter prerequisites
        ↓
authored world-state director
        ↓
traversal / party / rhythm / outfit signals
        ↓
Convergence interprets existing systems
        ↓
large-scale environmental transition
        ↓
permanent aftermath fact
        ↓
checkpoint / save
```

A Monolith Event does not require conventional enemy HP. Its state owner must still be explicit.

---

## 6. Save/restore contract

The long-term product depends on save records surviving years of new Chapters.

Preferred restore sequence:

```text
read bytes / slot
   ↓
identify version
   ↓
migrate candidate in memory
   ↓
validate intrinsic invariants
   ↓
validate subsystem-owned semantics
   ↓
commit authoritative restore
   ↓
rebuild derived runtime state
   ↓
verify no duplicate side effects
```

Hard rules:

- empty state is valid state;
- an existing save must not be treated as fresh merely because an inventory/outfit slot is empty;
- failed/corrupt candidate loads must not seed defaults over valid history;
- equipped persisted wardrobe IDs must be consistent with ownership before load mutation;
- repeat load must not duplicate rewards, modifiers, quest completion, or derived registrations;
- new schema fields require explicit version/migration behavior.

---

## 7. Durable vs derived state

Persist **facts**, not every runtime detail.

Good durable candidates:

- completed Chapter/Volume IDs;
- quest/checkpoint flags;
- claimed reward/Gift IDs;
- owned/equipped wardrobe IDs;
- major Convergence decisions;
- companion recruitment;
- permanent world-state consequences;
- stable Starskiff upgrades/decorations.

Usually derived/transient:

- active rhythm note instances;
- current timing windows;
- transient UI state;
- temporary VFX/MPC pulses;
- raw Starskiff rigid-body velocity;
- recomputable Convergence presentation values.

---

## 8. Future optional content manifest

Evergreen Gifts/Voyages may later use an optional online manifest, but online availability is not gameplay authority:

```text
optional manifest
   ↓
validate version/policy
   ↓
compare offered content IDs to local canonical history
   ↓
claim/download through existing content/reward paths
   ↓
record durable local fact
```

Network failure must not invalidate owned content or core gameplay.

---

## 9. Chapter package data flow

```text
progression spec
+ optional pillar manifests
+ Quill source
+ assets/maps
       ↓
offline validation
       ↓
runtime integration
       ↓
restart/idempotency proof
       ↓
packaged proof
       ↓
promote into Volume/Voyage
```

This is the scalable unit the project should optimize for.

---

## 10. Production worldbuilding authoring flow

Procedural authoring now follows one directional promotion path:

```text
design intent / reference
+ recipe / chapter data
+ optional DCC source
        ↓
source validation
        ↓
Tools/world_compiler.py or scoped DCC export
        ↓
tracked bundle / source artifact
        ↓
world_compiler_ue_driver.py / existing UE import + PCG
        ↓
material / Niagara / level presentation
        ↓
existing runtime owner signals
        ↓
visible world response
        ↓
scene-context + runtime evidence
        ↓
main
```

The compiler and DCC tools author *what exists and where*; runtime owners determine *what it means now*. A runtime colour or cymatic response proves that the generated world is consuming the presentation signal chain—it does not make the compiler an MPC writer. World recipes, GN builders and PCG graphs extend content vocabulary; they must not multiply durable-state or signal authorities.

For an interactive spatial edit, branch movement is frozen while the editor is open. The authoring session begins from current green `main`, uses one writer, captures evidence, closes the editor, and only then performs integration/merge work.

---

## 11. Governing principle

> **New content extends the vocabulary of durable facts and authored relationships; it does not multiply state authorities.**
