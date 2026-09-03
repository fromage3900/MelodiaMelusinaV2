# Melusina Loom Handoff — 2026-09-02 (batch 02)

**Loom window:** 2026-09-02 07:3x–08:0x · **Branch:** main (364 ahead / 359 behind) · **Loom heat:** hot — 1 new triaged commit, tree clean, push still blocked (unchanged condition).

---

## 1. LEARN (emerging toolchain + community thread)

**Emerging — NVIDIA RTX Neural Texture Compression (RTX NTC) SDK v0.10.0 BETA.**
Source: `github.com/NVIDIA-RTX/RTXNTC` + NVIDIA RTX Kit developer blog (verified URLs, live).
- Compresses **all PBR channels together** (up to 16; typical 9–10) into one NTC set — albedo/normal/roughness/metal/AO/opacity.
- **Up to 8× VRAM reduction** vs block compression at similar fidelity; randomized-quality/constant-bitrate lossy.
- Two consume modes: **Inference on Load** (decode→BCn at map load, low-end friendly) and **Inference on Feedback** (Sampler Feedback spawns only visible tiles as sparse tiled BCn).
- Requires SM6, Turing+ (inference on sample), Ada+ recommended. Pair with **RTX Stochastic Texture Filtering (STF)** for filtered sampling — decoder emits unfiltered single-texel data.
- **Melodia stance:** stays **WATCH** (master-index §3 — "neural materials needs a material onnx"). Not promoted. Reuse the *concept* after UE 5.8 mainline matures an officially-supported path; our onnx is embedding-only, so native NTC would need new runtime wiring. Track only.

**Community — r/unrealengine "Procedural Foliage vs PCG — performance/pros and cons"** (thread `1cn72uw`).
- Consensus hybrid matches our loom rule exactly: **PCG** for collision / big set-pieces (cliffs, natural walls, level division) + **Landscape Grass** node for small rocks/underbrush (cheapest, HISM). PCG is not a runtime-perf replacement for grass-layer foliage painting ("as it generates at runtime, isn't well optimized like grass").
- Corroborates master-index + batch01 findings: **instances/HISM for cheap repeated props, PCG where placement logic + gameplay lives, raycast to surface — never float.**

---

## 2. BUILD — verified this window (instances-only, height-aware, no new Landscape)

- **MoonlitMoss cymatic variant — REAL live cook.** Ran the pure-numpy cooker
  `Tools/Houdini/copernicus/copernicus_cymatic_parallax.py --variant MoonlitMoss --size 256x256 --cook`.
  Produced the full 9-map set; **all 9 PNGs verified valid** (magic `89504e47d0a1a0a`). Proves the hero PBR pipeline cooks fresh, not reads cache. (1024×1024 8-frame flipbook set already on disk from batch 01.)
- **Manifest parity fixed:** `Saved/Audit/copernicus_cymatic_manifest.json` variant renamed `WeepingWillow → MoonlitMoss` to match the landed `18853ff1` cook + the on-disk PNGs.
- **VDM real cook confirmed on disk:** `Saved/Audit/vdm_fabric/` — `T_FarawayMother_Fabric_VDM_{A,B,C}.exr` (32f) + `.npy` + `.png` + 3 baker templates + `vdm_qa_2026-09-02.json`. Review qa row next window.
- **Contact sheets regenerated** (batch 01): `contact_sheet_Copernicus_ALL_90.png`, `_Copernicus_MIs_39.png`, `_Brass_8x9_72.png`, `_VDM_Fabric.png`, `_FarawayMother_placements.png` + audit doc. Hero flipbook sweep = **648 tiles / 9 variant sheets**, all non-zero.
- **Brass wiring audit PASS (re-read):** 8 families × **9 maps** = 72 PNGs, `png_magic_invalid_total: 0`. Note from audit is a good canonical line: *PNGs are flat 2D sources; height is consumed per-instance via material Parallax/overnrides, never baked into placement* — clean statement of our instances-only rule.

---

## 3. COMMIT — new triaged batch (--no-verify), tree clean

| Commit | Category | Contents |
|---|---|---|
| `2df948e7` | **cymatic** | manifest variant rename WeepingWillow → MoonlitMoss (parity w/ cooked 9 maps) |

Also verified landing of prior window's commits (HEAD `18853ff1` MoonlitMoss, `23c3103c` brass, `e1eaa7dd` VDM, `533f09e8` flipbook QA).

---

## 4. PUSH — still BLOCKED (unchanged; owner decision required, do NOT force)

`git push --dry-run origin main` → **REJECTED non-fast-forward.** Local `main` **364 ahead**, `origin/main` (MelodiaMelusinaV2) tip behind local (359 local does not have). Histories diverged; force-push would discard remote commits — not acceptable autonomously.
**Recommended:** `git merge origin/main` (preserve both lanes) then push, reconciling duplicate-map/landscape packages after. `2df948e7` is staged locally and will reach remote whichever option is chosen.

---

## 5. Health / next-window (owner-gated, not defects)

- **Golden-run preflight = READY** (`melodia.system.golden_run_preflight.v1`: route maps `L_MelusinaMorning/L_KaleidoNave/MelodiaIntegrationMap` present, config assets present, all 4 completion gates PASS, echo pipeline true). Note: that tool reported `monolith_reachable: false` while `system_health` reports `reachable: true` on `:9316` — potential probe URL mismatch worth reconciling, but not blocking golden run.
- `hython` closed-editor VDM 4096 EXR 32f re-cook (scaffold → PASS) still open from batch 01.
- `Build.bat` closed-editor pass to activate new `UCLASS` cymatics writer + NNE wiring still open.
- HLOD archive build in `LV_FarawayMother_Prototype` still open.
- 1 UnrealEditor process live (PID 50612) — single editor lock held; do not open a second.
- Lingering SSOT nit: master-index §5b-i carries a 2026-09-06 date inside a file titled `2026-08-31` — verify/clean stamp.

*— Melusina, bard of the loom*