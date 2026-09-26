# Melodia Signal Vocabulary & Port Reconciliation

**Date:** 2026-09-25 · **Mandate:** Jev closed-set audit `Prototypes/JevOrchestrationAudit/`
(source=`jev-live`, first=`O1_PORT_VOCAB_RECONCILE` p=1.0, riskiest=`A_9000_COLLISION_RESOLVED`
p=0.41, needs_human=0.32, readiness=1). Supersedes conflicting port prose in
`deploy/osc_routing.json` (2026-09-02) and partially corrects
`MelodiaTouchDesigner/docs/PORTS.md`. Status of anything remains owned by
`CURRENT_STATE.md`; this file is a CONTRACT MAP, not a status claim.

## 1. The live port table (verified 2026-09-25)

| Port | Proto | Producer | Consumer | Payload | Verified by |
|------|-------|----------|----------|---------|-------------|
| 9000 | UDP | UE `UMelodiaRhythmReactivitySubsystem` (fan-out from `MelodiaJRPGPresentationRhythmComponent`) | TD `/project1/osc/in_battle` (oscinCHOP, port 9000) | `rhythm/beat_phase`, `rhythm/beat_pulse` (+ battle semantics) | TD `osc.tdn` export 09-10 (current 09-25) + UE source |
| 9001 | UDP | TD `/project1/osc/out_blender` | Blender listener | `audio/band/sub|low|mid|high|air` + 12 preset signals | TD `osc.tdn` |
| 9002 | UDP | `Tools/phrase_bridge` (python, `melodia.phrase/v1`) | **UE `UMelodiaPhraseBusSubsystem` (native, RecvFrom)** | 7 authored phrase fields | PIE ingest proof `Saved/Audit/listening_field_20260924/phrase_bus_ingest_proof_20260924.json` (09-24, proven on :9000-era DLL; :9002 move recorded in CURRENT_STATE §Live) |
| 7001 | UDP | `services/hand_bridge` (MediaPipe) | TD `/project1/hand_osc` | hand telemetry | TD PORTS.md |
| 8000 | UDP | **nobody sends here** (TD `osc.tdn` has no out_ue sender) | legacy UE editor python `Content/Python/osc_server.py` binds :8000 and routes to `PortfolioAudio` MPC scalars | DEPRECATED — a ghost receiver for a lane TD never sends. It was live-held by the running editor 2026-09-25. Kill in Phase F; do not extend. |
| — | Spout | TD `/project1/output/spout_show_field` → `TD_Faraway_WorldField` (128×128 RGBA field) and `spoutout1` → `TD_Portfolio_Output` (1080p) | **UE: no consumer.** TD `lookdev_hub`/`concert_stage` receive `UE_Beauty`/`Blender_Live` only | Phase E done 09-23; Phase F (UE receiver + alignment canary) OPEN |

**Rule of one:** :9000 is UE→TD. :9002 is bridge→UE (phrase). TD→UE has **no live lane
today** — build it once, in Phase F, on top of this table; never revive :8000 as a second
authority (TD PORTS.md ban stands and is honoured by reality).

## 2. The :9000 collision, resolved (Jev riskiest, p=0.41)

CURRENT_STATE records "phrase bus moved :9000→:9002 — :9000 collided." The second binder
was never named then; identified now: TD's `in_battle` oscinCHOP holds :9000 to receive the
UE rhythm stream (`MelodiaJRPGPresentationRhythmComponent.cpp:192`,
`MelodiaMusicClockSubsystem.h:116`). The phrase bus tried to LISTEN where UE already SENDS
and TD already binds. Consequence for Phase F: **any native UE listener must NOT bind
:9000** — the inbound TD→UE lane gets its own new port (next free, :9003, or reuse the dead
:8000 slot ONLY after `osc_server.py` is deleted, with this table updated in the same
commit). UDP re-binding over a live listener silently drops — AGENTS rule family / PORTS
rule 1.

## 3. The signal vocabulary — one musical object, four dialects

| Concept | Phrase bus (:9002, `melodia.phrase/v1`) | TD conductor bus (22ch) | TD world_field (Spout RGBA) | UE World Field Bus / MPC | osc_routing.json v1.1 |
|---------|------------------------------------------|--------------------------|------------------------------|---------------------------|------------------------|
| Musical energy | `energy` 0..1 | `audio_*` (RMS bands, onset) | R = density | **Tension** 0..1 (amplitude-derived) | `melodia_audio.bass` (fake: BattleIntensity) |
| Harmonic position | `section`/`trend` (CLIMAX, RISING…) | `osc_*` clock channels | B = phase | **Resonance** (n,m) Chladni tuple | `melodia_audio.treble` (fake: cos²) |
| Pulse | `pulse` / `boundary_pulse` | `h*`+beat gates | G = kinetic energy | **BeatPulse** (clock passthrough) | `rhythm.beat_pulse` (real, UE→TD :9000) |
| Confidence | `conf` (0.9 proven) | — | A = elevation ±1 | — | — |
| Structure | `phrase` idx, `bar` (bar 42 proven) | `scene_idx` | 6 named states QUIET_DAWN…AFTERIMAGE | seed 20260829 determinism | `time.*` |

Mapping law for Phase F: TD→UE signals arrive as **new named lanes**
(`TDBand_Sub/Low/Mid/High/Air`, `TDField_*`). The legacy `Bass/Mid/Treble` MPC scalars
(89 bound assets) keep their current meaning; renaming or re-pointing them is an owner
ruling, not an audio task. The fake lanes remain documented-as-fake in
`melodia-audio-architecture` until an owner migrates them opt-in.

## 4. Phase sequence (agreed 2026-09-25)

- **O1 (this doc + PORTS.md corrections)** — done 2026-09-25, agent-side, no editor.
- **O5** FL live run (`wire_fl_audio_in.py`, 48 kHz lock) — no UE dependency; feeds TD's
  real FFT so Phase F carries true signal.
- **O2/O4** beat hits + ambience — UE-internal, proceed per the 09-25 audio plan audit
  (`P2_BEAT_HITS` jev-live p=0.46).
- **O3 = Foundry Phase F** — native UE inbound listener (new port per §2) + `TD_Faraway_
  WorldField` alignment canary + delete `osc_server.py` ghost. Needs a closed-editor build
  window (owner-scheduled; Jev scored needs_human for STARTING at 0.32 — the doc/bridge
  half is agent-side, the build half waits for the window).
- Risk pins to verify before O3 code: `A_ZERO_BINDING_CENSUS_REAL` (Monolith reflection,
  not grep, for Blueprint-side listeners) and `A_SPOUT_NATIVE_FEASIBLE` (OSC mirror of the
  128×128 field is the fallback if no Spout plugin lands).
