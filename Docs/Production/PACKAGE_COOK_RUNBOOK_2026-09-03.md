# Package cook runbook — 2026-09-03 (lanes: build/audit)

Standing procedure + failure modes learned during the 2026-09-02 P0_Closeout cook series
(cook #1 fatal at MeshPartition, cook #2 15-min fail on the NeverCook two-domain ensure,
cook #3 exit 0 → 2.8 GB package → packaged boot 0 fatals → `package_launch` PASS row).

## 1. The NeverCook two-domain rule (generalized)

**Never add `DirectoriesToNeverCook=(Path="/<AnyEnabledPlugin>")` for an enabled plugin
path.** A path registered for two different domains ("Plugin:<X>" and "Never Cooked
Content") trips `ensure(!DefaultDomain.IsValid())` in AssetReferenceRestrictions and the
cook exits non-zero AFTER "Finalisation: End → Done!" — the body succeeds, the tally
fails. This was first learned for `/PCGExtendedToolkit`
(`Docs/Handoffs/P0_BATTLE_UI_CLOSEOUT_HANDOFF_2026-08-27.md` line 188) and re-learned for
`/MeshPartition/` on 2026-09-02. The rule is about the plugin path itself, not about
project referencers — a "no project references it, so it's safe" argument is irrelevant.

## 2. Engine-install modification (revertable, machine-wide)

Cook #3 succeeded with the engine MeshPartition problematic asset **renamed** (quarantined)
in the engine install:

- Affects **every UE project on this machine**, not just BS_GodFile.
- An engine **verify-install / update restores the file** and the cook breaks again — if a
  future cook fails at MeshPartition, check this first before re-diagnosing.
- Revert = rename back (one command). Re-apply = same rename. Record the exact name pair
  here when next touched.

## 3. Cook procedure

1. Editor closed; verify no `UnrealEditor*` process and no listener on 9316.
2. `MapsToCook` must match disk (`Config/DefaultGame.ini` §ProjectPackagingSettings) — see
   `DREAMSTATE_MAPSTOCOOK_REMOVAL_VERDICT_2026-09-03.md`.
3. Warm DDC timings observed: 32 min (cold) → 15 min (warm). A failed cook that reached
   "Finalisation" still leaves useful DDC.
4. Grep the cook log for `MODAL_OPEN` before concluding a hang (rule 8).
5. `0 LogCook: Error` + exit 0 is the pass; "Done!" alone is not (see §1).

## 4. Packaged verification gate

Launch `Windows\BS_GodFile\BS_GodFile.exe` outside the editor; evidence from the packaged
log (`Windows\BS_GodFile\Saved\Logs\BS_GodFile.log`): 0 fatal/assert lines, IoStore
containers mounted, `LoadMap /Game/Melodia/Levels/Menu/L_MelodiaMainMenu` complete,
`OrreryMainMenuGameMode: Main menu UI added to viewport`. Record via
`python Tools/record_gate.py package_launch pass --note ...` — prose is not a row.

## 5. Always-cook paths that must never regress

- `/Game/Melodia/UI` — packaged front end resolves WBP_MainMenu etc. via native soft paths
  (08-14 Gauntlet proved the omission).
- `Party/` — `BP_SirMelodiousPlayerUnit` loads via hardcoded `LoadClass` in
  `MelodiaJRPGPartyBootstrapSubsystem`; uncooked = Sir silently never joins (PIE hides it).
- `/Game/MelodiaIntegration/Narrative` — Quill assets.
