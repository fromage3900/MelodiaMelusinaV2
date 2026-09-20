# PLAYBOOK_FLIPBOOK_FIXA — material owns scrub

**Status:** quick reference (Package B, 2026-09-17)  
**Canonical long form (Fix A lane):** [`Playbooks/PLAYBOOK_FLIPBOOK_FIXA.md`](Playbooks/PLAYBOOK_FLIPBOOK_FIXA.md)  
**LeafPile receipt:** [`VFX_FIXA_LEAFPILE_2026-09-17.md`](VFX_FIXA_LEAFPILE_2026-09-17.md)

## Rule (non-negotiable)

When the **material** owns flipbook / atlas scrub (`Time * FlipFPS`, `MF_FlipbookScrub`, GridCols/Rows):

1. Niagara **SubUVAnimation = off** (`enabled=false`).
2. Sprite **SubImageSize** policy:

| Material kind | SubImageSize | Example |
|---|---|---|
| Flipbook scrub (`M_Niagara_MelodiaFlipbook` family, sheep BeatStar / PetalLoop) | **1×1** | BeatBurst, HybridSparkles FlipSparkles, PetalCascade PetalLoop |
| Static variant atlas (MI SubUV Columns/Rows pick cells; no FlipFPS scrub) | **Keep atlas grid** | `NS_Melodia_LeafPileLoop` → **2×2** with `MI_Leaves` |

Never run Niagara SubUV **and** material scrub on the same sheet (`RISK_DOUBLE`).

## Do not

- Monolith `save_packages` / `recompile_material` — **owner Ctrl+S only**.
- Reintroduce SubUV on CLEAN_FIXA systems during AAA polish.
- Force LeafPile to 1×1 (atlas variants, not flipbook).
