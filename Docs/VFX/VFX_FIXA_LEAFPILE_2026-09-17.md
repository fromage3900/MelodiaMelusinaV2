# Fix A — NS_Melodia_LeafPileLoop — 2026-09-17

Live Monolith apply; owner **Ctrl+S**; dirty packages = 0. Wiring lives in the
Niagara `.uasset` (not committed in this docs PR).

Asset: `/Game/EnvSandbox/VFX/Systems/Sakura/NS_Melodia_LeafPileLoop`
Emitter: `LeafPile`

| Pin | Before | After |
|-----|--------|-------|
| SubUVAnimation (particle_update) | enabled=true | **enabled=false** |
| Sprite SubImageSize | 2×2 | **2×2 kept** (leaf atlas variants — **not** flipbook scrub) |

## Why not SubImageSize 1×1

`MI_Leaves` is a **2×2 static atlas** (`SubUV Columns/Rows=2`, textures
`T_Leaves_Dead_2x2_*`). SubImageSize 2×2 selects leaf variants. SubUVAnimation
was the double-scrub culprit (animating through atlas cells). Fix A here =
**Niagara SubUV off; atlas grid stays**. Do not claim SubImage 1×1.

## Status at capture

**CLEAN_FIXA** (SubUV off; SubImage 2×2 intentional) after the 2026-09-17 live
apply. Treat this as asset-specific evidence, not a timeless project-wide risk
census. Durable rule: [`Playbooks/PLAYBOOK_FLIPBOOK_FIXA.md`](Playbooks/PLAYBOOK_FLIPBOOK_FIXA.md).
