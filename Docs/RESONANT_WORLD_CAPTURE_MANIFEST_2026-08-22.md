# Resonant World Capture Evidence Manifest

Date: 2026-08-22
Repository: `C:\EnvironmentPortfolio\BS_GodFile`
Owner: Resonant World / lookdev integration

## Purpose

`Content/Python/resonant_world_capture_manifest.py` is the read-only bridge
between a deterministic score/asset constellation and the overnight lookdev
lane. It exposes four canonical slots:

| Slot | Movement | Required output |
|---|---|---|
| Sakura ambience | `petal_cantata` | `breakdown_niagara_sakura_ambience_1920x1080.png` |
| Zen shrine axis | `star_loom` | `pcg_zen_shrine_axis_route_proof_1920x1080.png` |
| Baroque Escher ornament | `dissonant_expanse` | `breakdown_baroque_escher_ornament_1920x1080.png` |
| Nikki surface polish | `petal_cantata` | `materials_nikki_surface_polish_2048x2048.png` |

Each slot returns its score ID, constellation ID, absolute existing source
asset paths, intended camera/lighting/material state, candidate PNG paths,
dimensions, hashes, and an explicit verdict. The manifest never treats a
filename as approval and never copies, renders, or publishes an image.

The isolated render-only staging namespace is
`/Game/_PROJECT/Levels/RenderTests/`. It is explicitly separated from
`L_WP_SakuraDream`, Headquarters BFG, source graphs, gameplay maps, and
save/gameplay state.

## Current evidence verdict

The current local scan has zero clean-approved slots. It has observed PNG
candidates for all four slots, but those candidates remain rejected or
unreviewed. The SakuraDream PIE candidate
`C:\EnvironmentPortfolio\BS_GodFile\Saved\Screenshots\Monolith\LookdevLane3\L_Render_SakuraDream_beauty_raw.png`
has an explicit runtime/lookdev rejection: black/checker frames and
post-marker `Error`/`Ensure` matches. It must not enter webfront intake.

The material preview files under
`C:\EnvironmentPortfolio\BS_GodFile\Saved\Screenshots\Monolith\LookdevLane3\`
remain useful A/B evidence, but are not clean standalone captures when they
show preview geometry, debug presentation, or an unresolved material state.

## Commands

Read-only CLI scan:

```powershell
python -B Content/Python/resonant_world_capture_manifest.py --seed 3900 --output Saved/Audit/resonant_world_capture_manifest_3900.json
```

Offline MCP read:

```powershell
'{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"melodia_resonant_world_get_capture_manifest","arguments":{"seed":3900,"movement_id":"all","chunk_x":0,"chunk_y":0}}}' | python -B deploy/melodia_mcp_server.py
```

The MCP tool is read/verify-only. It is policy-covered in
`specs/mcp_tool_policy.v1.json`; its output is not a PIE or render approval.

## Promotion rule

The webfront lane receives a PNG only when all of the following are true:

- the exact target output exists at the manifest path;
- dimensions match the slot contract;
- a clean standalone visual review confirms no editor chrome, frustums,
  debug icons, clipping, empty gradients, or preview geometry; and
- the owning runtime/lookdev evidence links a fresh report/log with no
  post-marker `Error`/`Ensure` matches.

Until then, report the exact source paths and rejection reason, not a success
claim or a placeholder render.
