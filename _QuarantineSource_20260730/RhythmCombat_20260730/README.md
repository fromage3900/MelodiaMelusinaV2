# Quarantined 2026-07-30 — RhythmCombatComponent / RhythmInputComponent / RhythmCombatUI

**Why:** These three components (built by Cline, `Docs/RHYTHM_COMBAT_SYSTEM_HANDOFF_2026-07-30.md`) implement a custom combat-authority system — `URhythmCombatComponent::ExecuteRhythmAttack` computes its own damage multiplier from input accuracy and drives combo state directly. This is exactly what Decision 009 (2026-07-29, `_DECISION_LOG.md`) forbids: *"No custom damage callbacks, no rhythm judgement, no MelodiaCore battle override. Stock authority is the single source of truth."* It also violates the Harmonix MIDI Rhythm Contract's explicit boundary (`Docs/HARMONIX_MIDI_RHYTHM_CONTRACT_2026-07-29.md`): rhythm/timing systems may only decorate an already-valid stock command, never issue damage or advance a turn themselves.

Cline's work landed the same day as Decision 009 but after it — two parallel lanes produced contradictory output with no cross-check. Confirmed with the project owner (2026-07-30) that this should be killed, not integrated.

**Not touched / still fine to use**: `RhythmBeatTracker` (clean BPM/beat/bar utility, no damage or combat logic) stays in `MelodiaIntegration/` — it's a legitimate building block for the Harmonix-based skill-update plan going forward.

**Status**: reversibly quarantined, not deleted. Never referenced from anywhere else in the codebase (confirmed via project-wide grep before moving) — moving these out of `Source/BS_GodFile/MelodiaIntegration/` does not break any other compilation unit. Restore only if a future decision explicitly reopens custom rhythm-combat authority.
