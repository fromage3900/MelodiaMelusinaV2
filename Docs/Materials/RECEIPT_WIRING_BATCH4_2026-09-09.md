# Receipt — Wiring Batch 4 (Universal + Wool read-back) — 2026-09-09

**Status:** READ-BACK (live Monolith; **no** save_packages / recompile_material)  
**Date:** 2026-09-09  
**Index:** [Docs/Materials/README.md](README.md) · [Cleanup plan](../Plans/MATERIALS_WIRING_FLIPBOOK_CLEANUP_2026-09-09.md)  
**Owner lane:** New Bot

## Hard rules obeyed
- `validate_material` with `fix_issues=false` only
- Parameter / compile-stats read-back only
- **Owner Ctrl+S** for any intentional package save
- Agents must not call Monolith `save_packages` or `recompile_material`

## Universal — `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal`

### validate_material
| Severity | Count | Notes |
|----------|------:|-------|
| **error** | **33** | All `broken_texture_ref` — **not** missing Cymatic param names |
| warning | 119 | islands / unused |
| info | 1 | |

### Cymatic_* scalars present (defaults)
| Param | Value |
|-------|------:|
| Cymatic_ModeN | 4 |
| Cymatic_ModeM | 6 |
| Cymatic_BeatPulse | 0 |
| Cymatic_BassIntensity | 0 |
| Cymatic_MidIntensity | 0 |
| Cymatic_EmissiveScale | 0 |
| Cymatic_IridescenceShift | 0 |
| Cymatic_UVDistortion | 0 |
| CymaticAmplitude | 0 |

Related: `AudioBeatGain=1.5`, `AudioBassGain=1`, `AudioMidGain=1`. Drive scalars at 0 expected if MPC writer feeds them at runtime — confirm in PIE with `MPC_Cymatics_Driver`.

### get_compilation_stats
- `is_compiled`: true · VS 313 / PS 1184 / samplers 9 / expressions 1299

### Open
1. Resolve or quarantine **33 broken_texture_ref** (owner rebind + Ctrl+S).
2. PIE confirm MPC Beat/Bass/Mid drive Universal paths.

## Wool — `/Game/Melodia/Companions/ChoralSheep/Materials/M_Chorus_Wool_Master`

### validate_material
| Severity | Count | Notes |
|----------|------:|-------|
| **error** | **35** | All `broken_texture_ref` |
| warning | 105 | |
| info | 1 | |

### Chladni / Mode read-back
| Param | Value | Note |
|-------|------:|------|
| Cymatic_ModeN | 2 | not 0 |
| Cymatic_ModeM | 3 | not 0 |
| ChladniEmissiveStrength | 0.5 | |
| ChladniSheenStrength | 0.5 | |
| ChladniIntensity | 0 | gated |
| HarmonizeActive | 0 | gated |
| BeatAccent | 0 | gated |

### Open
1. broken_texture_ref cleanup / owner bind.
2. Optional lookdev: ungated ChladniIntensity/Harmonize/BeatAccent — owner + Ctrl+S.

## Flipbook Lane D
See [RECEIPT_OFFLINE_WORLDGRID_FLIPBOOK_2026-09-09.md](RECEIPT_OFFLINE_WORLDGRID_FLIPBOOK_2026-09-09.md). `M_SurrealFabric_Flipbook` still **MISSING**.

## Not done
- Graph rewires · texture rebinds · any Monolith save/recompile · SDF Enhanced (QUARANTINE)
