# Codex handoff — universal Melody Token wallet BP (2026-08-14)

**Lane split:** Codex drives Monolith and the editor. Claude is in C++ and coordination.
This is the editor-side half of the universal wallet; the C++ half is done and building.

**Do not create a second wallet.** `UMelodiaTokenWalletSubsystem` is the single authority
by Decision 020/029g, and the `MelodiaTokenWallet` *plugin* scaffold is quarantined for
having tried. Everything below binds to the existing subsystem.

---

## 1. What already exists (do not rebuild)

`UMelodiaTokenWalletSubsystem` — MelodiaCore, GameInstance subsystem, full BP surface:

```
FMelodiaWalletSnapshot GetSnapshot()          BlueprintPure — Shards map, Mana, Golden, TotalCollected
int32  GetShards(FName Element)               BlueprintPure
bool   TryGrantShards(Element, Amount, GrantId)
bool   TrySpendShards(Element, Amount)
bool   TryAddMana(float) / TrySpendMana(float)
bool   TryGrantGolden(Amount, GrantId) / TrySpendGolden / TryRefundGolden
bool   IsGrantConsumed(FName GrantId)         BlueprintPure
OnWalletChanged(const FMelodiaWalletSnapshot&) BlueprintAssignable
static Get(WorldContextObject)                BlueprintPure
```

Two properties of this API that the BP should rely on rather than reimplement:

- **`OnWalletChanged` fires exactly once per ACCEPTED transaction, never on rejection.**
  Bind it and re-render; do not poll, and do not compute balances in the widget.
  `FMelodiaWalletSnapshot` is documented as *"Immutable read model handed to UI. UI renders
  this and never computes balances itself."*
- **`GrantId` gives idempotency that survives a process restart.** A pickup passes its own
  stable id; a re-grant is rejected. This is what stops a collectible double-paying after
  save/reload — the exact class `repeat_consume` exists to catch.

## 2. What I added in C++ (built, needs an asset)

`Plugins/MelodiaCore/Source/MelodiaCore/MelodiaTokenCatalog.{h,cpp}`

The wallet is element-keyed and deliberately knows nothing about art. The catalog is the
missing half — what a player actually sees:

```
FMelodiaTokenDefinition { VariantId, DisplayName, Element, Value, Rarity, Icon, Material }
UMelodiaTokenCatalog    { Tokens[], GeneratedFrom }
  GetTokenByVariant(VariantId, out bFound)      BlueprintPure
  GetTokensForElement(Element)                  BlueprintPure
  ResolveCost(VariantCost, out ElementCost, out UnknownVariants)  BlueprintCallable
```

`ResolveCost` is the one to use for prices. It resolves everything **before** committing and
returns false if **any** variant is unknown — a partially-resolved cost silently undercharges,
which is worse than a refused transaction.

## 3. The rows to author

From the canonical model, `Content/Python/gmm/game/tokens.py` `TOKEN_TYPES`:

| VariantId | DisplayName | Element | Value | Rarity |
|---|---|---|---|---|
| `heart` | Forte Shard | Forte | 10 | common |
| `star` | Radiant Shard | Radiant | 12 | uncommon |
| `swirl` | Arcane Shard | Arcane | 15 | rare |
| `water` | Tide Shard | Tide | 12 | common |

Icons/materials (paths are in `tokens.py`; note **heart differs** — it lives under
`melodsytoken/Textures/` with a `T_` prefix, the others under `melodsytoken_textures/`
without one; a 2026-08-01 comment records the earlier wrong path):

```
MI_MelodyToken_Heart / _Star / _Swirl / _Water
  under /Game/EnvSandbox/Materials/Instances/MelodyTokens/
```

**Three of seven elements have no token variant** — Gale, Stone, Umbral. That is a content
gap, not a bug: the wallet can hold those shards, nothing grants them yet. Do not invent
variants to fill the table.

**Do not hand-maintain these rows.** They are a fourth copy of a vocabulary that already
exists in `tokens.py`, the wallet, and `EMelodiaSpellElement`. Generate them, and the asset
carries `GeneratedFrom` for provenance. `PostLoad` warns on duplicate variants, zero values,
and an empty catalog.

## 4. Suggested BP shape

`WBP_MelodiaTokenWallet` — one row per catalog entry:

```
Construct:  Catalog = load UMelodiaTokenCatalog
            Wallet  = UMelodiaTokenWalletSubsystem::Get(self)
            bind OnWalletChanged -> Refresh
            Refresh()

Refresh(Snapshot):
   for each FMelodiaTokenDefinition in Catalog.Tokens:
       icon    <- Icon
       label   <- DisplayName
       balance <- Snapshot.Shards[element name]     (0 when absent)
       value   <- Value                              (stat-economy weight)
   mana   <- ManaCurrent / ManaMax
   golden <- GoldenTokens
```

Render `Snapshot`; never call `GetShards` per row in a tick.

`Content/Melodia/UI/` already holds `WBP_MelodiaParchmentPanel`, `WBP_MelodiaDivider` and the
filigree atoms — reuse them rather than authoring new chrome. There is also an existing
`UMelodiaWalletHUDWidget` (`MelodiaTokenPresentation.h:81`) which is presentation-only; check
whether it should be the parent before creating a sibling.

## 5. Order

1. Create `DA_MelodiaTokenCatalog` under `/Game/Melodia/Data/` and populate the four rows.
2. Confirm no `PostLoad` warnings (`MELODIA_TOKENS` in the log).
3. Build `WBP_MelodiaTokenWallet` against catalog + subsystem.
4. Prove idempotency live: grant with a `GrantId`, grant the **same id again**, confirm the
   second is rejected and `OnWalletChanged` fires **once**. Then save, restart the process,
   re-grant that id, and confirm it is still rejected. That last step is the one that has
   historically been skipped.

## 6. Coordination

- **Claude is not touching the editor, Monolith, or `.uasset` files.** C++, Python tooling,
  and docs only.
- The working tree carries uncommitted C++ from a third lane (traversal capability registry,
  wallet, narrative, gacha). It **compiles** — I built it after fixing two UHT errors
  (`BlueprintReadWrite` on private members in `MelodiaTraversalComponent.h:205,208`, fixed
  with `meta=(AllowPrivateAccess="true")`). Those files are not mine to commit.
- Before committing: `git log -1` first, expect to re-stage. Several lanes are writing.
- `Tools/wardrobe_draft_lint.py` validates cosmetic `token_cost` against `tokens.py` and
  currently reports **0 token findings across 40 drafts**. If catalog rows drift from
  `tokens.py`, that linter will not catch it — it reads the Python, not the asset. A catalog
  vs `tokens.py` check is worth adding once the asset exists.

## 7. Known gap this does not close

`UMelodiaWardrobeSubsystem::PurchaseCosmetic(FName, int32 GoldenPrice)` takes a **flat Golden
price** and cannot express a shard cost. Cosmetic drafts price in shards. Wiring the wardrobe
purchase path through `ResolveCost` + `TrySpendShards` is a small C++ change — Claude's side,
not blocking this BP.
