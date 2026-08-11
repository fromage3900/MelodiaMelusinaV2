# Kiro Melody Token integration handoff

**Date:** 2026-08-01  
**Dependency:** Claude releases the four Universal-master token material instances and direct registry paths before Unreal pickup/HUD implementation begins.

---

## ✅ RELEASED 2026-08-01 (Claude) — read this before the tables below

Steps 1–3 of Sequencing are **done**. Materials exist, `tokens.py` is updated, GMM suite is
**285/285 passing**.

⚠️ **The predicted paths in this document were wrong.** Kiro anticipated
`/Game/EnvSandbox/Textures/melodsytoken/Materials/MI_MelodyToken_*`. The instances were authored
under a proper materials directory instead — `Textures/` is not where material instances belong,
and the old `melodsytoken/Materials/` folder holds the parentless import that had to be replaced.

**Actual released paths — use these:**

```
/Game/EnvSandbox/Materials/Instances/MelodyTokens/MI_MelodyToken_Heart
/Game/EnvSandbox/Materials/Instances/MelodyTokens/MI_MelodyToken_Star
/Game/EnvSandbox/Materials/Instances/MelodyTokens/MI_MelodyToken_Swirl
/Game/EnvSandbox/Materials/Instances/MelodyTokens/MI_MelodyToken_Water
```

Read them from `tokens.py` (`material_path`) rather than hardcoding — all four are now populated and
`material_fallback` has been removed from star/swirl/water.

**Verified:** all four report `M_Master_Toon_Universal` as parent, every texture resolves to its own
variant (none silently render Heart), and Star/Swirl/Water carry `HeightMap` +
`ParallaxStrength = 1.0` while Heart is `HeightMap = None` + `ParallaxStrength = 0` — checked
explicitly, because a Displacement map wired with parallax at 0 is visually identical to no parallax
and is exactly how this silently no-ops.

**Two corrections to the sections below:**

1. **Emission textures are unused — but emissive itself works fine.**
   ⚠️ *Corrected: an earlier version of this note claimed the master had no working emissive. That
   was wrong, and the mistake is worth recording because it will catch others.* Checking
   `MP_EMISSIVE_COLOR` on the master shows "nothing connected" — but this project runs
   **`r.Substrate=True`**, and under Substrate the legacy material pins (`BaseColor`, `Emissive`,
   `Roughness`, `Metallic`, `Normal`) are **all empty by design**. Everything routes through
   `MaterialExpressionSubstrateToonBSDF_4` → `FrontMaterial`. Its pin 5 `EmissiveColor` **is
   connected**, fed by `MaterialExpressionAdd_11`.

   The accurate statement is narrower: the master has **no emissive *texture sampler***. Emissive is
   composed from the Nikki chain — `GlowColor`/`GlowIntensity`, `InnerGlow*`, `BloomBoost`,
   `SparkleIntensity`, `DreamBloom*`, `TwinkleGlints`, `DreamHalo`, `GlobalEmissiveBoost`,
   `ElementEmissiveBoost` — summed into `Add_11`. So the per-element glow authored on the four token
   instances **does emit**. Nothing is broken.

   What is genuinely unused is each variant's `*_Emission` texture, because there is no sampler to
   plug it into. That is an art call, not a bug: authored glow gives uniform per-element emission,
   while a texture would let *regions* glow (the heart's core, the star's points, the swirl's inner
   spiral) — usually what makes a collectible read as lit-from-within rather than tinted. Adding a
   sampler is a **master-architecture change** affecting every material parented to the universal
   master, so it needs explicit owner approval and a closed-editor window. Do not hack it per
   instance.

   **General rule this cost us twice today:** before concluding a material feature is missing or
   dead, check whether Substrate reroutes it. The same trap produced the earlier `ShadingModelID`
   foliage finding.
2. **Two prior defects fixed, not just the missing variants.** `MI_MelodyToken_Heart` had **no parent
   material at all** — an orphaned glTF/Datasmith import outside the toon pipeline. And
   `heart.texture_path` pointed at a file that does not exist
   (`melodsytoken_textures/MelodyToken_Heart_BaseColor`); Heart's textures live under
   `melodsytoken/Textures/` with a `T_` prefix, unlike the other three.

`test_known_variants_have_explicit_material_fallbacks` has been replaced by
`test_all_authored_variants_have_their_own_material`, which asserts the intended end state and also
checks that no two variants share a material path.

**Still Claude's, not yet done:** step 4 — wallet save/restart/idempotence evidence. That is the
evening lane.

---

## ✅ WALLET PROVIDER RELEASED (Claude, 2026-08-01) — Kiro's pickup/HUD lane is unblocked

The five capabilities listed under "Token provider handoff required from Claude" now exist in
`Plugins/MelodiaCore/Source/MelodiaCore/MelodiaTokenWalletSubsystem.{h,cpp}`.
**Requires the pending C++ rebuild** — it is a reflected-header change, so treat it as live only
once that build reports success.

```cpp
UMelodiaTokenWalletSubsystem* Wallet = UMelodiaTokenWalletSubsystem::Get(this);

FMelodiaWalletSnapshot Snap = Wallet->GetSnapshot();
//   Snap.Shards (TMap<FName,int32>, all 7 elements always present)
//   Snap.ManaCurrent / ManaMax / GoldenTokens / TotalCollected

bool bAccepted = Wallet->TryGrantShards(TEXT("Forte"), 1, PickupGrantId);
// also: TrySpendShards, TryAddMana, TrySpendMana, TryGrantGolden, TrySpendGolden

Wallet->OnWalletChanged.AddDynamic(this, &UMyWidget::HandleWalletChanged); // FMelodiaWalletSnapshot
```

| Requirement | How it is met |
|---|---|
| authoritative snapshot | `GetSnapshot()` returns a copy; all seven element keys are guaranteed present, so UI can bind 7 rows without null-checks |
| accept / reject | every mutator returns `bool`; a rejection changes **no state and fires no event** |
| one changed event | `OnWalletChanged` broadcasts exactly once per **accepted** transaction |
| persists canonically | `CaptureToSave`/`RestoreFromSave` run inside `UMelodiaSaveGameSubsystem`'s existing save/load — not a second save path |
| rejects duplicates | `GrantId` checked against a **persisted** `TSet<FName>`; pass a stable battle-instance or pickup ID |

**`GrantId` is the load-bearing part.** Consumed IDs live in the save record, not in memory. An
in-memory guard passes the reopen-dialogue test and *still double-pays after a relaunch* — two
different bugs, and only the second reaches players. Pass `NAME_None` only for grants genuinely meant
to repeat.

### Architecture note

`UMelodiaRoguelikeRunSubsystem` **already owned** `HeartMelodyTokens`/`SwirlMelodyTokens` with its own
`RestoreDurableTokens` path, so a naive new wallet would have been exactly the second-authority
problem this document warns against. Two mismatches were found: the C++ save stored **per-variant
ints** (Heart and Swirl only) while GMM stores **element-keyed shards** across seven elements plus
mana/golden/total, and Star/Water had no C++ representation at all.

Resolved additively — new v4 save fields plus a **one-way migration** on first load of a pre-v4 save
(Heart → Forte, Swirl → Arcane), flagged so it cannot run twice. The legacy fields are deliberately
**not** zeroed: the run subsystem still owns them, and clearing another subsystem's state would be a
cross-authority write. That leaves a small **documented** overlap rather than a hidden one. Whether
the run subsystem should eventually consume the wallet instead of keeping its own two ints is an
owner decision, not an agent's.

---

## Authority split

- **GMM owns:** deterministic token definitions, `TokenWallet` arithmetic, and battle reward fixtures.
- **Claude owns this session:** wallet persistence through the canonical save authority, idempotent victory grants across result restore/reload, and full-process restart evidence.
- **Kiro owns:** Unreal pickup actors, mesh/material assignment, Niagara and HUD presentation, plus a thin Unreal facade that consumes the released token contract.
- There is **no runtime GMM↔Unreal command channel**.
- Tokens are a stat economy. They are not a second save, quest, battle, reward, or inventory authority.

Do not implement a parallel wallet in a widget, pickup actor, GameMode, or transient Blueprint map. Reuse the existing facade/subsystem composition pattern used by `UMelodiaPartySubsystem` and `UMelodiaPacingSubsystem`; persistent storage must join the canonical save transaction owned by Claude's lane.

## Canonical token table

| Variant | Display | Element | Value | Rarity | Released material (corrected) |
|---|---|---:|---:|---|---|
| `heart` | Forte Shard | Forte | 10 | common | `/Game/EnvSandbox/Materials/Instances/MelodyTokens/MI_MelodyToken_Heart` |
| `star` | Radiant Shard | Radiant | 12 | uncommon | `/Game/EnvSandbox/Materials/Instances/MelodyTokens/MI_MelodyToken_Star` |
| `swirl` | Arcane Shard | Arcane | 15 | rare | `/Game/EnvSandbox/Materials/Instances/MelodyTokens/MI_MelodyToken_Swirl` |
| `water` | Tide Shard | Tide | 12 | common | `/Game/EnvSandbox/Materials/Instances/MelodyTokens/MI_MelodyToken_Water` |

Fallback definitions without authored variant art yet:

| Token | Element | Value | Rarity |
|---|---|---:|---|
| `stone` | Stone | 11 | uncommon |
| `gale` | Gale | 11 | uncommon |
| `umbral` | Umbral | 13 | rare |

Do not invent direct material paths for Stone/Gale/Umbral. Keep their fallback status explicit until authored assets exist.

## Wallet contract

`TokenWallet` contains:

```text
shards: {
  Forte, Tide, Gale, Stone, Radiant, Umbral, Arcane
}
mana_current: float = 50
mana_max: float = 100
golden_tokens: int = 0
total_collected: int = 0
```

Operations and required behavior:

- `add_shard(element, amount)` adds to that element and increments `total_collected`.
- `spend_shard(element, amount)` rejects unaffordable spending and leaves state unchanged.
- `add_mana(amount)` clamps to `mana_max`.
- `spend_mana(amount)` rejects unaffordable spending.
- `add_golden(amount)` increments currency.
- `spend_golden(amount)` rejects unaffordable spending.
- Victory grants are idempotent per battle instance.

Claude owns persistence and idempotence proof. Kiro's UI may request operations through the facade and render returned/current state; it must not perform arithmetic locally or infer success from animation.

## Released material contract

All four authored token instances must parent `M_Master_Toon_Universal`.

- Heart: real Heart BaseColor/Emission/Metallic/Normal/Roughness textures; no displacement, so parallax stays off.
- Star: Star textures including Alpha and Displacement; nonzero parallax verified in close-up.
- Swirl: Swirl textures including Alpha and Displacement; nonzero parallax verified in close-up.
- Water: Water textures including Alpha and Displacement; nonzero parallax verified in close-up.
- Variant differentiation uses existing rim, glow, iridescence, sparkle, and approved palette controls—never a new material authority.
- No material may exceed Unreal's two-MaterialParameterCollection limit.

The duplicate Heart MI under `melodsytoken_material/` is a reported cleanup item only. Kiro uses the canonical `melodsytoken/Materials/` family and deletes neither copy.

## Kiro implementation surface

### 1. Facade boundary

Expose the minimum typed Unreal-facing requests needed by pickups and HUD, following existing subsystem/facade composition:

- query wallet snapshot;
- request add/spend shard;
- request add/spend mana;
- request add/spend golden token;
- receive one wallet-changed presentation event after an accepted transaction.

The facade delegates to the canonical economy/save authority. It does not own another map of balances and does not write save files directly.

### 2. Pickup presentation

For each authored pickup:

- token ID selects definition and released material path;
- pickup mesh uses the direct variant MI, not Heart fallback;
- Niagara/audio/stencil feedback is presentation-only;
- collection requests one authoritative transaction;
- pickup disappears or enters collected presentation only after acceptance;
- repeated overlap/click cannot collect twice;
- denied/duplicate collection cannot increment HUD or play success as though accepted.

Do not place or save pickups in `ZenForestTest` without explicit owner approval and a safe map-save window.

### 3. HUD presentation

Show only authoritative snapshot values:

- seven elemental shard balances;
- mana current/max with clamped display;
- golden token count;
- optional total-collected summary.

Requirements:

- no local increment-before-confirm pattern;
- clear element names and variant visuals;
- keyboard/controller focus only if the panel is interactive;
- reduced motion changes ornament, not transactions;
- opening/closing the panel does not alter wallet state or battle input authority.

### 4. Battle reward seam

The stock JRPG result remains terminal-outcome/reward authority. Kiro only presents the accepted token grant and resulting wallet state. Claude verifies that the grant is consumed once per battle instance and survives restart. Cline verifies branch correctness: non-victory outcomes do not receive a victory-only token grant unless explicitly authored.

## Sequencing

1. Claude authors and validates four MIs.
2. Claude updates `tokens.py` direct paths and updates the old fallback test to the new direct-path contract.
3. GMM suite passes.
4. Claude publishes final resolved asset paths and proves wallet save/restart/idempotence.
5. Kiro implements facade consumption and one representative pickup outside protected maps.
6. Kiro implements one wallet HUD readout from authoritative state.
7. Cline verifies victory/non-victory reward branch behavior.
8. All three run pickup → wallet → battle grant → save → full restart → HUD readback.

## Validation

### GMM contract

From `Content/Python`:

```powershell
python -m unittest discover -s gmm -p "test_*.py" -q
```

The existing `test_known_variants_have_explicit_material_fallbacks` must be revised when direct paths land; leaving it unchanged would intentionally fail the new contract.

### Unreal/material

- Every token MI reports `M_Master_Toon_Universal` as parent.
- `validate_material` returns 0 issues for all four.
- Every texture resolves.
- Star/Swirl/Water visibly show nonzero parallax in close pickup shots.
- No authored variant silently renders Heart.
- No map or live PPV is dirtied by material validation.

### Runtime transaction matrix

| Case | Expected |
|---|---|
| Collect one Heart | Forte +1, `total_collected` +1, one presentation event |
| Trigger same pickup twice | Second request rejected/no state change |
| Add mana beyond max | Display and state clamp to `mana_max` |
| Spend unavailable shard/mana/golden | Rejected; no state or success presentation change |
| Victory callback twice, same battle instance | One grant total |
| Defeat/fled/unavailable | No victory grant unless branch explicitly authors one |
| Save, fully exit, relaunch, load | All seven shards, mana, golden tokens, total count unchanged |
| Restore/reopen result after load | No duplicate grant |

## Stop conditions

Stop and coordinate if:

- a Kiro widget or pickup begins owning wallet arithmetic;
- a second save field/store is introduced outside the canonical record/save authority;
- direct material resolution falls back to Heart silently;
- the same pickup or battle instance grants twice;
- a non-victory branch receives an unintended victory grant;
- material validation exceeds two MPCs or compiles with issues;
- implementation requires saving `ZenForestTest` without explicit owner approval;
- work would modify `MelodiaHairComponent.cpp`, locked live PPV/grade assets, or Codex-owned materials/Niagara.

## Evidence report

```text
RELEASED TOKEN MI PATHS:
FACADE/SUBSYSTEM USED:
PICKUP TEST ASSET/MAP:
HUD ASSET:
TRANSACTION MATRIX RESULTS:
BEFORE-SAVE WALLET:
AFTER-FULL-RESTART WALLET:
VICTORY GRANT COUNT:
GMM TEST RESULT:
MATERIAL VALIDATION:
FILES/ASSETS MODIFIED:
DEFERRED/BLOCKED:
```
