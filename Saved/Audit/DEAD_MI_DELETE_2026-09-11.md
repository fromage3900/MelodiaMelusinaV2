# Dead-MI Delete Pass — Execution Record — 2026-09-11

**Branch:** `cleanup/dead-mi-sweep-2026-09-11` (tracked deletions only).

## Deleted (53 attempted, 52 removed, 1 held)

All with 0 hard referencers (live editor census, re-verified in-session),
binaries backed up to Temp `qol_backup/dead_mi_53/` (53/53):

- 32× `_Archive` SDF_Default twins + StorybookOutline (were never git-tracked;
  disk-only removal, live `SDF/Instances/` twins hold the names)
- 4× `_Loose` fence/planks/roof/tree (untracked; Kenney `MI_fence` live w/ 2 refs)
- 3× Kenney planks/roof/tree (tracked — committed here)
- 10× Niagara Foliage both homes (tracked — committed here; byte-grep over
  Content found no Niagara-system string refs either)
- 2× Masters-homed IridescentRock/SakuraLandscape (tracked — committed here;
  Instances-homed twins kept per convention)
- 2× MelodyToken dupes: `melodsytoken_material` copy removed (untracked);
  `MelodyTokens` copy removed (tracked — committed here);
  `melodsytoken` copy LIVE via SM_Cylinder (kept)
- **HELD:** `MelodyTokens/MI_MelodyToken_Heart` — the editor died mid-retry
  (see incident). 0 refs, backup held, one-line follow-up.

## Proof

- PIE smoke IntegrationMap (session pie_smoke_1_203831, BEFORE the crash):
  287 samples, 0 errors, clean teardown. Evidence JSON alongside.
- Post-delete disk check: 52/53 gone; survivor listed above.

## Incidents (same evening, not caused by the deletes)

1. Editor with the live bridge exited 20:31 (clean `LogExit`), then a second
   instance crashed 20:39 on the read-only landmine (`WBP_MelodiaQuillChoiceEntry`,
   via Claireon MCP `python_execute`) — same signature as the 12:40 Quill crash.
   Multiple agent surfaces are saving against read-only files; repo-wide
   read-only audit is now urgent, not optional.
2. Two-editor state recurred twice tonight (19:22, 20:07). All mutations held
   until single-holder confirmed each time.
3. Untracked `_Archive`/`_Loose` deletions are invisible to git by design;
   this commit carries only the 15 tracked deletions + evidence.

**Evidence level:** live-proven (referencer census + 287-sample smoke).
