# Paul Neale / Melodia Capstone Rehearsal Sheets

**Date:** 2026-09-09  
**Status:** ACTIVE STUDY PACK  
**Use:** Read aloud, rehearse without notes, then answer the drill questions in random order.

---

# SHEET 1 — 30-second opening

> **Melodia Melusina is an environment-led musical fantasy game I'm building in Unreal Engine 5.8. The player explores, encounters musical interactions and rhythm challenges, gains expressive abilities, and then uses those abilities to change how the world can be traversed. Over the summer I focused on turning the visual idea into a playable structure while developing the environments, materials, instruments, animation, and music-responsive visual language that make the world feel like Melodia.**

Goal: say this calmly in 25–35 seconds without sounding memorized.

---

# SHEET 2 — 90-second project explanation

> **The main design idea is that expression should have consequences in the environment. A music interaction isn't meant to sit beside exploration as a separate minigame. A successful musical action can produce a reward, that reward can change wardrobe or capability state, and the environment can respond by opening a traversal option.**
>
> **I deliberately did not build every low-level system from scratch. The Turn-Based jRPG Template from Phoenix Market is the mechanical combat foundation, Harmonix supplies musical-time and MIDI semantics, and QuillScript supports the narrative authoring side. My work is adapting those pieces into Melodia, building the Blueprint and content integration around them, and authoring the world, materials, instruments, creatures, and visual feedback.**
>
> **The capstone version compresses that idea into the Choral Sheep: creature, motif, harmony, world. A sheep carries a musical identity, multiple sheep form a harmonic relationship, and that harmony becomes something the environment can visibly respond to.**

---

# SHEET 3 — What did YOU build?

Answer:

> **My strongest authorship is the world and integration layer: environment design, lookdev, materials, instruments, Blueprint assembly, gameplay-facing interaction, music-reactive presentation, and the way those pieces are composed into a playable route. I also developed custom C++ and tooling with substantial coding assistance, but I'm not claiming that I personally hand-authored every framework implementation.**

Shorter version:

> **I designed the experience, authored the world and presentation, and integrated the systems that make those things behave together.**

Never say:

> “I just stitched some Blueprints together.”

Integration is work. Describe the decisions and result.

---

# SHEET 4 — Third-party systems attribution

## Phoenix / Turn-Based jRPG Template

**What is it?**  
Purchased mechanical foundation for turn-based JRPG behavior.

**What do I say?**

> **Phoenix gives me the mature JRPG mechanical base. I adapt and present it as Melodia instead of rebuilding party, turns, battle, skills, quest, and save behavior from zero.**

## Harmonix

**What is it?**  
Unreal musical-time / MIDI layer.

**What do I say?**

> **Harmonix gives me an authored musical clock and MIDI semantics so rhythm and visual effects can share musical timing.**

**Do NOT say:** “Harmonix is the main code.”

## QuillScript

**What is it?**  
Narrative authoring / integration foundation.

**What do I say?**

> **QuillScript gives me a structured narrative authoring layer that I can connect to the Unreal world.**

## MelodiaCore

**What is it?**  
Custom C++ plugin / R&D and integration code.

**Current safety fact:**  
Do **not** call it the authoritative battle/save foundation. The repo currently quarantines MelodiaCore as gameplay authority because of prior runtime instability.

**What do I say?**

> **MelodiaCore is custom project C++ I developed with substantial coding assistance. I use or salvage bounded integration/presentation pieces from it, but the proven JRPG framework remains the mechanical authority.**

---

# SHEET 5 — The gameplay loop from memory

Draw this without looking:

```text
EXPLORE
   ↓
INTERACT / DISCOVER
   ↓
MUSIC / ENCOUNTER
   ↓
RESULT
   ↓
REWARD
   ↓
WARDROBE / CAPABILITY
   ↓
WORLD ACCESS CHANGES
   ↓
CHECKPOINT
   ↺
```

Then say:

> **The point is that the player returns to exploration with changed state, so the same world can mean something different after musical progression.**

---

# SHEET 6 — One concrete technical flow

Memorize the current First Dream example:

```text
music challenge completion
→ reward.first_resonance_echo
→ wardrobe grant
→ Accessories equip
→ Glide capability
→ traversal portal unlock
```

Explain in human language:

> **A musical success causes a persistent gameplay reward. The wardrobe system equips the relevant state, that state grants Glide, and the environment checks the capability rather than hard-coding a special-case door.**

If asked “why does that matter?”:

> **It makes the environment reusable and systemic. I can author multiple world interactions around a capability instead of scripting every level beat independently.**

---

# SHEET 7 — Blueprint vs C++

Question: **Why use C++ at all?**

> **For stable reusable contracts and systems that multiple pieces of content need to access consistently. Blueprint stays my main artist-facing composition layer.**

Question: **Why not do everything in C++?**

> **Because a large part of this project is authored content and iteration. Blueprint is much faster and more legible for assembling level behavior, VFX, animation, references, and presentation.**

Question: **Did you write this C++ yourself?**

> **I developed it with substantial coding assistance. I can explain the responsibilities and the interfaces I actively use, but I don't claim hand authorship of every implementation detail.**

Question: **What does this class do?**

Use:

> **I would want the class open before describing the exact implementation, but its responsibility in the project is ___, and the part I interact with is ___.**

---

# SHEET 8 — Choral Sheep

Memorize:

> **Creature → Motif → Harmony → World**

## Creature

Must be appealing at rest. Art works before tech explanation.

## Motif

Pitch identity becomes material / bell / fleece information.

## Harmony

C + E + G creates a readable group state.

## World

The environment responds to that resolved relationship.

One-line thesis:

> **A creature carries musical identity, and musical relationships become world relationships.**

If asked why sheep:

> **Because they make an abstract music system emotionally readable. I can show the idea first as character behavior, then reveal the technical structure underneath it.**

---

# SHEET 9 — Chladni / cymatics

Question: **What is a Chladni pattern?**

> **It is a visible standing-wave pattern on a vibrating surface. At resonant modes, particles collect around nodal regions where the surface moves very little.**

Question: **Does every frequency produce one fixed shape?**

> **No. The pattern also depends on surface geometry, material properties, boundary conditions, and the resonant mode.**

Question: **Are you physically simulating that exactly?**

> **Not necessarily. I'm using the physics as a visual grammar and then authoring or evaluating patterns that are useful for real-time materials and effects.**

Question: **Where does it go in the art?**

> **Roughness, emissive, displacement, embroidery, Niagara masks, water patterns, decals, and environmental resonance.**

---

# SHEET 10 — TouchDesigner

Question: **Why TouchDesigner if the game is in Unreal?**

> **Because TouchDesigner is a very fast real-time visual laboratory. I can explore signal-to-image ideas there without making it part of gameplay authority, then either capture those graphics for presentation or rebuild the successful effect in Unreal.**

Memorize:

- CHOP = channels / time signals
- TOP = textures / images
- SOP = geometry
- DAT = data / text / scripts
- COMP = reusable component / network

One-line boundary:

> **Unreal is the game; TouchDesigner visualizes; After Effects assembles.**

---

# SHEET 11 — Environment design answer

Question: **How is this still environment design if there are gameplay systems?**

> **The systems exist so that the environment can communicate and respond. My spaces aren't only backgrounds: they contain traversal affordances, musical interactions, landmarks, gates, encounter spaces, and visible world-state changes. The technical work lets those environmental decisions become interactive.**

Question: **What is the art-direction goal?**

> **I want musical structure to feel embedded in the world rather than overlaid as generic rhythm UI. Materials, silhouettes, lighting, creatures, architecture, and VFX all participate in the same resonance language.**

---

# SHEET 12 — 3ds Max oral defense

Question: **Why are you using Blender/Houdini instead of Max?**

Do not get defensive.

Say:

> **My existing procedural environment pipeline is already productive in Blender and Houdini, so I don't want to replace working tools for arbitrary reasons. I do want a meaningful Max lane, and the Resonance Astrolabe is a good fit because it needs hierarchical mechanical animation and controller-driven rigging.**

Question: **What would you actually do in Max?**

> **Build the instrument rig, define constrained ring and needle relationships, expose high-level controls like pitch or resonance, animate it, then bake/export the result into Unreal.**

Question: **Why is that useful?**

> **It gives Max a specialist technical-animation role with a clear game consumer rather than duplicating an environment workflow I already have.**

Backup niche:

> **I can also use Max as an asset-validation/finalization station for pivots, transforms, smoothing, UV checks, naming, collision, and UE export.**

---

# SHEET 13 — Evidence words

Know these exactly.

**Source-built**  
It exists and compiles.

**Live-proven**  
I saw it work in intended runtime/editor conditions.

**Restart-proven**  
The persistent result survived save → full process exit → relaunch → load.

**Packaged-proven**  
It worked in a packaged build outside the editor.

Question: **Is everything finished?**

> **No. I separate what exists in source from what has actually been runtime-proven. The capstone is an integration slice, not a claim that the full game is complete.**

---

# SHEET 14 — Dangerous questions

## “How does your save system work internally?”

> **The mechanical template and the Melodia integration maintain the durable gameplay state I need for the slice. The player-facing proof I care about is that progression and equipped capability state can survive a full restart. I can open the implementation if we need to go deeper.**

Do not improvise low-level details.

## “Why didn't you write your own combat system?”

> **Because combat infrastructure wasn't the artistic problem I needed to solve. Using a mature foundation let me spend my development time on how music, progression, environments, materials, and traversal become one experience.**

## “So what is actually custom?”

> **The Melodia-specific integration and presentation: the world, environment logic, visual language, instruments, material systems, music-reactive presentation, capability/world relationships, and the way the frameworks are adapted into the playable route.**

## “Is this all Blueprint?”

> **No. It is a mixed Unreal project. Blueprint is my primary authoring surface; there is custom C++ and framework code underneath where stable systems need it.**

## “Can you explain this code?”

> **I can explain the role and the interface I use. If you want the exact implementation behavior, I would rather open the class than guess.**

---

# SHEET 15 — Things never to volunteer

Do not lead with:

- AI agents;
- Git management;
- commit counts;
- backend orchestration;
- CI;
- LFS;
- repo archaeology;
- enormous architecture diagrams;
- how many systems exist;
- how long an agent worked;
- token/model/tool discussions.

Unless explicitly relevant, they are production infrastructure, not the capstone story.

---

# SHEET 16 — Presentation fallback phrases

When nervous, use these.

### Bring a technical answer back to art

> **The reason I cared about that technically is that it lets the environment do this…**

### Narrow an overbroad question

> **For this slice, the part I actually rely on is…**

### Admit implementation uncertainty without collapsing

> **I don't want to invent an implementation detail from memory. The responsibility of that system is…**

### Separate prototype from final

> **That is currently a prototype/research direction; the part I am presenting as finished is…**

### Attribute third-party work

> **That behavior comes from the framework; my work begins at the integration and presentation layer here…**

### Move to visual evidence

> **It's easier to show the result than describe it abstractly—this is what the player sees.**

---

# SHEET 17 — Two-minute whiteboard test

Without notes, draw only:

```text
PLAYER
  ↓
EXPLORE
  ↓
MUSIC / INTERACTION
  ↓
RESULT
  ↓
CAPABILITY
  ↓
WORLD CHANGES
```

Beside it write:

```text
Framework = mechanics
Blueprint = assembly
UE content = experience
TD = visualization lab
AE = editorial
```

If you can explain those two drawings clearly, you can survive most high-level questions.

---

# SHEET 18 — Rehearsal circuit

Run this as a 20-minute loop.

### Round 1 — 3 minutes

- 30-second opening
- gameplay loop
- “what did you build?”

No notes.

### Round 2 — 5 minutes

Randomly answer:

- Why Phoenix?
- What is Harmonix?
- What is MelodiaCore?
- Blueprint vs C++?
- What is Chladni?
- Why TouchDesigner?
- Why 3ds Max?

Keep each answer under 30 seconds.

### Round 3 — 5 minutes

Open one actual Melodia asset and narrate it:

- Blueprint;
- material;
- sheep;
- environment;
- instrument;
- Data Asset.

Explain:

1. what the player sees;
2. what you authored;
3. what drives it;
4. what is third-party;
5. what remains unfinished.

### Round 4 — 5 minutes

Hostile-question simulation.

Answer without bluffing:

- “Did you actually write this?”
- “Why is this so complicated?”
- “Why not just use Max?”
- “Is this really a game?”
- “What is actually finished?”
- “Why should I care about this shader/system?”

Then bring every answer back to a visible result.

### Round 5 — 2 minutes

End with:

> **The next milestone is not more infrastructure. It is making the existing system produce one beautiful, legible capstone proof.**

---

# SHEET 19 — Night-before checklist

Know:

- exact 30-second pitch;
- one player-flow example;
- one environment breakdown;
- one material breakdown;
- one sheep/cymatics example;
- provenance of Phoenix / Harmonix / QuillScript;
- MelodiaCore limitation;
- one Max use case;
- one honest unfinished item;
- one next milestone.

Have ready:

- strongest gameplay clip;
- strongest beauty still;
- Blueprint screenshot;
- material graph or instance;
- sheep / Chladni comparison;
- optional restart-proof clip;
- Astrolabe / Max research target if discussing future work.

Do not spend the night memorizing source code.

---

# SHEET 20 — Final mantra

> **I am not defending a codebase. I am presenting a game world I designed, the interactions that make it playable, and the technical-art decisions that make its musical fantasy visible.**
