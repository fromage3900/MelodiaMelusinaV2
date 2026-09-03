"""Comprehensive handoff compiler — extracts ALL gameplay systems from MelodiaMelusina
and compiles into a single DeepSeek-ready markdown document.

Covers: Vision, Rhythm Combat, Turn Economy (HSR), Instruments, Songcraft Magic,
        Level Authoring, Encounter Systems, Overworld, Milestones, Procedural Layers,
        Audio-Reactive Parameters, 7 Core Combat Mechanics, UI Identity (P5).
"""
import sys
from pathlib import Path

OLD_PROD = Path("G:/MelodiaMelusina/MelodiaMelusina_PRODUCTION/MelodiaMelusina_PROD")
NEW_DOCS = Path("g:/EnvironmentPortfolio/BS_GodFile/Docs")

def read_safe(path):
    if not path.exists():
        return f"*(File not found: {path.name})*"
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            return path.read_text(encoding=enc)
        except Exception:
            continue
    return f"*(Could not decode: {path.name})*"

def extract_lines(text, start, end):
    lines = text.split("\n")
    return "\n".join(lines[start:end])

def main():
    # ── Read all source files ──
    master      = read_safe(OLD_PROD / "MASTER_PLAN.md")
    rhythm      = read_safe(OLD_PROD / "RHYTHM_SYSTEM.md")
    songcraft   = read_safe(OLD_PROD / "SONGCRAFT_MAGIC_SYSTEM.md")
    dream       = read_safe(OLD_PROD / "DREAMINTENSITY_SURREAL_EFFECTS_DESIGN.md")
    level_auth  = read_safe(OLD_PROD / "LEVEL_AUTHORING.md")
    claude_md   = read_safe(OLD_PROD / "CLAUDE.md")
    encounter   = read_safe(OLD_PROD / "FOREST_PHASE_2B_ENCOUNTER_AVOIDANCE.md")
    encounter_impl = read_safe(OLD_PROD / "FOREST_PHASE_2B_ENCOUNTER_IMPLEMENTATION.md")
    escher      = read_safe(OLD_PROD / "ESCHER_GRAMMAR_DESIGN.md")
    cathedral   = read_safe(OLD_PROD / "CATHEDRAL_ROOM_TYPOLOGY_DESIGN.md")
    dream_exec  = read_safe(OLD_PROD / "DREAMINTENSITY_TIER1_EXECUTION_GUIDE.md")
    cassini     = read_safe(OLD_PROD / "ED_CASSINI_INTEGRATION_PLAN.md")

    # ── Extract key MASTER_PLAN sections by line range ──
    sec_vision       = extract_lines(master, 46, 60)
    sec_research     = extract_lines(master, 122, 153)
    sec_rhythm_impl  = extract_lines(master, 153, 233)
    sec_overworld    = extract_lines(master, 233, 257)
    sec_milestones   = extract_lines(master, 245, 260)
    sec_design_v2    = extract_lines(master, 655, 712)
    sec_first_play   = extract_lines(master, 712, 870)
    sec_procedural   = extract_lines(master, 871, 1000)
    sec_nikki        = extract_lines(master, 329, 395)

    # ── Build the handoff document ──
    doc = f"""# DEEPSEEK HANDOFF: Melodia Melusina — Complete Gameplay Systems Reconstruction

> **Purpose:** This is the definitive reference document for rebuilding the Melodia Melusina
> gameplay systems inside the `BS_GodFile` (UE 5.8 Substrate Toon) project. It contains
> every designed mechanic, data structure, and implementation plan extracted from the former
> `G:\\MelodiaMelusina` project. DeepSeek and all agent loops should treat this as the
> canonical gameplay specification.
>
> **Generated:** 2026-07-09 from `MelodiaMelusina_PROD` source documents.

---

## Table of Contents

1. [Project Vision & Pillars](#1-project-vision--pillars)
2. [Project Brief (CLAUDE.md)](#2-project-brief-claudemd)
3. [Research: Turn-Based Rhythm Games](#3-research-turn-based-rhythm-games)
4. [Rhythm Combat Implementation Plan](#4-rhythm-combat-implementation-plan)
5. [Rhythm System Specification](#5-rhythm-system-specification-full)
6. [Design Direction v2: HSR Turn Economy, Instruments, P5 UI](#6-design-direction-v2)
7. [Songcraft Magic System](#7-songcraft-magic-system-full)
8. [Overworld Exploration](#8-overworld-exploration)
9. [Milestones](#9-milestones)
10. [First Playable Level: Melusina's Morning](#10-first-playable-level)
11. [Level Authoring Guide](#11-level-authoring-guide)
12. [Forest Encounter System](#12-forest-encounter-system)
13. [DreamIntensity Surreal Effects](#13-dreamintensity-surreal-effects)
14. [DreamIntensity Tier-1 Execution Guide](#14-dreamintensity-tier-1-execution)
15. [Audio-Reactive Procedural Layers](#15-audio-reactive-procedural-layers)
16. [Infinity Nikki Aesthetic Doctrine](#16-infinity-nikki-aesthetic-doctrine)
17. [Escher Grammar Design](#17-escher-grammar-design)
18. [Cathedral Room Typology](#18-cathedral-room-typology)
19. [ED Cassini Integration Plan](#19-ed-cassini-integration-plan)
20. [Transition Plan for BS_GodFile](#20-transition-plan-for-bs_godfile)

---

## 1. Project Vision & Pillars

{sec_vision}

---

## 2. Project Brief (CLAUDE.md)

The following is the complete project brief that was used to instruct AI agents in the
original MelodiaMelusina project:

```markdown
{claude_md}
```

---

## 3. Research: Turn-Based Rhythm Games

{sec_research}

---

## 4. Rhythm Combat Implementation Plan

{sec_rhythm_impl}

---

## 5. Rhythm System Specification (Full)

```markdown
{rhythm}
```

---

## 6. Design Direction v2

**HSR-Inspired Turn Economy, Instrument Combat Styles, Persona 5 UI Identity**

{sec_design_v2}

---

## 7. Songcraft Magic System (Full)

```markdown
{songcraft}
```

---

## 8. Overworld Exploration

{sec_overworld}

---

## 9. Milestones

{sec_milestones}

---

## 10. First Playable Level

**"Melusina's Morning" — spec + session logs showing PCG composition, input wiring,
and the 7 core combat mechanics expansion**

{sec_first_play}

---

## 11. Level Authoring Guide

```markdown
{level_auth}
```

---

## 12. Forest Encounter System

### 12a. Encounter Avoidance Design
```markdown
{encounter}
```

### 12b. Encounter Implementation Guide
```markdown
{encounter_impl}
```

---

## 13. DreamIntensity Surreal Effects

```markdown
{dream}
```

---

## 14. DreamIntensity Tier-1 Execution

```markdown
{dream_exec}
```

---

## 15. Audio-Reactive Procedural Layers

{sec_procedural}

---

## 16. Infinity Nikki Aesthetic Doctrine

{sec_nikki}

---

## 17. Escher Grammar Design

```markdown
{escher}
```

---

## 18. Cathedral Room Typology

```markdown
{cathedral}
```

---

## 19. ED Cassini Integration Plan

```markdown
{cassini}
```

---

## 20. Transition Plan for BS_GodFile

### What Already Exists in BS_GodFile
- `/Game/Melodia/_PROJECT/Blueprints/Gameplay/BP_MusicManager.uasset` (142 KB)
- `/Game/Melodia/_PROJECT/Blueprints/Gameplay/BP_RhythmHUD.uasset` (102 KB)
- `Content/Python/scaffold_rhythm_assets.py` — generates BP_RhythmKernel, BP_RhythmInputValidator, MPC_RhythmFeedback
- `Content/Python/setup_melodia_core_loop_demo.py` — thin demo stub
- `NPC_SakuraDream` — 6-param global MPC (DreamIntensity, WindStrength, PetalRate, SparkleVisibility, GlobalOpacity, ColorShift)
- 16 Niagara VFX systems (Sakura suite)
- `M_Master_Toon_Universal` (1015 expressions, Substrate Toon)

### Migration Priority Order

1. **Phase 0 — Clock Foundation**
   - Create `BP_RhythmKernel` using UE Quartz subsystem (NOT frame-tick)
   - Wire `OnBeatTriggered` / `OnBarTriggered` dispatchers
   - Bind to `MPC_RhythmFeedback.BeatPulse` for material/VFX sync

2. **Phase 1 — Input Validation**
   - Create `BP_RhythmInputValidator` with `GradeInputNow()` function
   - Windows: Perfect +/-90ms, Good +/-160ms, Miss outside
   - Wire Enhanced Input action (Spacebar / LMB)

3. **Phase 2 — HUD**
   - Create `WBP_RhythmHUD` with pulse ring + judgment popups
   - P5-style angled panels (12-18 degree slash entries)
   - Palette: ink-navy #0A0A14, aqua #7DD3C0, gilt #D4AF37

4. **Phase 3 — Turn Economy (AV System)**
   - SPD stat per unit, AV = 10000 / SPD
   - Turn-order bar widget (vertical portrait strip)
   - SP pool (5 max, party-shared, basic generates, skill spends)

5. **Phase 4 — Instruments & Skills**
   - DA_Instrument data asset (Music Box + Drums first)
   - NotePatternSet per instrument
   - BP_BattleSkillBase with RhythmModifier

6. **Phase 5 — Songcraft Integration**
   - DA_Song + DA_SpellInstance + DA_Material data assets
   - Composition UI (4-beat starter, expand to 8/12)
   - Deterministic RNG spell generation from song hash

7. **Phase 6 — Combat Mechanics Suite**
   - Combo system (Perfect chains, 1.2x stacking to 2.5x)
   - Enemy rhythm telegraph (visual note patterns)
   - Break mechanic (instrument weakness table)
   - Rhythm-based defense (dodge grading)
   - Harmony chain (multi-unit Perfect bonus)
   - Tempo shift (90 -> 110 -> 130 BPM escalation)
   - Perfect streak VFX (edge glow + slow-motion)

8. **Phase 7 — Audio-Reactive Environment**
   - Bind MPC_RhythmFeedback.BeatPulse to Sakura Niagara systems
   - Bind Crescendo meter to DreamIntensity on NPC_SakuraDream
   - Wire fractal ornament brightness to beat pulse + crescendo
   - L-System vine growth tied to turn counter

### Key Design Pillars (NEVER VIOLATE)

1. **"The beat rewards, it never punishes"** — Miss deals 0.4x damage, never zero.
   Missing is bad but playable. Perfect chains are where the magic is.
2. **"One clock"** — Every system (combat, VFX, materials, hazards) listens to the
   same Quartz music clock. No Tick-based timing anywhere.
3. **"Few working > many broken"** — Every asset verified rendering/running before
   it counts as done. No overclaiming.
"""

    output = NEW_DOCS / "DEEPSEEK_RHYTHM_GAMEPLAY_HANDOFF.md"
    output.write_text(doc, encoding="utf-8")
    print(f"SUCCESS: Generated comprehensive handoff ({len(doc):,} bytes)")
    print(f"  Location: {output}")
    print(f"  Sections: 20")

if __name__ == "__main__":
    main()
