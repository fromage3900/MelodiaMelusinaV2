# Infold / Infinity Nikki: sourced pipeline facts (2026-10-20)
Sources were reused from INFINITY_NIKKI_BRIEF_v2.md, plus Epic PCG docs. **[I]** = inference. No public source gives Infold's PCG graphs, streaming cell sizes, or procedural-vs-hand-placed ratios. Any numbers we use are our own targets.

## UE5 tooling & engine choice
- Infold switched to UE for an open world with large scale, high fidelity and real-time lighting. The team grew its own UE engineering in-house. [UE interview](https://www.unrealengine.com/developer-interviews/behind-the-scenes-of-infinity-nikki-tracing-a-glamorous-turn-to-an-unreal-open-world) · [Seven stories](https://www.unrealengine.com/en-US/spotlights/seven-stories-of-switching-to-unreal-engine)
  → *Implication:* Use stock UE 5.8 systems such as PCG, World Partition and Lumen first. Only write custom code (like our Melodia subsystem) where the look requires it.
- The game ships on mobile, PC and console. Apple's interview covers the work of scaling one UE build across devices. [Apple Developer](https://developer.apple.com/news/?id=9mgkwjnm)
  → *Implication:* Budget scalability tiers early for PCG density, Niagara and the OSC-driven MPC.

## Rendering / toon look
- The look is cartoon-like forms with **PBR lighting** on a Disney-derived model. They built custom character shadows, GI and tone mapping, and weekly "art benchmark" meetings lock the style. [UE interview](https://www.unrealengine.com/developer-interviews/behind-the-scenes-of-infinity-nikki-tracing-a-glamorous-turn-to-an-unreal-open-world)
  → *Implication:* Use M_Master_Toon_Universal for characters and regalia, but keep the environment on Lumen/PBR. Hold a weekly benchmark against 3 locked frames.
- The art director says outfits carry the narrative and symbolism, and that piling on visual information doesn't move people. [AUTOMATON](https://automaton-media.com/en/news/you-cant-touch-peoples-hearts-by-just-piling-together-visual-information-infinity-nikki-art-director-explains-how-outfits-are-designed-to-express-narrative-and-sym/) · [GDC 2026](https://schedule.gdconf.com/session/how-infinity-nikki-turns-outfits-into-fantasy-and-why-it-works/915309)
  → *Implication:* Melusina's regalia (circlet, earrings, wings) should each carry story meaning, not just add detail.

## Level design / world
- PR Peng (GDC 2026) describes map design as an "impossible triangle" of aesthetics, world consistency and platforming function. Trade-offs are made explicitly, for example art refusing sharp, rigid water edges just to serve gameplay. [AUTOMATON GDC lecture](https://automaton-media.com/en/column/infinity-nikki-level-designer-talks-about-philosophy-behind-large-scale-gameplay-and-map-expansions-in-version-2-0/)
  → *Implication:* Tag each Poitou zone and PCG graph with its priority corner. Keep canal banks organic.
- Lore (fan wiki, not official) describes Florawish as layered historical styles: Gothic stone, then glass and metal, then Alpine timber. [Florawish culture](https://www.infinity-nikki.com/lore/florawish-culture/) · [history](https://www.infinity-nikki.com/lore/florawish-history/)
  → *Implication:* Mix the Blender cathedral and Parisian builder outputs with maraîchin timber, so the world reads as eras layered by history.
- [I] The world looks like procedural foliage fields with hand-placed hero vignettes at the nodes.
  → *Implication:* PCG_OvergrownRuins and the Houdini masks drive reeds, poplars and duckweed. Heroes such as the abbey, PianoWalkway and bridges are placed by hand.

## Streaming / PCG (Epic docs; Infold-specific use unconfirmed)
- PCG works with World Partition: you can partition graphs and generate hierarchically. [Epic](https://dev.epicgames.com/documentation/unreal-engine/using-pcg-with-world-partition-in-unreal-engine?lang=en-US)
- Runtime hierarchical generation builds grid cells around streaming or generation sources. [Epic](https://dev.epicgames.com/documentation/en-us/unreal-engine/runtime-hierarchical-generation)
- Biome Core is documented by Epic. Partitioning of *local* biomes was not supported "before at least 5.8" (Epic staff, Oct 2025). [Biome Core](https://dev.epicgames.com/documentation/en-us/unreal-engine/procedural-content-generation-pcg-biome-core-and-sample-plugins-reference-guide-in-unreal-engine) · [forum](https://forums.unrealengine.com/t/pcg-biomes-v2-partitioning-for-local-biome-graphs/2680350)
  → *Implication:* Check local-biome partitioning in 5.8 before relying on it. Until then, use several small biomes fed by the Houdini masks.

## Audio
- Each BGM track is tied to a location and transitions as the player moves. The orchestration includes accordion. Infold treats spatial audio as part of gameplay. [Wikipedia](https://en.wikipedia.org/wiki/Infinity_Nikki) · [Wwise Up On Air](https://www.youtube.com/watch?v=JcZdVfxCCa8)
  → *Implication:* Give each zone its own cue, crossfaded. PianoWalkway and the TD→MPC feed count as gameplay, not decoration.

## Onboarding / first hours
- No Infold source on first-hours design was found. The general reference is [GDC Vault: Teaching First-Time Level Designers](https://www.gdcvault.com/play/1035054/Teaching-First-Time-Level-Designers).
- [I] From gameplay: the opening is a guided linear stretch, then one ability is taught in a safe space, then the world opens toward a visible landmark.
  → *Implication:* Teach one mechanic at a time (the piano walkway is a natural one), with the abbey visible as the goal.
