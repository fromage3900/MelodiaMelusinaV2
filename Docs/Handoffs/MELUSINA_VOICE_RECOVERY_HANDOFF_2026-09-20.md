# Melusina Voice Recovery Handoff — 2026-09-20

## Purpose

Recover and validate the surviving provenance-clean Melusina singing lineage before any retraining or production promotion.

## VERIFIED

- Creative authority: `Docs/Music/MELUSINA_PERFORMANCE_PERSONA_BIBLE_2026-09-08.md`.
- Narrative voice continuum: speech -> pitched speech -> hum -> sung line -> full performance.
- Recoverable workspace: `D:/Backups/Melodia/trimmed/VoiceSynthResearch`.
- Dedicated Python environment: `D:/Backups/Melodia/trimmed/VoiceSynthResearch/tools/venvs/diffsinger-py311`.
- Dedicated export environment with ONNX Runtime: `D:/Backups/Melodia/trimmed/VoiceSynthResearch/tools/venvs/diffsinger-export-py311_trimmed`.
- Bilingual exported voicebank:
  `D:/Backups/Melodia/trimmed/VoiceSynthResearch/DiffSingerProject/Melusina_Synthetic/voicebank`.
- Voicebank files present: acoustic, linguistic, duration, pitch, variance ONNX graphs; English and Japanese dictionaries; phonemes/languages metadata; `dsconfig.yaml`; `vocoder.ckpt` and `vocoder.json`.
- Voicebank config declares 48 kHz output and bilingual English/Japanese support.
- Recovered test projects include English and Japanese `.ust`/`.ustx` files for cute-feminine-bright, opera-tide, and soft-punk-husky candidates.
- Recovered singing probe audio exists under `tools/openvpi/DiffSinger/artifacts/melusina_cli_probe`.
- Recovered DiffSinger checkpoints include bilingual synthetic and expressive candidates, including `melusina_bilingual_final_synthetic` through step 20,000.
- Recovered Diffusion-SVC source exists at `D:/Backups/Melodia/trimmed/VoiceSynthResearch/tools/Diffusion-SVC`.
- No trained production Diffusion-SVC checkpoint was found in that repo's `exp` directory.

## PROMOTED CANDIDATE

Promote the recovered bilingual exported voicebank to **calibration candidate**, not final production authority:

`D:/Backups/Melodia/trimmed/VoiceSynthResearch/DiffSingerProject/Melusina_Synthetic/voicebank`

Reason: it is the strongest surviving bilingual singing artifact with a complete deployment bundle. It still requires the fixed EN/JA/range/persona calibration suite and owner listening.

## REJECTED / QUARANTINED

- Do not promote `melusina_bilingual_final_synthetic` solely because it reached step 20,000.
- Do not train on Adachi Rei, VY1/VY2, miki, Replivoice/A.I.VOICE, or recognizable unlicensed artist material.
- Do not revive the old Diffusion-SVC scaffold as production authority without a checkpoint, config, corpus manifest, and reproducible inference proof.
- Do not use the legacy Style-Bert-VITS2 server as CozyVoice. Its model directory is absent and its server source is only a recovery reference.

## REQUIRED NEXT ACTION

1. Use the recovered export environment to validate ONNX graph loading and the voicebank metadata.
2. Render the fixed calibration suite in EN, JA, bilingual transitions, low/mid/high range, and four personas.
3. Run objective audio QA: clipping, peak/RMS, silence, duration, pitch tracking, discontinuity, formant stability, timing, and resampling artifacts.
4. Produce a comparison board and request one bounded Jev choice among pre-authored candidates.
5. Promote only after owner listening and provenance review.

## EVIDENCE ROOT

`C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/melusina_voice_final/`

Current audit files include `voice_asset_inventory.json`, `candidate_matrix.json`, `calibration_suite.json`, and `cozyvoice_recovery_manifest.json`.
