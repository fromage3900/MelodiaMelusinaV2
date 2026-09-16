# Direct Listing Strike Prompts — 2026-09-10

**Purpose:** convert today's strongest verified paid Three.js/WebGL listings into bounded Kimi execution prompts.

**Rule:** build proof for the capability the buyer requests; do not recreate unpaid client deliverables, scrape client assets, or contact/apply automatically. Human reviews every proposal.

## Owner capability correction

Brennan has **used CLO 3D**. Treat CLO as a legitimate part of the garment/fabric pipeline and proposal vocabulary. Do not describe the owner as a CLO specialist unless the evidence supports that level of claim; use concrete language about actual CLO work performed and show artifacts/screenshots/source where available.

## Strike order

1. $3,000 real-time product animation / web-ready GLB assets — highest fit and strongest client history.
2. $30–$300/hr Three.js technical-artist consultant — very high fit because existing fabric/material systems plus owner CLO experience cover much of the requested pipeline.
3. $2,000–$5,000 knitwear configurator — viable after a clean generic configurator proof exists; CLO can provide a purpose-built original garment asset.
4. $10,000 procedural industrial homepage loop — high-value fourth strike; heavier proof, so do not let it block the first three.

---

# STRIKE 1 — $3,000 Web-Ready Product Animation / GLB

Listing: https://www.upwork.com/freelance-jobs/apply/Real-time-product-animation-for-the-web-game-ready-GLB-assets-for-Three-scroll-experience_~022097076063773171612/

## Kimi prompt

Read:
- `tools/fromage-webgl-kit/KIMI_PROTOTYPE_BATCH_2026-09-10.md`
- `tools/fromage-webgl-kit/prototypes/product-motion-lab/`
- `tools/fromage-webgl-kit/src/`

Execute **only the Product Motion Lab proof** for the currently live $3,000 real-time product-animation listing.

The buyer needs web-ready 3D assets for a Three.js / React Three Fiber scroll experience. Their actual production scope is two supplied handheld diagnostic products, with game-ready topology, PBR metal/rough materials, web-compressed GLBs, named scrub-safe animation clips, parented anchor locators, transparent beauty stills, and editable DCC source. We do **not** have their product geometry, so do not imitate or infer their proprietary product.

Build a clean-room generic proof that demonstrates the same production thinking using original procedural or owned geometry.

### Required proof

1. Use a neutral original handheld-device-like object with at least one animated subassembly.
2. Keep the scene presentation clinical, precise, restrained and neutral — not a fantasy/Melodia treatment.
3. Structure the object as if it were destined for glTF/GLB delivery:
   - clean parent/child hierarchy;
   - meaningful node names;
   - named locator/anchor objects;
   - compact material set;
   - no environment lighting baked into textures.
4. Implement deterministic scrub-safe phases named conceptually like:
   - `rotate_in`;
   - `use_sequence`;
   - `idle`.
   The same normalized time must always produce the same pose.
5. Ensure at least three callout anchors remain correctly parented to moving parts while scrubbing.
6. Add a concise budget panel showing:
   - triangles;
   - draw calls;
   - DPR;
   - approximate FPS;
   - texture count / approximate texture dimensions if relevant;
   - current asset byte size if a GLB exists.
7. Add one QA inspection mode such as wireframe/normals/material isolation.
8. Verify slider scrub `0 → 1 → 0` and scroll scrub both drive the same deterministic timeline.
9. Verify desktop and phone-width behavior.
10. If practical, create/export one original GLB demonstrating the hierarchy and named nodes. If Kimi cannot reliably produce the DCC/glTF file, keep the browser primitive group and document the exact Blender export structure we would use; do not fabricate a successful GLB export.

### Buyer-specific evidence note

Create `LISTING_3000_EVIDENCE.md` containing:
- what was actually executed;
- measured scene stats;
- how the demo maps to the buyer's requested 30–80k-triangle / 2K-max / compressed-web-asset mindset;
- how named clips and parented locators would map into a client-supplied Blender asset;
- which requested production requirements are **not yet proven** (e.g. KTX2/Basis or Draco/meshopt if we have not actually tested them);
- two or three existing live portfolio/demo URLs we can truthfully show if available;
- one suggested concise answer for “typical triangle + texture budget for a hero web asset.”

### Hard stop

Do not model a diagnostic product from the listing, do not create twelve requested beauty renders for an imaginary product, do not write React integration, and do not submit a proposal.

Finish when the generic proof is runtime-clean and proposal-ready.

---

# STRIKE 2 — $30–$300/hr Three.js Fabric Technical Artist Consultant

Listing: https://www.upwork.com/freelance-jobs/apply/Three-Technical-Artist-Consultant_~022092763085840401535/

## Kimi prompt

This is a **consulting-proof extraction task**, not a new shader-lab build.

First inspect the existing fabric/material systems in `fromage3900/my-site`, especially:
- `wix/realtime-3d-viewer.html`;
- `wix/melodia-3d-viewport.js`;
- `wix/melodia-atelier-lab.html` / `.js`;
- `wix/sdf-material-gallery.html`;
- any clearly owned supporting fabric PBR textures and material documentation.

The buyer wants strategic guidance on realistic fabric/garment visuals in Three.js: 3D asset preparation, PBR materials, lighting/rendering, texture maps, and an automated path from fabric swatches to production-ready normal/roughness/displacement/etc. They explicitly describe this as consulting/strategy rather than production. Brennan has used **CLO 3D**, so include CLO honestly where it strengthens the garment-creation and validation pipeline.

### Goal

Turn our **existing** fabric/material work into an honest consultant-facing evidence package. Do not rebuild the existing lab unless a missing capability materially improves the proof.

### Required work

1. Runtime-check the existing fabric viewer / material atlas locally.
2. Inventory what it already demonstrates:
   - fabric preset switching;
   - PBR map usage;
   - roughness/specular/sheen behavior;
   - lighting response;
   - texture organization;
   - inspection/turntable behavior.
3. Search the owner's available project/source assets for **actual CLO-authored work** or CLO pipeline evidence that can be safely shown. If no reusable evidence is in the repo, flag `OWNER CAPTURE NEEDED` instead of inventing it.
4. Separate assets into:
   - clearly owner-authored/reusable;
   - third-party/uncertain provenance;
   - Melodia-specific/noncommercial.
   Do not expose uncertain assets as commercial samples.
5. Identify the **smallest missing generic proof** needed for this listing. Prefer one addition, not a new application. Examples:
   - grazing-angle inspection lighting;
   - close-up textile inspection camera;
   - editable roughness/normal/sheen multipliers;
   - concise material-state readout.
6. If one such addition is justified, implement it in a clean-room commercial demo under `tools/fromage-webgl-kit/prototypes/` without modifying the deployed portfolio.
7. Write `FABRIC_CONSULTANT_EVIDENCE.md` covering:
   - current capabilities we can demonstrate;
   - a recommended CLO → DCC cleanup/retopo as needed → UV/material prep → glTF/GLB → Three.js fabric lookdev stack;
   - swatch capture → tileable base/albedo → normal → roughness → optional height/displacement → color management → validation workflow;
   - what should be measured from physical fabric versus artist-authored;
   - where Three.js approximations differ from measured BRDF/fiber rendering;
   - an automation architecture for batch-producing candidate texture resources without claiming the full pipeline already exists.
8. Produce one compact consultant-facing diagram/checklist in Markdown for evaluating third-party 3D artists/material work.
9. Finish with **3 concrete questions we would ask the client before advising their pipeline**.

### Hard stop

Do not claim measured fabric BRDFs, automated photometric swatch capture, physically exact reproduction, or a higher level of CLO specialization than the owner's real work supports. Do not rebuild the Fabric Material Lab from scratch. Do not contact the client.

---

# STRIKE 3 — $2,000–$5,000 Knitwear Three.js Configurator

Listing: https://www.upwork.com/freelance-jobs/apply/Three-Product-Configurator-Developer-Week-Fixed-Price_~022093492314330845907/

## Kimi prompt

The buyer wants a one-garment sweater configurator delivered as an embeddable component: orbit/zoom, stitch texture switching, color switching, chest embroidery/decal, and export of the final configuration as JSON. They supply the GLB. Their listing explicitly says applicants without a live configurator example will not be considered.

Our objective today is **not to clone Knitup or perform their job for free**. Build the minimum clean-room configurator proof that establishes we can execute the interaction model.

### Starting point

Reuse:
- the Fromage WebGL Kit runtime and GLB-loader primitives;
- safe generic material/fabric logic already in our repo where provenance permits;
- preferably **one original garment authored by Brennan in CLO 3D**, exported through a clean web-ready GLB pipeline; otherwise use a completely original procedural/owned generic garment asset and mark CLO capture/export as owner follow-up.

Do not use client assets or copy Knitup branding/UI.

### Required proof

Create or finish a generic `product-configurator` prototype under `tools/fromage-webgl-kit/prototypes/` with:

1. orbit + zoom;
2. one product/garment surface with at least three independently authored surface/stitch presets;
3. live base-color selection;
4. one generic chest decal/patch selector using locally generated/original marks;
5. a state model like:
   ```json
   {
     "surface": "...",
     "color": "...",
     "decal": "..."
   }
   ```
6. visible JSON export/copy or downloadable local JSON — no backend;
7. reset-to-default state;
8. mobile-width layout;
9. diagnostics for FPS/DPR/draw calls/triangles;
10. architecture notes showing where a client-supplied GLB and a host site's save/order integration would plug in.

### Evidence

Create `LISTING_KNITWEAR_CONFIGURATOR_EVIDENCE.md` containing:
- runtime-tested features;
- desktop + phone-width evidence paths;
- sample exported JSON;
- if used, CLO source/export notes and downstream web optimization steps;
- what would be required to convert the proof into an embeddable production component;
- what is intentionally absent: ecommerce/order backend, arbitrary uploads, React wrapper if not implemented, and client-specific GLB integration.

### Hard stop

Do not copy the referenced website, do not implement ecommerce/cart/order processing, do not fabricate a React/R3F implementation if the proof is vanilla Three.js, and do not submit the application.

Finish when we have a genuinely live configurator URL/local demo we can truthfully link in an application.

---

# STRIKE 4 — $10,000 Procedural Industrial Homepage Loop (after 1–3)

Listing: https://www.upwork.com/freelance-jobs/apply/artist-animate-and-build-the-the-loop-animation-the-company-homepage_~022096976272432704858/

Do this only after the first three are evidence-complete.

Use the existing `procedural-industrial-loop` brief. Focus on an original mechanical scene with deterministic procedural motion and clearly labelled illustrative STRUCTURAL / FLOW / THERMAL visualization styles. Their actual job uses supplied CAD and a supplied prototype/spec; do not reconstruct their proprietary scene. Demonstrate constrained system-driven animation, surface control, and web-delivery awareness. Create `LISTING_10000_EVIDENCE.md`, then stop.

---

# End-of-day decision gate

After each strike, rescore its listing using `SERVICES.md`.

Only prepare an application when:
- runtime evidence exists;
- proof is honestly relevant;
- no requested must-have is being falsely claimed;
- the listing still appears open/current;
- the likely economics still justify applying.

Human approval is required before any submission.