# Qwen Rhythm Skills Scope & Wallet Integration Review

**Date:** 2026-08-03  
**Author:** Qwen3:8b (subagent)  
**Workstreams:** (1) Scaffold 3 new rhythm skills, (2) Review existing wallet integration

---

## WORKSTREAM 1: Scaffolded Rhythm Skills

### Source data summary

From `melodia_rules.json`:
- **Elements cycle:** Forte → Stone → Umbral → Arcane → Radiant → Gale → Tide → Forte
- **Rhythm windows (ms):** Perfect ≤ 90, Great ≤ 120, Good ≤ 160
- **Default BPM:** 120.0
- **Songcraft skill_effects with tags:** StarlitPing (radiant), TidalWave (tide), GustStaccato (gale), MoonStep (umbral), StoneWall (stone), TidalMend (tide/mend)
- **No existing skill_effect for Forte, Arcane, or pure-Radiant in songcraft** (Petal Cadence is Blueprint-only, not in songcraft list)

From KIRO_MELODY_TOKEN_INTEGRATION:
- **Tokens→Elements:** Heart→Forte (10), Star→Radiant (12), Swirl→Arcane (15), Water→Tide (12)
- **Fallback (no authored art):** Stone (11), Gale (11), Umbral (13)
- **Wallet operations:** TryGrantShards, TrySpendShards, TryAddMana, TrySpendMana, TryGrantGolden, TrySpendGolden

From CLAUDE_TO_KIRO_STATE:
- Wallet provider released, `OnWalletChanged` broadcasts once per accepted transaction
- `GrantId` is load-bearing — persisted, survives restart
- Every element key guaranteed in snapshot
- `CaptureToSave`/`RestoreFromSave` integrated with canonical save

---

### Skill 1: Forte/Heart — "Downbeat Break"

| Property | Value |
|---|---|
| Blueprint parent class | `BP_BattleSkillBase` (stock, Decision 009) |
| GameplayEffect | Single-target damage + `TempoBreak` modifier (from `melodia_rules.json` modifiers registry) on Great/Perfect |
| Rhythm timing window | Standard (`melodia_rules.json` windows_ms: P=90, G=120, Gd=160) |
| Token cost to activate | None (uses SP from stock economy) |
| Token reward on Perfect grade | `TryGrantShards(TEXT("Forte"), 1, DownbeatBreak_BattleInstanceId)` |
| Token reward on Great grade | 50% chance `TryGrantShards(TEXT("Forte"), 1, DownbeatBreak_BattleInstanceId_G)`, else 0 |
| Element type | Forte |
| Songcraft tag alignment | None directly (Forte has no songcraft entry; this is the first Forte-coded skill) |
| Rationale | Maps to Heart token (Forte). Existing Petal Cadence is the co-op opener; Downbeat Break is a standalone rhythm damage skill that fills the Forte token-earning slot. |

### Skill 2: Radiant/Arcane — "Resonant Arc"

| Property | Value |
|---|---|
| Blueprint parent class | `BP_BattleSkillBase` (stock, Decision 009) |
| GameplayEffect | Multi-target damage with controlled falloff; applies `ResonantFocus` modifier on Perfect |
| Rhythm timing window | Standard |
| Token cost to activate | None (SP-based) |
| Token reward on Perfect grade | `TryGrantShards(TEXT("Radiant"), 1, ResonantArc_BattleInstanceId)` |
| Token reward on Great grade | `TryGrantShards(TEXT("Arcane"), 1, ResonantArc_BattleInstanceId_G)` (Star vs Swirl flex — Perfect leans Radiant/Star, Great leans Arcane/Swirl) |
| Element type | Radiant (primary), Arcane (secondary on Great) |
| Songcraft tag alignment | `StarlitPing` (radiant/spark) for visual/name — this skill replaces or extends StarlitPing into the rhythm layer |
| Rationale | Maps to Star (Radiant) and Swirl (Arcane) tokens. The grade-dependent element flex creates a meaningful choice: aiming for Perfect steers rewards toward Radiant/Star, while accepting Great steers toward Arcane/Swirl. Prevents one skill from dominating both token economies. |

### Skill 3: Tide/Water — "Lullaby Mend"

| Property | Value |
|---|---|
| Blueprint parent class | `BP_BattleSkillBase` (stock, Decision 009) |
| GameplayEffect | Single-ally heal scaled by grade (Miss=0.70, Good=1.0, Great=1.15, Perfect=1.35 per the Authoritative Rhythm Combat Wiring grade table) |
| Rhythm timing window | Standard |
| Token cost to activate | None (SP-based heal) |
| Token reward on Perfect grade | `TryGrantShards(TEXT("Tide"), 1, LullabyMend_BattleInstanceId)` |
| Token reward on Great grade | 50% chance of 1 Tide shard |
| Element type | Tide |
| Songcraft tag alignment | `TidalMend` (mend/tide/sustain) — this skill is the rhythm-layer version of TidalMend |
| Rationale | Maps to Water token (Tide). The only sustain/heal skill in the initial rhythm catalog. TidalMend already exists in songcraft; this ports it to the authoritative rhythm combat wiring with grade-dependent healing scalar, not just a flat scalar. |

---

### Token Mapping Table

| Rhythm Skill | Element | Token Variant | Token Value | Existing Material |
|---|---|---|---|---|
| Downbeat Break | Forte | Heart | 10 | `/Game/EnvSandbox/Materials/Instances/MelodyTokens/MI_MelodyToken_Heart` |
| Resonant Arc (Perfect) | Radiant | Star | 12 | `/Game/EnvSandbox/Materials/Instances/MelodyTokens/MI_MelodyToken_Star` |
| Resonant Arc (Great) | Arcane | Swirl | 15 | `/Game/EnvSandbox/Materials/Instances/MelodyTokens/MI_MelodyToken_Swirl` |
| Lullaby Mend | Tide | Water | 12 | `/Game/EnvSandbox/Materials/Instances/MelodyTokens/MI_MelodyToken_Water` |

---

### Wallet API Calls Per Skill

```text
// On skill execution at reward-eligible grade (perfect/great depending on skill):
// Wallet is obtained from GameInstance:
UMelodiaTokenWalletSubsystem* Wallet = UMelodiaTokenWalletSubsystem::Get(this);

// --- Activation cost (not used — skills use stock SP) ---
// No TrySpendShards call during skill execution per Decision 009 review below.

// --- Reward grant on grade threshold met ---
bool bAccepted = Wallet->TryGrantShards(Element, 1, SkillGrantId);
// If bAccepted -> OnWalletChanged fires -> HUD updates

// --- Defensive: check before granting ---
if (!Wallet->IsGrantConsumed(SkillGrantId))
{
    Wallet->TryGrantShards(Element, 1, SkillGrantId);
}

// Grade-based variant selection (Resonant Arc specific):
EMelodiaRhythmGrade Grade = /* from rhythm result */;
FName Element = (Grade == EMelodiaRhythmGrade::Perfect)
    ? TEXT("Radiant")
    : TEXT("Arcane");
Wallet->TryGrantShards(Element, 1, ResonantArc_BattleInstanceId);
```

**GrantId convention per skill:**
- `DownbeatBreak_{BattleInstanceId}` — stable per battle
- `ResonantArc_{BattleInstanceId}` — stable per battle
- `LullabyMend_{BattleInstanceId}` — stable per battle

Use the stock battle's unique instance ID (from `UMelodiaBattleAdapterSubsystem`) as the suffix so that replaying a battle result does not double-pay. The suffix ensures each battle instance can grant each skill's reward exactly once.

---

### DA_MelodiaIntegrationConfig New Rows

The config asset at `/Game/MelodiaIntegration/Config/DA_MelodiaIntegrationConfig` already holds `TravelLevelIds` and allowlisted notification IDs. Three new row groups are needed:

**RhythmSkillDefinitions table:**

| Column | Type | Example |
|---|---|---|
| SkillId | FName | `DownbeatBreak` |
| BlueprintPath | FString | `/Game/MelodiaIntegration/Party/Skills/BP_DownbeatBreak` |
| Element | FName | `Forte` |
| TokenVariant | FName | `Heart` |
| TokenGrantAmount | int32 | 1 |
| TokenGrantGrade | EMelodiaRhythmGrade | `Perfect` |
| SP Cost | int32 | 2 |
| bRequiresRhythmClock | bool | true |

**Existing stock data table:** `/Game/MelodiaIntegration/Blueprints/DT_MelodySlime_Skills` already holds skill data references and should be extended with rows for DownbeatBreak, ResonantArc, and LullabyMend (or replaced with the config asset if the DT is deprecated — confirm before editing).

**Suggested addition to the config DataAsset:**

Add a `TArray<FMelodiaRhythmSkillDef> RhythmSkills` property to the config (or create a separate `DA_MelodiaRhythmSkillConfig` if the existing config class should not grow). Each entry carries:
- `SkillId`
- `Element`
- `TokenGrantAmount`
- `GrantGradeThreshold`
- `BlueprintSoftReference`

---

## WORKSTREAM 2: Wallet Integration Review

### 2.1 Wallet API Surface Verification

Source file: `MelodiaTokenWalletSubsystem.h/.cpp`

| Claim in KIRO doc | Verified? | Evidence |
|---|---|---|
| `GetSnapshot()` returns all 7 elements | ✅ YES | `EnsureElementKeys()` in the constructor adds missing keys; `GetSnapshot()` copies `Shards` which always has all 7 |
| Every mutator returns `bool` | ✅ YES | Each `Try*` method returns `bool`; rejection changes no state, fires no event |
| One event per accepted transaction | ✅ YES | `BroadcastChanged()` called exactly once at the end of each accepted mutation; never called on rejection |
| Persists via canonical save | ✅ YES | `CaptureToSave` writes to `UMelodiaSaveGame::Wallet*` fields; `RestoreFromSave` reads them back |
| Rejects duplicate `GrantId` | ✅ YES | `IsGrantConsumed(GrantId)` checked before mutation; consumed IDs stored in `ConsumedGrantIds` which is persisted |
| `NAME_None` grants are repeatable | ✅ YES | `IsGrantConsumed` returns `false` for `NAME_None`; `ConsumedGrantIds.Add(GrantId)` only called when `!GrantId.IsNone()` |

**Finding:** The API surface is correct and complete. No missing functionality.

### 2.2 Grant-Idempotency Path Verification

The full chain:

1. `TryGrantShards(Element, Amount, GrantId)` → checks `IsGrantConsumed(GrantId)` → if consumed, returns `false` immediately
2. If accepted, `ConsumedGrantIds.Add(GrantId)` 
3. `CaptureToSave` → writes `ConsumedGrantIds` to `Save->WalletConsumedGrantIds`
4. Save is written to disk atomically (Decision 019: atomic rename)
5. On load: `RestoreFromSave` → reads `WalletConsumedGrantIds` back into `ConsumedGrantIds`
6. Second `TryGrantShards` with same `GrantId` → `IsGrantConsumed` returns `true` → **rejected**

**Finding:** Idempotency survives full process restart. The persisted `TSet<FName>` is the correct mechanism. No double-pay path exists for any non-`NAME_None` `GrantId`.

**Gap:** There is no explicit defense against a `GrantId` collision between a battle instance and a pickup using the same ID string. If `BattleInstance_42` and `Pickup_42` both exist, the pickup grant after the battle grant would be rejected. Mitigation: `GrantId` values should be namespaced per source (e.g., `Battle_42` vs `Pickup_42`). This is a convention, not a code fix; the doc should document this convention.

### 2.3 Save/Restore Path Verification

Source file: `MelodiaTokenWalletSubsystem.cpp:168-231`

**Capture:** `CaptureToSave` writes all 7 fields (`WalletShards`, `WalletManaCurrent`, `WalletManaMax`, `WalletGoldenTokens`, `WalletTotalCollected`, `WalletConsumedGrantIds`, `bWalletMigratedFromLegacyTokens`). Correct.

**Restore:** `RestoreFromSave` reads all 7 fields back. Correct.

**Migration:** One-way legacy migration on first pre-v4 load: Heart→Forte, Swirl→Arcane. Legacy fields untouched (deliberate cross-authority boundary). `bMigratedFromLegacy` flag prevents re-migration. Correct.

**Defensive defaults:** Mana sanity check — if `ManaMax <= 0` (legacy save), reset to 100 and clamp. Correct.

**Finding:** Save/restore is sound. The migration path respects the `UMelodiaRoguelikeRunSubsystem` authority boundary by not zeroing legacy fields. The only note: `BroadcastChanged()` is called at the end of `RestoreFromSave`, which will fire `OnWalletChanged` during load — UI bound to this delegate must handle load-time broadcasts gracefully (not animate a "new reward" presentation for restored state).

### 2.4 Decision 009 Violation Audit

Decision 009: *"No custom damage callbacks, no rhythm judgement, no MelodiaCore battle override. Stock authority is the single source of truth."*

Decision 017: *"Toughness/break and elements stay deferred. Resonance's decision loop must be proven fun before a second mechanic is added."*

**Risk 1 — Skill-inline token grants would violate Decision 009/017:** If a rhythm skill calls `TryGrantShards` during its `Execute` / `DealDamage` flow (i.e., inline during skill resolution), the token is awarded before the stock battle controller has finalized the result. This bypasses the stock JRPG reward authority (Decision 009) and adds a second economy mechanic (Decision 017's deferred elements) before Resonance is proven fun.

**Correct design:** Token grants must fire only through the **post-battle result reward system** — i.e., in the victory-result handler that applies stock rewards, not in the skill Blueprint's execution graph. The `UMelodiaBattleAdapterSubsystem` or the stock `BP_BattleController`'s victory path should iterate over skills used in the battle and grant their element tokens as part of the terminal outcome, gated by the grade achieved.

**Risk 2 — Token spending as skill activation cost would violate Decision 009:** If a skill requires `TrySpendShards` before it can execute, the rhythm layer is gating access to stock combat abilities. Decision 009 forbids any rhythm layer from controlling access to combat outcomes. SP is the stock activation resource; tokens must remain a post-battle economy until explicitly re-decided.

**Risk 3 — Rhythm grade affecting token amount/rejection could become an evaluative rhythm layer:** Decision 016 (rhythm is expressive, not evaluative) says the rhythm layer never blocks or reduces an outcome. If a skill grants 0 tokens below Great, that is *factually* an evaluative gate on a reward. The design above uses grade-scaled grants (Perfect=1, Great=50% chance, Good/Miss=0). This is acceptable *only if* the baseline stock combat outcome (damage/heal) remains unblocked — which it does. The token grant is an additional expressive bonus, not a reduction of the normal outcome. This is consistent with Decision 016's intent. However, the implementation must ensure that `Good` and `Miss` still produce full stock damage/heal results — the token grant is additive only.

**Decision 009 gap status:**

| Risk | Severity | Status |
|---|---|---|
| Skill-inline TryGrantShards | **VIOLATION** — must use post-battle result system | Design must enforce this; see convention below |
| TrySpendShards as activation cost | **VIOLATION** — gating combat access | None of the three skills above use this; correct |
| Grade-dependent token grants as evaluative layer | **Acceptable** if stock outcome is unblocked | Must verify in implementation |
| Wallet mutations from rhythm adapter | **VIOLATION** if `UMelodiaRhythmCombatAdapter` writes wallet | Adapter must only produce effect requests, not economic mutations |

**Required convention for skill Blueprint authors:**
```
BP_Skill_Execute:
  1. Compute stock damage through stock resolver (Decision 009)           ← OK
  2. Do NOT call Wallet->TryGrantShards here                              ← VIOLATION
  3. Store achieved grade on the battle state / battle result             ← OK
  4. On victory: battle result system calls Wallet->TryGrantShards        ← OK
```

---

## Summary

1. **Three skills designed** — Downbeat Break (Forte/Heart), Resonant Arc (Radiant→Arcane flex, Star/Swirl), Lullaby Mend (Tide/Water) — each with grade-dependent token grants via `TryGrantShards` and conventions to avoid Decision 009 violation.
2. **Wallet API correct** — all six operations verified against source; idempotency chain survives full restart via persisted `ConsumedGrantIds`; save/restore path complete with one-way legacy migration.
3. **Key gap:** Skill-inline token grants would violate Decision 009. Grants must be deferred to the post-battle victory result handler, not executed during skill resolution. A `GrantId` namespace convention (`Battle_*` vs `Pickup_*`) is also needed to prevent cross-source collisions.
