# Melusina UNDERTOW Music Handoff — 2026-09-22

## Purpose

Turn the first approved Melusina vocal material into original FL Studio-ready Melodia music.

## VERIFIED

- Workspace: `C:/EnvironmentPortfolio/studio/tracks/frost-rave`.
- Song: `UNDERTOW`, 128 BPM, A minor, Am / F / C / G.
- Existing MIDI: vocal guide, chords, bass.
- Authored source: `UNDERTOW_LYRICS_V2.md`.
- Authored spoken cues: `UNDERTOW_SPOKEN_WORD_SCAFFOLD.md`.
- Authored direction: `UNDERTOW_VOCAL_DIRECTION.json`.
- Authored melody: `UNDERTOW_v2_melody_scaffold.mid`.
- Form: INTRO / VERSE / PRE / DROP_A / BREAK / DROP_B / OUTRO.
- Existing spoken identity reference: `studio/voice-tests/melusina_tts_line_test.mp3`, 24 kHz mono, 5.976 seconds.
- Authored DS scaffolds: `UNDERTOW_EN_HOOK.ds` and `UNDERTOW_JA_PRE.ds`.
- Spoken render queue: `BS_GodFile/Saved/Audit/melusina_voice_final/spoken_render_queue.json`.
- Candidate singing probes now exist for the authored EN hook and JA pre; manifest: `BS_GodFile/Saved/Audit/melusina_voice_final/renders/diffsinger_onnx_candidate/render_manifest.json`.
- Fourteen existing Melusina spoken WAV assets are present in `Content/Melodia/Characters/Melusina/Audio`; inventory and hashes: `Saved/Audit/melusina_voice_final/spoken_asset_inventory.json`.

## JEV-DIRECTED FIRST PASS

- Lead lane: `Lead`.
- Drop B first harmony experiment: octave only.
- Do not add thirds until bilingual intelligibility and masking checks pass.
- The harmony choice is low-confidence and remains reversible.

## VOCAL RENDER STATUS

`CANDIDATE_RENDERED_NOT_APPROVED`: the recovered ONNX bank produced short EN/JA probes, but the selected 20,000-step DiffSinger checkpoint remains corrupt and CozyVoice is not recovered. No WAV or stem is being represented as approved.

After approval, derive and preserve the dry family:

`01_LEAD_DRY`, `02_LEAD_TUNED`, `03_DOUBLE_L`, `04_DOUBLE_R`, `05_REFLECTION`, `06_HARMONY_HIGH`, `07_HARMONY_LOW`, `08_WHISPER_TEXTURE`, `09_CHOPS`, `10_REVERSE_OR_TRANSITION`, `11_WET_REFERENCE`.

## FL STUDIO CONTRACT

Groups: DRUMS, BASS, MUSIC, TEXTURE, VOCAL_LEAD, VOCAL_STACK, VOCAL_FX, TRANSITIONS, PRINTS.

Exports: FULL_MIX, DRUMS, BASS, MUSIC, VOCALS, FX; add LEAD_VOCAL and BACKING_VOCAL when stable.

Sections: INTRO, LOOP_A, LOOP_B, BUILD, DROP, BREAK, OUTRO, STINGER.

## BLOCKER

- CozyVoice / CozyVoice runtime and approved model are not located in the audited C:, D:, G:, or user roots; existing spoken assets are present as identity/reference artifacts.
- The selected existing DiffSinger checkpoint is corrupt before render; the new ONNX candidate and existing step300/refine1000 audition lineage still need integrity/listening review.

## NEXT

Link the authorized neural-seed provenance and get owner listening on the new bilingual candidate plus existing audition candidates. Separately recover the approved CozyVoice runtime for INTRO, BREAK, and OUTRO. Once one useful vocal WAV passes the artistic gate, derive the dry stem family and begin the first FL Studio session from the authored MIDI scaffold.

Lyrics and melody are project-authored. No third-party artist stems belong in this production lane.
