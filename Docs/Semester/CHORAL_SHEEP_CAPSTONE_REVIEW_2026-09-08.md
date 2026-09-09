# Choral Sheep Capstone — Integrated Review

**Date:** 2026-09-08  
**Status:** REVIEWED / ACTIVE PRODUCTION  
**Game review head:** `3b57a5712257ee7ab6d1e4ada92f85f591a60cd4`  
**TouchDesigner review head:** `650d98a274ce845de5be6c937a4a385f5289795a`  
**Presentation spine:** **Creature → Motif → Harmony → World**

## Executive verdict

The capstone work is now **architecturally coherent, visually directed, and properly split across repositories**.

The project is no longer blocked on figuring out what the capstone is or inventing a TD/UE architecture.

It is blocked on the first real evidence chain:

```text
owner-confirmed rigged sheep
→ fresh export / UE deformation proof
→ one beautiful sheep
→ live-imported ROOT_C TD field
→ captured C-note Harmonize proof
```

That is a healthy blocker.

Do not broaden the capstone until that chain photographs well.

## 1. Repository / authority state

Current authority is explicit:

- Game / Unreal / capstone truth: `fromage3900/MelodiaMelusinaV2`
- TouchDesigner / AE performance pipeline: `fromage3900/MelodiaTouchDesigner` (private)
- Portfolio website: `fromage3900/my-site`
- `fromage3900/EnvironmentPortfolio`: historical root umbrella Git only

The local folder `C:/EnvironmentPortfolio/` may remain a workspace container.

The repositories should remain separate. No submodule or vendoring is required.

The integration rule remains:

> **UE is the authored world. TD is the concert-visual instrument. AE assembles the argument.**

## 2. Choral Sheep source truth

Verified current game-side data says:

- Choral Sheep is non-combat;
- authored interactions are Graze / Harmonize / Guide;
- one skeletal mesh is intended to support 12 pitch-class material/data variants;
- native actor is map-agnostic;
- companion/save/world authority is not owned by TD;
- Groom is optional for the base proof;
- the source rig is owner-confirmed fully rigged;
- fresh ARP/FBX → UE deformation/import proof is still pending.

Current evidence classification:

`OWNER-CONFIRMED RIG → EXPORT VERIFY`

Do not reopen the old zero-vertex-group / re-rigging lane unless the current source actually fails.

## 3. Capstone design lock

The first technical-art experiment is locked:

**Chladni Fleece**

The sequence is:

```text
QUIET
→ ROOT_C
→ INTERVAL_CE
→ RESOLUTION_CEG
→ WORLD_HIT
→ AFTERIMAGE
```

The core visual rule is:

> **hidden pearlescent embroidery revealed by song**

Harmony must become more **organized / coherent**, not merely brighter.

The first proof is still only one sheep + C.

E/G and the world response remain downstream.

## 4. Visual-reference package now committed

The visual-board set is now stored on remote Git under:

`Docs/References/VisualBoards/2026-09-08/`

### Choral Sheep

- `ChoralSheep/choral_sheep_creature_fleece.webp`
- `ChoralSheep/choral_sheep_chladni_fleece.webp`

### Mara Ellettra Vell / Electra + Ebenezer

- `MaraEllettraVell/mara_character_field_luthier.webp`
- `MaraEllettraVell/mara_instrument_variants.webp`
- `MaraEllettraVell/electra_cymatic_instruments.webp`
- `MaraEllettraVell/electra_ebenezer_relationship.webp`

### Melusina

- `Melusina/melusina_field_song_reference.webp`
- `Melusina/melusina_cymatic_instruments.webp`
- `Melusina/melusina_performance_outfit_song_states.webp`

These are **canonical committed reference images**, not runtime/final-render evidence.

The repository copies are intentionally Git-friendly optimized WebP previews. Higher-resolution generation-session outputs existed upstream.

Melusina's final portfolio authority remains the UE5.8 B2 beauty / portrait / breakdown suite once captured.

## 5. Existing runtime spine was preserved

The capstone docs correctly extend existing systems instead of inventing replacements.

Verified current source provides:

- `UMelodiaRhythmReactivitySubsystem`;
- `UMelodiaReactiveMeshRegistrar`;
- `UMelodiaAudioReactivePresentationSubsystem`;
- read-only `UMelodiaCymaticsSubsystem`;
- sole-writer `UMelodiaCymaticsWriterSubsystem`;
- `MPC_Melodia_Palette`;
- `MPC_Cymatics_Driver`;
- canonical UE↔TD semantic OSC lane on UDP **9000**.

No second global beat clock / generic music-reactivity subsystem / competing OSC bridge was added by the capstone work.

That is the correct architecture.

## 6. TouchDesigner lane — actual landed state

The private `fromage3900/MelodiaTouchDesigner` repo now contains substantially more than planning.

### Landed research / show contract

The six requested live-performance documents are present TD-side:

- `docs/MELODIA_LIVE_VISUAL_IDENTITY_CONTRACT_2026-09-08.md`
- `docs/ACTUAL_LIVE_SHOW_PIPELINES_RESEARCH_2026-09-08.md`
- `docs/MELODIA_SHOW_SYSTEM_ARCHITECTURE_2026-09-08.md`
- `docs/PIPELINE_RECIPES_CHORAL_SHEEP_2026-09-08.md`
- `docs/AGENT_BUILD_CONTRACT.md`
- `docs/CHORAL_SHEEP_CAPSTONE_TD_IMPLEMENTATION_PLAN_2026-09-08.md`

### ROOT_C source exists

Current source:

`td/grandmaster_melodia/project/project1/performance/scenes/chladni_fleece.tdn`

Shader:

`td/grandmaster_melodia/project/project1/performance/scenes/chladni_fleece/chladni_field.frag`

The source currently includes:

- deterministic C-root fixture;
- canonical `/project1/osc/in_battle` beat-phase / beat-pulse consumer;
- low-order Chladni field;
- pearl / lilac identity colors;
- `OUT_MAIN`;
- `OUT_ALPHA`;
- `OUT_FIELD`;
- `OUT_DEBUG`;
- static contract tests.

This is a real implementation advance.

But the source explicitly says:

**SOURCE-BUILT / NOT LIVE-IMPORTED**

That distinction is correct and must remain.

### TD stop gate

Next TD action is not another framework.

It is:

1. import `chladni_fleece` into the canonical live `.toe`;
2. verify operator paths and GLSL cook;
3. wire/check semantic inputs;
4. capture QUIET / C_ROOT / C_ROOT_HIT / debug evidence;
5. record TD + game SHAs, FPS/resolution, errors/warnings, LIVE vs FIXTURE;
6. stop before E/G until ROOT_C looks good.

## 7. After Effects lane

The TD repo now contains AE scaffolding, bridge/tooling, and lookdev assembly infrastructure.

That is useful supporting infrastructure.

It is **not yet the capstone-specific rebuildable AE master**.

The capstone-specific assembly spec, shot/pass manifest, and final 60–90 second edit remain outstanding.

## 8. Gemini deliverables — reconciled status

The original game-repo handoff requested six explicit outputs:

1. `CHORAL_SHEEP_TD_NETWORK_SPEC_2026-09-08.md`
2. `choral_sheep_capstone_replay.v1.json`
3. `TOUCHDESIGNER_CHORAL_SHEEP_CAPSTONE_BUILD_HANDOFF_2026-09-08.md`
4. `CHORAL_SHEEP_AE_ASSEMBLY_SPEC_2026-09-08.md`
5. `CHORAL_SHEEP_CAPSTONE_SHOT_PASS_MANIFEST_2026-09-08.md`
6. `CHORAL_SHEEP_CAPSTONE_README.md`

At this review point, those exact six files are still absent from `MelodiaMelusinaV2/main`.

However, TD-side work has now partially overtaken the original document-first sequence:

- ROOT_C TDN/GLSL implementation: **LANDED SOURCE**
- TD implementation plan: **LANDED**
- live-show visual / architecture contracts: **LANDED**
- deterministic replay schema: **STILL MISSING**
- capstone-specific AE assembly spec: **STILL MISSING**
- capstone shot/pass manifest: **STILL MISSING**
- short cross-repo capstone README: **STILL MISSING**

Do not discard the implementation just because the old checklist expected documentation first.

Close the missing contracts around the work that actually exists.

## 9. Review fixes performed

During this review, several pieces of drift were found and corrected.

### Game repo

Fixed:
- owner-approved sheep-board doc still claiming the images were not committed;
- reference manifest not linking the actual committed images;
- visual reference index not registering the new Mara/Electra/Melusina board set;
- capstone front door not surfacing the new visual-board folder;
- Gemini read-order duplication / stale rig wording;
- cross-repo contract not yet recording the now-visible private TD remote;
- repository authority map not yet recording the private TD remote;
- deliverable ledger not reflecting the landed ROOT_C source / TD outputs / AE scaffold;
- old July TD plans still presenting themselves as active; PR #130 was reviewed and squash-merged as superseded history.

### TD repo

Found and fixed:
- active README still naming UE show-control port `:8000`;
- UE realtime guide and runbook still naming `:8000`;
- `build_audio.py` could recreate an OSC output on `:8000`;
- `phase_a_scaffold.py` could recreate the old `:8000` route;
- top-level TDN / project legend comments still advertised `:8000`;
- TD agent contract used a broken cross-repo relative reference;
- canonical-contract path casing still said `Docs/` instead of the actual `docs/`;
- most importantly, `organize_project.py` still listed **`director` as an obsolete operator to destroy**, despite the new redirect saying the director should be preserved.

The organizer now preserves `director`.

Canonical UE↔TD semantics remain on UDP **9000**.

## 10. Convergence Mode review

The capstone batch also included a bounded repair to:

`deploy/surreal_arch/convergence_mode.py`

The fix correctly moves normal decoded PCM WAV data through the shared envelope/BPM analysis path instead of allowing successful WAV decodes to miss analysis.

Fallback/synthetic data is explicitly labeled lookdev behavior.

This is a good repair.

A fresh live smoke is still required before depending on it:

- normal PCM WAV;
- fallback/unsupported source;
- N-panel;
- playback/reset.

Convergence Mode remains support/lookdev, not capstone authority.

## 11. Evidence matrix

### Grounded / present now

- capstone thesis and scope;
- current sheep companion/data contracts;
- owner-confirmed fully rigged source;
- existing UE rhythm/cymatics/OSC architecture;
- one canonical UDP 9000 semantic lane;
- Choral Sheep analytical boards;
- owner-approved visual concept boards committed remotely;
- TD six-file live-performance contract;
- source-built ROOT_C TDN + GLSL;
- source outputs and static contract tests;
- AE/general lookdev scaffolding;
- repository authority / archaeology closeout.

### Not proven yet

- fresh ARP export;
- fresh UE skeletal import/deformation;
- approved M0 sheep beauty;
- UE Harmonize capture;
- pitch-C fleece on the actual sheep;
- ROOT_C live-imported/cooking inside the canonical `.toe`;
- fresh post-redirect TD test run;
- live vs fixture ROOT_C evidence captures;
- deterministic replay schema;
- C/E/G identity proof;
- resolved shared harmonic field;
- world-response proof;
- final TD transparent captures;
- capstone-specific AE master;
- 60–90 second final;
- exact Humber rubric mapping.

## 12. CI / validation truth

### Game repo

The latest recorded Echo Static Gates run in this review is:

`e48bcb0358` → **SUCCESS**

Later changes in this batch are predominantly documentation/reference-image paths and therefore did not trigger the workflow's current path filters.

Do **not** describe the newest game head as CI-validated solely from that earlier run.

### TD repo

A static test harness is present, including `test_chladni_fleece.py`.

There is no current GitHub Actions workflow in the TD repo, and no fresh captured post-redirect full-suite run was found during this review.

Do not claim a current “100% pass”.

## 13. Current ledger interpretation

- **CS-01:** OWNER-CONFIRMED / EXPORT VERIFY
- **CS-06:** LOCKED / TODO — actual C fleece proof still needed
- **CS-08:** SOURCE-BUILT / LIVE VERIFY
- **CS-15:** SOURCE OUTPUTS / CAPTURE TODO
- **CS-16:** SCAFFOLD PRESENT / CAPSTONE TODO
- **CS-19:** ACTIVE

Everything else should remain evidence-driven.

## 14. Next five actions

### 1 — owner / sheep export

Open the current fully rigged source and perform the fresh ARP/FBX → UE check.

If it works, stop touching rig architecture.

### 2 — M0 beauty

Get one clean, lovable sheep image.

Silhouette / face / ear / bell / fleece readability first.

### 3 — TD ROOT_C live gate

Import the source-built Chladni scene into the real grandmaster and capture the C-root proof.

Do not add E/G first.

### 4 — connect the contract around reality

Land the deterministic replay schema and short capstone TD/AE handoff around the actual ROOT_C scene that now exists.

### 5 — only after C works

Proceed:

```text
C
→ C/E
→ C/E/G
→ one world response
→ UE + TD passes
→ AE final
```

## Final production call

The capstone is no longer suffering from an ideas problem.

It has:
- a subject;
- a thesis;
- a visual identity;
- a runtime spine;
- a TD show language;
- reference boards;
- a source-built first scene;
- an editorial destination.

The next valuable commit is **evidence**, not another architecture document.

> **Make one sheep sing C beautifully. Then build outward.**
