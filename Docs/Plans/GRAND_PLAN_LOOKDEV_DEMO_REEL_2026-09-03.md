# Melusina & Sea Above — Lookdev + Demo Reel Grand Plan (2026-09-03)

## Demo-reel audit (what exists, rated)

**Melusina EEVEE character renders** (`._site_aside_untracked/`, 6 shots):
- Beauty full-body (20260715_01): **7/10** — strong hair/fabric/lighting, but floating
  (no contact shadow), basic skybox, UI orbs break immersion. FIX: contact shadow
  plane + environment lighting = +1.5 pts.
- Glam close-up (20260715_05): **8.5/10** — strong eyes/hair/color, but grainy skin
  texture + minimal background. FIX: denoise skin + subtle environment = +1 pt.

**Character assets**: 281 images in `_github_deploy/generated/assets/character/`

**Sea Above level**: dressed (136 reef/abyss/jelly + PCG ribbon/garden), but no
lighting, post, or cinematic camera yet. Currently reads as greybox with good
placement — needs lookdev + PPV to become reel footage.

**Melusina House Phase 3**: GN furniture, Nanite assembly, acoustic architecture,
material shader genome (2026-09-03 docs) — the interior portfolio hero shots.

## TONIGHT'S EXECUTION ORDER

### 1. P0 SHIPPER (verify the earlier cook)
- Your earlier cook is the real target. Verify it produced an executable at
  `Products/P0_Itch_Release/`. If yes → record `package_build` pass.
- Cook command (for reference): RunUAT BuildCookRun, maps=`LV_SeaAbove_Prototype+
  L_MelusinaMorning+L_KaleidoNave+MelodiaIntegrationMap`, Shipping, Win64.

### 2. SEA ABOVE LOOKDEV PASS (level becomes reel footage)
- a. PPV stack: one unbounded `PPV_NikkiDream` with
  MI_StorybookOutline_GameplayStandard (1.0) + MI_MeluColorGrade_GameplayStandard
  (1.0) + optional StarryNight (0.3). Spec: `Saved/Audit/sea_above_ppv_spec.json`.
- b. Lighting: twilight key (upper-left warm pink, matching Melusina's palette),
  cool blue rim, depth fog tuned to the drowned-cathedral tiers at -15k/-45k.
- c. Golden spiral camera path: PlayerStart(0,0,13175) → Quill(-910,500,13145) →
  MusicKey(0,-950) → Dock(-5099,5821,6270), pulling back through the silhouette
  ring at golden radii (5k, 8k, 13k, 21k, 34k, 55k).
- d. Capture: Movie Pipeline (not screenshot) at 4K, anti-aliased, 24fps for
  demo-reel output.

### 3. MELUSINA EEVEE UPGRADES (6 existing renders → reel-ready)
- Beauty: add ground contact shadow (matching the sea-surface reflection),
  replace skybox with the twilight environment, remove UI orbs. Target 8.5/10.
- Glam: denoise skin (keep the hexagonal hair pattern), add a subtle environment
  reflection in the rim light. Target 9/10.
- Output: `Products/Portfolio/Melusina_2026-09-03/` — hero + contact sheet.

### 4. PORTFOLIO ASSEMBLY (portfolio_schema.json pipeline)
- Run `deploy/portfolio_render.ps1` (headless UnrealEditor-Cmd) for UE shots.
- Integrate the Melusina House Phase 3 hero shots (Nanite furniture, acoustic
  rooms) as the interior portfolio layer.
- Aggregate into portfolio schema: scene/assets/materials/render/pcgs/stats.

## Authority & constraints
- No new material masters (AAA tier: Toon_Universal, Oceanology water, SDF
  cathedral, lookdev post profiles).
- Single writer: one editor :9316, one apply session.
- Height-aware placement (CanonicalLandscape only).
- Evidence: each shot = Movie Pipeline output + gate ledger row.

## Deliverables (tonight)
1. ✅ P0 package verified OR cook re-run
2. Sea Above lookdeved level with PPV + cinematic camera path
3. 6 upgraded Melusina EEVEE renders (reel-ready)
4. Portfolio schema populated (interior + exterior hero shots)

## Next actions (immediate)
1. Verify your earlier cook produced an executable.
2. Restart editor; load LV_SeaAbove_Prototype.
3. Apply PPV stack → set up twilight lighting → block the golden spiral camera.
4. In parallel: upgrade the 6 EEVEE renders.