# Zundamon ΓÇö Design Bible
## Character Integration for Melodia / Melusina Game Project

---

## 1. Character Identity

| Attribute | Value |
|-----------|-------|
| **Name** | Zundamon (πüÜπéôπüáπééπéô) |
| **Species** | Zunda Mochi Fairy |
| **Origin** | The Green East (Tohoku-analogue region) |
| **Age** | Appears young (ageless fairy) |
| **Height** | ~140cm (child-sized) |
| **Pronoun** | Boku (πü╝πüÅ) ΓÇö androgynous, slightly tomboyish |
| **Speech Quirk** | Ends sentences with "~na no da" (πü¬πü«πüá) |
| **Voice** | VOICEVOX Zundamon (speaker ID 3) ΓÇö childlike, high-pitched, energetic |
| **Birthday** | December 5th (canon) |
| **Hobby** | Wandering aimlessly, making mochi, acting important |
| **Weakness** | Extraordinarily unlucky (actually: uncontrolled dimensional magic) |
| **Weapon** | Zunda Arrow (πüÜπéôπüáπéóπâ¡πâ╝) ΓÇö a bow that fires magical mochi projectiles |
| **Signature Item** | Mochi Board (quest and shop interface) |
| **Designer** | Niniko Edomura (canon) |

### Appearance
- **Hair**: Short green hair with edamame-shaped hairclip/headband
- **Eyes**: Large, expressive, amber/gold
- **Outfit**: Green and white traditional Japanese-inspired fairy clothing with mochi motifs
- **Tail**: Small fairy tail (canon)
- **Human Form**: Capable of transforming between fairy/mochi form and humanoid form (canon since June 2021)

---

## 2. Legal & Licensing

| Dimension | Detail |
|-----------|--------|
| **Project** | Tohoku Zunko & Zundamon Project (ZunZun Project) |
| **Owner** | SSS LLC. |
| **Non-Commercial Use** | Completely free, no application needed |
| **Commercial Use** | Free for Tohoku-region registered companies. Non-Tohoku: separate license required |
| **Derivative Works** | Explicitly allowed. Creators retain rights to their own derivatives |
| **3D Model Modification** | Allowed and encouraged ΓÇö modify, retexture, redistribute freely |
| **Voice Use** | VOICEVOX: free for commercial and non-commercial use |
| **Attribution** | Not required but appreciated ("Tohoku Zunko & Zundamon Project") |
| **Guidelines** | https://zunko.jp/guideline.html |

> **For this project**: Non-commercial use (portfolio/demo) is fully covered. If the game goes commercial, a license discussion with SSS LLC. would be needed unless registered as a Tohoku business.

---

## 3. Lore Integration

### The Green East
The Green East is one of the seven directional realms in Melodia's cosmos. While Melusina guards the Astral Threshold (the boundary between all worlds), the Green East is a realm where food and magic are one and the same. Every dish is a spell. Every ingredient holds latent power. The Zunda mochi is the region's most sacred confection ΓÇö said to grant wisdom to those who consume it.

### How Zundamon Entered Melodia's Realm
Zundamon was the Green East's most enthusiastic (if clumsy) mochi merchant. One day, while experimenting with a new "dimensional mochi" recipe, her Zunda Arrow accidentally pierced a rift in reality. A single hyperactive mochi escaped through the portal. Zundamon chased it ΓÇö and found herself in Melodia's starting region, her arrow tangled in a sacred tree, three magical mochi scattered across the village square.

The Player meets her in this exact moment ΓÇö stuck, confused, and very hungry.

### Why She Stays
Zundamon discovers that her "bad luck" ΓÇö the constant tripping, the escaped mochi, the kitchen accidents ΓÇö is actually her innate dimensional magic leaking uncontrollably. The Green East's ambient magic normally stabilizes her. In Melodia's realm, without that stabilizing field, her power fluctuates wildly.

She stays because:
1. She can't go home until she stabilizes her power (late game quest)
2. She genuinely enjoys helping the Player (questkeeper role)
3. She's found a new market for her mochi (shopkeeper)
4. The Player's journey might be the key to controlling her abilities

### Connection to Melusina
- Both are **guardian beings** tied to specific regions/realms
- Both wield **magical archery** (Zunda Arrow / Melusina's celestial bow)
- Both are **dimensionally aware** ΓÇö they can sense the Astral Threshold
- Melusina recognizes Zundamon's leaking magic as similar to her own celestial energy
- Late-game dialogue: Melusina mentors Zundamon in power control
- Zundamon's comic misfortune is the tonal counterbalance to Melusina's dignified presence

---

## 4. Gameplay Role

### First NPC / Questkeeper
Zundamon is the **very first NPC** the player meaningfully interacts with after the tutorial. She serves as:
- **Tutorial bridge**: Teaches quest mechanics through her own comic misfortune
- **Quest hub**: Her Mochi Board is the game's quest interface
- **Early game shop**: Sells consumables and basic gear
- **Comic relief**: Periodic unlucky events that create mini-quests

### Quest Line (5 Quests)

| # | Name | Type | Trigger | Reward |
|---|------|------|---------|--------|
| 1 | **Mochi Retrieval** | Collect 3 escaped mochi in village | After freeing her from tree | 200g + 3x Zunda Mochi |
| 2 | **Kitchen Chaos** | Defeat slimes in her makeshift kitchen | Complete Q1 | 350g + Lucky Mochi |
| 3 | **Zunda Arrow Lost** | Retrieve her bow from nearby cave | Complete Q2 | Arrow Charm + shop discount |
| 4 | **Mochi Board Setup** | Gather materials to build her questboard | Complete Q1 | Unlock daily repeatable quests |
| 5 | **Power Unstable** | Help her stabilize her dimensional magic | Complete Q3 + late game | Zundamon joins as party member |

### Shop Inventory

| Item | Cost | Effect |
|------|------|--------|
| Zunda Mochi (Small) | 50g | Restore 30% HP |
| Matcha Mochi | 75g | Restore 20% MP |
| Intelligence Mochi | 200g | +15% EXP gain for 5 min |
| Zunda Arrow Charm | 500g | +10% Crit Rate (accessory) |
| Lucky Mochi | 100g | Random positive buff |
| Green East Silk | 300g | Crafting material |
| Dimensional Bean Paste | 25g | Cooking ingredient (quest item) |

### Mochi Rhythm Minigame (GMM Integration)
Inspired by real mochi-pounding (mochitsuki), a rhythm minigame where:
- Player presses buttons in time with Zundamon's calls of "Pettan! Pettan!"
- Successful pounding produces buff-granting mochi
- Missed beats produce "failed mochi" that still heal but with comedy debuffs
- Uses the existing GMM rhythm engine

---

## 5. Dialogue Personality Guide

### Speech Pattern
```
"Sentence... na no da!"
"Question... na no da?"

Examples:
  "I'm Zundamon, na no da!"
  "Mochi is the best food, na no da!"
  "Will you help me, na no da?"
```

### Emotional Range
| State | Behavior | Example |
|-------|----------|---------|
| **Happy** | Bouncing, tail wagging, "na no da!" emphasis | "Mochi time, na no da!" |
| **Confused** | Head tilt, finger on chin | "Where did that mochi go, na no da...?" |
| **Unlucky** | Tripping, dusting off, sighing | "I fell again, na no da..." |
| **Determined** | Clenching fists, eyes sparkling | "I'll protect everyone, na no da!" |
| **Embarrassed** | Looking away, fidgeting | "Don't look at me when I'm clumsy, na no da..." |
| **Proud** | Chest puffed, hands on hips | "My mochi is the best in all the realms, na no da!" |

### Relationship Arc with Player
1. **Stranger** (Quest 1): Grateful but formal. "Thank you, na no da!"
2. **Friendly** (Quest 2-3): Comfortable, joking. "You're the best customer, na no da!"
3. **Trust** (Quest 4): Opens up about her power. "I can tell you my secret, na no da."
4. **Partner** (Quest 5+): Loyal companion. "Where you go, I go, na no da!"

---

## 6. Technical Asset Manifest

### Already On Disk
```
F:\Inbox\...\Zundamon\
Γö£ΓöÇΓöÇ Zundamon.vrm              Γ£ô VRM model (17.2 MB)
Γö£ΓöÇΓöÇ Zundamon.fbx              Γ£ô FBX export (1.9 MB)
Γö£ΓöÇΓöÇ zundamon.pmx              Γ£ô MMD source model (2.8 MB)
Γö£ΓöÇΓöÇ zundamon_005.blend        Γ£ô Blender scene (9.5 MB)
Γö£ΓöÇΓöÇ Zundamon.unitypackage     Γ£ô Unity package (35.3 MB)
ΓööΓöÇΓöÇ Textures (15 PNGs)        Γ£ô All texture maps
```

### Copied to Unreal Project
```
BS_GodFile/Content/Melodia/Characters/Zundamon/
Γö£ΓöÇΓöÇ Zundamon.fbx              Γ£ô (1.9 MB)
ΓööΓöÇΓöÇ Textures/ (15 PNGs)       Γ£ô (3.5 MB total)
```

### Scripts Written
```
BS_GodFile/Content/Python/import_zundamon.py    Γ£ô UE import script
BS_GodFile/Tools/generate_zundamon_voice.py      Γ£ô VOICEVOX batch generator
BS_GodFile/Content/.../zundamon_dialogue.json    Γ£ô 20 voice lines (Japanese)
BS_GodFile/Docs/ZUNDAMON_NPC_SPEC.md             Γ£ô Blueprint specification
```

### Still Needed
```
[ ] VOICEVOX installation (voicevox.hiroshiba.jp)
[ ] Run import_zundamon.py in UE console
[ ] Create physics asset for SK_Zundamon
[ ] Create IK Rig for skeleton retargeting
[ ] Create Animation Blueprint ABP_Zundamon
[ ] Create Behavior Tree BT_Zundamon_NPC
[ ] Create Blueprint BP_Zundamon_NPC
[ ] Generate WAV files via generate_zundamon_voice.py
[ ] Import WAVs to Unreal Audio folder
[ ] Create Mochi Board quest UI widget
[ ] Create shop UI widget
```

---

## 7. Implementation Order

```
WEEK 1: Import & Setup
  [1] Run import_zundamon.py ΓåÆ SK_Zundamon + textures in UE
  [2] Create physics asset
  [3] Assign materials to mesh slots
  [4] Install VOICEVOX ΓåÆ generate voice WAVs
  [5] Import WAVs to UE

WEEK 2: Animation & Blueprint
  [6] Import MMD motion data ΓåÆ idle, walk, greet anims
  [7] Create ABP_Zundamon Animation Blueprint
  [8] Create BP_Zundamon_NPC Blueprint
  [9] Write behavior tree BT_Zundamon_NPC

WEEK 3: Quest & Shop Systems
  [10] Create quest data table DT_ZundamonQuests
  [11] Create shop inventory data asset DA_ZundamonShop
  [12] Build Mochi Board quest UI widget
  [13] Build shop UI widget
  [14] Wire dialogue system to voice lines

WEEK 4: Polish
  [15] Mochi rhythm minigame prototype
  [16] Zundamon unlucky event randomizer
  [17] Late-game power stabilization quest
  [18] Playtest & balance shop prices
```
