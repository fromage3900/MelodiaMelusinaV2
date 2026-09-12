# Audio-Reactive Flower — CHOP → OSC 9000 Handoff 2026-09-02

## Network description

**TD container:** `/project1/melodia_audio` (new — does not touch `/project1/osc` or legacy `/project1/audio`)
**Port:** `9000` ONLY — single source of truth per sprint. No listener on `9870`.

```
audiodeviceinCHOP audio_in (live mic, 44.1kHz, async)
audiofileinCHOP  file_in  (loop, set par.file to Content/Audio/128BPMarpeggiomelody.wav)
        ↓
switchCHOP source_switch  [0=device, 1=file] default 1 (no mic needed for validation)
        ↓
spectrumCHOP spectrum  (2048 Hann, 50% overlap — inspector only, bands use filtered RMS)
        ↘ filter_bass   audiofilter low-pass  ~250 Hz  → analyzeCHOP rms_bass  → mathCHOP gain2 clamp → lagCHOP 0.1/0.35
        ↘ filter_mid    audiofilter band-pass 250-2k   → analyzeCHOP rms_mid   → mathCHOP gain2 clamp → lagCHOP 0.1/0.35
        ↘ filter_treble audiofilter high-pass ~2k     → analyzeCHOP rms_treble→ mathCHOP gain2 clamp → lagCHOP 0.1/0.35
        ↓
mergeCHOP merge_bands (3ch) → renameCHOP rename_bands → nullCHOP audio_hub (viewer hub)
        ↓
oscoutCHOP osc_out  127.0.0.1:9000 + tableDAT osc_mapping
```

**Beat signals (UE→TD on same 9000, from UMelodiaRhythmReactivitySubsystem::Publish):**
Reuse shared `/project1/osc/in_blender` listener on 9000 if present; otherwise scoped `oscinCHOP in_beat` on 9000. Branch:
`sel_beat_pulse` / `sel_beat_phase` (selectCHOP) → `lag_beat_pulse` 0.05 / `lag_beat_phase` passthrough.

All 5 TD-side routes documented in `tableDAT osc_mapping` and `textDAT network_info`.

## New OSC routes (port 9000)

Documented in `deploy/osc_routing.json` group `melodia_audio` (v1.1 2026-09-02):

| Address | Type | Range | Direction | Source | UE target |
|---|---|---|---|---|---|
| `/melodia/audio/bass` | float | [0,1] | TD→UE | CHOP bass RMS 20-250 Hz | `MPC_Melodia_Palette.Bass` → flower scale `1.0+0.15*bass` |
| `/melodia/audio/mid` | float | [0,1] | TD→UE | CHOP mid RMS 250-2k | `MPC Mid` → hue / sway `+0.01*mid` |
| `/melodia/audio/treble` | float | [0,1] | TD→UE | CHOP treble 2k-20k | `MPC Treble` → emissive `0.6*treble` |
| `/melodia/audio/beat/pulse` | float | [0,1] | UE→TD | `UMelodiaRhythmReactivitySubsystem::Publish()` NotifyBeat 1.0 decay 6*DT | alias `/rhythm/beat_pulse` → `Max(VictoryPulse,CommandPulse)` in C++, `BeatPulse` in osc_server |
| `/melodia/audio/beat/phase` | float | [0,1] | UE→TD | `UMelodiaRhythmReactivitySubsystem` | alias `/rhythm/beat_phase` → `BeatPhase` |

Aliases `/rhythm/beat_pulse` and `/rhythm/beat_phase` are canonical C++ addresses; `/melodia/audio/beat/*` is sprint-documented prefix. Both are handled in `Content/Python/osc_server.py` and `battle_osc.py` (`on_beat_pulse` + `on_audio_beat_alias`).

## Files

- ` _TouchDesigner/grandmaster_melodia/scripts/wire_audio_reactive_flower.py` — idempotent TD wiring script (exec in textport or Envoy MCP)
- `deploy/osc_routing.json` v1.1 — adds `melodia_audio` group
- `Content/Python/gmm/game/battle_osc.py` — adds `on_audio_bands()` / `on_audio_beat_alias()` + `status()` audio_reactive_routes
- `Content/Python/osc_server.py` — adds handlers for 5 new routes (port-agnostic, works on 8000 legacy or 9000 single-truth)
- `Tools/validate_audio_reactive_osc.py` — 38-check loopback probe (no TD/UE needed)

## Validation

```
python Tools/validate_audio_reactive_osc.py
# 38 pass, 0 fail
# loopback on 127.0.0.1:9000 received all 7 addresses (5 new + 2 aliases)
Report: Saved/Audit/audio_reactive_osc_validation.json
```

**TD OSC monitor (manual):**
1. Run TD script: `exec(open('.../wire_audio_reactive_flower.py').read())` in textport → prints `MELODIA_AUDIO_REACTIVE: wired 23 OPS` + `OSC_OUT: 127.0.0.1:9000`
2. Set `file_in.par.file` to a WAV, `source_switch.par.index = 1`, play → `audio_hub` viewer shows 3 channels 0-1 moving.
3. Dialogs → OSC Out → confirm `127.0.0.1:9000` firing. No second listener on 9870 (script prints warning if found; validation checks absent).
4. PIE: drive `MPC_Melodia_Palette` B/M/T + BeatPulse/Phase → `M_Flower_Audio` WPO/emissive. C++ heartbeat at 0.5 Hz keeps stream alive at rest.

## Constraints satisfied

- Port 9000 only (task forbids second channel on 9870) — verified static + runtime.
- Extends existing OSC channel (does not duplicate battle OSC).
- BeatPulse/BeatPhase sourced from `UMelodiaRhythmReactivitySubsystem::Publish()` when available (fallback math aliases in TD script).
