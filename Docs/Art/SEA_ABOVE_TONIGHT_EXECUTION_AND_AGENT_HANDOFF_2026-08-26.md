# Sea Above — Tonight Execution + Agent Handoff Plan — 2026-08-26

Status: **execution-ready prototype plan**  
Scope: **docs + prototype guidance only**  
Target branch: `docs/monolith-concept-art-backlog-2026-08-26`  
Primary goal: prove the **Sea Above** visual thesis in-engine tonight using the existing Water V10 production family without destabilizing production water, runtime bridges, World Partition, or native-water promotion work.

---

## 0. Creative thesis

> The player discovers what appears to be a second ocean and sky beneath the real sea, then realizes the false horizon is the translucent bell/body of a colossal pelagic organism rising toward the world.

The prototype must sell this sequence:

1. **Normal coast** — serene, readable, beautiful.
2. **Anomaly** — bubbles/rain/fish behave incorrectly.
3. **Second horizon** — another blue sky/ocean is visible beneath the water.
4. **Bell pulse** — the false horizon reveals faint radial anatomy.
5. **Biological realization** — the viewer understands they were looking at an organism, not another world.

Do **not** try to finish the full boss, inverted-gravity traversal, swimming transitions, or encounter logic tonight. The prototype exists to answer one production question:

> Can the current Melodia water stack make the player believe another ocean exists beneath the world?

---

## 1. Existing project facts to preserve

### Canonical production water line

Use the existing production family around:

`/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v10_Upgrade`

The current project documentation identifies this as the canonical Water V10 master. It preserves the V9 art-direction graph — wave, ripple, proximity foam, bioluminescence, normals, WPO, and Substrate water outputs — while adding the native interaction compatibility layer.

The five integrated V10 instances are under:

`/Game/EnvSandbox/Materials/Instances/Water/v10/Integrated/`

with the established families:

- CalmPond
- BiolumGrotto
- CinematicHero
- OceanPreview
- RiverClear

### Production constraints

- `M_Water_Master_Grand_v10_Substrate` remains a **study line**. Do not promote or modify it during this prototype.
- Do not revive deprecated toon-water masters.
- Do not reparent existing V6/V7/V9 families.
- Do not change Melusina hair water material ownership.
- Do not rely on `RefractionStrength` as a required feature for Sea Above until a fresh graph audit proves it is actually connected.
- Do not add SceneDepth logic to the opaque SingleLayerWater surface graph. Screen-space depth behavior belongs in the underwater/post-process lane.
- V10 already contains the world-UV repair path; preserve it. The integrated family currently relies on world-space texture scales roughly in the `0.0009–0.0016` range, with `WaterV10WorldUVBlend=1.0` for the verified family.

### Current technical debt that is explicitly *out of scope tonight*

Do not let Sea Above absorb unrelated Water V10 promotion work:

- native Water Body body-level replay and slot promotion;
- Niagara Data Channel consumer proof;
- one-contact/one-response runtime replay;
- Water audio activation proof;
- Tier 2/3/4 performance capture;
- packaged World Partition audit;
- cold-build blockers unrelated to Water;
- V11 authoring.

---

## 2. Tonight definition of done

The prototype is complete when all of the following are true:

- [ ] One isolated Sea Above prototype map exists.
- [ ] Existing production validation/world maps remain untouched.
- [ ] One real surface-water presentation exists.
- [ ] One false-ocean plane exists beneath it.
- [ ] One giant Bell proxy implies regional creature scale.
- [ ] One lightweight membrane material exists outside the production water master.
- [ ] At least one upward-moving atmospheric Niagara effect exists.
- [ ] A slow 12–20 second Bell pulse is visible.
- [ ] The reveal reads from a fixed 16:9 hero camera.
- [ ] A 20–30 second playable/cinematic approach demonstrates normality -> second horizon -> Bell pulse.
- [ ] No production Water master was edited.
- [ ] No V9/V10 integrated production instance was destructively edited.
- [ ] No C++ or Data Channel changes were made for the prototype.
- [ ] One clean screenshot and one short capture are saved for review.

Stretch goal only after the above passes:

- [ ] A small falling ruin/debris piece crosses the false surface and produces an **upward splash**.

---

## 3. Recommended prototype asset layout

Use a clearly disposable/isolated prototype namespace. Suggested names:

### Level

`/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype`

### Material instances

`MI_SeaAbove_SurfaceOcean`

`MI_SeaAbove_FalseOcean`

These should be duplicates/children derived from the integrated V10 family, not edits to the canonical production instances.

Recommended starting parents:

- Surface Ocean: `MI_WaterV10_Integrated_RiverClear` or `MI_WaterV10_Integrated_CalmPond`
- False Ocean: `MI_WaterV10_Integrated_CinematicHero` or `MI_WaterV10_Integrated_OceanPreview`

### Creature membrane prototype

`M_SeaAbove_Membrane_Prototype`

Keep it completely separate from `M_Water_Master_Grand_v10_Upgrade`.

### Niagara prototypes

`NS_SeaAbove_UpwardDroplets_Prototype`

Optional stretch:

`NS_SeaAbove_UpwardSplash_Prototype`

### Creature proxy

`SM_SeaAbove_BellProxy_Prototype`

This may initially be an engine sphere/hemisphere or trivial DCC primitive; no production sculpt is required.

### Capture

`CINE_SeaAbove_HeroReveal_Prototype`

Use a single reliable hero-camera path before attempting multiple angles.

---

## 4. Tonight schedule

Times are approximate. The schedule is intentionally biased toward a visible result rather than infrastructure.

### Phase A — 20 min — isolate the map

1. Duplicate a safe existing Water validation/lookdev environment into `LV_SeaAbove_Prototype`.
2. Keep the source validation map unchanged.
3. Preserve one Water Body / Water Zone / existing sky setup only if it helps composition.
4. Remove anything that obscures the hero view.
5. Capture a baseline screenshot before Sea Above changes.

**Exit gate:** a clean coastal/cliff overlook exists and the prototype is isolated.

### Phase B — 40 min — create two water looks

#### Surface Ocean

Target: beautiful, quiet, readable water.

Initial tuning direction:

- lower wave amplitude than hero-ocean default;
- restrained ripple/foam activity;
- little or no visible bioluminescence in normal state;
- smooth but not perfect-mirror roughness;
- preserve world-UV behavior;
- shallow aquamarine into saturated/deeper blue.

#### False Ocean

Target: water that initially reads more like a sky or unreachable mirror-world than a second normal sea.

Initial tuning direction:

- wave amplitude about 20–35% of a normal ocean read;
- very slow wave/pan speed;
- foam near zero;
- subtle cyan/violet bioluminescent lift;
- `WaterV10WorldUVBlend=1.0` unless a specific visual test proves otherwise;
- begin world texture-scale lookdev near `0.0012`, then adjust by eye;
- deep cyan -> violet/indigo palette;
- do not make prototype success depend on refraction.

**Exit gate:** the two surfaces are visually distinct but still belong to the same art family.

### Phase C — 40 min — construct the second horizon

1. Create/place a very large static-mesh plane roughly 500m x 500m for first-pass composition.
2. Position it about 100–250m below the real surface as a starting point.
3. Assign `MI_SeaAbove_FalseOcean`.
4. Use exponential height fog / volumetric atmosphere / view composition to hide literal plane spacing.
5. Add a soft emissive sky/hemisphere/card beneath the false ocean.
6. Add slow cloud/noise motion beneath the water so the player reads **sky under sea**.

**Important:** physical correctness is not the target. Perceptual ambiguity is.

**Exit gate:** from the hero overlook, viewers can see a second horizon but cannot immediately measure or explain it.

### Phase D — 40 min — giant Bell proxy

1. Add a sphere/hemisphere or very low-complexity Bell proxy.
2. Scale it to an apparent multi-kilometre diameter.
3. Sink most of it beneath/behind the false ocean.
4. Create `M_SeaAbove_Membrane_Prototype` with only:
   - Fresnel;
   - blue/violet tint;
   - low opacity;
   - slow panning noise;
   - subtle emissive rim;
   - one exposed pulse scalar.
5. Hide the edges of the proxy with fog and framing.
6. Do not model tentacles, organs, veins, mouthparts, or traversal structures tonight unless they directly improve the hero shot.

**Exit gate:** the viewer does not read a sphere; they read a huge curved biological presence whose total size is unknown.

### Phase E — 30 min — three anomalies

Implement only three signals:

1. **Upward droplets/rain/bubbles** — simple Niagara, no Data Channel dependency.
2. **Distant fish/debris silhouettes** — cards or cheap meshes moving through the false-sky volume.
3. **Bell shadow / opacity sweep** — one very slow, very large movement below the false ocean.

Do not create systemic AI or simulation for these.

**Exit gate:** the environment communicates that physical rules are wrong before the Bell becomes obvious.

### Phase F — 30 min — biological pulse

Target period: **12–20 seconds**.

On pulse:

- membrane emissive rises;
- membrane WPO/scale subtly expands and relaxes;
- false-ocean brightness/biolum response lifts slightly;
- upward particles momentarily accelerate or intensify;
- optional tiny camera impulse / low-frequency audio cue.

Preferred integration order:

1. Reuse an existing project MPC/rhythm presentation control **only if it is already exposed and takes under ~15 minutes to hook up**.
2. Otherwise use a Timeline or simple material parameter animation for the prototype.

Prototype feeling outranks architecture tonight.

**Exit gate:** one pulse recontextualizes the entire horizon as anatomy.

### Phase G — 40 min — art-direct three shots

#### Shot A — Normality

Melusina approaches a serene coast. No obvious monster read.

#### Shot B — Second Horizon

The player reaches the overlook and sees a second luminous blue horizon beneath the real sea.

#### Shot C — Biological Realization

A Bell pulse reveals faint radial anatomy/curvature. The player understands the second world is alive.

Composition rule:

> The player should need several seconds to realize the Bell is present.

### Phase H — 30 min — scale + capture + stop

Use differential motion to imply scale:

- near grass/cloth/droplets: normal speed;
- mid mist/waves: slower;
- false horizon: almost stationary;
- Bell: extremely slow 10–20 second contraction, with no bobbing.

Capture:

1. one clean 16:9 screenshot;
2. one 20–30 second approach/reveal sequence;
3. one diagnostic screenshot showing layer placement if useful for handoff.

Then stop. Do not turn a successful visual prototype into a midnight engine refactor.

---

## 5. Agent handoff matrix

The following lanes are intentionally separable so multiple agents can contribute without editing the same production assets.

| Lane | Owns | Must not touch | Deliverable |
| --- | --- | --- | --- |
| Environment / Level | map composition, cliff vista, plane placement, fog, scale cues | production Water masters, C++, NDC | playable hero vista + camera |
| Water Lookdev | prototype MIs only | canonical master graph, existing integrated MI overrides | SurfaceOcean + FalseOcean looks |
| Creature / Material | Bell proxy + membrane material | Water master, production creature pipeline | readable Bell silhouette + pulse scalar |
| Niagara / Atmosphere | upward droplets, silhouettes, optional splash | production contact/NDC bridge | isolated prototype Niagara systems |
| Rhythm / Presentation | pulse timing and optional existing MPC hook | new runtime subsystem, combat gates | 12–20 sec reliable pulse |
| Capture / Validation | screenshots, short video, change audit | content authoring outside capture fixes | evidence package + go/no-go notes |

---

## 6. Agent-specific handoff instructions

### Agent A — Environment / Level Composition

**Mission:** create the Sea Above hero vista using existing water infrastructure and primitive geometry.

**Inputs:**

- this document;
- current Water validation/lookdev map as reference;
- `MI_SeaAbove_SurfaceOcean`;
- `MI_SeaAbove_FalseOcean`;
- Bell proxy from Agent C when available.

**Steps:**

1. Duplicate rather than edit the existing validation map.
2. Establish a coastal overlook with a strong downward sightline.
3. Place real water, then false-ocean plane below it.
4. Place atmospheric gap/fog between layers.
5. Add under-ocean sky/hemisphere.
6. Place Bell proxy so its full edge is never visible.
7. Establish one fixed hero camera and one short walk-in path.
8. Keep traversal simple; no gravity changes tonight.

**Output:**

- `LV_SeaAbove_Prototype` saved;
- one screenshot from the hero camera;
- short note with surface Z, false-ocean Z, Bell approximate scale, camera lens/FOV.

**Stop conditions:**

- stop if success requires editing the Water master;
- stop if World Partition re-authoring becomes necessary;
- stop if the false plane needs more than atmosphere/composition to read.

### Agent B — Water Lookdev

**Mission:** derive two prototype water looks from V10 integrated instances without production-family mutation.

**Steps:**

1. Duplicate approved integrated instances into Sea Above prototype namespace.
2. Create calm real-water presentation.
3. Create uncanny false-ocean presentation.
4. Preserve world-UV behavior.
5. Verify neither parent/canonical instance was edited.
6. Do not rely on refraction as a hard requirement.

**Output:**

- two saved prototype MIs;
- parameter-delta notes relative to their parents;
- one side-by-side screenshot if easy.

**Stop conditions:**

- no master-graph edits;
- no V11 work;
- no reparenting existing integrated families;
- no SceneDepth experiments in SingleLayerWater.

### Agent C — Bell / Membrane

**Mission:** imply a creature several kilometres across using the least geometry possible.

**Steps:**

1. Start with sphere/hemisphere primitive.
2. Build separate `M_SeaAbove_Membrane_Prototype`.
3. Expose `Pulse` scalar.
4. Add Fresnel + tint + panning breakup + low emissive.
5. Tune silhouette through fog, not mesh detail.
6. Test Bell at extreme scale and ensure the surface does not reveal obvious primitive topology.

**Output:**

- Bell proxy;
- membrane material;
- pulse parameter documented;
- screenshot of off/on pulse.

**Stop conditions:**

- no skeletal rig;
- no tentacle production model;
- no complex translucency/refraction stack;
- no dependence on full body visibility.

### Agent D — Niagara / Atmosphere

**Mission:** communicate impossible physics with minimal, isolated VFX.

**Steps:**

1. Build upward-moving droplets/bubbles.
2. Keep spawn count low enough for immediate iteration.
3. Add optional distant cards/particles for fish/debris motion.
4. If time remains, create upward-splash stretch prototype.
5. Place Niagara directly in prototype map.

**Output:**

- `NS_SeaAbove_UpwardDroplets_Prototype`;
- optional `NS_SeaAbove_UpwardSplash_Prototype`;
- brief cost/readability note.

**Stop conditions:**

- do not edit Water Data Channel bridge;
- do not replace contact/ripple production systems;
- do not create required FLIP dependencies.

### Agent E — Rhythm / Presentation Pulse

**Mission:** make the creature feel alive with one reliable, slow pulse.

**Steps:**

1. Check whether an existing safe MPC/presentation parameter can drive the effect quickly.
2. If hook-up exceeds roughly 15 minutes, use Timeline/local material parameter control.
3. Drive Bell emissive and subtle WPO/scale.
4. Optionally drive false-water biolum lift and Niagara intensity.
5. Reset values cleanly when prototype sequence stops.

**Output:**

- reproducible pulse period in 12–20 second range;
- list of driven parameters;
- no new gameplay/runtime subsystem.

**Stop conditions:**

- no combat dependency;
- no new authoritative rhythm writer;
- no save-system integration;
- no refactor of existing water presentation architecture.

### Agent F — Capture / Validation

**Mission:** prove the prototype and protect project integrity.

**Validation checklist:**

- verify canonical V10 master timestamp/content unchanged;
- verify production integrated instances unchanged;
- verify no V9 assets were reparented;
- verify no native-study-line edits;
- verify no C++ changes;
- verify no Data Channel/FLIP/World Partition changes;
- capture hero 16:9 screenshot;
- capture 20–30 second reveal;
- document visual failures or blockers as review notes rather than patching unrelated systems.

**Go/no-go question:**

> Does the second horizon convincingly read as another world before the Bell pulse reveals it as anatomy?

If **yes**, Sea Above graduates to phase-two preproduction.

If **no**, iterate composition/fog/relative scale first. Do not solve the problem by immediately increasing shader complexity.

---

## 7. Art-direction rules for all agents

1. **Wonder before horror.** The first read must be beautiful.
2. **No full-body reveal.** The Bell edge should disappear into haze/composition.
3. **Slow = large.** The creature moves much slower than the environment around it.
4. **Do not make both oceans equally noisy.** The false ocean should be quieter and stranger.
5. **Scale comes from parallax and occlusion, not polygon count.**
6. **Keep the anomaly count low.** Three strong wrong things are better than twelve weak ones.
7. **Do not tutorialize the reveal.** No boss bar or explanatory UI is required for prototype proof.
8. **Preserve Melodia readability.** The player silhouette and traversal foreground should remain legible.
9. **Avoid conventional monster language.** No obvious mouth/eyes/tentacle attack read in the first proof.
10. **The Bell pulse is the reveal.** Before the pulse, the viewer should plausibly believe the second horizon is environmental.

---

## 8. Phase-two backlog after tonight passes

Only schedule these after the hero-vista prototype works:

### A. Hanging Reefs traversal prototype

- suspended water volumes;
- inverted coral/reed silhouettes;
- simple swim/fall transitions;
- controlled orientation experiments.

### B. Pelagic Cathedral interior

- membrane arches;
- vascular columns;
- translucent biological windows;
- internal current routes;
- stronger creature pulse synchronization.

### C. Rhythm stability mechanic

- define whether rhythm stabilizes water volumes, gravity domains, membranes, or current direction;
- prototype one mechanic at a time;
- avoid coupling all traversal to rhythm before readability tests.

### D. Fashion-as-biological-semiotics prototype

Potential tags for later testing:

- pearlescent/iridescent -> symbiotic recognition;
- flowing/translucent -> juvenile-organism mimic;
- bioluminescent -> attraction / tendril pathing;
- dark/predatory -> defensive response.

Do not implement fashion hooks during tonight's visual proof unless an existing data path makes one trivial.

### E. Full encounter structure

Later sequence:

1. Cerulean Littoral;
2. Second Horizon;
3. Hanging Reefs;
4. Pelagic Cathedral;
5. Bell realization;
6. communication/de-escalation climax.

The final encounter should avoid a conventional weak-point kill unless later narrative work demands it.

---

## 9. Git / agent hygiene

- Keep generated reference images out of this docs commit unless intentionally added through the art asset pipeline.
- Prototype UE binary assets should land in isolated commits rather than being mixed with Water V10 core changes.
- Do not mix Sea Above prototype work with unrelated runtime convergence, wardrobe, save, combat, asset-lock, LFS, or native-water promotion work.
- If an agent needs to change a canonical Water asset, stop and create a separate proposal/review instead of silently expanding prototype scope.
- Every follow-up commit should state whether it changes:
  - prototype-only assets;
  - production materials;
  - code/runtime systems;
  - World Partition;
  - LFS/binaries.

Suggested commit batches once implementation begins:

1. `prototype(sea-above): block out second-horizon vista`
2. `art(sea-above): add isolated water lookdev instances`
3. `vfx(sea-above): add upward atmosphere and bell pulse`
4. `capture(sea-above): add validation evidence and notes`

Do not squash all implementation disciplines into one giant commit if multiple agents are working concurrently.

---

## 10. Handoff completion template

Every agent should leave this compact handoff in their PR/commit note:

```text
Sea Above lane:
Assets changed:
Assets intentionally not changed:
Visual/result status:
Evidence paths:
Known issues:
Next recommended owner:
Stop-condition encountered: yes/no
```

---

## 11. Final prototype review rubric

Score each 0–2.

| Criterion | 0 | 1 | 2 |
| --- | --- | --- | --- |
| Second horizon readability | absent | visible but confusing | instantly intriguing, not immediately explained |
| Creature ambiguity | obvious giant sphere/monster | partially hidden | reads as environment until pulse |
| Scale | ordinary | large | regional / unknowable |
| Water-family cohesion | disconnected | partly coherent | clearly Melodia water language |
| Performance pragmatism | expensive/fragile | tolerable | mostly planes, fog, MI tuning, cheap proxy |
| Reveal | no recontextualization | mild | Bell pulse changes understanding of the whole vista |
| Project safety | production assets altered | unclear | prototype isolated and canonical stack untouched |

**Pass target:** 11/14 or better, with mandatory score 2 in **Project safety** and at least 1 in **Reveal**.

---

## 12. One-sentence production rule

> Build Sea Above tonight as a perception trick using the water stack Melodia already has; earn the right to build the impossible mechanics only after the second horizon and Bell reveal work in a simple 20–30 second in-engine shot.
