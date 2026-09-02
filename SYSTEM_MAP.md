# System Architecture Map — Melodia Rhythm-JRPG

**Canonical Architecture Blueprint**
**Last Updated:** 2026-09-01 (Evening P0 Closeout & Chapter Loop Checkpoint)
**Target Engine:** Unreal Engine 5.8.0 | Blender 5.2 LTS | C++20
**Authority Reference:** `Docs/ORCHESTRA_CONVERGENCE_2026-08-20.md`, `Docs/ORCHESTRA_CONTRACT_2026-08-20.md`

---

## 1. High-Level Architectural Model

Melodia is structured around **Two Absolute Authorities** and **Four Converged Pillars**, enforcing strict separation of concerns between narrative progression, gameplay state, aesthetic presentation, and traversal mechanics.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 TWO ABSOLUTE AUTHORITIES                               │
├────────────────────────────────────────────┬───────────────────────────────────────────┤
│    QUILLSCRIPT NARRATIVE AUTHORITY         │       TURN-BASED JRPG STATE AUTHORITY     │
│   (UMelodiaNarrativeSubsystem)             │      (BP_JRPGSaveGame & Combat Core)      │
│  - Branching Dialogue & Cutscenes          │  - Party Stats, HP/MP Calculations        │
│  - Quest Flag Progression                  │  - Turn Queue & Action Resolution         │
│  - 7-Verb Notification Dispatch            │  - Inventory & Key Item Tracking          │
│  - Exactly-Once Reward Delivery            │  - Canonical Save/Load Persistence        │
└─────────────────────┬──────────────────────┴─────────────────────┬─────────────────────┘
                      │                                            │
                      ▼                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 FOUR CONVERGED PILLARS                                 │
├──────────────────────┬──────────────────────┬────────────────────┬─────────────────────┤
│ 1. RHYTHM COMBAT     │ 2. WARDROBE SYSTEM   │ 3. MUSIC AS KEY    │ 4. SINGLE-WRITER UI │
│ (Harmonix Overlay)   │ (Traversal Provider) │ (Resonant World)   │ (UI Bridge)         │
│                      │                      │                    │                     │
│ - Rides on JRPG cmd  │ - Mesh visual swap   │ - Stepping nodes   │ - Sole HUD writer   │
│ - Note accuracy grade│ - Traversal provider │ - Resonant phrases │ - Zero race conds   │
│ - Damage multiplier  │ - Glide / Swim / Dash│ - Unlocks routes   │ - Clean transitions │
│ - MPC Palette pulse  │ - State persistence  │ - Emits 7-verbs    │ - No widget leaks   │
└──────────────────────┴──────────────────────┴────────────────────┴─────────────────────┘
```

---

## 2. Core Subsystems

### 2.1 Narrative Authority (`UMelodiaNarrativeSubsystem`)
- **Header:** `Source/BS_GodFile/MelodiaIntegration/MelodiaNarrativeSubsystem.h`
- **Role:** Central dispatcher for narrative state, QuillScript dialogue nodes, and 7-verb structured notifications.
- **7-Verb Grammar:**
  1. `melodia:quest:<QuestId>.<State>` — Progression and quest objective flags.
  2. `melodia:battle:<EncounterId>` — Combat encounter trigger and terminal callback.
  3. `melodia:stat:<StatId>:<Value>` — Idempotent resonance social stat modifications.
  4. `melodia:wardrobe:<OutfitId>` — Outfits and cosmetic unlocks.
  5. `melodia:item:<ItemId>:<Count>` — Inventory item grant requests.
  6. `melodia:inspect:<TargetId>` — Environmental interaction and world discovery.
  7. `melodia:checkpoint:<SlotId>` — Checkpoint anchoring and save triggers.

### 2.2 Turn-Based JRPG State Authority (`BP_JRPGSaveGame` & Combat Core)
- **Role:** Sole source of truth for combat calculations, actor turn order, party health/mana, and serialization.
- **Persistence:** Serializes character stats, inventory, active wardrobe capabilities, and completed quest flags into canonical save game slots (`BP_JRPGSaveGame`).

### 2.3 Rhythm Presentation Seam
- **Component:** `MelodiaJRPGPresentationRhythmComponent` & `WBP_MelodiaRhythmHighway`
- **Role:** When a player selects an Attack or Resonance Skill in the JRPG command menu, the Rhythm Highway activates. Notes travel along the highway, and player timing grades (`Poor: 0.35`, `Good: 1.0`, `Great: 1.2`, `Perfect: 1.5`) multiply the stock JRPG damage calculation and pulse `MPC_Melodia_Palette`.

### 2.4 Wardrobe Traversal Subsystem (`UMelodiaWardrobeSubsystem`)
- **Header:** `Source/BS_GodFile/MelodiaIntegration/MelodiaWardrobeSubsystem.h`
- **Interface:** `IMelodiaTraversalCapabilityProvider`
- **Role:** Manages character mesh parts (head, body, dress, accessories) and grants concrete physical traversal capabilities (such as `Glide`, `Swim`, `Dash`) to enable reaching new world routes.

### 2.5 Resonant World & Music-as-Key (`APCGHeroMusicGraphHost`)
- **Role:** Musical stepping stones and environmental chords in overworld maps. When players step on harmonic nodes or play resonant melodies, the graph host validates the musical phrase and emits a narrative notification to remove physical route barriers.

### 2.6 Single-Writer UI Bridge (`UMelodiaUIBridgeSubsystem`)
- **Header:** `Source/BS_GodFile/MelodiaIntegration/MelodiaUIBridgeSubsystem.h`
- **Role:** Enforces a single-writer architecture across all viewport widgets (HUD, Dialogue, Battle UI, Main Menu), eliminating dual-widget leaks and input routing conflicts.

---

## 3. Universal Reusable Chapter Gameplay Loop Flow

Every chapter follows the standardized 6-phase sequence:

1. **Phase 1: Narrative Initiation & Sanctuary Departure** (`L_MelusinaMorning`)
   - QuillScript dialogue with NPC anchor -> authored departure gate opens.
2. **Phase 2: Overworld Traversal & Music-as-Key Route Unlock** (`LV_SeaAbove_Prototype`)
   - Third-person traversal -> Starskiff navigation -> harmonic phrase stepping unlocks route barrier.
3. **Phase 3: Turn-Based JRPG Combat with Rhythm Command Timing** (`L_KaleidoNave`)
   - Encounter start -> JRPG command selection -> Rhythm Highway input timing -> damage scaling.
4. **Phase 4: Battle Resolution & Idempotent Reward Distribution**
   - Boss defeat -> narrative resolution callback -> idempotent reward delivery (new outfit piece).
5. **Phase 5: Traversal Upgrade & World Progression**
   - Equip outfit -> activate `Glide` traversal capability -> traverse over gateway chasm.
6. **Phase 6: Canonical Checkpoint & Seamless Chapter Transition**
   - Canonical save to `BP_JRPGSaveGame` slot -> transition to next chapter map.

---

## 4. MCP Automation & Tooling Layer

- **Melodia MCP Server (`deploy/melodia_mcp_server.py`):** 38 unit/regression tests verifying offline schema inspection, narrative idempotency, and Blueprint fixture validation.
- **Agent Bridge MCP (`deploy/agent_bridge_mcp.py`):** Policy router ensuring safe read-only operations while denying dangerous mutations.
- **Monolith MCP (Port `9316`):** Live Unreal Editor JSON-RPC bridge for asset inspection, graph verification, and reflection queries.
