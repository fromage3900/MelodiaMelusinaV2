# Quarantined: `UMelodiaMinimalHUD` — 2026-07-31

Moved out of `Plugins/MelodiaCore/Source/MelodiaCore/` because it is dead code.

## Why

The 2026-07-31 duplicate-systems audit found **zero references in both directions**, which is the
standard Decision 020 requires before removing anything from MelodiaCore:

- **C++:** no file outside `MelodiaMinimalHUD.h/.cpp` names the class. (A grep for the substring
  `MinimalHUD` does hit `MelodiaSettingsPanelWidget` — but those are `Check_MinimalHUD` /
  `HandleMinimalHUDChanged`, a settings checkbox for the unrelated `bMinimalReactiveHUD` preference.
  Different thing, same word.)
- **Content:** binary scan of all `.uasset`/`.umap` found no reference. This matters —
  Decisions 020/021 exist because content references classes a C++-only grep calls dead. Here both
  sides agree.

It is also the file that carried the two `FSlateFontInfo` deprecation warnings (`:55`, `:84`) which
would have become hard errors in a future engine version. Removing the file resolves those without a
migration.

## Not deleted, because

`BS_GodFile\.git` is corrupt (commit through `C:\EnvironmentPortfolio\.repo_recovery_20260727\.git`
instead), so there is no reliable in-repo rollback. Quarantine-not-delete follows the precedent set
by Decision 022 and by `_QuarantineSource_20260730/RhythmCombat_20260730/`.

**Location matters:** this sits at the project root, *outside* any module's source tree, so UBT
never compiles it. An earlier quarantine attempt left files under `Source/BS_GodFile/_Quarantine/`,
inside the module directory, where UHT still generated code for them — stale `.obj` and
`.generated.h` artifacts for `RhythmCombat*` are still in `Intermediate/` from that period.

## Restoring

Copy both files back to `Plugins/MelodiaCore/Source/MelodiaCore/` and rebuild with the editor
closed. Note the class is a `UUserWidget` subclass; nothing currently instantiates it, so restoring
the files alone will not make it appear in-game.

## Related

- Not to be confused with `UMelodiaMobileHUD`, which is **live via asset** —
  `Content/Melodia/UI/WBP_Battle_Mobile.uasset` reparents to it — even though the GameMode that
  would display it (`AMelodiaMobileGameMode`) has zero asset references and never runs.
- `UMelodiaRhythmHUDWidget` is live with 5 asset references and is unaffected by this change.
