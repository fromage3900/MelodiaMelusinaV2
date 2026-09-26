# UPDATED PLAN — Handpaint Prep Phase 2 (2026-09-23, evening)

Lens: **cymatic × Infinity Nikki** — vibration-pattern geometry (Chladni/cymatic rings,
FrozenFracture language) rendered with polished dress-up-game softness: pearl/soft-gold
metal, sakura-pink and moonlit-blue accents, scalloped edges, heart/clef filigree.
Authority refs: `deploy/surreal_arch/melodia_gn/infinity_nikki_kit.py`,
`nikki_musical_decorations.py`, `chladni_layers.py`, `DA_MelodiaDesignTokens`,
`MI_Sakura_Lantern`, `MI_Zen_*` set, and the cymatic `T_Cymatic_FrozenFracture_*` map family.

## New sources (owner-supplied, copied from Downloads — originals untouched)

| Asset | File | Content | Verdict |
|---|---|---|---|
| TreasureChest | `06_TreasureChest/source/treasurechest.obj` (340 MB) | ZBrush raw: 2.389 M v / 2.403 M f, normals yes, **UV no**, one group | HI sculpt → needs fixed-topology paint mesh + UV |
| FallenMoon | `07_FallenMoon/source/fallenmoon.obj` (211 MB) | ZBrush raw: 3.069 M v / 3.069 M f, **no normals, no UV** | HI sculpt → decimate + recalc normals + UV |
| CosmicReaver base | `08_CosmicReaver_USDZ/source/cosmicdaddyfinal.usdc` (1.2 MB) | single low-poly base mesh, no textures | import → census → UV/fix as needed; candidate replacement/complement for `reaver_LOW` |
| MelodiaMelusinaFlowers | `09_MelodiaMelusinaFlowers/source/melodiamelusinaflowers.usdc` (37 MB) | single mesh set | import → census → UV/fix |

## Pipeline (per asset)

1. **Import & census** (headless Blender 5.2, `import_obj.py` / `import_usd.py`) → raw `<Asset>_raw.blend` + census JSON.
2. **Fixed topology** (`retopo_prep.py`):
   - ZBrush raws: decimate COLLAPSE to a paint budget (chest ~120 k, moon ~200 k env piece),
     then **voxel-dominant cleanup**: planar decimate pass where beneficial; recalc normals
     (moon lacks them); weld loose verts. Goal: even triangle distribution, no pinching,
     silhouette preserved ±0.5 %.
   - USDZ bases: keep topology; only fix non-manifold/pole issues if census flags them.
3. **UV** (`Smart UV Project`, island margin 0.02, angle 66°) on the paint mesh; verify
   island count + zero-area islands in report. UDIM not needed at these budgets.
4. **Copernicus cymatic bakes** — staged, not cooked here:
   - Shared source set: `Saved/Audit/copernicus_cymatic/FrozenFracture/*.png` (9 maps:
     BaseColor/Emissive/Height/Iridescence/Metallic/Normal/ORM/Opacity/Roughness)
     → copied to `Bakes_Cymatic/FrozenFracture/`.
   - Per-asset `bake_recipe.json`: which cymatic channels layer onto which material
     zone under the lens (e.g. chest lid = FrozenFracture Normal @ 15 % over painted
     wood; moon face = full cymatic Height→Normal as the "sea of vibration" relief;
     reaver blade = Iridescence ramp pearlescent).
   - Houdini Copernicus cook lane exists (`Tools/Houdini/overnight_orchestrator.py`);
     recipes are written so the cook is one JSON read away.
5. **Substance handpaint scaffolding** — per asset folder:
   `substance/<Asset>/meshes/<Asset>_high.fbx` + `<Asset>_low.fbx` (suffix pair matches
   Substance "by mesh name" baking), `textures/` (cymatic reference maps linked),
   `paint_guide.md` (lens-specific palette + motif placement). Painter project itself
   is created by owner on import (`.spp` is binary; not authorable here).
6. **Report** per asset: `*_prep_report.json` (polys, UV islands, dims, warnings).

## Asset-specific notes under the lens

- **TreasureChest**: cymatic concentric rings on the lid face; Nikki heart-filigree lock
  plate; bands in soft gold; body in warm cedar (cf. `MI_Zen_TeaHouseCedar`). Paint mesh
  target ~120 k, HI 2.4 M for normal/AO bake.
- **FallenMoon**: the big flat lunar face takes the cymatic FrozenFracture height field
  as its maria — vibration made geography. Cool pearl base, sakura rim where it "fell".
  Env piece: ~200 k paint mesh.
- **CosmicReaver**: USDZ base is the wearable low; keep consistent with the staged
  `CosmicReaver_HandpaintPrep.blend` (CAGE 82 k + ornaments). Cymatic iridescence on
  the blade edge, pearl inlay along the spine.
- **MelodiaMelusinaFlowers**: scatter set — petals get the cymatic ripple in the vein
  pattern; Nikki pastel gradient (sakura→lavender), pearl dewdrops.

## Sequencing (rest of tonight)

1. Chest import (heaviest OBJ) → topology/UV → done first while RAM is free.
2. FallenMoon import → topology/UV.
3. USDZ pair import → census → UV fix if needed.
4. Cymatic bake staging + Substance FBX exports + paint guides.
5. Update MANIFEST, final report.

Watch: RAM stays tight with UE open; one Blender job at a time, zombies reaped between runs.


---

# PHASE 5 — LONG-TERM ROADMAP: hard-surface detail, vertex paint, audio-reactive GN variants

Lens unchanged: cymatic × Infinity Nikki. Tonight's handpaint is NOT blocked — everything below is additive (_V2 meshes, new attributes, new GN assets). Evidence anchors: `Docs/Research/EMERGING_TOOLCHAIN_MASTER_INDEX_2026-08-31.md` §1/§5b-i/§7, `Saved/Audit/copernicus_cymatic/` (21 families × 9 channels, 1665 PNGs, audit-passed), Higgsas v13 catalog, Melodia Studio registered builders, repo one-writer rules.

## A. Hard-surface detail pass (per asset, smallest correct tool)

| Asset | Detail plan | Tool | Budget |
|---|---|---|---|
| ZenLantern (priority 1) | Panel seams on fire box, rib rings on umbrella roof, band trim, base molding stack | Bevel tiers (already in) + bool panel lines + weighted normal | <15k f total |
| StylizedCrossProp | Facet insets on star arms, trim ring on base, rune plate | Bool insets; relief reference: `paris_wall_detail` builder style | <8k f |
| SM_MelodyToken | Rim notches + engraved ring | **Constraint: cylinder silhouette must not change** — owner's existing Substance cylinder bakes must still apply. Detail inside silhouette only, normal-map friendly | <2.5k f |
| TreasureChest | Bands, corner caps, lock plate | NO bools on the 225k organic mesh — GN-generated trim conforming to bbox (Higgsas Geometry Measure + Curve) as separate pieces | trim <20k f |
| CosmicReaver | Ornament edging only | Cage/LOW counts are frozen (shape keys) — detail goes on `_LO` copies + separate trim pieces | trim <30k f |
| FallenMoon / Slime / Flowers / ReaverBase | No hard-surface pass (organic); decoration via Pillar C/D instead | — | — |

## B. Vertex paint convention (all 9 assets, one standard)

Attribute `vcol_melodia`, 4 channels, authored in Blender vertex-paint mode on the LOW/paint meshes:
- **R — wear mask** (edge/cavity wear; bake AO/cavity to vcol first, hand-tune)
- **G — decoration density** (where GN decorations may scatter: lantern eaves, cross arms, chest bands, moon rim)
- **B — audio-reactivity weight** (per-vertex 0..1 → UE vertex color → drives pulse amplitude + GN/Niagara response strength)
- **A — emissive zones** (Nikki sparkle points: lantern fire box, token rim, cross crystal, slime core)

Export: FBX vertex colors ON (verify flag — tonight's exports did not carry vcol; add check to `export_fbx.py`). UE: vertex color node → material params; sRGB off. Pilots: lantern, cross, token (Phase 5a).

## C. Addon usage map (use installed addons wisely = smallest correct tool)

- **Higgsas v13** (catalog-verified): Distribution + Falloffs → decoration scatter on G mask; Deformers → slime wobble / moon breathe (weight = B); Instance → charm/chain duplication; Geometry Measure → bbox-conforming chest trim; Curve → band paths.
- **Melodia Studio builders** (already registered): `MEL_skirt_hem_charm` + `MEL_skirt_hem_dangl_row` → lantern eave charm rows (direct fit); `MEL_garm_ribbon_trail` → chest/lantern ribbons; `GN_PARIS_DayNightFacade` pattern → lantern day/night material swap; wing builders stay garment-lane — reference only for prop motifs (no fifth track).
- **Roof Generator v3.1** (21 roof types) → pagoda roof variant tiers for lantern variants.
- **Surreal Architecture kit** (Gothic/Romanesque) → plinth/pedestal variants for cross + reaver base display.
- **Copernicus/Houdini** → staged trim-piece bakes; the 21 cymatic families ARE the authored procedural decoration texture set.
- **Hard rule (AGENTS.md):** `UMelodiaAudioReactivePresentationSubsystem` is the SOLE audio writer (MPC_Melodia_Palette). Blender GN audio response is AUTHORING-TIME ONLY — bake variant states, never a runtime audio path from Blender.

## D. Audio-reactive procedural variant system (long term)

Runtime contract (already live-proven): materials/Niagara/PCG read `MPC_Melodia_Palette` (BeatPulse/BeatPhase/BeatIntensity/BassIntensity) + World Field Bus (Tension/Pressure from the read-only cymatic Chladni consumer). Props never write audio.

Variant matrix — 21 authored cymatic families × 9 assets, 2–3 decoration GN setups each:
- Lantern: `CharmRow` (eave charms) · `RoofRib` (roof tiers) · `FlameCore` (A-channel emissive + CymaticMarble)
- Cross: `CrystalBloom` (DancingCrystals) · `RunePlate` (ChoirStone relief)
- Token: `RimSparkle` (FrostBloom, respects cylinder constraint)
- Chest: `GildedBand` (GildedCoral) · `RibbonTrail`
- Moon: `ChoirInlay` · `FractalCathedral` craters
- Slime: `Wobble` (Higgsas deformers, B-weighted) · `FrostBloom` core
- Flowers: `CymaticOrchid` veins (family name already matches)
- Reaver(+Base): `CrystalCathedral` edging, morph-driven by beat phase (shape keys = built-in variant driver)

UE wiring: vcol B → pulse amplitude param; vcol G → PCG/decoration density; vcol A → emissive mask; cymatic maps as material layers under handpaint. Deterministic at frame rate — audio only modulates authored sets (repo quantum/audio rule).

## E. Phasing

- **5a (2 sessions):** vcol convention on 3 pilots + export flag + UE import verify (vertex colors arrive on SM).
- **5b:** decoration GN pilots — lantern charm row + roof ribs, chest bands; bake static variants; contact-sheet evidence.
- **5c:** variant matrix expansion; `MI_Handpaint_*` extended with cymatic layers; lookdev in L_FallenMoon / L_KaleidoNave.
- **5d:** audio-reactive tuning vs MPC palette in PIE; Echo-ledger evidence rows (probe JSON + audit under `Saved/Audit/`, ledger row per gate — no prose-only claims).

Every phase closes with the same audit pattern as Phases 1–4: per-asset reports in the staging folder, durable copy under `Saved/Audit/`, contact-sheet proof.
