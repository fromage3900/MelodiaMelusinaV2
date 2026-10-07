# Melodia Animation Finishing + Shorewake Transformation Convergence Day — 2026-10-07

> **MUSE / HUMBER BOOTSTRAP FIRST:** `START_HERE_HOUDINI_2026-10-07.md`
>
> Do not start this document from the top on a fresh school machine. The front door contains the audited repo/SSD/license/artifact discovery path and a 10-minute cap on recovery work.

> Companion execution plan to `Docs/Houdini/MELODIA_HOUDINI_STUDIO_CONVERGENCE_2026-10-07.md`.
>
> **Scope today:** AnimationDoctor expansion, Sir Melodious avian polish, Shorewake Vellum/VAT finishing, Copernicus-driven transformation lookdev, and one bounded UE proof.
>
> **Planning-only commit:** this document does not claim any new HDA, Vellum solve, Copernicus bake, material edit, or UE proof has been completed.

## Mission

Use the full Houdini school session to first establish a comfortable **repo-backed Melodia Houdini Studio desktop/package**, then recover and regression-test the **owner-reported working local AnimationDoctor**, turn that same implementation into a **character finishing lab**, and use the already-staged Shorewake outfit as the hero convergence canary.

**Audit correction:** the successful AnimationDoctor from 2026-10-06 is not currently represented on Git main as a tracked HDA/HIP/PASS receipt. Git contains its mission/specification; the synced G: project/SSD is the expected recovery source for the actual working Houdini artifact. Muse must recover before extending, and must not reconstruct a new canonical Doctor from prose merely because Git search comes up empty.

The target is not “more procedural systems.” The target is one coherent authored chain:

```text
approved animation
  -> AnimationDoctor normalization / diagnostics
  -> KineFX motion + transition polish
  -> character-profile finishing
  -> Shorewake Vellum / VAT / secondary solve where justified
  -> Copernicus-authored fields and masks
  -> existing Magical Transform presentation vocabulary
  -> existing Wardrobe equip/state
  -> existing audio/cymatic readers
  -> UE 5.8 visual proof
```

Houdini authors and bakes. Unreal owns runtime state. Existing writers remain the only writers.

## Audit findings that change execution

1. **AnimationDoctor is local-first today.** No tracked `HDA_Melodia_AnimationDoctor*.hda`, AnimationDoctor HIP, or PASS receipt is visible on current main. Follow `START_HERE_HOUDINI_2026-10-07.md` and spend at most 10 minutes locating yesterday's local asset/session.
2. **The older Sir Houdini probe is not a dependency.** `hython_kinefx_probe.py` is referenced by the Sir plan but is not present in Git. The newest described Sir family is the v5 ARP lane in `Saved/Audit/SirMelodious_FlightUnit_20261003/PLAN.md`; select local v5 artifacts first.
3. **Shorewake has multiple generations.** Current runtime identity is `SK_ShorewakeDress_Melusina465`; the Aug-30/31 48MAT/magical-transform lane is historical and must not be selected just because its scripts are convenient.
4. **The old Copernicus dress baker is not clean-clone-safe.** `copernicus_dress_bake.py` depends on local `reef_common.py`, which Foundry intake records as missing from Git. Probe the synced SSD before use. If absent, consume existing ShorewakeTidepool outputs instead of repairing the old baker during setup.
5. **Workspace/package setup is Gate 0 today.** Repo search found no existing project-authored Houdini package, Melodia shelf, or saved desktop. Because today's work is interactive KineFX/Vellum heavy, build the portable `Melodia_Studio` + `Melodia_KineFX` environment first, using `START_HERE_HOUDINI_2026-10-07.md`. Do not edit `houdini.env`; use a thin local package pointer to repo-backed plugin content.
6. **`Tools/*` and `Saved/` ignore rules matter.** A new script or evidence receipt can exist locally and still be invisible to normal Git status. Check `git check-ignore -v` before assuming work is tracked.

## Authority boundaries — binding

1. **Wardrobe/save authority stays in Unreal.**
   - `UMelodiaWardrobeSubsystem` / wardrobe component owns equipped identity.
   - `specs/wardrobe/wardrobe_shorewake_manifest.v1.json` remains the current Shorewake gameplay contract.
   - Houdini must not invent durable outfit state.

2. **Magical Transform remains the runtime reveal authority.**
   - `UMelodiaMagicalTransformComponent` owns the per-character MID parameters:
     - `MagicalTransformProgress`
     - `MagicalTransformDissolve`
     - `MagicalTransformBloom`
     - `MagicalTransformSparkle`
     - `MagicalTransformBeat`
     - `MagicalTransformTint`
     - `Opacity` / `OpacityStrength`
   - It also owns only its two world-side MPC mirrors:
     - `MagicalTransform`
     - `MagicalTransformFlare`
   - Do not create a second transform timeline, Blueprint writer, OSC transform writer, or duplicate parameter vocabulary.

3. **Audio/cymatic single-writer rules stay binding.**
   - Current authority: `Docs/Architecture/AUDIO_REACTIVE_CANON.md`.
   - Current editor audio bridge remains the documented OSC lane; do not normalize or reassign ports as part of this outfit pass.
   - `UMelodiaCymaticsWriterSubsystem` remains sole writer of `MPC_Cymatics_Driver`.
   - Materials, Niagara, Houdini-authored assets and the outfit are **readers/consumers** of existing signals.

4. **Houdini Engine is editor authoring, not shipping runtime authority.**
   - Live cook is allowed for authoring/iteration.
   - Bake/cache/version outputs for runtime.
   - No packaged Houdini cooking is introduced today.

5. **Universe Foundry may orchestrate/evidence-gate the work, but does not become a garment generator.**
   - Preserve `mission_ref` provenance where an existing seam allows it.
   - Do not force the outfit through World Compiler. World Compiler is used only when a result is genuinely world/PCG content.

## Ground truth across Git + synced local project

Do not rebuild these from scratch. Git is authority for architecture/contracts; the synced local project may contain yesterday's unpromoted Houdini working assets and large derived inputs.

### Shorewake asset / lookdev lanes

Existing current or historical sources include:
- `Docs/Production/CANONICAL_SHOREWAKE_SUBSTANCE_STAGING_PIPELINE_2026-09-02.md`
  - weighted/unwrapped canonical outfit stage;
  - 28 material sets;
  - Chladni eigenmode resource family;
  - geometry bake resources.
- `Docs/Art/UNIVERSAL_GARMENT_FABRIC_DRAPERY_2026-09-02.md`
  - existing cloth tier doctrine;
  - `M_Skirt_Full` already identified as Tier D hero drape;
  - Vellum -> VAT direction already specified.
- `Docs/Art/DRESS_HOUDINI_SETUP_REVIEW_2026-08-30.md`
  - old and newer Shorewake build lanes, including superseded transformation paths.
- `Tools/Houdini/copernicus/`
  - deterministic dress/Cymatic/Copernicus work already exists.
- `Saved/Audit/copernicus_cymatic/ShorewakeTidepool/`
  - existing Chladni/eigenmode family.
- current wardrobe manifest points the runtime skirt slot at
  `/Game/Melodia/Characters/Melusina/Textures/Clothes/Retargeted/SK_ShorewakeDress_Melusina465`.

**Gate:** before sim or rebake, Muse must prove which current weighted mesh corresponds to the runtime asset. Do not silently revive the Aug-30/31 dress lane because it has convenient scripts.

### Existing transformation presentation

`MelodiaMagicalTransformTypes.h` and `wire_magical_transform_reveal.py` already define the reveal vocabulary and safe default-off material path.

This is a gift: Houdini does **not** need to own transformation playback. It should produce better motion, masks, fields, VAT/cache data and timing evidence that the existing runtime transform consumes.

---

# Three-phase execution plan

## PHASE 1 — AnimationDoctor becomes an Animation Finishing Lab

### Goal

After the bootstrap front door has recovered and regression-tested yesterday's exact Doctor implementation, generalize that implementation without forking it into character-specific HDAs. If recovery returns `ANIM_DOCTOR_LOCAL_ARTIFACT_MISSING`, do not create a replacement HDA inside Phase 1; switch to the fallback work order in the front door.

Keep the proven spine:

```text
REST
-> ROOT
-> CONTACT
-> JOINT HEALTH
-> RETARGET
-> MOTION POLISH
-> CHARACTER PROFILE
-> EVENT EXTRACTION
-> OUTPUT
```

### 1A — Sir Melodious avian profile

Add an optional `avian` profile to the existing Doctor, not `AnimationDoctor_Bird`.

Semantic groups to discover/map where present:
- body/root
- neck
- head
- beak
- crest
- wing_L / wing_R
- primary/secondary feather chains
- tail
- thigh / hock / foot / toes

Diagnostics / polish:
- wing fold/unfold continuity;
- joint-limit and orientation sanity;
- crest and tail controlled secondary motion;
- head stabilization;
- perch contact / toe target stability;
- landing/takeoff COM transition;
- wing-body collision envelope;
- intentional L/R asymmetry allowed, accidental inversion rejected.

Use KineFX Secondary Motion / constraints where appropriate. Keep primary authored animation intact.

### 1B — Melusina polish profile

Semantic groups:
- head/neck;
- hands/fingers;
- hair chains;
- skirt drivers;
- sleeves/ribbons;
- ornaments;
- face/blendshape channels if present.

Polish goals:
- remove mechanical transition pops;
- improve settle/overlap;
- retain clean silhouette;
- preserve feet/root contacts;
- generate conservative joint-limit envelopes from approved clips for human review;
- test at least one blend/transition pair, not only one isolated clip.

### 1C — Animation-derived VFX timing manifest

Derive **events**, not final runtime effects.

Candidate signals:
- foot contact;
- landing impulse;
- takeoff;
- wing apex;
- wing acceleration;
- hand/weapon gesture acceleration;
- cloth angular/linear velocity peak;
- crest compression/release;
- COM acceleration;
- transition start / visual peak / settle.

Output a small versioned manifest usable by UE authoring:
```text
event_name
frame/time
normalized_strength
semantic_source
clip_id
character_profile
input_hash
```

Do not make Houdini a gameplay event authority. These are authoring suggestions/evidence until intentionally wired to UE.

### Phase 1 exit gate

PASS only when:
- Melusina still passes the original Doctor checks;
- Sir Melodious passes the same Doctor with an avian profile;
- one transition per character has before/after evidence;
- no canonical skeleton was changed to accommodate a source clip;
- profiles are data/config, not duplicated Doctor implementations.

---

## PHASE 2 — Shorewake Vellum + Magical Transformation Convergence

### Goal

Use the full Houdini licence to finally execute the expensive hero-garment work already planned, while keeping the transformation runtime exactly where it belongs.

### 2A — Resolve the real Shorewake source first

Before any solve:
1. inventory the current runtime `SK_ShorewakeDress_Melusina465`;
2. inventory the weighted/unwrapped canonical Shorewake source;
3. compare skeleton, material regions, topology identity where possible, UVs and garment groups;
4. identify which historical tools are valid helpers versus superseded lanes;
5. write a source-selection receipt.

STOP if the proposed Vellum source cannot be proven to correspond to the current runtime garment.

### 2B — Constraint zones

Prefer semantic masks over one global cloth setting.

Suggested garment fields:
- `PIN` — waistband / hard attachments;
- `STRUCTURE` — bodice / load-bearing cloth;
- `SOFT` — controlled secondary cloth;
- `FREE` — skirt body;
- `HEM` — highest freedom / flourish;
- `COLLISION_GUARD` — regions that must not tunnel;
- optional `FX_ACCENT` — where transformation/VFX may concentrate.

These masks can be painted/derived in Houdini and emitted as attributes/textures for downstream use.

### 2C — Vellum finishing

Reuse the existing tier doctrine:
- rigid/structured pieces remain bone driven;
- light secondary pieces use restrained soft-pin/secondary solutions;
- `M_Skirt_Full` gets the expensive hero solve;
- hidden/support layers stay cheap.

For the hero skirt:
```text
approved Melusina animation
-> body collision proxy
-> waistband pins
-> Vellum settle
-> animated solve
-> post-process / smoothing
-> loop/transition check
-> cache + optional VAT bake
```

The purpose is **animation finishing**, not physically perfect cloth.

Run several bounded presets in parallel:
- Structured Satin
- Silk
- Light Chiffon
- Magical / slightly underdamped hero preset

Each preset must use the same input clip and publish parameters + evidence. Human picks the winner.

### 2D — Compose, do not replace, Magical Transform

Runtime composition target:

```text
base skeletal animation
+ approved Vellum/VAT secondary motion
+ Copernicus spatial masks/fields
+ UMelodiaMagicalTransformComponent progress/flare/tint
+ existing audio/cymatic readers
= Shorewake final presentation
```

The Vellum/VAT motion should continue to work whether transform progress is 0, mid-transition or 1.

### Phase 2 exit gate

PASS only when:
- canonical source is proven;
- one hero skirt solve is approved;
- a cache/VAT or equivalent reproducible output exists;
- transform parameters remain owned by `UMelodiaMagicalTransformComponent`;
- zero new wardrobe/save authority exists;
- original runtime outfit can be restored without data loss.

---

## PHASE 3 — Copernicus + WPO + Hue + Reactive VFX Proof

### Goal

Use Houdini/Copernicus as the **authoring field generator** and UE as the live consumer.

This is where the Shorewake transformation can finally feel like one material/cloth/VFX event rather than a mesh swap plus unrelated sparkles.

## What Copernicus should author

Good candidates:
- Chladni/eigenmode height;
- emissive mask;
- iridescence field;
- curvature/thickness-aware accent mask;
- flow/direction mask;
- dissolve/noise field;
- hem accent mask;
- VFX spawn-density mask;
- optional flipbook;
- VAT textures when the data is actually encoded as VAT.

SideFX Copernicus may interoperate with SOP geometry and export image/volume data; exploit that during authoring, but export/version the results for runtime.

## Runtime mapping — allowed and useful

| Authored / live input | Runtime consumer | Intended effect |
|---|---|---|
| Copernicus height/eigenmode | WPO material lane | bounded hem/skirt lift, resonance ripple, surface breathing |
| Copernicus emissive/curvature | material emissive | transformation wavefront accent |
| Copernicus iridescence | material colour/iridescence | pearl/tide colour travel |
| `MagicalTransformProgress` | per-MID material | master reveal amount / WPO blend weight |
| `MagicalTransformFlare` | world-side readers | bounded bloom/VFX intensity |
| `MagicalTransformTint` | per-character material | authored transformation hue/tint |
| existing palette `PaletteShift` / audio lanes | read-only material response | optional audio colour modulation where semantically correct |
| existing BeatPulse / Cymatic driver | read-only material/Niagara | beat accent, sparkle, ripple, small WPO impulse |
| AnimationDoctor event manifest | UE authoring / Niagara trigger setup | landing, wing apex, gesture, cloth-peak accents |
| VAT position/normal textures | garment WPO/VAT function | exact precomputed vertex animation |

### Important distinction: “translate position”

There are three different operations; do not conflate them.

1. **Visual vertex displacement**
   - WPO is appropriate.
   - Great for hem lift, ripple, breathing, wavefront displacement.
   - Does not move collision/gameplay/root state.

2. **Exact baked cloth deformation**
   - use VAT/cache data specifically authored for per-vertex motion.
   - A generic Copernicus `Position` bake is **not automatically a VAT**.
   - Do not treat an ordinary position map as exact animated vertex translation unless its vertex lookup contract is proven.

3. **Actor/component/root translation**
   - belongs to animation/gameplay/component logic in UE.
   - never drive this by a material or a random OSC scalar.

## Hue strategy

Prefer existing vocabulary before adding another parameter:
- transformation-authored hue: `MagicalTransformTint`;
- audio/global palette movement: existing palette readers such as `PaletteShift`, when semantically correct;
- surface-specific hue parameters only when the target material already owns them or an approved default-off extension is required.

Do not add `ShorewakeHue`, `ShorewakeAudioHue`, etc. merely because a prototype needs colour travel.

## OSC strategy

**No port work is required to prove this phase.**

Read `Docs/Architecture/AUDIO_REACTIVE_CANON.md` before touching OSC. Current live/editor wiring and single-writer rules win over stale port prose elsewhere.

For today:
- no new socket;
- no second Python bridge;
- no OSC route directly writing `MagicalTransformProgress`;
- no direct OSC writes to `MPC_Cymatics_Driver`;
- audio enters through the current canonical palette path;
- transform playback remains wardrobe/transform-component driven;
- materials/Niagara simply read the resulting signals.

If a port or routing mismatch is discovered, document it and stop that subtask. Do not “fix the ports while we are here.”

## Bounded visual canary

Use **one Shorewake transformation clip**.

Prove this sequence:
1. Melusina enters approved animation.
2. AnimationDoctor-polished clip plays.
3. Vellum/VAT skirt follows without a pop.
4. Existing Magical Transform reveal begins.
5. Copernicus mask shapes dissolve/WPO/emissive response.
6. Existing beat/audio lane may add a bounded accent.
7. Niagara/VFX timing follows one derived animation event.
8. Transform settles fully revealed.
9. Return to baseline/reload proves deterministic restoration.

Capture:
- side-by-side raw vs polished;
- Vellum preset contact sheet/playblast;
- material parameter values at start / peak / settle;
- one UE viewport capture;
- hashes/manifests for the chosen bake.

---

# Parallel execution on Humber machines

Use the school hardware for **parallel computation**, not parallel architecture.

One Muse coordinator owns decisions and merges evidence.

**Do not launch these workers until bootstrap reports the selected Doctor/Sir/Shorewake sources.** Otherwise every worker will independently rediscover stale lanes.

Safe workers:

### Worker A — Sir Melodious / avian Doctor
- profile mapping;
- joint limits;
- wing/crest/tail secondary;
- perch/takeoff/landing checks.

### Worker B — Shorewake Vellum
- source audit first;
- collision/pin masks;
- 3-4 deterministic cloth presets;
- cache/VAT candidate;
- no UE writes.

### Worker C — Copernicus transformation fields
- consume existing ShorewakeTidepool/bake resources;
- generate candidate masks/height/emissive/iridescence/flow fields;
- preserve seed/input hash/output hashes;
- no material authority.

### Worker D — Animation/VFX timing extraction
- derive motion/contact events from approved clips;
- emit manifest + plots/contact sheet;
- no gameplay binding.

### Worker E — Runtime seam audit
- read-only inspect Magical Transform, wardrobe, material functions, audio/cymatic consumers;
- identify the smallest existing seam for WPO/VAT/mask consumption;
- no new master or OSC design unless a hard blocker is proven.

### Serialization rule

Houdini batch solves can run in parallel.
Copernicus bakes can run in parallel.
Read-only UE audits can run in parallel.

**Actual UE asset/material writes are serialized: one editor writer at a time.**

---

# Muse Spark execution order

## P0 — Melodia Houdini Studio first, then audited source selection
Follow `START_HERE_HOUDINI_2026-10-07.md` exactly.

Timebox:
- repo + GUI licence preflight: **~2 minutes**;
- repo-backed package + `Melodia_Studio` / `Melodia_KineFX` desktops + shelf verification: **20–30 minutes**;
- AnimationDoctor local recovery: **10 minutes**;
- then return the compact bootstrap report from the front door.

The package/desktop setup is the first productive deliverable and remains useful for every later Houdini session.

Required selections before P1:
- recovered AnimationDoctor artifact type/path or explicit MISSING verdict;
- one known-good Melusina regression specimen;
- Sir v5 ARP source family path;
- current Shorewake runtime FBX path;
- canonical Shorewake USD presence/absence;
- ShorewakeTidepool presence/absence;
- `reef_common.py` presence/absence.

Do **not** begin by reading every Foundry document, fixing OSC ports, or repairing historical Copernicus scripts. The shelf/desktop design is now intentional P0 work; keep it bounded to the audited plugin structure in the front door rather than inventing a broader Houdini framework.

## P1 — Doctor / character polish
- Melusina regression pass;
- Sir avian profile;
- transition polish;
- event extraction.

## P2 — Shorewake cloth
- canonical source proof;
- constraints;
- Vellum preset batch;
- select one;
- cache/VAT evidence.

## P3 — transformation composition
- bind chosen authored masks/fields through existing material vocabulary;
- default-off identity check;
- preserve transform component ownership.

## P4 — reactive accent
- one WPO effect;
- one hue/tint response;
- one VFX event;
- existing audio/cymatic read only.

## P5 — UE proof
- one bounded transform run;
- restore baseline;
- record evidence;
- only then update canon/status docs.

---

# Stop conditions

Stop and report instead of widening scope if:

- Shorewake source identity cannot be proven;
- a proposed fix requires changing the canonical Melusina skeleton;
- Vellum requires replacing the approved primary animation;
- a generic position texture is being mistaken for VAT;
- a material effect would move gameplay collision/root state;
- a worker proposes a second Magical Transform writer;
- a worker proposes direct OSC -> `MPC_Cymatics_Driver`;
- a worker proposes a new OSC socket before proving the current routing insufficient;
- a new master material is proposed where a default-off extension of the existing material lane would work;
- the outfit is being forced through World Compiler solely to make the architecture diagram symmetrical;
- a historical Shorewake mesh is about to overwrite the current runtime asset without source proof.

---

# Definition of done today

A successful day assumes the local Doctor is recovered. If it is genuinely missing after the audited recovery cap, log that packaging gap and continue the Shorewake/Sir source work without pretending a replacement HDA is yesterday's pipeline.

When recovered, the target is:

1. The recovered AnimationDoctor regression passes on Melusina and the same implementation handles Sir Melodious through a profile.
2. One Sir avian clip receives useful Houdini-native polish.
3. One Melusina transition is cleaner than its raw source.
4. Current Shorewake source identity is proven.
5. One Vellum/VAT hero-skirt result is approved and reproducible.
6. Copernicus provides at least one useful transformation field/mask.
7. Existing Magical Transform remains the sole reveal writer.
8. One bounded WPO response works.
9. One bounded hue/tint response works.
10. One animation-derived VFX event is demonstrated.
11. Existing audio/cymatic/OSC writer boundaries remain intact.
12. UE can return to the original deterministic state.

That is enough. Do not turn a successful finishing day into a rewrite of the renderer, wardrobe, world compiler, or signal architecture.
