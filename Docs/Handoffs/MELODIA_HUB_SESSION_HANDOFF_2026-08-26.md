# Melodia Integration Hub — Session Handoff (2026-08-26)

**Scope of this session:** turn `MelodiaIntegrationMap` into the P0 gameplay-loop test hub, lock in
one Melody Slime as the enemy pattern, place MelodyToken fixtures for wallet testing, and prep
handoffs for live UI-data binding. P0 is **still open** — this session found and fixed one real
regression, found a second real regression live via PIE testing, and is blocked on one Blueprint
edit pending your approval (Claude Code's own permission classifier, not a project rule, declined
it twice).

Baseline: `Saved/Audit/baseline_20260826.txt`, `Saved/Audit/integration_map_inventory_20260826.json`.

## ⚠️ Mid-session editor crash — read this before trusting any "saved" claim below

A stale editor process (never fully dying even after repeated `taskkill`/`Stop-Process -Force`,
including outside the sandbox) sat on Monolith's port while a second instance was launched
alongside it — a live "second writer" collision. Somewhere in that window, an autosave/checkout
prompt from the stale instance overwrote `MelodiaIntegrationMap.umap` and
`BP_MelodiaEncounter_FirstDream.uasset` back to their pre-session content, even though both had
already reported `saved: true` with a confirmed fresh disk mtime beforehand. **A fresh mtime after
save is not sufficient proof under a second-writer collision — re-query the live actor list /
CDO after any suspected concurrent-editor window, not just the mtime.**

Separately, the editor then hit a **fatal DDC crash** on relaunch: `F:\UE_DDC` (the local
DerivedDataCache path) returned `Input/output error` on write and was 99% full, so the "Installed"
cache graph had no writable node. Fixed for all future launches via `Launch_Editor.bat` (repo
root) — see the DDC section below.

Both lost items (the 5 `MelodiaHub` actors + the encounter's `EnemyId`) were **redone and
re-verified via a fresh live actor-list query after the redo-save** — confirmed present, not
just mtime-checked. `BP_EnemyUnit_MelodySlime` (created earlier, before the collision window)
survived intact the whole time.

---

## ✅ Done and verified this session

1. **P0-NARR-01 fixed and committed** (`3912f570`). `MelodiaQuillHarmonyAwakening.qsc`'s three
   separate (and malformed) notifications are now one atomic
   `melodia:questcomplete:<QuestId>:<FlagId>:<RewardId>:<IntentId>:<CheckpointId>` verb, routed to
   the already-built `HandleQuestCompleteVerb`/`CommitQuestCompletion` C++ path
   (`MelodiaNarrativeSubsystem.cpp:1071,1146`) and covered by `MelodiaIntegrationTests.cpp:317-355`.
   Full offline suite green.
2. **First-Dream kit placed in `MelodiaIntegrationMap`** (new `MelodiaHub` outliner folder, x=1200-2200
   east of the existing PlayerStart/stock-content room, clear of the pre-existing stock
   demo dressing which we deliberately left in place): `BP_MelodiaEncounter_FirstDream_Hub`,
   `BP_MelodiaTraversalGate_Hub`, `BP_MelodiaPortal_Hub`, `BP_MelodiaStateAnchor_Hub`.
   `BP_MelodiaEncounter_FirstDream_Hub.EnemyId` set to `enemy.single_stock_fixture` (was `None`).
3. **One Melody Slime locked in as the pattern**: `/Game/_PROJECT/Characters/Enemies/BP_EnemyUnit_MelodySlime`,
   duplicated from stock `BP_WeakEnemy` (parent `BP_EnemyUnitBase`), stats pulled from
   `DT_MelodySlime_Enemies` row `SlimeTideCurrent` (lowest-stat row, chosen deliberately for fast
   iteration — HP 163, dmg 6-10, speed 85, Tide element). Two new identity vars added for the
   variant pattern: `MelodySlimeRowName` (Name, ="SlimeTideCurrent") and `MelodySlimeElement`
   (Name, ="Tide"). **To make the next variant**: duplicate this Blueprint, pick a different
   `DT_MelodySlime_Enemies` row (48 rows exist, one per Forte/Tide/Gale/Radiant/Umbral/Stone/Arcane
   family member), copy its `max_hp`/`base_damage`/`speed` into `firstLevelStats`/`lastLevelStats`
   (mangled field names below), and update the two identity vars. That's the whole recipe.
4. **Resolved the `BP_MelodySlimeBattle` duplicate-path question**: canonical is
   `/Game/_PROJECT/Characters/Enemies/BP_MelodySlimeBattle` (correct `BP_TurnBasedJRPGTemplate` parentage,
   real dependencies). `/Game/Melodia/_PROJECT/Characters/Enemies/BP_MelodySlimeBattle` is a stale
   duplicate parented off the deprecated `_ThirdParty` template copy — flagged, not touched.

## 🔴 Found live, via your own PIE test — the actual P0 blocker

**`BP_MelodiaJRPGPlayerController` is a byte-for-byte duplicate of stock `BP_JRPGPlayerController`**
(same parent — native `PlayerController` — same 21 functions, 24 of 25 identical variables), not a
true subclass. Anything in the stock battle system that hard-casts to `BP_JRPGPlayerController_C`
(confirmed: `BP_InteractionDetector`'s `Set jRPGPlayerController` node, typed
`object:BP_JRPGPlayerController_C`) silently fails against the live Melodia controller and returns
None. That null cascades through `BP_BattleController`/`BP_BattleBase`/`BP_EnemyUnitBase` — this is
the wall of `Accessed None trying to read currentTargetUnit/currentAttackingUnit/jRPGPlayerController/
exploreCharacter` errors from your walk-and-interact test tonight.

**I tried the "obvious" fix and it broke something worse.** Repointing
`BP_MelodiaJRPGGameMode.PlayerControllerClass` straight at stock `BP_JRPGPlayerController` does
satisfy every cast — but stock `BP_JRPGPlayerController`'s own `playerUnits` default is the stock
Mage/Swordsman/Priest/Archer roster, not Sir Melodious. Live PIE test confirmed it: the stock
controller's own party/explore-pawn spawn logic took over and possessed `BP_JRPGCharacter_C_0` /
`BP_PriestCharacter_C_0` (two AI controllers double-possessing the same pawn, "Melusina is gone").
**Reverted immediately** — `PlayerControllerClass` is back to `BP_MelodiaJRPGPlayerController_C`,
confirmed saved (`BP_MelodiaJRPGGameMode.uasset` mtime 19:15:15). Current state = pre-session:
Melusina spawns correctly, the battle-cast bug is back to its original (not worse) state.

**The actual correct fix, not yet applied — blocked pending your approval:**
Reparent `BP_MelodiaJRPGPlayerController` from native `PlayerController` to
`/Game/TurnBasedJRPGTemplate/Blueprints/Controllers/BP_JRPGPlayerController`. This satisfies every
stock cast site (fixing the battle system) while keeping its own `CursorFxAccumulator` addition and
letting its own overridden defaults (`playerUnits` = Sir Melodious, `gold`=10, `partySize`=3, etc.
— full list below) carry forward as instance overrides on the now-inherited variables.

I called `blueprint_query reparent_blueprint` twice; Claude Code's own auto-mode permission
classifier declined both (`"Blocked by classifier"` — not a project rule, not your explicit denial).
**Two ways to close this:**
- **You do the reparent yourself**: open `BP_MelodiaJRPGPlayerController` → Class Settings → Parent
  Class → change to `BP_JRPGPlayerController`. Unreal will likely flag ~24 variables as now-redundant
  (already declared on the new parent) — accept its offer to remove the child's redundant
  declarations. **Then immediately re-check `playerUnits`'s default value is still Sir Melodious**
  (`/Game/MelodiaIntegration/Party/BP_SirMelodiousPlayerUnit`) — reparenting does not reliably
  preserve a child's default-value override for a variable that becomes inherited, and this is
  exactly the failure mode that just bit the "retire the duplicate" attempt. Also re-check `gold`=10,
  `partySize`=3, `isExplore`=True, `exploreCharacterMode`. Compile, save (chmod the `.uasset` first if
  `save_loaded_asset`/Ctrl+S silently fails — this project's `.uasset` files keep reverting to
  read-only after `git checkout`), confirm the file's disk mtime moved.
- **Or grant the permission** and ask me to retry `reparent_blueprint` on
  `/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGPlayerController` → new parent
  `/Game/TurnBasedJRPGTemplate/Blueprints/Controllers/BP_JRPGPlayerController.BP_JRPGPlayerController_C`
  — I'll do the same post-reparent default-value verification and report back.

**Full pre-reparent default snapshot** (for restoring anything the reparent drops), read from the
live CDO before any change:
```
playerUnits    = { BP_SirMelodiousPlayerUnit_C : () }
usableItems    = { BP_BluePotion_C:1, BP_RedPotion_C:1, BP_RevivePotion_C:1 }
miscItems      = { BP_Stone_C:5 }
equipment      = {}
gold           = 10
partySize      = 3
isExplore      = True
exploreCharacterMode = NewEnumerator2
CursorFxAccumulator  = 0.0   (Melodia-only addition, not on stock parent)
```

**Do not repeat the "retire the duplicate" fix** — it demonstrably breaks Melusina's spawn. Reparent
is the only remaining correct path.

---

## 🔧 DDC crash fix — use `Launch_Editor.bat`, not a raw double-click, from now on

`F:\UE_DDC` (99% full, `Input/output error` on write) caused a fatal crash on startup: "Unable to
use cache graph 'Installed' because it has no writable nodes available." `-DDC-ForceMemoryCache`
bypasses it, but it's a raw command-line flag only — confirmed directly from
`Engine/Source/Developer/DerivedDataCache/Private/DerivedDataBackends.cpp:766` (`FParse::Param`
against the process command line, no `.ini` equivalent exists). **`Launch_Editor.bat` in the repo
root now bakes this in — use it instead of double-clicking `BS_GodFile.uproject` going forward.**
Trade-off: no persistent shader/asset cache between sessions (slower cold starts), but immune to
the F: failure mode. Clear space on F: (or fix whatever's causing the I/O error) and this
workaround stops being necessary — the flag can be dropped from the script at that point.

---

## 🟡 Not started — MelodyToken wallet-system fixtures

The editor went unresponsive (repeated "no docked tabs" modals plus your own concurrent PIE
testing) before I could pull live CDO details on `/Game/Melodia/Blueprints/BP_MelodyToken_Universal`
and place instances in the hub. What's known from this session's research, to save re-deriving it:

- Pickup Blueprint: `/Game/Melodia/Blueprints/BP_MelodyToken_Universal`. Mesh:
  `/Game/EnvSandbox/SM_MelodyToken`. Four elemental material variants already exist:
  `MI_MelodyToken_Swirl/Star/Heart/Water` at `/Game/EnvSandbox/Materials/Instances/MelodyTokens/`.
- Wallet authority: `UMelodiaTokenWalletSubsystem` (canonical: `Plugins/MelodiaCore`; a thinner,
  **do-not-use** stub duplicate also exists at `Plugins/MelodiaTokenWallet` — same
  two-sources-of-truth disease as the controller/palette duplicates, per
  `HANDOFF_P0_LOOKDEV_PHASE_2026-08-24.md`). `GetSnapshot()` → `FMelodiaWalletSnapshot`
  (`Balances`, `Resources`, `ResourceMax`, `Shards`, `ManaCurrent/Max`, `GoldenTokens`,
  `TotalCollected`), plus `BlueprintPure GetShards/GetBalance/GetResource/CanAfford`.
- HUD: `WBP_MelodiaWallet_Universal` (parent C++ `UMelodiaWalletHUDWidget`) is the **shipped** wallet
  widget — fixed `BindWidgetOptional` TextBlocks `TXT_Forte/Tide/Gale/Stone/Radiant/Umbral/Arcane/
  Mana/GoldenTokens` + `TXT_TotalCollected`, matching `DA_MelodiaCurrencyRegistry`'s 9 currencies 1:1.
  `WBP_MelodiaCurrencyRow` (0 bindings) is a confirmed-redundant leftover from an abandoned
  data-driven design — do not "fix" it, deleting it is an owner decision, not a gap to close.

**Next-session task**: once Monolith/editor is responsive, place 2-3 `BP_MelodyToken_Universal`
instances in the `MelodiaHub` folder near the encounter kit (different elemental material each, to
exercise different currency rows), confirm what `BP_MelodyToken_Universal`'s pickup logic actually
grants (which `Balances`/`Resources` key, how much), and PIE-walk into one with the wallet HUD open to
confirm `WBP_MelodiaWallet_Universal`'s corresponding `TXT_*` field updates live.

---

## 🖥️ UI live-data integration — prompt for you or a fresh agent session

Copy-paste this into a new session once the controller fix lands:

```
Wire Melodia's battle/wallet UI to read live game state. Verified 2026-08-24/26, do not re-derive:

- WBP_Battle_Rhythm's JudgementText/ComboText/ClockSourceText are already converted to real
  variables (they were non-variable widgets before, which cannot be bound at all -- that part is
  done). Data source: MelodiaBattleSession has SessionCombo (live) + SessionMaxCombo (persistent),
  NOT "MaxCombo". UMelodiaRhythmHUDWidget (C++ parent) exposes BlueprintReadOnly ActiveHUDMode,
  bIsSprinting, bIsGliding, LastActionPromptText -- it has NO Combo/Judgement/ClockSource
  properties, that data lives on MelodiaBattleSession instead.
- Wallet: WBP_MelodiaWallet_Universal (parent C++ UMelodiaWalletHUDWidget) is the SOLE shipped
  wallet widget, BindWidgetOptional TXT_Forte/Tide/Gale/Stone/Radiant/Umbral/Arcane/Mana/
  GoldenTokens + TXT_TotalCollected. Data source: UMelodiaTokenWalletSubsystem::GetSnapshot() ->
  FMelodiaWalletSnapshot, or the BlueprintPure GetShards/GetBalance/GetResource/CanAfford getters.
  DO NOT touch WBP_MelodiaCurrencyRow -- it is a confirmed-dead leftover widget, not a gap.
  DO NOT use Plugins/MelodiaTokenWallet's UMelodiaTokenWalletSubsystem -- that is a stub duplicate;
  Plugins/MelodiaCore's is canonical.
- MelodiaUIBridgeSubsystem is the SOLE widget owner for battle presentation
  (MelodiaJRPGBattleOverlaySubsystem was deliberately retired into it) -- do not add widget
  creation anywhere else.
- Rule from this project's own standing lessons: verify every claim above against the LIVE object
  (get_cdo_properties / get_variables), not just this doc -- and never verify via
  capture_scene_preview/capture_anim_frames screenshots, they have returned byte-identical frames
  for different states multiple times this project. Bone/curve/variable-value reads only.
```

---

## Guardrails carried forward

- No new subsystem/authority. Stock TurnBased JRPG owns battle/party/save; QuillScript owns
  narrative.
- One editor, one baseline at a time. This session hit the modal-dialog trap
  (`MODAL_OPEN "This asset editor has no docked tabs"`) repeatedly on `duplicate_blueprint`/
  `save_asset` calls against Blueprints not already open in a tab — expect it, it just needs a
  manual dismiss each time, nothing is broken when it appears.
- Every `.uasset` write: `os.chmod`/`attrib -R` writable first if `save_asset` fails, then confirm
  the file's disk mtime actually moved. Bit twice this session already (`BP_MelodiaJRPGGameMode.uasset`
  came back read-only from git checkout both before AND after the revert-save).
- A change that compiles clean is not proof it works — the controller swap compiled with 0 errors
  and still broke pawn spawn. Only a real PIE walk-through is evidence.
