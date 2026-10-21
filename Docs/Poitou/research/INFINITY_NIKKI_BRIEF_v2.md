# Infinity Nikki → Poitou v2 brief (UE 5.8) — v2 (deeper sourcing pass, 2026-10-20)
Sources (verified): [UE interview](https://www.unrealengine.com/developer-interviews/behind-the-scenes-of-infinity-nikki-tracing-a-glamorous-turn-to-an-unreal-open-world) · [UE "Seven stories"](https://www.unrealengine.com/en-US/spotlights/seven-stories-of-switching-to-unreal-engine) · [Apple Developer interview](https://developer.apple.com/news/?id=9mgkwjnm) · [AUTOMATON art-director interview](https://automaton-media.com/en/news/you-cant-touch-peoples-hearts-by-just-piling-together-visual-information-infinity-nikki-art-director-explains-how-outfits-are-designed-to-express-narrative-and-sym/) · [GDC 2026 session](https://schedule.gdconf.com/session/how-infinity-nikki-turns-outfits-into-fantasy-and-why-it-works/915309).
**[I]** = inference from gameplay/screenshots, not sourced. Added v2 sources: [Wikipedia – Music](https://en.wikipedia.org/wiki/Infinity_Nikki) · [Wwise Up On Air: Infinity Nikki audio](https://www.youtube.com/watch?v=JcZdVfxCCa8) · [Florawish/Culture lore wiki](https://www.infinity-nikki.com/lore/florawish-culture/) · [Florawish/History lore wiki](https://www.infinity-nikki.com/lore/florawish-history/) · [AUTOMATON: GDC 2026 level-design lecture (PR Peng)](https://automaton-media.com/en/column/infinity-nikki-level-designer-talks-about-philosophy-behind-large-scale-gameplay-and-map-expansions-in-version-2-0/) · [GDC Vault: Teaching First-Time Level Designers (K. Tominaga)](https://www.gdcvault.com/play/1035054/Teaching-First-Time-Level-Designers).
Still no public source gives fog distances, LOD bands, prop density or PCG-vs-hand-placed ratios; all numbers remain our targets.

## 1. Shading & grading
- Sourced: cartoon forms but **PBR lighting** (Disney-derived UE model); custom GI/char shadows and tone mapping; weekly "art benchmark" meetings lock style. → Keep Lumen/PBR, stylize via albedo/shape not unlit toon. Run a weekly benchmark against 3 reference frames.
- [I] Pastel, high-key, low-contrast shadows tinted blue-lilac; warm sun. → Albedo cap 0.85, min 0.08; shadow tint ~#8A93C8; sun ~#FFE8C8; saturation grade +10% mids, −15% shadows.
## 2. Toon look on terrain [I]
- Terrain reads as soft painted value blocks with flower/grass masses, not micro-detail. → Max 4 terrain layers per view; macro tint variation over 20–40 m; grass card tips lightened 15%; no tiling normal detail >0.3 strength.
## 3. Horizon & layering [I]
- 3 bands: near detail, mid silhouette (castle/towers), far pale hills fading into height fog; landmarks stay readable through haze. → Near 0–150 m, mid 150–800 m (HLOD), far >800 m as cards/imposters; exponential height fog desaturates far band to ~40% contrast, tint #CFDDEA. Abbey silhouette must read at 1 km.
## 4. Wayfinding & landmarks [I] (+ sourced design principle)
- Sourced (GDC 2026, PR Peng via AUTOMATON): map design is an "impossible triangle" of aesthetics, world consistency and platforming function; art won't make water with "sharp, rigid edges" just for gameplay — trade-offs are made explicitly per map. → Log which corner each Poitou zone prioritises.
- One vertical hero visible from most of a region (Florawish clock/castle type); paths flanked by flowers/lamps; "whim" collectibles sparkle off-path. → Maillezais ruin as hero, visible from ≥70% of walkable area; poplar rows as directional lines to it; secondary landmark every ~150–200 m.
## 5. Prop density & clustering; procedural vs hand-placed [I]
- PCG-like foliage fields + hand-placed hero vignettes at nodes; dense clusters, open breathing space between. → PCG for poplars, reeds, duckweed, meadow; hand-place heroes (abbey, punts, piano walkway, bridges). Cluster rule: 60/30/10 hero/medium/small within 6 m vignettes, ≥12 m quiet gaps.
## 6. Water & canals [I]
- Calm, stylized reflective water, light ripples, flowers at banks. → Canals 4.8/7.2 m wide (grid multiples), green-teal #6FA89A, duckweed noise 30–60% coverage, SSR+planar for poplar reflections, flow speed ≤0.1 m/s.
## 7. Music & interactive sound (partly sourced)
- Sourced (Wikipedia/FoldEcho credits): each BGM track is tied to a specific location and transitions dynamically as the player moves; orchestral (Budapest Scoring Orchestra) with strings, flutes, Irish whistle, guitar, **accordion**; lighter scenic areas get more uplifting cues. Wwise talk: team treats spatial audio and music as part of gameplay. [I] specific musical interactables. → Piano-key walkway: 0.6 m keys, one note per step, French-folk/musette scale; accordion/harp stems crossfade by zone (radius 40–80 m); punt poles add percussion.
## 8. Abstraction of real places & whimsy scale (partly sourced)
- Sourced (fan lore wiki, not official): Florawish blends eras — old stone neoclassical/Gothic, later stained glass + metal "mirroring western-European palatial architecture", modern wooden Alpine-style houses (front gables, overhanging eaves, wood-tile roofs). I.e. a *mix* of real styles layered by in-world history, not a copy of one town. [I] ornament exaggeration ratios. → Keep abbey ruin true silhouette; simplify masonry to 2.4 m bays; exaggerate ornaments (finials, lamps, flowers) 1.3–1.5×; flowers up to 2× real.

## Contract rules
1. All modular geometry snaps to 0.6 m; bays = 2.4 m.
2. Lighting is PBR/Lumen; no unlit toon shaders on environment.
3. Albedo within 0.08–0.85 linear.
4. Shadow tint ≈ #8A93C8; sun ≈ #FFE8C8.
5. Bands: near ≤150 m, mid ≤800 m via HLOD, far >800 m cards.
6. Far band ≤40% contrast after fog.
7. Abbey visible from ≥70% of walkable nav area.
8. A secondary landmark within 200 m of any point.
9. Hero assets hand-placed; foliage/reeds/poplars PCG only.
10. Vignettes ≤6 m radius, separated by ≥12 m quiet space.
11. ≤4 terrain layers visible per frame.
12. Canal widths are multiples of 2.4 m.
13. Ornament scale 1.3–1.5× real; architecture silhouette 1.0×.
14. Every walkway key = 0.6 m and triggers one note.
15. Music zones crossfade over ≥10 m.
16. Weekly benchmark vs 3 locked reference frames.
17. Each zone has its own music cue; accordion present in ≥1 layer of every Poitou cue.
18. Architecture shows ≥2 layered historical styles (e.g. Romanesque/Gothic stone ruin + later timber/maraîchin houses).
19. Water edges are organic; no sharp rectilinear banks except built canal quays.
20. Each zone doc states its priority: aesthetic / consistency / traversal.
