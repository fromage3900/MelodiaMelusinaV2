# MELODIA MELUSINA — World Identity & Co-Identity Canon
**Status**: v0.2 — LIVING DRAFT (locked in dialogue with Brennan, 2026-10-20; revised 2026-10-21)
**Domain**: Creative identity — tone, look, mythos. The *who and why* of the world.
**Authority note**: This is the creative north star. It is **not** a status document —
`CURRENT_STATE.md` stays the only status authority. It does **not** govern portfolio UI
(that is `Docs/DESIGN_SYSTEM.md`) or the technical build (that is
`Docs/Production/MELUSINA_FINAL_ENVIRONMENT_CONVERGENCE_GOAL.md`). This doc governs the
*feeling, the face, and the soul* the build and the portfolio both serve.
**Seed**: Capstone meeting with Paul Neale, 2026-10-20 — "full french."
**Revision note (2026-10-21)**: this document was unversioned until now — it existed only as
an untracked file on one working tree. It is now tracked. Its §4 meter statement was
corrected to match the single governing meter the build actually uses (see below), and its
§5 Zen Forest row now matches the build spec.

---

## 0. The one line

> **Melodia Melusina is a French cathedral-world where architecture is music and water
> remembers — the living legend of Mélusina, made into a place you can walk.**

Everything below is an explication of that sentence. If a future decision contradicts it,
the decision is wrong.

---

## 1. The mythic spine (mythos)

The world is built on the **real legend of Mélusina** (Melusine), recorded by Jean d'Arras
(*La Fleur des Histoires*, c. 1400). This is not invented lore — it is a 600-year-old French
tale that already names your anchor place. We are *adopting* it, not authoring from zero.

The legend, in its bones:

- **A water fairy.** Mélusina is daughter of a king and a fairy of the Fair Water; she is
  bound to a fountain/well. Where she appears, water follows.
- **She marries a mortal, Raymondin, at a well.** Their pact: he may have her, wealth, and
  many children — so long as he never seeks her on the **seventh day** (Saturday), the day
  she withdraws to her own nature.
- **She founds Maillezais.** The legend says she is seen and **heard singing in the cloister
  of Maillezais** like a nun. The abbey on the Poitou marsh is *her* building.
- **He breaks the pact. She transforms, and flees.** Discovering her secret, Raymondin
  betrays her; she does not die — she *becomes* the marsh's voice: a wailing, weeping presence
  who returns as a **harbinger of loss** for the house that betrayed her.

Why this is the world's spine — the legend already contains your systems:

| Legend | Your world, already built |
| :-- | :-- |
| Water fairy, bound to well & fountain | Canals, the Village Well, marsh, Sea Above, lock gates |
| **Sings in the Maillezais cloister** | Cathedral-as-instrument; arrows play the bells; Chladni resonance |
| Transformation on the **seventh day** | The FLOW ⇄ SEQUENCE duality; the intact ⇄ ruin decay slider |
| Harbinger of **loss**, the weeping return | The game's melancholy register; the abbey-as-ruin |
| Founding **abbey + castle** (Lusignan, Chauvigny) | The Poitou Romanesque ruins; the towers of Poitou |

**Melusina the heroine** is therefore an *avatar / echo of the fairy* — not a separate
character bolted onto a setting. She is the place remembering itself. She sings where stone
remembers a voice.

> **Open, owner-level (see §8):** how literally to bind the heroine to the legend — full
> incarnation, or a quiet echo. The legend is the *world's* soul regardless.

---

## 2. Tone (the feeling)

Three words that must always be true at once: **sunlit, reverent, grieving.**

- **Sunlit** — this is not dark fantasy. Golden 5500K afternoon through dust in a ruined
  nave. Hopeful, warm, *French light*. (Convergence spec: `Poitou_Sun` 45 lux, `#FFE8C8`.)
- **Reverent** — cathedral silence, the hush of standing in something older than you. The
  music is *played to the stone*, not performed at an audience.
- **Grieving** — under the light, the ache. A ruin is a building that loved something and
  lost it. The fairy who sings and is gone. This is the "little melancholic" that must never
  be smoothed out — it is the load-bearing emotion.

Restraint is the style. Whimsy lives in *precision* (the elastic-glass pluck, the crisp
tracery cusp), never in clutter or costume-fantasy. Wonder through **taste**, not excess.

**Sonic register (binds to `Docs/Audio/MELODIA_SONIC_IDENTITY.md`):** elastic glass — plucked
glass, silk strings, bouncy and intimate, dry. Melodic percussion, graded by intensity.
*Forbidden here as in the audio doc:* boomy impacts, orchestral swells, cinematic reverb
wash, metallic clang. The world feels like it sounds: a bell you can walk inside.

---

## 3. Look (the face)

The world's look is **French Romanesque-Gothic rising from water**, rendered in the
high-craft "stylized realism" tradition of Infold (*Infinity Nikki*): rigorous real
classical architecture, exaggerated for silhouette and light.

**What "the Infold tradition" means technically (researched 2026-10-22; provenance and
sources in `Docs/Research/INFINITY_NIKKI_ANIME_JRPG_ART_DIRECTION_2026-10-22.md`):**
Infold's own lead programmer describes their material system as *"a re-engineered fabric
algorithm that preserves the advantages of four-layer UV blending textures, while requiring
only minimal parameter adjustments"*. **Melodia already speaks that language** - the
four-layer toon blend and its `MF_ColorRamp3` / `MF_DF_ContactBlend` / `MF_ClothWindDrape`
functions are the same family of idea. So the look is not a new shader stack to build: it
is the existing one, used with the discipline Infold describes. A garment tier reuses the
four-layer blend driven by the wind lane; it does not introduce a second material
authority.

Two more of their rules, both adopted:
- **Fashion as narrative.** Infold: *"Each piece tells a story... It's fashion as
  narrative."* Here: a garment that carries no capability is **not yet Melodia clothing**
  (the wardrobe bar), and a room's clutter says who lived there rather than filling space.
- **Slow enough to breathe.** Infold's pacing note - *"we want to let players breathe and
  appreciate all the details"* - is the same argument as the P0 golden walk's ten-minute
  opening with 0:40 beats. The walk is the design, not a delay before the design.

**The signature image:** a limestone cathedral-ruin *rooted in a marsh* — pointed arches and
a rose window still standing, water lapping the foundation, pollard ash and reed bed in the
reflection, morning mist lifting off a canal toward a lime-washed village.

- **Materiality (real French referents, already in the repo):** `pierre de taille` limestone
  from Chauvigny / Saint-Maximin; deep rustication grooves (`refends`); standing-seam
  **zinc** and Angers **slate** roofs; lime-wash; oak; pollarded ash. Universal PBR
  `MI_Poitou_RuinStone`.
- **Ornament is acoustic.** This is the world's unique law — see §4. Chladni node-patterns
  into cornices, balustrades, tracery. Decoration is *frozen sound*.
- **Palette.** World-tone sits under the portfolio's plum / gold / ivory system
  (`Docs/DESIGN_SYSTEM.md`) but reads as *place*, not UI: warm limestone ivory, marsh green,
  lilac ambient bounce (`#8A93C8`), gold afternoon, deep plum shadow, slate water.
- **Light.** Golden directional sun + lilac sky-bounce + soft exponential height-fog mist.
  Light is the emotional dial: the same nave at dawn-mist and at golden-hour is two feelings
  of the same soul.
- **Zero slop.** No proxies, no floating boxes, no greybox in shipped lands. Nanite complex
  collision, ground-probed to the landscape. Craft is part of the feeling — a floating foot
  breaks the spell.

---

## 4. The architectural-music law (the unique mechanic-aesthetic)

> **"The architectural rhythm IS the music."** — Convergence spec §1.1

This is the one idea that makes Melodia Melusina *not another cathedral game*. It is already
built; this doc canonizes it as identity:

- **Bay cadence = musical meter.** **The governing meter is 0.6 m grid / 2.4 m bar /
  128 BPM 4/4** (1 beat = 0.469 s, 1 bar = 1.875 s, walk = 1.28 m/s). 2.4 m = one bar of
  4/4; 3.6 m = 6 beats = 1.5 bars of 4/4. Walking the nave is keeping time.
  *(2026-10-21: this replaces an earlier "2.4 m = allegro 3/4, 3.6 m = andante 4/4" phrasing
  that was internally inconsistent and disagreed with the build. The single governing
  statement lives in the build spec §1.1 and is the one both documents now defer to.)*
- **The building is an instrument.** Chimney stacks are hollow tuned resonators (`tuyaux
  d'orgue`); arrows released on the WaveHarp *play the bells* of the bell-garden; the rose
  window and the Chladni floor are standing-wave figures.
- **Decoration is frozen sound.** Cornice profiles and ironwork are drawn from real Chladni
  acoustic node equations (Dorian, 128 BPM in the Poitou recipe). What looks like ornament is
  a snapshot of a note.

So: **to build the world is to compose it.** Every architect is a musician here, and every
player who moves through the space is playing it.

---

## 5. The canonical lands

The world is a small number of deeply-authored French lands, each a movement of one piece.
(As-built in the Convergence spec §5; identities preserved, non-French lands flagged in §8.)

| Land | Movement | French anchor |
| :-- | :-- | :-- |
| **Poitou Abbey** — Sunlit Maillezais Sanctuary (`L_Poitou_v2`) | The chorus / the ruin that sings | Poitou-Charentes Romanesque, coastal marsh — *the fairy's own abbey* |
| **Melusina Morning** — Meadow Cantata (`L_MelusinaMorning`) | The overture / dawn | Breton coastal pastoral, dry-stone dikes, maritime pine |
| **Kaleido Nave** — Starlight Cathedral (`L_KaleidoNave`) | The nocturne / crystal | Rayonnant Gothic, refractive caustics (Gothic made of light) |
| **Zen Forest** — Tranquil Shaded Canopy (`L_ZenForestTest`) | *—* | **Japanese cedar — NOT French. NOT core canon pending owner decision; see open question §8.** |

The first three are already one French chord (Romanesque earth → pastoral dawn → Gothic
light). The fourth is the seam the "full french" shift must decide: until the owner decides,
Zen Forest is **neither core canon nor deleted** — it must simply not be described as one of
the canonical French lands. The build spec's §5 Level 4 now carries the same flag.

---

## 6. Do / Don't — keeping the lock

**Do**
- Ground every structure in a real French treatise (Vignola, Durand, Haussmann, Romanesque
  Poitou) *then* exaggerate for silhouette and light.
- Treat water as a character, never scenery. Wells, canals, marsh, fountain — the fairy's body.
- Let the melancholy breathe. A ruin is a love letter with a hole in it.
- Make ornament acoustic. If it's decoration, ask what note it is.
- Ship only high-craft, grounded, complex-collision geometry. Taste is the special effect.

**Don't**
- Cartoon-warp architecture or scatter disembodied musical notes as decoration (the spec's
  explicit refusal). The music is *in the structure*, not stickers on it.
- Import non-French pastiche (Japanese, generic "fantasy," Norse, Art-Deco) into the *core*
  lands. Other traditions may live in a clearly-labeled "beyond" tier, not the canon heart.
- Swap the house sonic material per hit (kills instrument identity) — graded intensity only.
- Let a foot hover over stone. Broken collision is a broken spell.
- Add a second cathedral language. One world, one voice.

---

## 7. How this doc relates to the others

```
        MELODIA MELUSINA — World Identity & Co-Identity  (this doc — who/why)
        ┌───────────────┬───────────────────┬──────────────────────┐
        ▼               ▼                   ▼
   CONVERGENCE      SONIC IDENTITY      DESIGN SYSTEM
   (the build/how)  (the sound)         (the portfolio face)
   Poitou Abbey     elastic glass       plum / gold / ivory
   Nanite collision graded-by-intensity artbook editorial
        │               │                   │
        └───────────────┴───────────────────┘
                 all three serve the same soul
```

This doc does not override any of them. It is the sentence they all complete.

---

## 8. Open decisions — for Brennan (and Paul)

These are the genuine creative calls this draft *proposes* and asks you to ratify, trim, or
rewrite. Nothing here is final until you sing "yes."

1. **The heroine & the legend.** Full incarnation (Melusina *is* the fairy, awake in the
   world) or quiet echo (she hums a melody the abbey remembers)? I lean **echo-with-teeth** —
   she doesn't monologue the myth, the world *is* the myth and she's the one who can hear it.
2. **Zen Forest.** Keep as a deliberate "other shore" (a dream/distant-land tier, explicitly
   not-French), translate it French (cedar → Aude cypress / Lorraine fir), or retire it from
   the canonical four? This is the biggest lever on "full french."
3. **The melancholy level.** How loud is the grief under the light? A lullaby with a ache, or
   a dirge most of the way that only brightens at the very end?
4. **Name of the world-as-world.** Is it "Melodia Melusina" (the game), or does the land
   itself want a name — *the Marsh*, *the Resonant Country*, *Poitou*? (A place-name sharpens
   every future pitch.)
5. **Tone words sign-off.** Do "sunlit / reverent / grieving" hold? Add or cut one?

---

## 9. Lineage

- Seed: Capstone meeting with Paul Neale, 2026-10-20 ("full french").
- Builds on: `MELUSINA_FINAL_ENVIRONMENT_CONVERGENCE_GOAL.md` (build),
  `Docs/Audio/MELODIA_SONIC_IDENTITY.md` (sound), `Docs/DESIGN_SYSTEM.md` (portfolio face),
  `Docs/Houdini/GOTHIC_GEOMETRY_REFERENCE_2026-10-05.md` (craft).
- Mythos source: the legend of Mélusina / Melusine (Jean d'Arras, c. 1400) and its real
  attachment to Maillezais, Lusignan, and the Poitou marsh — external reference, offered as
  proposal for Brennan to accept or reshape.
- This is v0.1. It lives and changes with the world. Next lock after §8 answers.
