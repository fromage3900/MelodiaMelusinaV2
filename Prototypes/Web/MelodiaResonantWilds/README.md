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
- **Open world.** Five biomes from the Gaea world-gen setups sit around Shorewake Village, each with its own tempo, meter, key and style:
  - Petal Cantata: waltz, 3/4
  - Liquid Cathedral: organ, 4/4
  - Fugue Grotto: subject and answer, 4/4
  - Cadence Cathedral: toccata, 4/4
  - Aurora Glacier: glacial, 4/4

  The score changes on the next bar line when you cross a border.
- **Things to do:**
  - Slime camps, which respawn
  - Elite Chorus events
  - Chests
  - Lost Sheet Music, which teaches skills
  - Pylons for fast travel
  - Music-key shrines: call and response, where you answer the shrine's phrase on the next bar
  - Biome **Maestros** (world bosses) with toughness **BREAK**
  - **Resonance Rifts**: tiered, infinite and timed, with DT_Burdens at tier 3+
  - The **Movement** chain: one per biome, which gives new players a direction
- **Gear.** Items fill the Wardrobe slots (instrument, headpiece, gown, gloves, shoes, charm). There are five rarities, Common → Opus. Opus items carry an **Aria** from DT_Artifacts and the authored rhythm-skill DataAssets. The **Forge** hones gear +1…+15 with falling odds and banked pity. Salvage turns spare gear into gold and shards, and gear score gates what you can take on.
- **Retention hooks:**
  - Bounties (3 claimed = Chorus Cache)
  - Blessings bought with Golden Notes (DT_Blessings)
  - Shrine attunement: +1% damage each
  - Exploration fog on the map
  - An idle reward from your Choral Sheep when you return
  - Everything saves to `localStorage`

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

`js/audio.js` beat clock and procedural score · `js/rhythm.js` judging, combo, Crescendo, Encore · `js/world.js` streamed terrain, biomes, props, landmarks, water, rift arena · `js/chibi.js` Melusina (code-built chibi, posed from game state) · `js/entities.js` sheep, slimes, boss phrases · `js/combat.js` damage, skills, projectiles · `js/loot.js` items, forge · `js/activities.js` camps, shrines, bosses, events, rifts · `js/progress.js` save, XP, bounties, exploration · `js/ui.js` HUD, touch controls, panels · `js/game.js` loop.

Terrain follows the idea in [OpenWorldJS](https://github.com/obecerra3/OpenWorldJS): tiles centred on the player and streamed from a noise heightmap with biomes. Here the tiles are small CPU chunks with analytic normals, so they are cheap on phones. Beat ripples and the Crescendo glow are injected into the terrain and water shaders.

## 🧁 Melusina (code-built chibi)

`js/chibi.js` builds her from primitives. The look follows the Melusina chibi sprite sheet and pixel art:

- lavender wavy hair with side and back locks, a fringe and purple hair clips
- a pink flowered beret, a lavender heart vest with a pink neck bow
- pink puff sleeves and long pink gloves
- a cream-and-pink skirt with a navy ruffle and a white treble-clef emblem
- dark-brown skin, big purple eyes, pink lace-up boots with white socks

She is posed every frame from game state: run cycle, beat-locked bounce, attack swing, V-arm cast, dash lean, hurt flinch and blinking. Wardrobe gear recolours her skirt, and the circlet, gold boot cuffs and lyre/baton toggle through the same fields as before.

## 📦 Playable folder for a website section

`dist/` is the whole game in one static folder. Rebuild it after any change:

```powershell
python Prototypes/Web/MelodiaResonantWilds/tools/build_dist.py
```

Copy `dist/` into your site as `/resonant-wilds/` and embed it:

```html
<iframe src="/resonant-wilds/index.html" width="100%" height="520" style="border:0" allow="autoplay" title="Melodia — Resonant Wilds"></iframe>
```

## 🎨 Next steps in ChatGPT (image prompts)

Use these to keep iterating on the design before the next model pass.

**1. Front reference, matched to the sprite sheet**
```
Full-body chibi reference of "Melusina" for a mobile rhythm game, 2.5 heads tall, soft toon shading, matte collectible-toy finish. Long wavy lavender hair with pale iridescent highlights, side and back locks reaching the waist, a fringe with two purple hair clips. A pink flowered beret tilted to one side. Dark warm-brown skin, big purple eyes with white highlights, small smile, rosy cheeks. Lavender vest with a small pink heart, pink bow at the neck, pink puff sleeves, long pink gloves. Pink skirt over a cream petticoat, navy ruffle at the hem, white treble-clef emblem on the front. Pink lace-up boots with white socks. Symmetrical A-pose, plain white background, no shadows, no text.
```

**2. Pose sheet matching the code animations**
```
Chibi sprite sheet of the same character, six poses in a 3x2 grid on a plain background, same scale and baseline: idle, run cycle, attack with a gold lyre-bow raised to one side, cast with both arms raised out in a V, dodge leaning forward, hurt flinch with a small sweat drop. Keep the outfit, colours and hair identical in every frame.
```

**3. Beret and flower icon for the HUD**
```
Round game icon, 256 px: a pink flowered beret with a small gold centre flower, soft toon shading, dark plum outline, transparent background.
```

**4. Rhythm telegraph art**
```
Set of three flat ground-warning rings for a rhythm action game, pastel pink, lavender and gold, thin outline, transparent background, readable on dark and light terrain. One solid ring, one dashed ring, one cone.
```

Send the results back and I'll wire them in.
