# Infinity Nikki + Anime JRPG — research folded into Melodia's canon (2026-10-22)

**Why this file exists:** the world identity canon anchors Melodia's look to Infold's
*Infinity Nikki* and the project AGENTS names "Wardrobe bar: Infinity Nikki" as one of the
three bars. A bar with no content is a wish. This is the research that makes the bar
concrete — what Infold actually shipped, what the genre expects, and which parts change
Melodia's art direction and its pipeline.

**Status:** research with folds applied. The folds are listed under "Folded in" and are
already in the canon and the pipeline contracts — this file is the provenance, not a
second authority.

---

## 1. Infinity Nikki — what Infold actually did

Sources fetched 2026-10-22:
- **Apple Developer** — "How Infold Games fashioned an open world for *Infinity Nikki*"
  (2026-04-03), an interview with Douhu (lead gameplay systems designer, outfits), Ade
  (lead programmer) and Dodie (art director).
  https://developer.apple.com/news/?id=9mgkwjnm
- **Intel Gaming Access** — "Infinity Nikki – Dress Up to Level Up" (2025-12-01),
  Infold Games on their own process.
  https://game.intel.com/us/stories/infinity-nikki-dress-up-to-level-up/
- **IGN** — "Dress Up, Jump Up: Developer Kentaro Tominaga Shares Gameplay Design of
  *Infinity Nikki*" (2024-08-23).
  https://www.ign.com/articles/dress-up-jump-up-developer-kentaro-tominaga-shares-gameplay-design-of-infinity-nikki
- **Polygon** — "*Infinity Nikki* is an upcoming open-world fashion RPG" (2024-08),
  which names the design lineage: "Zelda-like elements".
  https://www.polygon.com/24168858/love-nikki-infinity-fashion-rpg-papergames/
- **Epic Games** — "Behind the Scenes of *Infinity Nikki*: Tracing a Glamorous Turn to an
  Unreal Open World" (developer interview; the page did not render for us, so nothing is
  quoted from it here).
  https://www.unrealengine.com/developer-interviews/behind-the-scenes-of-infinity-nikki-tracing-a-glamorous-turn-to-an-unreal-open-world

### The four facts that matter to Melodia

**1. The fabric system is built on FOUR-LAYER UV BLENDING.** Ade, on the material system:
> "Infinity Nikki introduces a revolutionary material system. At the core is a re-engineered
> fabric algorithm that preserves the advantages of four-layer UV blending textures, while
> requiring only minimal parameter adjustments to accurately simulate a wide range of
> materials, including the natural coarseness of cotton and linen, the smooth sheen of silk
> and satin, as well as the delicate tactile qualities of various velvets and flannel."

**Melodia already has this vocabulary.** The toon master's four-layer analogue is the
project's own style contract; the material functions `MF_ColorRamp3`, `MF_DF_ContactBlend`
and `MF_ClothWindDrape` are the same family of idea. The research does not add a new
material authority — it **confirms that the existing one is the right one**, and it says
what a *garment* tier needs: the same four-layer blend, driven by the wind lane, so that
cloth reads as cloth without a second shader stack.

**2. The wardrobe IS the progression.** Infold:
> "Different outfits are imbued with different abilities that allow players to guide Nikki
> — and her cat companion, Momo — through clever puzzles."

and, on their own design intent:
> "We leaned into exploration, emotional discovery, and player agency—making style and
> creativity the real 'progression'."

The game's own framing is "Dress up to level up". **This is the "Wardrobe bar" made
concrete**: in Melodia, the garment carries the capability — which is exactly what
`UMelodiaWardrobeSubsystem` already owns ("owned/equipped fashion state and its gameplay
capability hooks"). The bar is not a costume fantasy; it is a rule: *if a piece of
clothing has no capability attached, it is not yet Melodia clothing.*

**3. "Fashion as narrative" is a stated intent, and the pieces tell stories.** Infold:
> "Also, the outfit design goes beyond aesthetics. Each piece tells a story—for example, a
> mermaid gown might use specific materials and details to convey themes of loneliness or
> elegance. It's fashion as narrative."

For the house leg this is the same demand the fill contract already makes: books, candles
and jars are not decoration, they are the previous owner's scholarship. A dressing family
carries a **story**, and the artist should be able to see it.

**4. The pace is deliberately slow, because the player must breathe.** Douhu on the
double-jump:
> "That's because we want players to have plenty of time to experience the world. Our core
> gameplay is based on jumping, but it's not a very quick motion. It's a slow, like a
> micro-response for that specific floating motion. And that's because we want to let
> players breathe and appreciate all the details of Miraland."

That is the P0 golden walk's own thesis (a 10-minute opening with 0:40 beats, a house leg
that is walked and not sprinted) — now backed by a shipped precedent rather than taste.

### Two production lessons worth stealing verbatim

- **Constraint-based, baked, not collision-based, live.** Ade:
  > "Through proprietary skeletal chain algorithms and enhanced cloth solvers, the team
  > replaces costly and unstable traditional collision-based algorithms with more stable
  > and controllable constraint-based algorithms."
  and
  > "We introduced a flexible and soft-driven constraint stage during preprocessing, ensuring
  > that even under dramatic movements, the initial garment avoids clipping the body."

  *Melodia's version:* the settling pass (`UMelodiaDressingSubsystem::PhysicallyDrop`) and
  the cloth tier should be **baked at cook/preprocess time**, not simulated live — the same
  answer the fill contract already gives for PCG (bake vs runtime generation is W8, and
  this says which way the evidence points).
- **Free combinations without instability.** Infold's cloth system supports "collision
  handling between different garment types and multiple clothing layers, enabling free
  outfit combinations without sacrificing stability." The wardrobe must be combinable
  *because* it was designed for combination, not despite it.

---

## 2. The anime-JRPG side: the wardrobe is a catalogue, and it has known failure modes

The genre's canonical wardrobe is **Final Fantasy XIV's Glamour** (and its descendants):
- The **Glamour Dresser** stores up to 400 pieces of gear, sorted by category; storing an
  item as an "outfit glamour" costs a **glamour prism**. (Square Enix's own UI guide:
  https://na.finalfantasyxiv.com/uiguide/fashion/equipment-glamours/fashion_dresser_how_to.html)
- **The known flaw:** storing an outfit glamour **loses the item's dyes** — a long-standing
  complaint, and the reason players ask for "a glamour catalogue they can access anywhere"
  rather than a chest in one room.
  https://www.player2.net.au/2023/06/final-fantasy-xivs-glamour-system-has-a-fundamental-flaw/
- The community answer is a **catalogue**: "Eorzea Collection" is a shared catalogue of
  looks (https://ffxiv.eorzeacollection.com/glamours) — the community built the thing the
  game should have shipped.

**What Melodia takes from it:**

1. **The catalogue must be a DATA authority, reachable from anywhere** — not a chest in one
   room. `DA_MelodiaDressingCatalog` is exactly that shape (a gameplay-tag family → hero
   prop set), and it is reachable from any level or any system.
2. **Storing a look must never destroy the artist's material choice.** The dye loss is the
   lesson: Melodia's catalogue stores the **material instance with the mesh**
   (`FMelodiaDressingProp::MaterialOverride`), so a saved look keeps the exact surface the
   artist chose. That is the Melodia answer to a genre-wide bug.
3. **The catalogue needs a way to be browsed, not only queried.** "The community built the
   thing the game should have shipped" is a feature request for Melodia's own wardrobe UI
   later — a catalogue the artist can look through, not only a key the code can query.

---

## 3. Folded in — where each lesson now lives

| Lesson | Folded into | What it changed |
|---|---|---|
| Four-layer UV blending is the fabric substrate | `Docs/MELODIA_MELUSINA_WORLD_IDENTITY_CANON_2026-10-20.md` §3 | the canon now says what "high-craft stylized realism in the Infold tradition" means technically, and that the garment tier reuses the existing four-layer toon vocabulary rather than a second shader stack |
| The garment carries the capability | the canon §2 (the wardrobe bar) | "Wardrobe bar: Infinity Nikki" becomes a testable rule: a garment with no capability is not yet Melodia clothing |
| Fashion as narrative | `specs/p0/melusina_room_dressing_pipeline.v1.json` (W1/W5) | each dressing family carries a **story tag**: what the room's clutter says about the person who lived there |
| Baked, constraint-based settling (not live collision) | `specs/p0/melusina_room_dressing_pipeline.v1.json` (W2/W8) | the settling pass and the cloth tier are bake-time work; W8's bake-vs-runtime question now has a shipped precedent pointing one way |
| Slow pace so the player can breathe | the canon's pacing (P0 golden walk) | the 10-minute opening with 0:40 beats is a shipped design decision, not a taste call |
| The catalogue is reachable from anywhere and preserves materials | `specs/p0/melusina_dressing_catalog.v1.json` + `MelodiaDressingCatalog.h` | the catalogue stores the material instance with the mesh, so a saved look keeps the artist's surface |
| The catalogue must be browsable | `specs/p0/melusina_room_dressing_pipeline.v1.json` (W1) | a follow-up: a wardrobe UI over the catalogue, built on the same data |

## 4. What this research does NOT change

- It creates **no new authority**: no new material master, no second wardrobe system, no
  new dressing pipeline. The existing toon master, `UMelodiaWardrobeSubsystem` and
  `UMelodiaDressingSubsystem` keep their jobs.
- It does not import Infinity Nikki's systems: no Chaos Cloth requirement for the house
  leg, no new shader stack, no cloth solve in the fill.
- It does not license anything from Infold: the lessons are practice and architecture, not
  assets.
