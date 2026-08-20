# Visual polish plan — Infinity Nikki lens, 2026-08-03

For Kiro (editor work) and JetBrains Rider (Python/asset plumbing). Read this before touching any
PPV, outline, sky, or master-material asset. Everything below was re-verified from the scripts on
disk today, not from memory.

## Where things stand (ground truth, verified)

- **WP conversion is DONE** (owner-confirmed). `L_FallenMoon` + `L_KaleidoNave` are World Partition;
  `.ini` files generated. Do **not** re-run `WorldPartitionConvertCommandlet`.
- 4 gameplay levels carry one identical PPV stack (priority 10, unbound):
  `MI_Outline_PremiumV3_Hero` w=1.0 · `MI_MeluColorGrade_PortfolioHero` w=1.0 · `MI_StarryNight_Hero` w=1.0
  (verified by PRE_REBUILD_HEALTH_PASS_2026-08-02).
- Second unbound volume per level (`MoonPost` etc.) at priority 0 with real overrides
  (`MoonPost` = 26 overrides) — **leave alone**, it is the baseline grade.
- `L_FallenMoon` outline was raised 0.08 → 1.0 during health pass; keep unless owner says it was deliberate.
- Duplicate levels exist: `/Game/L_InfiniteScore` vs `/Game/EnvSandbox/Environments/L_InfiniteScore`,
  `/Game/L_MelusinaMorning` vs `/Game/Melodia/Levels/Opening/L_MelusinaMorning`. Confirm which the
  GameMode/DefaultMap loads before touching maps.

## THE central design fact (reads this carefully)

**Colour grading lives in the universal master's "Nikki" parameter group, NOT in the PPV.**
`setup_nikki_render_post_process.py` (2026-08-01) removed all colour-grade overrides from the volume
because they doubled `M_Master_Toon_Universal`'s Nikki group and darkened the render levels. The
volume now carries only lens character: bloom 1.0 / vignette 0 / grain 0 / CA 0.

Nikki group (all default 0 = neutral, `setup_master_universal.py`):
`RimIntensity, PastelLift, DreamSaturation, DreamContrast, DreamShadowLift, DreamHighlightSoft`,
`DreamHueShift, SparkleIntensity, GlowIntensity, Iridescence, FabricSheen, Celestial*`.
Pick `DreamSaturation/DreamContrast/PastelLift` to make scenes "triple AAA dreamy" — on an
instance (`MI_*`), never on the master unless you rebuild parameters.

Known MASTER rebuild footgun: `setup_master_universal.py` carves the graph on `--force`; without
`--force` it skips (idempotent). Sky is `M_PP_StarryNightOverlay_Candidate` + its profiles.

## MPC authority — RECONCILE, do not delete

- **`MPC_MelodiaPalette`** (`/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette`) is the live
  palette: sky reads `PalDeep=R1999_Navy, PalLight=R1999_Gold, PalStar=Melusina_SoftWhite,
  PalNebula=Melusina_Lavender` (`apply_starrynight_v7.py` PAL_PINS), and grade V2 split-tone anchors
  on its `PrimaryColor` (`PPV_DEEP_STUDY_V4`). It is **canonical for sky/grade.**
- **`MPC_Portfolio_Palette`** (`setup_portfolio_mpc.py`) is the doc-claimed "scene cohesion" source
  (BaseTintShift/ShadowDreamBias/TimeOfDayWarmth…). **After the recent master rebuild it is NOT
  wired into the master anymore** — no `CollectionParameter` to it in `setup_master_universal.py`
  (only `UseUDSTimeOfDay` + Day_to_Night_Color via UDS MPC). Docs still claim it powers
  ShadowDreamBias. This is stale truth: it currently does nothing. Either wire it back
  (ShadowDreamBias > ShadowDreamStrength on instances) or delete the doc claim. **Don't silently
  delete the collection while scripts reference it.**
- UDS MPC (`UltraDynamicWeather_Parameters`) drives time-of-day tint via Day_to_Night_Color when the
  instance static switch `UseUDSTimeOfDay` is ON. Default OFF.
- **2-MPC budget is the engine ceiling on the sky** (UDS + MelodiaPalette already both used) — NO
  third collection on `M_PP_StarryNight...`. Master has budget left (only UDS wired), so grading-on-
  the-master can still add a palette MPC if you want live grade.

## The 3 fixes — all already in code, not yet visually confirmed

From `PPV_DEEP_STUDY_V4_2026-08-02` Drives (all verified by compile, not by eye):

1. **Outline jitter** — three root causes (MinWidthPx 0.6→floor 1.0px; AA band floor
   `rcp(max(w));
  2px,1.0)`); `max()` over 8 taps = noise amplifier; mitigated by tuning `InkBlurStrength 0.28→0.45`
   on the Hero profile). **Verify before capturing** on the Penrose lattice in `L_FallenMoon`
   (780 thin beams) with a slow orbit tilt; compare TLK vs JJ. Return `InkBlurStrength .40–.50`
   if shimmer remains; tune split-tone `SplitAmt 0.30` down if too warm.
2. **Grade V2** — 7-step chain in `M_PP_MeluColorGrade` order: Expose→Tone→Vibrance→SplitTone→Paper
   →Rhythm(MPC)→Vignette. Consts not parameters (reason: `update_custom_hlsl_node` blanks inputs).
   **Rider task:** promote the ~6 consts to real parameters (full 16-input array + rewiring), values
   unchanged to avoid drift. Author `MI_MeluColorGrade_*` profile variants.
3. **Starry night sky → Vine Gogh V7** — discrete dab lattice in `M_PP_StarryNightOverlay_Candidate`;
   stroke rows quantized with per-cell length/thickness/hue, canvas gaps via StrokeGap. Uses
   `UseUDSTimeOfDay=0, ManualNightAmount=1` when hand-slaved.

   **MUST-FIX before any capture:** the sky uses `UseUDSTimeOfDay=0` (manual). If UDS time is ~16:00
   the night gate (NightAmount) sits at 0 and the sky is invisible. Set `UseUDSTimeOfDay=1` + UDS time
   ≈23:00 for the night shots.

## Rule list — triple-AAA rules that are non-negotiable

- Always **duplicate before editing** template/LL assets (master, PP materials, UDS). Working
  agreement: no new compensation flags; a fix never needs a new knob to cancel behaviour; it must
  delete the cause.
- Never add a third CollectionParameter → supermaterial sky/grade materials (hard ceiling 2).
- Don't edit the live master without an idempotent script; prefer instances.
- Save only the target maps (WorldPartition + root map), never portfolio/Melodia maps wholesale.
- Use the `Saved/Audit/*.json` reports (nikki_post_process, universal_build_last) as ground truth
  after each script run.
- `r.Substrate=True`, `r.CustomDepth=3`, `r.MotionBlur=False` are the standing render settings.

## Suggested order (one pass, then verify, then capture)

1. In editor pile the sky time-of-day gates consistent (~23:00, UseUDSTimeOfDay=1) on 4 levels.
2. Rebuild master only if needed (`--force`), else leave; tune `DreamSaturation ~ +0.15 / DreamContrast
   ~ +0.1 / PastelLift ~ +0.08` on the four hero MI profiles for the AAA dreamy lift. Make a
   before/after on each level.
3. Verify outline on the Penrose lattice; adjust InkBlur & SplitAmt if needed.
4. (Deferred) promote Grade consts → parameters and build profile instances.
5. Capture/render the archive set.

## Files of record — pointing pointers

- `Content/Python/setup_universe.py`, `apply_starrynight_v7.py`, `setup_master_universal.py`,
  `setup_nikki_render_post_process.py`, `setup_portfolio_mpc.py`, `setup_time_of_day_mpc.py`
- `Content/Python/material_lib.py` (collection helpers, MPC_DIR)
- Docs: `Handoffs/PPV_DEEP_STUDY_V4_2026-08-02.md`, `PRE_REBUILD_HEALTH_PASS_2026-08-02.md`,
  `CLAUDE_TO_KIRO_STATE_2026-08-01.md`, `PREMIUM_OUTLINE_STACK_2026-08-01.md`
- MPCs: `MPC_MelodiaPalette` (canonical), `MPC_Portfolio_Palette` (unused right now),
  `MPC_Portfolio_Audio` (audio-reactivity only), UDS MPC (time-of-day).

Open questions for the owner when you are with them:
1. Fix the duplicate-level paths (Root vs EnvSandbox / Melodia) — which is loaded?
2. The MPC_Portfolio_Palette claim: wire it or drop the doc line.
3. Keep `MI_Outline_PremiumV3_Hero w=1.0` or restore ~0.5 for a subtle 3D line?
