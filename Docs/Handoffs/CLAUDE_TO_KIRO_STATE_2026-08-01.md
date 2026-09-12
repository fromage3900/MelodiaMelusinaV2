# Claude → Kiro — state handoff, 2026-08-01 evening

Written to be read cold, mid-task. Short version at the top, detail below.

---

## TL;DR

1. **You are unblocked.** The token wallet provider is built, linked, and Live-Coding patched.
2. **You don't need to build assets to test it** — there are console commands.
3. **Everything is already Blueprint-exposed.** Nothing in your lane has been pre-empted.
4. **Live Coding blocks full rebuilds** — close the editor if you need a real build.

---

## 1. Token wallet provider — RELEASED

`Plugins/MelodiaCore/Source/MelodiaCore/MelodiaTokenWalletSubsystem.{h,cpp}`

Built and verified by artifact, not by exit code: UHT generated the reflected header, the `.obj`
compiled, and `UnrealEditor-MelodiaCore.dll` relinked. Console-command additions landed afterwards
via Live Coding (`patch_applied: true`, 0 errors).

```cpp
UMelodiaTokenWalletSubsystem* Wallet = UMelodiaTokenWalletSubsystem::Get(this);

FMelodiaWalletSnapshot Snap = Wallet->GetSnapshot();
//   Snap.Shards  — TMap<FName,int32>, ALL SEVEN elements always present
//   Snap.ManaCurrent / ManaMax / GoldenTokens / TotalCollected

bool bAccepted = Wallet->TryGrantShards(TEXT("Forte"), 1, PickupGrantId);
// also TrySpendShards / TryAddMana / TrySpendMana / TryGrantGolden / TrySpendGolden

Wallet->OnWalletChanged.AddDynamic(this, &UMyWidget::HandleWalletChanged);
```

Your five stated requirements, and how each is met:

| Requirement | Implementation |
|---|---|
| authoritative snapshot | `GetSnapshot()` returns a copy; all 7 element keys guaranteed present, so a HUD can bind 7 rows without null-checks |
| accept / reject | every mutator returns `bool`; **a rejection changes no state and fires no event** |
| one changed event | `OnWalletChanged` broadcasts exactly once per **accepted** transaction |
| canonical persistence | `CaptureToSave`/`RestoreFromSave` run inside `UMelodiaSaveGameSubsystem`'s existing save/load — not a second save path |
| duplicate rejection | `GrantId` checked against a **persisted** `TSet<FName>` |

### The part that matters most: `GrantId`

Consumed grant IDs live **in the save record**, not in memory. An in-memory guard passes the
"reopen the dialogue" test and *still double-pays after a relaunch* — those are two different bugs,
and only the second one reaches players. Pass a stable battle-instance or pickup ID. Pass
`NAME_None` only for grants genuinely meant to repeat.

## 2. Test harness — verify without building assets

These are **test-only** and commented as such. They call the identical public API a Blueprint calls,
so proving behaviour here proves it for your pickups and HUD.

```
melodia.Wallet.Dump
melodia.Wallet.Grant <Element> <Amount> [GrantId]
melodia.Wallet.Spend <Element> <Amount>
melodia.Wallet.AddMana <Amount>
melodia.Wallet.SpendMana <Amount>
```

Expected: repeat `Grant` with the same `GrantId` → REJECTED. Overspend → REJECTED, no state change.
`AddMana 999` → clamps at `ManaMax`.

**The real test** (yours or mine, whoever gets there): grant with a `GrantId`, save, **fully exit the
process**, relaunch, load, repeat the same grant. Must still be rejected.

## 3. Nothing in your lane was pre-empted

Every function is `BlueprintCallable`/`BlueprintPure` with a `WorldContext` `Get`, and
`OnWalletChanged` is `BlueprintAssignable`. They appear in any Blueprint's node search under
**`Melodia|Wallet`**. Pickup actors, collect feedback and HUD remain yours — I built no pickup, no
widget, and no facade beyond the subsystem itself.

## 4. Architecture note you should know

`UMelodiaRoguelikeRunSubsystem` **already owned** `HeartMelodyTokens`/`SwirlMelodyTokens` with its own
`RestoreDurableTokens` path. A naive new wallet would have been exactly the second-authority problem
your own handoff warns against. Two mismatches:

- the C++ save stored **per-variant ints** (Heart and Swirl only), while GMM stores **element-keyed
  shards** across seven elements plus mana/golden/total;
- Star and Water had **no C++ representation at all**.

Resolved additively: new v4 save fields, plus a **one-way migration** on first load of a pre-v4 save
(Heart → Forte, Swirl → Arcane), flagged so it cannot run twice. Legacy fields are deliberately
**not** zeroed — the run subsystem still owns them, and clearing another subsystem's state would be a
cross-authority write. That leaves a small **documented** overlap rather than a hidden one.

Open question for the owner, not for either of us to decide unilaterally: should the run subsystem
eventually consume the wallet instead of keeping its own two ints?

## 5. Traps worth knowing (each one cost real time today)

- **Live Coding blocks full rebuilds** — `Unable to build while Live Coding is active`. Fine for
  function bodies; **new reflected types still need a closed-editor build**.
- **Substrate reroutes material pins.** `r.Substrate=True` here, so legacy `MP_EMISSIVE_COLOR`,
  `MP_BASE_COLOR` etc. read "nothing connected" **by design** — everything routes through the
  Substrate BSDF node. I twice concluded a feature was missing from that absence. If you inspect a
  material, check the BSDF node, not the legacy pins.
- **Never save `ZenForestTest`.** Owner art work is dirty there and every agent has left it unsaved.
- **A material may reference at most 2 MaterialParameterCollections** — exceeding it fails
  compilation outright, no graceful degrade.
- **The asset probably already exists.** Repeatedly this session, something was nearly rebuilt that
  the project already had.

## 6. Owner decisions settled today

| Decision | Status |
|---|---|
| `MPC_Melodia_Palette` | **canonical** — the `MPC_Portfolio_Palette` duplicate is not the authority |
| `L_SakuraPath` | **deprecated** — not maintained, don't judge its look |
| Terrain parallax | **no** — landscape depth stays height-blend + normals |
| Emissive sampler on universal master | **added**, behind `bUseEmissiveMap` (default **off**, so existing materials are unchanged) |

## 7. Where the PPV stack stands

`PPV_NikkiDream` runs the approved outline, the Portfolio Hero grade, and the Van Gogh sky.
Hero + Gameplay instances now exist for all three. Four Melody Token materials are authored on
`M_Master_Toon_Universal` and your `DT_MelodiaTokens.json` already points at them.

⚠️ The sky is currently **pinned on** for tuning (`UseUDSTimeOfDay=0`, `ManualNightAmount=1`). Before
any capture, use `MI_StarryNight_Hero`, which follows the UDS clock properly.
