# Current System Map — Melodia Melusina

**Last Updated:** 2026-09-02  
**Target:** Unreal Engine 5.8 | Blender 5.2 LTS | C++20 | Python 3.11

---

## 1. Current shape

Melodia is now treated as **stable runtime core + expandable authored journey**.

```text
AUTHORING / CONTENT
Volumes • Movements • Chapters • Episodes • Reveries • Monolith Events
                          │
                          ▼
              progression / content packages
                          │
                          ▼
RUNTIME CORE
Phoenix combat + Melodia rhythm + Wardrobe + Convergence + Starskiff/world
                          │
                          ▼
Narrative intents / checkpoints / rewards / canonical durable save
```

The product may grow indefinitely; the number of state authorities must not.

---

## 2. Current stable owners

### TurnBased JRPG / Phoenix
Combat skeleton, turns, targets, action resolution, party state, inventory, terminal results.

### Melodia rhythm
Battle-integrated timing/performance layer. It executes/grades authored actions; it does not own a parallel battle simulation.

### Narrative / Quill
Narrative progression, stable intents, flags, consequences, checkpoints, exactly-once reward consumption.

### Wardrobe
Owned/equipped outfit state and gameplay capability/identity hooks.

### Convergence
Cross-system interpretation layer. Reads owner truth; should not become duplicate storage.

### Starskiff
Vehicle/traversal runtime. Durable upgrades/history may persist; transient motion should normally rebuild.

### UI Bridge
One writer per visible surface.

---

## 3. Current proof status

P0 / First Dream + Sea Above remains the primary full-stack integration proof. The 2026-09-01 documentation records a green automated/gate baseline for that captured state.

The proof established that these seams can work together:

- Quill → world progression;
- Phoenix → rhythm timing → result;
- wardrobe → traversal/gameplay;
- music → world route;
- reward/checkpoint → save/load;
- single-writer UI.

The current follow-up is deeper **restart/idempotency/persistence closure**, not invention of a replacement framework.

---

## 4. Current closure graph

```text
Wardrobe / durable world state
        ↓
Starskiff / exploration
        ↓
Phoenix action
        ↓
Melodia rhythm
        ↓
Convergence / consequence
        ↓
checkpoint / reward
        ↓
SAVE
        ↓
full process restart
        ↓
restore
        ↓
repeat load without duplication
```

---

## 5. Content-scale shift

The old statement that **every Chapter must execute one identical six-phase loop** is no longer current product architecture.

The same stable core can support:

- narrative/exploration Reveries with no combat;
- combat-heavy Episodes;
- creature/music relationships;
- Starskiff travel Chapters;
- outfit-semiotics Chapters;
- Monolith Events with environmental climax rather than HP bars;
- future Gifts and Voyages.

Reusable state ownership matters more than reusable pacing.

---

## 6. Long-term direction

See:

- `Docs/Strategy/MELODIA_ENDLESS_JOURNEY_NORTH_STAR_2026-09-02.md`
- `Docs/Strategy/MELODIA_CHAPTER_TIER_AND_VOLUME_ARCHITECTURE_2026-09-02.md`
- `Docs/Strategy/MELODIA_EVERGREEN_CONTENT_AND_GIFT_MODEL_2026-09-02.md`

**Target end state:** new journeys mostly add data, art, narrative, encounters, outfits, world relationships, and tests—without reopening core ownership.

---

## 7. Multi-machine development

`LAPTOP-Q8S5OSQ2` (Acer Nitro, 16 GB RAM) is configured as a `worker-first-16GB` node:
- Two-PC workflow: `Docs/Production/TWO_PC_DEVELOPMENT_WORKFLOW_2026-09-02.md`
- Laptop onboarding closeout: `Docs/Production/LAPTOP_ONBOARDING_CLOSEOUT_2026-09-02.md`
- Master index: `Docs/Production/MASTER_INDEX.md`
