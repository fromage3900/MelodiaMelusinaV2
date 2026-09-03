# TouchDesigner Project Workspace

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
