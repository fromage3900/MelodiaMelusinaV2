# M_Master_Toon_Universal — Professional Node Review

Reviewer stance: this shader is loved and stays in production (~105 parented
instances confirmed live). The goal is out-of-the-box usability: every family
accounted for, gated, clamped, grouped; dead weight removed; duplicated
machinery consolidated. Companion masters `M_Master_Nikki` /
`M_Master_Nikki_Landscape` (built 2026-07-02, `build_nikki_masters.py`) carry
the lean philosophy; this document governs the big master.

Source data: full node dump `Saved/Audit/universal_master_nodes.json`
(918 expressions), instance audit `Saved/Audit/universal_instance_overrides.json`
(105 instances scanned), and targeted live connection traces (2026-07-02/03).

Status legend: KEEP (core, untouched) · GATE (keep, add static switch)
· ABSORB (keep machinery, rebrand grouping) · CONSOLIDATE (merge onto MF)
· FIX (bug/design fix) · REMOVE (delete via traced bypass + native sweep).

## Verdict table (families)

| # | Family | ~Nodes | Verdict | Notes |
|---|--------|-------|---------|-------|
| 01 | Base Surface (tint/weight/UV/rough/metal) | 40 | KEEP | Core. RoughnessMap/MetallicMap wiring VERIFIED LIVE (TextureObjectParameter_88/89 → sample → lerp → StaticSwitch_48/49 → Multiply_861/862). The old "dead wiring" record was stale — corrected here. |
| 02 | Triplanar | 15 | KEEP | Feature; verify consumers during consolidation pass. |
| 03–05 | Layers A/B/C + samplers | 140 | KEEP | Core system, the material's whole point. |
| 06–07 | Layer blends A↔B, B↔C | 90 | KEEP | Core. |
| 05x | Core Parallax block | 35 | **KEEP (trace-corrected 2026-07-04)** | NOT a duplicate. Live trace: `ParallaxScale`(739)/`ParallaxStrength`(740)/`ParallaxHeight`(743) each feed 3 Multiplies (one per layer) and are multiplied *together* with `LayerA/B/C_ParallaxScale`(697/700/720): `Multiply_791 = (Subtract_140 × ParallaxScale_739) × LayerA_ParallaxScale_697`. The `05\|Parallax` group = **global master parallax controls**; per-layer params = per-layer trim. One integrated system. Removing the core block would break parallax on all layers. Prior CONSOLIDATE verdict was a node-dump guess, disproven. Good base to *expand* (stylized editable depth) per user's render-day steer. |
| — | Channels control | 20 | KEEP | Separate rough/metal switches — now confirmed functional. |
| — | PaletteRamp | 15 | CONSOLIDATE | One of FIVE ramp implementations; unify onto `MF_ColorRamp3` and add the advanced ColorRamp params (RampLow/Mid/High/PosMid/Contrast/Strength) matching M_Master_Nikki. |
| 08 | Rim & Glow | 50 | KEEP | Signature toon feature. |
| 09 | Sparkle | 45 | GATE (`bSparkle_Active`) | 20 instances use it → gate ON for those (list in audit JSON). |
| 10 | Iridescence & Sheen (+Dream) | 60 | KEEP + CONSOLIDATE sheen | Premium core. Fabric sheen here + hair sheen in Character family = two sheens; hair sheen is REMOVEd with Character, so this becomes the single sheen. |
| 11 | Gilding | 20 | GATE or CONSOLIDATE onto `MF_GildingOverlay` | Niche; curvature-driven. |
| 12 | Shadow Garden | 15 | CONSOLIDATE | Two shadow-tint systems; keep the one with instance evidence, remove the other (check audit). |
| 13 | Shadow Dream | 12 | CONSOLIDATE | See above. |
| 14 | Celestial/Nebula | 60 | GATE (`bCelestial_Active`) | Major feature, only 4 instances use it → big instruction win for the other 101. |
| 15 | Fairy Dust | 24 | GATE (`bFairyDust_Active`) | 6 users. |
| 16 | Henshin (magical transform) | 28 | GATE (`bHenshin_Active`) | 21 users (most-used optional family — gate still correct; ON where used). |
| 17 | Character (skin/hair/eyes/cheek, SkinWrap) | 52 | REMOVE | 13 params (814–822, vec 167–170), group `17 | Character`. ZERO instance users (audit-verified). Entry points traced: each sub-family funnels via Multiply_934/936/937/939/944 and Lerp_289→OneMinus_125; terminal injections to be traced hop-by-hop at execution (targeted calls only). |
| 18 | Elemental | 12 | GATE (fold under Henshin gate or own toggle) | Cosmetic. |
| 19 | Weather (moss/snow/wet) | 40 | GATE (`bWeather_Active`) | 12 users. |
| 20 | Cinematic (distance fade/contact rim/dither) | 36 | KEEP | Used widely (DistanceFade overrides common). |
| 21 | TimeOfDay | 12 | KEEP | MPC/UDS hook. |
| 22 | Macro & Detail | 12 | FIX | **Root cause of "scales oddly" found:** macro pattern is UV-driven (`TextureCoordinate_22 × MacroScale(807) → Multiply_923 → noise`), so pattern scale depends on each mesh's UV density. Fix: drive from `WorldPosition.xy / MacroWorldScale` (world-consistent breakup). Instances overriding MacroScale (e.g. MI_IridescentRock at 160) need a re-look after the fix. |
| — | Madoka (~40) | 40 | ABSORB → group `VeinGlow` | User decision 2026-07-03: used by 4 live instances as generic vein-glow (Zen_Karesansui, Zen_MoonlitGarden, Show_MadokaBarrier, Showcase2_MadokaPulse). Params keep names (renames would break overrides); regroup + clamp sliders. |
| — | Itto (~32) | 32 | ABSORB → group `InkWear` | Used by 5 instances as generic crack/ink/wear (Universal_CrackedClay, Escher_Woodcut, Show_IttoCarved, Showcase2_IttoSpiral + ramps). Same treatment. |
| — | Temporal/Ink boil | 20 | KEEP (review sliders) | Niche but cheap; clamp. |
| — | Scaffolding/orphans | ~150/~118 | REMOVE (orphans only) | `MEL.delete_unused_expressions` native sweep after Character removal; clears legacy triplanar/LayerC leftovers too. |

## Instance-impact evidence (Stage 0, 2026-07-03)

- 105 instances parented to the master were scanned.
- Character/SkinWrap: **0 users** → clean removal.
- Itto/Madoka: **9 users** (see table above) → absorbed, not removed (user call).
- Gate flips needed when switches land: Sparkle 20, Henshin 21, Weather 12,
  FairyDust 6, Celestial 4 (exact lists in `universal_instance_overrides.json`).

## Traced splice points (for the execution stages)

- BaseColor tail: `Lerp_308 → Lerp_309 (Madoka, α=843) → Lerp_310 (Itto, α=850)
  → {MaterialFunctionCall_0.'BaseColorIn (V3)', StaticSwitchParameter_0.'False'}`
  — stays (absorb), but this is also where the new ColorRamp inserts.
- Roughness: `Add_309(A=Lerp_301, B=MF_Itto.RoughnessAdd) → SubstrateToonBSDF_4.Roughness` — stays.
- Madoka emissive: `MF_Madoka.Emissive → Multiply_973(×843) → Add_308.B` — stays.
- Macro: `TextureCoordinate_22 × ScalarParameter_807(MacroScale) → Multiply_923`;
  strength via `Subtract_163 × ScalarParameter_806 → Add_297.B`.
- Character entries: SkinWrap `Lerp_289(α=814) → OneMinus_125 → …`;
  Cheek `Multiply_937`; Eye `Multiply_939`; HairSheen `Multiply_944`
  (terminal injections traced at execution).

## Safety rules for all execution on this asset

1. Never bulk-loop `get_inputs_for_material_expression` (crashed the editor
   twice on 2026-07-02). Enumeration + targeted `get_expression_connections` only.
2. Never `delete_asset` anything potentially open in the user's editor.
3. `save_asset(..., only_if_is_dirty=False)`; per-stage git commits.
4. Backup: `_Scratch/M_Master_Toon_Universal_BACKUP_20260702`; git `9155e9b`.

## Execution status

- [x] Stage 0 audit (script `Content/Python/audit_universal_instance_overrides.py`)
- [x] Stage 1 review (this document; per-family verdicts above)
- [x] Stage 2 additive (commits `0a33642`, `6d57e37`, `377b20d`, `a6a325c`):
      142 scalars clamped; InkWear/VeinGlow regroup; ColorRamp inserted;
      gates live for Celestial/Sparkle/FairyDust/Weather/Elemental (default
      OFF; 42 audited user instances flipped ON + saved). **Henshin gate
      deliberately skipped**: `MagicalTransform` fans to 5 consumers incl.
      Subtracts — gating risks the zero-state math for marginal savings.
- [x] Stage 3 removal: Character family bypassed
      (`Lerp_288→Lerp_297.A`, `Multiply_954→Add_313.B`) + native sweep.
      918 → 844 exprs; 13 character params gone.
- [x] Stage 4 (partial): **Macro world-space fix applied** — was
      `TexCoord × MacroScale` (default 0.0008, UV-dependent); now
      `WorldPosition.xy × MacroScale × 1e-5` (100 ≈ 10 m period). 24
      instances' legacy overrides migrated (×125000, clamped 1–512; 3
      garbage negatives reset to 100). Zen instances clamped at 512 were
      UV-dense — **eye-check recommended**: BambooWood, MossStone,
      RiverStone, TempleStep.
- [ ] Stage 4 remaining: ramps → MF_ColorRamp3; single sheen; one
      shadow-tint system; core-parallax resolution
- [ ] Stage 5 Melodia conversions: fix M_SDF_ParallaxPulse, then
      M_Substrate_VinylGroove / _Facade_Baroque / _CelestialStarMap
- [ ] Stage 6 wrap: CURRENT_STATE.md, before/after table

Instruction budget so far: PS 1128 → 946 (default path), expressions
918 → 851 (gates add a few nodes back on top of the 844 post-removal floor).
