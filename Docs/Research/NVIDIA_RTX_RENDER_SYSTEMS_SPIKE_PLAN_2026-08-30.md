# NVIDIA RTX Render Systems — UE5.8 Spike Plan

**Date:** 2026-08-30  
**Project:** Melodia Melusina / Unreal Engine 5.8  
**Status:** TONIGHT CANARY + FOLLOW-UP R&D  
**Default decision:** WATCH until measured on real Melodia scenes  
**Hard rule:** do not migrate the shipping project onto NvRTX tonight.

---

# 1. Goal

Evaluate NVIDIA's current 2026 rendering stack against **real Melodia problems** rather than generic photoreal demos.

Primary questions:

1. Can DLSS 4.5 materially improve Melodia's heavy UE5.8 scenes without compromising temporal stability of stylized materials, water, Niagara, thin filigree, foliage, or rhythm readability?
2. Does the NvRTX 5.8 Preview branch provide a compelling enough rendering advantage to justify maintaining a source-engine fork?
3. Does RTX Mega Geometry meaningfully improve ray-traced/path-traced Nanite fidelity in dense Melodia geometry/foliage?
4. Are RTX Neural Texture Compression / Neural Shaders mature enough for a contained R&D lane, or should they remain custom-SDK WATCH items?
5. Can NVIDIA's current path-tracing stack become a **portfolio/reference renderer** without becoming shipping runtime authority?

The evaluation separates:

```text
stock UE5.8 plugin integration
NvRTX engine-fork integration
standalone RTX Kit SDK experiments
shipping runtime dependency
portfolio/reference-render dependency
```

These are not the same adoption decision.

---

# 2. Current NVIDIA evidence snapshot — August 2026

## RTX Kit

NVIDIA currently describes RTX Kit as a suite for neural rendering, immense geometry, and real-time/path-traced rendering. Publicly listed technologies include:

- RTX Neural Shaders;
- RTX Neural Texture Compression (NTC);
- RTX Texture Filtering;
- RTX Texture Streaming;
- RTX Mega Geometry;
- RTX Dynamic Illumination / ReSTIR DI, GI, PT;
- RTX Global Illumination / SHaRC / NRC;
- RTX Path Tracing;
- RTX Character Rendering;
- supporting ray-tracing utilities.

Primary source:

- https://developer.nvidia.com/rtx-kit

NVIDIA's 2026.2 update adds/expands ReSTIR PT and updates SHaRC, RTX Path Tracing, Character Rendering, and Neural Shaders.

- https://developer.nvidia.com/blog/nvidia-rtx-innovations-are-powering-the-next-era-of-game-development/

## NvRTX for UE5.8

NVIDIA currently lists an **NvRTX Unreal Engine 5.8 Preview** branch.

- https://developer.nvidia.com/game-engines/unreal-engine/rtx-branch

This is important: the 5.8 branch is explicitly Preview. Treat it as a separate-engine R&D lane, not a project migration target.

## DLSS 4.5 for UE5.8

NVIDIA's official UE plugin supports UE5.8 and currently exposes:

- Super Resolution / DLAA;
- Ray Reconstruction;
- Multi Frame Generation;
- Dynamic Multi Frame Generation;
- Reflex Low Latency;
- NVIDIA Image Scaling.

NVIDIA's current public package is DLSS 4.5, updated July 2026.

- https://developer.nvidia.com/rtx/dlss

## RTX Mega Geometry

NVIDIA describes RTX Mega Geometry as accelerating BVH construction for cluster-based geometry systems and enabling dramatically more ray-traced triangles. In UE context, its value proposition is especially relevant to **Nanite ray-tracing fidelity**, where conventional ray tracing may use lower-detail fallback representations.

- https://developer.nvidia.com/rtx-kit
- https://www.nvidia.com/en-us/geforce/news/gamescom-2026-dlss-4-5-ray-reconstruction-release-announcements-trailers/

NVIDIA's standalone getting-started requirements document Turing-or-newer hardware, driver 570+, CMake 3.28+, and a modern Windows SDK for the sample SDK, but actual UE/NvRTX feature support must be verified on the test machine/driver.

- https://developer.nvidia.com/blog/?p=95850

## Neural shading

RTX Neural Shaders and NTC are now real SDKs, with DirectX cooperative-vector support introduced through modern Agility SDK / Shader Model paths. However, this remains a custom graphics integration class of work, not equivalent to installing a standard UE material plugin.

- https://developer.nvidia.com/blog/nvidia-releases-rtx-neural-rendering-tech-for-unreal-engine-developers/
- https://developer.nvidia.com/blog/how-to-get-started-with-neural-shading-for-your-game-or-application/

**Project interpretation:** Neural Shaders/NTC remain research spikes unless a turnkey NvRTX/UE integration is verified on the exact 5.8 branch used.

---

# 3. Melodia-specific NVIDIA test hierarchy

Do the low-risk stock-engine tests first.

```text
Tier N0  Hardware + driver + plugin canary
Tier N1  DLSS 4.5 / DLAA / Reflex on stock UE5.8
Tier N2  Ray Reconstruction on one ray-traced Melodia shot
Tier N3  NvRTX 5.8 Preview isolated-engine canary
Tier N4  RTX Mega Geometry Nanite fidelity comparison
Tier N5  ReSTIR PT / SHaRC portfolio-reference renderer test
Tier N6  RTX Neural Texture Compression standalone/source-texture experiment
Tier N7  Neural Shaders / cooperative vectors WATCH
```

Do not invert this order.

---

# 4. Hardware capability canary

Before installing anything, record:

```text
GPU model
GPU architecture
VRAM
NVIDIA driver version
Windows build
DX12 Agility support state
UE5.8 exact build
monitor refresh rate
G-SYNC state
current render API
current project RHI
hardware ray tracing on/off
Lumen mode
Nanite mode
Substrate mode
```

Create:

```text
Saved/Audit/RND/NVIDIA/<timestamp>/hardware_manifest.json
```

Suggested schema:

```json
{
  "schema": "melodia.rnd.nvidia-capability.v1",
  "gpu": "",
  "vram_gb": 0,
  "driver": "",
  "windows_build": "",
  "ue": "5.8.x",
  "rhi": "DX12",
  "ray_tracing": false,
  "lumen_hwrt": false,
  "nanite": true,
  "substrate": true,
  "notes": ""
}
```

If the machine/driver cannot support a lane, mark it `BLOCKED_BY_HARDWARE` rather than forcing workarounds into the production project.

---

# 5. N1 — DLSS 4.5 stock UE5.8 benchmark

This is the best NVIDIA test for tonight because it does **not** require an engine fork.

## Test map

Prefer one existing or duplicated heavy scene with:

- water;
- thin geometry/filigree;
- Niagara particles;
- Nanite environment assets;
- alpha-tested or dense foliage if available;
- stylized/Substrate materials;
- a fixed gameplay camera and fixed cinematic camera.

If `LV_RND_CymaticEcology` is ready, use it as one comparator because moving interference lines and particles are a good temporal-stability torture test.

## Modes

Capture, at minimum:

```text
TSR native project baseline
DLSS Quality
DLSS Balanced
DLAA
```

Where available and valid:

```text
DLSS Ray Reconstruction
Reflex On
Reflex On + Boost / current plugin equivalent
```

Multi Frame Generation is a **separate test**, not part of image-quality comparison.

## Metrics

For every fixed camera:

```text
internal render resolution
output resolution
GPU frame time
CPU game/render thread time
presented FPS
1% low if captured externally
VRAM
visible ghosting
thin-line stability
foliage shimmer
water shimmer
Niagara trail stability
toon-edge stability
material iridescence stability
rhythm-HUD legibility if present
```

## Pass gate

DLSS becomes `ADOPT-CANDIDATE` if:

- Quality mode provides a material GPU-time win at equivalent output resolution;
- no severe stylized-edge or water/Niagara temporal artifacts appear;
- fixed-camera screenshots and motion captures remain compositionally faithful;
- package/standalone build works;
- disabling the plugin cleanly restores baseline behavior.

---

# 6. N1b — Multi Frame Generation / Dynamic MFG

Do not judge MFG from editor viewport FPS.

Test in standalone/package where supported.

Record:

```text
base rendered FPS
presented FPS
latency with Reflex state
input feel during camera pan
rhythm input perception
frame pacing
UI/HUD artifacts
Niagara temporal artifacts
```

**Important Melodia-specific rule:** rhythm gameplay cannot be evaluated by presented FPS alone. The underlying simulation/input timing remains authoritative. MFG is rejected for any mode where perceived latency/visual interpolation makes rhythm judgement feel misleading even if FPS rises dramatically.

For a portfolio/cinematic mode, MFG may still be useful independently of gameplay approval.

---

# 7. N2 — Ray Reconstruction benchmark

Use one scene with difficult ray-traced signals:

- glossy water reflection;
- wet pearl/coral material;
- metallic filigree;
- translucent-looking or layered stylized surfaces where valid;
- moving Niagara particles nearby.

Compare:

```text
native denoising path
vs
DLSS Ray Reconstruction
```

Fixed camera + slow camera pan.

Measure:

```text
reflection stability
specular detail retention
water edge stability
ghosting/disocclusion
thin geometry reconstruction
GPU cost
```

A win here could matter more to Melodia than raw frame generation because the art direction relies heavily on water, shimmer, filigree, and high-frequency material response.

---

# 8. N3 — NvRTX 5.8 Preview isolated canary

**Do not repoint the main project.**

Required isolation:

```text
separate NvRTX source build directory
separate test project copy or disposable worktree
separate DerivedDataCache if needed
no automatic project conversion
no production asset resave
```

Record:

```text
NvRTX branch SHA/tag
base Epic UE SHA/version
Visual Studio toolchain
build time
engine disk footprint
first shader compile time
project open result
plugin compatibility failures
package result
```

### Canary content

Only copy/point to one R&D map and minimum assets necessary.

**Stop immediately** if core project plugins require invasive engine-side patches just to open the test.

### Maintenance cost gate

NvRTX cannot be promoted merely because an image looks better.

Score:

```text
visual gain
performance gain
engine merge burden
plugin compatibility
build time
shader compile burden
packaging
upgrade burden
source-control burden
```

For a solo/very small project, the fork burden gets a heavy penalty.

---

# 9. N4 — RTX Mega Geometry benchmark

This is the most interesting NvRTX-specific environment test.

## Melodia test A — dense ornamental Nanite

Use:

- procedural coral;
- baroque ornament;
- high-detail terrain/architecture;
- dense Nanite static geometry.

Fixed camera includes:

- ray-traced shadow detail;
- glossy/reflection read;
- silhouettes of small geometry.

Compare conventional ray-tracing representation vs Mega Geometry enabled according to the exact NvRTX 5.8 branch documentation/build.

## Melodia test B — foliage canary

Only if the exact 5.8 Preview branch exposes a relevant foliage path.

Use one SpeedTree-derived or dense foliage micro-scene.

Do not assume NVIDIA's in-development 2026 foliage system is production-ready or publicly exposed in the same form used in partner titles.

## Metrics

```text
ray-traced triangle/BVH stats if exposed
GPU frame time
BVH build/update time
VRAM
reflection/shadow geometric fidelity
camera-motion stability
foliage animation compatibility
Nanite/World Partition compatibility
```

### Promotion gate

Mega Geometry is useful only if it produces a **visible Melodia-specific gain** in water reflections, fine shadowing, dense ornament, or foliage while maintaining sane GPU/build cost.

---

# 10. N5 — RTX Dynamic Illumination / ReSTIR PT / SHaRC

This lane is aimed primarily at **reference/portfolio rendering** unless performance proves unexpectedly good.

## Hero shot

Build one controlled scene:

`LV_RND_RTX_SeaAbove_HeroShot`

Include:

- water / mirror-like surface;
- multiple small emissive/magical lights;
- layered high-frequency materials;
- one hero character or ornamental silhouette;
- slow 5-second camera move.

Compare:

```text
stock UE5.8 Lumen/HWRT baseline
stock Path Tracer reference where applicable
NvRTX path tracing / current branch features
ReSTIR PT or SHaRC path if exposed by branch
```

## Why

NVIDIA's 2026.2 RTX Kit specifically positions ReSTIR PT as improving path reuse at arbitrary bounces and difficult glossy/mirror surfaces. This maps directly to Sea Above / water-heavy Melodia lookdev.

## Decision split

Possible outcomes:

```text
SHIPPING: REJECT/PARK
PORTFOLIO_REFERENCE_RENDERER: ADOPT
```

That is a valid result.

---

# 11. N6 — RTX Neural Texture Compression

Do not attempt to wire NTC into the shipping UE renderer tonight.

Start as a standalone asset-memory experiment.

## Test set

Pick one representative 4K material family:

- pearl/coral;
- brocade/fabric;
- terrain;
- ornamental stone;
- one Copernicus-generated P2 material family.

Include:

```text
BaseColor
Normal
ORM or equivalent packed maps
Height if used
special masks
```

Compare:

```text
uncompressed source footprint
BCn project baseline
RTX NTC representation
visual reconstruction error
encode time
decode/sample feasibility
```

## Record

```text
SDK version/commit
GPU/driver
input dimensions
input channel count
bits-per-pixel / target quality
source MB
BCn MB
NTC MB
visual notes
runtime integration status
```

### Decision

NTC remains `WATCH` until a stable UE5.8 runtime integration route exists that does not require maintaining a bespoke material renderer.

However, source-data/memory experiments are still valuable because Melodia's material density is unusually high.

---

# 12. N7 — RTX Neural Shaders / Cooperative Vectors

This is **not tonight's production integration**.

Research canary only:

- verify SDK builds;
- run vendor sample;
- verify DirectX cooperative-vector support on current driver/Agility SDK;
- document hardware support;
- identify whether an Unreal 5.8/NvRTX path exists for a custom material prototype;
- do not rewrite Substrate/master materials around it.

Potential long-term Melodia use cases:

```text
neural approximation of expensive layered iridescent material
neural texture/material decoding
compact learned caustic response
learned cloth/silk/pearl BSDF approximation
neural radiance-field-like local presentation
```

Promotion requires a project-owned, maintainable integration path.

---

# 13. Tonight combined experiment — RTX × Cymatic Ecology

If DLSS 4.5 installation succeeds quickly, the most informative small combined test is:

```text
LV_RND_CymaticEcology
```

Why this is useful:

- thin standing-wave lines stress temporal reconstruction;
- moving particles stress ghosting;
- water/iridescence stress specular reconstruction;
- rhythmic pulses create deterministic repeated motion;
- fixed cadence makes A/B capture easier.

Run:

```text
TSR
DLSS Quality
DLAA
Ray Reconstruction if valid
```

Capture the exact same 8-beat sequence.

This gives us both a cool prototype and a renderer torture test in one night.

---

# 14. Evidence layout

```text
Saved/Audit/RND/NVIDIA/<timestamp>/
  hardware_manifest.json
  dlss/
    baseline_tsr.json
    dlss_quality.json
    dlaa.json
    motion_capture_notes.md
  ray_reconstruction/
  nvrtx/
  mega_geometry/
  ntc/
```

Commit only lightweight manifests, screenshots/contact sheets, and Markdown results.

Do not commit:

- NVIDIA SDK binaries;
- engine source/build products;
- plugin redistribution files unless license/repo policy explicitly permits;
- shader caches;
- DerivedDataCache;
- giant captures.

---

# 15. Renderer scorecard

Score each lane independently.

| Category | Weight |
|---|---:|
| Visible Melodia quality gain | 25 |
| GPU/performance gain | 20 |
| Temporal stability | 15 |
| Integration simplicity | 10 |
| Maintainability / upgrade burden | 10 |
| Hardware reach | 5 |
| Packaging/reproducibility | 5 |
| Source-control friendliness | 5 |
| Replaceability / graceful fallback | 5 |

Guidance:

```text
>= 80 : ADOPT candidate
65–79 : PARK / selective mode
< 65  : REJECT for shipping
immature/inaccessible : WATCH
```

A portfolio/reference-render lane may be adopted even if shipping score is lower, but the two decisions must be recorded separately.

---

# 16. Recommended tonight order

```text
1. Cymatic static field canary
2. DLSS 4.5 plugin/hardware canary
3. Cymatic rhythm event bridge
4. DLSS Quality/DLAA A/B on cymatic scene
5. Cymatic Niagara dust
6. Ray Reconstruction canary if ray-traced scene is ready
7. Stop
```

Do **not** start building NvRTX 5.8 Preview until the native/stock-engine work above has produced evidence. An engine fork compile can consume the entire night without producing a game-visible improvement.

NvRTX / Mega Geometry becomes the next isolated machine task after the stock plugin canary.

---

# 17. Success condition

By the end of the first session we want two concrete answers:

1. **Cymatic Ecology:** does rhythm-driven environmental coherence look uniquely Melodia and deserve prototype status?
2. **NVIDIA stock UE lane:** does DLSS 4.5 improve the real scene enough to become a supported renderer path?

Everything else stays staged behind those answers.
