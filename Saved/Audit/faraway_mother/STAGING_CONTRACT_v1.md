# Faraway Mother — Landscape-first staging contract (v1)
Date: 2026-09-21  
Level: `LV_FarawayMother_Prototype` only  
**Never** mutate `L_MelusinaMorning`.

## Owners
| Lane | Owner |
|------|--------|
| Landscape create + height-aware PCG exec | Grok Bot |
| Landscape layer MIs + Copernicus Faraway sheets (Sheen→NikkiPearlSheen) | Material Artist |
| Green / go-no-go each layer | User |

## Hard gates (post–Morning disaster)
1. **One UE writer at a time** (Monolith scene-context begin/end).
2. **No mass destroy+save** scripts on a live portfolio map.
3. **PCG snap = Landscape only** (reject Spire / dress / other PCG / null hits).
4. After every layer: **SAVE → RELOAD → VERIFY** before the next.
5. No hand-spawn of km-scale meshes; blown bounds → **skip**, don’t autofit.
6. Deterministic seeds (`20260829` unless user overrides).

## Stage order
1. **Landscape only** — `LM_FarawayMother_Terrain` (or hero carve). Player Start + walk collision. No PCG. Save/reload/verify.
2. **Material ground** — Landscape layers + `MI_Copernicus_Faraway*` (fix AlabasterDrape under-wire). Prove look. Save/reload/verify.
3. **Height-aware PCG by biome** — WeaveRidge → LaceCanopy → FrillValley → ResonantSeamWay via existing `MEL_mother_*`, density caps. Save/reload/verify each.
4. **Hero statics last** — Heart Gate, silhouette, walkways. Data layers / HLOD as specified.
5. Beauty / lookdev plates only after layers 1–4 verify.

## Stop conditions
- Any non-Landscape snap hit in a PCG pass → halt that graph, fix filter, do not save-over.
- Editor hang / unexpected wipe → stop, restore from Autosave/git, do not “clean” the world.
- Work on Morning requested → refuse unless user explicitly greens Morning by name.

## Status
Draft for green. **No mutate until User + Material Artist green this contract.**
