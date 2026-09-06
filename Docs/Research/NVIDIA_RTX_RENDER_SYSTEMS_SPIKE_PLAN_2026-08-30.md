# NVIDIA RTX / UE5.8 Render Systems — Tonight Spike Plan (2026-08-30)

**Scope:** Stock NVIDIA UE5.8 plugin stack only. No NvRTX engine fork tonight.
**Hard rule:** Presented FPS does not override rhythm latency concerns.
**Evidence map:** `LV_RND_CymaticEcology` (same scene as Track A — single scene, two tests)

---

## Track B — NVIDIA Stock UE5.8 Canary

### B0 — Machine Manifest

Record before any render testing. File: `Saved/Audit/RND/NVIDIA/<timestamp>/B0_machine_manifest.json`

```json
{
  "gpu_model": "",
  "gpu_architecture": "",
  "vram_gb": 0,
  "driver_version": "",
  "windows_build": "",
  "ue5_build": "",
  "ue5_exact_cl": "",
  "rhi": "DX12",
  "hardware_ray_tracing": false,
  "lumen_state": "SoftwareRayTracing|HardwareRayTracing|Disabled",
  "nanite_state": "Enabled|Disabled",
  "substrate_state": "Enabled|Disabled",
  "notes": ""
}
```

**How to collect:**
- GPU: `dxdiag` → Display tab, or `nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv`
- UE CL: `Help → About Unreal Editor` → bottom line
- Ray tracing / Lumen / Nanite / Substrate: `Project Settings → Rendering`

---

### B1 — DLSS 4.5 Install & Canary

**Package source:** NVIDIA Developer → Unreal Engine DLSS Plugin (UE5.8-compatible).
Current known package: DLSS 4.5 + Streamline 2.x + NGX SDK.

**Steps:**
1. Download DLSS plugin for UE5.8 from NVIDIA Developer portal (account required)
2. Copy to `Plugins/DLSS/` in project root (do NOT copy to engine plugins folder)
3. Enable in `.uproject` plugins array: `"DLSS": true, "DLSSBlueprint": true`
4. Build (closed editor): `Build.bat BS_GodFile Win64 Development`
5. Open `LV_RND_CymaticEcology` in editor
6. Verify `r.NGX.DLSS.Enable 1` in console → no crash, no error in log
7. Disable plugin (`"DLSS": false`), reopen — verify TSR fallback is clean (no black frame, no crash)

**Record in `B1_dlss_install.json`:**
```json
{
  "dlss_plugin_version": "",
  "streamline_version": "",
  "ngx_sdk_version": "",
  "build_result": "pass|fail",
  "fallback_clean": true,
  "notes": ""
}
```

---

### B2 — Cymatic Temporal Torture Test

**Scene:** `LV_RND_CymaticEcology` with A2 live coherence active (or A0 static field if A2 not ready).
**Sequence:** Fixed 8-beat rhythm loop, camera locked (no movement). Same sequence every run.

**Test matrix — run each mode, record results:**

| Mode | Console command | Notes |
|---|---|---|
| TSR Baseline | `r.AntiAliasingMethod 4` + `r.TemporalAA.Upscaling 0` | UE5.8 default |
| DLSS Quality | `r.NGX.DLSS.Enable 1` + `r.NGX.DLSS.Quality 1` | 67% input res |
| DLSS Balanced | `r.NGX.DLSS.Enable 1` + `r.NGX.DLSS.Quality 2` | 58% input res |
| DLAA | `r.NGX.DLSS.Enable 1` + `r.NGX.DLSS.Quality 0` | Full res AA only |

**Metrics to record per mode (from `stat gpu`, Unreal Insights, or `r.RHI.EnableFrameTimeCapture`):**

| Metric | How to capture |
|---|---|
| GPU frame time (ms) | `stat gpu` → Scene rendering total |
| Output resolution | `r.ScreenPercentage` effective + output |
| Internal resolution | Logged by DLSS plugin on startup |
| VRAM (MB) | `r.RDG.Debug.ResourceDump` or GPU-Z |
| Thin interference-line stability | Visual: 1=stable, 2=shimmering, 3=crawling |
| Water shimmer | Visual: 1=clean, 2=minor, 3=obvious |
| Niagara ghosting | Visual: 1=none, 2=minor trail, 3=obvious smear |
| Toon-edge stability | Visual: 1=stable, 2=minor flicker, 3=crawling |
| Iridescence stability | Visual: 1=stable, 2=shimmering, 3=broken |

**Output file:** `B2_temporal_comparison.json`
```json
{
  "sequence": "8-beat fixed loop",
  "modes": {
    "TSR": { "gpu_ms": 0, "vram_mb": 0, "stability_notes": {} },
    "DLSS_Quality": { "gpu_ms": 0, "vram_mb": 0, "stability_notes": {} },
    "DLSS_Balanced": { "gpu_ms": 0, "vram_mb": 0, "stability_notes": {} },
    "DLAA": { "gpu_ms": 0, "vram_mb": 0, "stability_notes": {} }
  }
}
```

---

### B3 — Ray Reconstruction (if DLSS RR supported on hardware)

**Precondition:** Hardware ray tracing available (B0 manifest). DLSS 4.5 installed (B1 pass).

**Scene:** Same `LV_RND_CymaticEcology` — use glossy/wet water surface + filigree/pearl shot.

**Steps:**
1. Enable HWRT: `r.RayTracing 1`, `r.Lumen.HardwareRayTracing 1`
2. Capture native denoising baseline: `stat screenshotat Saved/Audit/RND/NVIDIA/<ts>/B3_native_denoise.png`
3. Enable Ray Reconstruction: `r.NGX.DLSS.DenoiserMode 1`
4. Same shot: `B3_ray_reconstruction.png`
5. Slow camera pan (0.1 m/s) — record 10s clip or screenshot sequence
6. Note reflection/specular stability differences

**Output:** `B3_ray_reconstruction.json` + screenshots

---

### B4 — Multi Frame Generation (Separate Test)

**Critical:** Do not judge from editor viewport FPS. Use standalone/packaged build.

**Precondition:** GPU supports MFG (RTX 40-series or later Blackwell). DLSS 4.5 installed.

**Package command:**
```
RunUAT.bat BuildCookRun -project="[path]/BS_GodFile.uproject" -platform=Win64 -configuration=Development -cook -stage -package -targetplatform=Win64
```

**In packaged build:**
1. Enable: `r.NGX.DLSS.FrameGeneration 1`
2. Enable Reflex: `r.Reflex.Enabled 1`
3. Run fixed 8-beat rhythm sequence
4. Record via `stat fps` overlay

**Metrics:**
```json
{
  "rendered_fps": 0,
  "presented_fps": 0,
  "reflex_state": "Enabled|Disabled",
  "input_latency_feel": "normal|perceptible|obtrusive",
  "rhythm_readability": "clean|minor_artifacts|broken",
  "ui_artifacts": "",
  "niagara_artifacts": "",
  "notes": ""
}
```

**Hard rule reminder:** If presented FPS looks good but rhythm input feels off, that is a rhythm concern, not a rendering win. Record both separately.

---

## Track C — Next Session: NvRTX Isolated Branch Canaries

**Precondition:** Track A (cymatic ecology interaction working) + Track B (stock stack measured).

**These are NOT for tonight. Plan only.**

### C1 — NvRTX 5.8 Preview Build
- Separate engine source build (not the main project)
- Disposable project copy or git worktree
- No production asset resave
- Record: branch SHA, build time (hours), disk footprint (GB), shader compile cost
- Record: incompatible project plugins list
- Package canary before claiming it works

### C2 — RTX Mega Geometry
- Dense ornamental/Nanite scene (use existing Surreal/Baroque ornaments)
- Reflection + shadow geometry comparison vs stock Lumen
- BVH/ray stats if the branch exposes them (`r.RayTracing.Stats`)
- GPU time + VRAM delta vs stock
- Optional: SpeedTree dense foliage micro-canary **only** if the branch feature actually exists

### C3 — ReSTIR PT / SHaRC Portfolio Renderer
- Map: `LV_RND_RTX_SeaAbove_HeroShot`
- Baseline: stock Lumen + HWRT reference
- Path tracer reference (`r.PathTracing 1`) where applicable on stock
- NvRTX PT feature delta (ReSTIR GI, SHaRC cache, etc.)
- Keep SHIPPING vs PORTFOLIO_RENDERER decision separate

### C4 — Neural Texture Compression
- One 4K texture family (Copernicus/P2 or pearl material)
- Source (raw) vs BCn (DXT1/5/BC7) vs NTC footprint comparison
- Visual diff at 1:1 and 4× zoom
- SDK + build manifest
- Runtime UE integration: **WATCH status** unless a turnkey UE5.8 route is proven

---

## Evidence Layout

```
Saved/Audit/RND/NVIDIA/<timestamp>/
  B0_machine_manifest.json
  B1_dlss_install.json
  B2_temporal_comparison.json
  B2_TSR_baseline.png
  B2_DLSS_Quality.png
  B2_DLSS_Balanced.png
  B2_DLAA.png
  B3_native_denoise.png          (if B3 attempted)
  B3_ray_reconstruction.png      (if B3 attempted)
  B3_ray_reconstruction.json     (if B3 attempted)
  B4_mfg_results.json            (if B4 attempted)
  manifest.json
```

**manifest.json schema:**
```json
{
  "timestamp": "ISO8601",
  "gpu": "",
  "driver": "",
  "ue_build": "",
  "tracks_attempted": ["B0","B1","B2"],
  "tracks_passed": [],
  "next_decision": "",
  "notes": ""
}
```

---

## Tonight Stop Rule

Session is successful if we leave with:
1. One convincing `Perfect → coherent cymatic ecology` interaction (Track A)
2. One measured `TSR vs DLSS Quality/DLAA` comparison on that same interaction (B2)
3. A clear next decision (not an unfinished engine compile)

If those are done early → Ray Reconstruction (B3). NvRTX/Mega Geometry comes only after stock-engine result is in hand.
