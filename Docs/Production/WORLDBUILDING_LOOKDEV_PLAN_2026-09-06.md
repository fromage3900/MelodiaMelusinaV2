# Worldbuilding, Material Fixes & Nikki Treatment Plan — 2026-09-06

Companion to `GIT_STATE_STUDY_2026-09-05.md` (§5a). Everything here is grounded in a
read-only census run today on unified main (binary string-scan of .uasset imports —
confirms presence, never absence, per rule 20).

## 0. Editor-writer contention (read first)

P0 golden run (owner) > this campaign. Every editor-touching batch below is gated on:
(1) golden run done, (2) the other lane's unsaved edits committed/discarded,
(3) exactly one editor, no concurrent Monolith writer. Offline work (this doc, specs,
Blender/hython prep, PNG→atlas tooling) proceeds freely.

---

## 1. Worldbuilding — the reusable chapter chassis

The product spec (`_VERTICAL_SLICE_SCOPE.md` §2) already defines the Universal Reusable
Chapter Loop. What worldbuilding needs is a **chapter bible template** so each new
chapter is authored, not invented. One folder per chapter:

```
Chapters/<NN>_<name>/
  CHAPTER.md          logline, emotional movement, Melusina's feeling-arc
  route.md            maps + travel edges (allowlist delta previewed, not live-edited)
  quill/              .qsc scripts (7-verb notifications only)
  encounters.json     allowlist IDs (quests, flags, rewards, stats)
  assets.md           outfit set, instrument, VFX kit, flipbook/texture pulls
  score.md            theme, BPM band, beatmap source (quantum may rank, never grade)
  lookdev.md          PPV recipe + Nikki tiers per surface (see §4)
```

Existing world inventory and their chapter status:

| World | State | Chapter readiness |
|---|---|---|
| First Dream (Morning→KaleidoNave) | P0 loop, all gates pass | DONE — it is the reference chapter |
| Shorewake / Sea Above | dressed map gate pass; dress/cymatics pipeline live | Chapter 2 candidate — boat lane owns route |
| Melusina's House | builder roadmap pinned on Line B; REF sheets in Docs/References | interior/wardrobe chapter |
| Faraway Mother | fabric-mountain systems (P2), Gown flipbooks exist | skyline-as-character chapter |
| Dreamstate | merged into route leg (retired as separate map) | memory-flashback garnish, not a chapter |
| Sol's Gaea landscape | unified main, height-blend bound | shared terrain authority for all chapters |

Authoring rule that keeps P0-learned authorities safe: a chapter may add **data**
(qsc, DA rows, PPV, meshes, outfits, songs) but never a new subsystem. If a chapter
seems to need code, that's a defect signal — the six exit criteria of the golden run
("no new system is required to explain a route failure") apply to worldbuilding too.

## 2. Material fixes ledger (from the 09-05 convergence, still open)

The convergence deleted broken masters/orphans and repaired 89 instances, but three
fix-classes from the safe-material skill remain uncensed in the field:

1. **Dead parameter overrides** — instances that reparented onto
   `M_Master_Toon_Universal` keep overrides whose names no longer exist on the new
   parent (marble-bug class #1). Offline census possible: parse each MI's override
   names vs parent's parameter table via Monolith `get_cdo_properties`-style reads
   when editor is free. Budget: one batch, 50–100 MIs/subagent, recompile+save per batch.
2. **The 4 `NikkiChain` variants** (`M_Master_Toon_Universal_NikkiChain`, `..._V1`,
   `..._Repair`, `..._RepairV2`) — four parallel chain-masters is exactly the
   parallel-authority defect AGENTS warns about. Decide ONE owner (recommend RepairV2,
   newest), reparent consumers, delete the rest. Editor batch + verify_baseline re-freeze.
3. **Retired-master consumers** — M_Master_Nikki and M_Master_Toon_Cosmic are gone from
   the catalog, but redirector/orphan sweep across the 1,089-MI estate hasn't been
   re-run since unify. `Tools/bp_sweep.py` + `bp_live_path.py` scoped to Materials, offline.

Each fix ends the same way: editor re-freeze of the T3D baseline (one command) so
verify_baseline stays the tripwire.

## 3. Melusina flipbook animation materials — census truth first

What exists today (binary-scanned, not assumed):

| Asset family | Reality | Consequence |
|---|---|---|
| `A_FB_Melusina_A_Src_*` (16) | **AnimSequences** (FemaleBardRetargeted skeletal), NOT flipbooks | the "FB" is a naming trap; 3D anim, no material work |
| `T_PearlFlipbook_FrameNN_{BaseColor,Normal,Roughness,Height,Iridescence}` | per-frame PBR texture sets (PearlWoven_Flipbook/) | **no UE Flipbook objects exist in git (0 found)** — nothing scrubs frames yet |
| SurrealFabric_Flipbooks/{BrassPatina,CelestialSilk,CymaticPulse} | per-frame PNG sets, 461 imported 09-05 as flat Texture2Ds | same: imported as stills, playback unwired |
| `T_Brass_Flipbook_30_Atlas_4x4` | a REAL 4×4 atlas, one texture | ready for atlas-scrub today |
| `Content/Alphas_Sparkles/T_Alpha_{sparkle_pulse,fluid_metaball}_flipbook.png` | classic VFX flipbook atlases | for Niagara materials (§4), not cloth |
| `GC_MelusinaHairFlip_v22` (Cinematics) | hair-flip cinematic asset | separate track; include in lookdev only |

**The missing piece is one Material Function + one master, then instances:**

- `MF_FlipbookScrub` (new, additive-only authoring): Vertical Texture Object Parameter
  input (the frame array via `TextureObjectParam` + index math, or atlas UV-chop for
  4×4 sheets), inputs: FrameIndex / Rate / StartFrame / Loop, outputs: frame-UVs +
  valid-mask. HLSL custom node route only (`create_custom_hlsl_node`); NEVER
  `build_material_graph` on anything that exists (it wipes graphs).
- `M_Melusina_FlipbookCloth` = M_Master_Toon_Universal_NikkiChain winner (§2.2) +
  MF_FlipbookScrub driving BaseColor/Normal/Roughness/Height/Iridescence (full PBR
  flip — PearlWoven has all five channels per frame; that's rare and worth exploiting).
  Time source: a `FrameRate` scalar + engine Time, battle-sync option via
  MPC_Melodia_Palette beat lane (single-writer rule intact: read only).
- Instances: `MI_Melusina_DawnChorus_Flip`, `MI_Melusina_Shorewake_Flip`, one per
  SurrealFabric family. Catalog them into DA_MelodiaCosmeticCatalog the normal way.

Sticker/2D pass: Melusina's sticker aesthetic (Infinity-Nikki language) is already in
the chain — `MF_NikkiStickerEdge` + `MF_NikkiStickerShade` exist. The flipbook cloth
master wires both so animated fabric reads as inked paper at silhouette edges. That's
the "flipbook animation material + Nikki treatment" in one graph.

## 4. Niagara VFX materials — the Nikki treatment campaign

Census result: **30 VFX materials under `EnvSandbox/VFX/Materials/`, ZERO reference any
Nikki MF.** Two parent families:
- `M_Niagara_SakuraSprite` (+ ~13 MI children: Petal, Mote, Ember, FairyDust, Gust,
  LanternGlow, WaterMist, MistSheet, Cosmic, GroundWisps…)
- `M_SDF_Foliage_Niagara` (+ 5 Foliage MIs), plus orphans (AuroraRibbon, NebulaPetal,
  Pond, Sparkle, Ripple, SDF_Loop, PetalMesh/PetalPile, 2 Legacy)

Treatment tiers (apply lowest-risk first; each tier is one additive MF call + recompile
+ owner viewport check — captures lie, per the skill):

| Tier | Nikki MF(s) | Targets | Effect |
|---|---|---|---|
| T1 pastel-grade | MF_NikkiPastelGrade / MF_NikkiDreamGrade | all sprite MIs via parent `M_Niagara_SakuraSprite` | the "Infinity Nikki color air" in one edit — parent-level, children inherit |
| T2 rim + twinkle | MF_NikkiRimGlow, MF_NikkiTwinkleIris | Petal, FairyDust, LanternGlow, Sparkle, Mote family | petal-edge glow, iris sparkle on facing angles |
| T3 sparkle flipbooks | MF_NikkiSparkle + `T_Alpha_sparkle_pulse_flipbook`, `T_Alpha_fluid_metaball_flipbook` | Sparkle, Ripple, Pond, Mote_Ember | replaces static alpha with animated flipbook sampling (uses §3's scrub MF — build it first) |
| T4 sticker edges | MF_NikkiStickerEdge + MF_NikkiStickerShade | SakuraSprite parent (guarded by a static switch default OFF) | 2D sticker silhouette look; switch lets each MI opt in per-effect |
| T5 WPO squish | MF_NikkiSquishWPO | PetalMesh_Loop, PetalPile | organic squash on landings; verify vertex-lightweight path |

Governance: parent edits (`M_Niagara_SakuraSprite`, `M_SDF_Foliage_Niagara`) touch ~18
children at once — do them in isolated batches, recompile all children
(`get_compilation_stats` 0-PS = silent failure), re-freeze verify_baseline (these are
in the frozen catalog). Legacy parents (`M_MI_Niagara_*_Legacy`) self-reference —
confirm dead via `bp_live_path`, delete if orphan, don't treat.

## 5. Sequencing with everything else

```
NOW (offline)        this doc + chapter bible folder + MF_FlipbookScrub spec + tier specs
GOLDEN RUN (owner)   P0 closeout — editor is yours, nothing else touches it
AFTER P0_CLOSED:
  batch L  offline cleanup (§2.3 sweep) + NikkiChain variant decision memo
  batch M  §2.1/§2.2 editor fixes, one batch, re-freeze baseline
  batch F  MF_FlipbookScrub + M_Melusina_FlipbookCloth (T0 of §3)
  batch N  tiers T1→T2 in parent(s), viewport-verified per tier
  batch N' T3–T5 + flipbook cloth instances on DawnChorus/Shorewake outfits
  lookdev  capture pass AFTER materials land (see melodia-lookdev-demo-reel); owner
           eyes on final; agent captures for record only
```

Each batch ends with: compile-clean, verify_baseline re-freeze if a frozen asset
moved, one commit on a `cleanup/` or `feature/` branch via PR (the unified-main
convention now proven), and a ledger note where a gate is affected.

## 6. Fall-term framing (the professor lens)

This campaign *is* the reusable-chapter argument: a material system with one master
family, one flipbook scrub contract, one treatment tier stack, and per-chapter
instances that inherit — so Chapter N+1 costs a fraction of Chapter N. Document it as
you go (each batch's commit + this plan's tables are the evidence trail).
