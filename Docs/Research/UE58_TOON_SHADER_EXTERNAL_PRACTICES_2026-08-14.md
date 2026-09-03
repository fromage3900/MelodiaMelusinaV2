# UE 5.8 Toon Shading — External Practices Research & Deep Review

**Date:** 2026-08-14 · **Scope:** how top studios/teams run toon (三渲二) pipelines on UE 5.x, and a deep review of the project's current toon platform against those practices. Primary sources were re-opened and verified this session; "publicly observed" items are labeled as such and are not claims of access to proprietary graphs.

---

## 1. Deep review — the project's current toon platform (verified this session)

### 1.1 Verified live configuration

| Item | Verified state |
|---|---|
| Substrate | `r.Substrate=True` in `Config/DefaultEngine.ini`; **Blendable GBuffer** (`r.Substrate.ProjectGBufferFormat=0`) |
| Core toon path | `M_Master_Toon_Universal` → `SubstrateToonBSDF`; 1,400+ instances parented to it |
| Toon Profiles | 18 `TP_*` assets under `EnvSandbox/Materials` |
| Specialist parents | Landscape HeightBlend, Water (v6 canonical, v7 experimental), Impressionist, SDF/Cosmic, Foliage, Fabric/Character, Post Process |
| MooaToon | **Not installed.** `Plugins/MooaToon` does not exist; deferred per prior decision |
| 2026-08-14 sweep | 2,299 meshes censused; 1,680 bad mesh slots (WorldGrid/`MI_Env_*`/`MI_Universal_*`/NONE) routed to per-prop materials; 2,397 material instances LayerA-activated + PBR-routed; 15 `MI_BlingVol3_*` created |

### 1.2 What the live census proved about the current graphs

- The per-prop instance leaves are **parameter shells**: they parent to `M_Master_Toon_Universal` and override almost nothing. Before this session's pipeline, their Albedo/NormalMap/ORM/weights all fell through to the master's **default texture set** (`/Game/Textures/sbs_-_seamless_abstract_pack…`, gradient `Horizontal_1`, SDF `Marble_5`) — i.e. every imported environment prop was rendering grey procedural noise, not its pack texture.
- The master's Layer A path (`Albedo`/`NormalMap`/`ORM`/`RoughnessMap`/`MetallicMap` in group `LayerA`, gated by `bLayerA_Active` + `LayerA_TextureWeight` + the Hybrid-group `TextureWeight`) is the correct texture contract; 4b/4c only set the top-level `TextureWeight` knob, which is why the LayerA fix (override all three + the switch) was the real repair.
- 718 root-level duplicate meshes exist (`<stem>.uasset` at `Meshes/Environment` root vs `<stem>/StaticMeshes/<stem>.uasset`), both zero-referenced per the census. Dedupe + final verify phases are queued.

### 1.3 Deep-review verdict (consistent with the 2026-08-08 intake)

The platform is architecturally sound and now substantially repaired, but it is **Epic-native Substrate Toon, not a studio toon framework**. That distinction matters: everything below shows that the strongest toon results in UE5 come either from (a) Epic's experimental `SubstrateToonBSDF` + `ToonProfile` on **Adaptive GBuffer**, or (b) engine-fork frameworks like MooaToon. The project is on path (a) with **Blendable GBuffer**, which caps what the toon path can express. The Blendable constraints are concrete, from the official docs verified this session:

- **One closure feature per pixel** — priority Fuzz > SSS > Haziness.
- **No F90, no per-pixel-MFP diffusion SSS, no haziness, no native glints.**
- Glints require `r.Substrate.Glints=1` and are **not available on Blendable** — sparkle/gemstone features cannot be implemented with native Substrate glints on the current GBuffer format.

---

## 2. External research — how top teams run toon on UE 5.x

### 2.1 Epic's own path: Substrate Toon + Toon Profile (official docs, verified 2026-08-14)

From [Substrate Materials Overview](https://dev.epicgames.com/documentation/en-us/unreal-engine/overview-of-substrate-materials-in-unreal-engine) (UE 5.8):

- **GBuffer formats are a fidelity/performance fork.** Blendable = fixed memory, predictable speed, 60 Hz, cross-platform consistency, no cook overhead. Adaptive = full Substrate potential, `+15%` cook time, forces DBuffer decals, only SM6 current-gen/PC; other platforms silently fall back to Blendable.
- **Closure budgets:** `r.Substrate.BytesPerPixel=80` default; `r.Substrate.MaxClosureCount`; materials are auto-simplified when over budget; simplification is visible in the Material Editor Substrate stats panel.
- **Parameterization is F0/Diffuse Albedo**, not BaseColor/Metalness — dielectric F0 0.02–0.06 (gemstones to 0.18), conductors 0.5–1.0 (gold 1.0/0.71/0.29, copper 0.95/0.64/0.54). This is the vocabulary the current master's PBR inputs should be mapped to.
- **Layering:** `Substrate Vertical Layer` for true coat/transmittance layering (car paint, varnish, wetness); `Horizontal Blend` and `Coverage Weight` operators; **Material Layers UI is not unified with Substrate** — the project's LayerA/B/C approach inside one Toon BSDF is the correct Substrate-era pattern, not the legacy Material Layer system.
- **Complexity sets** map features to lighting cost: Simple (default lit) → Single (F90, Fuzz, SSS, Clear Coat) → Complex (Anisotropy, Specular Profile, Eye, Hair) → Complex Special (Glints). Toon surfaces with anisotropic hair/sheen should be deliberately Complex-tier and budgeted.

**Practice translation:** top teams using Epic-native toon keep one Toon BSDF as the common lighting response, put stylization into Toon Profiles + ramps + masks, and reserve Adaptive GBuffer (or per-platform Blendable fallback) as a declared quality tier. The 2026-08-08 intake reached the same conclusion; this session's verified docs confirm the exact knobs.

### 2.2 MooaToon — the dominant community/studio toon framework (primary source, verified 2026-08-14)

[MooaToon](https://github.com/JasonMa0012/MooaToon) ("The Ultimate Solution for Cinematic Toon Rendering in UE5", 726★, updated 2026-07-15, v5.7 released). Publicly credited work includes **miHoYo's Honkai Impact 3rd Part 2 cinematic** (「海正用火的声音歌唱」, rendered with MooaToon) and multiple anime MV productions; education partner aixmmc.

Key facts:

- **It is an engine fork.** Installs either a precompiled engine or source-built engine with modified engine plugins (`MooaToonScripts` C++ in `Engine/Plugins`), plus a project plugin (`Plugins/MooaToon` = materials + blueprints). Updating = re-downloading the whole engine package; only the newest UE version is maintained (older = paid support).
- **It does not support Substrate.** FAQ: "暂不支持Substrate." This makes MooaToon and the project's current Substrate path **mutually exclusive**.
- **Platform reality:** no mobile; XR untested; Lumen-based GI; shadow-control features require `Ray Tracing Shadow` + Hardware Ray Tracing; translucency edge light needs Lumen front-layer translucency reflections.
- **Feature set that defines the studio toon vocabulary** (the de-facto checklist for UE5 anime pipelines):
  - Lumen GI intensity/blending and reflection intensity — toon teams treat GI as a *mix knob*, not a fixed physical result.
  - Virtual Shadow Map + Ray Traced shadows with **partial self-shadow ignore** and **controllable hair shadow width** (cel shadows that don't smear on hair).
  - Material-layer system for two style families: **Japanese animation** (pure color, fast, clear light/shadow) vs **American cartoon** (GI present, softer shading).
  - Customizable Base/Shadow/Specular color; light/shadow range; ramp map; highlight range; **anisotropic highlight**.
  - **Kajiya-Kay dynamic stylized hair highlighter**.
  - **Per-light, screen-space-depth rim light**.
  - **Face shadow** via spherical-mapped vertex normal, normal map, or custom method.
  - **Outline**: back-face outline + screen-space depth/normal-convolution front-face outline, outputting velocity so **TSR anti-aliasing keeps outlines stable**; one-click smooth-normal baking tool; Houdini sample for normals/vertex colors.
  - Cinematic post: correct auto/manual exposure, global exposure compensation, saturation/contrast, LookDev tool; morph-target normal intensity.

**Practice translation:** the highest-leverage toon features this project does not yet have as first-class items are: (1) smooth-normal/vertex-color baking for outlines and face shadow; (2) an explicit outline pass that writes velocity (TSR-safe); (3) Kajiya-Kay hair/anisotropic highlight; (4) light/shadow *range* controls as a ramp contract; (5) GI-as-mix-knob. All of these are implementable in the Substrate Toon path without forking the engine — they are material/graph features, not engine features — except for the shadow-width/self-shadow tricks which need RT shadow hooks.

### 2.3 Infinity Nikki (Infold/Papergames, UE5) — the project's named benchmark

From the [Epic technical interview](https://www.unrealengine.com/developer-interviews/behind-the-scenes-of-infinity-nikki-tracing-a-glamorous-turn-to-an-unreal-open-world) (already verified and documented in `Docs/Research/INFINITY_NIKKI_PIPELINES_AND_PROJECT_UPDATES_2026-08-14.md`), the durable patterns are:

- **PBR-based lighting under a cartoon fantasy surface** — believability under changing light/weather/weekly art benchmarks, not per-material lighting hacks.
- **Versatile fabric masters that merge textures and reduce variants**; standardized PBR inputs; custom treatment for transparent character pieces; special high-value materials for jewelry.
- **VT/VHM terrain optimization; platform-aware foliage/fur LOD**; Enlighten for dynamic bounced lighting and cross-platform consistency (Silicon Studio press release, verified earlier this month).
- **Restrained post processing** to leave room for photo filters/modes.
- Engine-side cloth (Chaos Cloth) + authored clipping rules; photo/pose layer separate from locomotion.

This is the project's existing benchmark for *governance* (few masters, shared contracts) — and it is the correct answer to "one master per outfit/biome" (intake doc §4). Note: Infinity Nikki predates 5.8 Substrate Toon; its published material is about production discipline, not about Substrate knobs.

### 2.4 Other top UE5 toon/stylized productions (publicly observed)

| Production | Studio | UE | Observed toon technique (public) |
|---|---|---|---|
| **Azur Promilia** | Manjuu | UE5 | Anime-style open world; cel shading with hard shadow ramps, baked-style albedo, outline + rim in footage/tech trailers |
| **The First Berserker: Khazan** | Neople/Nexon | UE5 | Stylized cel/dark-comic rendering — harsh directional shadows, silhouette weight, ink-style accents |
| **Phantom Blade Zero** | S-GAME | UE5 | Painterly stylized look; non-photoreal lighting as a headline feature in public trailers |
| **Honkai Impact 3rd Pt.2 cinematics** | miHoYo | UE5 (MooaToon) | Verified above — studio-grade 三渲二 cinematics via the MooaToon engine fork |
| **Persona 3 Reload / Metaphor** | Atlus | UE4 | Precedent for anime-UE toon at AAA scale: ramp-driven shading + outline + face shadow; not UE5, cited as lineage |

These are labeled as public observations (trailers/release material), not verified primary technical documentation. The pattern across all of them is identical to MooaToon's feature list: **shadow ramps + outline + rim + face shadow + hair highlight + baked normals**, regardless of whether the lighting is engine-native (Substrate/legacy lit) or engine-forked.

---

## 3. Decision matrix — for Melodia's toon path

| Axis | Substrate Toon (current) | MooaToon (fork) |
|---|---|---|
| Engine cost | Config switch + material work | **Engine source fork or precompiled engine**; re-download per update; only newest UE maintained |
| Compatibility | Stays on stock UE 5.8; all other plugins safe | Forked engine; plugin/tool compat must be re-validated; **no Substrate** |
| GBuffer | Blendable now; Adaptive available on SM6 | Legacy + RT shadow hooks |
| Cel control | Toon Profile + ramp/texture work (all material-level) | Richer shadow/outline/hair hooks via engine changes |
| Mobile | Blendable is the sanctioned cheap path | **Not supported** |
| Studio precedent | Epic-native indie/AA pipelines | miHoYo cinematics, anime MV studios |
| Migration risk | None | Full fork; irreversible-ish; only worthwhile if measured quality gap is proven |

**Recommendation (unchanged from prior lanes, now with primary-source backing):** stay on Substrate Toon with Blendable GBuffer as the baseline, promote **Adaptive GBuffer as the declared Hero/Cinematic tier** (SM6 PC), and implement the MooaToon-style feature list at the **material/graph level** — this is possible for everything except RT-hook shadow features. Re-evaluate the fork only if a measured benchmark shows the material-level implementation can't reach the style bar (e.g. hair shadow width, self-shadow control).

## 4. Recommended adoptions for the current master (next toon work, in priority order)

1. **Ramp contract**: consolidate onto `MF_ColorRamp3`; expose light/shadow *range* + ramp per MooaToon's model (MooaToon exposes exactly this and it is the single biggest control artists use).
2. **Outline lane**: back-face + screen-space front-face outline **writing velocity** (TSR-stable), with a smooth-normal baking tool (MooaToon ships one; the project has SDF/ornament work that needs it) — put it in the Post Process/outline lane per the intake doc.
3. **Face shadow + baked normals**: spherical-vertex-normal face shadow as an optional character-lane feature (project has `MF_AnimeSkinWrap`/`TP_Character`).
4. **Hair/anisotropic highlight**: Kajiya-Kay dynamic highlight as a character/fabric extension with a cheap fallback (Blendable-safe; do NOT plan native glints on the current GBuffer).
5. **GI-as-knob**: add an explicit GI intensity/blend control group on the master (MooaToon's core differentiator; also how Nikki keeps PBR believability).
6. **Adaptive GBuffer tier**: set project GBuffer format to Adaptive with per-platform closure budget (`r.Substrate.MaxClosureCount`), or keep Blendable + document the Hero tier switch — a concrete capture fixture (day/dusk/night/wet/Lumen/photo) decides it. Watch the `+15%` cook cost and SM5 fallback.
7. **Parameter hygiene** from the sweep: the LayerA contract (Albedo/NormalMap/ORM/RoughnessMap/MetallicMap + `LayerA_TextureWeight`/`TextureWeight`/`bLayerA_Active`) is now enforced pipeline-wide via `fix_pbr_pipeline.py` — treat it as the canonical input contract for all new toon surfaces.

## 5. Sources (all opened/verified 2026-08-14)

- [Substrate Materials Overview (UE 5.8)](https://dev.epicgames.com/documentation/en-us/unreal-engine/overview-of-substrate-materials-in-unreal-engine) — GBuffer formats, closure budgets, F0 parameterization, simplification, operators, Blendable feature limits.
- [MooaToon repository](https://github.com/JasonMa0012/MooaToon) + [mooatoon.com](https://mooatoon.com) + [Getting Started](https://mooatoon.com/docs/GettingStarted) + [FAQ](https://mooatoon.com/docs/FAQ) — feature list, engine-fork model, v5.7, no-Substrate, platform limits, miHoYo credit.
- Epic's [Behind the Scenes of Infinity Nikki](https://www.unrealengine.com/developer-interviews/behind-the-scenes-of-infinity-nikki-tracing-a-glamorous-turn-to-an-unreal-open-world) (verified previously; summarized in `Docs/Research/INFINITY_NIKKI_PIPELINES_AND_PROJECT_UPDATES_2026-08-14.md`).
- Silicon Studio [Enlighten integration release (Infinity Nikki)](https://www.siliconstudio.co.jp/en/news/pressreleases/2025/250206InfinityNikki/pdf/NewsRelease_20250206_EN.pdf).
- Project-internal baselines: `Docs/Research/UE58_TOON_MATERIAL_INTAKE_INFINITY_NIKKI_2026-08-08.md`, `Saved/Audit/sweep_pbr_state.json`, `Saved/Audit/pbr_pipeline_state.json`, `Config/DefaultEngine.ini`.

## 6. Bottom line

The project is now a **repaired, Epic-native Substrate Toon platform**. The external research confirms the repair direction: the world's toon pipelines converge on the same feature vocabulary (ramps, outline with velocity, rim, face shadow, hair highlight, GI-as-knob, baked normals), and all of it except RT-hook shadow tricks is implementable on Substrate Toon + Blendable GBuffer at the material level. MooaToon is the fork alternative and is **mutually exclusive with Substrate**; it stays deferred pending a measured gap. The highest-value next move is the ramp/outline/normal-baking lane plus an Adaptive-GBuffer Hero tier with a capture fixture.
