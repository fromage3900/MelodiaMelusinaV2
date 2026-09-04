# Melodia Melusina — Technical Vertical Slice

**Purpose:** Professor / technical-review front door  
**Engine:** Unreal Engine 5.8  
**Project:** Single-author rhythm-JRPG / environment-led exploration game  
**Current milestone:** P0 vertical-slice convergence and runtime closure  
**Status date:** 2026-09-04

---

## 1. Executive Summary

Melodia Melusina is an environment-led Unreal Engine 5.8 game built around a simple systemic thesis:

> **Player expression through music and clothing should produce meaningful traversal, world-state, and progression consequences.**

The current vertical slice is intentionally narrower than the full product vision. Its job is not to prove every planned chapter, world, boss, procedural tool, or live-content system. Its job is to prove that the project's core gameplay authorities can cooperate in one coherent player journey.

The active proof route connects:

```text
Narrative / exploration
        ↓
Music / rhythm interaction
        ↓
Challenge result
        ↓
Reward
        ↓
Wardrobe state
        ↓
Traversal capability
        ↓
Changed world access
        ↓
Checkpoint / canonical save
        ↓
Process restart / restore
```

This page separates **implemented source**, **live-proven runtime behavior**, **restart-proven persistence**, and **work that is still intentionally open**.

---

## 2. What the Vertical Slice Is Meant to Prove

The current slice is centered on the First Dream / Sea Above production lane and exists to demonstrate:

- authored narrative and exploration;
- environment-led player guidance;
- Phoenix / TurnBased JRPG encounter integration;
- Melodia rhythm execution;
- wardrobe as gameplay rather than cosmetic-only presentation;
- traversal consequences derived from player state;
- world interaction that reacts to that state;
- canonical reward / checkpoint state;
- canonical save and restore;
- a stable architecture that can support later chapter authoring without replacing core systems each time.

The current proof content is centered on:

- `L_MelusinaMorning`;
- First Dream / Kaleido Nave encounter flow;
- Sea Above traversal;
- Resonant Weave / wardrobe gameplay;
- music-to-world interaction;
- Starskiff traversal integration;
- canonical checkpoint and persistence.

The slice is an **integration laboratory**, not a claim that the whole game is complete.

---

## 3. Current Player-Facing Golden Path

A professor-facing demo should be understandable without exposing every experimental subsystem.

### A. Establish the world

Begin in the strongest current environment presentation, ideally `L_MelusinaMorning` or the current First Dream route.

The goal is to establish:

- environment composition;
- lighting and atmosphere;
- material quality;
- authored environmental storytelling;
- Melodia's visual identity before technical explanation begins.

### B. Demonstrate music as a gameplay key

The player reaches a music/rhythm interaction.

The important architectural point is that rhythm does not exist as an isolated minigame. Its judged result can be consumed by other systems without making those systems duplicate rhythm logic.

### C. Demonstrate wardrobe → traversal consequence

The currently proven P0 interaction chain is:

```text
music challenge completion
    → reward.first_resonance_echo
    → wardrobe grant
    → automatic Accessories equip
    → Glide capability becomes available
    → traversal/world portal unlocks
```

This is the clearest current proof of Melodia's central design idea:

> **expression changes capability, and capability changes the world.**

### D. Demonstrate Sea Above / Starskiff

Where stable enough for the live review, the player can board the Starskiff, transfer possession, move, and disembark.

The point of this section is not vehicle spectacle. It demonstrates that traversal state is owned through reusable gameplay contracts rather than one-off level scripting.

### E. Demonstrate persistence

The project has already completed a full-process restart check where canonical wardrobe state was saved, Unreal was closed, the process was relaunched, the save was loaded, and the equipped Accessories state restored.

For a live professor demo, a short recorded restart proof is preferable to spending presentation time waiting for editor relaunch.

---

## 4. Architecture: Stable Owners, Not Duplicate Systems

A major technical goal of P0 has been to stop adding parallel authorities and instead make the existing systems cooperate.

### Current ownership model

| Domain | Stable owner / rule |
| --- | --- |
| Narrative / durable progression | Canonical narrative record / save authority |
| Wardrobe | `UMelodiaWardrobeSubsystem` + player wardrobe component |
| Traversal capability | `UMelodiaTraversalCapabilityRegistry` |
| Player traversal consumption | `UMelodiaTraversalComponent` |
| Rhythm execution | `UMelodiaRhythmCombatSubsystem` |
| JRPG battle state | Phoenix / TurnBased JRPG stack |
| Presentation | Read-only consumers react to gameplay authorities |
| UI | Single-writer direction; no competing HUD authorities |
| Save/load | Canonical JRPG / narrative save path; no second SaveGame authority |

This design is deliberate.

The project has repeatedly rejected the tempting short-term solution of adding:

- another wardrobe manager;
- another progression manager;
- another save object;
- another traversal authority;
- another global rhythm path;
- another UI writer.

The production rule for the vertical slice is:

> **Prove and harden the existing authority before inventing a replacement.**

---

## 5. Live-Proven Runtime Evidence

The strongest current P0 evidence was recorded in:

`Docs/Evidence/P0_EXPLORATION_WARDROBE_GLIDE_PORTAL_PROBE_2026-08-31.md`

### Proven in PIE / runtime

The current integration map has demonstrated:

1. The relevant portal reports traversal locked before challenge completion.
2. The music node can complete successfully with a judged result.
3. The reward is granted through the canonical path.
4. Wardrobe receives and equips `Cos_Accessories_MelusinaV2`.
5. The equipped form owns the Glide gameplay grant.
6. `UMelodiaWardrobeSubsystem` reports the Accessories slot equipped.
7. Airborne Glide traversal requests are accepted while invalid grounded requests fail closed.
8. The portal transitions from locked to unlocked.
9. The live prompt text updates accordingly.
10. The editor session ends without dirty packages from the verification run.

### Focused automated verification

The closeout evidence also records passing focused tests for:

- `Melodia.Wardrobe` — 6/6;
- `Melodia.P0` — 4/4;
- `Melodia.Quest.Shorewake` — 1/1;
- `Melodia.Melusina.Traversal.CapabilityContract` — 1/1.

Additional gameplay hook, traversal integration, equip roundtrip, and save/load roundtrip checks are also recorded as passing in the P0 evidence.

---

## 6. Restart-Proven Persistence

A full-process restart check has already demonstrated the following path:

```text
equip Accessories
    → canonical save
    → close UnrealEditor process
    → relaunch
    → canonical load
    → LOADED_NARRATIVE_RESTORED
    → ApplyWardrobeState
    → Accessories equipped = true
```

This is stronger than source presence or an editor-only object check because the durable state survived a complete process restart.

The current persistence implementation is still being hardened further in:

- Issue #51 — Runtime closure: atomic persistence + repeat-load proof
- PR #54 — `runtime: close canonical persistence restore invariants`

The final persistence closure target remains:

```text
Outfit
 → Starskiff
 → Encounter
 → Phoenix command
 → Rhythm phrase
 → Convergence consequence
 → Reward
 → Save
 → Quit
 → Relaunch
 → Load
 → same durable state
 → Load again
 → no duplication
```

That full chain is the acceptance target, not a claim that every step is already packaged-proven.

---

## 7. Starskiff Status

`BP_Starskiff_MK2` now derives from native `AMelodiaStarskiffPawn`.

The current implementation includes:

- floating movement;
- MoveForward / MoveRight input;
- capability and range boarding checks;
- possession transfer on board;
- disembark;
- canonical boat traversal request;
- placement in `LV_SeaAbove_Prototype`.

PIE verification has exercised boarding and movement acceptance.

Starskiff is therefore a useful professor-facing integration surface, but it should remain **stabilization-only** until the core review path is safe.

---

## 8. Rhythm + Presentation Convergence

The rhythm layer has been moving toward a clean gameplay-authority / presentation-consumer model.

`UMelodiaRhythmCombatSubsystem` exposes judged lane-hit results.

Presentation components consume those results for:

- hit VFX;
- UI reaction;
- continuous audio-reactive values;
- Niagara presentation.

The important technical constraint is that presentation does not become a second gameplay authority.

This lets visual polish remain expressive while preserving deterministic gameplay ownership.

---

## 9. Environment + Procedural Production

Melodia's technical scope extends beyond runtime gameplay into environment production.

Current production/research lanes include:

- Blender Geometry Nodes asset-family generation;
- Houdini procedural environment workflows;
- terrain / worldgen tooling;
- material and shader systems;
- Blender-to-Unreal assembly;
- Nanite-oriented environment production;
- audio-reactive / cymatic environment experiments;
- Python tooling for procedural worldbuilding and validation.

These are valuable production multipliers, but they are **not on the P0 critical path**.

Before technical review, procedural tooling should be shown only when it is already stable enough to demonstrate without risking the gameplay presentation.

---

## 10. Evidence Discipline

Melodia uses four distinct verification labels.

### Source-built

The implementation exists and compiles.

### Live-proven

The behavior was directly observed in the intended runtime/editor session.

### Restart-proven

The durable result survived a complete save, process exit, relaunch, and load.

### Packaged-proven

The behavior was reproduced in a packaged Development build outside the editor.

These categories must not be collapsed into one another.

A system being present in source is not sufficient evidence that it works in the shipped runtime.

---

## 11. Current Review Boundary

### Protect and polish

- First Dream / Sea Above route;
- strongest environment presentation;
- rhythm interaction;
- wardrobe → Glide → traversal chain;
- visible world-state response;
- Starskiff only where stable;
- canonical save/load;
- character presentation;
- UI clarity;
- one reliable 5–10 minute demo route.

### Stabilize, do not expand

- persistence restore invariants;
- repeat-load / idempotency proof;
- Starskiff runtime;
- HUD / single-writer verification;
- packaged-build proof.

### Freeze until after review

- new gameplay frameworks;
- new save architecture;
- broad new economy systems;
- new traversal authorities;
- new procedural experiments that do not improve the demo;
- new monolith / boss systems;
- speculative AI-toolchain expansion;
- large new content branches.

The project is now in **closure mode** for this milestone.

---

## 12. What Is Intentionally Not Being Claimed Yet

The current project should **not** claim:

- that the full game is complete;
- that every planned chapter is authored;
- that every Convergence consequence is implemented;
- that every persistence edge case is closed;
- that repeat-load/idempotency is fully certified;
- that all gameplay paths are packaged-proven;
- that all procedural systems are production-ready;
- that every wardrobe asset is final-character compatible;
- that every experimental branch belongs on the professor-facing route.

This boundary is part of the production discipline, not a weakness in the pitch.

---

## 13. Professor-Facing Technical Talking Points

### 1. Gameplay consequence from expression

The player does not simply collect cosmetics.

Wardrobe state can grant traversal capabilities, and those capabilities change world access.

### 2. Stable subsystem ownership

The project has moved away from prototype duplication toward clear Unreal ownership boundaries.

The same durable gameplay state can be consumed by world interaction, traversal, presentation, and persistence without making each system authoritative.

### 3. Environment art supported by procedural production

The project combines authored environment design with procedural tooling rather than treating procedural generation as a replacement for art direction.

### 4. Evidence-driven production

Source presence, live runtime proof, process-restart proof, and packaged proof are tracked separately.

### 5. Current production lesson

The current milestone is deliberately shifting from expansion to closure:

> **Use the systems already built to author one coherent, beautiful, restart-safe player journey.**

---

## 14. Suggested 5–10 Minute Review Route

```text
[0:00–1:30]
Environment / Melusina Morning / First Dream
    ↓
[1:30–3:00]
Music / rhythm interaction
    ↓
[3:00–4:30]
Reward → Wardrobe equip → Glide unlock
    ↓
[4:30–6:00]
Traversal / Sea Above / Starskiff if stable
    ↓
[6:00–7:00]
Checkpoint + explain restart proof
    ↓
[7:00–10:00]
Architecture / questions / technical discussion
```

A prerecorded restart clip should be available as backup evidence.

---

## 15. Current North Star

The immediate goal is not to make Melodia larger.

The immediate goal is to make the existing vertical slice:

- coherent;
- beautiful;
- technically legible;
- stable;
- restart-safe;
- easy to demonstrate;
- easy for another Unreal developer to understand.

Once P0 closes, the project can return to broader chapter authoring and procedural expansion from a much healthier production foundation.

---

## 16. Canonical Supporting Documents

For deeper review:

- `_VERTICAL_SLICE_SCOPE.md`
- `Docs/Handoffs/CURRENT_P0_STATUS_2026-08-25.md`
- `Docs/Evidence/P0_EXPLORATION_WARDROBE_GLIDE_PORTAL_PROBE_2026-08-31.md`
- `Docs/Plans/RUNTIME_PERSISTENCE_CLOSURE_PLAN_2026-09-02.md`
- Issue #51 — runtime persistence closure
- PR #54 — persistence restore invariants

This page is the **technical front door**, not a replacement for those evidence and implementation records.
