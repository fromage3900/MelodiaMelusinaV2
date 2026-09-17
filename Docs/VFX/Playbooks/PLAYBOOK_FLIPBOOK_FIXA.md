# Playbook — Flipbook Fix A (double-scrub)

**When to use:** a Niagara sprite (or ribbon) samples a flipbook / atlas material
**and** the emitter has `SubUVAnimation` enabled, or `SubImageSize` is animating
the same sheet the material already scrubs.

**Defect:** two clocks on one atlas → double-speed, skipped cells, torn frames.

## Rule

**The material owns scrub.** Niagara does not.

1. Disable Niagara `SubUVAnimation` (module may stay present; **enabled = false**).
2. Then pick **exactly one** SubImageSize policy:

| Material kind | SubImageSize | Example |
|---|---|---|
| Flipbook / FlipFPS / Grid scrub (`M_Niagara_MelodiaFlipbook`, `M_SurrealFabric_Flipbook`, sheep BeatStar) | **1×1** | Choral Sheep BeatBurst / HybridSparkles / PetalCascade |
| **Static variant atlas** (no FlipFPS; MI SubUV Columns/Rows pick cells) | **Keep the atlas grid** | `NS_Melodia_LeafPileLoop` → **2×2** with `MI_Leaves` |

Do **not** force LeafPile to 1×1. That atlas is leaf variants, not a flipbook.

## Verify

- Pin-read: `subuv_live=false`.
- Flipbook case: `SubImageSize=1×1`.
- Atlas case: `SubImageSize` matches MI Columns×Rows; SubUVAnimation still **off**.
- Status: `CLEAN_FIXA`. Never reintroduce Niagara SubUV when the material owns scrub.

Ship evidence 2026-09-17: **RISK_DOUBLE = 0**. Receipts in
[`../VFX_FIXA_RISKS_2026-09-17.md`](../VFX_FIXA_RISKS_2026-09-17.md) and
[`../VFX_FIXA_LEAFPILE_2026-09-17.md`](../VFX_FIXA_LEAFPILE_2026-09-17.md).

## Do not

- Invert ownership without an owner look call (Niagara-owns-scrub + material full-UV is a valid **single** clock).
- `save_packages` from Monolith; owner Ctrl+S.
- Apply Fix A to mesh/ribbon systems with no sprite atlas (`N_A_RIBBON_MESH`).
