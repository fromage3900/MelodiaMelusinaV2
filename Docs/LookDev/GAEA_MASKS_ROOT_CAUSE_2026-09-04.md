# Why the Gaea masks were not visible — root cause (2026-09-04)

Supersedes the "Gaea material intake — CLOSED" section of
`Docs/Plans/SEA_ABOVE_PCG_DRESSING_PLAN_2026-09-04.md`. That section was wrong: importing
the weightmaps as **textures** is only half the pipeline, and two of its specific claims
did not hold. Corrections are marked below.

## The graph, stated exactly

`M_Master_Nikki_Landscape` wires each Gaea lane the same way:

```
Multiply_22 = LandscapeLayerSample["Snow"]  x  Lerp(A=1.0, B=Gaea_SlopeMask, Alpha=Gaea_SlopeWeight)
Multiply_23 = LandscapeLayerSample["Water"] x  Lerp(A=1.0, B=Gaea_WaterMask, Alpha=Gaea_WaterWeight)
                    |
                  Add_5  ->  Saturate_2  ->  Alpha of LinearInterpolate_8  ->  BaseColor
```

Two consequences follow directly from that shape, and together they are the whole answer.

**A mask can only ever subtract.** It multiplies a *painted* landscape layer weight. Where
a layer is unpainted the product is zero no matter what the mask contains, so a Gaea mask
can remove coverage but can never introduce it.

**The weight is a 0–1 blend factor, and the lerp is unclamped.** `Alpha=0` yields 1.0
(mask ignored); `Alpha=1` yields the mask itself. Anything above 1 drives the result
negative wherever the mask is below 1.

## Cause 1 — the weights were an order of magnitude out of range

Measured on `MI_Glacier_Landscape_Layered`:

| Parameter | Found | Valid range |
|---|---|---|
| `Gaea_SlopeWeight` | **13.1188** | 0–1 |
| `Gaea_WaterWeight` | **10.5679** | 0–1 |

At 13.12, a mask value of 0 evaluates to `1 + (0-1)*13.12 = -12.12`. Summed and passed
through `Saturate_2`, the blend alpha clamps to **0** across nearly the whole terrain — so
the extended-layer branch (`bUseExtendedLayers`) never blended in at all. The masks did not
merely fail to show; they actively suppressed the layer set.

Both are now **1.0**. Re-render moved 177,616 of 921,600 pixels (19%).

These values had been set to 1.0 in commit `4af6f72e` and were **not** committed as 13.12 —
the drift was live in the editor. Something is writing out-of-range values into this
instance; see Cause 4.

## Cause 2 — the mask/layer routing does not match the parameter names

The original graph called the Snow lane `Gaea_SlopeMask` and had no Rock mask lane. That
made the semantic contract ambiguous and left the exported Rock map unused. The master
now exposes `Gaea_SnowMask`/`Gaea_SnowWeight` for `LandscapeLayerSample["Snow"]`, keeps
`Gaea_WaterMask` on `LandscapeLayerSample["Water"]`, and adds a normalized
`Gaea_RockMask`/`Gaea_RockWeight` product on `LandscapeLayerSample["Rock"]` before the
extended coverage sum. `Gaea_SlopeMask` remains reserved for a future true slope or
procedural mask.

`Gaea_WaterMask` -> `LandscapeLayerSample["Water"]` is correct.
`Gaea_FlowMask` has no exported source and stays inert at weight 0 (unchanged, still right).

This semantic repair is implemented in `Content/Python/semantic_gaea_mask_wiring.py` and
saved to `M_Master_Nikki_Landscape`; the Glacier instance now overrides the three exported
semantic maps (`Gaea_SnowMask`, `Gaea_WaterMask`, `Gaea_RockMask`) and both new weights are
1.0.

## Cause 3 — the weightmaps were never applied as landscape paint

The four target layers exist with LayerInfo assets (`Base`, `Snow`, `Water`, `Rock`),
matching `contract.json`. Measured paint weight, sampled per-component:

| Layer | nonzero | max | mean | verdict |
|---|---|---|---|---|
| Base | 32/48 | 1.0000 | 0.4916 | healthy |
| Snow | 16/48 | 0.4980 | 0.1650 | painted |
| Water | 0/48 | 0.0000 | 0.0000 | **absent** |
| Rock | 21/48 | 0.0706 | 0.0092 | **effectively absent** |

`Water` and `Rock` are imported into the paint layers via
`Landscape.landscape_import_weightmap_from_render_target`, driven by
`Content/Python/import_gaea_landscape_paint.py`. After import, `Water` reads 0.15–0.48 at
points where its mask is bright.

**Measurement caveat, recorded because it produced a false result twice.** Water covers
**0.76%** of the map. A uniform 48-point sample expects ~0.37 hits, so "nonzero=0" is not
evidence of absence — it has to be sampled *at* bright mask pixels. An earlier sweep also
returned all-zero for every layer because it sampled one component across the whole
landscape, outside that component's own extent.

## Cause 4 — `W_Glacier_Rock` is a near-black export

| Weightmap | mean | max | coverage >10 |
|---|---|---|---|
| `W_Glacier_Rock` | 4.09/255 | **31/255 (12%)** | 15.5% |
| `W_Glacier_Water` | 1.91/255 | 255/255 | 0.76% |

The rock weightmap peaks at **12% weight**. Even wired perfectly it can never make the rock
layer read — which matches the measured Rock paint (max 0.0706) exactly, i.e. the paint
already came from this map and re-importing it is a no-op. **This is a Gaea-side export
problem, not a UE one.** Re-export the Rock layer with correct normalisation before
expecting rock to appear.

Water is a hard binary mask over 0.76% of the terrain — thin channels. It will never be a
dominant read, and that is presumably intended.

## Corrections to the earlier document

- **"Snow weightmap imported but not bound" — wrong.** `W_Glacier_Snow.uasset` did not
  exist. The staging PNG was present (18,830 bytes) but the import silently produced no
  asset and the script reported success. It is now genuinely imported (sRGB off, TC_MASKS).
- **"Gaea material intake — CLOSED" — wrong.** Texture import is half the pipeline; the
  paint-layer import is the other half and had never been run.

## Other out-of-range values on the same instance

Found alongside the weights, same signature — long decimals, far outside master defaults:

| Parameter | Master | Instance | Action |
|---|---|---|---|
| `Rock_TriplanarNormalStrength` | 1.0 | **6599.2773** | reset to 1.0 |
| `Rock_DetailAlbedoReference` | 0.18 | **-0.2281** | reset to 0.18 |
| `TriplanarPro_Scale` | 0.01 | 0.3452 | left — plausibly authored |
| `Rock_DetailAlbedoStrength` | 0.0 | 5.7556 | left — plausibly authored |
| `CymaticsLandscapeMaxEmission` | 1.0 | 1.4320 | left — plausibly authored |

A normal-strength multiplier of 6599 destroys the normal outright; a negative albedo
reference is not a valid pivot. The clustering of implausible long-decimal values suggests
an automated sweep or randomiser has run over this instance. **Worth finding that writer** —
resetting values it will overwrite again is treating a symptom.

## Version-control status — read this before assuming the work is safe

`.gitignore:111` is a blanket `Content/*`. Consequently:

- `MI_Glacier_Landscape_Layered.uasset` **has never been committed**, so the Gaea material
  work from `4af6f72e` was never actually version controlled.
- The SeaAbove landscape's 74 modified `__ExternalActors__` files (17.4 MB) carrying the new
  paint are likewise untracked, consistent with that level's existing state.

The small Gaea assets are force-added here. Bringing 17.4 MB of landscape external actors
under version control is a repo-policy decision and `.gitignore` is a protected file, so
that is left to the owner rather than decided unilaterally.
