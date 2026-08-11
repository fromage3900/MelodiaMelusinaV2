# Melodia Voice → QuillScript handoff (Kiro + owner)

**Date:** 2026-08-01
**Dependency:** None. All assets below exist and are saved in the running editor.
**Scope:** Spoken Melusina voice wired inline into QuillScript dialogue. Singing (DiffSinger) is a
separate lane; see §4.

---

## What shipped this session

1. **13 Melusina spoken WAVs rendered** via the CosyVoice 3 server
   (`C:\EnvironmentPortfolio\VoiceSynthResearch\tools\melusina_tts_server.py`, port 8765, anchor seed
   `Melusina_EN_TTS_Demo_v0.1\anchor_vc_seed_v1_30s.wav`) and **auto-imported as USoundWave** at:

   ```
   /Game/Melodia/Characters/Melusina/Audio/mel_<beat>_<nn>
   ```

   | Asset | Line | Profile |
   |---|---|---|
   | `mel_perch_01` | "The perch is empty again…" | default |
   | `mel_perch_03` | "Sir Melodious? Is that you?…" | gentle |
   | `mel_arrival_01` / `_02` | post-festival arrival texture | default / gentle |
   | `mel_halfsong_01` / `_02` | half-song, place that still listens | whisper / gentle |
   | `mel_road_01` / `_02` | the road, the rehearsed phrase | default / gentle |
   | `mel_battle_entry` | "The dream is restless…" | default |
   | `mel_reunion_01` | "You were never too late." (the one named moment) | gentle |
   | `mel_snackrun_01` | "He does this…" | default |
   | `mel_dream_01` | bridge-gone catastrophe (dream) | whisper |

   All 13 verified in the editor as `SoundWave` class, asset registry registered.

2. **`melusina_bard_dialogue.json` authored** at
   `Content\Melodia\Characters\Melusina\melusina_bard_dialogue.json` — bard register line-set from
   the grief hook (feel-first/name-once; Sir alive; absence-with-shape; reunion named once). This is
   the authoring source of truth for Melusina's spoken lines. The stale
   `melusina_dialogue.json` (Threshold-Guardian framing) is **untouched** — decide separately whether
   to archive it.

3. **`$ Voice` wired inline** into `MelodiaMorningIntro` (2 lines so far):

   ```
   - Melusina
     The perch is empty again. I know a small absence can fill a whole room.
     $ Voice {&/Game/Melodia/Characters/Melusina/Audio/mel_perch_01} 0.9

   - Melusina
     Sir Melodious? Is that you? The quiet petal is humming again.
     $ Voice {&/Game/Melodia/Characters/Melusina/Audio/mel_perch_03} 0.9
   ```

   Recompiled via `CompileQuillSource` (43 statements), saved. Verified: Statements 2 & 4 carry the
   `Voice` commands with correct `{&/Game/...}` refs and volume. Zero errored blueprints.

---

## How it works (verified in code)

- `$ Voice {&/Game/...} <volume>` maps to `AQuillscriptInterpreter::Voice(USoundBase*, float)` —
  a `UFUNCTION(BlueprintCallable)` (`QuillscriptInterpreter.h:461`), dispatched through
  `ExecuteCommand` → `CallFunction` → `CallMemberOnTarget` (`QuillscriptInterpreter.cpp:1482/2128`).
- The `{&/Game/...}` parameter resolves via `UQuillscriptAsset::FindScriptReference` → asset load
  (`QuillscriptAsset.cpp:334`). Full object path works: `{&/Game/Melodia/Characters/Melusina/Audio/mel_perch_01}`.
- Voice plays on the **"voice" channel** and is **auto-stopped at the next dialogue line**
  (`QuillscriptInterpreter.cpp:582-585`) — so per-line spoken audio needs no custom C++.
- `VoiceTypingSpeed` uses the sound duration to pace text reveal (`:1382`) — longer lines will feel
  naturally timed once a voice is attached.
- Command must sit on its own line in the `.qsc`/source text (any indentation); it attaches to the
  preceding statement.

---

## Kiro's checklist (PIE + Development package)

1. Open `L_MelusinaMorning`, `Alt+P`. Confirm the two opening Melusina lines speak.
2. Confirm each line's voice **stops** when the next dialogue line appears (auto, plugin handles it).
3. Confirm the voice ducking/mix sounds right vs. ambience; adjust the trailing volume float (0.9)
   in the `.qsc` if needed — no Blueprint change required.
4. Verify the option branches (`Reunion` / `Listening`) and the battle path still behave — the two
   Voice commands must not affect branching or the battle notify chain.
5. **Save/load gate:** let the first dream resolve, save, full-restart, load — no double-play of the
   voice, no stale audio.
6. **Development package gate:** cook and run the authored loop in a Development build; confirm the
   SoundWave references resolve (packaging refs come from the `{&/Game/...}` strings in Statements).

## Owner's checklist

- Decide the fate of `melusina_dialogue.json` (stale guardian framing) — archive or leave.
- Wire more lines: `mel_reunion_01`, `mel_battle_entry`, and the dream register can be attached to
  their authored beats exactly like the two examples above.
- For **Sir Melodious** there is no voice yet. He is the answering voice (psych reference rule):
  give him a voicebank before any of his lines get audio.

---

## How to render more lines (port 8765)

```powershell
# Server (CosyVoice 3, anchor seed):
python C:\EnvironmentPortfolio\VoiceSynthResearch\tools\melusina_tts_server.py
# Health:
curl http://127.0.0.1:8765/health
# One line (default profile):
curl -X POST http://127.0.0.1:8765/v1/synthesize ^
  -H "Content-Type: application/json" ^
  -d '{"text":"...","style":"Speak naturally, clear feminine voice."}'
# Profiles: melusina_default / melusina_gentle / melusina_whisper / melusina_nordic
```

Drop the WAV into `Content\Melodia\Characters\Melusina\Audio\` and let UE auto-import
(24 kHz mono from CosyVoice; UE accepts as-is). Naming: `mel_<beat>_<nn>.wav`, keep ids in
`melusina_bard_dialogue.json` in sync.

---

## Singing lane (separate — Phase 2, G: drive)

Singing banks are **not** in UE. They live at
`C:\EnvironmentPortfolio\VoiceSynthResearch\release_candidate\` (DiffSinger/OpenUtau package +
CosyVoice speech). The open blocker before any singing asset can be imported is the **vocoder gate**:
`melusina_unified_voicebank\ENGINE_COMPATIBILITY.md` records a hop-size/vocoder mismatch producing
hiss/noise on the packaged ONNX model. Fix that (NSF-HiFiGAN at the acoustic's exact hop length,
validate via OpenVPI `infer.py` + OpenUtau render) before rendering the half-song or reunion stems.

## Files touched this session

- `Content\Melodia\Characters\Melusina\melusina_bard_dialogue.json` (new)
- `Content\Melodia\Characters\Melusina\Audio\mel_*.wav` + auto-imported `.uasset` (13 new)
- `Content\MelodiaIntegration\Narrative\MelodiaMorningIntro.uasset` (recompiled source: 2 Voice commands)

## Evidence

```
TTS SERVER:        UP (CosyVoice 3, 24kHz, anchor seed loaded)
WAV RENDERED:      13/13
UE AUDIO ASSETS:   13 SoundWave under /Game/Melodia/Characters/Melusina/Audio
QUILL RECOMPILED:  MelodiaMorningIntro -> 43 statements, saved
VOICE COMMANDS:    STMT 2 (mel_perch_01), STMT 4 (mel_perch_03)
ERRORED BPS:       0
DIRTY PACKAGES:    only L_FallenMoon (pre-existing, unrelated)
```

## Stop conditions

- Do not add a second voice authority. `$ Voice` inline is the contract; the `"voice"` channel owns
  stop/start per line.
- Do not wire audio into `melusina_dialogue.json` without first archiving/replacing its guardian
  framing.
- Do not import DiffSinger singing stems until the vocoder gate passes.
- Do not save unrelated portfolio/Melodia maps.
