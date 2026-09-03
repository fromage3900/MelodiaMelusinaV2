# Melusina Sings — DiffSVC Training + Multi-Program Integration Plan (2026-08-11)

Companion to `MELUSINA_BILINGUAL_VOICE_INTAKE_2026-08-11.md`. This is the **execution plan**:
Adachi Rei construction detail, the concrete DiffSVC training recipe on this machine, and the
path to Melusina actually singing in OpenUtau, TuneLab, SynthV, and UTAU.

---

## 0. What this machine already has (verified 2026-08-11)

| Asset | State | Path |
|---|---|---|
| GPU | RTX 4070 SUPER 12 GB, driver 595.95 | — |
| torch | **2.6.0+cu124, CUDA verified working** in `cosyvoice-py312` venv | `C:\EnvironmentPortfolio\VoiceSynthResearch\tools\venvs\cosyvoice-py312` |
| OpenUtau | 0.1.565 installed | `C:\Program Files\OpenUtau` |
| Synthesizer V Studio Pro | installed (EN/JA/Canto dicts) | `C:\Program Files\Synthesizer V Studio Pro` |
| TuneLab | run 2026-07-29; **ChoristaUtau + moresampler + doppeltler extensions** installed | `%APPDATA%\TuneLab\Extensions\ChoristaUtau` |
| Trained DiffSinger acoustic checkpoints | **REAL, multiple lineages** | `tools\openvpi\DiffSinger\checkpoints\` |
| Trained DDSP-SVC Melusina model | `melusina_phase2` with `vocoder_best.pt` + **504 renders** | `tools\openvpi\ddsp-singing-vocoders\exp\melusina_phase2` |
| Vocoder experiments | nsf_hifigan smoke/stage2/stage3 + nsf_univnet + extended | `tools\openvpi\SingingVocoders\experiments\` |
| Survival corpus | `corpus_alpha_jd2` (22 wavs) + `melusina_cute_vcv_interim\wavs` (111 wavs) | `C:\EnvironmentPortfolio\data\`, `release_candidate\` |
| Tool manifest | `integration\tool_paths.json` (VTL 2.4 listed "working", vLabeler listed) | `C:\EnvironmentPortfolio\VoiceSynthResearch\integration\` |

### What is MISSING / must be rebuilt (hard truth)
- **DiffSinger repo is a partial clone** — no `scripts/`, `basics/`, `configs/` → cannot train
  or run `infer.py` in place. Needs upstream restore (commit `753b7cc6`).
- **Both `diffsinger-py311` venvs are gone** (only `cosyvoice-py312` survives).
- **All training data dirs are gone** (`VoiceSynthResearch/data/` empty;
  `corpus_bilingual_split` referenced by configs does not exist). Only 22 + 111 wavs survive.
- **VTL 2.4 folder gone** from `Downloads` (tool_paths says "working" — stale).
- **vLabeler not extracted**, **MakeDiffSinger partial** (only forced_alignment + variance-temp).
- **No DiffSVC / so-vits-svc / MoeVS anywhere** yet — this is new install work.
- Disk: G: 75 GB free, C: 65 GB free — sufficient.

---

## 1. Adachi Rei — construction detail (the actual recipe, not folklore)

Recovered from missile39's own memos (`mechanical-girl.seesaa.net/article/460135960.html` =
the join-rule memo; `460135623.html` = dev post; `460137223.html` = usage post) and the
community toolchain record (note.com/bntng_777 + Scrapbox 無生物音源制作メモ).

### 1.1 The pipeline Rei used (verified at method level)
1. **Vowels**: "very simple CSM/sine-wave (additive) synthesis" in Audacity — harmonic stacks
   deliberately "盛りまくった" (piled on heavily) so the voice survives UTAU resampling.
2. **Consonants**: synthesized non-voice source (his: xylophone sample) run through the
   **Vocalizer formant-filter VST** (A-Quest) — the community-standard inanimate-bank
   toolchain is Audacity + Vocalizer; then waveform-level repair in Audacity.
3. **Join** by the four rules below, tuned per unit.
4. **Optimize for one resampler**: TIPS (`scientistb.web.fc2.com/program`), flat "ベタ打ち"
   envelopes; UTAU default resampler secondary; per-unit envelope tuning avoided (human-style
   envelopes break some units).
5. **frqeditor** hand-drawn frequency tables for any aperiodic/noise-based unit so UTAU can
   pitch-shift it (makes inanimate sources singable).

### 1.2 The four join rules (his "law" — implement these verbatim)
| Rule | Case | Recipe |
|---|---|---|
| 1 | V→V (diphthong-like, ひぇ = h+i+e) | Fade V1 out under a **loosely overlapping** V2 fade-in. Vowel-to-vowel change is continuous (palatal shape change). |
| 2 | C1+V1+C2+V2 (ひゃ = h+i+y+a) | V1 fade-out + C2 fade-in, **no overlap trickery** — the intervening consonant keeps the vowels distinct. |
| 3 | Pseudo-diphthongs (ふぁ/ふぃ/ふぇ/ふぉ) | **They are C1+V1+V1.1+V2, not C1+V1+V2.** ふぁ = f+u+w+a ("ふゎ"). A naive ふ+あ fade gives "ふあー" — wrong. V1 = small consonant-attached residual vowel; V1.1 = proper standalone vowel acting consonant-like toward V2. |
| 4 | Voiced consonants (ざ) | **Gradual noise→voiced opening ramp**, not "noise + あ". A splice reads as "noise, then あ" ("っあー"). The opening must be IN the waveform. |

### 1.3 Waveform gate (his failure case, reused as our QA rule)
Several prototype units rendered raspy/muffled in UTAU — dense old お waves and muddy
exciter-treated voiced waves. **Fix is at the waveform, never the oto.ini.** Every unit must
pass: period structure clean enough to survive concatenation, no "centipede-leg" voiced waves.

### 1.4 Bank scale economics
50 sounds + α is a complete, hand-tunable CV bank ("50音＋αがあれば…それなりにきれいに歌って
くれる") — this is why the project was possible. Ports then scale it: fan VCV / EN C+V /
DiffSinger 12-language / VOCALOID5/6. The tiny-artificial-bank → neural-seed chain is proven.

### 1.5 What this means for Melusina concretely
- **Vowel-first identity** (vowels carry identity) — our CosyVoice anchor already fixed the
  vowel identity; the singing bank must match its vowel formants.
- **Rule 3 is the canary**: any ふぁ-type unit must be built as residual-vowel + onset vowel.
- **Waveform gate before oto tuning** on every CV/VCV unit.
- **TIPS/flat-envelope** baseline, resampler compatibility matrix documented per bank.
- Licensing: technique is free to imitate; **Rei WAVs, Replivoice output, VY1/VY2, miki** are
  excluded from the pipeline (miki is a real human provider's voice — never touch).

---

## 2. DiffSVC training — the concrete recipe for THIS machine

"DiffSVC" = **Diffusion-SVC** (`CNChTu/Diffusion-SVC`, v1_Stable branch, MIT) — the
actively-maintained diffusion voice-conversion model (successor lineage of prophesier/diff-svc
which is AGPL/archived). It converts **any source singing** into Melusina's timbre. This is the
fastest route to "she sings": compose with any voice, convert to her voice.

### 2.1 Install (new work)
```
git clone -b v1_Stable https://github.com/CNChTu/Diffusion-SVC.git
G:\...\venvs\diffsvc-py311  (python 3.11, torch 2.6+cu124 — mirror cosyvoice venv pattern)
pip install -r requirements.txt
pretrain/  <- ContentVec encoder (checkpoint_best_legacy_500.pt, 190 MB, HF ChiTu mirror)
pretrain/  <- DiffSinger community vocoder nsf_hifigan (NOT nsf_hifigan_finetune), from openvpi.github.io/vocoders
```

### 2.2 Dataset (the critical constraint — build from what survives)
Diffusion-SVC needs **target-voice singing slices >=2 s, all same sample rate** (config,
default 44.1 kHz), speaker id folder `data/train/audio/1/` (id must be 1 for single speaker),
val: `data/val/audio/1/` (~10 clips).

Surviving sources to assemble into a Melusina singing corpus:
1. `melusina_cute_vcv_interim\wavs` (111 wavs — CV units, short; pair/chain them into >=2 s phrases)
2. `corpus_alpha_jd2\raw\wavs` (22 wavs, 1.25-1.8 s vowels — chain into phrases)
3. `ddsp-singing-vocoders\exp\melusina_phase2\runtime_gen` renders (504 wavs, up/down keys — the model's own output is valid training data for the diffusion stage)
4. `jp_vc_test` + CosyVoice anchor renders (speech — usable as supplementary target timbre, but singing slices are primary)
5. **New render**: TTS→singing-style source via edge-tts (EN/JP) through the CosyVoice anchor
   `inference_vc` (the exact chain already proven in `run_jp_vc_test.py`) to pad the corpus to
   >=20-30 min if needed.

Recommended corpus floor: **30-60 min** total singing slices (mix of CV chains, phrase singing,
and key-shifted copies). Use `fap` (fishaudio/audio-preprocess) for resampling to the config's
rate and splitting.

### 2.3 Preprocess + train (12 GB card profile)
```
# configs/config.yaml: sample rate, f0_extractor: crepe (noise-robust; our corpus is synthetic
# so parselmouth is fine — start parselmouth for speed, switch crepe if quality suffers)
# n_spk: 1
python preprocess.py -c configs/config.yaml
python train.py -c configs/config.yaml   # or finetune from model_0.pt base model
```
Recommended configuration per the README's own guidance:
- **Naive + shallow-diffusion combo** (config_naive.yaml + config_shallow.yaml, then
  `python combo.py`) — lowest training cost with better-than-full-diffusion quality; naive
  model may have range issues on small data → keep base-model finetune short (few steps) or
  use the infinite-range DDSP front-end.
- Training on 4070S 12 GB: small network 512x20 (or 512x30), batch 8-16, `k_step_max` shallow
  (100-200) + naive. Expected: **a few hours** for the diffusion stage, minutes for naive.
- fp32 (the SingingVocoders lineage warns bf16 hurts quality; keep Diffusion-SVC defaults).

### 2.4 Inference (the "she sings" moment)
```
python main.py -i <source_singing.wav> -model <melusina.pt> -o <out.wav> -k 0 -id 1 -speedup 10 -method pndm -kstep 100 -nmodel <naive.pt> -pe crepe
```
Source singing can come from **any** program: SynthV render, OpenUtau render, TuneLab render,
or our DiffSinger models' output (once the vocoder gate passes). `-k` = key shift, `-speedup` 10,
`-method` pndm/ddim/unipc/dpm-solver, `-kstep` shallow depth.

### 2.5 Export for editors (multi-program)
- **ONNX export** (`diffusion/onnx_export.py` → MoeVoiceStudio config) → usable in
  **MoeVoiceStudio (MoeVS)** which plugs into **UTAU** and **OpenUtau** as a
  resampler/conversion plugin.
- Diffusion-SVC checkpoints also convert into **DDSP-SVC / so-vits-svc / DiffSinger** weight
  formats via the SingingVocoders export chain (README: exported vocoder weights are accepted
  by all four).

---

## 3. Getting her working in "various programs" — the integration matrix

| Program | Route | What's needed | Status |
|---|---|---|---|
| **OpenUtau 0.1.565** | (a) DiffSinger ONNX bank (native, note→voice, full control) — needs vocoder gate + `dsdur/`+`dsvocoder/` packaging + phonemizer fix (track B of intake) | bank at `release_candidate\melusina_*`; fix = wire `openutau_vocoder_onnx_step300`, add `dsdur/`, switch character.yaml phonemizer to `OpenUtau.Core.DiffSinger.DiffSingerPhonemizer` | **Blocker: vocoder gate** |
| **OpenUtau** | (b) MoeVS plugin (DiffSVC conversion after render) | install MoeVS, point at exported ONNX | After §2.5 |
| **TuneLab** | ChoristaUtau runs UTAU banks via **moresampler** — the Adachi-Rei-style CV/VCV concatenative bank (JA) works here with zero neural deps | build the CV/VCV bank per §1; moresampler already installed in the extension | **Concatenative bank is the TuneLab path** |
| **TuneLab** | DiffSinger `.ds` probe exists (`tunelab_package\test\melusina_ja_minimal.ds`) — verifies whether TuneLab accepts OpenVPI ONNX layout | probe exists; acceptance unverified | Test gate |
| **SynthV Studio Pro** | **Source singer** for DiffSVC — compose in SynthV with an installed voice, render WAV, convert to Melusina via DiffSVC | SynthV installed; needs a licensed voicebank | Ready as source |
| **UTAU** | MoeVS plugin (DiffSVC) + the concatenative bank (moresampler/TIPS) | MoeVS install + bank | After §2.5 |
| **TouchDesigner / UE** | Post-render stems imported as in the spoken pipeline (`$ Voice` / `PlayMusicalNote`) | existing pipeline | At the end |

### Decision: which route is "she sings" first?
1. **Fastest (days): DiffSVC conversion.** Compose with SynthV/any voice → convert to
   Melusina. No vocoder gate, no phoneme labels, small dataset OK (30-60 min target; we have
   ~140 surviving wavs + 504 renders + can synthesize more via the proven edge-tts→anchor VC
   chain). Output lands in UE as normal audio.
2. **Highest control (weeks): DiffSinger native ONNX bank.** Note→voice in OpenUtau/TuneLab.
   Blocked on the vocoder gate; needs the DiffSinger repo + venv + corpus rebuilt.
3. **Concatenative UTAU bank (the Adachi-Rei path, days-weeks):** pure CV/VCV bank, zero
   neural deps, works in TuneLab (moresampler) and UTAU today. The identity oracle for
   everything else.

---

## 4. Execution order

### Phase 1 — DiffSVC up and singing (this session's goal)
1. Clone `CNChTu/Diffusion-SVC` v1_Stable; create `venvs\diffsvc-py311` (python 3.11, torch
   2.6+cu124 — copy the cosyvoice venv pattern); `pip install -r requirements.txt`.
2. Download pretrains: ContentVec `checkpoint_best_legacy_500.pt` (HF ChiTu mirror) +
   DiffSinger community `nsf_hifigan` vocoder (openvpi.github.io/vocoders).
3. Build the corpus: gather surviving wavs (111 CV + 22 vowels + 504 renders + jp_vc_test),
   chain short units into >=2 s slices, resample to config rate, split train/val.
4. `preprocess.py` → `train.py` (small net, naive+shallow combo). Verify on TensorBoard
   (first validation renders test audio automatically).
5. First conversion: render a short SynthV/OpenUtau phrase → `main.py` → **owner listens**
   (the evidence gate from the intake: RMS/ZCR/lo-hi metrics + listening).
6. `diffusion/onnx_export.py` → MoeVS package → test in OpenUtau (plugin) + UTAU.

### Phase 2 — Vocoder gate (unblocks native DiffSinger singing)
Per intake track B: wire `openutau_vocoder_onnx_step300` into a bank (`dsdur/`+`dsvocoder/`+
character.yaml fix) → owner-listens EN+JA probes. Then the real fix: rebuild data dir
(`VoiceSynthResearch/data/vocoder_clean_48000/`), canonical `ft_hifigan.yaml` config
(batch 10, warmup <=1000, max_updates 4000 ≈ 2000 real, augs off first to bisect the stall).

### Phase 3 — Concatenative CV/VCV bank (Adachi-Rei rules)
Build the 50+α JA CV bank + EN supplements from CosyVoice anchor-rendered units, applying the
four join rules and the waveform gate; package for TuneLab/UTAU (moresampler baseline, TIPS
compat matrix).

### Phase 4 — UE integration
Import stems via the existing spoken pipeline; wire `$ Voice` / `PlayMusicalNote`; store
render provenance (source program, DiffSVC model, seed, key shift) beside each asset.

---

## 5. Evidence gates (owner standard: WAV analysis + listening)
- After each DiffSVC training milestone: render one JA + one EN phrase + a key-shift delta;
  run the 8-metric gate (finite/length, DC offset, RMS >=0.05, ZCR 0.05-0.15, lo/hi 10-300,
  noise floor >=25 dB below fundamental, gt-reconstruction SNR >=15 dB) then owner listens.
- Record every render with: source program, model checkpoint, `-k`/`-kstep`/`-method`, seed.

---

## 6. Related
- `MELUSINA_BILINGUAL_VOICE_INTAKE_2026-08-11.md` — the intake this plan executes
- `Docs/Handoffs/MELODIA_VOICE_QUILLSCRIPT_HANDOFF_2026-08-01.md` — spoken voice → QuillScript
- `PROCEDURAL_VOICE_RND_PLAN.md` (G:) — the standing bilingual strategy (VTL/KlattGrid)
- `integration\tool_paths.json` (G:) — tool manifest (OpenUtau/vLabeler/VTL/OpenVPI pins)

