# Universal Bilingual Melusina Voice System — Intake & Research (2026-08-11)

Deep intake on the voice-synth research lane, with the three expanded research tracks
(Adachi Rei construction method, DiffSinger vocoder gate, procedural singing synthesis)
folded in. Owner decisions recorded at the bottom.

## 1. Verified current state

### Spoken voice (EN) — WORKING, partially wired
- **TTS server**: `C:\EnvironmentPortfolio\VoiceSynthResearch\tools\melusina_tts_server.py`
  (FastAPI :8765, **Fun-CosyVoice3-0.5B** — natively 9 languages incl. ja/en, zero-shot
  cloning off anchor seed `Melusina_EN_TTS_Demo_v0.1\anchor_vc_seed_v1_30s.wav`; profiles
  default/gentle/whisper/nordic). **Bug: `locale: en|jp` param is declared but never read** —
  `infer()` always calls `inference_instruct2`; no per-locale branch, no ja regression test.
- **UE assets**: 14 `mel_*.wav` + `.uasset` at `/Game/Melodia/Characters/Melusina/Audio/`
  (handoff said 13; `mel_intro_greeting` is a 14th). All EN.
- **Dialogue source**: `melusina_bard_dialogue.json` (13 lines, `language: "en"`, 4 profiles).
- **Wired**: only `mel_perch_01`/`_03` via `$ Voice` in compiled `MelodiaMorningIntro`
  (43 stmts). All five `.qsc` files contain **zero** `$ Voice` and **zero CJK** text.
- **QuillScript contract**: `$ Voice {&/Game/...} <vol>` → `AQuillscriptInterpreter::Voice`
  (voice channel, auto-stop per line, `VoiceTypingSpeed` pacing). Localization machinery
  exists (`FText`, `Localize`, `TurnOffLocalization`, string tables) — untested for CJK fonts.

### Japanese spoken proof — EXISTS, not integrated
- `tools/run_jp_vc_test.py` + `release_candidate/jp_vc_test/`: **8 JA lines rendered through
  the Melusina anchor** (edge-tts ja-JP-NanamiNeural → CosyVoice `inference_vc`). This proves
  bilingual *spoken* voice works with the current anchor today.

### Singing (DiffSinger/OpenUtau) — BLOCKED on the vocoder gate
- `Melusina_JA_Final/`: 677 WAVs, 340/575 VCV + 66/115 CV; **51 CV + 255 VCV missing**
  (`RECORDING_LIST.txt`, 379 lines).
- `melusina_unified_voicebank/` + `melusina_bilingual_phase2/` + `melusina_bilingual_final_synthetic/`:
  bilingual acoustic+variance ONNX (en+ja dicts, `onnx.checker` clean, style presets
  `cute_feminine_bright` etc.). Waveform gate failed (hiss/noise; OpenUtau "Part result not found").
- **Corpus spec**: `release_candidate/data/bilingual_corpus_spec.json` (JA CV/VCV 115 units,
  EN ARPAbet 39 units, 6 modes × 6 intonations × 4 registers) + `parallel_phrase_manifest.csv`
  (720 tagged EN/JA prompts). Note: `MELUSINA_VOCAL_SUITE_INDEX.md` points at
  `prototype/bilingual_corpus_spec.json` — **stale path**, real files are under `release_candidate/data/`.

### R&D corpus
- `rendered_audio_audit.json`: 1099 probe WAVs, 1027 pass / **72 fail** (liminal_glass set,
  peak 26868 — clipping). `PROCEDURAL_VOICE_RND_PLAN.md` (7-phase bilingual plan, Tidal
  Equation lead anatomy) is the standing strategy doc.

## 2. Research track A — Adachi Rei construction method (delegated, returned)

Recovered the creator's (missile39) own memos; method is now implementable, not just folklore:

- **Vowels**: "very simple CSM/sine-wave (additive) synthesis" → heavily stacked harmonics so
  the voice survives UTAU resampling. Vowel-first: vowels carry perceived identity.
- **Consonants**: synthesized non-voice source (xylophone-derived) run through the **Vocalizer**
  formant-filter VST (the community-standard inanimate-bank toolchain: Audacity + Vocalizer),
  then waveform-level repair in Audacity.
- **The four join rules (his "law", the highest-value artifact)**:
  1. V→V (diphthong-like): fade V1 out under loosely-overlapped V2 fade-in.
  2. V→C→V (e.g. ひゃ): V1 fade-out + C2 fade-in, no overlap trickery.
  3. Pseudo-diphthongs are C1+V1+V1.1+V2 — ふぁ = f+u+w+a ("ふゎ"), NOT ふ+あ fade.
  4. Voiced consonants (ざ): gradual noise→voiced opening ramp, never a splice.
- **Waveform gate**: units too dense/muddy render raspy in UTAU — fix the waveform, not the oto.
- **Bank scale**: 50 sounds + α is a complete hand-tunable CV bank; TIPS resampler + flat
  envelopes; frqeditor for aperiodic sources.
- **Lineage proof**: tiny artificial CV → fan VCV / English C+V / Spanish / French CVVC /
  **DiffSinger 12-language** / VOCALOID5 concat / VOCALOID6 AI. The tiny-artificial-bank →
  neural-seed chain is validated.
- **Physics next step**: Kiguchi Nodoka (explicitly "inspired by Adachi Rei") = tube-segment
  tract simulation, time-varying glottal source, physically-injected turbulence — fixes
  diphthongs/stops/clusters that static formant filters cannot (https://nodoka.onyon.me/).
- **Licensing**: technique safe to imitate. Rei WAVs, Replivoice (A.I.VOICE) output, VY1/VY2,
  miki (a real human provider's voice) — all excluded from the pipeline. Rei's own consonants
  are reusable under license but the project's stricter provenance gate (no Rei samples) stands.

## 3. Research track B — DiffSinger vocoder gate (delegated, returned)

Root cause is **not** a mel/hop mismatch (48k/128/hop512 numbers all match):

1. **The shipped `vocoder.ckpt` is the step-10 smoke** — MD5-identical
   (`EAAA179F0DB328CF3B6A7A81E035120F`) in every bank, = ~5 real optimizer updates vs the
   ~2000 the upstream recipe expects ("少量数据差不多 2000 步"). Output is a pretrained-44.1k
   generator driven by a foreign 48k mel domain at near-zero LR (5000-step warmup on 100-step
   runs → LR never left the floor). Measured: RMS 0.025–0.066, ZCR 0.014–0.046, lo/hi energy
   322–4964 — sine-excitation-dominated, not white hiss.
2. **Both stalled fine-tunes died at the same byte-identical point** (sanity plots done, no
   checkpoint, 3-byte hparams) — a deterministic first-batch hang; the 84-clip
   `expanded_48k_long` run trained fine to step 400. **Training data dir is gone**
   (`VoiceSynthResearch/data/` missing; only `C:\EnvironmentPortfolio\data\corpus_alpha_jd2`
   (22 wavs) + `melusina_cute_vcv_interim/wavs` (111) survive) — no re-run can start today.
3. **OpenUtau "Part result not found"** = `dsdur/` folder missing (files at bank top level),
   dictionary in DiffSinger `*.txt` format instead of OpenUtau `dsdict-*.yaml`, and wrong
   default phonemizer (`DiffSingerJapanesePhonemizer` on a bilingual bank → use
   `OpenUtau.Core.DiffSinger.DiffSingerPhonemizer`).
4. **The fix already exists in the repo**: `openutau_vocoder_onnx_step300/` satisfies every
   OpenUtau renderer check and was never wired in.

**Decision table** (from research): promote step-300 ONNX as interim (unblocks gate now) →
fix the NSF-HiFiGAN fine-tune as the real fix (canonical `ft_hifigan.yaml`: batch 10,
warmup ≤1000, max_updates 4000 (~2000 real), no bf16, freeze MPD optional, `nccl_p2p: false`
if stuck). Reject BigVGAN/iSTFTNet/WaveRNN/UnivNet for this corpus size.

## 4. Research track C — Procedural singing synthesis (done in-session)

- **VocalTractLab 2.4** (Dec 2025): GPL, Windows GUI + **API + source in the zip**; gestural
  scores + speaker files (a child speaker is even included); articulatory → continuous tract
  motion, glottal source control. API is the route for batch rendering (2.1b shipped
  Matlab/Python examples; 2.4 API ships with binaries+source). This is the plan's Stage-1
  renderer, now confirmed capable of sustained F0 control for singing.
- **Praat KlattGrid**: scriptable parametric singer with exactly the Tidal Equation parameter
  set — Pitch, Flutter, Voicing amplitude, Open phase, Power1/Power2, Collision phase,
  **Spectral tilt**, Aspiration, **Breathiness**, Double pulsing, 6 oral + nasal + tracheal +
  frication formants. A KlattGrid can render sustained notes with vibrato and breathiness
  contours (the minimal script is 3 lines). Best diagnostics/identity-oracle tool.
- **Pink Trombone**: sketching only (browser, no batch API).
- **Kiguchi Nodoka** is the working precedent that the whole pipeline is feasible: physics
  tract simulation → shipped VCV JA / VCCV EN / VCV KO / toki pona banks, moresampler
  recommended. Its failure-mode notes (diphthongs/stops/clusters need continuous tract
  motion) are the exact argument for VTL over static formant filters.
- **DiffSinger corpus format** (BestPractices, fetched): raw dataset = `wavs/` +
  `transcriptions.csv` with `name, ph_seq, ph_dur` (acoustic) + `note_seq, note_dur`
  (variance); language-prefixed phonemes (`ja/o`, `en/eh`) with `merged_phoneme_groups`
  + `use_lang_id` for cross-lingual sharing; variance params energy/breathiness/voicing/
  tension — **never energy+breathiness+voicing together**; pitch via parselmouth/rmvpe/
  harvest; hnsep via world/vr; DS files can replace WAV-derived variance attributes
  (`binarization_args.prefer_ds: true`). This is the exact metadata conversion path the
  procedural renderer must emit.
- **Verdict**: VTL (renderer) + KlattGrid (identity oracle/diagnostics) + the existing
  720-prompt parallel corpus → procedural bilingual singing corpus → DiffSinger acoustic +
  variance → vocoder per track B. All open-source, license-clean.

## 5. Gaps to the "universal bilingual" system

| # | Gap | Where | Effort |
|---|---|---|---|
| 1 | `locale` param declared, never read | `melusina_tts_server.py:51` | Easy |
| 2 | No JA voice profile in `VOICE_PROFILES` | server `:61-78` | Easy |
| 3 | 8 JP spoken WAVs exist, never imported/wired | `jp_vc_test/` vs `Content/Melodia` | Easy |
| 4 | Zero Japanese dialogue content; CJK font unverified | all `.qsc` + dialogue JSON | Medium |
| 5 | 12 of 14 lines unwired | only `mel_perch_01/03` | Easy |
| 6 | **No UE voice authority** (line registry keyed by line_id × locale × profile × render seed) | `Source/` — zero VoiceLine/VoiceSubsystem/Locale code | **Architectural** |
| 7 | Vocoder gate: smoke checkpoint shipped, fine-tune stalls, data dir gone | track B | Hard (blocks ALL singing) |
| 8 | JA VCV bank incomplete (306 units missing) | `Melusina_JA_Final/RECORDING_LIST.txt` | Hard (singing) |
| 9 | No render provenance (seed/model/profile) beside assets | pipeline + UE | Medium |
| 10 | Stale path in `MELUSINA_VOCAL_SUITE_INDEX.md` (`prototype/` vs `release_candidate/data/`) | index doc | Trivial |
| 11 | 72 failing probe WAVs (liminal_glass clipping) unaddressed | `rendered_audio_audit.json` | Low |

## 6. Owner decisions (2026-08-11)

1. **Singing is a dedicated research track**, Adachi-Rei-inspired (procedural, no human
   provider) — tracks A–C above are its research base.
2. **UE voice registry (gap 6) is approved** as the missing architecture — the
   "universal" layer.
3. **JP content pass (gaps 3–4) approved**.
4. Evidence standard = **WAV analysis + owner listening** (not blind panels): the 8-metric
   gate from track B (finite/length, DC offset, RMS ≥0.05, ZCR 0.05–0.15, lo/hi 10–300,
   noise floor ≥25 dB below fundamental, gt-reconstruction SNR ≥15 dB, then owner listening
   on JA + EN + key-shift deltas).

## 7. Recommended build order

1. **Unblock the vocoder gate now**: wire `openutau_vocoder_onnx_step300` into a bank
   (`dsvocoder/` + `dsdur/` + character.yaml phonemizer fix) → owner-listen the EN + JA
   probes. (Track B §4)
2. **Server**: branch on `locale`, add `melusina_jp_*` profiles, add a ja regression line.
3. **UE voice registry**: `UDataAsset` (line_id → per-locale text/sound/profile/provenance)
   + `UMelodiaVoiceSubsystem` handed to `$ Voice`; locale = player setting.
4. **JP content pass**: import the 8 existing JA WAVs, render 13 JA counterparts, author
   JA dialogue variants, verify CJK font in the QuillScript widget.
5. **Procedural singing**: VTL/KlattGrid renderer for the Tidal Equation anatomy → emit the
   DiffSinger corpus format → train acoustic+variance → vocoder fix → stems.
6. **Evidence**: render-seed provenance + WAV-metric + owner-listening gates on every render.

## 8. Related docs

- `Docs/Handoffs/MELODIA_VOICE_QUILLSCRIPT_HANDOFF_2026-08-01.md` — spoken voice → QuillScript
- `Docs/AUDIO_IMMERSION_PLAN_2026-08-09.md` — mixing architecture, SCL_Voice/submixes
- `C:\EnvironmentPortfolio\VoiceSynthResearch\PROCEDURAL_VOICE_RND_PLAN.md` — standing strategy
- `Docs/MELUSINA_MARKETING_INTRO_PREP_2026-08-02.md` — singing-lane roadmap (SynthV/SVC path)
