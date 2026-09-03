# Niagara stub replacement map — 2026-08-01

## Evidence basis

The 2026-08-01 library audit identifies the following as actual visible-output prototypes, not merely stylized sprite effects: `NS_ConstellationTwinkle`, `NS_ConstellationDraw`, `NS_SakuraPondShimmer`, and `NS_SakuraLanternMotes`. The project already has advanced systems for those effect roles.

## Candidate replacements

No source system or map assignment was changed. The role-matched advanced systems were duplicated into `/Game/EnvSandbox/VFX/Candidates/AdvancedReplacements/`:

| Legacy stub | Candidate system | Derived from | Intent |
|---|---|---|---|
| `NS_ConstellationTwinkle` | `NS_ConstellationTwinkle_AdvancedCandidate` | `NS_FairyDust` | readable magical twinkle field |
| `NS_ConstellationDraw` | `NS_ConstellationDraw_AdvancedCandidate` | `NS_MagicTrail` | authored constellation-drawing path/ribbons |
| `NS_SakuraPondShimmer` | `NS_SakuraPondShimmer_AdvancedCandidate` | `NS_Uni_RainRipples` | GPU planar water response |
| `NS_SakuraLanternMotes` | `NS_SakuraLanternMotes_AdvancedCandidate` | `NS_EmberMotes` | warm lantern-adjacent motes |

Every candidate has clean Niagara compilation diagnostics. The generic Niagara validator reports `System::IsValid()` false for several GPU ambient systems while their GPU scripts are fully valid; this is a validator limitation, not a compile failure. `MagicTrail`'s event-receiver spawn warning is the known false positive documented in the library audit.

## Replacement policy

1. Test a candidate in the existing map location and camera.
2. Capture before/after with identical placement.
3. Swap only that placed actor's Niagara asset after visual approval.
4. Retain the source system until the map reference and capture are signed off.

## Separate SDF lane

The six `NS_SDF_*` systems are prototype systems, but they have their own candidate lane and should not be casually replaced by unrelated atmospheric effects. Their visible result now comes from dedicated/reused SDF materials and actual Niagara count/lifetime/loop bindings; promote them according to their intended environmental role.
