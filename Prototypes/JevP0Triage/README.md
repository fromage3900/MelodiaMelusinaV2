# Jev P0 Triage Conductor (isolated prototype)

Jev picks the next P0 verification step from 5 authored actions. Code reads
state, Jev judges, humans execute. Nothing here writes to the editor, maps,
assets, or the gate ledger — delete this folder to remove everything.

## Run

  python Prototypes/JevP0Triage/test_jev_p0_triage.py      # 10 tests, no key
  python Prototypes/JevP0Triage/assemble_p0_state.py 60 "notes here"

Without TYPESAFE_API_KEY every output is `classical-fallback` (deterministic
rules, never Jev evidence). With the key set, the same call goes live
(`jev-live`) with zero logic changes.

## Files

- `jev_p0_triage.py` — closed action set, state, Jev Choice+Noul+Score call,
  fallback, cooldown/hysteresis arbiter, debug HUD.
- `assemble_p0_state.py` — read-only live readers (echo ages, git dirt,
  C: disk, :9316). Never invents telemetry; unknown stays None.
- `test_jev_p0_triage.py` — authored-only, determinism, cooldown, HUD.

## Pipeline study (captures → site)

Proven tonight: audit stills → ffmpeg 1920w JPG → `melodia/captures/<date>/`
→ gallery section in `melodia/index.html` → push `my-site` main.
Next: Jev selects the capture recipe + framing (CAPTURE_STILLS branch and the
capture Score already score publish-readiness); World Compiler recipe on a
duplicated map + HighResShot is the quick-level path — no production-map
mutation. AE leg is manual (no afterfx/aerender on this box); TD exports can
ride the same captures folder when the bridge is warm.
