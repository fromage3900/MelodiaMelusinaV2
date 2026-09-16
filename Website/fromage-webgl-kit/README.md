# Fromage WebGL Kit — Treasury

**Isolated website lane.** Lives under `Website/fromage-webgl-kit/` on the game repo and `tools/fromage-webgl-kit/` on `my-site`. Not the recruiter GitHub Pages surface.

**Purpose:** turn existing Three.js/WebGL + 3D technical-art capability into small, bounded paid work that funds the Melodia `EARNED_POOL` without becoming a second full-time project.

**This README is the only current Treasury/status document.** Do not create dated lead scans, strike handoffs, finish-later lists, or submission-state documents. Durable service definitions live in [`SERVICES.md`](SERVICES.md); actual money lives in [`TREASURY_LEDGER.json`](TREASURY_LEDGER.json); prototype-specific technical truth lives beside the prototype/code it describes. Old planning is recoverable from Git history.

---

## 1. Active strike — premium eyewear / accessory 3D web pipeline

**Status:** ACTIVE / OWNER WORKING NOW  
**Source:** Upwork — “3D Blender Designer” / premium eyewear e-commerce  
**Listing:** https://www.upwork.com/freelance-jobs/apply/Blender-Designer_~022095185281992255243/

### Why this is the current best strike

The buyer-shaped problem is unusually close to the kit’s demonstrated strengths:

- premium product modelling / cleanup in Blender;
- metal, acetate, lens and small-detail material lookdev;
- web-ready GLB/GLTF delivery;
- 360° / orbit presentation;
- close-up detail framing;
- product animation / scroll-ready presentation;
- browser-safe geometry, textures and loading behavior;
- repeatable work across multiple accessories/products if the relationship continues.

The goal is not “win the biggest listing”; it is **win a bounded listing whose requested work looks like work we can already prove**.

### Existing proof that directly supports it

- robust fit-to-view across inconsistent source units and outlier geometry;
- static-preview rebuilds that remove unnecessary rigs/embedded baggage;
- measured triangle counts rather than guessed badges;
- packed ORM channel inspection and material debugging;
- missing-texture and broken-path detection;
- web-size texture reduction and asset replacement;
- GLB loading + deterministic product-motion work;
- renderer diagnostics, mobile framing and browser QA;
- a **clean-room Fabric Material Lab** using six owner-authored commercial-safe material presets, runtime-verified in a real browser with material controls, grazing-angle inspection, JSON state export and mobile-width QA.

Use these as **process/proof-stack evidence**. Do not present Melodia-specific assets as client-ready eyewear samples or generic commercial inventory.

### Scope boundary

Base offer should stay close to:

```text
client photos / supplied reference or model
→ Blender modelling / cleanup
→ premium PBR material + lighting pass
→ web optimization
→ GLB/GLTF
→ 360 / orbit + close-up presentation
→ optional simple authored product animation
→ desktop/mobile QA
```

Quote separately for:

- virtual try-on / face tracking / AR;
- ecommerce, cart, inventory or backend work;
- prescription or optical simulation;
- CAD reconstruction / manufacturing tolerances;
- large custom configurator logic;
- unlimited revisions or an entire catalogue hidden inside one sample price.

The listing’s headline fixed price is **not** permission to commit an open-ended product catalogue. Clarify per-product / batch scope before commitment.

### Speculative-work rule

Do not recreate a client product from their photos as unpaid production. A proposal sample may use an owned/original neutral eyewear-or-accessory proof, or existing process evidence, and should stop once capability is demonstrated.

---

## 2. Treasury commercial order

1. **Eyewear/accessory strike:** finish only the evidence/proposal work needed to make a truthful application or delivery decision.
2. **Product / GLB lane:** finish browser runtime proof and captures where they strengthen accessory/product proposals.
3. **Fabric / material lane:** reuse the runtime-verified clean-room material proof for premium finishes, variants and technical-art consulting.
4. **Search using the same proof stack:** product viewers, configurators, WebGL rescue, luxury/fashion accessories, agency 3D integration, bounded technical visualization.
5. Build a new prototype **only when a qualified paid lead exposes a real proof gap**.

### Proof-stack state

- `prototypes/product-motion-lab/` — real generated GLB + browser wiring; final runtime/capture verification remains the useful next evidence step.
- `prototypes/fabric-material-lab/` — **runtime-verified clean-room proof**, owner-authored material provenance resolved.
- `prototypes/procedural-industrial-loop/` — archived reusable proof; original listing is dead and creates no obligation to pursue similar work.

### Industrial loop boundary

The prototype remains useful for deterministic animation, procedural composition, capture discipline and technical presentation. Do **not** present its Structural / Flow / Thermal component-coding modes as physical simulation fields.

---

## 3. Reusable commercial primitives

- `src/core/createRuntime.js` — renderer/camera lifecycle, resize, frame loop, cleanup.
- `src/assets/createGLBLoader.js` — bounded GLB loading with progress/error handling.
- `src/game/createStateMachine.js` — tiny deterministic interaction state helper.
- `src/audio/createAudioReactiveBus.js` — opt-in Web Audio FFT bus.
- `src/animation/createDeterministicTimeline.js` — scrub-safe absolute-time animation sampling.

Keep these small. A paid problem earns an abstraction; an imagined future problem does not.

---

## 4. What we sell

See [`SERVICES.md`](SERVICES.md) for the canonical scope/rate card. Current offers are:

1. Three.js / WebGL Rescue Pass
2. Interactive 3D Product / Asset Viewer
3. Branded Browser Microgame
4. Interactive Music World / Visualizer
5. Procedural WebGL Environment Prototype
6. Interactive 3D Product Configurator / Variant System

For the current strike, **SKU 2 is the center of gravity**; SKU 6 is optional follow-on scope, not assumed base scope.

---

## 5. First revenue gate

The first milestone is not a startup or a revenue target. It is proof that the loop works.

All five must become true:

1. one real prospect/buyer accepts a bounded WebGL/3D deliverable;
2. payment is actually received;
3. platform + inference costs and owner hours are recorded;
4. at least **CAD $20 equivalent** is designated to `EARNED_POOL`;
5. the job leaves one reusable, generic, IP-safe primitive/checklist/benchmark/template.

Record the real result in [`TREASURY_LEDGER.json`](TREASURY_LEDGER.json). Do not add speculative payment rows.

### Preferred first win

Prefer a job that can be finished and handed off decisively: one product model/viewer, one GLB cleanup, one material/product presentation pass, one broken viewer, one small interaction, or another similarly bounded deliverable.

---

## 6. Lead qualification

Score 0–2 on each:

- capability match;
- proof already available;
- scope boundedness;
- client credibility;
- budget adequacy;
- reuse potential;
- low legal/IP risk;
- low integration risk.

Interpretation:

- **13–16:** APPLY / CONTACT
- **9–12:** WATCH / clarify
- **0–8:** IGNORE unless strategically exceptional

Price is not a substitute for fit. **Owner comfort is a hard gate** on high-value work.

Human approval is required before contact, proposal submission, price commitment or financial spend.

---

## 7. IP and truth boundary

Never package Melodia-specific characters, textures, music, purchased templates, third-party material graphs, or client assets as generic kit inventory.

Every commercial claim must be one of:

- directly demonstrated;
- measured;
- clearly described as a proposed workflow;
- explicitly scoped as follow-on work.

Do not upgrade a proposed capability into a completed capability because an agent wrote a convincing paragraph about it.

---

## 8. Stop conditions

Pause or decline when:

- Treasury work starts displacing Choral Sheep / academic P0;
- the buyer expects unrelated backend/full-stack ownership;
- unpaid speculative work grows beyond a tiny capability assessment;
- legal/IP ownership is unclear;
- scope cannot be bounded before acceptance;
- effective pay collapses after revisions/platform costs;
- the reusable-kit work grows faster than real demand.

**Commercial progress is:** working proof → qualified lead → human-reviewed proposal → bounded agreement → paid result → reusable capacity. Commits and planning documents are not revenue.
