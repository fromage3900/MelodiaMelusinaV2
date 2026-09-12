# Unified PPV Stack + Oceanology Lookdev Integration Plan — 2026-08-28 (superseded)

**Lane:** `asset_qa` + `author` (additive; no master edits, no C++ source changes in this phase)
**Goal:** One polished, repeatable gameplay PPV stack on the certification levels, plus the Oceanology plugin integrated as hero-surface authority in ocean regions with the Nikki/bioluminescence/SDF aesthetic layered on top. See the 2026-09-04 grandmaster convergence handoff for current authority.

---

## 0. TL;DR — the two threads

| Thread | What | Blocker | Status |
|---|---|---|---|
| **PPV stack** | 3-blendable gameplay PPV_NikkiDream on 4 certification levels; grandmaster outline + grade + ink | Grandmaster editor migration and runtime proof | In progress |
| **Oceanology** | Plugin loads → MI instances under Nikki aesthetic → bioluminescence + SDF on ocean surface | .uplugin already corrected to 5.8.0; needs editor boot to confirm native load | .uplugin fixed; awaiting editor boot |

---

## 1. The four blendables (the unified stack)

This is the stack captured live on ZenForestTest 2026-08-27 and codified in
`finalize_ppv_hero_stack.py`. It is the **single reusable standard** for every shipping level.

| # | Blendable | Weight | Role | Domain | Audio-reactive? |
|---|---|---|---|---|---|
| 1 | `MI_StorybookOutline_Premium_Hero_Dream` | 1.0 | Ink outline + sticker edge + hatch shading on silhouettes | MD_POST_PROCESS | No (static character) |
| 2 | `MI_StarryNight_Hero` | 1.0 | Van Gogh star-field overlay, dream-state celestial tint | MD_POST_PROCESS | No (static character) |
| 3 | `MI_MeluColorGrade_PortfolioHero` | 1.0 | Color grading: Melusina palette, warmth, contrast curve | MD_POST_PROCESS | Yes — reads MPC_Melodia_Palette (BeatPhase, GlobalReactivity) |
| 4 | `MI_MelodiaInk_PortfolioHero` | 0.31 → target 1.0 | Printed music-box ink: halftone, hatch, grain, sync-vision, smear | MD_POST_PROCESS | Yes — reads MPC_Melodia_Palette + MPC_MelodiaInk (14 audio params) |

**Why these four and not three:** The 2026-08-26 plan documented a 3-blendable GameplayStandard
stack (Outline + Grade + Ink). The 2026-08-27 live capture added StarryNight as the fourth. The
owner's current direction is the 4-blendable PortfolioHero stack. The 3-blendable plan is
superseded — it remains in the tree for historical reference only.

**Ink weight:** Currently 0.31 on the live capture. Once the ink compiles and the 4 missing pins
are wired, the weight should be re-evaluated at 1.0 in a PIE session — 0.31 was set when the ink
was broken and contributing nothing visible. The plan target is 1.0, tuned by eye in PIE.

**Domain check:** All four must be MaterialDomain `MD_POST_PROCESS`. The material audit flagged
`MI_StarryNight_VanGogh` as resolving to `MD_SURFACE` (silently dropped by UE). The live capture
uses `MI_StarryNight_Hero`, not `MI_StarryNight_VanGogh` — but this must be verified per-PPV at
runtime, because the audit and the live capture disagree (see §3 below).

---

## 2. Level taxonomy

Packaged shipping maps are the six entries in `Config/DefaultGame.ini`,
including `/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype`.
Gameplay PPV certification covers Morning, KaleidoNave, ZenForestTest, and Sea
Above. FallenMoon and `_Template/L_Template` remain lookdev/regression maps.

`apply_dream_candidate_ppv.py` applies the gameplay 3-blendable stack through
the centralized contract. `finalize_ppv_hero_stack.py` is now reserved for the
lookdev/regression maps and may include StarryNight. It:
1. Loads each level
2. Finds or spawns `PPV_NikkiDream` (unbound=True, enabled=True, priority=10.0)
3. Sets WeightedBlendables to the 4 MIs at exact weights
4. Strips 7 color-grading scene overrides (keeps bloom 1.0 as lens character)
5. Saves the level
6. Writes `Saved/Audit/ppv_shipping_hero_2026-08-27.json`

---

## 3. The PPV reconciliation problem (must resolve first editor session)

Two sources disagree about the live state on ZenForestTest:

| Source | PPV label | Slot 1 | Grade weight | Ink weight |
|---|---|---|---|---|
| Live capture 2026-08-27 (`ppv_live_state_zenforesttest_2026-08-27.json`) | PPV_NikkiDream | MI_StarryNight_Hero @ 1.0 | 1.0 | 0.31 |
| Material audit 2026-08-28 (`melodia_material_audit`) | PPV_Dreamprint_Candidate | MI_StarryNight_VanGogh (surface domain — BROKEN) | 0.18 | — |

These cannot both be today's truth. **First editor action:** read the live PPV state through
Monolith (`editor_query` or `get_level_actors` + property read) and see which is real. Three
possibilities:
1. The audit is stale (cached from before the 08-27 hero stack was applied) → the live capture
   is correct, nothing to fix.
2. Someone swapped the stack after 08-27 → the audit is current, the hero stack script needs to
   be re-run.
3. Two PPV actors exist (PPV_NikkiDream + PPV_Dreamprint_Candidate) → remove the old one.

---

## 4. The ink compile fix (first editor action, after PPV reconciliation)

**Root cause:** M_PP_MelodiaInk's Custom HLSL node (MaterialExpressionCustom_7) declares 42
named inputs. 38 are wired. 4 are missing: `SceneColor`, `cR`, `cB`, `smeared`. These are the
4 SceneTexture PostProcessInput0 samples — the base frame color and three dynamic-UV offsets
(print misregistration R/B channels + motion smear).

**Why they're missing:** The connections audit (`m_pp_melodiaink_connections.json`) shows zero
SceneTexture expressions in the graph at all. The original build script
(`build_dreamprint_material.py:wire_custom_inputs`) creates 4 SceneTexture nodes from scratch
(st_base, st_cr, st_cb, st_smear) and wires them. Either the build was interrupted or a later
edit dropped them.

**The simple `_fix_ink_wiring.py` will NOT work** — it assumes 4 SceneTextures already exist
(`sts[0..3]`). There are none. It would IndexError.

**Correct fix path:**
1. Run `build_dreamprint_material.py:wire_custom_inputs(mat, custom, force=True)` — this creates
   the 4 SceneTextures at their correct coordinates, builds the dynamic-UV graph (print offset +
   smear offset chains), and wires all 42 inputs.
2. Recompile the material.
3. Save.
4. Verify compile via `melodia_material_get_compile_stats` (live).

**After the ink compiles:** the audio-reactivity gap closes. The ink is the only material that
reads the full 14-param audio set from MPC_Melodia_Palette + MPC_MelodiaInk. Once it compiles,
the entire PPV stack is audio-reactive through two of its four blendables (Grade + Ink).

---

## 5. Oceanology integration — the plan

### 5.1 Plugin load (prerequisite for everything below)

The `.uplugin` is already corrected: `EngineVersion: 5.8.0`, binaries match engine BuildId
`55116800`. The plugin should load natively on next editor boot. The 2026-08-27 Gate E core
pass confirmed: native load, actor spawn, PIE stability, save/close/reopen survival.

**Verify on boot:**
- `LogPluginManager` shows `Mounting Project plugin Oceanology_Plugin` + both modules loaded
- No compatibility modal
- `AOceanologyInfiniteOcean` class is registered (spawnable via Python)

If the modal still appears despite the 5.8.0 correction, the fallback is a full closed-editor
rebuild from Source/ (AGENTS.md rule 15/21).

### 5.2 Authority model (from OCEANOLOGY_WATER_COEXISTENCE_2026-08-15.md)

| Concern | Authority | Oceanology's role |
|---|---|---|
| Gameplay water query | `UMelodiaWaterInteractionSubsystem` | Adapter behind existing interface (spike #1) |
| Swim/dive state | `UMelodiaTraversalComponent` | Plugin swimming OFF |
| Contact events → FLIP/audio | `UMelodiaWaterInteractionSubsystem` | Plugin wave-crest splash OFF |
| Surface shading | v9/v10 MIs + `UMelodiaWaterRippleMaterialBridgeComponent` | FFT master intact; Nikki/biolum applied at MI layer |
| Underwater post-process | `UMelodiaWaterUnderwaterPostProcessComponent` (music-reactive) | Plugin fog/caustics as base at LOWER priority; Melodia grade on TOP |
| Audio reactivity | `MPC_Melodia_Palette` single-writer | Plugin wave-state audio OFF; ocean is MPC consumer |

**Single rule:** Oceanology is the hero-surface simulation authority in ocean regions ONLY. It
is never a second writer on gameplay state. The Nikki aesthetic layers on top as MI instances
parenting the plugin's `M_Oceanology` master.

### 5.3 Material integration (non-destructive, MI layer only)

```
M_Oceanology (plugin master — DO NOT EDIT, reparenting breaks FFT wiring)
  └─ MI_Oceanology_NikkiHero  (NEW, under /Game/EnvSandbox/Materials/Instances/Oceanology/)
       ├─ TP_Default baseline (surface)
       ├─ MF_WaterBioluminescence_v9 → emissive/foam channel (exponential decay impulse)
       ├─ MF_NikkiSDFRibbon → wave crest accent (SDF band + distance falloff)
       ├─ MF_NikkiPearlSheen → caustic iridescence (dual-layer thin-film)
       ├─ MF_NikkiGlitterHalo → foam sparkle (world-aligned hash + fresnel)
       └─ MPC_Melodia_Palette params (BeatPulse, GlobalReactivity, etc.) → same accumulator chain as v9/v10
```

**What this gives us:**
- FFT ocean waves (Oceanology's spectral Gerstner) with Nikki dream aesthetics on top
- Bioluminescent glow on wave contact, decaying exponentially (same I(t) = I₀·e^(-2.5·dt) as
  the grotto water — one decay model across surface and underwater)
- SDF ribbon tracing wave crests in pastel light
- Pearl-sheen caustics that shift with viewing angle
- Audio-reactive: the ocean pulses with the music through the same MPC the PPV reads

**What we do NOT do:**
- Do not edit `M_Oceanology` (reparenting breaks FFT wiring)
- Do not enable plugin swimming/buoyancy (Melodia traversal wins)
- Do not enable plugin wave-state audio (single writer on `MS_Water_*`)
- Do not double caustics (disable plugin caustics if Melodia underwater material already
  projects them — decide in L_Atlantis slice, spike #3)

### 5.4 Underwater post-process priority

```
[BASE]  Oceanology underwater PP (fog, caustics, absorption, god rays) — photoreal base
[TOP]   UMelodiaWaterUnderwaterPostProcessComponent (dynamic v9 underwater material) —
        music-reactive grade tinted last by MPC
```

The Melodia underwater component is per-pawn (camera-manager blend), NOT a PPV actor. The
Oceanology underwater PP is a plugin-managed volume. They coexist by priority: plugin base
below, Melodia reactive grade above. This is already designed in the coexistence doc; no new
code needed, just configuration at placement time.

### 5.5 Niagara integration

Oceanology ships with spectral Gerstner Niagara systems:
- `NS_SpectralGerstnerWaves_Displacement` — wave deformation
- `NS_SpectralGerstnerWaves_Splash` — crest splash
- `NE_FoamBurst` / `NE_WhitewaterSplash` — foam emitters

These are the plugin's particle authority for ocean effects. The bioluminescence harmony bridge
(`UMelodiaWaterNiagaraBridgeComponent`) already writes contact events to Niagara Data Channels
at 60 contacts/sec max. The integration path:
1. Let Oceanology's Niagara drive the wave/foam simulation
2. The Melodia Niagara bridge feeds bioluminescence impulses into the same particle system
   (emissive color on contact, exponential decay)
3. `NPC_Melodia_Palette` writes the same audio scalars to Niagara that it writes to the PPV

The ocean's foam glows on beat impacts. That's the lookdev signature.

### 5.6 Region model

| Region | Water authority | Aesthetic |
|---|---|---|
| L_Atlantis ocean vistas | Oceanology (FFT Gerstner, hero surface) | Nikki hero + bioluminescence + SDF ribbon |
| Interior grottos / celestial ponds | native Water + v10 FLIP ladder | Nikki grotto + bioluminescence (unchanged) |
| Gameplay-validated zones | native Water + v9/v10 | unchanged |

Oceanology is scoped to hero ocean vistas only (RTX 3080/4070+ class). Interior water stays on
the existing ladder.

### 5.7 Post-install verification checklist

1. **Closed-editor build** with plugin enabled (AGENTS.md rules 15/21 — full rebuild, unity
   collisions checked).
2. **Spike #1:** surface-query entry point confirmed; adapter fills all `FMelodiaWaterSample`
   fields; gameplay consumers see identical behavior vs native regions.
3. **Spike #2:** capture plugin MI parameter list via reflection (Monolith `get_cdo_properties`,
   NOT Python `load_blueprint_class` — the D_DamageType fatal rule).
4. **Spike #3:** caustics dedup — disable plugin caustics if Melodia caustics already project.
5. **PIE:** swim/dive via `UMelodiaTraversalComponent` authoritative; contact events spawn FLIP
   pool/splash once; `MS_Water_*` MetaSounds fire once per event.
6. **Material:** bridge param writes land on the Oceanology MI (verify via material telemetry
   params, same method as v9); MPC pulse visibly drives the ocean surface.
7. **Post-process stack:** both underwater layers active, Melodia grade on top, no double
   caustics.
8. **Audit report** into `Saved/Audit/`; update the coexistence doc's spikes to verdicts.

---

## 6. Execution order (the session plan)

### Phase 1 — Foundation repair (editor closed, then first editor session)

| Step | Action | Tool | Editor? |
|---|---|---|---|
| 1.1 | .uplugin already fixed (5.8.0) | — | done |
| 1.2 | Launch editor | owner | yes |
| 1.3 | Confirm Oceanology loads natively (LogPluginManager) | `melodia_system_health` | yes |
| 1.4 | Reconcile PPV state on ZenForestTest (read live actors) | Monolith `get_level_actors` | yes |
| 1.5 | Fix ink: `wire_custom_inputs(force=True)` → recompile → save | `build_dreamprint_material.py` via Monolith `run_python` | yes |
| 1.6 | Verify ink compiles | `melodia_material_get_compile_stats` | yes |
| 1.7 | Re-run material audit | `melodia_material_audit` | yes |
| 1.8 | Re-run PPV report | `melodia_ppv_report` | yes |

### Phase 2 — Unified stack deployment

| Step | Action | Tool | Editor? |
|---|---|---|---|
| 2.1 | Strip color overrides on the 4 gameplay certification levels | `strip_ppv_color_overrides.py` | yes |
| 2.2 | Apply grandmaster gameplay stack to the 4 certification levels | `apply_dream_candidate_ppv.py` via Monolith | yes |
| 2.3 | Verify audio/cymatics contract (beat grid, MPC scalars, driver, weights) | `bind_ppv_audio_contract.py` | yes |
| 2.4 | PIE on Sea Above: confirm deterministic outline and downstream beat/cymatics response | owner capture | yes |
| 2.5 | Keep StarryNight hero stack confined to lookdev/cinematic regression maps | `finalize_ppv_hero_stack.py` | yes |

### Phase 3 — Oceanology integration

| Step | Action | Tool | Editor? |
|---|---|---|---|
| 3.1 | Confirm plugin loaded (step 1.3 covers this) | — | yes |
| 3.2 | Read-only asset inventory (registered classes, water materials) | Monolith reflection | yes |
| 3.3 | Create `MI_Oceanology_NikkiHero` parenting `M_Oceanology` | Monolith material tools | yes |
| 3.4 | Wire bioluminescence MF + Nikki SDF/pearl/glitter MFs into MI emissive/foam | Monolith | yes |
| 3.5 | Wire MPC_Melodia_Palette params into MI (same names as v9/v10) | Monolith | yes |
| 3.6 | Spike #1: surface-query entry point → adapter design | C++ (separate session) | no |
| 3.7 | PIE: ocean + Nikki aesthetic + audio reactivity | owner eyeball | yes |

### Phase 4 — Lookdev renders

| Step | Action | Tool | Editor? |
|---|---|---|---|
| 4.1 | Stage SakuraDream render test level with ocean + PPV stack | Monolith | yes |
| 4.2 | Capture `niagara_sakura_ambience` hero render (1920x1080) | `resonant_world_compile_passage` | yes |
| 4.3 | Capture `nikki_surface_polish` material passport (2048x2048) | same | yes |
| 4.4 | Write PNG evidence + assertion JSON next to frames | `resonant_world_project_chronicle` | yes |

---

## 7. The ink expansion — Rider shader authoring (this session)

The owner asked whether to expand MelodiaInk beyond simple halftone, since the outline already
does dot/hatch shading. Three design options were proposed and ALL THREE have been authored as
Rider-authorable shader source (.ush) in the new `MelodiaShader` module.

### 7.1 The MelodiaShader module (new this session)

Created at `Source/BS_GodFile/MelodiaShader/` with:

| File | Purpose |
|---|---|
| `MelodiaShader.Build.cs` | Module rules — registers `Shaders/` dir, deps: Core/CoreUObject/Engine/RenderCore/RHI |
| `Public/MelodiaShader.h` | Module registration (IMPLEMENT_MODULE) |
| `Private/MelodiaShader.cpp` | Module implementation (no C++ logic — pure shader container) |
| `Shaders/MelodiaInkCommon.ush` | Shared types (FMelodiaInkAudio, FMelodiaInkParams), helpers (hash, SDF, luminance, decay) |
| `Shaders/MelodiaInkSdfNotation.ush` | **Option A**: SDF music-notation patterns (staff lines, note-heads, crescendo, grace notes, dissonant crosshatch, victory radiance) |
| `Shaders/MelodiaInkBioluminescent.ush` | **Option C**: Bioluminescent decay bridge — shared I(t)=I₀·e^(-λ·dt) with water bioluminescence |
| `Shaders/MelodiaInkPatternRouter.ush` | **Option B**: Pattern router — crossfades between 4 modes (halftone, SDF notation, watercolor, shattered) + applies bioluminescent bridge |
| `Shaders/MelodiaNikkiCommon.ush` | Nikki aesthetic helpers (SDF ribbon, pearl sheen, glitter halo, petal shadow, sticker edge, squish WPO) — extracted from expand_nikki_features.py |
| `Shaders/MelodiaBiolumCommon.ush` | Shared bioluminescence helpers (contact impulse, sum impulses, color shift, foam-to-glow) — for water + ocean |

Registered in `BS_GodFile.uproject` (new module entry) and `BS_GodFile.Build.cs` (new dependency).
This is a **header change** (new module) — requires a full closed-editor rebuild per AGENTS.md #15/#21.

### 7.2 How Rider uses these files

Per AGENTS.md §2.1 and the `melodia-shader-rider` skill:
- Rider maps `Source/BS_GodFile/MelodiaShader/Shaders/` as a shader source root
- Full HLSL syntax validation, macro expansion, semantic highlighting — offline, no editor needed
- IWYU inspection flags unused `#include` directives on shader sources
- Qodana (`QDJB` profile) runs static analysis before the shader reaches the editor lane

### 7.3 How the editor consumes these files

The shader source is NOT compiled by UE's shader compiler directly (that path is for
virtual node shaders, not Custom HLSL). Instead:
1. The build script (`build_dreamprint_material.py`) reads the `.ush` content and inlines it
   into the Custom node's `code` property — same pattern it already uses for the existing HLSL
2. OR: a Material Function is created that wraps the `.ush` as a shader include (editor lane)
3. The `.ush` files serve as the **source of truth** for the HLSL — Rider validates, the build
   script consumes, the Custom node embeds

### 7.4 The three ink expansion options — now authored

| Option | Concept | File | Unique vs outline? | Status |
|---|---|---|---|---|
| A: SDF music-notation ink | Distance-field patterns that read as musical notation (staff lines, note-heads, crescendo swells) driven by audio params | `MelodiaInkSdfNotation.ush` | Yes — field-based, not edge-based | Authored |
| B: Interchanging pattern router | Pattern-index float driven by musical state; crossfade between 4 HLSL pattern functions | `MelodiaInkPatternRouter.ush` | Yes — pattern selection by musical state | Authored |
| C: Bioluminescent ink bridge | Wire ink emissive to same exponential-decay impulse as water bioluminescence | `MelodiaInkBioluminescent.ush` | Yes — connects surface Nikki to underwater Oceanology | Authored |

The pattern router (#B) composes ALL THREE: it calls the SDF notation pattern (#A), applies
the bioluminescent bridge (#C), and crossfades between modes. It is the master entry point.

### 7.5 Integration with the existing ink build

The existing `build_dreamprint_material.py` embeds HLSL as a Python string (`CODE = r"""..."""`).
The new shader source files are the **authoritative version** of that HLSL. The integration path:

1. Author/edit the `.ush` files in Rider (syntax-validated)
2. The build script reads the `.ush` content and inlines it into the Custom node
3. The Custom node compiles in the editor (after the 4 missing pins are wired)
4. The material instance (MI_MelodiaInk_PortfolioHero) inherits the parameters

A future improvement: the build script can `#include` the `.ush` at build time instead of
maintaining a parallel Python string. For now, the `.ush` files are the design reference and
Rider validation surface; the Python string remains the runtime source until the editor session
proves the new patterns compile and render correctly.

### 7.6 New parameters added to the ink

The expanded ink adds these parameters to the Custom node (beyond the existing 42):

| Parameter | Default | Range | Purpose |
|---|---|---|---|
| `PatternIndex` | 0.0 | 0..3 | Pattern selector (0=halftone, 1=SDF, 2=watercolor, 3=shattered) |
| `PatternBlend` | 0.0 | 0..1 | Crossfade between current and next pattern |
| `BiolumDecay` | 2.5 | 0.5..10 | Decay constant λ (matches water) |
| `BiolumIntensity` | 2.0 | 0..5 | Peak impulse I₀ (matches water) |
| `BiolumOn` | 0.0 | 0/1 | Bioluminescent bridge gate |

These are material instance parameters — each PPV profile (GameplayStandard, PortfolioHero,
Narrative) can dial them independently. The PortfolioHero profile (used in the 4-blendable stack)
should have `BiolumOn=1` and `PatternIndex=1` (SDF notation) for the hero look.

---

## 8. Risk register

| Risk | Mitigation |
|---|---|
| Oceanology compatibility modal still appears despite .uplugin fix | Full rebuild from Source/ (rule 15/21); Gate E already passed on 08-27 |
| Ink `wire_custom_inputs(force=True)` recreates the entire input set — may duplicate existing MPC/scalar nodes | The function checks `by_name` dict and reuses existing CollectionParameter nodes; only creates new ones if missing. Verify post-run that expression count doesn't balloon. |
| Two PPV actors on ZenForestTest (NikkiDream + Dreamprint_Candidate) | Step 1.4 reconciliation; remove the old actor if duplicate found |
| `MI_StarryNight_Hero` domain silently resolves to MD_SURFACE | Verify per-PPV at runtime via Monolith; if broken, fix the parent master's MaterialDomain to MD_POST_PROCESS |
| Oceanology MI parameter names don't match v9/v10 (spike #2) | Capture via Monolith reflection before wiring; adapt parameter names |
| Plugin example BPs fail to compile on 5.8 | Known debt (Gate E caveats); do not fix plugin assets without owner approval |
| Double caustics in underwater PP | Spike #3 decides; disable plugin caustics if Melodia already projects |
| D_DamageType fatal crash if any script inspects a skill Blueprint | Never call `load_blueprint_class()` on skill assets; use Monolith `get_cdo_properties` instead |

---

## 9. Definition of done

### PPV stack
- [ ] M_PP_MelodiaInk compiles (0 errors, 4 SceneTexture inputs wired)
- [ ] Material audit shows no audio-reactivity gap (ink consumes audio)
- [ ] PPV report shows no surface-domain blendables, no label mismatch, no grade weight mismatch
- [ ] All 4 gameplay certification levels have PPV_NikkiDream with the 3-blendable gameplay stack
- [ ] Color overrides stripped on all 4 certification levels
- [ ] Audio contract verified (beat grid, MPC scalars, blendable weights)
- [ ] PIE on ZenForestTest: owner confirms 4-blendable stack renders correctly
- [ ] `ppv_shipping_hero_2026-08-27.json` is retained as historical lookdev evidence; current proof must identify the 4 certification levels and the grandmaster outline

### Oceanology
- [ ] Plugin loads natively (no compatibility modal)
- [ ] `MI_Oceanology_NikkiHero` created and parented to M_Oceanology
- [ ] Bioluminescence MF + Nikki SDF/pearl/glitter MFs wired into MI
- [ ] MPC_Melodia_Palette params wired into MI
- [ ] PIE: ocean surface pulses with music; bioluminescence glows on contact
- [ ] Audit report written to `Saved/Audit/`

### Lookdev renders
- [ ] `niagara_sakura_ambience` hero PNG captured (1920x1080) + assertion JSON
- [ ] `nikki_surface_polish` material passport PNG captured (2048x2048) + assertion JSON
- [ ] Both pass `resonant_world_validate` evidence verdicts

---

## 10. Files referenced

| File | Role |
|---|---|
| `finalize_ppv_hero_stack.py` | Applies 4-blendable stack to 5 levels (idempotent) |
| `build_dreamprint_material.py` | Ink master build + `wire_custom_inputs(force=True)` for pin fix |
| `strip_ppv_color_overrides.py` | Strips 7 color-grading overrides per PPV actor |
| `bind_ppv_audio_contract.py` | Audio contract auditor (beat grid, MPC, blendables) |
| `finalize_ppv_for_shipping.py` | One-command entry point for PPV finalize |
| `wire_water_bioluminescence_harmony.py` | Bioluminescence harmony bridge config |
| `expand_nikki_features.py` | 7 Nikki MF build scripts (SDF ribbon, pearl, glitter, etc.) |
| `OCEANOLOGY_WATER_COEXISTENCE_2026-08-15.md` | Coexistence authority model |
| `OCEANOLOGY_ENABLE_STATE_2026-08-27.md` | Gate E core pass evidence |
| `PPV_FINALIZE_PLAN_2026-08-26.md` | Prior PPV plan (3-blendable, superseded by this doc) |
| `ppv_live_state_zenforesttest_2026-08-27.json` | Live PPV capture (the 4-blendable source of truth) |
| `m_pp_melodiaink_connections.json` | Ink graph connection audit (38/42 wired) |
