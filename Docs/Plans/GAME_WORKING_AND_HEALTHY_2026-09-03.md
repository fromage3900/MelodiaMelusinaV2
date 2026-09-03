# Getting the Game Actually Working — Plan, 2026-09-03

Supersedes the ad-hoc lane list. Written after a full session of driving the editor,
the cook and the repo, so every claim below is something that was observed, not read
in a doc.

---

## 0. The definition we should hold ourselves to

**"Working" = a player double-clicks the packaged `.exe` and plays the route end to
end, on a machine that is not this one.**

Not "the gate ledger says pass." Not "the level opens in the editor." The ledger said
`package_launch` passed for three weeks while no `.exe` existed anywhere on disk.

---

## 1. The real problem is not any single bug — it is false greens

This session found six things that *claimed* success while being untrue:

| Claim | Reality |
|---|---|
| `gate_ledger` — `package_launch` PASS | No `.exe`, no `Saved/Packages`, no `StagedBuilds` |
| `verify_assembly()` — 3 PCG graphs "staged" | Echoed a constant; none of the 3 exist |
| `save_current_level()` | Returned `False` silently for every level in the project |
| `KLEIN_VEIL_SING` — 6 master params "all present" | 2 of 6 |
| `BeatPulse` wired through 30 nodes | Reads 0 — no beat grid was ever cooked |
| `klein_veil_import.py` setting MI scalars | Silent no-op on CollectionParameter names |

I added a seventh myself and had to retract it — I called several textures "blank
white" from eyeballing thumbnails; measuring pixels showed a pale-lilac albedo.

**The health work is not "fix bugs." It is "make the project stop lying."** Every gate
must fail loudly when its subject is absent. That is worth more than any single fix,
because it is what let three weeks of "P0 is closed" coexist with an unshippable build.

---

## 2. Ranked blockers to a working route

### P0 — the route runs packaged
1. **Verify cook #4.** In flight now → `G:\melodia_packages\P0_Route_20260903`. The
   `AlwaysCook` fix (`7f8f3319`) stages `DA_MelodiaIntegrationConfig`,
   `DA_MelodiaPersonaContent` and the beat-grid MIDI, which the previous package was
   missing. **Then boot it and walk the route** — do not mark this pass on exit code.
2. **Re-run the golden run against the new package**, not the editor.
   `specs/p0/core_p0_dream_golden_run.v1.json`.
3. **`MPD_Default.uasset` is quarantined inside the UE_5.8 install** to make the cook
   pass. An engine update restores it and packaging breaks again. Either script the
   quarantine as a documented pre-cook step or find a project-side fix.

### P1 — the look reads
4. **Melusina deltas**: sleeves purple→pink, stockings black→white, boots too dark,
   bodice grey. Owner has said the grey is acceptable for now.
   Probe by swapping the **Albedo texture**, not `BaseTint` — tint only shows where
   texture influence is low, which is why five diagnostic tints produced no visible
   change.
5. **Audio-reactivity — CLOSED (owner, 2026-09-03).** Driven via **MPC + TouchDesigner OSC**,
   not from `Source/`. `MelodiaMusicClockSubsystem` carries the OSC/external-clock hook that makes
   `HasMusicalTime()` true; the pipeline is specified in
   `Docs/Architecture/MELUSINA_T3D_LIVELINK_OSC_PIPELINE_2026-08-14.md` and
   `Docs/Handoffs/AUDIO_REACTIVE Flower_CHOP_OSC_2026-09-02.md`.
   My earlier "no writer in `Source/`, decide whether to delete them" framing was **wrong** — I read
   only the C++ subsystem and concluded absence from it meant absence everywhere. The params are
   externally driven by design. Nothing to decide and nothing to delete.
   Practical consequence for verification: a **packaged run with no OSC source will read these as
   flat**, so never treat a static packaged capture as evidence the reactive path is broken —
   check it with TouchDesigner feeding the clock.

6. **Retire the duplicate `MPC_Melodia_Palette`** at `/Game/_PROJECT/04_Materials/`
   (Aug-11, 17 scalars). `MF_MeluSparkle` and `MF_MeluPaletteColors` still point at it
   with empty `ParameterName`.

### P2 — the world fills in
7. **Faraway PCG is blocked on Blender→UE export**, not on graphs or wiring
   (`0ae8324e`). 14 of 15 `MEL_mother_*` builder meshes were never exported. The 120
   manifest points already carry explicit transforms, so once meshes exist the level
   assembles as ISM directly — no PCG graph required.

---

## 3. Repo health

- **692 commits exist on no remote.** `recovery/snapshot-20260903` captured the tree at
  06:30 and is now 692 behind. Push a fresh orphan snapshot — ~20 min, no history
  rewrite, and it is the only thing standing between this work and one disk.
- **We are on `docs/university-prep-2026-09-03`, not `main`.** `main` is a strict
  ancestor (0 behind, 12 ahead), but several session commits live only on this branch.
  Merge when convenient.
- **History cannot be pushed** — 3 corrupt LFS objects (`Blue_Nebula_6/7/8`) whose bytes
  do not hash to their OID. Orphan snapshots sidestep this. Do not attempt history
  surgery; it is not on the critical path.
- **`git lfs lock` works and is unused.** `.gitattributes` marks `*.uasset` lockable, so
  git-lfs makes them read-only until locked — that is the cause of every silent
  `saved: False`. Locking before editing is both the concurrency fix and the save fix.
- **9 stashes.** Easiest place for work to die quietly; triage them.

---

## 4. Sequence

```
now      verify cook #4 → boot the exe → walk the route      ← the only P0 that matters
then     fresh orphan snapshot push (protect 692 commits)
then     Melusina albedo pass (P1 #4)
later    Blender export for Faraway (P2), MPC retirement, stash triage
```

## 5. Working agreements that would have saved this session

1. **Measure, don't eyeball.** Count pixels before calling a texture blank; read the
   property back after setting it; check the file on disk after a save returns.
2. **A gate that cannot fail is not a gate.** If a validator returns a constant, it is
   documentation, not verification.
3. **One editor, one writer.** Two agents cost a stale-DLL false negative, duplicated
   master work, a lost Monolith port and mid-edit commits. `git lfs lock` already
   solves this.
4. **Verify visually after every material change.** Two regressions this session were
   caught in one capture each and would have been invisible in a diff.
