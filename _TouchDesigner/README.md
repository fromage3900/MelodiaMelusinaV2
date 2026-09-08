# TouchDesigner Project Workspace

## 2026-09-08 — Current live-performance authority

For current Melodia performance / concert / Capstone 01 work, read **before editing the project**:

1. `Docs/MELODIA_LIVE_VISUAL_IDENTITY_CONTRACT_2026-09-08.md`
2. `Docs/MELODIA_SHOW_SYSTEM_ARCHITECTURE_2026-09-08.md`
3. `Docs/ACTUAL_LIVE_SHOW_PIPELINES_RESEARCH_2026-09-08.md`
4. `Docs/PIPELINE_RECIPES_CHORAL_SHEEP_2026-09-08.md`
5. `Docs/AGENT_BUILD_CONTRACT.md`
6. `Docs/CHORAL_SHEEP_CAPSTONE_TD_IMPLEMENTATION_PLAN_2026-09-08.md`

Visual references:
`../Docs/References/ChoralSheepCapstone/REFERENCE_MANIFEST.md`

**Authority correction:** TouchDesigner owns Melodia's live visual interpretation and performance networks. Unreal remains the canonical game/world authority. The older `Docs/TD_GRANDMASTER_MELODIA_PLAN.md` is historical where it describes TD as a broad real-time SSOT, generic portfolio viewer, or five-style-preset authority.

Current concert rule:

> **Steal the timing, not the branding.**

Current flagship proof:

> **QUIET → C ROOT HIT → Chladni Fleece → AFTERIMAGE**


This directory is the TouchDesigner project root for the Environment Portfolio Platform.
The active project is `grandmaster_melodia/grandmaster_melodia7.22.toe` on the `G:` workspace.
Embody/Envoy controls that running project through `http://127.0.0.1:9870/mcp`.

## Quick Start

1. Open TouchDesigner 2025.32460+.
2. Open `grandmaster_melodia/grandmaster_melodia7.22.toe`.
3. Confirm the Embody COMP is enabled after every TD restart.
4. Verify the Envoy MCP listener on `http://127.0.0.1:9870/mcp`.
5. Check `C:/EnvironmentPortfolio/.embody/envoy.json` for the active TD PID and project.
6. Tag networks for externalization (lctrl + lctrl on any COMP/DAT).
7. Export networks via Ctrl+Shift+U, or Envoy `export_network`, into `networks/`.

The workspace-level `.mcp.json` now registers the same Envoy bridge, so agents launched from
`C:\EnvironmentPortfolio\BS_GodFile` can use the live TD project.

## Directory Structure

```
_TouchDesigner/
├── grandmaster_melodia/       ← Active TD project and versioned snapshots
├── components/                ← Reusable .tox components
│   ├── nikki_post_fx.tox
│   ├── nikki_particles.tox
│   ├── melusina_audio.tox
│   └── osc_router.tox
├── networks/                  ← TDN-exported networks and live graph snapshots
│   ├── nikki_post_fx.tdn
│   ├── nikki_particles.tdn
│   ├── melusina_audio.tdn
│   └── osc_routing.tdn
├── shaders/                   ← GLSL prototypes
│   ├── toon_nikki.glsl
│   ├── toon_madoka.glsl
│   ├── toon_celestial.glsl
│   └── toon_itto.glsl
└── exports/                   ← Rendered outputs, screenshots
```

## Nikki Aesthetic Reference

See `Docs/NIKKI_VERTICAL_SLICE_PLAN.md` Section 2 for the complete Nikki color bible,
material presets, post-processing specs, and particle style guide.

## MCP Integration

The `.mcp.json` at the EnvironmentPortfolio root registers all three MCP servers:
- Envoy (TD): `localhost:9870`
- Monolith (UE): `localhost:9316`
- Blender MCP: `localhost:9877`
