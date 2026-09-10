# Lookdev → Breakdown → Website/Three.js Sync — Implementation Plan

> **For Hermes:** this is a plan, not an execution. Nothing below has been run.

**Goal:** Produce the final approved visual proof set (Melusina B2 hero + portrait, material/topology/
silhouette proof, Sakura Dream, Kaleido Nave, Fallen Moon) plus matched shader-breakdown visuals, and
promote both into `fromage3900/my-site` — into the **existing** shader-breakdown page and the
**existing** Three.js viewport — without creating a new public route or a parallel capture framework.

**Architecture:** two repos, one direction of flow. `MelodiaMelusinaV2` renders and is the technical
authority; `my-site` ingests, encodes, manifests, and publishes. Bridge artifacts are files on disk
(`Products/Portfolio/<date>/`) carried by the existing `my-site/tools/*.ps1` pipeline. Nothing new is
invented — every step below names a tool that already exists.

**Tech stack:** UE 5.8 Movie Render Queue + `Content/Python/run_portfolio_capture.py`; PowerShell ingest
+ ffmpeg loop encoders; JSON manifests (`render-passports.json`, `site-plates.json`); three.js r128
(GLTFLoader + OrbitControls) on GitHub Pages behind the Wix shell at `fromageart.xyz`.

---

## 0. Freeze constraints (read before anything else)

`my-site/content/showcase-freeze.json` is `status: soft_freeze`. This plan is legal **only** because
every path it touches is already on the allowlist.

**Allowed exact paths this plan uses**
- `wix/shader-breakdowns.html`
- `wix/realtime-3d-viewer.html`
- `wix/melodia-3d-viewport.js`
- `wix/melodia-atelier-lab.html` + `wix/melodia-atelier-lab.js`
- `content/render-passports.json`
- `content/site-plates.json`
- `index.html` (only if a plate slot changes)

**Allowed prefixes this plan writes into**
- `generated/assets/character/`
- `generated/assets/unreal/`
- `generated/optimized/curated-art/`
- `tools/fromage-webgl-kit/`

**Blocked — do not do these even if they would look better**
- create a new public page (no `wix/<new-thing>.html`);
- redesign navigation or rewrite recruiter copy;
- add a second render/capture framework;
- replace the three.js viewer with a different renderer;
- promote a WebGL prototype into canonical recruiter navigation.

If a task seems to need a new page, it is a freeze-exception request, not a task.

---

## 1. Current state (verified 2026-09-10, not assumed)

**Live:**
- `https://fromage3900.github.io/my-site/` — Pages `status: built`, https enforced, workflow build
- Wix shell / custom domain: `https://www.fromageart.xyz/`
- Root `index.html` is a breathe gateway with a single escape: "selected art → enter"

**Already strong — do not rebuild:**
- `wix/shader-breakdowns.html` — UE5 Substrate Toon, 22 material instances, master
  `M_Master_Toon_Universal` (916 expressions, 11 static switches), Hero Surface / Cosmic SDF /
  SDF Ornament families, live webm loops + material-isolate previews.
- `wix/realtime-3d-viewer.html` + `wix/melodia-3d-viewport.js` — three.js r128, GLTF/OBJ/FBX loaders,
  OrbitControls, ACES filmic tone mapping, sRGB output, pedestal + shadow plane + ring. Loads
  `models/grand_piano.glb`, `models/pillar_stone.glb`, `models/fountain_round.glb`.
  Carries an explicit honesty banner: "an interactive presentation study, not a 1:1 Unreal renderer."

**Asset inventory on the site:**
- `generated/assets/character/` — 46 files
- `generated/assets/unreal/` — 32 files
- `generated/assets/material-loops/` — 25 files

**Evidence debt — the real reason for this session:**
- `content/render-passports.json` = **30 entries: 16 accepted, 9 reject, 5 supporting**
- Nine public plates are explicitly self-reviewed as *reject*. The freeze permits evidence
  corrections; it does not permit leaving rejected plates standing as proof.

**Pipelines that already exist (use these, do not write new ones):**
| Tool | Role |
|---|---|
| `MelodiaMelusinaV2/deploy/portfolio_render.ps1` | headless capture driver → `Products/Portfolio/<date>/` |
| `MelodiaMelusinaV2/deploy/render_queue_submit.ps1` | queue one job onto `origin/render-queue` (Blender \| UnrealMRQ) |
| `my-site/tools/build_unreal_capture_brief.ps1` | emits the shot brief from current site slots |
| `my-site/tools/ingest_unreal_portfolio.ps1` | brings UE captures into `generated/assets/` |
| `my-site/tools/scan_portfolio_renders.ps1` | audits what landed |
| `my-site/tools/encode_material_loops.ps1` | webm loops from material captures |
| `my-site/tools/encode_material_loops_from_stills.ps1` | webm loops when only stills exist |
| `my-site/tools/auto_publish_loops.ps1` | publishes loops into the manifest |
| `my-site/tools/build_curated_art_derivatives.py` | curated-art derivatives |
| `my-site/tools/validate_assets.py` / `validate_portfolio.ps1` | asset + page validation |
| `my-site/tools/verify_sendoff_freeze.py` | freeze compliance gate |
| `my-site/tools/verify_showcase_polish.py` | polish gate |

---

## 2. Approach — four workstreams, in the freeze's closeout order

The freeze doc fixes the order. Do not reorder it; screenshot #4 before #3 produces a hero page
leading with unpromoted art.

```
A. Capture      Melusina B2 hero + portrait  →  material/topology/silhouette proof
B. Breakdown    per-material isolate stills + loops  →  shader-breakdowns.html
C. Worlds       Sakura Dream → Kaleido Nave → Fallen Moon beauty  →  unreal/ + site plates
D. Sync         passports → plates → three.js models → verify:all → deploy
```

---

## 3. Step-by-step

### Task 1 — Freeze preflight (2 min, read-only)

Run from `my-site`:
```bash
python tools/verify_sendoff_freeze.py
git status --short
```
Expected: freeze verification passes; note every dirty path, because anything outside the allowlist
must be reverted before you start.

Pass condition: no dirty path outside the allowlist in §0.

### Task 2 — Generate the capture brief from the live site (5 min)

Run from `my-site`:
```powershell
./tools/build_unreal_capture_brief.ps1
```
This derives what to shoot from the *current* `site-plates.json` slots, so the shoot matches the site
instead of the site being retrofitted to the shoot.

Output: a capture brief naming each required plate. Keep it as the shot list for Task 3.

### Task 3 — Capture in UE (Melusina B2 hero + portrait first)

Run from `MelodiaMelusinaV2` with the editor CLOSED to Live Coding:
```powershell
./deploy/portfolio_render.ps1
```
- Driver: `Content/Python/run_portfolio_capture.py` via `UnrealEditor-Cmd -ExecutePythonScript`.
- Output: `Products/Portfolio/$(date +%Y-%m-%d)/`.
- Order matters: Melusina B2 hero, then portrait, then material/topology/silhouette proofs.

Pass condition: files exist on disk with a timestamp newer than the run start. **Verify on disk before
claiming a render** — a `success: true` from tooling is not an image.

### Task 4 — Ingest captures into the site (10 min)

Run from `my-site`:
```powershell
./tools/ingest_unreal_portfolio.ps1
./tools/scan_portfolio_renders.ps1
```
Landing zones (allowlisted prefixes): `generated/assets/character/`, `generated/assets/unreal/`.

Pass condition: "before" and "after" file counts on those two directories differ by exactly the number
of plates the brief asked for.

### Task 5 — Material loops for the breakdown page (15 min)

For animated families (Nebula, Starfield, EclipseHalo, AuroraVeil, water/ink studies):
```powershell
./tools/encode_material_loops.ps1
# stills-only fallback:
./tools/encode_material_loops_from_stills.ps1
./tools/auto_publish_loops.ps1
```
Output: `generated/assets/material-loops/` (currently 25 files).

Pass condition: `shader-breakdowns.html` references resolve — open the page and confirm every loop
plays and none 404.

### Task 6 — Three.js viewer sync

Export/confirm the viewer models as glTF and drop them where the viewport already looks:
`wix/models/*.glb`.

Rules:
- Keep three.js r128 and the existing loaders — do not add a renderer dependency (freeze explicit).
- Keep the "interactive study, not a 1:1 Unreal renderer" disclosure verbatim.
- Keep the sphere/pedestal framing (ARN: PBR Fabric Lookdev Sphere, Royal Velvet, 4.6k tris, ORM pass).

Pass condition: each `.glb` loads in the viewport with no console error, and orbit + auto-rotate work.

### Task 7 — Correct the evidence debt

Edit `content/render-passports.json` only. For each of the 9 `reject` entries choose one and record
which:
1. **replace** with a plate captured in Task 3–5 and re-review it at pixel level → `accepted`;
2. **downgrade** to `supporting` with an honest `does_not_prove` list;
3. **retire** the slot and repoint the consuming plate in `content/site-plates.json`.

No entry leaves this file without a status. The definitions in the file already say what each status
means — use them as written.

### Task 8 — Plate repointing

Update `content/site-plates.json` so every slot points at an accepted or explicitly-supporting plate.
The `notes` field already records prior retirements (jewelry plate killed, glam_03 removed, Sakura
horizon slots retained only as rejected placeholders). Append to that convention, do not overwrite it.

### Task 9 — Gates

Run from `my-site`:
```bash
npm run verify:all
python tools/validate_assets.py
python tools/verify_sendoff_freeze.py
python tools/verify_showcase_polish.py
```
Expected: all pass. A failing `verify_sendoff_freeze` means a path outside §0 was touched — revert that
path, do not widen the allowlist.

### Task 10 — Deploy + live browser QA

Commit to `my-site/main` (protected — PR or the documented publish path), let the Pages workflow run,
then verify on the **live** URLs, desktop and mobile:
- `https://fromage3900.github.io/my-site/wix/shader-breakdowns.html`
- `https://fromage3900.github.io/my-site/wix/realtime-3d-viewer.html`
- `https://fromage3900.github.io/my-site/`

Pass condition: renders visible, loops playing, viewport interactive, no 404s, escape link from the
breathe gateway works.

---

## 4. Files likely to change

**Game repo (`MelodiaMelusinaV2`)** — render output only:
- `Products/Portfolio/<date>/` (build output, not source)

**Site repo (`my-site`)** — all allowlisted:
- `generated/assets/character/*`, `generated/assets/unreal/*`, `generated/assets/material-loops/*`
- `wix/models/*.glb`
- `wix/shader-breakdowns.html`, `wix/realtime-3d-viewer.html`, `wix/melodia-3d-viewport.js`
- `content/render-passports.json`, `content/site-plates.json`

**Never touched by this plan:** `index.html` (unless a plate slot changes), navigation, `wix/*` pages
not listed, `tools/verify_sendoff_freeze.py`, `.github/workflows/pages.yml`.

---

## 5. Risks, tradeoffs, open questions

**Risks**
- *Unity/Live Coding lock* blocks the headless cook. Close every `UnrealEditor` process first; the
  cook fails with `Unable to build while Live Coding is active` otherwise.
- *Render claim without proof.* A green tool exit is not an image. Every capture step ends with an
  on-disk file check.
- *Plate drift.* Changing a plate without updating `site-plates.json` leaves the page pointing at a
  retired file — a 404 that only shows on the live URL.
- *Freeze erosion.* The most likely failure is not a bad render, it is "just one new page." Everything
  here fits existing routes on purpose.

**Tradeoffs**
- Only 9 of 30 passport entries are marked reject, but 5 more are `supporting` — i.e. not sufficient
  alone for the strong claim their slot implies. Correcting all 14 is honest but lengthens the session.
  Recommended: fix all 9 rejects, triage the 5 supporting ones only where a slot actually leans on them.
- three.js r128 is old. Upgrading would be a renderer change and is freeze-blocked; accept it and keep
  the disclosure banner.

**Open questions for the owner**
1. Which of the 9 rejected plates do you want **replaced** vs **retired**? Retiring is cheaper and
   honest; replacing keeps the moodboard fuller.
2. Is `wix/models/*.glb` the intended home for new viewer assets, or should they live under
   `generated/optimized/curated-art/` and be referenced from there?
3. Melusina B2 hero — is the capture rig the two `SceneCapture2D` actors now committed in
   `LV_SeaAbove_Prototype` (commit `78ce468b`), or the Movie Render Queue path in
   `deploy/portfolio_render.ps1`?

---

## 6. Definition of done

- [ ] Melusina B2 hero + portrait captured, ingested, visible on the live site.
- [ ] Material/topology/silhouette proof captured and referenced by the breakdown page.
- [ ] Sakura Dream, Kaleido Nave, Fallen Moon beauty plates captured and slotted.
- [ ] Every shader-breakdown loop plays on the live page.
- [ ] Three.js viewport loads its models with no console error, disclosure intact.
- [ ] Zero `reject` entries remain in `render-passports.json`.
- [ ] `npm run verify:all` + both verify tools green.
- [ ] Live browser QA passes desktop and mobile on all three entry URLs.
- [ ] Freeze exception list empty — nothing outside §0 was touched.
