# Melusina Voice Recovery Handoff — 2026-09-22

## Purpose

Recover and validate the surviving provenance-clean Melusina singing lineage before retraining or production promotion.

## VERIFIED

- Creative authority: `Docs/Music/MELUSINA_PERFORMANCE_PERSONA_BIBLE_2026-09-08.md`.
- Voice continuum: speech -> pitched speech -> hum -> sung line -> full performance.
- Recoverable workspace: `D:/Backups/Melodia/trimmed/VoiceSynthResearch`.
- Python 3.11 environment: `D:/Backups/Melodia/trimmed/VoiceSynthResearch/tools/venvs/diffsinger-py311`.
- ONNX Runtime export environment: `D:/Backups/Melodia/trimmed/VoiceSynthResearch/tools/venvs/diffsinger-export-py311_trimmed`.
- Bilingual exported voicebank:
  `D:/Backups/Melodia/trimmed/VoiceSynthResearch/DiffSingerProject/Melusina_Synthetic/voicebank`.
- Voicebank bundle contains acoustic, linguistic, duration, pitch, and variance ONNX graphs; EN/JA dictionaries; phoneme/language metadata; `dsconfig.yaml`; `vocoder.ckpt`; and `vocoder.json`.
- `dsconfig.yaml` declares 48 kHz output and bilingual EN/JA support.
- EN and JA `.ust`/`.ustx` candidate projects exist for `cute_feminine_bright`, `soft_punk_husky`, and `opera_tide`.
- Bilingual DiffSinger checkpoints and probe renders exist in the recovered workspace.
- Owner correction recorded: Melusina's identity was synthesized from a neural seed. The recovered workspace contains a visible procedural/VTL generation trace, but this audit does not equate that trace with the identity seed.
- Diffusion-SVC source exists, but no trained production Diffusion-SVC checkpoint was found in its `exp` directory.
- The maintained OpenVPI DiffSinger source and matching 48 kHz vocoder export were hash-recorded in `diffsinger_calibration_attempt.json`; the selected `model_ckpt_steps_20000.ckpt` failed PyTorch archive integrity before model construction and is rejected.
- Official OpenUtau v0.1.565 launched from the local audit install, but its log recorded no project load or WAV export.
- Authored UNDERTOW calibration inputs now exist at `studio/tracks/frost-rave/UNDERTOW_EN_HOOK.ds` and `UNDERTOW_JA_PRE.ds`.
- The recovered bilingual acoustic ONNX bank plus an audit-only ONNX vocoder adapter rendered both authored probes at 48 kHz; manifest: `Saved/Audit/melusina_voice_final/renders/diffsinger_onnx_candidate/render_manifest.json`.
- The render is objective-QA pending owner listening: non-silent and unclipped, but rough pitch diagnostics show discontinuities in these short probes and no production promotion has occurred.

## PROMOTED TO CALIBRATION CANDIDATE

`D:/Backups/Melodia/trimmed/VoiceSynthResearch/DiffSingerProject/Melusina_Synthetic/voicebank`

This is the strongest surviving bilingual singing artifact. It is not yet final: owner listening, objective QA, and provenance review remain open.

## JEV DECISION — 2026-09-22

- First calibration style: `cute_feminine_bright` — confidence `0.96`.
- First performance persona: `Lead` — confidence `0.97`.
- First Drop B harmony test: `octave` — confidence `0.36`, intentionally reversible.
- First QA emphasis: `bilingual_intelligibility` — confidence `0.86`.

## REJECTED / QUARANTINED

- Do not promote the highest-step checkpoint solely because of training step count.
- Do not train on Adachi Rei, VY1/VY2, miki, Replivoice/A.I.VOICE, or recognizable unlicensed artist material.
- Do not revive the old Diffusion-SVC scaffold as production authority without checkpoint, config, corpus manifest, and inference proof.
- Do not treat the legacy Style-Bert-VITS2 server as CozyVoice; its configured model is absent.

## NEXT

Link the authorized neural-seed record and recover an intact checkpoint, or use the new bilingual ONNX candidate plus the existing step300/refine1000 audition renders for owner listening while repairing the reproducible export path. The 2026-09-22 pinned-source attempt reached checkpoint load and rejected `model_ckpt_steps_20000.ckpt` for archive corruption before creating a WAV; no checkpoint was promoted. Complete pitch/timing/formant/listening review before deriving stems. Keep owner listening as the final artistic gate.

Evidence root: `C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/melusina_voice_final/`.
