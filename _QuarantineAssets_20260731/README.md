# Quarantined content assets — 2026-07-31

## `Content/Melodia/Characters/Melusina/BP_Melusina.uasset` + `BP_Melusina_BACKUP_20260729.uasset`

Moved out of `Content/` as part of the Melusina pawn unification (Decision 029g). Direction: the
live battle pawn `BP_MelusinaJRPGCharacter` is canonical; this exploration-only pawn is retired.

### Reference check performed before quarantine (via Monolith, live editor, this session)

- **Zero `.umap` references** to this package anywhere in the project.
- Two real `.uasset` referencer chains, both traced to dead ends:
  - `BP_MelodiaGameMode` → only placed in `/Game/L_MelusinaMorning` (root-level, **not** the live
    route map, which is `/Game/Melodia/Levels/Opening/L_MelusinaMorning`) — and that root map itself
    has **zero referencers**, i.e. nothing loads it. `BP_MelodiaGameMode`'s other four referencers
    are `L_WP_*` World Partition sandbox maps, explicitly outside the vertical-slice route per
    `_VERTICAL_SLICE_SCOPE.md`.
  - `WBP_Battle_Rhythm` → referenced only by the same `BP_MelodiaGameMode`, same dead end.
- A **third**, separate `BP_Melusina` variant exists at `/Game/Characters/Melusina/BP_Melusina`
  (older, 2026-07-16, its own dependency set) — also zero referencers, **not** touched by this
  quarantine, left in place. Flagged in `_ROADBLOCKS_2026-07-31.md`'s duplicate-asset list for a
  future cleanup pass.

Stop condition from the original plan ("if a live-route map references it, stop and rethink")
**did not trigger** — confirmed clear before moving anything.

### Not deleted, because

Same reasoning as every other quarantine this session: `BS_GodFile\.git` is corrupt (commit through
`.repo_recovery_20260727\.git` instead), so there is no reliable in-repo rollback.

### `PackageRedirect` handled in the same change

`Config/DefaultEngine.ini` carried:
```
+PackageRedirects=(OldName="/Game/Characters/Melusina/BP_Melusina",NewName="/Game/Melodia/Characters/Melusina/BP_Melusina")
```
This pointed old references at the now-quarantined asset. Removed rather than repointed — the
redirect existed to survive a prior *move*, not to keep resolving after a *retirement*. Leaving it
would mean any stale reference silently resolves to a package that no longer exists in `Content/`,
which is a worse failure than a normal missing-asset error.

### Restoring

Copy both `.uasset` files back to `Content/Melodia/Characters/Melusina/`, re-add the
`PackageRedirect` line above to `Config/DefaultEngine.ini`, and add
`MelodiaOutfitComponent`-equivalent capability check on `BP_MelusinaJRPGCharacter` before assuming
outfit behavior needs reverting too (`BP_MelusinaJRPGCharacter` already gained its own
`MelodiaOutfitComponent` this session — restoring this pawn does not remove that).
