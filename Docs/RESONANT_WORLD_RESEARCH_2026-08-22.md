# Resonant World research and expansion brief

## Thesis

Melodia Melusina should not make a musical copy of Minecraft. It should make a
world in which matter, wardrobe, traversal, architecture, and memory are all
different ways of composing.

The player does not merely mine blocks. They harvest phrases, tune places,
dress a temporary musical identity, and build structures that become part of a
living arrangement. The world is infinite in the way a good improvisation is
infinite: the seed provides a grammar, the authored movements provide a
recognisable vocabulary, and the player's edits become the new refrain.

The core loop is:

```text
explore -> hear a motif -> collect resonant matter -> style a voicing
-> change what the place can become -> build or perform -> leave a persistent echo
```

This is the Melodia version of the Minecraft loop. It keeps the freedom and
long-term building value, but changes the fantasy from survival/crafting to
expression, attunement, and world composition.

## What the research changes

### No Man's Sky: scale needs a reason to return

Hello Games' public materials describe a universe that continues to grow with
new stars, planets, biomes, creatures, stories, and community-scale building.
The lesson to borrow is not the number of planets; it is the combination of a
stable generation grammar with a live authored layer that gives exploration
meaning over time.

Melodia therefore needs three different kinds of persistence:

- deterministic geography from `world_seed + coordinate`;
- sparse player edits, such as built note structures, tuned bridges, and
  planted motifs;
- authored seasonal or narrative movements that can add new possibilities
  without invalidating old worlds.

The seed must regenerate the same base world. A selection made by a quantum
service must be stored as a world decision before it affects a saved world.

Two additional Hello Games lessons matter for Melodia. Their own art notes
stress that procedural generation still needs a recognizable authored style;
their settlement work combines a finite construction kit with unique layouts,
colour schemes, and decoration; and their discovery/catalogue systems make
what the player found part of the long-term journey. Melodia's equivalent is
an authored movement kit plus stable harmonic coordinates, not an infinite
asset lottery: a Petal Cantata shrine should remain legible as a shrine while
its motif, arrangement edits, seasonal voicing, and discovered “echo name”
persist around it.

That yields a stronger persistence rule: save the *identity of the echo* and
the sparse edits that made it, not a baked copy of the entire generated scene.
When a generator version changes, the same movement/region/voxel identity can
be re-dressed by the new authored kit while the player's musical history stays
canonical.

### Unreal PCG and World Partition: stream a composition, not a monolith

Unreal's PCG and World Partition workflows support partitioned generation,
Data Layers, HLOD, and runtime or hierarchical generation modes. That matches
the project's existing hero PCG graphs and lets the system keep gameplay
landmarks separate from cheap background dressing.

The rule for Melodia is:

- World Partition owns where a chunk is streamed.
- The Resonant generator owns the chunk's stable identity, harmonic region,
  movement, seam anchors, and voxel metadata.
- PCG owns how an authored movement is dressed in Unreal.
- A landmark graph owns interactive hero geometry and is kept out of HLOD when
  gameplay depends on it.

This keeps the generator engine-agnostic while still making real use of the
project's PCG library.

### Infinity Nikki: the outfit should be a world verb

The strongest transferable idea from Infinity Nikki is not fashion scoring by
itself. It is the relationship between outfit theme, ability identity,
movement, and world response. Official material describes abilities beginning
from an outfit theme, outfits changing traversal or movement, and the world
reacting to an ability outfit by growing or blooming life. Recent official
material also shows custom ability styling, dye/evolution, mount styling, and
scene previews.

Melodia's translation is:

- A cosmetic is the visible instrument.
- A resonant form declares the world verb.
- A style score says how strongly the current look expresses a musical axis.
- The traversal, narrative, and save systems remain the authorities that apply
  the result.

So a petal sleeve is not merely “+healing.” It is a voicing that can make a
dead garden remember its bloom phrase. A water-hair form is not merely a
swimming skin; it can conduct a river into a playable current. A star cape can
turn an observatory into a loom of route nodes.

The existing wardrobe architecture already has the right separation:
`Cosmetic -> Form -> Style`. The Resonant World layer consumes that contract;
it does not duplicate unlock state or create a second traversal authority.

## The unique fantasy: a world that can be styled into existence

The world should have a “current voicing,” analogous to a current outfit but
larger than a character loadout. It is the combination of:

- a root pitch and mode;
- a movement, such as Petal Cantata or Star Loom;
- a landmark instrument;
- a wardrobe form and its style axes;
- a local motif and unresolved tension;
- the player's persistent arrangement edits.

The same piece of geography can therefore be experienced differently without
being regenerated into nonsense. A shrine remains a shrine, but its flowers,
water, path affordances, lighting, and response phrases change according to
the active voicing.

### The six authored movements

The current generator defines six cross-system ecologies. The companion asset
atlas resolves them against the real project rather than treating them as
fictional names.

- **Petal Cantata** — bloom, Sakura PCG, SakuraDreamer, petal/sparkle/fabric
  Niagara, pond shrine water, and a gentle ionian/dorian palette.
- **Star Loom** — weave, cosmic PCG, CosmicWeaver, floating motes and wish
  bursts, constellation density, and lydian/dorian movement.
- **Liquid Cathedral** — conduct, crystal harp and grotto PCG, Melusina's
  water-hair materials, water-family profiles, and the existing Chaos Drift /
  Entropy Dust quantum-reactive VFX path.
- **Cadence Cathedral** — compose, the hero musical PCG ring, piano keybed and
  note assets, MIDI/beat-grid sources, and the project's musical ornament
  kitbash.
- **Mirage Gala** — drift, spline paths, Escher/cyberpunk contrast, wind-aware
  fabric trails, MirageDancer, and ankle-bell/ribbon motion.
- **Dissonant Expanse** — resolve, black-basin and ruin grammars, controlled
  tension, water-sheet traversal, and a survivable frontier for unresolved
  notes.

The movement is not a closed biome. It is a compositional lens that can appear
in different modes and can be layered over a region. The origin chunk presents
the seed's headline movement; neighbouring chunks choose compatible companion
movements using stable coordinates.

## The material grammar

Every generated voxel carries more than a material name:

- `material_id` — what it looks like or what it can be used for;
- `pitch_class` and `scale_degree` — the note identity inside the world mode;
- `voice` — bass, harmony, melody, or silence;
- `timbre` — the instrument family a surface suggests;
- `energy` — a stable intensity value for response, glow, particles, and
  gathering rarity.

This makes a block-like system that is musical without forcing every action to
be a rhythm minigame. Walking over a xylophone trail can reveal a phrase.
Mining resonant silt can yield a lower register. Building a column changes the
voicing of the local arrangement. The player can always make something
beautiful: dissonance is an authored interpretation, not a fail screen.

## Long-term generation contract

The current implementation in
`Content/Python/resonant_world_generator.py` provides:

- a deterministic world profile: root, mode, BPM, meter, motif, and movement;
- harmonic regions that repeat intentionally across a very large world;
- a proof ring of existing hero PCG landmarks;
- seam-safe streamed chunk anchors;
- stable voxel IDs and sparse edit records;
- arrangement scoring that describes a structure as a refrain, searching
  phrase, or beautiful dissonance;
- an explicit rule that narrative, combat, inventory, and save authority stay
  outside the generator.

The generated manifest is an authoring/debug contract for Unreal. It is not a
replacement for World Partition, PCG, the JRPG template, QuillScript, or the
canonical narrative record.

The concrete bridge is now
`Content/Python/resonant_world_pcg_adapter.py`. It consumes the Resonant
manifest, reuses `pcg_scale_world_pipeline` and `pcg_visual_chunk_builder`, and
emits decorated hero-volume/static specs. The adapter preserves the existing
graph/profile, Data Layer, HLOD, and interactive-actor ownership; its new data
is movement/motif/mode/wardrobe metadata for the existing owner to consume.

The same handoff can now carry the real imported
`Content/MelodiaIntegration/MIDI/128BPMarpeggiomelody.mid` through
`Content/Python/resonant_world_phrase_bridge.py`. The current audit produces
192 stable phrase voxels, classifies each note as resonant or dissonant
material, and preserves the existing Harmonix/Melodia music clock as the
runtime audio authority.

The wardrobe bridge makes the Infinity Nikki-inspired idea concrete without
collapsing the project's contracts. `resonant_world_wardrobe_bridge.py` emits
a deterministic voicing preview with three layers: the real first-outfit
catalog records, an existing GMM archetype/palette and its cloth pieces, and a
movement/form request. It also carries current PCG, Niagara, water, and phrase
resolution into the same readback. The source wardrobe manifest remains
decorative-only and editor-materialization-pending, so the artifact labels its
movement form as `declares_only` and sets every mutation boundary to false.
This is the right intermediate step: designers can judge whether an outfit
actually changes a place before a closed-editor catalog readback and one
canonical traversal/narrative hook are attempted.

## Wardrobe as a procedural instrument

The wardrobe should influence the world through authored hooks, not arbitrary
stat accumulation.

### Outfit expression

Each current look contributes to musical axes such as:

- `resonance` — sustained, pure, architectural response;
- `cadence` — rhythmic, route, and traversal response;
- `lilt` — petal, ribbon, and wind response;
- `flow` — water and continuous-motion response;
- `orbit` — star, constellation, and route-loop response;
- `tension` — controlled dissonance, danger, and unresolved portal response.

Slot weighting remains important: silhouette and primary form should matter
more than a charm or accessory. A recolour may share the same form, while its
style scores change how strongly the world expresses that form.

### World response

The world response should be a short-lived, readable transformation rather
than a permanent stat buff:

- Petal Cantata opens plants, creates a safe route, and adds a high register
  to nearby instruments.
- Star Loom reveals hidden nodes, changes the density of sky geometry, and
  turns NPC schedules toward observatory routes.
- Liquid Cathedral connects water surfaces, exposes submerged notes, and
  drives the shared material/VFX pulse.
- Mirage Gala changes wind lanes, ribbon bridges, and movement phrasing.
- Dissonant Expanse reveals a portal only when the player's arrangement gives
  the tension a resolving answer.

These are “attire as spellbook” mechanics, but the canonical traversal and
narrative authorities still decide whether a capability is unlocked and
whether a context suppresses it.

The current Petal Cantata preview is a concrete slice: SakuraDreamer selects
`resonance` and `lilt`, resolves the existing petal/sparkle/fabric Niagara
systems, selects the authored `pond_shrine` water profile, carries the 128 BPM
MIDI phrase's 192 note voxels, and keeps the world response pointed at the
existing PCG/World Partition owner. The artifact is a response plan, not a
runtime grant or a new save path.

### New research-derived rules: make magic a passage

The official Infinity Nikki material adds three useful constraints to the
Melodia translation. First, an outfit ability can visibly change the living
world: the Petal Ripple ability grows plants and changes nearby creatures.
Second, outfit design starts from a theme and is carried through materials,
movement, and VFX rather than being a detached stat. Third, the current game
supports open-world scene preview, clothing effect toggles, and ability-outfit
scheme handling. The Melodia implementation therefore compiles a four-stage
`Resonant Passage` instead of firing one opaque effect:

`invocation → unfolding → threshold → release`

Each stage has a musical job, a world verb, an existing PCG query, an existing
Niagara/water binding, a phrase window, an NPC zone, and the active wardrobe
axes. A deterministic photo anchor and effect toggles make the response
reviewable before it is wired to an editor asset. This is how the system gets
the magical feeling without hiding logic in a monolithic ability Blueprint.

Epic's PCG/World Partition guidance is also a direct architectural constraint:
generated actors follow the source PCG component's Data Layers and HLOD Layer.
The passage therefore describes dressing and ownership, but never creates a
parallel streaming or actor-spawn authority.

The same principle applies to collection. The current passage portfolio binds
each movement to one of the existing seven elemental currency rows in
`specs/economy/melodia_currency_registry.v1.json`. This turns “gather resonant
matter” into a real project affordance without creating a second economy:
movement selects the element, while the existing pickup/challenge and wallet
authorities decide whether and how much to grant.

## Quantum architecture: useful, honest, and optional

The project already has the correct first principle: quantum code is an
asynchronous decision service, not a frame-loop dependency.

### Current foundation

- `MelodiaQuantumDrawSubsystem` already makes an asynchronous request and
  publishes the result through the canonical material/VFX path.
- `/rank_layouts` is the existing small JSON service contract.
- `qsharp_layout_ranker.qs` performs a genuine two-candidate
  score-weighted-amplitude measurement when Q# is available.
- the classical baseline is retained and the backend field reports what
  actually ran.

### New movement composer

`Content/Python/quantum/resonant_movement_ranker.py` extends the same idea to
world-scale composition:

1. The classical layer creates a small candidate set from authored movements.
2. Each candidate receives a bounded objective vector:
   outfit synergy, asset coverage, traversal safety, visual contrast, and motif
   continuity.
3. The baseline ranks those candidates deterministically.
4. With exactly two candidates, the Q# operation may perform one measured
   choice. With more candidates, the ranker deliberately falls back to the
   classical baseline.
5. The response stores the winner, baseline winner, scores, backend, and trace
   id before Unreal applies any PCG binding.

The service endpoint is `/rank_world_movements`. The minimal contract lives at
`specs/resonant_world_movement_rank.v1.json`.

The PCG handoff is a separate deterministic artifact at
`Saved/Audit/resonant_world_pcg_plan_3900.json`. It currently emits nine
chunks, five hero volume specs, and 162 static specs for the proof radius. It
now carries the compact Sakura wardrobe voicing summary as an optional
non-granting input plus a four-stage magic-passage summary, and it does not
touch a production map.

### Quantum setup update

The primary documentation supports the boundary already chosen here: Q# mixes
classical and quantum instructions, while Amazon Braket treats QPUs as
co-processors inside a classical hybrid job and recommends simulators before a
real device. The useful Melodia experiment is therefore staged:

1. Classical authoring ranks a small set of movement candidates and records the
   deterministic baseline.
2. A two-candidate Q# measurement may choose the movement during world
   preparation; the result, baseline winner, backend, and trace are persisted.
3. A separate offline experiment can test QAOA/Max-Cut-style optimization over
   a small arrangement graph, measuring quality, latency, noise sensitivity,
   and cost against the classical solver.

Quantum never selects per-frame effects, individual voxels, or player inputs.
That preserves replayability while leaving a real path to a deeper hybrid
experiment once the content grammar is fun on classical hardware.

### What quantum should not do

Quantum should not select individual voxels, grade player inputs, drive
per-frame traversal, or replace authored design. Those jobs need replayability,
latency, and direct control. The useful quantum boundary is a low-frequency
macro choice: which authored movement, route family, puzzle seed, or small
layout candidate should be staged next.

### Future experiment

If a larger candidate problem becomes valuable, run it offline as a hybrid
constraint/optimization job. QAOA or a similar method can be compared against a
classical solver on a bounded 5–12-node arrangement problem. The deliverable
is a quality/latency comparison, not a claim of quantum advantage. A live world
must still have a classical result, a timeout, and a stored replay record.

### Research update: the right scale for the experiment

The current Unreal documentation makes the PCG boundary sharper: partitioned
generation splits output across a grid for streaming, while hierarchical
generation allows large and small grids to share cached data. Runtime
generation is a separate proximity-driven mode. Therefore the Resonant
composer should choose a macro movement or route family before PCG begins; PCG
itself should own the spatial decomposition and cache/stream behavior.

The current quantum documentation points toward a two-stage experiment:

1. Use the local Q# simulator for the existing two-candidate proof and compare
   it against the deterministic baseline.
2. If the problem grows into a real constraint graph, send an offline
   specification to a hybrid job. QAOA/Max-Cut-style experiments are suitable
   for a bounded adjacency problem such as choosing six movement transitions
   with penalties for repeated visual grammar, unsafe route changes, and broken
   motif continuity.

The hybrid job would return a candidate transition sequence, not live actors or
voxels. The sequence would be stored as an authored world decision and replayed
by the ordinary generator. This matches the platform model: classical
resources and a QPU cooperate in an iterative job, with inputs and outputs
stored separately from game runtime.

## Asset audit result

The generated atlas currently scans 59,291 files under Content, Plugins,
Products, Imports, and generated outputs. The most important cross-system
families are present:

- 9,219 EnvSandbox assets and 2,933 Melodia assets in the broader project
  inventory;
- 71 directly matched musical PCG files and 115 Sakura-related PCG/style
  files;
- 26 cosmic and 12 grotto/Escher/cyberpunk PCG matches;
- 209 wardrobe-related files and 1,704 Melusina-related files;
- 18 water-related files plus water-family JSON profiles;
- 104 musical ornament matches;
- 59 quantum files and the existing Q# project/experiment harness;
- 4,349 audio/MIDI matches and 2,059 material matches in the atlas scan.

Some movement bindings currently resolve through logical JSON manifest records
such as `manifest:niagara/NS_Nikki_WishBurst`, not promoted `.uasset` files.
The atlas labels this distinction instead of hiding it. That is important for
production readiness.

## Known gates

These are real remaining gates, not design claims:

- The wardrobe architecture document says the reflected types need a closed
  editor build; the current forms are designed but not proven in PIE.
- The material audit found that the canonical palette MPC is written by C++,
  while the current master material path does not yet consume the audio
  channels correctly.
- Water v10 has documented promotion and PIE gates still open.
- Q# may not be installed in every local environment; the new movement ranker
  must report and use the classical baseline in that case.
- The local Q# project currently cannot resolve its pinned
  `Microsoft.Quantum.Sdk/0.20.2101` without the installed SDK/NuGet access. The
  source contract is present and the Python path remains honest about the
  unavailable backend; this is an environment promotion gate, not a reason to
  invent a pseudo-quantum result.
- The atlas proves authoring references, not that every referenced asset is
  loaded, compiled, performant, or safe in a shipping map.
- The magic passage is now an offline/read-model contract; its four stages are
  not runtime evidence until the existing proof map is applied and observed in
  PIE.

## Recommended build sequence

### Slice A — make the proof ring playable

Use seed 3900 and the existing hero landmark ring. Spawn the generated chunks
into a test World Partition map, bind each landmark to its existing PCG graph,
and expose the movement/region/motif metadata in a debug panel.

The offline handoff for this slice is already generated by
`resonant_world_pcg_adapter.py`. The next editor action is to teach the
existing proof-map setup lane to read its decorated specs and passage summary,
not to create a new map builder. The current checked-in setup script is
editor-only and does not provide a headless plan-only mode. Until that owner
lane is available, `resonant_world_proof_handoff.py` provides a pure validation
envelope and correctly reports `editor_apply.performed: false`.

### Slice B — make one outfit change one place

Choose Petal Cantata. Wire one existing Melusina wardrobe form through the
canonical narrative/traversal path. On a successful form query, activate the
Sakura PCG/VFX response and let the result affect a shrine, not the whole map.

### Slice C — make building become music

Use the piano keybed, note ornaments, and MIDI beat-grid. A placed structure
should expose its arrangement score and play a small motif. There is no fail
state; the score changes the interpretation and reward phrase.

### Slice D — add movement selection offline

Use `/rank_world_movements` to choose between two authored movements during
world preparation or a controlled event. Persist the response and replay it in
the next load. Measure authoring value, latency, and quality against the
classical baseline.

### Slice E — expand through content, not generator complexity

Add new movement records, PCG graphs, outfit forms, motifs, and NPC zones. Keep
the core generator stable. Long-term variety should come from a growing,
reviewable grammar library and player edits, not from an opaque algorithm that
cannot explain why a place exists.

## Primary references

- [Infinity Nikki — Petal Ripple: World Rhythms](https://infinitynikki.infoldgames.com/en/news/388)
- [Infinity Nikki — official ability/outfit design notes](https://infinitynikki.infoldgames.com/en/news/155)
- [Infinity Nikki — official scene preview and styling systems](https://infinitynikki.infoldgames.com/en/news/560)
- [Hello Games — No Man's Sky about/procedural universe](https://www.nomanssky.com/about/)
- [Hello Games — The Art of No Man's Sky](https://www.nomanssky.com/2016/04/art-of-no-mans-sky/)
- [Hello Games — Frontiers settlements and save streaming](https://www.nomanssky.com/frontiers-update/)
- [Unreal Engine — PCG with World Partition](https://dev.epicgames.com/documentation/unreal-engine/using-pcg-with-world-partition-in-unreal-engine?lang=en-US)
- [Unreal Engine — PCG generation modes](https://dev.epicgames.com/documentation/en-us/unreal-engine/using-pcg-generation-modes-in-unreal-engine)
- [Unreal Engine — World Partition](https://dev.epicgames.com/documentation/unreal-engine/world-partition-in-unreal-engine?lang=en-US)
- [Microsoft Learn — Q# overview](https://learn.microsoft.com/en-us/azure/quantum/qsharp-overview)
- [Microsoft Learn — Q# projects and Python integration](https://learn.microsoft.com/en-us/azure/quantum/how-to-work-with-qsharp-projects)
- [Microsoft Learn — Hybrid quantum computing](https://learn.microsoft.com/en-us/azure/quantum/hybrid-computing-overview)
- [Amazon Braket — Hybrid Jobs](https://docs.aws.amazon.com/braket/latest/developerguide/braket-jobs.html)
- [Amazon Braket — Hybrid algorithms](https://docs.aws.amazon.com/braket/latest/developerguide/hybrid.html)
- [AWS — Braket Hybrid Jobs](https://docs.aws.amazon.com/braket/latest/developerguide/braket-jobs.html)
- [AWS — QAOA Hybrid Job example](https://docs.aws.amazon.com/braket/latest/developerguide/braket-jobs-run-qaoa-algorithm.html)
- [Microsoft — Quantum resource estimator](https://learn.microsoft.com/en-us/azure/quantum/install-run-resource-estimator)
- [Hello Games — No Man's Sky press and ongoing universe](https://www.nomanssky.com/press/)
- [Hierarchical WaveFunction Collapse, AAAI AIIDE](https://ojs.aaai.org/index.php/AIIDE/article/view/27498)
