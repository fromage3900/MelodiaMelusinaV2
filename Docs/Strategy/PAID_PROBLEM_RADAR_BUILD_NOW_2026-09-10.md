# Paid Problem Radar — Build-Now Catalogue

**Status:** ACTIVE SIDECAR STRATEGY  
**Date:** 2026-09-10  
**Primary objective:** earn the first externally funded inference budget without displacing capstone P0.  
**Initial milestone:** **first $20 earned**, then $100, then test whether the system can become inference-cost-neutral.

## Operating constraint

This is **not** a new primary production track.

`CAPSTONE_NOW.md` remains authoritative for immediate owner work. The monetization lane may:

- package work that already exists;
- turn current capstone outputs into generic demonstrations;
- prepare reusable service templates, intake forms, evidence, and proposals;
- scout paid problems that overlap existing skills;
- create clean-room reusable tools when they are already justified by current production.

It must **not** steal the session from Choral Sheep P0, create another global framework, or trigger broad Git archaeology.

The core rule is:

```text
MAKE THE CAPSTONE WORK
→ IDENTIFY THE GENERIC / COMMERCIALIZABLE PIECE
→ SEPARATE PROJECT-SPECIFIC IP
→ PACKAGE THE REUSABLE PROOF
→ SELL A BOUNDED SOLUTION
→ RETURN A CAPPED SHARE TO TOKEN TREASURY
```

---

# Token treasury model

Three accounting pools:

```text
FREE_POOL
  promotional / student / startup / cloud credits

EARNED_POOL
  inference budget funded by paid work, products, bounties, or other revenue

PERSONAL_POOL
  owner's money; never spent autonomously
```

Agents may recommend spend. They do not receive uncapped financial authority.

Every opportunity should eventually record:

- source;
- client / sponsor credibility;
- gross value;
- estimated platform fees;
- estimated human hours;
- estimated inference cost;
- probability of winning;
- delivery risk;
- evidence already available;
- `APPLY / WATCH / IGNORE`;
- actual result after closure.

Useful metrics:

```text
Opportunity EV =
(net payment × estimated win probability)
- inference spend
- human-time allowance
- delivery / revision risk

Token ROIC =
revenue attributable to agent-assisted work
÷ paid inference expenditure
```

The system optimizes for **durable useful output per token**, not maximum agent activity.

---

# BUILD NOW — Tier 0

These are the offerings that can begin from existing work **without waiting for a new major R&D project**.

## 1. Three.js / WebGL Interactive 3D Rescue

**Type:** productized service first; reusable starter kit later.  
**Readiness:** VERY HIGH.  
**Why now:** the portfolio already contains a browser-side WebGL asset/material inspection study (`fromage3900/my-site`, `wix/realtime-3d-viewer.html`).

### Problem we sell against

Clients commonly have one of these pains:

- GLB / GLTF too large;
- scene loads slowly;
- mobile frame rate collapses;
- materials look wrong in browser;
- product viewer needs material switching / hotspots / cameras;
- interactive 3D prototype exists but feels unfinished;
- Three.js implementation needs a bounded rescue rather than a total rebuild.

### Smallest sellable offer

**Interactive 3D Rescue Pass**

Client supplies one existing scene or asset package. Deliver:

1. technical diagnosis;
2. prioritized fixes;
3. one implemented rescue pass;
4. before / after evidence;
5. handoff notes.

Keep scope fixed to one scene, one viewer, or one defined problem cluster.

### Existing proof to leverage

- `fromage3900/my-site/wix/realtime-3d-viewer.html`
- browser-side orbiting / asset inspection;
- material-response inspection;
- topology / shading-channel presentation;
- current portfolio's Three.js / WebGL visual language.

### Build-now work

- [ ] create a generic, non-Melodia screenshot / short capture of the viewer;
- [ ] write a 5-question client intake form;
- [ ] make a before/after performance-report template;
- [ ] define `DIAGNOSE`, `RESCUE`, and `PROTOTYPE` scopes;
- [ ] prepare one reusable proposal paragraph;
- [ ] do **not** fork the whole website merely to create a marketplace template yet.

### Pricing hypothesis — validate against each platform/client

These are test bands, not declared market truth:

- diagnosis / micro-rescue: **$100–250**;
- bounded implementation: **$300–750**;
- polished interactive prototype: **$750–2,500+** depending on scope.

Goal #1 is not maximizing price. Goal #1 is proving that one bounded paid problem can replenish inference spend.

---

## 2. UE5 Rescue Pass

**Type:** productized technical-art / implementation service.  
**Readiness:** HIGH.  
**Why now:** the game already exercises gameplay integration, materials, save/load, UI, packaging, runtime validation, and technical-art debugging.

### Problem we sell against

- Blueprint system is broken;
- packaged build behaves differently than editor;
- material / parameter wiring is confusing;
- scene or interaction needs a targeted implementation pass;
- prototype needs debugging and cleanup before presentation;
- art team needs someone who understands both Unreal presentation and technical constraints.

### Smallest sellable offer

**UE5 Rescue Pass — one problem cluster**

Deliver:

1. reproducible diagnosis;
2. smallest safe fix;
3. editor/runtime proof;
4. concise handoff;
5. optional packaged-build verification when relevant.

### Existing proof to leverage

Use only **closed / evidenced** systems. Do not advertise unresolved work as proven.

Potential proof areas include:

- rhythm/gameplay vertical-slice integration;
- material and MPC-driven art behavior;
- UI / state-machine work;
- save / restart validation once current evidence is complete;
- art-facing UE5.8 technical workflow.

### Build-now work

- [ ] make a one-page `UE5 Rescue Pass` service card;
- [ ] define exactly what counts as one problem cluster;
- [ ] create a reproducibility / evidence checklist;
- [ ] assemble 2–3 screenshots or captures from already-proven systems;
- [ ] write an intake checklist: UE version, source control, reproduction steps, expected result, packaged-build requirement;
- [ ] never promise fixes to unknown proprietary plugins before inspection.

### Pricing hypothesis

- micro-fix / diagnosis: **$100–250**;
- bounded rescue: **$250–600**;
- larger technical-art implementation: quote after diagnosis.

The agent should prefer highly bounded rescue jobs over vague "finish my whole game" contracts.

---

## 3. Realtime Concert / Audio-Reactive Visual Prototype

**Type:** custom service first.  
**Readiness:** HIGH for a demonstration; MEDIUM for standardized delivery.  
**Supporting repo:** `fromage3900/MelodiaTouchDesigner`.

### Problem we sell against

Artists / events need:

- audio-reactive visuals;
- hand / performer-reactive visuals;
- TouchDesigner show content;
- Unreal / TouchDesigner integration;
- concert loops and stage packages;
- compositing / reel-ready outputs;
- a prototype that proves an interaction before a full show build.

### Existing proof to leverage

Current TD repository documents:

- live performer camera + hand tracking;
- FFT, vocal pitch, and chord analysis;
- GPU water / caustics / ripple systems;
- OSC show control;
- Unreal/TD bridge work;
- After Effects 32-bit compositing scaffolding;
- tracking / beat keyframe export;
- automated verification harness.

Claims must follow repository status labels: e.g. do not call UE→TD Spout ingestion production-proven while it remains `VERIFY LIVE`.

### Smallest sellable offer

**One-Song Realtime Visual Prototype**

Deliver:

1. one defined track / input;
2. one coherent visual system;
3. 2–4 meaningful audio / gesture parameters;
4. recorded proof;
5. client-facing control notes.

Do not start by selling an entire touring show.

### Build-now work

- [ ] capture one clean 20–40 second demo from already-working TD systems;
- [ ] make a generic visual variant that does not require Melodia IP;
- [ ] define supported input modes: audio only / performer hand / OSC;
- [ ] write one-song prototype scope;
- [ ] prepare a delivery checklist and recording spec;
- [ ] keep copyrighted client music out of public demo exports unless licensed / permitted.

### Pricing hypothesis

- prototype / loop package: **$250–750**;
- one-song custom system: **$500–2,000+**;
- show-scale integration: quote separately after proof / discovery.

---

## 4. Clean-Room Cymatics / Chladni Material Toolkit

**Type:** digital product candidate + custom shader service.  
**Readiness:** MEDIUM-HIGH because current capstone work directly produces the proof.  
**Critical rule:** commercial version must be **clean-room and original**.

### Why now

The Choral Sheep P0 already requires a convincing pitch-C Chladni / Harmonize visual response. If that work succeeds, the generic underlying idea can become a small reusable toolkit rather than dying as a one-off project material.

### Product concept

A small UE toolkit containing some combination of:

- original Chladni / cymatic texture assets;
- material functions for frequency / phase / amplitude-like artistic controls;
- roughness / emissive / normal / displacement response examples;
- MPC-driven runtime parameter demo;
- one minimal showcase mesh / level;
- documentation and parameter presets.

### IP / provenance firewall

Do **not** commercially distribute:

- extracted game assets;
- copied shader code;
- proprietary textures;
- third-party LUTs without redistribution rights;
- any component whose license does not permit resale / redistribution.

The current capstone can use visual references and legitimately licensed dependencies as allowed, but the sellable toolkit must be independently authored and have a clean dependency manifest.

In particular, do not simply repackage a project-specific "Nikki-derived" material graph as a commercial product. Create an original generic implementation whose code, textures, naming, examples, and documentation are ours to distribute.

### Smallest sellable version

**Cymatics Material Mini-Pack v0.1**

- 6–12 original pattern textures;
- 1 clean reusable UE material function / master;
- 3 presets;
- 1 minimal demo scene;
- 1 PDF/Markdown quickstart;
- 1 short video / GIF proof.

### Build-now work

The clever move is to do almost none of this separately today.

While finishing Choral Sheep:

- [ ] keep notes on which parameters are genuinely reusable;
- [ ] record provenance for every source asset / texture / function;
- [ ] capture the successful visual response;
- [ ] mark what would need a clean-room rewrite;
- [ ] after P0 is approved, extract only the generic portion into a separate package.

This lets capstone work create the commercial R&D at near-zero additional inference cost.

---

# BUILD NEXT — Tier 1

These are promising, but should not interrupt P0 today.

## 5. Houdini Procedural Artifact / Instrument Generator

**Type:** HDA / tool product + custom procedural service.  
**Trigger:** activate when Resonance Astrolabe / instrument procedural work is genuinely underway.

Potential generic deliverable:

- radial instrument / ornament generator;
- silhouette controls;
- symmetry / spoke / ring modules;
- cymatic engraving / displacement hooks;
- export presets for Unreal;
- seeded variation.

Commercial rule: build a generic artifact generator, not a product containing Melodia narrative assets.

**Do not start a separate HDA product pass before the game needs the procedural module.**

---

## 6. 3ds Max Sim-Ready / Physical-AI Asset Lane

**Type:** service / contract watch lane.  
**Readiness:** LOW-MEDIUM today; strategically interesting.

Observed demand suggests physical-AI / robotics pipelines need clean articulated assets, hierarchy, pivots, functional parts, and consistent DCC delivery.

This may become a useful 3ds Max niche because it has a concrete production purpose rather than existing only as software-box-checking.

Build only after a real lead or test brief appears.

Possible proof exercise later:

- one appliance / fixture / furniture object;
- correct pivots and articulated parts;
- Max-native hierarchy;
- clean naming;
- simulation-ready export;
- documented validation.

---

# INTERNAL TOOL — Paid Problem Radar

The scout itself is a build-now internal tool, but it should stay tiny.

## Sources to watch

- Upwork;
- Polycount paid freelance / job boards;
- Work With Indies / adjacent game-industry boards;
- Contra or similar credible freelance marketplaces;
- selected public Reddit hiring communities where rules permit;
- GitHub-linked paid OSS / bounty services;
- direct inbound requests;
- grant / credit / startup / student programs.

Do not bypass platform rules, scrape where prohibited, or auto-submit spam proposals.

Preferred workflow:

```text
DISCOVER
→ VERIFY CLIENT / REWARD
→ MATCH TO CAPABILITY
→ ESTIMATE EV
→ RETURN TOP 3–5
→ OWNER APPROVAL
→ DRAFT CUSTOM RESPONSE
→ HUMAN / COMPLIANT SUBMISSION
→ TRACK RESULT
```

## Opportunity taxonomy

```text
UE_RESCUE
TECH_ART
ENVIRONMENT_LOOKDEV
HOUDINI_PROCEDURAL
THREEJS_INTERACTIVE
WEBGL_OPTIMIZATION
LIVE_VISUALS
3D_ASSET_PRODUCTION
PHYSICAL_AI
PAID_OSS
DIGITAL_PRODUCT
FREE_CREDIT
```

## Kill rules

Immediately deprioritize:

- rev-share-only requests;
- vague "build my whole game" work with tiny budgets;
- unpaid production-sized tests;
- clients whose requested stack is mostly outside demonstrated ability;
- bounty values that cannot be corroborated;
- work requiring major speculative R&D before payment;
- gigs that would directly jeopardize capstone deadlines;
- requests to misrepresent professional experience, authorship, or capabilities;
- jobs where acquiring the client likely costs more than the expected margin.

---

# First sellable portfolio evidence

We do **not** need a new commercial website first.

Minimum evidence stack:

1. one short `Three.js/WebGL viewer` proof;
2. one `UE5 technical-art rescue / system` proof;
3. one `audio-reactive / TouchDesigner` proof;
4. Choral Sheep cymatics proof when P0 closes;
5. a concise capability / intake page.

These can later feed `fromageart.xyz` once they are polished and factual.

---

# First-money experiment

## Target

Earn the first **$20 of EARNED_POOL** through a bounded problem we can solve with existing capability.

This is intentionally tiny. We are validating the loop, not trying to replace employment.

### Preferred order

1. **Three.js / WebGL rescue** — existing browser proof and relatively easy remote handoff;
2. **UE5 rescue** — strong skill overlap; choose bounded problems only;
3. **concert / realtime visual prototype** — strongest differentiation, but requires better demo capture;
4. **clean-room cymatics product** — compound value after Choral Sheep proof;
5. paid OSS / bounties — opportunistic only after credibility filtering.

### Success means

```text
lead found
→ opportunity scored
→ owner approves
→ tailored proposal sent
→ paid delivery completed
→ actual inference cost recorded
→ revenue assigned to EARNED_POOL
→ retrospective improves next search
```

Even a tiny paid rescue counts if it proves the loop.

---

# Next owner-session landing strip

Do not turn this into a day of setup.

When there is a spare sidecar block **after the current art task**:

1. capture the current browser 3D viewer for 15–30 seconds;
2. capture one proven UE system / material interaction;
3. capture one clean audio-reactive TD visual;
4. put those three proofs in a small prospect folder;
5. let a cheap agent turn them into service-card drafts;
6. let a stronger model inspect only the best live opportunities;
7. owner chooses whether to apply.

No new logo, company, storefront, LLC, payment automation, or giant SaaS platform is required to test the first $20.

---

# Research snapshot / revalidation rule

Research on 2026-09-10 found current demand across Three.js/WebGL, Unreal troubleshooting, Houdini/procedural work, realtime concert visuals, 3D asset production, and sim-ready / physical-AI assets. Specific listings and prices are transient.

Before using any listing as a live lead, revalidate:

- posting still open;
- date;
- client / sponsor credibility;
- budget and payment terms;
- platform fees;
- proposal count where visible;
- IP / NDA restrictions;
- whether portfolio proof honestly supports the claim.

Current market examples discussed during the research session included Upwork, Polycount, and paid GitHub bounty systems. Do not treat any cached listing, claimed bounty total, or old price as current without rechecking.

---

# Agent assignment rule

Cheap models may:

- scan and classify leads;
- summarize requirements;
- estimate rough scope;
- deduplicate opportunities;
- prepare intake / proposal drafts;
- maintain the ledger;
- compare actual vs expected economics.

Strong / expensive models are reserved for:

- the top few opportunities;
- ambiguous technical feasibility;
- high-value proposal strategy;
- contract / scope-risk review;
- difficult implementation reasoning.

Owner retains:

- final art judgment;
- final capability claims;
- application approval;
- pricing approval;
- contractual acceptance;
- financial authority;
- final delivery sign-off.

This follows the existing Agentic Studio rule: cheapest proven reliable agent does broad work; strong models handle only the hard remainder; runtime/art evidence closes the milestone.

---

# Definition of done for this strategy

This document has succeeded when it stops being planning and produces evidence:

- [ ] 3 prospect-ready proof captures;
- [ ] 3 bounded service cards;
- [ ] first scored opportunity shortlist;
- [ ] first approved proposal;
- [ ] first paid result;
- [ ] first EARNED_POOL entry;
- [ ] retrospective showing actual token cost vs revenue.

Until then, keep the system small.