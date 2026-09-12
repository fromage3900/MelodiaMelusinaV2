# MPC_Melodia_Palette Canonical Move — Execution Spec (NOT YET EXECUTED)

**Why deferred:** requires a closed editor + full `Build.bat` + PIE re-proof.
Editor is open (owner + live Hermes lane). Do NOT start this while any editor
holds the project.

**Target:** `/Game/Melodia/Materials/MPC_Melodia_Palette` (dir exists and is
empty; mirrors `MPC_Cymatics_Driver` in `Melodia/Cymatics/`).
**Scope of the move:** `MPC_Melodia_Palette.uasset` ONLY. `MPC_MelodiaInk.uasset`
(same folder, doc-level refs only) moves in the same session or stays — not
load-bearing for P0.

## Step 0 — Preconditions (all must hold)

1. Exactly one editor, 0 dirty packages, Hermes lane idle.
2. Full static chain green on the starting commit (record the baseline row).
3. Audio-reactivity PIE proof green BEFORE (so the after-proof has a control):
   `UMelodiaAudioReactivePresentationSubsystem` writes land on the MPC
   (Bass/Mid/Treble/BeatPulse visible).

## Step 1 — Code edits (header change = rebuild mandatory)

1. `Plugins/MelodiaWardrobe/Source/MelodiaWardrobe/Public/MelodiaMagicalTransformTypes.h:112`
   `"/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette.MPC_Melodia_Palette"`
   → `"/Game/Melodia/Materials/MPC_Melodia_Palette.MPC_Melodia_Palette"`
2. `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaRhythmReactivitySubsystem.cpp:22`
   `"/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"`
   → `"/Game/Melodia/Materials/MPC_Melodia_Palette"`

## Step 2 — Python sweep (mechanical, review the diff)

~50 files under `Content/Python/` embed the old path (full list discovered
2026-09-10 via grep for `Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette`).
Mechanical replace old → new across `Content/Python/*.py`, then
`python -m compileall` the touched files. TouchDesigner/OSC/specs/docs refs
(`_TouchDesigner/`, `deploy/osc_routing.json`, `specs/`, `Docs/`) update in the
same commit (docs-only, no runtime effect).

## Step 3 — Asset move (in-editor, ONE session)

`EditorAssetLibrary.rename_asset("/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette",
"/Game/Melodia/Materials/MPC_Melodia_Palette")`, save, confirm material
graphs that sample the collection still resolve (they reference by path —
redirector covers stragglers; fix up after).

## Step 4 — Closed-editor rebuild

Close editor → `Build.bat` (full, NOT Live Coding — header constant changed) →
reopen → confirm DLL timestamp advances.

## Step 5 — Re-proof (ledger rows, not prose)

1. Audio-reactivity PIE: MPC params move with music (control from Step 0).
2. Wardrobe magical-transform pulse (exercises `MelodiaMagicalTransformTypes.h:112`).
3. `verify_baseline` + map-load smoke. `static_gates` row only if all green.

## Rollback

Code revert (2 lines) + rename asset back + rebuild. The old path must not
linger as a redirector beyond the session (a stale-path MPC silently eats all
writes — the exact failure mode in `MelodiaRhythmReactivitySubsystem.cpp:17-21`
comments).

## Done definition

`_PROJECT/04_Materials/` holds no MPC; both C++ paths point at
`/Game/Melodia/Materials/`; Python sweep compiles; PIE reactivity proven;
ledger row written. Until then, `_PROJECT` stays — it is load-bearing.
