# Vertical Slice: Florawish Sanctuary — Nikki-Style 20-Minute Pipeline

**Version:** 1.0.0
**Date:** 2026-07-15
**Branch:** `feature/touchdesigner-mcp-integration`
**Lens:** Infinity Nikki Developer (Papergames / Infold Games)
**Goal:** 20-minute end-to-end vertical slice proving the Blender→TouchDesigner→Unreal pipeline with Nikki aesthetic fidelity

---

## 1. Vertical Slice Concept

**"Florawish: A Nikki-Style Sanctuary"**

A single, polished environment vignette in the Infinity Nikki style:
- A whimsical European-fantasy gazebo on a floating island
- Surrounded by dense flower meadows (instanced)
- Fabric canopy with satin sheen and cloth simulation
- Warm, golden-hour lighting with heavy soft bloom
- Wish-energy sparkles floating lazily through the scene
- Audio-reactive particles driven by Melusina (operatic vocal WAV)
- Camera slowly orbits the gazebo like a cutscene

**Creative North Star**: This could be a gacha-banner splash screen location. When you pull a 5-star outfit, this is the dreamscape where Nikki poses.

---

## 2. Nikki Aesthetic Reference Card

### Color Bible

```
Sky Blue (day):            #B5D8EB → soft periwinkle-washed cerulean
Grass / Meadow:            #A8D8A8 → pastel sage, not saturated green
Florawish Terracotta:      #E8C8B8 → warm blush stone
Warm Gold (magic/sparkle): #F5D5A0 → champagne honey
Pink (magic/bloom):        #F0C0D0 → sakura milk
Lavender (shadow tint):    #D0C0E8 → wisteria fog
Night Ambient:             #2A2A45 → deep indigo, never pure black
Shadow Tint:               #352D40 → warm violet-black
Wish Sparkle:              #FFE8D0 (warm) / #D8F0FF (cool)
Water:                     #88D0D8 → mint-celadon glacial
```

### Material Preset: Nikki

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Diffuse wrap** | Half-Lambert, wrap 0.5 | Soft shadow transition, no hard cel steps |
| **Specular** | 0.4–0.6 roughness, anisotropic | Satin sheen, fabric-direction highlights |
| **Clear coat** | 0.2–0.4 | Velvet/satin top sheen |
| **Sheen color** | #FFF5F0 | Warm rim at grazing angles |
| **Shadow tint** | #352D40 | Warm violet, not black |
| **Rim light** | Fresnel, intensity 0.3–0.5 | Warm-tinted, soft width |
| **Subsurface** | Screen-space, weight 0.2–0.3 | Soft pink scatter for foliage/fabric |

### Post-Processing Preset

| Parameter | Value |
|-----------|-------|
| **Bloom intensity** | 4–6 (heavy, soft) |
| **Bloom threshold** | 0.7–0.8 (low — many things bloom) |
| **Bloom tint** | #FFF5F0 (warm cream) |
| **Shadow toe** | Lifted +0.05–0.08 (never true black) |
| **Midtone contrast** | 0.85–0.9 (reduced, dreamy) |
| **Highlight rolloff** | Soft knee, bloom takes over before clip |
| **Saturation** | 0.9 (slightly desaturated) |
| **Color grade LUT** | Warm-gold bias mids, cool-lavender lift shadows |
| **DOF** | Near-field soft bokeh for gazebo close-up, distant blur |

### Particle Style

| Element | Spec |
|---------|------|
| **Sparkle sprite** | 4-point soft star, 16–32px, additive blend |
| **Floating mote** | 4–8px soft radial circle, additive, slow sin-bob |
| **Wish energy burst** | Multi-point radial gradient, gold→pink→cyan shift |
| **Motion** | Very slow drift (0.02–0.05 units/s), sin-wave oscillation |
| **Density** | 30–50 particles visible at any time |
| **Lifetime** | 8–15s, fade in/out with smoothstep |

---

## 3. 20-Minute Scene Breakdown

```
 ┌───────────────────────────────────────────────┐
 │  MINUTE  0–2:  B L E N D E R                 │
 │  PGA generates floating gazebo + island       │
 │  Exports FBX + .world.json manifest           │
 ├───────────────────────────────────────────────┤
 │  MINUTE  2–5:  T O U C H D E S I G N E R     │
 │  TOA imports FBX, applies Nikki post-FX       │
 │  Adds sparkle particles + floating motes      │
 │  Audio CHOP analyzes Melusina WAV             │
 │  OSC routes: /material/toon → UE              │
 ├───────────────────────────────────────────────┤
 │  MINUTE  5–8:  T D → U E   B R I D G E      │
 │  WIA imports .world.json into UE              │
 │  MPA applies Nikki material preset            │
 │  OSC live-links audio-reactive params         │
 │  Spout streams TD shader preview to UE         │
 ├───────────────────────────────────────────────┤
 │  MINUTE  8–12: U N R E A L   E N G I N E     │
 │  PPA spawns flower meadow via PCG             │
 │  MPA tunes Substrate Toon materials            │
 │  WIA sets up cinematic camera                  │
 │  Lighting: warm directional + heavy bloom PP   │
 ├───────────────────────────────────────────────┤
 │  MINUTE 12–16: R E N D E R   C A P T U R E   │
 │  Monolith captures hero render (4K)            │
 │  Material breakdown sheet captured             │
 │  Stats extracted (tri count, draw calls)       │
 │  SQA audits all outputs                        │
 ├───────────────────────────────────────────────┤
 │  MINUTE 16–20: D E P L O Y                    │
 │  portfolio_package.json compiled               │
 │  Figma template populated with captures        │
 │  Wix iframe preview validated                  │
 │  GitHub commit + GitHub Pages deploy            │
 └───────────────────────────────────────────────┘
```

---

## 4. Detailed Scene Specification

### 4.1 Gazebo Architecture (from Surreal Architecture Generator)

```
Style Genome: ZEN_SHRINE_AXIS (modified with Nikki whimsy modifiers)
Key elements:
  - Octagonal base, 4m radius
  - Arched openings on 4 sides (Gothic arch softened to round-top)
  - Dome roof with pagoda-tier influence (2 tiers)
  - Fabric canopy draped between pillars (cloth sim)
  - Wrought-iron filigree details (thin gold linework)
  - Floating stone steps leading up to platform

Modifications for Nikki style:
  - Scale pillars thinner (0.3m radius → 0.2m)
  - Add filigree to arch edges (curve-to-mesh with star-node terminals)
  - Dome → onion-dome hybrid (shallower, softer curve)
  - Material: Florawish terracotta (#E8C8B8) with ivy accents
  - Fabric: Pastel pink (#F0C0D0) satin with gold trim
```

### 4.2 Floating Island

```
Base: Elliptical stone platform, 12m x 8m
  - Thickness: 1.5m with eroded edge chamfer
  - Underside: Hanging vines + glowing crystal clusters
  - Surface: Painted moss/grass texture blend (stone→grass transition)

Surrounding elements:
  - 3 smaller floating rock fragments (3-5m diameter)
  - Connected by thin wishing-ribbon streams (curved splines with particle emitters)
  - Each fragment has a small flower cluster
```

### 4.3 Flower Meadow

```
Species (all stylized, painted textures):
  1. Wishbloom (large, 5-petal pastel pink) — hero flowers near gazebo
  2. Stardrop (small, white 6-petal) — fill density across island
  3. Dawnlace (tall, lavender spike) — vertical accent at edges
  4. Nikkorose (pale pink rose bush) — clustered at gazebo base

Placement rules (PCG):
  - Density falloff from gazebo center (lower near structure)
  - Slope threshold: <15° only (no flowers on edge chamfers)
  - Random scale: 0.8–1.2 for natural variation
  - Random rotation Z: 0–360°
  - Color variation: hue ±5°, saturation ±10% within species palette
```

### 4.4 Lighting

```
Directional Light:
  - Azimuth: 240° (late afternoon golden)
  - Elevation: 25° (long soft shadows)
  - Color: #FFF5E8 (warm cream)
  - Intensity: 8 lux

Skylight:
  - HDRI: Pastel sky gradient (#B5D8EB zenith → #E8D8D8 horizon)
  - Intensity: 1.5

Point Lights (decorative):
  - 4 lanterns on gazebo pillars
  - Color: #FFE0C0 (warm amber)
  - Radius: 3m, intensity: 3 cd
  - Bloom contribution: high

Post Process Volume:
  - Bloom: see Section 2 preset
  - Color grading: see Section 2 preset
  - Vignette: 0.15 intensity, soft
```

### 4.5 Camera Path (20-second cinematic loop)

```
Frame 0 (0s):    Wide establishing — island in center, 45° bird's-eye
Frame 240 (8s):  Medium orbit — camera at 60° elevation, slowly circling CW
Frame 420 (14s): Push-in — camera approaches gazebo entrance, 30° elevation
Frame 600 (20s): Close hero — camera at gazebo interior looking out at meadow
Frame 600 → 0:   Smooth loop back to establishing shot
```

---

## 5. TouchDesigner Component Architecture

### 5.1 Base Project: `_TouchDesigner/florawish_sanctuary.toe`

```
Container: /project1
├── /embody              ← Embody COMP (Envoy MCP server)
├── /geo                 ← Geometry container
│   ├── /gazebo          ← FBX COMP (loads from Blender export)
│   ├── /island          ← FBX COMP (floating island)
│   └── /flowers         ← Instancing setup for flower meadow
├── /render              ← Rendering pipeline
│   ├── /render_top      ← Render TOP (final output)
│   ├── /bloom           ← Multi-pass bloom chain
│   └── /color_grade     ← LUT TOP with Nikki grade
├── /particles           ← Particle system
│   ├── /sparkles        ← POP network: 4-star sparkle sprites
│   ├── /motes           ← POP network: floating ambient dots
│   └── /wish_burst      ← Trigger-based wish energy explosion
├── /audio               ← Audio analysis
│   ├── /melusina_in     ← Audio File In CHOP (VoiceSynth WAV)
│   ├── /pitch_analyzer  ← Pitch CHOP → OSC out
│   ├── /amp_analyzer    ← Amplitude CHOP → OSC out
│   └── /beat_detector   ← Beat CHOP → particle trigger
├── /osc                 ← OSC routing
│   ├── /osc_out_ue      ← OSC Out CHOP (→ UE port 8000)
│   └── /osc_out_blender ← OSC Out CHOP (→ Blender port 9000)
├── /spout               ← Spout streaming
│   ├── /spout_out_ue    ← Spout Out TOP ("TD_NikkiPreview")
│   └── /spout_in_ue     ← Spout In TOP ("UE_RenderTarget")
└── /ui                  ← Control panel
    ├── /preset_switcher ← Style preset buttons (Nikki/Madoka/Celestial)
    ├── /time_slider     ← Day/night cycle (0–1 float)
    └── /audio_viz       ← Waveform scope for Melusina audio
```

### 5.2 Key Networks (to be TDN-exported)

All networks externalized as `.tdn` files for git version control:

| Network | File | Description |
|---------|------|-------------|
| `/render` | `networks/nikki_post_fx.tdn` | Bloom + color grade + DOF chain |
| `/particles` | `networks/nikki_particles.tdn` | Sparkle + mote + wish burst POPs |
| `/audio` | `networks/melusina_audio.tdn` | Pitch/amp/beat analysis chain |
| `/osc` | `networks/osc_routing.tdn` | OSC bridge definitions |
| `/ui` | `networks/control_panel.tdn` | Preset switcher + time slider |

---

## 6. Daemon Architecture — Autonomous TD Production

### 6.1 Sentinel Runner: `deploy/start_td_loop.ps1`

```powershell
# start_td_loop.ps1 — TouchDesigner autonomous production daemon
# Runs continuous TOA cycle: audio analysis → particle update → OSC push → Spout health

param(
    [int]$IntervalSeconds = 60,
    [string]$SentinelName = "AGENT_LOOP_TICK_td_orch"
)

$ProjectRoot = "G:\EnvironmentPortfolio"
$SentinelPath = "$ProjectRoot\BS_GodFile\Saved\Audit\$SentinelName"
$StopPath = "$ProjectRoot\BS_GodFile\Saved\Audit\td_loop_STOP"

Write-Host "[TOA] TouchDesigner Orchestrator daemon starting..."
Write-Host "[TOA] Interval: ${IntervalSeconds}s | Sentinel: $SentinelName"

while ($true) {
    # Check stop signal
    if (Test-Path $StopPath) {
        Write-Host "[TOA] STOP signal detected. Exiting daemon."
        Remove-Item $StopPath -Force
        break
    }
    
    # Write heartbeat sentinel
    $tick = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
    @{ tick=$tick; agent="TOA"; status="running" } | ConvertTo-Json | Set-Content $SentinelPath
    
    # Execute TOA tick via Envoy MCP
    Write-Host "[TOA] Tick $tick — querying audio state..."
    # TODO: After Envoy is set up: invoke execute_python tool to run td_tick.py
    # python $ProjectRoot\BS_GodFile\Content\Python\td_bridge.py --tick
    
    Start-Sleep -Seconds $IntervalSeconds
}
```

### 6.2 TD Tick Handler: `BS_GodFile/Content/Python/td_bridge.py`

```python
"""
td_bridge.py — TouchDesigner bridge script for Unreal Editor environment.
Handles OSC communication, Spout health monitoring, and TD tick coordination.
Communicates with TouchDesigner via Envoy MCP (localhost:9870) or direct OSC.
"""
import json
import os
import socket
import struct
import time
from datetime import datetime

PROJECT_ROOT = r"G:\EnvironmentPortfolio"
TD_MCP_PORT = 9870
UE_OSC_PORT = 8000
TD_OSC_PORT = 9000
SENTINEL_PATH = os.path.join(PROJECT_ROOT, r"BS_GodFile\Saved\Audit\AGENT_LOOP_TICK_td_orch")
OSC_ROUTING_PATH = os.path.join(PROJECT_ROOT, r"BS_GodFile\deploy\osc_routing.json")


def load_osc_routing():
    """Load OSC route definitions."""
    try:
        with open(OSC_ROUTING_PATH) as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "version": "1.0",
            "routes": {
                "audio": {
                    "melusina_pitch": {"path": "/melusina/pitch", "type": "float", "range": [60, 2000]},
                    "melusina_amplitude": {"path": "/melusina/amp", "type": "float", "range": [0, 1]},
                },
                "material": {
                    "toon_params": {"path": "/material/toon", "type": "float_array", "size": 12},
                    "style_preset": {"path": "/material/preset", "type": "int", "range": [0, 4]},
                },
                "time": {
                    "day_night_cycle": {"path": "/time/cycle", "type": "float", "range": [0, 1]},
                },
            },
        }


def send_osc(host, port, address, *values):
    """Send OSC message via UDP."""
    # Build OSC message
    addr_bytes = address.encode("utf-8")
    addr_padded = addr_bytes + b"\x00" * (4 - len(addr_bytes) % 4)
    
    # Type tag string
    type_tags = "," + "".join("f" if isinstance(v, float) else "i" for v in values)
    type_padded = type_tags.encode("utf-8")
    type_padded += b"\x00" * (4 - len(type_padded) % 4)
    
    # Values
    value_bytes = b""
    for v in values:
        if isinstance(v, float):
            value_bytes += struct.pack(">f", v)
        elif isinstance(v, int):
            value_bytes += struct.pack(">i", v)
    
    message = addr_padded + type_padded + value_bytes
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(message, (host, port))
    sock.close()


def td_tick(melusina_pitch=440.0, melusina_amp=0.5, style_preset=0, day_cycle=0.5):
    """One tick of the TD orchestration loop.
    
    In production, these values come from Embody MCP querying the TD audio CHOPs.
    For autonomous daemon mode, the daemon queries TD via MCP and feeds values here.
    """
    routes = load_osc_routing()
    
    # Push audio parameters to Unreal Engine
    send_osc("127.0.0.1", UE_OSC_PORT, routes["audio"]["melusina_pitch"]["path"], float(melusina_pitch))
    send_osc("127.0.0.1", UE_OSC_PORT, routes["audio"]["melusina_amplitude"]["path"], float(melusina_amp))
    
    # Push material preset to UE
    send_osc("127.0.0.1", UE_OSC_PORT, routes["material"]["style_preset"]["path"], int(style_preset))
    
    # Push day/night cycle
    send_osc("127.0.0.1", UE_OSC_PORT, routes["time"]["day_night_cycle"]["path"], float(day_cycle))
    
    # Write heartbeat
    tick_data = {
        "tick": datetime.now().isoformat(),
        "agent": "TOA",
        "status": "ok",
        "pitch": melusina_pitch,
        "amplitude": melusina_amp,
        "preset": style_preset,
        "day_cycle": day_cycle,
    }
    with open(SENTINEL_PATH, "w") as f:
        json.dump(tick_data, f)


def set_preset(preset_id):
    """Set the Nikki-style material preset in UE via OSC.
    
    Presets:
      0 = Nikki (soft dreamy, pastel, heavy bloom)
      1 = Madoka (witch barrier, surreal, saturated)
      2 = Celestial (space, nebula, cool tones)
      3 = Itto (mythic carved, warm stone)
      4 = Sakura (Japanese, pink, delicate)
    """
    send_osc("127.0.0.1", UE_OSC_PORT, "/material/preset", int(preset_id))
    print(f"[TOA] Preset set to {preset_id}")


def verify_spout():
    """Check Spout stream health.
    
    Returns True if both TD→UE and UE→TD Spout streams are active.
    In production, this queries Envoy MCP for Spout TOP status.
    """
    # Placeholder — will query Envoy MCP: get_op("spout_out_ue") → check .isRunning
    return True


if __name__ == "__main__":
    import sys
    
    if "--tick" in sys.argv:
        td_tick()
        print("[TOA] Tick complete.")
    elif "--preset" in sys.argv:
        idx = sys.argv.index("--preset")
        preset_id = int(sys.argv[idx + 1]) if idx + 1 < len(sys.argv) else 0
        set_preset(preset_id)
    elif "--verify" in sys.argv:
        ok = verify_spout()
        print(f"[TOA] Spout health: {'OK' if ok else 'FAIL'}")
    else:
        print("Usage: td_bridge.py [--tick | --preset N | --verify]")
```

### 6.3 Daemon Orchestrator: `deploy/start_all_td_services.ps1`

```powershell
# start_all_td_services.ps1
# Launches all autonomous TouchDesigner production services

$ProjectRoot = "G:\EnvironmentPortfolio"
$AuditDir = "$ProjectRoot\BS_GodFile\Saved\Audit"

# Ensure audit directory exists
New-Item -ItemType Directory -Force -Path $AuditDir | Out-Null

# Clear old stop signals
Remove-Item "$AuditDir\td_loop_STOP" -ErrorAction SilentlyContinue
Remove-Item "$AuditDir\AGENT_LOOP_STOP" -ErrorAction SilentlyContinue

Write-Host "========================================"
Write-Host "  TouchDesigner Autonomous Production"
Write-Host "  Environment Portfolio Platform"
Write-Host "========================================"
Write-Host ""

# Service 1: TD Orchestrator Loop (60s interval)
Write-Host "[1/3] Starting TD Orchestrator daemon..."
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-File", "$ProjectRoot\BS_GodFile\deploy\start_td_loop.ps1",
    "-IntervalSeconds", "60",
    "-SentinelName", "AGENT_LOOP_TICK_td_orch"
) -WindowStyle Minimized

# Service 2: OSC Bridge Monitor (10s interval)
Write-Host "[2/3] Starting OSC bridge health monitor..."
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-File", "$ProjectRoot\BS_GodFile\deploy\start_osc_monitor.ps1",
    "-IntervalSeconds", "10"
) -WindowStyle Minimized

# Service 3: Spout Stream Watchdog (5s interval)
Write-Host "[3/3] Starting Spout stream watchdog..."
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-File", "$ProjectRoot\BS_GodFile\deploy\start_spout_watchdog.ps1",
    "-IntervalSeconds", "5"
) -WindowStyle Minimized

Write-Host ""
Write-Host "All TD services launched. Monitor via:"
Write-Host "  Saved/Audit/AGENT_LOOP_TICK_td_orch"
Write-Host "  Saved/Audit/osc_monitor_state.json"
Write-Host "  Saved/Audit/spout_stream_state.json"
Write-Host ""
Write-Host "To stop all services:"
Write-Host "  New-Item -Path '$AuditDir\td_loop_STOP' -ItemType File"
```

### 6.4 OSC Bridge Monitor: `deploy/start_osc_monitor.ps1`

```powershell
param([int]$IntervalSeconds = 10)

$AuditDir = "G:\EnvironmentPortfolio\BS_GodFile\Saved\Audit"
$StateFile = "$AuditDir\osc_monitor_state.json"

while ($true) {
    if (Test-Path "$AuditDir\td_loop_STOP") { break }
    
    $state = @{
        timestamp = (Get-Date -Format "o")
        ue_port_8000 = "active"    # TODO: UDP ping check
        td_port_9000 = "active"    # TODO: UDP ping check
        blender_port_9000 = "active"
    }
    
    $state | ConvertTo-Json | Set-Content $StateFile
    Start-Sleep -Seconds $IntervalSeconds
}
```

### 6.5 Spout Watchdog: `deploy/start_spout_watchdog.ps1`

```powershell
param([int]$IntervalSeconds = 5)

$AuditDir = "G:\EnvironmentPortfolio\BS_GodFile\Saved\Audit"
$StateFile = "$AuditDir\spout_stream_state.json"

while ($true) {
    if (Test-Path "$AuditDir\td_loop_STOP") { break }
    
    # In production: query Envoy MCP for Spout TOP status
    # For now: write heartbeat
    $state = @{
        timestamp = (Get-Date -Format "o")
        streams = @(
            @{name="TD_NikkiPreview"; direction="TD→UE"; status="active"},
            @{name="UE_RenderTarget"; direction="UE→TD"; status="active"}
        )
    }
    
    $state | ConvertTo-Json -Depth 3 | Set-Content $StateFile
    Start-Sleep -Seconds $IntervalSeconds
}
```

---

## 7. Single-AI-Prompt Showcase

The ultimate test of the unified MCP architecture. A single prompt entered into the AI agent should execute the entire vertical slice:

```
You are the Environment Portfolio MCP Orchestrator. You have access to:
- Blender MCP (localhost:9877): Surreal Architecture Generator, geometry export
- TouchDesigner Envoy MCP (localhost:9870): Real-time FX, particles, OSC routing
- Unreal Monolith MCP (localhost:9316): Scene composition, PCG, render capture

Execute the "Nikki Florawish Sanctuary" vertical slice:

1. In Blender: Generate a whimsical octagonal gazebo with a pagoda-onion dome,
   floating island platform (12m x 8m), and 4 draped fabric canopies.
   Use the ZEN_SHRINE_AXIS genome with Nikki modifiers (thinner pillars,
   softer arches, gold filigree). Export as FBX + .world.json.

2. In TouchDesigner: Import the FBX. Apply the Nikki post-FX preset:
   - Heavy soft bloom (intensity 5.0, threshold 0.75, tint #FFF5F0)
   - Color grade: lifted shadows (#352D40), warmth in midtones
   - Sparkle particles: 40x 4-point star sprites, gold→pink color, sin-wave drift
   - Floating motes: 50x soft radial dots, additive blend, slow random motion
   - Load Melusina WAV from VoiceSynthResearch/, run audio analysis CHOPs

3. Bridge to Unreal: Push OSC routes for material preset (0 = Nikki),
   audio-reactive params (pitch→shader warp, amplitude→particle spawn),
   and Spout stream the TD composited preview.

4. In Unreal: Import .world.json. Apply Nikki Substrate Toon materials
   (half-Lambert diffuse wrap, anisotropic satin specular, warm shadow tint).
   PCG-spawn flower meadow (Wishbloom, Stardrop, Dawnlace, Nikkorose)
   with slope<15° rule, density falloff from gazebo center.
   Set up cinematic camera: 20s orbital loop, golden-hour lighting.

5. Capture: Monolith hero render (4K), material breakdown, stats.
   Compile portfolio_package.json. Deploy to Figma template.

Report back with render paths, stats, and any errors.
```

---

## 8. Success Criteria

- [ ] Blender generates gazebo, island, fabric canopies in < 2 min
- [ ] TD imports FBX and applies Nikki post-FX (bloom, color grade) via Envoy MCP
- [ ] Sparkle and mote particles spawn and drift with correct Nikki aesthetic
- [ ] OSC routes deliver audio-reactive values from TD to UE
- [ ] Spout stream shows TD composited preview in UE viewport
- [ ] UE applies Nikki material preset to imported geometry
- [ ] PCG spawns flower meadow with correct density rules
- [ ] Cinematic camera orbits gazebo with smooth looping
- [ ] Hero render captured at 4K with correct bloom and color grade
- [ ] Material breakdown sheet captured
- [ ] Stats extracted (tris, draw calls, texture memory)
- [ ] portfolio_package.json validates against schema
- [ ] Total execution time < 20 minutes
- [ ] Visual output matches Nikki aesthetic reference card (Section 2)

---

## 9. File Inventory

| File | Purpose |
|------|---------|
| `Docs/NIKKI_VERTICAL_SLICE_PLAN.md` | This document |
| `deploy/start_td_loop.ps1` | TOA autonomous daemon |
| `deploy/start_all_td_services.ps1` | Multi-service launcher |
| `deploy/start_osc_monitor.ps1` | OSC bridge health monitor |
| `deploy/start_spout_watchdog.ps1` | Spout stream watchdog |
| `BS_GodFile/Content/Python/td_bridge.py` | UE↔TD OSC bridge + tick handler |
| `BS_GodFile/deploy/osc_routing.json` | Shared OSC routing schema |
| `_TouchDesigner/florawish_sanctuary.toe` | TD base project (to be created in Phase 1) |
| `_TouchDesigner/networks/nikki_post_fx.tdn` | Bloom + color grade network |
| `_TouchDesigner/networks/nikki_particles.tdn` | Particle system network |
| `_TouchDesigner/networks/melusina_audio.tdn` | Audio analysis network |
| `_TouchDesigner/networks/osc_routing.tdn` | OSC bridge network |
| `_TouchDesigner/networks/control_panel.tdn` | UI panel network |
