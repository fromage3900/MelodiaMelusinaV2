# TouchDesigner + MCP Integration Plan — Environment Portfolio Platform

**Version:** 1.0.0
**Date:** 2026-07-15
**Branch:** `feature/touchdesigner-mcp-integration`
**Status:** Draft — Awaiting Phase 1 Execution

---

## 1. Executive Summary

This document defines the integration of **TouchDesigner** (Derivative) as a third pillar in the Environment Portfolio Platform, sitting alongside **Blender 5.1** (procedural geometry) and **Unreal Engine 5.8** (scene composition & rendering). TouchDesigner fills the platform's missing real-time interactivity, audio-reactivity, and live-visualization gaps while enabling **unified MCP (Model Context Protocol) orchestration** — a single AI agent controlling all three DCC tools simultaneously.

### Why TouchDesigner?

| Gap in Current Pipeline | How TouchDesigner Fills It |
|--------------------------|----------------------------|
| No real-time visual preview during iteration | Live compositing & FX in TD TOPs/SOPs |
| VoiceSynth (Melusina) audio has no visual target | Audio CHOPs → reactive shader parameters → OSC to UE |
| Portfolio is static renders only | Interactive portfolio viewer with parameter morphing, day/night cycles |
| AI agents are siloed per tool (PGA↔Blender, MPA↔UE) | Unified MCP layer: one agent orchestrates Blender + TD + UE |
| No live performance / demo mode | TD is purpose-built for real-time performance installations |
| Shader prototyping is slow (UE material graph edits → recompile → test) | Prototype GLSL in TOPs interactively, port to UE when validated |

---

## 2. Architecture Overview

### 2.1 Three-Pillar Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    UNIFIED MCP ORCHESTRATION LAYER                    │
│               (AI Agent → Embody/Envoy + Monolith + Blender MCP)     │
└───────┬─────────────────────────┬───────────────────────────────────┘
        │                         │
        ▼                         ▼
┌───────────────┐  ┌──────────────────────────────┐  ┌───────────────────┐
│   BLENDER 5.1  │  │     TOUCHDESIGNER 2025+     │  │  UNREAL ENGINE 5.8 │
│                │  │                              │  │                    │
│ • Surreal Arch │  │ • Real-time compositing      │  │ • Scene composition│
│ • Geometry Gen │  │ • Audio analysis & reactivity │  │ • PCG scattering   │
│ • Greybox Sys  │  │ • Shader prototyping (GLSL)  │  │ • Nanite/Lumen      │
│ • Material Make│◄─┤ • Particle systems (POPs)    ├─►│ • Substrate Toon   │
│ • Live Link    │  │ • DMX/LED output             │  │ • Monolith MCP      │
│ • World Export │  │ • Portfolio viewer           │  │ • Render captures   │
│ • Blender MCP  │  │ • Embody/Envoy MCP (53 tools)│  │ • Figma pipeline   │
└───────┬───────┘  └──────────────┬───────────────┘  └─────────┬─────────┘
        │                         │                             │
        │     OSC / Spout         │      OSC / Spout / NDI     │
        └─────────────────────────┴─────────────────────────────┘
              Real-time bridges between all three tools
```

### 2.2 Communication Matrix

| From → To | Protocol | Purpose | Latency |
|-----------|----------|---------|---------|
| Blender → TouchDesigner | OSC | Geometry parameter sync, camera transforms | < 5ms |
| TouchDesigner → Blender | OSC | Audio analysis results, animation curves | < 5ms |
| Blender → TouchDesigner | Spout | Live viewport texture streaming (Windows only) | < 1 frame |
| TouchDesigner → Unreal | OSC | Material parameters, audio-reactive values | < 5ms |
| TouchDesigner → Unreal | Spout | Real-time texture/shader output | < 1 frame |
| TouchDesigner → Unreal | NDI | Compressed video streaming | 1-2 frames |
| Unreal → TouchDesigner | OSC | Render pass feedback, camera state | < 5ms |
| Unreal → TouchDesigner | Spout | Render target preview | < 1 frame |
| AI Agent → TouchDesigner | MCP (HTTP) | Network creation, parameter control, Python exec | ~50ms |
| AI Agent → Unreal | MCP (Monolith) | Editor control, scene capture, material inspection | ~50ms |
| AI Agent → Blender | MCP (9877) | Python execution, mesh generation | ~50ms |
| TD ↔ UE (heavy) | TouchEngine SDK | Full .tox component hosting inside UE | Process-level |

---

## 3. MCP Unification Layer

**This is the core innovation.** Three existing MCP servers, one unified agent:

### 3.1 Existing MCP Servers (Already in the Project)

| Server | Tool | Port | Status |
|--------|------|------|--------|
| **Monolith MCP** | Unreal Engine 5.8 | 9316 | Active — 28 tools |
| **Blender MCP** | Blender 5.1 | 9877 | Configured — needs user enable |
| **(NEW) Embody/Envoy** | TouchDesigner 2025+ | 9870 | To be installed |

### 3.2 The Embody/Envoy MCP Server

Selected over `8beeeaaat/touchdesigner-mcp` for these reasons:

| Feature | Embody | 8beeeaaat |
|---------|--------|-----------|
| Tools | **53** | 12 |
| YAML network export (TDN) | **Yes** | No |
| Git-diffable version control | **Yes** | No |
| Undo support | **Yes (one Ctrl+Z per batch)** | No |
| Multi-session coordination | **Yes** (`claim_scope`/`release_scope`) | No |
| Auto-restoration on project open | **Yes** | No |
| Clipboard paste from web | **Yes** | No |
| Test suites | **92 suites / 2,090 tests** | None |
| Maturity | 624 commits, v6.0.126 | 103 commits, v1.5.0 |
| Language | Python (native to TD) | TypeScript (Node.js) |
| Auto-generates AGENTS.md | **Yes** | No |

**Installation target:** `G:\EnvironmentPortfolio\_TouchDesigner\` as the project root for Embody's `.mcp.json` generation.

### 3.3 Unified MCP Configuration

Every AI client (Claude Code, Codex, Cursor, Windsurf, Copilot) sees **all three MCP servers** simultaneously in `.mcp.json`:

```json
{
  "mcpServers": {
    "envoy": {
      "type": "http",
      "url": "http://localhost:9870/mcp"
    },
    "monolith": {
      "type": "http",
      "url": "http://localhost:9316/mcp"
    },
    "blender": {
      "type": "http",
      "url": "http://localhost:9877/mcp"
    }
  }
}
```

A single AI session can now:
1. Generate architecture in Blender (`blender` tools)
2. Stream it to TouchDesigner for real-time FX and audio-reactive treatment (`envoy` tools)
3. Export treated scene to Unreal Engine for final composition and rendering (`monolith` tools)
4. Capture portfolio renders and deploy to web — all in one loop

---

## 4. The 6th Agent: TouchDesigner Orchestrator Agent (TOA)

### 4.1 Role Definition

A new agent persona joining the 5-agent framework defined in `BS_GodFile/AGENTS.md`:

| Attribute | Value |
|-----------|-------|
| **Role** | Real-Time Interaction & MCP Orchestration Specialist |
| **Specialization** | TouchDesigner network architecture, audio-reactive visual design, real-time shader prototyping, multi-tool MCP coordination |
| **System Ownership** | All `.toe` project files, `.tox` components, TDN-exported networks, OSC routing tables, Spout/NDI stream configurations |
| **Tooling** | TouchDesigner 2025+, Embody/Envoy MCP, OSC protocol, Spout SDK, GLSL, Python 3.11 (`td` module) |

### 4.2 System Boundaries

| File Path / Resource | Read | Write | Constraints |
|----------------------|------|-------|-------------|
| `_TouchDesigner/*.toe` | TOA | TOA | Embody must be installed in each project |
| `_TouchDesigner/components/*.tox` | All agents | TOA | Components must declare I/O ports |
| `_TouchDesigner/networks/*.tdn` | All agents | TOA | Git-versioned; diff before commit |
| `BS_GodFile/Content/Python/td_bridge.py` (new) | TOA, WIA | TOA, WIA | OSC config shared with UE OSC plugin |
| `BS_GodFile/deploy/osc_routing.json` (new) | TOA, WIA, SQA | TOA | Schema changes require SQA approval |
| `_AssetLibrary/TD_Shaders/` (new) | TOA, MPA | TOA | GLSL prototypes → MPA ports to UE Material |
| `VoiceSynthResearch/` (read-only) | TOA | None | Audio files accessed via TD Audio File In CHOP |

### 4.3 Communication Contracts

#### 4.3.1 OSC Routing Schema (`osc_routing.json`)

```json
{
  "version": "1.0",
  "routes": {
    "audio": {
      "melusina_pitch": { "path": "/melusina/pitch", "type": "float", "range": [60, 2000] },
      "melusina_amplitude": { "path": "/melusina/amp", "type": "float", "range": [0, 1] },
      "melusina_formants": { "path": "/melusina/formants", "type": "float_array", "size": 5 }
    },
    "camera": {
      "ue_camera_transform": { "path": "/ue/camera", "type": "float_array", "size": 16 },
      "td_camera_transform": { "path": "/td/camera", "type": "float_array", "size": 16 }
    },
    "material": {
      "toon_params": { "path": "/material/toon", "type": "float_array", "size": 12 },
      "style_preset": { "path": "/material/preset", "type": "int", "range": [0, 4] }
    },
    "time": {
      "day_night_cycle": { "path": "/time/cycle", "type": "float", "range": [0, 1] },
      "beat_sync": { "path": "/time/beat", "type": "float", "range": [0, 1] }
    }
  }
}
```

#### 4.3.2 Spout Stream Registry

| Stream Name | Producer | Consumer | Resolution | Format |
|-------------|----------|----------|------------|--------|
| `TD_ShaderPreview` | TouchDesigner TOP | Unreal (SpoutReceiver plugin) | 1920x1080 | RGBA8 |
| `UE_RenderTarget` | Unreal (SpoutSender) | TouchDesigner TOP | Variable | RGBA16F |
| `Blender_Viewport` | Blender (Spout addon) | TouchDesigner TOP | Variable | RGBA8 |

#### 4.3.3 TDN Network Contract

All TouchDesigner networks used in the pipeline are externalized as `.tdn` files (diffable YAML) and checked into version control. This means:
- Every TD network change is code-reviewable as a git diff
- AI agents can read and understand the full network via the `export_network` MCP tool
- Networks can be reconstructed deterministically from `.tdn` files on project open (Roundtrip mode)

---

## 5. Technical Integration Details

### 5.1 TouchDesigner ↔ Blender Bridge

**Primary: OSC over UDP**

Blender side (NodeOSC addon or custom Python):
```python
# In Blender Python — send geometry metadata to TD
import socket, json, struct

def send_osc(host, port, address, *args):
    # OSC message builder → UDP socket
    pass

# On every depsgraph update:
send_osc("127.0.0.1", 9000, "/blender/mesh/count", len(bpy.data.objects))
send_osc("127.0.0.1", 9000, "/blender/camera/pos", *camera.location)
```

TouchDesigner side (OSC In DAT + CHOP):
```
OSC In DAT (port 9000) → DAT to CHOP → Math CHOP → Constraint CHOP → Export CHOP
```

**Secondary: Spout (Windows) for live viewport sharing**

Blender requires the community Spout addon (`spout-blender` on GitHub). TD has native **Spout In TOP**.

### 5.2 TouchDesigner ↔ Unreal Engine Bridge

**Primary: OSC over UDP**

UE side uses the native OSC plugin (enabled in `BS_GodFile.uproject`):

```python
# In Unreal Python — receive TD audio parameters
import unreal
osc_manager = unreal.OSCManager

# Listen for /material/toon parameter updates
# Map to Substrate Toon BSDF parameters in real-time
```

TouchDesigner side:
```
Audio File In CHOP → Analyze CHOP → Math CHOP → OSC Out CHOP (→ UE on port 8000)
```

**Secondary: TouchEngine SDK (deep integration)**

For scenarios requiring full `.tox` component execution inside UE:
- Install TouchEngine for UE Plugin from GitHub (`TouchDesigner/TouchEngine-UE`)
- Load `.tox` files as UE assets
- Bidirectional texture and data passing at process level

**Tertiary: Spout for texture sharing**
- TD Spout Out TOP → UE SpoutReceiver plugin → UE Render Target
- Enables real-time TD compositing overlaid on UE scene

### 5.3 VoiceSynth → Visual Pipeline

The Melusina (DiffSinger/OpenUtau) voicebank gains a visual dimension:

```
Melusina WAV render
       │
       ▼
TouchDesigner Audio File In CHOP
       │
       ├──► Pitch CHOP → OSC → UE Substrate Toon "impressionist" shader warp
       ├──► Amplitude CHOP → OSC → UE particle spawn rate (Niagara)
       ├──► Spectral CHOP → OSC → TD particle system color palette
       └──► Beat CHOP → OSC → UE camera shake / world shader time offset
```

### 5.4 Interactive Portfolio Viewer

TouchDesigner hosts a real-time portfolio browser:

```
TD Panel COMP layout:
┌──────────────────────────────────────────────┐
│  [Project Selector]  ← populated from        │
│                       portfolio_package.json  │
│                                               │
│  ┌────────────────────────────────┐           │
│  │    3D Viewport (Render TOP)    │           │
│  │   - FBX/USD model loaded       │           │
│  │   - Day/night cycle slider     │           │
│  │   - Material preset switcher   │           │
│  │   - Audio reactive mode        │           │
│  └────────────────────────────────┘           │
│                                               │
│  [Stats Overlay]  [Material Sheet]  [Wireframe]
└──────────────────────────────────────────────┘
```

Export pipeline: UE → FBX/USD export → TD FBX COMP / USD In COMP → lit and animated in TD.

### 5.5 Shader Prototyping Workflow

```
1. AI Agent describes shader concept
   │
2. TOA builds GLSL prototype in TD GLSL TOP
   │  (instant feedback, no UE recompile)
   │
3. Iterate until visually approved
   │
4. Export GLSL → MPA ports to UE Material Graph
   │  via setup_material_functions.py or custom UE Material node
   │
5. Validate parity between TD prototype and UE render
```

---

## 6. Implementation Phases

### Phase 1: Foundation (Week 1-2)

| Step | Task | Owner | Dependencies |
|------|------|-------|-------------|
| 1.1 | Create `_TouchDesigner/` directory structure | TOA | None |
| 1.2 | Install Embody `.tox` into a base TD project | TOA | TD 2025.32820+ |
| 1.3 | Verify Envoy MCP connectivity from AI client | TOA + WIA | Step 1.2 |
| 1.4 | Write `.mcp.json` with all 3 servers at project root | TOA | Step 1.3 |
| 1.5 | Install Blender NodeOSC addon | PGA | None |
| 1.6 | Enable UE OSC plugin in `BS_GodFile.uproject` | WIA | None |
| 1.7 | Verify OSC round-trip: Blender → TD → UE | All agents | Steps 1.5, 1.6 |
| 1.8 | Commit baseline `.gitignore`, directory structure | SQA | All above |

**Deliverable:** All three tools communicating via MCP + OSC. AI agent can query all three tools from one session.

### Phase 2: Audio Reactivity (Week 2-3)

| Step | Task | Owner | Dependencies |
|------|------|-------|-------------|
| 2.1 | Build TD audio analysis network (Pitch, Amp, Spectral, Beat) | TOA | Phase 1 complete |
| 2.2 | Create `osc_routing.json` with Melusina audio parameters | TOA | Step 2.1 |
| 2.3 | Wire OSC routes: TD → UE material parameters | TOA + MPA | Step 2.2 |
| 2.4 | Test with reference Melusina WAV render | TOA + SQA | Step 2.3 |
| 2.5 | Build "audio-reactive demo" TD network | TOA | Step 2.4 |

**Deliverable:** Melusina singing voice drives visual effects in Unreal Engine in real-time.

### Phase 3: Portfolio Viewer (Week 3-4)

| Step | Task | Owner | Dependencies |
|------|------|-------|-------------|
| 3.1 | Define FBX/USD export pipeline from UE | WIA | Phase 1 complete |
| 3.2 | Build TD portfolio viewer base network | TOA | Step 3.1 |
| 3.3 | Implement project selector from `portfolio_package.json` | TOA | Step 3.2 |
| 3.4 | Add day/night cycle to viewer (hooked to TD World SHOP) | TOA | Step 3.2 |
| 3.5 | Add material preset switcher (Nikki, Madoka, Celestial, Itto, Sakura) | TOA + MPA | Step 3.2 |
| 3.6 | Polish viewer UI in TD Panel COMPs (Melodia design tokens) | TOA | Step 3.3-3.5 |

**Deliverable:** Interactive portfolio viewer in TouchDesigner that loads UE exports.

### Phase 4: MCP Orchestration Demo (Week 4-5)

| Step | Task | Owner | Dependencies |
|------|------|-------|-------------|
| 4.1 | Write orchestration prompt: "Build a Zen shrine, add audio-reactive materials, render to portfolio" | TOA | Phase 2+3 |
| 4.2 | AI agent executes: Blender geometry → TD audio FX → UE render → Figma deploy | All agents | Step 4.1 |
| 4.3 | SQA audits full loop output | SQA | Step 4.2 |
| 4.4 | Record demo video of unified workflow | TOA | Step 4.3 |

**Deliverable:** Recorded demo of single AI prompt controlling Blender + TD + UE end-to-end.

### Phase 5: Production Hardening (Ongoing)

| Step | Task | Owner | Dependencies |
|------|------|-------|-------------|
| 5.1 | Write TOA-specific agent rules (AGENTS.md updates) | TOA + SQA | Phase 4 |
| 5.2 | Add TD to PowerShell loop runners | WIA | Phase 4 |
| 5.3 | Performance profiling: OSC latency, Spout throughput | TOA + SQA | Phase 4 |
| 5.4 | Write TD smoke tests (via Embody `run_tests` MCP tool) | TOA | Step 5.2 |
| 5.5 | Document all networks in TDN format, commit to repo | TOA | Ongoing |

---

## 7. Directory Structure

```
G:\EnvironmentPortfolio\
├── _TouchDesigner/                    ← NEW: TD project root
│   ├── .mcp.json                      ← Auto-generated by Embody
│   ├── AGENTS.md                      ← Auto-generated by Envoy
│   ├── CLAUDE.md                      ← Auto-generated for Claude Code
│   ├── env_portfolio_base.toe         ← Master TD project
│   ├── components/                    ← Reusable .tox components
│   │   ├── melodia_audio_analyzer.tox
│   │   ├── melodia_portfolio_viewer.tox
│   │   ├── melodia_shader_prototype.tox
│   │   └── melodia_osc_router.tox
│   ├── networks/                      ← TDN-exported networks (git-versioned)
│   │   ├── audio_pipeline.tdn
│   │   ├── portfolio_viewer.tdn
│   │   └── shader_library.tdn
│   ├── shaders/                       ← GLSL prototypes
│   │   ├── toon_nikki.glsl
│   │   ├── toon_madoka.glsl
│   │   ├── toon_celestial.glsl
│   │   ├── toon_itto.glsl
│   │   └── toon_sakura.glsl
│   └── exports/                       ← Rendered outputs, screenshots
├── BS_GodFile/
│   ├── Content/Python/
│   │   └── td_bridge.py               ← NEW: OSC client for UE→TD comms
│   ├── deploy/
│   │   └── osc_routing.json           ← NEW: Shared OSC schema
│   └── Plugins/
│       └── TouchEngine/               ← Optional: TouchEngine for UE
├── _AssetLibrary/
│   └── TD_Shaders/                    ← NEW: TD-curated GLSL sources
├── VoiceSynthResearch/                ← (Existing, read-only for TOA)
├── Docs/
│   └── TOUCHDESIGNER_MCP_INTEGRATION_PLAN.md  ← This document
└── .gitignore                         ← UPDATED: Added TD patterns
```

---

## 8. Risk Analysis & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| TouchDesigner license cost (Commercial ~$600) | N/A | Low | User has license installed |
| Embody requires TD 2025.32820+ | Medium | High | Verify TD version before install |
| OSC packet loss under heavy load | Low | Medium | Use TCP OSC for critical params; Spout for textures |
| Spout is Windows-only | N/A | None | Project is Windows-based |
| Blender Spout addon instability | Medium | Low | Fallback to OSC-only; Spout for UE↔TD is native |
| AI agent confusion across 3 MCP tool sets | Medium | Medium | AGENTS.md per-tool context; Embody auto-generates Claude rules |
| Increased project complexity | Medium | Low | TouchDesigner is optional; pipeline works without it |
| TouchEngine requires end-user TD license | Low | Low | Only used in development; Commercial license covers it |

---

## 9. Success Criteria

- [ ] AI agent can create a TouchDesigner network via Envoy MCP and see live results
- [ ] OSC messages flow bidirectionally between all 3 tools (Blender ↔ TD ↔ UE)
- [ ] Melusina audio WAV drives real-time visual changes in UE material parameters
- [ ] Interactive portfolio viewer loads UE-exported FBX/USD and renders with Melodia toon shaders
- [ ] Single AI prompt executes end-to-end: Blender geometry → TD audio FX → UE render → Figma deploy
- [ ] All TD networks are version-controlled as `.tdn` files in git
- [ ] SQA smoke tests pass for the full 3-tool pipeline
- [ ] Demo video recorded showing unified workflow

---

## 10. References

| Resource | URL |
|----------|-----|
| Embody (Envoy MCP) | https://github.com/dylanroscover/Embody |
| TouchDesigner MCP (alt) | https://github.com/8beeeaaat/touchdesigner-mcp |
| TouchEngine for UE | https://github.com/TouchDesigner/TouchEngine-UE |
| TouchEngine SDK (Windows) | https://github.com/TouchDesigner/TouchEngine-Windows |
| TouchDesigner Docs | https://docs.derivative.ca/ |
| Blender NodeOSC Addon | https://github.com/maybites/blender.NodeOSC |
| Blender Spout Addon | https://github.com/spoutblender/spoutblender |
| UE OSC Plugin | Built-in (enable in `.uproject` plugins list) |
| Spout SDK | https://github.com/SpoutDev/Spout2 |
| OSC Protocol Spec | https://opensoundcontrol.stanford.edu/ |

---

## Appendix A: Envoy MCP Tools (Complete List)

*53 tools available in Embody v6.0.126 — key tools for this integration:*

| Tool | Use in This Pipeline |
|------|---------------------|
| `create_op` | Build audio analysis networks, portfolio viewer UI |
| `connect_ops` | Wire CHOPs → TOPs → SOPs |
| `set_parameter` | Tune audio analysis thresholds, shader uniforms |
| `execute_python` | Run custom OSC bridge scripts |
| `export_network` | Generate `.tdn` for git version control |
| `import_network` | Restore networks from `.tdn` on project open |
| `diff_tdn` | Review TD changes before commit (like git diff for TD networks) |
| `capture_top` | Verify visual output (returns pixel grid + quality verdict) |
| `get_docs` | Query official TD documentation from MCP context |
| `batch_operations` | Execute complex multi-step builds in one undo block |
| `run_tests` | Execute TD-specific smoke tests |
| `create_extension` | Scaffold new TD extensions (COMP + DAT + wiring) |

## Appendix B: Monolith MCP Tools (Existing)

*28 tools already active in UE 5.8 — key for TD interplay:*

| Tool | Use in This Pipeline |
|------|---------------------|
| Scene capture / render | Portfolio renders triggered by unified agent |
| Material inspection | Validate TD-shader → UE-material ports |
| CSV profiling | Performance data fed to TD dashboard overlays |

## Appendix C: Quick-Start Checklist

For the user to begin Phase 1:

1. [ ] Verify TouchDesigner version ≥ 2025.32820
2. [ ] Download `Embody-v6.0.126.tox` from https://github.com/dylanroscover/Embody/releases/latest
3. [ ] Create `G:\EnvironmentPortfolio\_TouchDesigner\` directory
4. [ ] Create base TD project: drag Embody `.tox` into fresh project, save as `env_portfolio_base.toe`
5. [ ] Toggle `Envoyenable` on Embody COMP → verify server on `localhost:9870`
6. [ ] Verify `.mcp.json` auto-generated at project root or `_TouchDesigner/`
7. [ ] Install Blender NodeOSC addon from GitHub
8. [ ] Enable UE OSC plugin in `BS_GodFile.uproject` (add `"OSC": { "Name": "OSC", "Enabled": true }`)
9. [ ] Run Phase 1 verification: `py verify_osc_loop.py` (to be written in Step 1.7)
