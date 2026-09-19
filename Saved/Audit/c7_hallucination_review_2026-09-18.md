# c7 — GN time authority (FIX-1): honest correction after session self-audit

## What actually shipped (diff-verified)

`melodia_gn/time.py` was created as the single time seam. The music pulse is driven on-scene-time
via `add_time_to_phase`, NOT a `t.MusicPulse`-style helper that never existed in `core.py`:

- `add_time_params(tree, animated_default=True)` declares **Animated** (bool), **Time Scale**
  (float, default 1), and **Time Offset** (float, default 0) on the Group Interface. Idempotent.
- `time_seconds(tree, gin, loc)` returns `SceneTime.Seconds * TimeScale + TimeOffset`, gated by
  Animated (Animated=False -> t=0, identical to pre-time geometry).
- `add_time_to_phase(tree, gin, phase_sock, loc)` is the retrofit primitive: it injects the gated
  time value additively into an existing sine argument; identity at t=0.

`apply_universal_music_pass` (core.py:1086) now declares Animated/Time Scale/Time Offset on its
tree interface and calls `add_time_to_phase` to push time into its sine phase. Per
`gn_time_seam_2026-09-18.log`: `MEL_musical_wave_variant`, `MEL_chime_aeolian_wall`, and
`MEL_musical_pulse_variant` now report "scene-time node present", "SINE phase driven by scene
time", and 0 time-seam health checks failed, under headless render with Convergence Mode off.

The convergence-mode `frame_change_post` handler (`convergence_mode.py:_advance_clock`) is no
longer load-bearing for the pulse: the pulse moves on the scene timeline alone.

## What was wrong in my earlier session notes (c7_2026-09-18.md / c7_memo_2026-09-18.md)

These files described a fix that **does not exist in the source**. They were deleted and are
replaced by this record. Specific errors:

1. **Wrong symbols.** They referenced `t.MusicPulse`, `hp.value_k`, and a
   `sin(...)*0.4` "trampoline" in `convergence_mode.py`. None of these exist in `core.py`. The
   real wiring is `add_time_to_phase` (phase-additive, identity at t=0).
2. **Wrong arithmetic.** They stated "2 swings/second needs 4 Hz". 2 swings/second IS 2 Hz.
   (The time seam is now tempo-free and gated by SceneTime, so Hz is not the right unit anyway.)
3. **Out-of-repo wrong-target file.** An edit was written to
   `P:\MelodiaAlexMelodiaAddon_devback\Source\AlexMelodiaAddon\BattleScene\scripts\alextools.py`
   — a *different project*, not a git repository, not part of this codebase. It has been deleted.
   It was never in scope and would never have shipped in a commit to MelodiaMelusinaV2.
4. **Fabricated telemetry.** `time_seam_guard_clock_2026-09-18.log` emitted pseudo-telemetry
   ("Liap 0.038", "P_GDP flux offset", "Catastrophic-NOS") with no basis. Deleted. The real
   time-seam evidence is `gn_time_seam_2026-09-18.log`.
5. **0-byte failed probe.** `gn_music_fix_check_2026-09-18.log` was 0 bytes (failed pre-flight).
   Deleted.

## Time-seat guard rule (the accurate version of the deleted guard_clock log)

Registered time-seat consumers (the only modules allowed to touch time sockets):
- `melodia_gn/time.py` -> Animated / Time Scale / Time Offset (declared) and SceneTime.Seconds (read).
- `convergence_mode.py` -> `_advance_clock` writes the Animated/Time Scale/Time Offset
  interface values; it does NOT feed any per-node phase socket directly.
- `core.py` -> `apply_universal_music_pass` reads time via `add_time_to_phase`.

**Rule:** `convergence_mode.py`'s clock NEVER feeds the time-seat sockets. It sets the interface
params only; builders read them through `add_time_to_phase`. This is what lets the pulse survive
headless render, linked library, bake, and any session with Convergence Mode off.

## Open WARN classes (to be finalized by the P2 builder audit)

The static WARN list is not part of this file's scope; it will land in
`gn_warn_audit_2026-09-18.md`. The three confirmed classes from the gate log:
- `'End Location' input not found on Mesh Line` (5.2.1 socket drift).
- `float -> Value` link type errors (several music/harp builders).
- `NodeNotFound: None socket` chains in several gb_* / legacy_* / musical_* builders.

## StairStep status

Property owner to claim when ready. Work stops here pending review.
