# Grandmaster Melodia — Master Integration Plan (v2.0)

**Version:** 2.0.0
**Date:** 2026-07-15
**Branch:** `feature/touchdesigner-mcp-integration`
**Status:** Executing

---

## Version Lock

| Tool | Version | Key Detail |
|------|---------|------------|
| **TouchDesigner** | 2025.32460 (Mar 10 2026) | Python 3.11.10, Embody v6.0.126 installed |
| **Unreal Engine** | 5.8 | Monolith MCP on :9316 |
| **Blender** | 5.1 | Surreal Architecture v2.134.0, 417 classes |
| **TouchEngine UE Plugin** | v1.7.0 (UE 5.7) | Needs source build for UE 5.8 |
| **Embody/Envoy** | v6.0.126 | Envoy on localhost:9870 (SSE transport) |

## Critical Finding: TouchEngine UE Plugin

The official TouchEngine UE Plugin targets **UE 5.7**, not 5.8. For UE 5.8 integration, there are two paths:

| Path | Latency | Setup | Best For |
|------|---------|-------|----------|
| **OSC + Spout** | < 5ms | Zero plugin dependency | Real-time parameter control, texture sharing, audio reactivity |
| **TouchEngine Source Build** | Process-level | Compile plugin for UE 5.8 | Loading .tox components as native UE assets, offline rendering |

**Decision: OSC + Spout for real-time control. TouchEngine for offline .tox asset loading.**

## Critical Finding: TD Python API

The `COMP.create()` method accepts both type objects AND string names:
```python
me.create('audiofilein', 'myAudioIn')    # string — always works
me.create(audiofileinCHOP, 'myAudioIn')  # type object — works if defined
```

Some type objects (`lumaKeyTOP`, `waveCHOP`) don't exist in TD 2025.32460. **Use string names for reliability.**

---

## 2. Three Integration Paths (UE 5.8)

### Path A: OSC Real-Time Control (Production)
```
TouchDesigner OSC Out CHOP :8000  ──►  Unreal Engine OSC Plugin
  Channels: /material/preset, /niagara/sparkle/rate, /melusina/pitch

Unreal Engine OSC Server :8001  ──►  TouchDesigner OSC In CHOP
  Channels: /ue/camera, /ue/render/stats
```
- Zero plugin dependency
- < 5ms latency over localhost UDP
- 12 toon parameters, 13 Niagara parameters, 5 audio channels

### Path B: Spout Texture Sharing (Production)
```
TD Spout Out TOP  ──►  UE SpoutReceiver Plugin
  Stream: "TD_MelodiaPreview" (1920x1080, RGBA8, 60fps)

UE Spout Sender  ──►  TD Spout In TOP
  Stream: "UE_RenderTarget" (variable, RGBA16F, 60fps)
```
- GPU zero-copy texture sharing
- Windows-only (project target matches)
- TD has native Spout In/Out TOPs

### Path C: TouchEngine .tox Loading (Offline/Precomputed)
```
TD COMP → Save .tox  ──►  UE Content Browser → ToxAsset → TouchEngine Actor
```
- For pre-built TD components (post-FX chains, particle presets)
- Requires plugin source compile for UE 5.8
- Best for: Nikki LUT, bloom chain, audio analyzer as reusable UE assets

---

## 3. Infinity Nikki Developer Lens

### What Papergames Would Use TD For

Infinity Nikki uses UE5 with Enlighten GI, proprietary cloth/fabric systems, and a soft "dreamy" PBR+toon hybrid. **As an Infinity Nikki developer**, here is where TouchDesigner slots in:

| Production Need | Current Nikki Pipeline | TD Enhancement |
|-----------------|----------------------|----------------|
| **Shader prototyping** | UE Material Graph edits → recompile → test (slow) | TD GLSL TOP → instant feedback → port to UE Material when approved |
| **Particle tuning** | Niagara parameter tweaking in-editor (slow iteration) | TD POPs → real-time OSC → Niagara live parameters |
| **Bloom/color grade iteration** | UE Post Process Volume → cook → check (slow) | TD Composite TOP chain → instant feedback → port final values to UE PP |
| **Audio-reactive VFX** | Manual keyframing or blueprint triggers | TD Audio CHOP analysis → OSC → Niagara spawn rates |
| **Fabric material lookdev** | Substance → UE material instance → test render | TD GLSL anisotropic satin → tune in real-time → export to UE |
| **Portfolio presentation** | Static UE renders → Figma → Wix | TD interactive viewer → live preset switching → hero capture |
| **Wish energy/Whimstar FX** | Niagara system authoring (1-3 days per system) | TD POP prototype in < 1 hour → OSC parameters → Niagara port |

### Nikki Visual DNA in TD Terms

```
Bloom:     3-pass Gaussian (5px, 15px, 30px), additive composite, threshold 0.75, tint #FFF5F0
Shadows:   Lifted +0.08, tinted #352D40 (warm violet, never black)
Diffuse:   Half-Lambert wrap (0.5), soft shadow transition
Specular:  Anisotropic Blinn-Phong, roughness clamped > 0.3, satin sheen
Rim:       Fresnel-based, warm cream tint, intensity 0.3-0.5
Particles: Additive blend, 4-point star SDF sprites, gold→pink color shift, sin-wave drift
DOF:       Soft bokeh near-field, cinematic focus pulls in cutscenes
Color:     Slightly desaturated (0.9), warm midtone bias, cool shadow lift
```

---

## 4. Master Execution Plan

### Phase 1: TD Foundation (NOW — direct in TD)

Since `create()` works with string names in this build, scaffold using reliable string type names.

```python
# Phase 1 Scaffold — run in TD Textport (Alt+T)
me = op('/project1')

# 7 foundation containers with string type names
audio     = me.create('base', 'audio')
postfx    = me.create('base', 'postfx')
particles = me.create('base', 'particles')
shaders   = me.create('base', 'shaders')
osc       = me.create('base', 'osc')
geo       = me.create('base', 'geo')
render    = me.create('base', 'render')
ui        = me.create('base', 'ui')

print('Grandmaster containers created in', me.path)
```

### Phase 2: Nikki Post-FX Chain
- Bloom: `lumaLevel` TOP → 3x `blur` TOP → `composite` TOP
- Color grade: `ramp` TOP → `lookup` TOP
- Vignette: `ramp` TOP (radial) → `over` TOP

### Phase 3: OSC Routing Hub
- `oscin` CHOP on port 9000 (Blender camera)
- `oscout` CHOP on port 8000 (UE material + Niagara)
- `table` DAT for routing map

### Phase 4: Audio Engine
- `audiofilein` CHOP → Melusina WAV
- `pitch` CHOP → `/melusina/pitch`
- `envelope` CHOP → `/melusina/amp`
- `spectrum` CHOP → particle color
- `beat` CHOP → wish burst trigger

### Phase 5: Particle Systems
- `particlesGpu` COMP × 3 (sparkles, motes, burst)
- Wired to audio CHOPs for reactivity

### Phase 6: UE 5.8 Integration
- TouchEngine plugin source compile for UE 5.8 (or stick with OSC/Spout)
- OSC Plugin already in BS_GodFile.uproject
- SpoutReceiver plugin install

### Phase 7: Style Presets
- Table DAT with 5×12 preset matrix
- Switch CHOP → OSC out

### Phase 8: Portfolio Viewer
- FBX loader → Nikki post-FX → Render TOP
- Dropdown COMP for project selection
- Text TOP stats overlay

---

## 5. What's Already Built

| Artifact | Location | Status |
|----------|----------|--------|
| Nikki gazebo FBX | `_TouchDesigner/exports/nikki_sanctuary.fbx` | Ready to load |
| World manifest | `_TouchDesigner/exports/nikki_sanctuary.world.json` | 1,579 tris |
| Niagara FX manifest | `Content/Python/gmm/fixtures/niagara_nikki_library.json` | 5 systems, 11 routes |
| OSC routing schema | `BS_GodFile/deploy/osc_routing.json` | Full spec |
| TD bridge script | `Content/Python/td_bridge.py` | 5 presets, CLI |
| OSC validator | `Content/Python/validate_osc_loop.py` | 8/8 pass |
| Daemon scripts | `BS_GodFile/deploy/start_td_*.ps1` | 4 services |
| TD particle builder | `_TouchDesigner/components/nikki_particles.py` | 3 POPs, OSC routing |
| MCP config | `.mcp.json` | All 3 servers |
| Cursor MCP | `~/.cursor/mcp.json` | Envoy added |
| Architecture docs | `Docs/TOUCHDESIGNER_MCP_INTEGRATION_PLAN.md` | Full spec |
| Vertical slice plan | `Docs/NIKKI_VERTICAL_SLICE_PLAN.md` | 20-min spec |
| Grandmaster plan | `Docs/TD_GRANDMASTER_MELODIA_PLAN.md` | 7 containers |
| Agent framework | `BS_GodFile/AGENTS.md` | 6 agents |

---

## 6. Immediate Next Action

Run this in TD Textport (uses string type names — battle-tested for 2025.32460):

```python
me = op('/project1')
for name in ['audio','postfx','particles','shaders','osc','geo','render','ui']:
    comp = me.create('base', name)
    comp.comment = 'Grandmaster Melodia — ' + name
    print('Created', comp.path)
print('Phase 1 scaffold complete.')
```

Then we build Phase 2 (Nikki post-FX) directly in TD, one container at a time, each committed as `.tdn` for version control.
