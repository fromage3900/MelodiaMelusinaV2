# Paul Neale / Professor-Facing Capstone Presentation Strategy

**Date:** 2026-09-09  
**Status:** ACTIVE REHEARSAL AUTHORITY  
**Project:** Melodia Melusina  
**Audience:** Humber 3D Animation / professor-facing review  
**Purpose:** Present the game as an environment-led playable artwork with technical credibility, without turning the review into a backend or code-authorship defense.

---

## 1. Presentation thesis

Use this as the central explanation:

> **Melodia Melusina is an environment-led musical fantasy game in Unreal Engine 5.8. The player explores, discovers musical interactions, resolves rhythm encounters, earns expressive capabilities, and uses those capabilities to change how the world can be traversed. Over the summer, the project moved from visual concept work into a playable production structure, while developing the environments, materials, instruments, animation, and music-responsive visual language that give Melodia its identity.**

The project should read as:

**game → environment → interaction → visual language → technical support**

not:

**repository → architecture → code → agents → game**

The engineering exists to make the fantasy believable. The fantasy is the presentation.

---

## 2. What the reviewer should understand

The reviewer only needs to leave with five clear ideas:

1. Melodia is a real playable Unreal project, not only concept art.
2. The core loop connects exploration, music, reward, wardrobe/capability, and changed world access.
3. Environment art communicates gameplay state rather than acting only as decoration.
4. Music can become visible through materials, VFX, cymatic motifs, and world response.
5. Existing frameworks were deliberately integrated instead of every low-level system being rebuilt from scratch.

Everything else is supporting detail.

---

## 3. Recommended presentation order

### 0:00–1:00 — The fantasy

Open on the strongest environment or short gameplay shot.

Say what Melodia is and what the player does.

Do **not** begin with architecture diagrams, Git history, code, automation, or tooling.

### 1:00–3:00 — The player-facing loop

Show:

```text
explore
→ discover / interact
→ music or encounter
→ reward / capability
→ world changes
→ continue exploring
```

Use one concrete playable example rather than explaining every system.

### 3:00–5:00 — Environment and visual authorship

Show the strongest evidence for:

- composition;
- lighting;
- atmosphere;
- materials;
- environmental storytelling;
- creature / instrument design;
- interaction readability.

The goal is to make the project unmistakably read as environment / technical-art work.

### 5:00–6:30 — Music becomes visual

Use Choral Sheep / Chladni Fleece / cymatics as the clearest compact explanation:

```text
creature
→ motif
→ harmony
→ world
```

Describe TouchDesigner as an R&D / presentation laboratory and Unreal as the authored game world.

### 6:30–7:30 — How it is built

Keep this brief.

Use this sentence:

> **I use existing gameplay frameworks where they solve mature problems, then build the integration and presentation layer that makes them behave as Melodia. Unreal Blueprints are my main artist-facing assembly layer; custom C++ exists where the project needs stable reusable support, but the capstone is not being presented as a from-scratch engine-programming exercise.**

### 7:30–10:00 — Breakdown / questions

Only go deeper technically when the question requires it.

Prefer concrete evidence:

- Blueprint graph;
- material instance;
- mesh / topology;
- rig;
- Niagara;
- Data Asset;
- short code excerpt;
- save/reload proof;
- DCC breakdown.

---

## 4. Provenance and authorship — exact safe language

### Turn-Based jRPG / Phoenix Market

The repository records the **Turn-Based jRPG Template by Phoenix Market** as the mechanical baseline for party / turn / skill / battle / quest / save functionality.

Say:

> **I built on a purchased Turn-Based jRPG framework rather than rewriting a mature combat foundation. My work is in adapting it to Melodia, integrating the player-facing systems around it, and authoring the environments and presentation.**

Do not imply the Phoenix framework was authored from scratch.

### Harmonix

Harmonix is used as Unreal's musical-time / MIDI layer.

Say:

> **Harmonix gives me authored musical timing and MIDI semantics. I use that timing to synchronize rhythm presentation and music-responsive visuals.**

Do **not** say:

> “The main code came from Harmonix.”

That is inaccurate to the current repository architecture. Harmonix is a timing/music layer, not the main gameplay codebase.

### QuillScript

Use QuillScript as the narrative authoring / integration foundation only to the extent currently proven in the project.

Say:

> **QuillScript gives me a narrative authoring foundation; I connect narrative events to the surrounding Unreal gameplay and presentation.**

Avoid claiming it owns more persistent gameplay state than current evidence supports.

### MelodiaCore

MelodiaCore is a real custom project plugin, but the repository explicitly quarantines it as a gameplay authority because earlier runtime work was unstable.

Therefore do **not** present MelodiaCore as “the main C++ system that runs the game.”

Safer wording:

> **MelodiaCore is a custom C++ plugin and R&D/integration layer I developed with substantial coding assistance. Some useful types and presentation/integration work live there, but I do not use it as the authoritative battle/save foundation; the proven JRPG stack remains the mechanical baseline.**

This distinction protects the presentation from overclaiming.

---

## 5. AI-assisted coding boundary

Do not make agentic workflow part of the presentation unless the assignment or reviewer explicitly asks about authorship/process.

If asked directly:

> **I used substantial coding assistance while developing the custom C++ and integration work. I can explain the systems I actively use, why they exist, and how they connect to my Blueprints and content, but I am not presenting myself as having hand-authored every implementation line.**

If asked about a C++ detail beyond working knowledge:

> **I would need to open that class to give you the exact implementation. What I can explain confidently is its responsibility, the interface I use, and what gameplay behavior it supports.**

Never bluff implementation details.

Follow the course's current AI disclosure / academic-integrity requirements when the official brief is available.

---

## 6. The one technical architecture sentence to memorize

> **The mature framework owns the mechanics, Unreal gameplay state exposes what the world needs to know, and Blueprint/material/Niagara content turns that state into the player-facing experience.**

A more technical version, only if needed:

> **I try to keep gameplay authority separate from presentation: systems decide what is true, while Blueprint, materials, VFX, animation, and UI decide how the player experiences it.**

---

## 7. One system flow worth being able to draw from memory

Use the current First Dream proof:

```text
music challenge
→ judged result
→ reward
→ wardrobe equip
→ Glide capability
→ portal/world access changes
→ checkpoint/save
```

Explain it in plain English:

> **The important part is not any one subsystem. The point is that an expressive action changes persistent player capability, and the environment reacts to that capability.**

That sentence connects technical work directly back to environment design.

---

## 8. Choral Sheep explanation

Use the current capstone spine:

> **Creature → Motif → Harmony → World**

### Creature

A charming authored companion that must work visually before the technical layer matters.

### Motif

The sheep carries musical identity through pitch-linked data and material response.

### Harmony

Multiple notes can create a readable musical relationship.

### World

That relationship creates a visible environmental payoff.

Core sentence:

> **The sheep are useful because they let me demonstrate the entire Melodia thesis at a tiny scale: musical identity begins on a creature and propagates outward into the world.**

Do not begin the Sheep presentation with a TouchDesigner network or architecture chart.

---

## 9. Cymatics / Chladni explanation

Memorize this:

> **A Chladni figure visualizes a resonant vibration mode. On a vibrating surface, particles collect around nodal regions with very little movement, making the standing-wave structure visible. I am using that principle as a visual design grammar rather than trying to run a full physical simulation for every note.**

Then connect it to production:

> **The resulting motifs can drive roughness, emissive response, displacement, Niagara, embroidery-like detail, decals, or environment patterns.**

Important nuance:

A frequency alone does not uniquely define a Chladni pattern. Geometry, material, boundary conditions, and resonant mode also matter.

---

## 10. TouchDesigner explanation

Memorize:

> **TouchDesigner is my real-time visual laboratory, not the gameplay brain. I use it to convert audio or game signals into time-based visual experiments, then either capture those results for presentation or rebuild the successful idea as a production effect in Unreal.**

Operator cheat sheet:

- **CHOP** — channels / time-varying signals;
- **TOP** — textures / images / compositing;
- **SOP** — geometry;
- **DAT** — text, tables, scripts, structured data;
- **COMP** — components / reusable networks.

The production boundary is:

```text
Unreal = authored game/world truth
TouchDesigner = visual R&D / replay / presentation
After Effects = final editorial/composite
```

---

## 11. 3ds Max niche — use it because the problem fits

Do not move the established environment pipeline into Max merely to satisfy software preference.

The strongest targeted use case is a **Resonance Astrolabe technical-animation rig**.

Proposed role:

- hierarchical mechanical instrument;
- concentric rings;
- needles / arms;
- constrained movement;
- custom attributes;
- controller relationships;
- bakeable Unreal animation.

Possible artist controls:

```text
Pitch
Amplitude
Harmonic Complexity
Resonance / Open
Preview
Bake
```

Presentation sentence:

> **I want to use 3ds Max as a specialist technical-animation DCC for the instruments. My existing Blender/Houdini pipeline already serves environment generation well, while the Astrolabe gives me a real reason to study Max's hierarchical controller and rigging workflow and then bake that result into Unreal.**

Fallback Max use case:

- asset validation;
- pivots / transforms;
- smoothing;
- UV validation;
- naming;
- collision;
- Unreal export;
- small MaxScript/Python validation utility.

The Max exercise must create visible production value, not exist as ceremonial software usage.

---

## 12. Claims to avoid

Avoid saying:

- “I wrote the whole game in C++.”
- “MelodiaCore is the main gameplay authority.”
- “The main code came from Harmonix.”
- “I built the JRPG framework.”
- “Every arrow on my architecture diagrams is final.”
- “TouchDesigner runs the gameplay.”
- “Every system is production-ready.”
- “I made hundreds of systems.”

Prefer:

- **integrated**
- **adapted**
- **authored**
- **implemented**
- **prototype**
- **research direction**
- **live-proven**
- **restart-proven**
- **planned**

---

## 13. Evidence discipline

Use four labels consistently:

1. **source-built** — exists and compiles;
2. **live-proven** — directly observed working in runtime/editor;
3. **restart-proven** — survived save, process exit, relaunch, load;
4. **packaged-proven** — reproduced outside editor in packaged build.

Do not convert a source claim into a runtime claim.

If uncertain, say exactly what level has been proven.

---

## 14. Review objective

The ideal review conversation is about:

- world composition;
- materials;
- modeling;
- topology;
- animation;
- rigging;
- 3ds Max;
- Unreal scene construction;
- musical visual language;
- technical-art decisions;
- player readability.

The supporting architecture should be visible only long enough to prove that the artwork belongs to a functioning game.

---

## 15. North-star sentence

> **Show the fantasy first. Explain only enough technology to prove that the fantasy is interactive, intentional, and reproducible.**
