# Render Polish Plan — tonight 2026-09-30 (written 18:24 ET; execution window 18:25–19:05 ET)

Rules: duplicates only (`*_Render2026`, folder /Game/Melodia/_PROJECT/04_Materials/PostProcess/Render2026). Originals stay untouched. No save_packages (the owner presses Ctrl+S). No BP_MelusinaJRPGCharacter, no PCG. Sheep MI and UI belong to other bots. The shard material and emissive belong to New Bot.

## Target architecture (hybrid)
- **Screen-space ink (ours, modernised):** a depth+normal edge (16-tap radial Sobel-style) with distance-scaled pixel width (RefDistance/depth, clamped Min/MaxWidthPx, whole-pixel). The hard reject is replaced by a **clamped** delta, so big silhouettes ink. A sky cut is added (depth > SkyDepth → no edge).
- **Per-class weights through CustomStencil:** 0 = world/props (StencilPropWeight), 1–3 = style colours, 4 = hero skip (hulls draw instead), 5 = character PP ink (StencilCharacterWeight), 6 = foliage override (StencilFoliageWeight). Foliage auto-detection via SubsurfaceColor stays.
- **Placement: BL_SceneColorBeforeDOF.** The pass runs pre-TSR at render resolution, so TSR anti-aliases and stabilises the lines. The ink no longer reads a jittered depth after TSR, and it composites under translucency and VFX. JitterCompensation = 0 (texel snap).
- **Surface side (MooaToon):** the MF_MooaEncode/Decode attribute MFs are the long-term home for a per-material outline width / ID (CustomData). **Deferred.** It needs master edits on M_Master_Toon_*, which is not tonight's job.
- **Hull outlines** stay the character line.

## Steps (priority order)
| # | Step | Owner | Time |
|---|---|---|---|
| 1 | Duplicate `M_PP_StorybookOutline_Frozen` → `M_PP_StorybookOutline_Render2026`. Patch the HLSL: clamped reject, sky cut, stencil class weights (new scalars StencilPropWeight 1, StencilCharacterWeight 1, StencilFoliageWeight 0.6, SkyDepth 500000). BlendableLocation BeforeDOF. Recompile | agent | 10 min |
| 2 | `MI_StorybookOutline_Render2026`: OutlineWidth 1.3, DepthRelativeThreshold 0.02, DepthWeight 1, NormalWeight 0.6, CreaseThreshold 0.55, EdgeStrength 1, Min/MaxWidthPx 1/2.5, RefDistance 1500, FalloffStart/End 8000/40000, FoliageDepth/NormalInk 0.6/0.15, FoliageFade 1500/8000, **HalftoneAmount 0**, DistanceFadeStrength 0.6 (10000→45000), JitterCompensation 0, InkBlurStrength 0.35 | agent | 3 min |
| 3 | `MI_MelodiaInk_Render2026` (dup of the Frozen MI): InkHalftone 0, InkStrength 0.35, InkHatch 0, grain kept at 0.1 → the dot screen is gone, the paper stays | agent | 2 min |
| 4 | `MI_MeluColorGrade_Render2026` (dup of the Frozen MI): ShadowLift −0.088→0.02, HighlightSoft 0.51→0.75 (rolls the shard whites), VignetteBaseIntensity 0.5→0.2, DreamHighlightSoft 0.24→0.45 | agent | 3 min |
| 5 | `MI_MeluColorGrade_Render2026_FallenMoon`: as step 4 plus ShadowLift 0.06, Contrast 0.72 (open the night up) | agent | 2 min |
| 6 | Fix the dangling FallenMoon/Kaleido refs **without map edits**: create new MIs at the missing paths (`.../Candidates/Profiles/MI_StorybookOutline_Premium_Hero`, `MI_Outline_PremiumV3_Hero`, `MI_StarryNight_Hero`, `.../Melodia/.../Candidates/Profiles/MI_MeluColorGrade_PortfolioHero`) as children of the Render2026 masters and MIs. They are new assets that are reversible by deletion | agent | 5 min |
| 7 | FallenMoon exposure: these PPV edits can't be kept without a map save while another level is open. The lift goes through the PPV (priority 10 beats UDS 1): AE Manual (`AEM_Manual`), bias +1.5 EV (tune ±0.5), or keep Histogram with min=max. Applied live only when FallenMoon is the open level | Brennan Ctrl+S (map) | 5 min |
| 8 | Morning PPV_NikkiDream: swap in Render2026 outline/ink/grade (Starry_Frozen kept). Vignette override 0.1. LocalExposure HighlightContrastScale 0.8 (shard blowout via grade) | agent → Brennan Ctrl+S (external actor) | 5 min |
| 9 | Recapture Morning MeadowChorus + WestRim and FallenMoon Portfolio_A with a `_render2026` suffix. Eye check | agent | 10 min |
| 10 | Kaleido/SeaAbove PPV swap to the explicit Render2026 names and re-enabling SeaAbove's PPV: map edits, next session (step 6 already gives Kaleido ink) | Brennan | 10 min |
| 11 | Later: stencil 5/6 assignment per class (character PP ink, foliage), a value-range guard in the lookdev audit, MooaToon CustomData outline ID | later | — |

Kill switch: in any PPV, swap the Render2026 entries back to the *_Frozen MIs. The Frozen assets are untouched.

## EXECUTION STATUS — 18:20 ET (editor crashed 18:13 ET; all editor work stopped)
**The crash was not one of this pass's calls.** The stack is `FMonolithMaterialActions::DeleteExpression` (Monolith delete_expression over HTTP). This pass never called delete_expression. Its only writes were duplicate_material, create_material_instance, set_instance_parameters, and one editor-python edit on the new Render2026 master. That edit was add-only: 5 ScalarParameter nodes, custom-node inputs appended, code replaced, BlendableLocation set. My call that was in flight at 18:13 (resetting SceneExposureEV to 0) got "connection refused", so it arrived after the crash. The log shows BP_MelusinaJRPGCharacter saved at 18:06:34 and 18:12:59, before the crash. None of those saves came from this agent.

On disk (all saved at 18:11–18:12 by someone else's Ctrl+S or save; never by this agent):
- Render2026/M_PP_StorybookOutline_Render2026 (BeforeDOF, 332 PS, compiled): clamped reject, sky cut, stencil class weights, SceneExposureEV
- Render2026/MI_StorybookOutline_Render2026 (plan step 2 values)
- Render2026/MI_StorybookOutline_Render2026_FallenMoon: **saved with SceneExposureEV = 3.0 from a test. Set it back to 0.** The pre-tonemap lift gets cancelled by auto exposure, so it is ineffective
- Render2026/MI_MelodiaInk_Render2026 (InkHalftone 0, InkStrength 0.35, InkHatch 0, InkDotLumaDrive 0)
- Render2026/MI_MeluColorGrade_Render2026 (ShadowLift 0.02, HighlightSoft 0.75, Vignette 0.2, DreamHighlightSoft 0.45), and _FallenMoon (ShadowLift 0.06, Contrast 0.72, Vignette 0.15)
- New assets at the previously missing paths: EnvSandbox/.../Candidates/Profiles/MI_StorybookOutline_Premium_Hero (→ Render2026_FallenMoon), MI_Outline_PremiumV3_Hero (→ Render2026), MI_StarryNight_Hero (→ StarryNight_Frozen), and Melodia/.../Candidates/Profiles/MI_MeluColorGrade_PortfolioHero (→ Grade_Render2026). FallenMoon and Kaleido now pick up Render2026 without map edits (verified live in FallenMoon before the crash)

Not done: the Morning PPV swap (step 8), the FallenMoon exposure edit on the PPV (step 7), and the Morning recaptures.
FallenMoon Portfolio_A was recaptured (Saved/Portfolio/Hero/L_FallenMoon/hero_FallenMoon_Portfolio_A_2026-09-30_render2026.png). The verdict: exposure is unchanged and still very dark, and no visible ink gain at this dark exposure. The fix has to be the PPV exposure edit (step 7).

Resume rules (from the parent): only after the relaunch, and only after New Bot has done the regalia re-parent and the owner has saved. No delete-node, no edits to original materials, small calls.

## EXECUTION STATUS, FINAL, 2026-09-30 19:20 ET (closeout)
Applied (small calls, no node deletes, no save_packages; every Ctrl+S by the owner):
- `MI_StorybookOutline_Render2026_FallenMoon`: SceneExposureEV 3.0 to 0 (18:45, saved 19:13:53).
- L_MelusinaMorning `PPV_NikkiDream`: blendables Render2026 outline 1.0 / StarryNight_Frozen 1.0 / Render2026 grade 0.69 / Render2026 ink 1.0; vignette override 0.1; local-exposure highlight contrast override 0.8 (18:45, saved 19:13:53, actor `6/2U/SXESN1EMPQO4ZW3Q2U4IED`).
- L_FallenMoon priority-10 `PPV_NikkiDream`: auto-exposure bias override +1.5 EV (method Histogram) (19:14, saved 19:14:46, actor `7/DL/RANDXO0WWWH6YVA16F9F10`). Visual not yet checked.
- Recaptures skipped (owner: final renders later).
Committed: **41c464a07** on main (19:16:58 ET, owner-approved ALLOW_MAIN_COMMIT, hooks passed, not pushed): the 10 Render2026/Candidates assets + the Morning PPV actor.
Not in git: the Fallen Moon PPV actor. `Content/__ExternalActors__/EnvSandbox/*` is gitignored (.gitignore:231), so it's saved on disk only. The same applies to any Sea Above/Kaleido PPV edits.
Also note: only 10 Render2026-related assets exist, not 11 (6 in Render2026/ + 4 at the Candidates paths).
Open: see GEM_LOOKDEV_PLAN.md and CLOSEOUT_2026-09-30.md.
Step status: 1-6 done + committed (41c464a07). 7 done (saved, gitignored, visual pending). 8 done + committed. 9 skipped (owner). 10 open (see GEM_LOOKDEV_PLAN L3/L4). 11 open (+ gem value guard G8).
