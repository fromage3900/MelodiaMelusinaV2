# Project-wide Immersion & Audio Plan — BS_GodFile (2026-08-09)

Status: **Phase A+B in progress, built via Monolith.** C++ changes staged for the next
closed-editor rebuild.

## Current state (before this pass)

- Audio plumbing existed but was **quarantined**: `PlayBGM`/grade tones/metronome lived in
  `UMelodiaBattleSession` / `MelodiaRhythmExecutionComponent`, which nothing instantiates.
  The live battle path (`BP_BattleController` + `MelodiaJRPGPresentationRhythmComponent`)
  started the Quartz clock but played **nothing**.
- One BGM asset (`SW_BGM_Battle_Placeholder_128`), one UI SFX (`A_UI_Bubble`), ~116
  CosyVoice lines (113 unwired), ambience BP placed in no gameplay map.
- No SoundClasses / submixes / attenuation authored (engine defaults only).

## Done in this pass

### Assets imported (from drive scan)
| Asset | Path | Source | Use |
|---|---|---|---|
| `SW_BGM_Battle_Duvet_Cover` | `/Game/Melodia/Audio/BGM/` | Duvet cover render (93 BPM, 211 s) | Default battle BGM |
| `SW_BGM_Zundamon_Sewaa_Full` | `/Game/Melodia/Audio/BGM/` | Sewaa mix (131 BPM, 155 s) | Fast-skill battle BGM |
| `SW_BGM_Zundamon_Sewaa_Inst` | `/Game/Melodia/Audio/BGM/` | Sewaa instrumental | Alt/clean BGM |
| `SW_BGM_Zundamon_Stem_Vox_*` (11) | `/Game/Melodia/Audio/BGM/` | Sewaa vocal stems | Remix/singing later |
| `UI_Blip_a..w` (26) | `/Game/Melodia/Audio/SFX/UI/` | Zundamon kitchen | UI/menu blips |

All BGM assets: **looping enabled**, assigned to `SCL_Music` + `SUBMIX_Music`.

### Mixing architecture (authored, verified)
```
/Game/Melodia/Audio/Mix/
  SoundClasses/  SCL_Master, SCL_Music, SCL_SFX, SCL_Voice, SCL_Ambience
  Submixes/      SUBMIX_Music, SUBMIX_SFX, SUBMIX_Voice, SUBMIX_Ambience
```
Assignments: BGM → SCL_Music/SUBMIX_Music; A_UI_Bubble → SCL_SFX/SUBMIX_SFX;
A_Ambience_Melusina_98bpm → SCL_Ambience/SUBMIX_Ambience.
(SCL_Voice exists for dialogue-ducking; the SoundMix override to the new classes is the
next mixing step.)

### C++ wiring (staged; needs closed-editor rebuild)
`MelodiaJRPGPresentationRhythmComponent` (live battle path):
- `BeginPlay`: binds `OnMelodiaBeat` + calls `PlayBGMQuantized()` when audio present
  (works with or without Quartz fallback — binds before the early-out).
- `RecordTimingError`: per-hit grade tone via `PlayHitSFX(Grade)` (880/660/440/220 Hz).
- `HandleMelodiaBeat`: metronome click per integer beat (flag `bPlayMetronomeClick`).
- `EndPlay`: unbinds beat, stops BGM.
- New flags: `bPlayBattleBGM`, `bPlayMetronomeClick`.

`MelodiaAudioComponent`:
- `PlayBGMQuantized()` now mirrors `PlayBGM`'s sourcing chain: Sewaa for
  `tempo_shift`/`crescendo_wave` → Duvet → placeholder.
- New `SetCurrentSkill(FName)` for per-skill BGM selection.

## What the user asked: how to make the rhythm game stand out

1. **A protagonist who sings your battle music.** Melusina has an OpenUtau/DiffSinger
   voice (3,057 probe wavs + training models at `F:\Backups\Melodia\...\VoiceSynthResearch`).
   The Duvet cover is the proof. Roadmap: original sung loop → chart aligned to sung
   phrases. The Sewaa vocal stems show the pipeline works at 131 BPM.
2. **The world is the metronome.** `MPC_Melodia_Palette` (18 scalars) already pulses the
   toon master. Complete adoption: foliage, candles, water, props via the MPC.
3. **The library chooses your song (quantum).** Quantum ranker exists; feed it 3-5 real
   authored patterns + the two real tracks. (Quantum lane: separate agent.)
4. **QuillScript dialogue interleaved with notes.** 113 unused voice lines, incl.
   `sor_rhythm_intro_01`, `mel_battle_entry`, 9 battle-tagged lines. Author 6-10 battle
   interjections.
5. **OSC → TouchDesigner** (127.0.0.1:9000) built — streamed/recorded performances get
   live-reactive visuals.
6. **Tempo contrast**: Sewaa 131 BPM vs Duvet 93 BPM vs placeholder 128 — per-encounter
   tempo band is already the quantum dimension.
7. **Accessibility**: note-hit visibility is toon; add "hearing mode" (pulse + haptics) —
   quality gate `accessibility: pass`.

## Remaining (next sessions)

- **Rebuild** (closed editor): land the C++ wiring + the two pre-existing build-error
  fixes (Piano include — already fixed by its lane; water `AWaterBody` — lane-owned WIP).
- Wire the Sewaa/other BGM per skill id into Blueprint battle flow (`SetCurrentSkill`).
- Import Lyra/JRPG-sample SFX (`.uasset` sources — needs a source-project migration
  session, can't run while this editor is open).
- Place `A_Ambience_Melusina_98bpm` + weather BP in battle/exploration maps (map
  authoring, one editor session).
- SoundMix rebind: point `SM_MelodiaUserPreferences` overrides at the new project
  SoundClasses (currently engine `/Engine/EngineSounds/*`).
- Voice ducking: sidechain SCL_Voice → SCL_Music (needs a submix/sidechain chain).
- Attenuation presets for 3D grade pops / ambient placement.
