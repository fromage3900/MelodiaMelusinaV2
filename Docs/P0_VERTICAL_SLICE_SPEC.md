---
title: P0 Vertical Slice Design Spec - Melodia
version: 0.1
---

# P0 Vertical Slice Design Spec (Melodia)

This document locks the gameplay and integration requirements for the P0 playable vertical slice of **Melodia**. The goal is an **ASAP end-to-end loop** that proves the core “emotion modifier + economy + rhythm skills” pipeline.

## 1. Summary of P0 Core Gameplay

### Token Wallet Economy — 4 Global Systems

Melodia uses four **global** economy systems (not per-character counters). They are **shared state** that all characters/companions can contribute to or consume:

1. **HealingEconomy** — tracks healing resource generation/spend globally  
2. **ManaEconomy** — tracks mana/Resonance resource generation/spend globally  
3. **UtilityEconomy** — tracks utility/buff/cleanse/debuff resource generation/spend globally  
4. **GriefEconomy** — tracks grief state accumulation/dissipation globally (drives all modifiers)

**Design rule:** Grief biases the other three economies.

### Grief Hook (central emotional modifier)

When rhythm note hits occur, the **GriefEconomy** level adjusts the economy yields:

- Higher **GriefEconomy** => **more ManaEconomy gain**
- Higher **GriefEconomy** => **less HealingEconomy gain**

Mechanically (P0-proof behavior):
- When GriefEconomy is high, rhythm note hits yield **more** `ManaEconomy`
- In the same condition, rhythm note hits yield **less** `HealingEconomy`

### Companion Rhythm Skills (Skill Families + Chain Feed)

All skill families use the token wallets above as their *input cost* and/or *output effect*.

#### Healing Song family
- `HealingSong_Base` — consumes `HealingEconomy`, heals, and grants small `ManaEconomy`
- `HealingSong_ScalarT1/T2/T3` — stronger heal per tier (same family behavior)

P0 chain rule:
- **Casting HealingSong grants small Mana** (this routes around the grief penalty on Healing -> Mana flow)

#### Mana Song family
- `ManaSong_Base` — consumes `ManaEconomy`, restores mana/Resonance
- `ManaSong_ScalarT1/T2/T3` — scales restoration

P0 chain rule:
- **Casting ManaSong reduces GriefEconomy**

#### Utility Song family
- `UtilitySong_Debuff_PT1` — consumes `UtilityEconomy`, applies “mana drain debuff”
  - P0 behavior: first debuff is a **mana drain** that drains enemy/target `ManaEconomy`
- `UtilitySong_Buff_PT2` — applies buff
- `UtilitySong_Cleanse_PT2` — removes debuffs from companion/party
- Scalar variants on each family entry — potency/duration scales with tier

P0 chain rules:
- `UtilitySong_Debuff` (mana drain) makes targets weaker via reduced ManaEconomy availability
- `UtilitySong_Buff` buffs party
- `UtilitySong_Cleanse` clears debuffs

### Chain Loop (“all feeds into one another”)

P0 loop intent:
- **HealingSong → small Mana bonus**
- **ManaSong → reduces Grief**
- **Utility Debuff → mana drain → enemy weaker**
- **Utility Buff → buffs party**
- **Utility Cleanse → clears debuffs**

## 2. WBP / HUD Requirements (P0)

The P0 HUD must display and drive the 4 economy systems and the emotional state:

- **4 economy indicators** (one per global system):
  - `HealingEconomy`
  - `ManaEconomy`
  - `UtilityEconomy`
  - `GriefEconomy`
- **Grief indicator** (bar or icon)
- **Cast buttons** for each skill family:
  - Healing Song
  - Mana Song
  - Utility Song (at least Debuff in P0)
- **Scalar tier display** per skill family
- **Rhythm/combo feedback** that ties into economy yield updates

## 3. P0 Quest / Dungeon Loop

The P0 playable loop is a single, deterministic encounter pipeline that forces the player to cast the required skills:

1. **Dungeon route entry**
2. **One encounter trigger** (enemy type selected to pressure status/debuff)
3. **Grief hook activates** upon rhythm gameplay in this route
4. **Skill usage gates**:
   - Cast `HealingSong` at least once
   - Cast `ManaSong` at least once
   - Cast `UtilitySong_Debuff` at least once (mana drain)
5. **Encounter resolves**
6. **Quest step advances** only after the required skill usage is satisfied

## 4. Economy State & Math Constraints (P0 “safe” behavior)

Even for the vertical slice, the economy systems must be safe under repeated casts:

- **All economies are clamped** to avoid negative balances
- Grief modifier math must be **deterministic** and unit-testable

Suggested clamp rule for P0:
- `HealingEconomy`, `ManaEconomy`, `UtilityEconomy`, `GriefEconomy` are constrained to `[0 .. MaxValue]` (exact maxima are implementation details)

## 5. Implementation Touchpoints (What must exist)

The P0 build must include:

- Global economy state data structs/variables
- Rhythm hit event path that updates economy yields based on Grief
- Blueprint/plugin hooks for:
  - `HealingSong` base + 1 scalar tier
  - `ManaSong` base + 1 scalar tier
  - `UtilitySong_Debuff` (mana drain) base behavior
- HUD/WBP bindings
- Dungeon route + quest integration fixture
- Enemy type (debuff/status pressure aligned with the Utility Debuff behavior)

---

## 6. Task Ledger (P0)

### Section 1: P0 Vertical Slice — Core Integration Tasks (priority order for ASAP playable)

| Task | System | Priority | Status | Notes |
|---|---|---:|---|---|
| 1. Define 4 global economy data structs/variables (HealingEconomy, ManaEconomy, UtilityEconomy, GriefEconomy) | Global Economies | 1 | open | 4 global systems (shared state) |
| 2. Implement grief modifier: rhythm note hit → adjusts Healing/Mana economy yields based on GriefEconomy level | Grief Hook | 2 | open | Yields biased by grief |
| 3. Implement HealingSong (base + 1 scalar tier) — consumes HealingEconomy, heals, grants small Mana | Healing Song | 3 | open | Chain feed: Heal -> small Mana |
| 4. Implement ManaSong (base + 1 scalar tier) — consumes ManaEconomy, restores, reduces GriefEconomy | Mana Song | 4 | open | Chain feed: Mana -> Grief drop |
| 5. Implement UtilitySong_Debuff (mana drain type) — consumes UtilityEconomy, applies mana drain debuff | Utility Song | 5 | open | First debuff is mana drain |
| 6. Wire HUD/WBP: 4 economy display slots + cast buttons + grief indicator + scalar tier display | HUD/WBP | 6 | open | Player visibility + inputs |
| 7. Dungeon route: one level entry, one encounter trigger, one grief hook activation | Dungeon Route | 7 | open | P0 loop entry point |
| 8. Enemy: one enemy type that uses status/debuff pressure (mana drain reciprocal) | Enemy | 8 | open | Enemy pressures debuff/status loop |
| 9. Quest integration: one quest chain tied to skill usage + encounter resolution | Quest Integration | 9 | open | Gate completion on casts |

### Section 2: Next Highest Leverage Tasks (testing + polish)

| Task | Category | Priority |
|---|---|---:|
| 1. Economy system idempotency: verify repeated casts don't corrupt economy state | Safety | 1 |
| 2. Grief modifier edge cases: economy clamp min/max (no negative balances) | Safety | 2 |
| 3. UtilitySong_Buff variant (PT2) — extend from UtilityEconomy | Utility | 3 |
| 4. UtilitySong_Cleanse variant (PT2) — clears debuffs from party | Utility | 4 |
| 5. Scalar tier 3 for all skill families | Content | 5 |
| 6. Rhythm hit accuracy → economy yield validation (MATH-style eval) | Math/Test | 6 |
| 7. WBP: scalar tier UI update on economy threshold change | HUD | 7 |
| 8. Chain loop test: HealingSong → ManaGain → ManaSong → GriefDrop → more HealingGain | Integration | 8 |
| 9. Enemy AI: scale mana drain potency by grief level (synergy with grief hook) | Enemy AI | 9 |
| 10. Quest step: "cast all 3 skill families at least once" as P0 completion condition | Quest UX | 10 |

### Section 3: Overnight Testing Targets

Which systems to test overnight using the existing harness:

- Grief modifier calculation (unit test: economy yield at grief 0 / 50 / 100)
- HealingSong blueprint fixture execution
- ManaSong blueprint fixture execution
- UtilitySong_Debuff (mana drain) blueprint fixture execution
- WBP binding checks: 4 economy bindings + cast button events
- Quest progression check: skill cast count updates quest state

### Section 4: Integration Touchpoints (files to create/edit)

List the blueprint fixtures, harness tasks, and policy entries that need to be created or updated for P0 integration:

- New MATH harness tasks for each skill family
- New WBP fixture for HUD
- Policy entries for any new MCP tools
- Quest allowlist entries for new quest IDs
- Dungeon encounter fixture

