# ♪ Melodia — Resonant Wilds

A mobile-first open-world **rhythm ARPG** in three.js. It plays like a Lost Ark / Diablo loop: kill, loot, gear up, push harder content. Every swing, skill, dodge and enemy attack lands on the beat.

It runs on the Melodia UE project's own data. The rules, skills, enemies and biomes come from the UE files through `tools/export_ue_data.py`. It is a browser prototype and does **not** own the game.

---

## ▶ Run it

Serve the repo root (ES modules need http, not `file://`):

```powershell
python -m http.server 8080
```

Open `http://127.0.0.1:8080/Prototypes/Web/MelodiaResonantWilds/` on a phone (same Wi-Fi, use the PC's IP) or a desktop browser. Landscape is best on phones. Headphones help. If taps feel late, use **Settings → Calibrate**. Bluetooth audio usually needs +150–250 ms.

No build step. three.js r170 is vendored in `vendor/` (MIT, licence alongside).

## 🎮 Controls

| Touch | Keys | |
|---|---|---|
| Left thumb, anywhere | WASD / arrows | Move |
| ⚔ (hold = auto on each beat at ×1.0) | Space / J / left click | Basic attack; tap it as the ring closes |
| Four skill buttons | Q E R F or 1–4 | Skills (cost Harmony ◆, cooldowns in beats) |
| ⤳ | Shift / right click | Dodge. On the landing beat it becomes a **Perfect Dodge** |
| ENCORE | T / C | Ultimate: ×3 burst, then two bars of guaranteed Perfects |
| Gold pill | X / Enter | Interact (forge, bounties, font, rift, shrine, Maestro, pylon) |
| Menu row | I K M B | Wardrobe · Skills · Map (fast travel) · Bounties |

## 🔁 The loop

- **Rhythm language.** Taps are graded against the beat you actually hear, using Web Audio output latency plus a calibration offset. Grades are PERFECT / GREAT / GOOD / MISS. On-beat hits build a combo and a **Crescendo** meter shown as dynamics (pp → p → mf → f → ff), which raises crit and move speed. They also fill **Encore** and refund **Harmony**. Slimes hop on the beat. Their attacks are telegraphs that land on a counted beat (elites and bosses count "3, 2, 1" aloud).
- **Open world.** Eight biomes sit around Shorewake Village on a **2×** map (radius 1400). Each has its own tempo, meter, key, ethereal score style, and a continuous **region ambience** bed:
  - Petal Cantata: soft waltz, 3/4
  - Liquid Cathedral: choral nave, 4/4
  - Mist Choir (Choir Marsh): choir pads, 4/4
  - Fugue Grotto: subject and answer, 4/4
  - Glass Orchard: crystalline bells, 4/4
  - Cadence Cathedral: glass toccata, 4/4
  - Starlit Moor: high-bell drone, 4/4
  - Aurora Glacier: glacial shimmer, 4/4

  The score changes on the next bar line when you cross a border; ambience crossfades immediately. Explore mixes are pad-led; combat still lifts drums without leaving the ethereal identity.
- **Things to do:**
  - Slime camps, which respawn
  - Elite Chorus events
  - Chests
  - Lost Sheet Music, which teaches skills
  - Pylons for fast travel
  - Music-key shrines: call and response, where you answer the shrine's phrase on the next bar
  - Biome **Maestros** (world bosses) with toughness **BREAK**
  - **Resonance Rifts** (Recitals): tiered, infinite and timed, with DT_Burdens at tier 3+
  - The **Movement** chain: one per biome, which gives new players a direction
- **Gear.** Items fill the Wardrobe slots (instrument, headpiece, gown, gloves, shoes, charm) with SVG icons. Five rarities, Common → Opus. Opus items carry an **Aria** from DT_Artifacts and the authored rhythm-skill DataAssets. Gear score gates what you can take on.
- **Harmonic Synthesis (Atelier / cymatics).** Salvage always yields **Motifs** (element materials) plus gold/shards. At the Forge, spend Motifs into Chladni **cymatic loops** to raise Synthesis Quality and transfer Motifs as traits. **Temper** (hone +1…+15 with pity) is the follow-up step. Opus Aria = Super Trait slot.
- **Echo Lineage (Uma inheritance).** Clearing a Rift banks a residual Phrase. The next Recital shows pass chance (Arias + Blessings as Score Supports, plus pity). Inherited Motifs buff that run only — re-clear to breed a stronger Echo.
- **Retention hooks:**
  - Bounties (3 claimed = Chorus Cache)
  - Blessings bought with Golden Notes (DT_Blessings)
  - Shrine attunement: +1% damage each
  - Exploration fog on the map
  - An idle reward from your Choral Sheep when you return
  - Staged **Rift Clear** reward reveal
  - Everything saves to `localStorage` (`melodia_resonant_wilds_v2`, migrates from v1)

## 🧬 What comes from UE

| Web game | UE source |
|---|---|
| Timing windows 90/120/160 ms, grade multipliers, combo bonus, Harmony (SP 3/5), Crescendo gains, Encore gains and ×3, toughness, element wheel (×1.5 / ×0.5), modifiers (Crescendo_Minor, HasteDance, GuardHymn, TempoBreak, ResonantFocus) | `Plugins/MelodiaCore/Rules/melodia_rules.json` |
| 31 skills: element, tier, SP cost, power, MIDI note chart (played when you cast) | `Content/Melodia/DataStuctures/DT_MelodySlime_Skills.json` |
| 48 slimes: HP, toughness, damage, speed, element, BPM (sets attack cadence) | `DT_MelodySlime_Enemies.json` |
| Opus arias, Blessing Font, rift Burdens, element shards | `DT_Artifacts.json`, `DT_Blessings.json`, `DT_Burdens.json`, `DT_MelodiaTokens.json` |
| Biomes: name, seed 3900, terrain recipe (terrace strength, flow, lakes, radial gradient, height range), musical binding | `Docs/WorldGen/GAEA_SETUP_*.json` |
| Choral Sheep **Harmonize**, Wardrobe slots, music-as-key shrines | the proven UE seams in `CURRENT_STATE.md` |

Regenerate after changing any of those files:

```powershell
python Prototypes/Web/MelodiaResonantWilds/tools/export_ue_data.py
```

`js/design.js` holds only what the ARPG adds on top: how each skill is delivered, biome tempos and palettes, loot tables, bounties.

## 🗂 Files

`js/audio.js` beat clock and procedural score · `js/rhythm.js` judging, combo, Crescendo, Encore · `js/world.js` streamed terrain, biomes, props, landmarks, water, rift arena · `js/entities.js` Melusina, sheep, slimes, boss phrases · `js/combat.js` damage, skills, projectiles · `js/loot.js` items, Motifs, Harmonic Synthesis, temper · `js/echo.js` Echo Lineage · `js/activities.js` camps, shrines, bosses, events, rifts · `js/progress.js` save, XP, bounties, exploration · `js/ui.js` HUD, touch controls, panels, rift reward reveal · `js/game.js` loop · `assets/icons/` SVG icon pack + `manifest.json`.

UI frames live in Figma: [Resonant Wilds Web UI](https://www.figma.com/design/Vin9X81mAyJ4GQIjGBmzcI).

Terrain follows the idea in [OpenWorldJS](https://github.com/obecerra3/OpenWorldJS): tiles centred on the player and streamed from a noise heightmap with biomes. Here the tiles are small CPU chunks with analytic normals, so they are cheap on phones. Beat ripples and the Crescendo glow are injected into the terrain and water shaders.
