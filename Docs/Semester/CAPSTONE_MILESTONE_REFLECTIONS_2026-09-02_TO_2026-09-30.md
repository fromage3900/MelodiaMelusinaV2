# Capstone Milestone and Reflection Package

**Review window:** 2026-09-02 through 2026-09-30 (Toronto dates)  
**Project:** Melodia Melusina — Capstone 01, Choral Sheep: Harmonic Ecology  
**Prepared:** 2026-09-30  
**Purpose:** Owner-requested, repository-grounded material for later Humber capstone submissions. This is a retrospective snapshot, not the live task queue.

## Executive summary

Across this window, the capstone moved from a defined creative and technical brief to a canonical Choral Sheep runtime, Harmonize behavior, and a C-root fleece treatment with REST/HIT visual evidence. The surrounding music and presentation pipeline also advanced: the game and TouchDesigner gained a proven phrase-signal path, while the show tooling gained stage control, Spout output, and stronger capture checks.

The full planned capstone arc is still unfinished. The repository does not show a completed C–E–G shared field, a Choral Sheep-caused environmental response, a deterministic capstone replay, or the planned 60–90 second final film. The strongest Sheep evidence by Sep 30 is scoped UE behavior plus REST/HIT fleece stills; the separate TouchDesigner ROOT_C source remains distinct from a live-imported and captured capstone pass. Final visual approval and Humber rubric mapping are also open.

**Defensible summary:** The project established and tested a single-note Choral Sheep Harmonize/fleece response using existing Melodia systems, while building the environment and show pipeline needed for later harmony and world-response stages. The evidence supports a prototype milestone, not completion of the full Harmonic Ecology film.

## How to read this retrospective

The review follows the four school-start weeks: Sep 2–8, Sep 9–15, Sep 16–22, and Sep 23–30 (last bucket ends at the review cutoff). It draws primarily from MelodiaMelusinaV2 mainline, with TouchDesigner and my-site commits as supporting evidence. The links below are representative milestones, not an exhaustive itemization of the unusually dense commit history.

The repo’s evidence ladder is SOURCE BUILT → LIVE PROVEN → RESTART PROVEN → PACKAGED PROVEN. A committed tool, asset, document, or test does not by itself prove a finished shot. The project’s own progress rule is playable minutes and captured proof, not commit volume. Current status remains governed by [CURRENT_STATE.md](../../CURRENT_STATE.md); the academic template still lists the official brief, rubric, weight, and due date as pending in [FALL_2026_ACADEMIC_MATRIX.md](FALL_2026_ACADEMIC_MATRIX.md).

## Planned mission status at the cutoff

| Mission gate | Plan | Evidence by Sep 30 | Assessment |
|---|---|---|---|
| M0 — Base creature | Stable Sheep identity, usable rig, presentation-ready base | Canonical UE companion, body/animation work, and live interaction proof are present. The current record does not tie a fresh ARP export/deformation receipt and final approved beauty together. | Runtime base substantially integrated; keep export provenance and visual approval as separate checks. |
| M1 — One note | Harmonize, pitch C, readable response, return to rest | Approved Nikki-derived Sheep material path and C-root treatment are present; current state records PIE Harmonize behavior and REST/HIT stills. ROOT_C TouchDesigner source is marked source-built; live import/cook/captured pass evidence is a distinct gate. | Partially proven prototype; not yet a fully packaged UE/TD shot. |
| M2 — One chord | Readable C/E/G identities, increasing coherence, clear chord resolution | C was the first locked note. No current evidence closes the shared C/E/G field or final chord state. | Open; downstream of a strong C proof. |
| M3 — World answer | Clear, non-authoritative environment response caused by the chord | Morning, Sea Above, resonance ecology, and Universe Foundry work advanced as supporting environment systems. No captured Sheep-to-world response is shown; the UE world-field receiver/alignment canary was still open. | Open. Environment progress is real, but it is not the capstone’s causal world-response proof. |
| M4 — Showcase package | Beauty/utility passes, deterministic TD replay, rebuildable AE master, 60–90 second edit, claims matched to evidence | TD/AE scaffolding and an 8-second still-based edit exist; the capstone replay, shot/pass package, AE master, and final film remain outstanding. | Open. |
| Academic mapping | Match work to official Humber outcomes and submission rules | The academic matrix still says the official brief/rubric is pending. | Await the official brief before claiming rubric compliance. |

The Oracle / Thirteenth Note remains explicitly gated end-of-semester stretch work. Not activating it in this window is not a missed core-capstone goal.

## Week 1 — Sep 2–8: define the capstone and lock the first experiment

**Plan and work.** The first capstone was formalized as Choral Sheep — Harmonic Ecology, with the presentation spine Creature → Motif → Harmony → World. Chladni Fleece was locked as the first technical-art experiment: start with one Sheep and one C-root response, then expand only after the C proof reads. The Nikki-derived character material became the final Sheep lookdev authority. By the Sep 8 review, TouchDesigner ROOT_C TDN/GLSL source, a deterministic fixture, output contract, and static tests were present; the game repo also landed the C-root content batch and safer Harmonize presentation entry.

**Goals met**
- Turned a broad music-reactive-creature idea into a bounded first milestone and later gate sequence.
- Established owner-approved Sheep visual references and the material/authority boundary.
- Reused existing UE music/reactivity and OSC architecture rather than proposing a second global bridge.
- Created source-level C-root material and TD work for testing.

**Goals not met by week close**
- Fresh export/deformation verification and approved Sheep beauty were still required.
- The canonical TD scene had not passed live import/cook and captured QUIET/C_ROOT/C_ROOT_HIT states.
- C/E/G, environment propagation, and the final showcase were not yet finished evidence.
- Humber rubric mapping remained pending.

**Main bottleneck.** The distinction between source-built and live-proven mattered immediately: a TDN, shader, and fixture existed, but live .toe integration and readable proof capture remained gates.

**Reflection draft.** “I narrowed the capstone to a testable question: can the Sheep’s C-note Harmonize state reveal a musically organized pattern inside its approved fleece material? Reusing the project’s signal and material owners kept the experiment focused. I learned that a technically complete source package is only the beginning; the real milestone is a readable result inside the live project.”

**Representative evidence**
- [Capstone first-experiment lock](https://github.com/fromage3900/MelodiaMelusinaV2/commit/14ddc0dd)
- [Choral Sheep Day 1 gates](https://github.com/fromage3900/MelodiaMelusinaV2/commit/45282170)
- [C-root Sheep content batch](https://github.com/fromage3900/MelodiaMelusinaV2/commit/f6076362)
- [TD ROOT_C source and evidence](https://github.com/fromage3900/MelodiaTouchDesigner/commit/578a72dc)
- [TD/UE material and telemetry preparation](https://github.com/fromage3900/MelodiaTouchDesigner/commit/f62d34c9)

## Week 2 — Sep 9–15: put the Sheep into the runtime

**Plan and work.** Source work moved into the canonical Unreal companion lane. Commits added the Choral Sheep body, locomotion animation Blueprint, retarget chain, companion role, baked animation takes, and velocity/speed presentation. The week also advanced supporting environment work: resonance-ecology enrichment for Sea Above and saved Morning/Sheep-dell water, flora, and PCG dressing. The capstone creature was becoming part of an authored world rather than a standalone shader test.

**Goals met**
- Integrated the canonical Sheep as a data-driven companion and extended existing interaction/animation contracts.
- Landed the retargeted animation foundation and Sheep-specific material/VFX revisions.
- Advanced environment presentation and reusable PCG support around Morning and Sea Above.

**Goals not met by week close**
- The record does not show a final owner-approved Sheep portrait.
- The single-note C result had not become a complete, judged capstone shot.
- No C/E/G harmony, shared-field resolution, or Sheep-triggered world payoff was evidenced.
- The official rubric and final-film package remained open.

**Main bottleneck.** Integration moved faster than presentation evidence. A mesh, animation Blueprint, and companion behavior can prove runtime architecture, but do not automatically prove a beautiful and legible capstone sequence.

**Reflection draft.** “I brought the Sheep into Melodia’s actual companion and animation path instead of building a parallel prototype. That made the work more reusable, but raised the standard for evidence: I needed to show the Sheep behaving and reading clearly in the real environment, not just report that assets were wired.”

**Representative evidence**
- [Canonical Sheep body, locomotion, retarget, and companion role](https://github.com/fromage3900/MelodiaMelusinaV2/commit/d10edbf0)
- [Sheep animation takes baked to the export skeleton](https://github.com/fromage3900/MelodiaMelusinaV2/commit/731c6c3a)
- [Sheep follow/ABP and VFX updates](https://github.com/fromage3900/MelodiaMelusinaV2/commit/a7ad21c8)
- [Sea Above resonance-ecology enrichment](https://github.com/fromage3900/MelodiaMelusinaV2/commit/6acf901b)
- [Morning Sheep-dell brook and bell-bank staging](https://github.com/fromage3900/MelodiaMelusinaV2/commit/ca543c8f)

## Week 3 — Sep 16–22: move from integration toward visible proof

**Plan and work.** The Sheep retarget set and animation/VFX updates were brought onto main. Morning and other environment work gained reload-proven placements and live PIE stills. On Sep 20, the project recorded a Sheep REST/HIT material comparison: Harmonize behavior was exercised, the C-root material response was visible, and the current state lists the companion/Harmonize seam as LIVE PROVEN. Unique Sheep fleece material and companion VFX deltas were landed while the Sheep Blueprint itself stayed parked.

**Goals met**
- Reached the strongest capstone-specific proof of the month: live companion/Harmonize behavior paired with REST/HIT fleece imagery.
- Kept the Sheep material change on the approved character-material path.
- Built more presentable environmental context and saved/reload-checked parts of Morning.
- Advanced VFX and scene support without replacing the established gameplay owner.

**Goals not met by week close**
- REST/HIT evidence still needed the owner’s visual judgment against the locked Board 06 reference.
- No C/E/G shared harmonic field or world-response shot was demonstrated.
- The TD phrase bridge still had a transport/build question; the later complete seven-field readback is recorded on Sep 24, not this week.
- The capstone short film, deterministic replay, and shot/pass package remained open.

**Main bottleneck.** The bottleneck shifted from making the system exist to proving visual quality and cause/effect. Before/after stills support the claim, but the final image and a continuous, judged transition were not closed.

**Reflection draft.** “This week changed the work from setup into an observable prototype: the companion could Harmonize, and the C-root fleece had a REST/HIT comparison. The next step was no longer another Sheep framework. It was an owner-reviewed beauty shot and a short capture that made the transition unmistakable.”

**Representative evidence**
- [Sheep retarget and animation/VFX set](https://github.com/fromage3900/MelodiaMelusinaV2/commit/d260dec3)
- [Morning PIE stills and recorded result](https://github.com/fromage3900/MelodiaMelusinaV2/commit/1b7b3a81)
- [Unique Sheep fleece MI and companion VFX deltas](https://github.com/fromage3900/MelodiaMelusinaV2/commit/ceef53aa)
- [Current state’s Sep 20 REST/HIT evidence and behavior readback](../../CURRENT_STATE.md)

## Week 4 — Sep 23–30: connect the music signal and widen production support

**Plan and work.** The UE/TD phrase path reached an integration proof: PIE readback recorded all seven authored fields from the phrase bridge. A port collision was then resolved by moving the phrase bus from UDP 9000 to 9002, leaving 9000 for the existing rhythm lane and 9001 for Blender. The TD repo added two-way iPad telemetry, live Spout broadcast, transition smoothing, couture shader tuning, and an eight-gate validator calibrated against its variants. On the game side, Morning/Foundry environment work and the Sheep animation Blueprint received more changes; a separate browser prototype was promoted to main with an explicit commit note that it does not change UE runtime authority.

Portfolio work advanced as supporting presentation, not as proof of the Sheep capstone. Site PR #67 curated the Sep 26 process plates and removed weak or misleading entries. TouchDesigner issue #5 remains open for the separate H1–H8/couture capture set, which had mislabeled, near-empty, cross-family, or duplicate outputs and requires a labelled smoke-set review before another bulk export.

**Goals met**
- Proved the UE phrase-bus seam with exact field readback and corrected a real port collision.
- Advanced TD stage-control and output infrastructure for later capstone capture.
- Preserved additional Sheep animation and environment work on main.
- Applied a more critical curation pass to portfolio plates.

**Goals not met by week close**
- The full Choral Sheep C → C/E → C/E/G → world-response sequence was not captured.
- TD infrastructure progress did not establish that ROOT_C had been live-imported, cooked, and captured as a Sheep pass.
- No final Sheep beauty, deterministic capstone replay, AE master, or 60–90 second film is recorded.
- The official course brief/rubric remains missing authority for final submission formatting.

**Main bottlenecks.** Cross-system transport needed explicit port ownership; live-editor and rendering constraints slowed verification; capture validity needed stronger source-to-output labeling and visual QA. Work also spread across character lookdev, action-combat/archery, world tools, the website, and Git hygiene. Those are real project advances, but they do not all move the Sheep capstone gate.

**Reflection draft.** “I proved that Melodia can move authored musical state between Unreal and TouchDesigner, but connectivity alone did not finish the capstone. The result clarified the next proof: the actual Sheep must drive a readable C-root capture, followed by C/E/G and one visible world response. I also learned to treat capture validation as part of production, because a labelled export can still be the wrong or unusable image.”

**Representative evidence**
- [PhraseBus RecvFrom and networking fix](https://github.com/fromage3900/MelodiaMelusinaV2/commit/f6c16048)
- [Runtime closeout map and recorded phrase readback](https://github.com/fromage3900/MelodiaMelusinaV2/commit/330fbfaf)
- [Bounded Universe Foundry contracts](https://github.com/fromage3900/MelodiaMelusinaV2/commit/bdb0acbf)
- [Revised Choral Sheep animation Blueprint preserved](https://github.com/fromage3900/MelodiaMelusinaV2/commit/ea092629)
- [TD control/Spout/smoothing upgrade](https://github.com/fromage3900/MelodiaTouchDesigner/commit/31924124)
- [TD eight-gate QA validator](https://github.com/fromage3900/MelodiaTouchDesigner/commit/321a1483)
- [Site PR #67 curation](https://github.com/fromage3900/my-site/pull/67) · [TD capture QA issue #5](https://github.com/fromage3900/MelodiaTouchDesigner/issues/5)
- [Isolated Resonant Wilds browser prototype](https://github.com/fromage3900/MelodiaMelusinaV2/commit/f11fb39e) — keep separate from UE runtime claims.

## Cross-cutting bottlenecks

1. **Official assignment requirements:** the course brief, rubric, weight, due date, and reuse rules remain pending, so academic compliance cannot yet be claimed.
2. **Source-to-live-to-capture gap:** ROOT_C source and the UE Sheep material exist, but the capstone needs traceable live import/cook and an unmistakable capture.
3. **Visual acceptance:** an implemented C-root pattern is not automatically a final hero image. Board 06, the Nikki material lock, readable silhouette, and owner visual approval remain the quality bar.
4. **Scope pressure:** concurrent environment, character, combat, portfolio, and tooling work generated substantial commits. The repo’s own rule says playable/presentable minutes and captured proof matter more than commit count.
5. **Capture reliability and portability:** some receipts live under Saved/Audit, while Saved content is generally gitignored. Gather actual stills, video, and logs into the approved school submission location rather than assuming a Git link contains them.
6. **Presentation assembly:** headless After Effects repeatedly failed on this machine; the existing short proof was assembled with ffmpeg from stills. A rebuildable, capstone-specific AE master and final film remain open.

## Submission-ready framing

A careful submission statement can say:

> “I integrated Choral Sheep as a non-combat companion in Melodia and extended its Harmonize presentation with a C-root Chladni fleece response on the approved character-material path. Repository records show live interaction behavior and REST/HIT still evidence. I also developed the UE/TouchDesigner phrase-signal path and the environment/show pipeline needed for later stages. The C/E/G shared field, Sheep-driven world response, final edited film, and official rubric mapping remain in progress.”

Before formal submission, attach reviewable media and confirm the assignment brief. The highest-value evidence packet is: one approved Sheep beauty; a continuous quiet → Harmonize/C-root → rest clip; live TD ROOT_C import/cook capture with signal and error readback; later C/E/G and world-response evidence; and the final rubric-mapped edit. Do not describe the 8-second still-based edit, general TD tests, portfolio render counts, or isolated Resonant Wilds prototype as the completed Choral Sheep film.

## Source references

- [Choral Sheep integrated review](CHORAL_SHEEP_CAPSTONE_REVIEW_2026-09-08.md)
- [Choral Sheep deliverable ledger](CHORAL_SHEEP_CAPSTONE_DELIVERABLE_LEDGER_2026-09-08.md)
- [Chladni Fleece experiment definition](CHORAL_SHEEP_CHLADNI_FLEECE_EXPERIMENT_2026-09-08.md)
- [Choral Sheep visual/material and authority contract](../References/ChoralSheepCapstone/AGENT_CONTEXT.md)
- [Paul Neale presentation strategy](PAUL_NEALE_CAPSTONE_PRESENTATION_STRATEGY_2026-09-09.md)
- [Fall 2026 academic matrix](FALL_2026_ACADEMIC_MATRIX.md)
