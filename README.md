# 𝄞 Melodia Melusina 𝄞

![Melodia Banner](Docs/melodia-banner.svg)

![Unreal Engine 5.8](https://img.shields.io/badge/Unreal_Engine-5.8_%2B_C%2B%2B-informational?logo=unrealengine&logoColor=white&color=0a1929)
![Blender 5.2](https://img.shields.io/badge/Blender-5.2_LTS-critical?logo=blender&logoColor=white&color=e87d0d)

### ♪ an evergreen single-player Rhythm-JRPG about fashion, music, impossible ecology, and the places that answer back

> **The beautiful things are not rewards around the game. They are how the game is played.**

Melodia is a turn-based fantasy RPG built in Unreal Engine 5.8. Rhythm is how actions are executed. Clothing is build identity and a language the world can read. Exploration, music, creatures, water, fabric, ecology, and ornament are allowed to become mechanics instead of staying scenery.

The long-term idea is simple:

> **Finish a real journey. Let the world keep growing after it.**

Melodia is not being built as a battle-pass treadmill or an always-online obligation. A Volume should have a real ending. Later, I can add another Voyage, Reverie, outfit, creature, letter, tiny gift, strange island, or entire new sea because I had a good idea — not because a calendar says I owe the game content.

---

## ♪ The skeleton under the pretty stuff

```text
Turn-based strategy      = the skeleton
Rhythm execution         = performance
Wardrobe / outfits       = build identity + world relationship
Convergence              = interpretation between systems
Starskiff                = travel + accumulated journey
QuillScript              = narrative progression
Persistence              = memory
```

The project already contains a working Phoenix / TurnBased JRPG scaffold, battle-integrated Melodia rhythm systems, Wardrobe gameplay state, Quill/narrative progression, save/load infrastructure, Starskiff work, music-as-key world interaction, reusable validation tooling, and a growing browser R&D surface.

The rule now is **stop rebuilding the skeleton and make it survive the journey.**

---

## ♫ What Melodia is becoming

I think of the game as **a place**, not a content conveyor belt.

```text
MELODIA MELUSINA
│
├── Volume I — a complete journey
│   ├── Movements
│   ├── Chapters
│   ├── Episodes
│   ├── Reveries
│   └── rare Monolith Events
│
├── Gifts / letters / little returns
├── new Voyages
└── future Volumes, if there is more journey to make
```

A player should be able to disappear for a year, come back, and feel welcomed rather than punished.

> *A parcel arrived on the Starskiff while you were away.*

That is much closer to the feeling I want than **CLAIM REWARD: 03:41:19 REMAINING**.

Canonical strategy lives here:

1. [`Docs/Strategy/MELODIA_ENDLESS_JOURNEY_NORTH_STAR_2026-09-02.md`](Docs/Strategy/MELODIA_ENDLESS_JOURNEY_NORTH_STAR_2026-09-02.md) — ♪ the long-term game-as-a-place north star.
2. [`Docs/Strategy/MELODIA_CHAPTER_TIER_AND_VOLUME_ARCHITECTURE_2026-09-02.md`](Docs/Strategy/MELODIA_CHAPTER_TIER_AND_VOLUME_ARCHITECTURE_2026-09-02.md) — ♫ Reveries → Episodes → Chapters → Movements → Monolith Events → Volumes.
3. [`Docs/Strategy/MELODIA_EVERGREEN_CONTENT_AND_GIFT_MODEL_2026-09-02.md`](Docs/Strategy/MELODIA_EVERGREEN_CONTENT_AND_GIFT_MODEL_2026-09-02.md) — ♬ Gifts, mail, archives, Voyages, and the no-FOMO rule.
4. [`CURRENT_STATE.md`](CURRENT_STATE.md) — what is actually real today.
5. [`TODO.md`](TODO.md) — what we are actually doing next.

---

## ♬ Runtime authority — one truth per thing

The project gets more ambitious only if ownership gets less confusing.

| Thing | Owner |
|---|---|
| turns, targeting, battle resolution, stock JRPG state | Phoenix / TurnBased JRPG |
| narrative flags, intents, checkpoints, consequences | `UMelodiaNarrativeSubsystem` + QuillScript |
| timing / note-highway execution | Melodia rhythm / `MelodiaCore` |
| owned + equipped wardrobe state | `UMelodiaWardrobeSubsystem` |
| interpretation across outfit × rhythm × battle × world | Convergence |
| player-facing UI writes | `UMelodiaUIBridgeSubsystem` |
| durable Melodia history | canonical save + narrative record |

Rhythm may change **how well** an authored action happens. It does not become a second combat game.

Convergence may interpret relationships. It does not become a junk drawer that owns everybody else's state.

A 3D parcel may look like it contains an outfit. It still cannot grant the outfit by itself.

---

## 𝄞 The current golden proof

P0 / First Dream + Sea Above remains our useful full-stack song:

```text
Outfit
→ Starskiff / exploration
→ Phoenix command
→ Rhythm phrase
→ Convergence / world consequence
→ Reward
→ Save
→ Quit process
→ Relaunch
→ Load
→ same durable state
→ Load again
→ no duplication or drift
```

That is an **integration proof**, not mandatory pacing for every future Chapter.

A Reverie can be ten quiet minutes on the Starskiff. A creature story can use music without battle. A Monolith Event can end in traversal or world-state intervention instead of enemy HP.

The reusable thing is the contract, not the shape of the story.

---

## ♪ Current work

Right now the high-value work is boring on purpose:

- persistence / restore invariants;
- repeat-load idempotency;
- durable Starskiff + Convergence ownership;
- packaged restart proof;
- reusable Chapter packages;
- keeping old saves readable as the world grows.

**Do not** solve this by rewriting Phoenix, inventing another SaveGame authority, persisting live rhythm sessions, or building a remote gift backend before the local game is reliable.

The dream gets to be enormous because the boring parts are allowed to stay boring.

---

## ♫ Browser playgrounds

The repo now has a few deliberately non-authoritative Three.js laboratories. They are for seeing ideas quickly, not replacing Unreal.

- [`Docs/Tools/puzzle-sandbox/index.html`](Docs/Tools/puzzle-sandbox/index.html) — **𝄞 Cymatic Sanctuary**, a 12-instrument Music-as-Key sandbox with resonant phrase gates and JSON export.
- [`Prototypes/Web/MusicKey3D/`](Prototypes/Web/MusicKey3D/) — watercolor / toon world-puzzle interaction lab.
- [`Prototypes/Web/MelodiaFolio3D/`](Prototypes/Web/MelodiaFolio3D/) — Traveling Folio, Starskiff post, real repo-model turntable, and cozy 3D UI experiments.
- [`Prototypes/Web/MelodiaFolio3D/mara.html`](Prototypes/Web/MelodiaFolio3D/mara.html) — Mara-style presentation variant.

Run them from the repo root:

```powershell
python -m http.server 8080
```

Then browse the relevant path under `http://127.0.0.1:8080/`.

---

## ♬ Content grows in different sizes

| Scale | What it is allowed to do |
|---|---|
| **Reverie / Interlude** | intimate character, outfit, creature, sanctuary, or Starskiff story; heavy reuse |
| **Episode** | one memorable gameplay proposition |
| **Chapter** | meaningful authored change; at most one major mechanical extension |
| **Movement** | recombine existing systems into a new grammar |
| **Monolith Event** | break one assumption the player thought was safe |
| **Volume** | emotionally complete game-scale journey |

The working Volume-I scaffold supports 50+ named Chapters, but the point is **many authored memories**, not fifty new global systems.

---

## ♪ Toolchain

The center of gravity is Unreal Engine 5.8 + Houdini + Blender 5.2 LTS + SpeedTree / Substance / ZBrush and supporting tools where they genuinely help.

The test for every shiny new thing is still:

> **Does this make visibly better Melodia per hour without creating a more expensive maintenance problem?**

Music can author geometry offline. Houdini can author impossible evidence. Browser prototypes can test interaction and presentation. Unreal still owns the game.

---

## ♫ Repository map

| Directory | What lives there |
|---|---|
| `Source/BS_GodFile/` | native gameplay + integration |
| `Plugins/MelodiaCore/` | rhythm / presentation foundations |
| `Plugins/MelodiaWardrobe/` | wardrobe implementation |
| `Content/Melodia/` | characters, levels, UI, authored game content |
| `Content/EnvSandbox/` | environments, Monolith work, materials, procedural lookdev |
| `specs/` | progression + stable data contracts |
| `Tools/` | tests, audits, authoring automation |
| `Docs/Strategy/` | current product/content north stars |
| `Docs/Tools/` | small browser/tool experiments worth keeping |
| `Prototypes/Web/` | Three.js interaction + UI laboratories |

Bulk art remains governed by the project's Git/LFS/Perforce rules. Code, specs, and documentation stay Git-authoritative.

---

## 𝄞 Start here

For setup and validation commands: [`QUICKSTART.md`](QUICKSTART.md)

For the shortest useful reading path:

```text
README
  ♪
Endless Journey North Star
  ↓
CURRENT_STATE
  ↓
TODO
  ↓
SYSTEM_MAP / DATA_FLOW
  ↓
the Chapter, tool, or system you are actually touching
```

---

## ♬ License & provenance

Original repository source, tools, and configurations are MIT licensed; third-party assets retain their own licenses and provenance requirements.

- [`LICENSE`](LICENSE)
- [`Docs/CREDITS.md`](Docs/CREDITS.md)
- [`Docs/SOURCES_MATRIX.md`](Docs/SOURCES_MATRIX.md)

---

> **Melodia is not a game that never ends because it refuses to finish. It is a journey that can keep finding new places after an ending.** ♪
