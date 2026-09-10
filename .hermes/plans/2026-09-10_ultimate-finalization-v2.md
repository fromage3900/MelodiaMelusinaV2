# Ultimate Finalization Plan v2 — Submissions · Treasury · Lookdev · Three.js

> Supersedes `2026-09-10_152407-ultimate-finalization-submissions-treasury-lookdev.md` (v1).
> v1's §4 lookdev session still stands and is referenced, not repeated. v2 folds in six
> read-only audits and **corrects two errors in my own earlier claim review** (§0.3).

**Goal:** Submit the three Upwork lanes on evidence that survives a technical reviewer, keep the nine
job applications moving under the owner's send rule, hold the Humber deadline, and finish the render
set — without breaking the soft freeze or displacing Choral Sheep P0.

---

## §0 Three corrections to record before anything else

### 0.1 The five industrial attachment files do not exist — not even in PR #176

I previously wrote that the five media files were "enumerated and preserved in the closed archive" and
called the claim merely *overstated*. That was too generous. The submission audit walked PR #176's
head branch `cursor/industrial-final-polish-9850` — **16,791 paths** — and found **zero `.mp4`,
zero `.webm`, and none of the twelve claimed `industrial_*.png` files**. PR #176's nine changed files
are three `Docs/Strategy/*.md`, two `.patch` files, two `APPLICATION_DRAFT_AFTER_QA.md`, and two
`runtime_report.json`.

What *is* preserved is `runtime_report.json` — the **measurements** (`console_errors: []`,
`canonical_seed: 1`, `draws: 81`, `tris: 16948`, `loopDelta: 0`). So:
**the numbers are real; the pictures do not exist anywhere reachable.** The manifest's
`binary_media_policy` / `preservation` claim is **UNPROVEN**, and the proposal's promised collateral
must be re-captured.

### 0.2 The $30–$300/hr rate IS sourced — I was wrong

I said the rate "doesn't match" `SERVICES.md` and implied it was invented. `SERVICES.md` does use
fixed project ranges (CAD $200–750 / $500–2,000+ / $750–3,000+ / $600–3,000+ / $1,000–5,000+), but
`DIRECT_LISTING_STRIKES_2026-09-10.md` strike 2 states **$30–$300/hr** for the fabric listing. The
figure is real; it comes from the listing, not the rate card. Still unverified: **CAD 1.36**, the
**10 % platform fee**, and the **$25 / $5 / $15 inference estimates** — none appear in either repo.

### 0.3 The industrial numbers belong to a build you are not shipping

Unchanged and confirmed. `EVIDENCE.md:65` and `INDUSTRIAL_CANONICALIZATION_RECEIPT` both order one
normal-browser re-measure before the Cursor figures are reused. The receipt is a **provenance**
document, not an **evidence** document.

---

## §1 Honest readiness — nothing is ready today

From the submission audit. Per-lane gate completion (verbatim from `APPLICATION_TRACKER_SNAPSHOT.csv`):

| Lane | Gate | Actually present | Missing |
|---|---|---|---|
| **$10k Industrial Loop** | **90 %** | source canonical on main; receipt; `runtime_report.json` numbers | the 5 attachments (nowhere); normal-browser sanity check; all 8 `shared_package_files` |
| **Fabric Consultant** | **44 %** | 6 docs + viewer source present | runtime QA unexecuted (16/16 `UNVERIFIED`); provenance unclassified; no CLO/Blender artifact; 3 `[INSERT …]` links unfilled |
| **$3k Product GLB** | **35 %** | generator, checker, loader module, lab shell | the GLB itself; `assets/` is **404**; `app.js` never imports `auriga-meter.js`; checker never once run |

**"Ready-now" list: empty.** Every lane fails at least one hard gate. Lane 1 is closest and is not
zero-work. Both application drafts carry their own header:
*"DRAFT / DO NOT SUBMIT UNTIL EVIDENCE LINKS ARE CHOSEN."*

---

## §2 Decisions taken

**1. Rejected plates — retire the weak, replace only what a slot leans on.** Confirmed. The site
already has a **rejected-plate guard active** (`verify_showcase_polish.py`: *"rejected-plate guard
active"*), so this is hygiene, not an emergency.

**2. New viewer models → `generated/optimized/curated-art/` as GLB.** `wix/models/` is **not** in the
freeze's `allowed_prefixes`; the allowed set is exactly `generated/assets/character/`,
`generated/assets/unreal/`, `generated/optimized/curated-art/`, `tools/fromage-webgl-kit/`.
Referenced from the already-allowlisted `wix/melodia-3d-viewport.js`. No exception needed.

  **New finding to pair with it:** `wix/models/` is **298.8 MiB** across 27 files and
  `wix/textures/pbr/` is **89.6 MiB**. Serving raw DCC exports — no DRACO, no meshopt, no KTX2 —
  to browsers, on a public directory. One entry, `models/UpdatedShirt.fbx`, **returns HTTP 404 on the
  live site**, so the "Melusina (Updated Shirt)" button silently renders a fallback cylinder. That's
  a verified live defect, not a style opinion.

**3. Melusina B2 hero capture = the MRQ/driver path, pointed at the dressed level.** Unchanged.
`run_portfolio_capture.py` loads one level per run via `PORTFOLIO_CAPTURE_LEVEL` (default Sakura),
then runs `render_exporter` + `scene_metadata_exporter`. The two SceneCapture2D actors are level
dressing, not a capture system. Set the env var or you render Sakura and get null metadata.

---

## §3 The three.js / WebGL polish lane — now concrete, and mostly pre-authorised

The audits turned this from a wish into a file:line list. Critically, a **standing freeze exception
already exists** that was written for exactly this work:

> `professor-interactive-polish-2026-09-08`
> scope: `robust WebGL fallback/loading`, `professor-facing copy accuracy`,
> `accessibility and reduced-motion behavior`, `metadata/social-preview correctness`,
> `remove misleading Unreal/Substrate equivalence language`

So several fixes below need **no new exception**. Only the three.js version consolidation does.

### 3a · Biggest structural finding — four three.js versions ship under one portfolio

| Where | Version | Form |
|---|---|---|
| `index.html` cutscene, `wix/melodia-3d-viewport.js` (the live viewer) | **r128 / 0.128.0** (2021) | legacy global `three.min.js` |
| `melodia/index.html`, `folio`, `music-key`, `sanctuary` | **0.185.0** | ESM + importmap |
| kit `templates/microgame`, both prototypes | **0.186.0** | ESM + importmap |

The r128 viewer uses APIs deleted since: `outputEncoding = sRGBEncoding` (→ `outputColorSpace` in
r152), the `THREE.OrbitControls` global (removed r150+), and the whole `examples/js/` directory
(deleted r148). **This is the single most visible 3D surface on the portfolio, and it is the surface
the fabric lane offers as evidence of current capability.** It cannot be fixed by bumping a number —
it needs an ESM rewrite, which is the one item here that needs its own manifest exception.

### 3b · Concrete defect list, ranked by reviewer impact

1. **`wix/models/UpdatedShirt.fbx` → HTTP 404 live.** Repoint `melodia-3d-viewport.js:115` or
   withdraw the button. *(no exception)*
2. **The kit README's claim that it sits "outside the deployed portfolio surface" is false.**
   `pages.yml` uploads `path: .` — `LEADS_2026-09-10.md`, the submission pack and every application
   draft are live HTTP 200. Reword, or the kit leaks its own commercial strategy. *(README is
   allowlisted)*
3. **Three of eight inspection modes are functionally wrong** in `melodia-3d-viewport.js`:
   `Roughness (G)` and `Occlusion (R)` render the packed ORM via `MeshBasicMaterial`; `Metallic (B)`
   renders flat grey with no texture. Also `aoMap` needs a `uv2` attribute in r128 — clone uv→uv2 in
   `onMeshReady` or drop the AO claim. *(no exception)*
4. **`createRuntime` throws unguarded on a machine without WebGL** — blank card, uncaught error —
   while the *legacy* r128 viewer in the same repo handles it correctly with a user-facing message.
   Newer code being less defensive than the code it should replace is the worst direction of travel.
5. **80–90 MB FBX downloads with zero loading indication.** Wire `onProgress` into a determinate bar.
   *(pre-authorised: "robust WebGL fallback/loading")*
6. **Zero tests, zero lint, zero CI for the kit.** Its only automated validation is a 152-line GLB
   checker gating a file that does not exist. Add `package.json` + `node --check` + a workflow step.
7. **`auriga-meter.js`, `createGLBLoader.js`, `createAudioReactiveBus.js` are imported by nothing.**
   `createAudioReactiveBus` also throws `InvalidStateError` on second `start()` (media-element source
   can only be created once per element) and never sets `crossOrigin`.
8. **`wix/melodia-atelier-lab.html:371` badge reads "WebGL 3D study · PBR reference"** over a page
   where 4 of 5 tabs run on `canvas.getContext('2d')`. The "Substrate Toon Shader Laboratory" is a 2D
   drawing of a shader. Relabel or move the badge inside the turntable tab.
9. **`wix/melodia-living-worlds.js` computes FPS every 1.2 s and discards it.** Use it for adaptive
   pixelRatio. `melodia-atmosphere.js` is 8 KB of dead code no page loads.
10. **Industrial loop's `timeSeconds` accumulates frame deltas** while its README, EVIDENCE.md and
    on-screen diagnostics all assert absolute-time determinism. Make the clock epoch-based or soften
    the claim.
11. **`melodia/folio` and `melodia/music-key` have no `prefers-reduced-motion` and no error
    boundary**; `constellation-brush.html` has no WebGL check and black-pages if three.js fails.
    *(constellation-brush and the wix pages: no exception. The two `melodia/*` pages: bundle into one.)*

**What is already genuinely good and must not be "polished" away:** `melodia-living-worlds` is the
strongest WebGL artifact on the site — zero external assets, custom GLSL, real motion toggle with
`aria-pressed`, noscript fallback, `document.hidden` skip. And the viewer's honesty banner
(*"an interactive presentation study, not a 1:1 Unreal renderer"*) is the most professional sentence
on the portfolio. Keep it verbatim.

---

## §4 The lookdev → breakdown session (v1 §4 stands, with one change)

Full detail in `2026-09-10_152038-lookdev-breakdown-website-threejs-sync.md`. One change from the
prep run:

**Task 0 is now mandatory.** `build_unreal_capture_brief.ps1` currently reads
`G:\EnvironmentPortfolio\...\portfolio_package.json` — a **2026-07-09** snapshot of the stale laptop
**mirror** (71 `G:\` references), scene `ZenForestTest`. Its six slots are July Zen-shrine material,
not Melodia. **Regenerate the intake from the live C: repo before any capture**, or the session shoots
the wrong world. Second defect in the same tool: `application/unreal-capture-brief.md` is emitted with
unexpanded PowerShell variables on every line (`$sceneName`, `$(System.Collections.OrderedDictionary.id)`).
The JSON half is correct.

The six real slots, once the intake is fixed, target `wix/shader-breakdowns.html` — which the surface
audit confirms is **a static image grid with zero WebGL**, despite being a canonical route. That's
fine, but know it: the breakdown page is a *gallery*, not an interactive.

---

## §5 Blockers that outrank the plan

1. **Disk** — C: 60 GB free against your own ≥120 GB target. Pagefile cap (~+24 GB, needs reboot) and
   the Twinmotion/DNA/RealityScan uninstalls (~+13 GB). **`Saved/Audit` stays off-limits.**
2. **Sep 14 add-by** — ANMN 302 + 306 unregistered, four days out, owner-send only.
3. **Zero applications sent** — nine composed, five drafted.
4. **Not new, but now quantified:** `wix/models/` + `wix/textures/pbr/` = **388 MB served publicly**,
   with `T_Melusina_Shirt_N.png` alone at **21.7 MB** (4096²). ~200 MB of VRAM once uploaded with mips.

---

## §6 Sequencing

```
Day 0  Regenerate the capture intake off C: (Task 0) · disk decision · send the Humber message
Day 1  Industrial: normal-browser sanity check on main + re-measure draws/tris/loopDelta
Day 2  Re-capture the 5 attachments from main · fabric: run viewer + score all 16 QA rows
Day 3  Product: Blender bake → checker → wire auriga-meter.js into app.js → browser scrub verify
Day 4  Three.js polish pass — items 1,3,7,8,9,11 (no exception needed) → verify:all → deploy
Week 2 Choral Sheep P0 beauty + musical-response capture (the actual priority)
By Oct 9  ANMN 301 Animatic to spec
```

**The one-line rule from the kit's own README, worth obeying literally:**
*"If an agent discovers itself writing more planning docs than runtime evidence, stop."*

---

## §7 Open decisions

1. **Where does the treasury ledger live?** `FIRST_20.md` names seven fields; **no file, path, or tool
   exists**. Zero rows, zero payments, no `EARNED_POOL` balance anywhere in either repo.
2. **Which price list is canonical — CAD or USD?** `SERVICES.md` (5 SKUs, CAD fixed ranges) and
   `PAID_PROBLEM_RADAR` (6 offerings, USD tiers) quote different numbers for the same rescue work.
3. **Funnel rule conflict:** `FIRST_20.md` says "keep at most the top 3"; `LEADS_2026-09-10.md` marks
   **7 APPLY**.
4. **The fabric provenance contradiction is a real exposure, not a paperwork issue.**
   `MATERIAL_PROVENANCE_MANIFEST.json` is honest — 6 presets `UNKNOWN` with `source_or_license: null`,
   the 7th `MELODIA_SPECIFIC`, all `commercial_reuse: false` — but the same textures are **already
   published in the public repo** at `wix/textures/pbr/`. The manifest says UNKNOWN is a "blocker for
   redistribution" while the redistribution is live. **Either audit them properly or pull them.**
5. **`wix/models/` — 298.8 MiB.** Deliberate recruiter downloads, or build leftovers? Answer decides
   whether the fix is "convert + prune" or "keep, but stop serving from the page directory."
6. **Is the r128 → 0.185 consolidation authorised?** It needs its own manifest exception; the
   professor-polish scope does not cover swapping the runtime the recruiter pages depend on.

---

## §8 Definition of done

- [ ] Three Upwork lanes submitted, each with a runtime gate **observed**, not asserted.
- [ ] Industrial attachments re-captured from current main and attached.
- [ ] Nine applications sent under per-item owner instruction; hold list respected.
- [ ] ANMN 302 + 306 registered before Sep 14. C: ≥ 120 GB free.
- [ ] Melusina B2 hero + portrait captured, ingested, live.
- [ ] Zero `reject` entries in `render-passports.json`.
- [ ] `verify:all` + `verify_sendoff_freeze.py` + `verify_showcase_polish.py` green.
- [ ] Choral Sheep P0 beauty + musical-response proof captured.
- [ ] ANMN 301 Animatic delivered to spec before Oct 9.
- [ ] Freeze exceptions used: only those pre-existing, plus (if approved) the three.js consolidation.

---

## §9 Annexes — six audit reports

Full text: `C:\Users\froma\AppData\Local\hermes\cache\delegation\subagent-summary-2..4-20260910_*.txt`
plus the per-task live transcripts under `...\delegation\live\deleg_bb5ac61f\`.

| # | Audit | Headline |
|---|---|---|
| 1 | Treasury model | Two competing SKU catalogues; treasury ledger is a convention with **no artifact**; first-$20 gate **0/5 complete**; 18 open decisions |
| 2 | Submission package | Nothing ready-now; **0 of 8** `shared_package_files` exist; **the 5 industrial attachments don't exist even in PR #176** |
| 3 | Kit runtime | 4 three.js versions; 2 of 5 `src/` primitives never executed; kit README's "outside the deployed surface" claim is **false** |
| 4 | Fabric / CLO | **No CLO artifact anywhere** — only Marvelous Designer was ever audited; provenance manifest honest but contradicted by already-published textures |
| 5 | Public WebGL surfaces | Live 404 on `UpdatedShirt.fbx`; 3 wrong inspection modes; `shader-breakdowns.html` has zero WebGL; strong exception pre-authorises fallback/a11y work |
| 6 | Prototypes + Auriga | One complete prototype, one weaker shell, one toy, one empty placeholder, one unbuilt lane; the checker has **never produced a real `CHECK_OK`** |

Where any annex contradicts §1–§6, the annex wins — it read the source; this plan synthesises it.
