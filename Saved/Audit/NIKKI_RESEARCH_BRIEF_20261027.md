# Infinity Nikki — art-direction research brief (2026-10-27)

Purpose: tune Faraway Mother dressing / water / sparkle params from primary sources for tonight's renders.

## Sources
- Apple Developer interview with Infold leads (Douhu/Ade/Dodie), Apple Design Award 2025 (Visuals & Graphics) coverage.
- AUTOMATON WEST: Infinity Nikki art director on outfit narrative/material design.
- AUTOMATON: GDC 2026 level-design talk (V2.0 map/ability iteration).

## Findings that map to Faraway Mother
1. **Color is the first design axis.** Lead with a restrained pastel harmony and let one accent family carry each area (their gold+green example). Our frame: cream/silk base + pink/lilac family + white pearl accents is on-canon; keep scatter materials inside this family.
2. **"Beyond reality" fabric evolution, not photoreal fabric.** Reconstruct real fabric, then exaggerate: embroidery layers, glitter effects. Our silk-mountain terrain + blossom-emit scatter already reads as evolved fabric; resist adding photoreal foliage.
3. **Jewelry/gemstone material system**: dedicated algorithmic sparkle — complex refraction, subsurface transmission, highly variable specular; prismatic sparkle must read at night too. Action: PearlJewel / CrystalTip instances deserve an iridescent/specular sparkle pass (MI_BLK_BlossomWhiteEmit is a start; consider a thin-film/iridescence parameter on the pearl MI).
4. **Bright, inviting, warm lighting; small water surfaces reflect the deep sky.** Water should mirror sky color — the oceanology hero MI (MI_Oceanology_Melodia_Hero) repoint is the right call; verify it has a strong sky/reflection response at basin scale.
5. **Density is negotiated with traversal, not maximized.** GDC: the "impossible triangle" of aesthetics / world consistency / platforming — Sticky Amber density had to be lowered for playability. Keep the route corridor (SeamWay exclusion) clean and cluster dressing at readable gaps; sparse jewelry-scatter at ~4k instances over ±4 km is in the right register — do not carpet.

## Param actions applied / recommended
- Keep dress_config densities as authored (1.0 stride); per-biome knobs now live in `Saved/Audit/tmp/dress_config.json` for artist tuning.
- Water: BLK_Waterfall + water-edge scatter now on `MI_Oceanology_Melodia_Hero` (19 slots).
- Next material pass (not tonight): iridescence/sparkle on pearl + crystal MIs; emissive twinkle for canopy proxies.
