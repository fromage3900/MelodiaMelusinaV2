# M_Master_Toon_Universal — Professional Overhaul Plan (Infinity-Nikki Game-Ready)

**Goal:** the shared toon master becomes genuinely out-of-the-box usable for an
Infinity-Nikki-style stylized environment portfolio: dead functions removed,
existing functions *expanded* (not just gated), and ease-of-use first. ~105
instances depend on it, so every change is additive/gated or migration-audited.

Companion doc: `UNIVERSAL_MASTER_NODE_REVIEW.md` (per-family verdicts + node dump
`Saved/Audit/universal_master_nodes.json`). Master is clean in git; backup at
`_Scratch/M_Master_Toon_Universal_BACKUP_20260702`.

---

## Already shipped (this overhaul, committed)

| Area | What | Commit |
|------|------|--------|
| Dead removal | Character/skin/hair/eyes family removed (traced bypass + native sweep) | `0a33642` |
| Dead removal | Itto + Madoka regrouped to InkWear/VeinGlow (names kept for 9 live instances) | `0a33642` |
| Ease of use | 142 scalars clamped to sane slider ranges | `0a33642` |
| Expansion | Advanced ColorRamp at BaseColor tail (RampLow/Mid/High/PosMid/Contrast/Strength) | `0a33642` |
| Ease/perf | Feature gates default-OFF: Celestial/Sparkle/FairyDust/Weather/Elemental (42 user instances flipped ON) — folds unused families out, PS 1128→946 | `6d57e37`,`377b20d`,`a6a325c` |
| Fix | Macro variation was UV-driven (default 0.0008, "scaled oddly") → world-space; 24 instances migrated | `a6a325c` |
| Fix | DetailNormal was a marble COLOR texture in a normal slot → real normal; SparkleMask ugly twinkle → Sparkle4 | `599dd48` |
| Expansion | **Real thin-film spectral iridescence** (IQ cosine palette) replacing flat single-hue tint; new IridescenceCycles | `285a82e` |
| Expansion | **Colored, color-ramped shadows** (bShadowRamp_Active: ShadowRampLow/Mid/High driven by shadow depth) | `cff595b` |
| Magic | **Dream Rim Iridescence** (bDreamRim_Active: fresnel × IQ thin-film spectral shimmer spliced into emissive — rainbow silhouette rim) | `a5050e4` |
| Magic | **Dream Bloom** (DreamBloomStrength default 0: brightest base areas bloom into soft pastel self-glow — the "everything gently luminous" Nikki quality) | `3697144` |
| MPC | **GlobalEmissiveBoost wired** as a global emissive multiplier from MPC_Portfolio_Palette (default 1.0 = no change) — whole-level glow control alongside GlobalSparkleIntensity + TimeOfDay | `e9e12af` |

Net so far: **918 → 907 expressions** (magic/MPC adds sit on top of the removal
floor), the 5-billion-slider disease gone, garbage instances (IridescentRock)
cleaned. Overnight verification (2026-07-04): sparkle map confirmed on the good
`T_Spark_Sparkle4`; both MPCs (MPC_Portfolio_Palette, MPC_CelestialVault) resolve
with defined params — no silent-zero failures.

---

## Remaining stages (this plan)

### Stage A — Dead-function removal (consolidation)
- **Shadow Garden (Flowers)** family (~15 nodes, ShadowFlower*): audited 2026-07-03
  → **KEEP**. It's *not* dead — 3 sakura-adjacent instances actively use it for
  flower-dappled shadows (`MI_Landscape_SakuraGarden` 0.55, `MI_Landscape_PondBank`
  0.38, `MI_Show_CherryBlossom` 0.70). On-theme Nikki feature; distinct from the
  color-ramped Shadow Dream (dappled shape vs graded tint). Optional: gate it behind
  `bShadowGarden_Active` (default OFF, flip ON for those 3) to save PS on the other
  ~100 instances — same pattern as the other feature gates.
- ~~**Core-parallax vs per-layer parallax** duplication~~ **RESOLVED 2026-07-04 —
  NOT a duplicate, nothing to remove.** Live trace: the `05 | Parallax` group is a
  set of *global* parallax controls that multiply *together* with the per-layer
  `LayerA/B/C_ParallaxScale` (`(height×ParallaxScale)×LayerA_ParallaxScale` per
  layer). One integrated global×per-layer system; removing the core block would
  break parallax on every layer. See NODE_REVIEW family 05x. Reframed as an
  *expand* target (stylized editable depth) per the render-day steer.
- Final `MEL.delete_unused_expressions` sweep for any new orphans.
- Est. → ~800 expressions.

### Stage B — Expand existing functions (Nikki richness)
- **Unify the remaining ramp implementations** onto `MF_ColorRamp3` (Palette +
  any per-family leftovers) — one ramp path, consistent params.
- **Single configurable sheen**: merge the two sheen calcs onto `MF_IridescenceSheen`.
- **Iridescence follow-up**: expose an `IridescenceThickness` texture input option
  (per-pixel film thickness → localized rainbow, e.g. wet petals) behind a switch.
- **MF_VertexPaintBlend**: wire the authored-but-unwired 4-way vertex-color blend
  behind `bVertexPaintBlend_Active` (Shelves1's vertex colors are the test case) —
  the trimsheet hand-paint feature that's been scoped twice.

### Stage C — Ease-of-use / organization pass
- **Parameter group audit**: confirm every param has a numbered group
  (`01 | Base` … `19 | Weather`); move stragglers (a few InkWear/VeinGlow/Triplanar
  params). Report-only naming; no `rename_asset` (standing ban).
- **Instance-facing defaults**: verify the master's default values give a clean
  neutral surface with all gates off (the "drop it on a mesh and it looks fine"
  baseline).
- **Docs**: a one-page "Universal Master — Instance Author's Guide" (which switch
  turns on what, sane ranges) in `Docs/Production/`.

### Stage E — Melodia art-style integration (user request 2026-07-03)
- **Volumetric ink blend**: wire `MF_InkAccumulation` (BaseColor/InkColor/InkAmount/
  CavityPower/AccumBias → InkedColor) into the BaseColor tail behind `bInk_Active`
  (default OFF) — cavity-driven ink pooling for the sumi-e/Melodia look.
- **Impasto paint**: wire `MF_Impressionist_Impasto` (StrokeMask → ImpastoHeight)
  into the normal/detail path behind `bImpasto_Active` (default OFF) — brush-stroke
  relief.
- **Melodia SDF + Baroque as layer options**: expose the beloved SDF/baroque
  procedurals (M_SDF_RoseWindow, GildedFiligree, BaroqueScrollwork, VinylGroove) as
  MF-wrapped emissive/overlay options selectable per instance (needs each converted
  to an MF first, or sampled as baked textures). Bigger — sequence after A–D.
- **Splice safety**: all at the known BaseColor tail (ColorRamp `graded` →
  `MaterialFunctionCall_2`/iridescence consumers); switch-gated so the ~105
  instances are unaffected until opted in.

### Stage D — Instance fix-up pass (data-driven)
- Re-run `audit_universal_instance_overrides.py`; **report + fix** any remaining
  out-of-range overrides against the new clamps (the IridescentRock-class garbage).
- Verify the 4 macro-migrated Zen instances (BambooWood/MossStone/RiverStone/
  TempleStep at the 512 clamp) read correctly — retune if not (flagged in review doc).
- Confirm all 42 gate-flipped instances still resolve.
- Spot-fix broken texture refs like the StonePath=None case (already fixed one).

---

## Missed tasks recovered from the old plan (`generic-enchanting-boot.md`)

Reviewed the prior consolidated plan; these Stage-4/5 items were scoped but not
executed and are folded above:
- Ramp unification, single sheen, shadow-tint consolidation → **Stage A/B**.
- MF_VertexPaintBlend wiring → **Stage B**.
- Instance audit fix-ups → **Stage D**.
- **Melodia Substrate conversions** (VinylGroove/Facade_Baroque/CelestialStarMap,
  fix broken M_SDF_ParallaxPulse) → separate track, not part of the master overhaul
  but still open.
- **Water master** got its layered-wave expansion (`062eaff`); UE5.8-water + UDS
  reflection integration remains open (separate, bigger scope).

---

## Sequencing & rules
A → B → C → D. Each stage: compile stats + BSDF-intact check; targeted
`get_expression_connections` only (never bulk `get_inputs` loops — crash risk);
`save_asset(only_if_is_dirty=False)`; per-stage git commit with exact paths;
gates/switches default-OFF so no existing instance changes look unless opted in;
report any instance that would lose an overridden param before removing it.

## Verification
Per stage: capture a representative instance before/after (switch OFF must match
prior look by construction); param-diff; final `git status` clean of own files;
update `UNIVERSAL_MASTER_NODE_REVIEW.md` execution ledger + this doc's shipped table.
