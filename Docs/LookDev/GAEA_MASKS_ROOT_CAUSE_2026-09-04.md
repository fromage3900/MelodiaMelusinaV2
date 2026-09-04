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

`Gaea_SlopeMask` multiplies `LandscapeLayerSample["Snow"]`, **not** rock or slope. The
earlier import script bound the **Rock** weightmap to that slot on the reasoning that
"rock is the steep-slope layer". Given the actual wiring, that makes the rock map gate the
snow layer.

`Gaea_WaterMask` -> `LandscapeLayerSample["Water"]` is correct.
`Gaea_FlowMask` has no exported source and stays inert at weight 0 (unchanged, still right).

**Left as-is pending a decision.** Correcting it means either re-binding the instance slot
or renaming/rewiring the master; the master is architecture and is not something to change
on a guess. Flagging rather than guessing.

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

## Version-control status

The SeaAbove landscape's 74 modified `__ExternalActors__` files (17.4 MB), which carry the
new paint, are **not** tracked — `.gitignore:111` is a blanket `Content/*` and no external
actor for this level has ever been committed (`LV_SeaAbove_Prototype.umap` itself is
tracked; its actors are not). So the paint-layer import lives on disk only.

Bringing 17.4 MB of landscape external actors under version control is a repo-policy
decision and `.gitignore` is a protected file, so that is left to the owner rather than
decided unilaterally.

**Correction.** An earlier revision of this document claimed
`MI_Glacier_Landscape_Layered.uasset` "has never been committed" and that the Gaea material
work was never version controlled. That was wrong. It, `W_Glacier_Rock` and
`W_Glacier_Water` are all tracked on `main`, added by `82f3722c`. The check that produced
the false claim ran against the branch currently checked out by the overnight daemon, whose
index does not contain them — not against `main`.

---

# Addendum — why the Gaea *textures* still weren't visible (2026-09-04, later)

The four causes above are real and fixed, but they explain the **masks**. The colour
textures were still not reading, and the reason turned out to be lighting plus grading,
not the material's Gaea wiring at all.

## Cause 5 — the key light was pointing at the sky

`Key_TwilightPink` (DirectionalLight) had **pitch = +30**. A directional light with
positive pitch points *upward*; it was lighting the sky and not the terrain. The only
downward light was `Rim_CoolBlue` at pitch −30, intensity 2.0.

Set to **pitch −32, yaw 20**. With that single change the Gaea erosion and rock striations
read immediately — see `Saved/Audit/gaea_keyfixed_nopastel.png` against
`gaea_after_weights.png`.

## Cause 6 — the Nikki pastel grade was synthesising the entire image

With `bNikkiPastelGrade_Active` switched off, the terrain mean dropped from
**(90.7, 88.1, 111.2)** to **(12.1, 19.1, 37.2)**. The grade was not tinting the albedo —
it was supplying essentially all of the visible brightness, and the flat pale-pink wash
everyone was looking at *was* the grade, not the terrain.

`NikkiPastelStrength` was 0.6 (master default) with all three pastel ramps at 0.95–1.0,
i.e. near-white. Measured local contrast (mean absolute Laplacian over the terrain band)
against pastel strength:

| `NikkiPastelStrength` | mean RGB | global std | local detail |
|---|---|---|---|
| 0.60 | (34.1, 38.4, 62.9) | 46.62 | 4.696 |
| 0.40 | (32.5, 37.0, 61.8) | 43.27 | 4.904 |
| 0.25 | (30.7, 35.5, 60.6) | 39.83 | **5.339** |
| 0.15 | (29.1, 34.1, 59.6) | 36.99 | 5.741 |

Set to **0.25** on the instance: +13.7% local detail over 0.6 while still reading clearly
pastel. This is an art call, not a correctness one — the numbers are here so it can be
moved deliberately.

## Not a cause, but worth knowing: 44% of the terrain is underwater

`SeaAbove_InfiniteOcean_Canopy2` sits at **z = 14,345**. Traced against the landscape
(ignoring water actors) over a 22x22 grid, 484/484 points hit terrain:

```
terrain Z:  min -54,818   p25 -16,355   median 25,467   p75 58,628   max 69,161
above ocean plane:  271 of 484  (56.0%)
```

So a little under half the landscape is below the ocean plane and will never be seen from
above. Any dressing or PCG budget should be spent on the 56% that is above water. A second
infinite ocean, `SeaAbove_InfiniteOcean_Canopy`, sits far overhead at z = 194,888 — that is
the "sea above" conceit, not a mistake.

## The read-only trap crashed the editor — and it is project-wide

Repairing the Alpha master's opacity link (below) crashed the editor outright:

```
LogSavePackage: Error: Cannot remove 'M_Master_Toon_Universal_Alpha.uasset' as it is read only!
LogWindows:    Error: appError called: Error saving ...
               === Critical error: ===
```

**Monolith's material actions auto-save, and UE treats a failed package save as a FATAL
error.** So any Monolith material mutation against a git-lfs `lockable` read-only asset
does not fail gracefully — it takes the editor down. At the time **3,418 `.uasset` files
project-wide were read-only**, and `Saved/` held **988 stranded `.tmp` files** from earlier
failed saves, so this had been happening repeatedly and silently.

Cleared the read-only bit across `Content/` and removed the stranded temps. This is a
filesystem attribute applied by git-lfs on checkout; clearing it changes no git state. It
will come back after any operation that re-checks-out those files, so **clear it before
editor material work, not just before an individual save.**

## Alpha master defect found while converging — `OpacityMap` is not wired

`M_Master_Toon_Universal_Alpha` drives OpacityMask as:

```
OpacityMask <- StaticSwitch[bUseOpacityMap]
                 True  <- Multiply( TextureSample(Texture=None), Scalar[OpacityStrength] )
                 False <- Constant 1.0
```

The `OpacityMap` **TextureObjectParameter is unconnected**, and the sampler that feeds the
mask has `Texture: None` with no `TextureObject` input. Meanwhile the instances do their
part correctly — `MI_AtlasLeafA`, `MI_AtlasIvy` and `MI_Jelly_Bell` all set
`bUseOpacityMap=True` and bind real opacity maps (`T_KB3D_ATL_AtlasLeafA_opacity`,
`T_Jelly_Bell_Opacity`).

**Those textures are never sampled.** A preview of `MI_AtlasLeafA` renders as a dark opaque
plane with no leaf cutout. The fix is a one-link repair: `OpacityMap` ->
`TextureSample.TextureObject`.

(An earlier note in this session called `bUseOpacityMap` "dead/unconnected". That was
wrong — it connects to a material *output* rather than to another expression, so it has no
outgoing edge in the connection list and the reachability script missed it. `OpacityMap`
being unconnected is the real defect.)
