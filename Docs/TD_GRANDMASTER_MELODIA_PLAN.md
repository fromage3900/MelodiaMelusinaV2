# Grandmaster Melodia TouchDesigner Project — Architecture & Build Plan

**Version:** 1.0.0
**Date:** 2026-07-15
**Branch:** `feature/touchdesigner-mcp-integration`
**Status:** Ready for execution
**TD Project:** `_TouchDesigner/grandmaster_melodia.toe`

---

## 1. What Is the TD Grandmaster?

In the Melodia architecture, every surface has a single source of truth:

| Grandmaster | Surface | Authority |
|-------------|---------|-----------|
| **Figma** (`Yx8ud7n39NdWZvnNvo4Xlf`) | Visual design, tokens, typography, component atoms | Design SSOT |
| **GMM** (Unreal `gmm/` package) | PCG, materials, gameplay, runtime, portfolio capture | Engine SSOT |
| **Melodia Studio** (Blender `surreal_arch/`) | Geometry authoring, kitbash, ornament, world export | Authoring SSOT |
| **TD Grandmaster** ← NEW | Real-time FX, audio reactivity, MCP orchestration, portfolio viewer, live shader prototyping | **Real-time SSOT** |

The TD Grandmaster is the **live, interactive hub** that all other grandmasters pass through. It is not a replacement for any existing grandmaster — it is the real-time layer that makes the portfolio **performative rather than static**.

---

## 2. Architecture

### 2.1 System Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                    TD GRANDMASTER MELODIA (.toe)                      │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  ┌───────────┐ │
│  │ AUDIO ENGINE │  │  POST-FX     │  │  PARTICLES  │  │  SHADERS  │ │
│  │ Melusina WAV │  │ Nikki Bloom  │  │ Sparkles    │  │ GLSL TOPs │ │
│  │ Pitch→CHOP   │  │ Color Grade  │  │ Motes       │  │ Toon Lib  │ │
│  │ Amp→CHOP     │  │ DOF Bokeh    │  │ Wish Burst  │  │ Fabric    │ │
│  │ Beat→CHOP    │  │ LUT Chain    │  │ Petals      │  │ Crystal   │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬──────┘  └─────┬─────┘ │
│         │                 │                 │               │       │
│  ┌──────┴─────────────────┴─────────────────┴───────────────┴─────┐ │
│  │                      OSC ROUTING HUB                            │ │
│  │          ┌──────────┐  ┌──────────┐  ┌──────────┐              │ │
│  │          │ → Blender│  │  → Unreal│  │ → Niagara│              │ │
│  │          │  :9000   │  │  :8000   │  │  :8000   │              │ │
│  │          └──────────┘  └──────────┘  └──────────┘              │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────────┐│
│  │                   MCP ORCHESTRATION (Envoy)                      ││
│  │   .mcp.json registers: envoy:9870 + monolith:9316 + blender:9877 ││
│  │   Single AI session controls all 3 tools through TD as hub       ││
│  └──────────────────────────────────────────────────────────────────┘│
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────────┐│
│  │                  PORTFOLIO VIEWER (Panel COMPs)                  ││
│  │   Project selector → FBX loader → Preset switcher → Capture      ││
│  └──────────────────────────────────────────────────────────────────┘│
└────────────────────────────┬─────────────────────────────────────────┘
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
    ┌──────────┐     ┌──────────────┐     ┌──────────┐
    │ BLENDER  │     │ UNREAL 5.8   │     │  FIGMA   │
    │ Geometry │     │ PCG + Render │     │ Wix Web  │
    └──────────┘     └──────────────┘     └──────────┘
```

### 2.2 Container Hierarchy

```
/project1                              ← Root
├── /embody                            ← Embody COMP (Envoy MCP)
│
├── /audio                             ← AUDIO ENGINE
│   ├── /melusina_in                   ← Audio File In CHOP (VoiceSynth WAV)
│   ├── /pitch_analyzer                ← Pitch CHOP
│   ├── /amp_analyzer                  ← Amplitude CHOP → Envelope Follower
│   ├── /spectral_analyzer             ← Spectrum CHOP
│   ├── /beat_detector                 ← Beat CHOP
│   └── /waveform_scope                ← Waveform visualization
│
├── /postfx                            ← POST-FX CHAIN
│   ├── /bloom_chain                   ← Multi-pass Bloom (Nikki preset)
│   │   ├── /threshold                 ← Luma Key TOP
│   │   ├── /blur_5px                  ← Blur TOP (Gaussian, 5px)
│   │   ├── /blur_15px                 ← Blur TOP (Gaussian, 15px)
│   │   ├── /blur_30px                 ← Blur TOP (Gaussian, 30px)
│   │   └── /composite                 ← Composite TOP (additive)
│   ├── /color_grade                   ← LUT TOP
│   │   ├── /nikki_lut                 ← Nikki warm-golden grade
│   │   ├── /madoka_lut                ← Madoka surreal/collage grade
│   │   ├── /celestial_lut             ← Celestial cool/deep astral grade
│   │   ├── /itto_lut                  ← Itto warm stone grade
│   │   └── /sakura_lut                ← Sakura cherry blossom grade
│   ├── /dof_bokeh                     ← Bokeh Blur TOP (depth-driven)
│   └── /vignette                      ← Ramp + Over TOP
│
├── /particles                         ← PARTICLE SYSTEMS (POPs)
│   ├── /sparkles                      ← POP: Nikki 4-point star sparkles
│   ├── /motes                         ← POP: Ambient floating dots
│   ├── /wish_burst                    ← POP: Explosive wish energy
│   ├── /petals                        ← POP: Sakura petal fall
│   ├── /fabric_trail                  ← POP: Ribbon streamers
│   └── /magical_glow                  ← POP: Soft radial glow orbs
│
├── /shaders                           ← SHADER PROTOTYPE LAB
│   ├── /glsl_nikki_toon               ← GLSL TOP: Nikki soft toon
│   ├── /glsl_satin_fabric             ← GLSL TOP: Anisotropic satin
│   ├── /glsl_crystal                  ← GLSL TOP: Crystal/refraction
│   ├── /glsl_water                    ← GLSL TOP: Stylized water
│   ├── /glsl_aurora                   ← GLSL TOP: Aurora/sky gradient
│   └── /glsl_sparkle_sprite           ← GLSL TOP: 4-point star generator
│
├── /geo                               ← GEOMETRY LOADER
│   ├── /fbx_import                    ← FBX COMP (loads from _TouchDesigner/exports/)
│   ├── /usd_import                    ← USD COMP (UE exports)
│   ├── /camera_rig                    ← Camera COMP (cinematic orbit)
│   └── /light_rig                     ← Light COMP (warm key + fill)
│
├── /osc                               ← OSC ROUTING HUB
│   ├── /osc_in_blender                ← OSC In CHOP (:9000, Blender camera)
│   ├── /osc_out_ue_material           ← OSC Out CHOP (:8000, UE material params)
│   ├── /osc_out_ue_niagara            ← OSC Out CHOP (:8000, UE Niagara params)
│   └── /osc_out_ue_camera             ← OSC Out CHOP (:8000, UE camera)
│
├── /spout                             ← SPOUT STREAMING
│   ├── /spout_out_preview             ← Spout Out TOP ("TD_MelodiaPreview")
│   └── /spout_in_ue                   ← Spout In TOP ("UE_RenderTarget")
│
├── /ui                                ← CONTROL PANEL + PORTFOLIO VIEWER
│   ├── /preset_switcher               ← Slider COMPs for 5 style presets
│   ├── /time_slider                   ← Day/Night cycle (0-1 float → OSC)
│   ├── /audio_gain                    ← Audio reactivity gain slider
│   ├── /particle_density              ← Global particle density multiplier
│   ├── /project_selector              ← Dropdown of portfolio projects
│   ├── /stats_overlay                 ← Text TOP showing tris/counts/FPS
│   ├── /material_sheet                ← Table COMP showing material breakdown
│   └── /capture_button                ← Button COMP → snapshot export
│
├── /render                            ← FINAL RENDER OUTPUT
│   ├── /render_main                   ← Render TOP (combines all layers)
│   ├── /render_hero                   ← Render TOP (4K hero shot)
│   └── /render_preview                ← Render TOP (1080p live preview)
│
└── /export                            ← EXPORT PIPELINE
    ├── /tdn_export                    ← TDN network externalization (Embody)
    ├── /screenshot_export             ← Movie File Out TOP (PNG sequence)
    └── /osc_manifest_export           ← DAT → file (current OSC routing)
```

---

## 3. Style Preset System

The TD Grandmaster owns the **5 Nikki/Melodia style presets** as the runtime authority:

### 3.1 Preset Parameter Matrix

| Parameter | Nikki | Madoka | Celestial | Itto | Sakura |
|-----------|-------|--------|-----------|------|--------|
| **Bloom Intensity** | 5.0 | 3.0 | 4.0 | 2.5 | 4.5 |
| **Bloom Threshold** | 0.75 | 0.85 | 0.80 | 0.90 | 0.78 |
| **Bloom Tint** | #FFF5F0 | #E6B3FF | #B3CCFF | #FFD9B3 | #FFE6F0 |
| **Shadow Lift** | 0.08 | 0.05 | 0.06 | 0.04 | 0.07 |
| **Shadow Tint** | #352D40 | #261A40 | #141A30 | #1A1010 | #2E1A33 |
| **Saturation** | 0.90 | 1.20 | 0.85 | 0.75 | 0.95 |
| **Contrast** | 0.88 | 1.05 | 0.95 | 1.10 | 0.90 |
| **Diffuse Wrap** | 0.50 | 0.30 | 0.40 | 0.60 | 0.55 |
| **Sparkle Color 1** | #FFD9A0 | #E0B0FF | #A0D0FF | #FFC080 | #FFC0D8 |
| **Sparkle Color 2** | #F0C0D0 | #C080FF | #80A0FF | #E0A060 | #F080A0 |
| **Particle Density** | 1.0 | 1.3 | 0.8 | 0.6 | 1.1 |

### 3.2 Preset Switching Protocol

```
[UI Slider: preset_id 0-4]
       │
       ▼
[Switch CHOP] → maps preset_id to 12-float toon_params array
       │
       ├──► [TD Post-FX]: Update bloom, LUT, DOF parameters
       ├──► [TD Particles]: Update sparkle colors, density
       └──► [OSC Out]: Push toon_params + preset ID → UE port 8000
```

---

## 4. Audio Engine (Melusina → Visuals)

### 4.1 Analysis Chain

```
[Audio File In CHOP]
  file: VoiceSynthResearch/*.wav or live mic input
       │
       ├──► [Pitch CHOP]        → /melusina/pitch     → UE shader warp amount
       ├──► [Envelope Follower]  → /melusina/amp       → UE particle spawn rate
       ├──► [Spectrum CHOP]      → /melusina/formants  → TD particle color palette
       ├──► [Beat CHOP]          → /melusina/beat      → TD wish burst trigger
       └──► [RMS CHOP]           → /melusina/rms       → TD bloom intensity modulation
```

### 4.2 Audio→Visual Mappings

| Audio Feature | Visual Effect | Target |
|---------------|---------------|--------|
| Pitch (Hz) | Shader distortion/warp amount | UE Substrate Toon "Impressionist" warp |
| Amplitude (0-1) | Particle spawn rate multiplier | UE Niagara + TD POPs |
| Spectral centroid | Particle color temperature (warm↔cool) | TD sparkle LUT index |
| Beat detection | Wish burst trigger | TD burst POP → UE Niagara burst |
| RMS | Bloom intensity modulation | TD bloom composite weight |

---

## 5. Portfolio Viewer (Interactive)

### 5.1 Project Loading

```
[project_selector Dropdown]
  reads: _TouchDesigner/exports/project_index.json
  options: ["Nikki Florawish", "Zen Shrine", "Baroque Cathedral", ...]
       │
       ▼
[FBX COMP] loads: _TouchDesigner/exports/{project}.fbx
       │
       ▼
[Geometry COMP] positions, lights, cameras
       │
       ▼
[Render TOP] renders with active post-FX + particles
```

### 5.2 Interactive Controls

| Control | Type | Range | OSC Route |
|---------|------|-------|-----------|
| Day/Night Cycle | Slider | 0–1 | `/time/cycle` → UE |
| Style Preset | Radio | 0–4 (Nikki/Madoka/Celestial/Itto/Sakura) | `/material/preset` → UE |
| Particle Density | Slider | 0.1–2.0 | `/niagara/*/rate` → UE |
| Camera Orbit Speed | Slider | 0–5 | Camera COMP rotation speed |
| Audio Reactivity | Slider | 0–2.0 | Gain on audio→visual CHOPs |
| Screenshot | Button | — | Export PNG to `exports/` |

### 5.3 Stats Overlay

```
[Text TOP] renders live overlay:
  Project:       Nikki Florawish Sanctuary
  Triangles:     1,579
  Meshes:        23
  Materials:     7
  Preset:        Nikki (warm golden hour)
  FPS:           60
  Audio:         Melusina - Aria of Wishes.wav (playing)
  OSC:           UE:8000 OK | Blender:9000 OK
```

---

## 6. MCP Orchestration Hub

### 6.1 Unified Command Flow

A single AI agent session (via Cursor/Claude Code) sends one prompt:

```
"Switch to Madoka preset, load Zen Shrine FBX, amp up particles 2x,
 trigger wish burst on next beat, screenshot hero render, push OSC to UE"

         ┌─────────────────────────────────────────┐
         │        TD GRANDMASTER (Envoy MCP)       │
         │                                         │
         │  1. set_parameter(preset=1)             │
         │  2. set_parameter(fbx_path=zen_shrine)  │
         │  3. set_parameter(particle_density=2.0) │
         │  4. execute_python(wish_burst_on_beat)  │
         │  5. capture_top(render_hero, 4K)        │
         │  6. send_osc(/material/preset, 1)       │
         │                                         │
         └──────────────┬──────────────────────────┘
                        │
         ┌──────────────┼──────────────┐
         ▼              ▼              ▼
    Blender MCP    Monolith MCP    external OSC
    (if needed)    (if needed)     (always)
```

### 6.2 TDN Version Control

All networks externalized as `.tdn` (diffable YAML):

| Network | TDN File | Version Controlled |
|---------|----------|--------------------|
| `/postfx` | `networks/postfx_chain.tdn` | Yes — git diff shows LUT changes |
| `/audio` | `networks/audio_engine.tdn` | Yes |
| `/particles` | `networks/particle_systems.tdn` | Yes |
| `/osc` | `networks/osc_routing.tdn` | Yes |
| `/shaders` | `networks/shader_lab.tdn` | Yes |
| `/ui` | `networks/control_panel.tdn` | Yes |
| `/geo` | `networks/geometry_loader.tdn` | Yes |

---

## 7. Build Plan (Executable Steps)

### Phase A: Foundation (NOW — TD is open, Embody installed)

| Step | Action | MCP Tool |
|------|--------|----------|
| A1 | Save current TD project as `grandmaster_melodia.toe` in `_TouchDesigner/` | Manual in TD |
| A2 | Create `/audio` container with Audio File In CHOP | `create_op` |
| A3 | Create `/postfx` container with Bloom chain (3-pass Gaussian) | `create_op` + `connect_ops` |
| A4 | Create `/osc` container with OSC Out CHOPs to ports 8000/9000 | `create_op` |
| A5 | Create `/render` container with Render TOP output chain | `create_op` |
| A6 | Tag all top-level COMPs for TDN externalization | Embody `lctrl+lctrl` |
| A7 | Export all networks → `networks/*.tdn` | `export_network` |
| A8 | Commit to git | Manual |

### Phase B: Style Presets (after Phase A)

| Step | Action | MCP Tool |
|------|--------|----------|
| B1 | Build preset switcher UI (5 radio buttons) | `create_op` (sliderCOMP) |
| B2 | Create preset parameter storage (Table DAT with 5×12 matrix) | `create_op` (tableDAT) |
| B3 | Wire preset → bloom parameters | `connect_ops` |
| B4 | Wire preset → OSC out (toon_params) | `connect_ops` |
| B5 | Export preset network → `networks/style_presets.tdn` | `export_network` |

### Phase C: Particle Systems (after Phase B)

| Step | Action | MCP Tool |
|------|--------|----------|
| C1 | Build sparkle POP (40 particles, 4-star sprites, gold→pink) | `create_op` (particlesGpuCOMP) |
| C2 | Build mote POP (50 particles, soft radial dots) | `create_op` |
| C3 | Build wish burst POP (120 particles, audio-triggered) | `create_op` |
| C4 | Wire audio CHOPs → particle parameters | `connect_ops` |
| C5 | Export particle networks → `networks/particles.tdn` | `export_network` |

### Phase D: Portfolio Viewer (after Phase C)

| Step | Action | MCP Tool |
|------|--------|----------|
| D1 | Build project selector (Dropdown COMP) | `create_op` |
| D2 | Wire selector → FBX loader | `connect_ops` |
| D3 | Build stats overlay (Text TOP reading manifest JSON) | `create_op` |
| D4 | Build material sheet (Table COMP) | `create_op` |
| D5 | Build camera orbit rig (Camera COMP + sin/cos CHOP) | `create_op` |

### Phase E: Integration & Polish (after Phase D)

| Step | Action | MCP Tool |
|------|--------|----------|
| E1 | Load Nikki gazebo FBX → verify render | Manual test |
| E2 | OSC round-trip test with UE | `execute_python` (td_bridge.py --verify) |
| E3 | Full style preset cycle test (all 5 presets) | `execute_python` |
| E4 | Audio reactivity test with Melusina WAV | Manual test |
| E5 | Capture hero render at 4K | `capture_top` |
| E6 | TDN export all networks, commit to git | `export_network` |

---

## 8. Integration Points With Existing Grandmasters

| TD Grandmaster → | Protocol | What Flows |
|------------------|----------|------------|
| **Figma Grandmaster** | export: PNG renders → Figma fill slots | Hero renders, material sheets, particle stills |
| **GMM (Unreal)** | OSC + Spout | Style presets, audio-reactive params, real-time shader preview |
| **Melodia Studio (Blender)** | OSC + FBX import | Camera transforms, geometry counts, world manifest loading |
| **Wix/Web** | Figma pipeline → GitHub Pages | Portfolio captures, animated previews |

---

## 9. Success Criteria

- [ ] TD Grandmaster project loads Nikki gazebo FBX with correct materials
- [ ] 5 style presets switch correctly (bloom, color, particles all update)
- [ ] Melusina WAV drives particle spawn rate via audio CHOPs
- [ ] OSC parameters reach UE on port 8000 (validated via td_bridge.py)
- [ ] All networks exported as `.tdn` and committed to git
- [ ] Portfolio viewer shows project stats overlay and material sheet
- [ ] Hero render captured at 4K matching Nikki aesthetic reference
- [ ] Single AI prompt via Envoy MCP switches preset, changes particles, screenshots

---

## 10. Immediate Next Step

Run Phase A right now — build the foundation containers in TD:

```
TODO: AI agent uses Envoy MCP to:
  create_op("audio", "baseCOMP", parent="/project1")
  create_op("postfx", "baseCOMP", parent="/project1")  
  create_op("particles", "baseCOMP", parent="/project1")
  create_op("osc", "baseCOMP", parent="/project1")
  create_op("render", "baseCOMP", parent="/project1")
  create_op("geo", "baseCOMP", parent="/project1")
  create_op("ui", "baseCOMP", parent="/project1")
```

Then tag each for TDN externalization so everything is git-versioned from the start.
