# Wool Lab Review — 2026-08-28 (Flat vs Worley vs Lit)

## What we tested
You said renders looked off (flat pastels) and wanted to experiment. We built a lab:

| Test | What | Strength | Reading at thumbnail | Reading at 100% |
|------|------|----------|----------------------|-----------------|
| **01 Flat** | Pastel base `sat 0.38` only — shipping Albedo intent | 0% | Clean, Inf Nikki soft | Wool comes from **light + normal + sheen**, not color |
| **02 Worley 12%** | `Worley-mimic` mottle (dots → blur) at 12% overlay — Houdini COP intent | Low | Barely visible at thumb | Soft cellular mottle, visible at 512+ close-up |
| **03 Worley 25%** | Same at 25% | Med | Faint mottling at thumb | Editorial, more “mottled pastel”, risks stains in UE |
| **04 Worley12 + fibers** | 12% + ~1100 directional 1px strokes at 12-18 alpha | Low+ | fibers invisible at thumb (by design — they’re 1px) | Fine fleece grain at 100% |

Plus pop test: `sat 0.38` (current) vs `sat 0.52` (Infinity Nikki pop) both at Worley12.

All albedos live in `Saved/Audit/choral_sheep/experiments/` while shipping albedos stay untouched at `Saved/Audit/choral_sheep/houdini_variants/` (flat).

## Evidence

- `experiments/_EXPERIMENT_WoolLab_SuperSheet.png` — 12 PCs × 4 variants (see image, top row C = PC00)
- `experiments/_COMPARE_PC04_E.png` — E on full 2048 strip (flat | w12 | w25 | w12+fibers)
- `experiments/_EXPERIMENT_Saturation_Pop.png` — LEFT 0.38 vs RIGHT 0.52, both w12
- `experiments/lit_demo_*.png` — quick fake-lit sphere (flat albedo × radial light) for E/C/Fs — proves flat already reads as volume under light

## Findings

1. **Worley12 at thumbnail is *supposed* to be invisible.** At game distance (sheep 400-1200cm, ShellCard LOD) you will not see albedo mottling — wool will read from groom + sheen + your sculpted normal. Worley25 starts to survive thumbnail but looks busy close-up. Recommendation: **keep Worley ≤12% if we bake it, or keep 0% and let grooming do the work.**

2. **Fibers at 1px do not survive downscale.** They’re a close-up micro-detail for 2K inspection, not for 256 thumb. They’ll be crushed by UE texture compression (BC7) at 1K. If we want fiber, it should be in normal/rough or groom, not in albedo.

3. **Saturation pop (0.52) kills the Nikki softness.** RIGHT column is punchier but loses the dusty resonance garden. Keep 0.38 for coats; pop can be reserved for accent emissive/bell.

4. **Lit sphere (flat) proves flat is fine.** Even without Worley, a sphere lit top-left at 512 reads as wool volume — highlight + AO does more than mottling. Your sculpted normals + `wool_clump_scale 0.62-0.68` groom + `sheen 0.46-0.625` will carry the rest.

## Choices — pick one to promote

- **A) Ship flat** (current `houdini_variants/`). Cleanest, most Inf Nikki, safest for LOD. Promote nothing, keep experiments as audit.
- **B) Promote Worley12** — Bake 12% Worley into main albedos: `python Tools/Houdini/experiment_wool_lab.py --size 1024 --out Saved/Audit/choral_sheep/houdini_variants` with `--strength` 0.12 (needs re-run via lab → promote script).
- **C) Promote Worley12+fibers** — Same but with 1px fibers (my least recommended — fibers better in normal).
- **D) Pop saturation** — Rebuild all 12 at `sat 0.52` (more vibrant, less dusty).

We can also blend: flat albedo + sculpted normal (you bring) + groom is the *intended* stack (see `ChoralSheepDefinition.json` LOD bands). That stack was the original TONIGHT_ASSEMBLY plan.

## Groom note
Groom 12ABCs in `Saved/Audit/choral_sheep/grooms/` are still placeholders (60b). Real strands need `hython build_choral_groom_hip.py + cook_groom_variants.py`. Their contact sheet reads correctly: Fs shaggiest, C/B tightest.

## Next step
Tell me A/B/C/D, and I’ll promote + rebuild 1024 + update `variant_recipe.json` + run `batch_create_choral_sheep_mis.py` wiring. Or say “hybrid” and we’ll keep flat for far LOD and Worley12 for hero close-up only.
