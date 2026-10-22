# Poitou v2 — Current State (locked 2026-10-20 4:15 PM ET)

## Goal
L_Poitou_v2 (/Game/EnvSandbox/Poitou/L_Poitou_v2) fully driven by the live Houdini Engine HDA
(poitou_layout_live.hdalc, ~2 s recook). Identity: "Musical but French" — Marais Poitevin / Maillezais Abbey.
Silhouette is French; music lives in rhythm, ornament, sound. Grid 0.6 m, bar = 2.4 m, 128 BPM.

## Status
| # | Step | Owner | State |
|---|------|-------|-------|
| 1 | Terrain: 1 km core, iles 4-12 m, gentle 1-3 km ring, M_Poitou_Landscape + 8 mask layers | TAL | in progress |
| 2 | Existing room-shell / builder HDAs on building points; SM_Cathedral_* church/abbey; quays along canals | TAL | in progress |
| 3 | Placeholder -> real mesh swap (Nikki mapping) | TAL | queued |
| 4 | MI_Poitou_* (6) + Poplar_Band1-3 + FarStone, fade 80000-300000 | MA scripts / TAL runs | queued |
| 5 | Horizon: 3 poplar bands, inter-band mist, faint far spire | TAL/MA/Nikki | queued |
| 6 | DA_PianoWalkway_Poitou (D4-D5, 24 cm keys, oak/tar, SW_Poitou_KeyPluck) on footbridge; spline sampler next | TAL from AE spec | queued |
| 7 | BP_Poitou_SpanBob, poplar sway, bird loops | AE offline | in progress |
| 8 | Hero sculpts: ruin pieces, pollard ash, punt+pole, lock/bridge details, square props | Brennan | open |

## Files
- Houdini: C:\Users\froma\agent-tools\poitou_houdini\ (build_poitou.py, build_poitou_hda.py, hda\, export\, ue\)
- MA scripts: ma_poitou_materials.py, ma_poitou_horizon.py (same folder)
- Box: /workspace/poitou_layout/ (style_contract.md, layout_plan.md, heatmaps/, houdini/)

## Rules
- TAL is the only agent in Unreal. Save only Poitou packages. No deletes without Brennan's OK
  (Landscape_old_7/_8 hidden, not deleted). No PIE, no editor restart, no git/installs, off D:.
- L_MelusinaMorning untouched. Demo edits (SW_WaveHarp_Orchestra_C4 muted etc.) stay until Brennan decides.
- Reuse existing systems (PCGPianoKeyboard, builders, room shells) — never reinvent.

## Adopted from Nikki's Infinity Nikki brief (/workspace/poitou_board/INFINITY_NIKKI_BRIEF.md)
- Lumen/PBR kept; toon from shapes, lilac shadow #8A93C8, warm sun #FFE8C8; env albedo 0.08-0.85; <=4 terrain layers in view.
- Horizon bands: near 0-150 m, mid 150-800 m (HLOD), far >800 m cards; fog #CFDDEA to ~40% far contrast; abbey readable at 1 km.
- Maillezais visible from >=70% of walkable area; poplar rows aim at it; secondary landmark every 150-200 m.
- Procedural: foliage/reeds/poplars. Hand-placed: abbey, punts, walkway, bridges. Prop clusters <=6 m, 60/30/10, >=12 m gaps.
- Canals width multiples of 2.4 m, teal #6FA89A, patchy duckweed. Accordion/harp zones crossfade >=10 m.
- Abbey keeps real silhouette, 2.4 m bays; ornament 1.3-1.5x, flowers up to 2x.
- Albedo floor 0.08 linear; exception: accents <5% of screen (Tar #26221E stays).
- (brief v2) Each zone has its own music cue, accordion in >=1 layer; architecture mixes >=2 historical layers (Romanesque/Gothic abbey + 17-19th c. lime-wash village); water edges organic except built quays; each zone names its priority (beauty / world consistency / platforming).
