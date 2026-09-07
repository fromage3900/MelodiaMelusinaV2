# P0 Melusina Render + Website Breakdown Plan — 2026-09-07

**Status:** ACTIVE / recruiter-facing P0  
**Owner:** Brennan Shepherd  
**Engine target:** Unreal Engine 5.8  
**Primary website:** `fromage3900/my-site`  
**Rule:** direct work on `main`; **do not create a new branch for this render push**.

---

## 0. Why this is P0

The website has already quarantined the failed 2026-08-13 Cam_Beauty plate because the Flip cache sits below the scalp and the frame reads bald. Recruiter-facing pages temporarily use the existing EEVEE stage beauty `melusina_beauty_eevee_20260715c_01.png`.

That fallback is acceptable only as a stopgap. The next public character hero must be a **reviewed Unreal Engine 5.8 capture with correct hair, clean silhouette, deliberate lighting, and enough technical evidence to support a professional breakdown**.

This plan supersedes ad-hoc "make another beauty render" attempts. The goal is one small, coherent, production-quality set rather than a pile of near-duplicate stills.

---

## 1. External research distilled into production rules

### Epic portfolio guidance

Epic's early-career art guidance says to show only the best, finished, polished work; minimize clicks; state your contribution and software; and include breakdown/WIP evidence, with in-engine presentation as a bonus.

**Production rule for Melusina:** the public set should be **small, polished, and explicit**. One excellent hero plus a compact proof sequence is stronger than twelve inconsistent renders.

Source:
- https://www.epicgames.com/site/earlycareers/career-paths

### Environment / game-art portfolio guidance

ArtStation's environment-art guidance emphasizes strong beauty presentation rather than flat viewport grabs, plus different angles, wireframes, texture/material proof, and process breakdowns. ArtStation interviews also repeatedly recommend self-editing: the weakest piece lowers the perceived level of the whole portfolio.

**Production rule for Melusina:** every technical frame must still look designed. Debug evidence belongs in the breakdown, not in the opening art board.

Sources:
- https://magazine.artstation.com/2017/03/game-environment-artist/
- https://magazine.artstation.com/2017/07/game-recruiters-application/
- https://magazine.artstation.com/2019/03/games-portfolio-top-10/
- https://magazine.artstation.com/2020/10/unreal-journey-environment-art/

### Infinity Nikki / Infold visual benchmark

Infold describes Infinity Nikki as stylized fantasy grounded in PBR: high-quality character self-shadowing, GI adjustments for dark areas, dedicated handling for translucent clothing, controlled jewelry highlights, standardized material inputs, and cautious post/color grading so natural lighting still carries the image. Their newer Apple feature also emphasizes material categories, fantasy exaggeration layered over physically plausible fabric behavior, and preserving garment silhouette.

**Production rule for Melusina:** do not chase "anime flatness." Preserve believable fabric response, readable self-shadow, strong jewelry/specular accents, clean translucent edges, and an authored silhouette; then layer Melodia's fantasy color and cymatic identity on top.

Sources:
- https://www.unrealengine.com/developer-interviews/behind-the-scenes-of-infinity-nikki-tracing-a-glamorous-turn-to-an-unreal-open-world/
- https://developer.apple.com/news/?id=9mgkwjnm

### Unreal Engine 5.8 render pipeline

UE 5.8 marks Movie Render Graph as Production Ready. Movie Render Queue remains valid and supports high-quality offline output, temporal subsampling, reusable presets, 16-bit HDR/linear outputs, render passes, and OCIO. The Path Tracer is excellent for ground-truth or compatible production renders, but it is a different rendering path from the real-time game renderer.

**Production rule for Melusina:** the **authoritative portfolio beauty is Deferred/Lumen/MRQ or MRG using the actual game material/PPV path**. Path Tracer is optional comparison/reference only; it must not replace the shipped stylized renderer if the result diverges from the real game.

Sources:
- https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes
- https://dev.epicgames.com/documentation/unreal-engine/movie-render-pipeline-in-unreal-engine
- https://dev.epicgames.com/documentation/unreal-engine/cinematic-render-settings-and-formats-in-unreal-engine
- https://dev.epicgames.com/documentation/unreal-engine/cinematic-render-passes-in-unreal-engine
- https://dev.epicgames.com/documentation/unreal-engine/path-tracer-in-unreal-engine
- https://dev.epicgames.com/documentation/unreal-engine/color-management-with-opencolorio-in-unreal-engine

---

## 2. Current project facts that constrain the plan

### Already proven / reusable

- `render_exporter.py` has already produced real UE hero renders end-to-end.
- MRQ presets were created and verified against the live UE 5.8 Python API:
  - `Content/EnvSandbox/MRQ/Presets/MRQ_Preset_Cinematic.uasset` — 4K / 16-bit multilayer EXR.
  - `MRQ_Preset_MI_Loop_1080.uasset` — 1080 PNG.
- `MovieRenderPipeline` is explicitly enabled.
- The unified `M_Master_Toon_Universal` now owns the character/material feature spine; masked wardrobe instances have been converged onto it.
- The existing website already has render-passport and named-plate infrastructure.
- Existing EEVEE stage lighting and renders remain useful as **backup/reference**, not as the final Unreal proof.

### Known hazards

- `run_mrq_capture.py` is **not yet live-verified**. Do not block tonight's art on automation.
- Time-of-day / sky drift has already invalidated render A/B comparisons. **Lock sky, exposure, PPV, and time before auditioning.**
- `update_material_instance()` must be called after parameter writes or readback can lie while the renderer stays stale.
- The 2026-08-13 Blender Cam_Beauty is explicitly rejected for public use.
- Hair has two distinct concepts in the project:
  - gameplay hair;
  - cine/water-hair experiments.
  Never label one as the other.

---

## 3. P0 render priority

### P0-A — Melusina UE B2 Hero Suite

This is the highest-value render work.

Deliver exactly these **six authored outputs** before expanding:

| ID | Shot | Purpose | Public? |
|---|---|---|---|
| A1 | **3/4 full-body beauty** | Main character memory / homepage / Selected Art | YES |
| A2 | **portrait / bust** | Face, hair, eyes, makeup, translucent accents | YES |
| A3 | **material macro** | Fabric + jewelry + transparency + graphic detail | YES, breakdown |
| A4 | **in-world context** | Proves she actually lives in UE, not only a studio turntable | YES |
| A5 | **back / silhouette** | Hair, garment construction, wing/accessory silhouette | breakdown |
| A6 | **wireframe / topology proof** | Technical credibility; same pose/camera family as A1 where possible | breakdown |

**Stop condition:** if A1 and A2 are exceptional and A3–A6 are merely adequate, publish A1/A2 first and keep the weaker proof frames off the art-first board.

### P0-B — World beauties after Melusina

After A1–A6:

1. `L_SakuraDream` canonical world beauty.
2. `L_KaleidoNave` canonical architecture/world beauty.
3. `L_FallenMoon` canonical world beauty.
4. True Melusina back/silhouette replacement if A5 did not clear the quality bar.

The site currently has to qualify several of those cards as "study" / "beauty pending"; one undeniable image for each has more recruiter value than another generic technical screenshot.

---

## 4. Melusina art direction

### A1 — 3/4 full-body hero

**Lens:** start 55–70 mm full-frame equivalent.  
**Camera height:** around sternum/shoulder level, not low-angle fashion distortion.  
**Pose:** contrapposto or soft S-curve; shoulders and hips should not be parallel. One hand may support a prop/accessory, but keep both hands readable.  
**Framing:** leave breathing room around hat, hair, hem, wings and hands. Do not crop accidental fingertips or decorative extremities.

**Silhouette gate:**
- hair must separate from shoulders/background;
- translucent hat/wing elements must read as intentional forms;
- skirt layers must not merge into one pink mass;
- no arm/waist tangencies;
- no chain/jewelry clipping.

### A2 — portrait / bust

**Lens:** start 85–105 mm.  
**Goal:** eyes + face + hairline + cheek markings + jewelry + one translucent accent.

Required:
- visible catchlight in both eyes unless the pose intentionally occludes one;
- no fringe/hairline failure;
- nose/chin shadows shaped, not crushed;
- specular jewelry accent below clipping;
- enough fill that facial material remains legible on mobile.

### A3 — material macro

Frame 2–4 material stories in one image:
- white bodice cloth;
- cyan→violet sleeve gradient;
- layered pink/lavender skirt;
- metal/chain/jewelry;
- translucent/emissive accessory;
- music-note graphic panel.

Do **not** make this a material-ball grid. It should be a photographic/detail crop of the actual character.

### A4 — in-world context

Put Melusina in a real authored UE space, preferably `L_MelusinaMorning` or the strongest current chapter location.

The frame must prove:
- character scale;
- authored lighting compatibility;
- environment/character color harmony;
- real-time toon + PBR interaction;
- no stage-only cheat that collapses in gameplay lighting.

### A5 — back / silhouette

This replaces the site's current wireframe/silhouette stand-in.

Prioritize:
- hair mass;
- skirt layering;
- wing/hat profile;
- accessories hanging away from the body;
- readable negative space between arms/torso and hair/shoulder.

### A6 — wireframe / topology

Keep the same camera or a directly comparable camera to A1. A wireframe is most useful when the recruiter can visually map it to the beauty.

Show:
- game mesh topology;
- garment separation;
- hair solution;
- accessory construction.

Avoid noisy viewport chrome. Render or capture a controlled wireframe overlay.

---

## 5. Lighting recipe

The target is **romantic fantasy with readable production materials**, not flat anime key/fill.

### Character key

Start with a broad soft key 35–50° off camera and slightly above eye line.

Intent:
- cheek planes and nose remain dimensional;
- bodice weave/specular reads;
- skirt layer depth survives;
- self-shadow is attractive, not eliminated.

### Fill

Use a softer cool/lavender fill at substantially lower intensity than the key. Tune by image, not by arbitrary absolute light values.

Goal:
- preserve dark-form information;
- never flatten the face;
- keep cyan/violet materials colorful rather than gray.

### Rim / hair separator

Use a narrow cool or pink rim from the opposite side.

This is **mandatory** until the hair silhouette reads at thumbnail size.

### Jewelry / translucent kicker

One restrained warm/gold kicker may be used for chain/jewelry. If translucent hat/wing pieces need help, isolate them with a carefully placed light rather than globally increasing exposure.

### Background

Two preferred modes:

1. **Editorial studio:** muted deep violet/blue gradient with gentle atmospheric bloom.
2. **In-world:** environment color that contrasts with the hair/garment silhouette without turning the shot into visual noise.

Never use a background so bright that white cloth disappears or so saturated that cyan/pink edges become unreadable.

---

## 6. Exposure, color and PPV lock

Before the first real audition:

- disable/avoid automatic exposure drift;
- record manual exposure / exposure compensation;
- lock white balance;
- lock sky actor state and time of day;
- lock PPV blendables and weights;
- lock camera transform, focal length, aperture and focus distance;
- call `update_material_instance()` after material writes;
- capture a tiny reference slate with those values in the audit log.

**No comparing two render variants if any of those changed unintentionally.**

### Color-management rule

For the website master:
- retain a 16-bit EXR master when practical;
- export a deliberate sRGB web derivative;
- avoid baking random monitor-specific grading into the only master;
- use OCIO only if the viewport and output transform are explicitly matched and tested.

---

## 7. Capture pipeline: fast audition → final

### Stage 1 — fast audition

Use the already-proven `render_exporter.py` or manual MRQ/MRG UI.

Target:
- 1920×1080 or 1600×2000 PNG;
- fixed lighting/exposure;
- fast enough to iterate on pose, lens, hair and silhouette.

Make 3–5 A1 candidates, not 30.

Delete/reject aggressively after review.

### Stage 2 — final beauty

Use the verified 4K cinematic MRQ preset manually if the automation runner is still unverified.

Recommended outputs:
- **landscape master:** 3840×2160;
- **portrait master:** 3200×4000 or 3840×4800;
- **16-bit EXR master** + high-quality PNG/JPEG/WebP derivatives for the site.

For stills:
- motion blur off unless the shot genuinely needs movement;
- enough temporal sampling to clean hair/transparency edges;
- start around 16–32 temporal samples and only increase if the image visibly benefits;
- warm up enough frames for Lumen, Niagara, cloth and virtual-texture state to settle;
- do not use high-resolution tiling unless memory requires it and the actual effect stack has been tested under tiling.

### Stage 3 — optional Movie Render Graph migration

UE 5.8's MRG is now Production Ready and gains graph-only future features plus Light Modifier support. That is a strong long-term direction, but **do not rebuild tonight's capture pipeline merely to use the newer tool**.

After the P0 hero ships, encode:
- base hero render;
- portrait light variant;
- material-isolation / wireframe layers;
- metadata/audit output

as a reusable MRG configuration.

---

## 8. What the breakdown page should contain

A recruiter should understand the piece in this order:

### 1. Hero image
A1, full width. No tech copy over the face.

### 2. One-sentence role statement
Example structure:

> Melusina — original character and real-time lookdev for Melodia, rendered in Unreal Engine 5.8 with the project's unified stylized material spine.

Do not overclaim proprietary/AAA production equivalence.

### 3. A2 portrait
Large enough to inspect face, hair, material breakup and accessory response.

### 4. Material story
A3 plus a compact labeled legend:
- skin / face;
- bodice cloth;
- gradient sleeve;
- skirt fabric;
- metal/jewelry;
- translucent/emissive accent;
- graphic panel;
- hair.

Only name exact material instances where the asset binding is verified.

### 5. Construction proof
A1 ↔ A6 comparison:
- beauty;
- wireframe;
- optional clay/base-color view.

### 6. Garment / silhouette proof
A5 plus a small front/back or 3/4/back pairing.

### 7. In-engine context
A4 with:
- level name;
- real-time renderer;
- lighting approach;
- concise performance/context note if measured.

### 8. Pipeline strip
Only verified steps, e.g.:

`Concept / sculpt → Blender / retopo / rig → texture & material authoring → UE5.8 → M_Master_Toon_Universal → MRQ/MRG capture → website passport`

### 9. Optional motion proof
One 4–8 second loop if:
- hair is stable;
- cloth does not clip;
- idle is representative;
- compression does not destroy translucent/sparkle detail.

A bad loop is worse than no loop.

---

## 9. Website integration contract

When the new Unreal B2 keeper is approved, update **all public representations together**.

### Canonical source

Preferred asset location in `fromage3900/my-site`:

`generated/assets/character/melusina_ue58_b2_beauty_34_20260907_01.png`

Companion examples:
- `melusina_ue58_b2_portrait_20260907_01.png`
- `melusina_ue58_b2_material_macro_20260907_01.png`
- `melusina_ue58_b2_back_20260907_01.png`
- `melusina_ue58_b2_wireframe_20260907_01.png`

### Update these website surfaces

- `wix/index.html`
- `wix/curated-art.html`
- `wix/hiring-dossier.html`
- `wix/recruiter-one-sheet.html`
- `wix/resume.html` where appropriate
- OG/social-preview images on recruiter/technical pages
- `content/site-plates.json`
- `content/render-passports.json`
- generated Melusina passport if the capture metadata changes

### Critical `<picture>` rule

If a PNG/JPEG changes, also verify every `<source srcset>` in the same `<picture>`.

The previous failed plate survived a naive source swap because browsers preferred stale WebP `<source>` entries over the updated fallback `<img>`.

### Responsive QA

Test at minimum:
- 1440 px desktop;
- 1024 px tablet-ish width;
- 390 px mobile;
- 1200×630 social/OG crop.

At every width:
- face must remain visible;
- hair silhouette must not merge into background;
- no accidental head/hat/hand crop;
- captions must not imply a stronger proof level than the image supports.

---

## 10. Render acceptance checklist

### Character / anatomy
- [ ] hairline and hair mass read correctly
- [ ] no bald/scalp failure
- [ ] no obvious garment/body clipping
- [ ] no broken hand pose
- [ ] eyes focus correctly
- [ ] facial markings intact

### Composition
- [ ] silhouette reads at 320 px tall
- [ ] hands/hat/hem not accidentally cropped
- [ ] no major tangencies
- [ ] clear value hierarchy: face first, silhouette second, detail third

### Materials
- [ ] white bodice retains texture and highlight variation
- [ ] cyan/violet sleeves do not clip or posterize
- [ ] skirt layers separate by value/roughness
- [ ] jewelry has highlight definition without white clipping
- [ ] translucent accents have clean edges and no sorting ugliness
- [ ] hair response matches the intended hair solution

### Lighting / render
- [ ] manual exposure locked
- [ ] time-of-day/sky locked
- [ ] PPV canonical and logged
- [ ] material-instance updates flushed
- [ ] no temporal shimmer / hair crawl in final
- [ ] no viewport chrome
- [ ] no accidental debug actors

### Website
- [ ] render passport status = accepted before promotion
- [ ] old rejected Baldusina plate remains reject/history only
- [ ] all `src` and `srcset` paths agree
- [ ] OG/social image updated
- [ ] desktop + mobile manually reviewed

---

## 11. Breakdown acceptance checklist

A Melusina project page is ready when it contains:

- [ ] 1 indisputable Unreal hero
- [ ] 1 portrait
- [ ] 1 in-world shot
- [ ] 1 material/detail image
- [ ] 1 topology/wireframe comparison
- [ ] 1 back/silhouette proof
- [ ] short verified material legend
- [ ] concise software/pipeline statement
- [ ] contribution statement: solo/original work where true
- [ ] no repeated near-identical beauty frames
- [ ] no diagnostic/rejected images mixed into the finished board

---

## 12. Tonight's execution order

### 0–20 min — lock the scene
1. Open the live Melusina UE level/stage.
2. Confirm correct hair implementation.
3. Lock time of day, exposure, PPV.
4. Hide review/debug actors.
5. Confirm `M_Master_Toon_Universal` bindings are current.

### 20–60 min — A1 audition
1. Place 55–70 mm camera.
2. Build 3–5 compositions.
3. Fix pose/tangencies.
4. Add hair-separation rim.
5. Fast-render each candidate.

**Gate:** choose one A1 before moving on.

### 60–90 min — A2 + A3
1. 85–105 mm portrait.
2. Refine eye/catchlight and facial shadows.
3. Shoot one material macro.

### 90–120 min — A4/A5/A6
1. In-world context.
2. Back/silhouette.
3. Controlled wireframe.

### Final pass
1. Render the keeper set at final resolution.
2. Review pixels at 100% and thumbnail size.
3. Copy only approved keepers into website intake.
4. Update passports/slots.
5. Verify desktop/mobile/social crops.
6. Commit **only the approved set and metadata**.

---

## 13. Explicit kill list

Do not spend tonight on:

- another Baldusina diagnostic frame;
- 10+ tiny pose variations;
- material balls for the art-first page;
- flat viewport screenshots presented as beauty;
- Path-Tracer versions that no longer resemble the real game;
- rebuilding the capture system before art is approved;
- new character shader masters;
- a new git branch;
- world renders before Melusina A1/A2 are secure.

---

## 14. P0 definition of done

P0 is complete when:

1. A1 and A2 are accepted at pixel-review quality.
2. The hair silhouette is correct.
3. One compact technical breakdown exists.
4. The new Unreal image replaces the temporary EEVEE fallback on recruiter-facing pages.
5. `content/render-passports.json` marks the new hero accepted and the 2026-08-13 bald plate remains rejected.
6. Desktop/mobile/OG crops pass.
7. The site deploy is green.
8. The next render priority becomes `L_SakuraDream` world beauty.

---

## 15. Existing repo references to use, not duplicate

- `Docs/QUEUE.md` — MRQ setup state and render automation caveat.
- `Docs/WebsiteRenderArchive/RENDER_CAPTURE_CHECKLIST.md` — legacy beauty/wireframe/material/PCG/stats precedent.
- `Docs/DASH_RENDER_SYSTEM_SPEC_2026-08-30.md` — existing controlled capture-system intent.
- `Docs/Handoffs/NIKKI_GENSHIN_BLENDER_2026-08-13.md` — exact failure analysis for the rejected bald plate.
- `Tools/render_stage_glam_and_kitbash.py` — EEVEE fallback render family.
- `Tools/prep_stage_render_lighting.py` — stage lighting recipes.
- `Tools/setup_melusina_master_studio.py` — studio setup precedent.
- `Tools/melodia_stage_shot.py` — stage shot automation precedent.

**Do not invent another parallel capture or material system. Extend these contracts after the P0 art is shipped.**
