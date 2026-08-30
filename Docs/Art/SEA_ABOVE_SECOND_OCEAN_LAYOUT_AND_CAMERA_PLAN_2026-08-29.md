# Sea Above — Second-Ocean Layout + Camera / Perception Plan — 2026-08-29

**Scope:** layout plan only. No asset writes, no editor mutation. This sits under
`Docs/Art/SEA_ABOVE_SYSTEM_INTEGRATION_VISUAL_SHADER_BREAKDOWN_2026-08-26.md` (authority on
material/VFX ownership) and consumes
`Docs/OCEANOLOGY_STYLIZATION_AND_TRAVERSAL_INTEGRATION_RESEARCH_2026-08-29.md` (authority on the
Oceanology seam).

**Sources read:** `MONOLITH_LEVEL_DESIGN_BIBLE_2026-08-26` §01, `SEA_ABOVE_TONIGHT_EXECUTION_AND_AGENT_HANDOFF_2026-08-26`
§C/G/H, the system-integration breakdown, `P0_MATERIAL_SEA_ABOVE_GATE_2026-08-27` (the only doc
carrying real blockout coordinates), `SESSION_CLOSEOUT_WATER_MATERIALS_2026-08-29`,
`OCEANOLOGY_WATER_COEXISTENCE_2026-08-15`, `UNIFIED_PPV_OCEANOLOGY_LOOKDEV_PLAN_2026-08-28`,
`HOUDINI_SEA_ABOVE_P0_AND_AAA_POLISH_PLAN_2026-08-28` §0.1, and the 16 external actors of
`LV_SeaAbove_Prototype` on disk.

**Level scope note:** this plan concerns `LV_SeaAbove_Prototype` only. `MelodiaIntegrationMap` is the
all-in-one systems/Echo test level and is not touched by any step here (see CLAUDE.md).

---

## 1. State on disk — what the level actually contains

16 World Partition external actors, four Data Layers.

| Actor | Layer | Recorded value | Source |
|---|---|---|---|
| `AOceanologyInfiniteOcean` (+ `M_Water_Oceanology_Melodia_Inst`) | DL_Water | real ocean, graft already assigned | research doc §2.4 |
| `AOceanologyManager`, `AOceanologyWaterVolume` | DL_Water | volume **still a 2 m cube** | Houdini plan §0.1 |
| `SeaAbove_FalseOceanPlane_Prototype` | DL_Water | **Z −5000 cm (−50 m)**, `MI_SeaAbove_FalseOcean_Clean` | gate doc |
| `SeaAbove_BellProxy_Prototype` | DL_Creature | **Z −18000 cm (−180 m)** sphere | gate doc |
| `SeaAbove_CentralCore_Proxy` | DL_Creature | **Z −16000 cm (−160 m)** sphere | gate doc |
| `SeaAbove_ObservationCliff_Prototype` | — | cylinder at origin | gate doc |
| 2 × membrane proxies on `M_SeaAbove_Membrane_Prototype` | DL_Creature | — | external actors |
| `SeaAbove_UpwardDroplets_Prototype` (Niagara) | DL_Creature | — | external actors |
| Lighting: DirectionalLight, SkyLight, SkyAtmosphere, **ExponentialHeightFog**, VolumetricCloud | DL_Lighting | — | external actors |
| `SM_MassiveSandstoneCliff_03`, 12 floating islands | DL_Islands | — | external actors / Houdini §0.1 |
| `CineCameraActor` (hero cam), `SeaAbove_PlayerStart`, `SeaAbove_QuillTrigger_Cutscene` | — | — | external actors |

Two competing false-ocean materials exist, meant to be A/B'd by swapping on the plane:
`MI_SeaAbove_FalseOcean_Clean` (v10 line, 20 overrides — currently bound) and
`MI_SeaAbove_FalseOcean_Oceanology` (17 overrides, Beaufort 2, `Biolum_Weight` 0.35).

---

## 2. The reframe the layout depends on

The design bible says the hidden creature is *"an inverted jellyfish whose translucent bell mass is
large enough to be mistaken for a second ocean and sky."*

Read literally: **the second ocean and the Bell are not two objects at two depths. The false ocean
plane *is* the Bell's crown, seen from above and not yet understood.** The reveal works because the
surface the player has already accepted as water is shown — by radial anatomy travelling across it on
the pulse — to have been a membrane the whole time.

The current blockout does not encode this. It has a plane at −50 m and a separate sphere at −180 m —
a diagnostic arrangement ("sphere under a pool"), not the intended read. The gate doc calls the level
*"intentionally a disposable blockout at this stage"*, so this is expected. But the next layout pass
has to resolve it, because two of the doc's own visual gates — *"Bell perimeter remains hidden"* and
*"pulse creates the biological realization"* — cannot both pass in the current arrangement.

**Layout consequence:** the Bell's crown must be tangent to, or just beneath, the false-ocean plane
along the hero sightline, and its bulk must fall away by curvature — not sit as a discrete object at
a lower altitude.

---

## 3. Doc correction — the depth gap is not height fog

`SEA_ABOVE_SYSTEM_INTEGRATION_VISUAL_SHADER_BREAKDOWN_2026-08-26` §2 diagrams the middle layer as
`ATMOSPHERIC DEPTH GAP — Exponential Height Fog / volumetric haze` and calls it *"the primary scale
trick."* The instinct is right; the named mechanism is wrong for the geometry that got built.

The false ocean sits **below the real water surface**, so the player sees it *through* Oceanology's
Single Layer Water. Rays into the water are attenuated by the SLW absorption/scattering path, not by
`ExponentialHeightFog` — height fog integrates along the above-water ray and governs the horizon, not
the sub-surface look.

Depth-gap tools, in order of authority:

1. **Real-ocean SLW absorption + scattering** — `Absorption`, `DeepScatteringColor`,
   `ShallowScatteringColor`, `PhaseGLow/High` on `MI_SeaAbove_SurfaceOcean_Oceanology`. This is the
   primary scale trick.
2. **False-ocean emissive** — the `Biolum_*` set on the graft (already 0.35 weight) punching back
   through that attenuation.
3. `ExponentialHeightFog` — above-water horizon only.
4. `VolumetricCloud` — sky read, and the under-sky mirror if it is kept.

**The lever that makes the trick work:** tune absorption to extinguish *faster than 50 m of water
justifies*. The brain then reads kilometres of attenuation over metres of geometry, and attenuation
wins. Physical correctness is not the target — tonight-execution §C already says so
("Perceptual ambiguity is").

**Derived constraint, and it sets the layout:** the false ocean's depth is not an aesthetic choice.
It is bounded by the real ocean's absorption extinction depth. Measure extinction first, then place
the plane at roughly 70–80 % of it so it reads as *barely* present. If extinction lands near 60–70 m,
the existing **−50 m is already close to correct and should not be moved.**

---

## 4. Second-ocean layout spec

### 4.1 Altitudes

| Layer | Z | Set by |
|---|---|---|
| Hero camera eye | **+10 to +25 m** above sea level — see §6.1, do not go higher | perception, not terrain |
| Real ocean (Oceanology) | 0 | gameplay water authority, unchanged |
| False ocean plane | **−50 m (keep)**, re-confirm against measured absorption extinction | §3 |
| Bell crown, on the hero sightline | **−55 to −65 m** — just beneath the plane, not 130 m under it | §2 |
| Bell centre | crown − R, with R ≈ 2.5–3 km | §4.3 |
| Under-sky dome | below the Bell, or cut — see §4.4 | breakdown §10 |

`SeaAbove_CentralCore_Proxy` (−160 m) sits above `SeaAbove_BellProxy_Prototype` (−180 m), so the
current pair is already "core inside bell". Keep that relationship; move both as a unit.

### 4.2 Plane extent — the thing that is actually undersized

Tonight-execution suggests *"roughly 500 m × 500 m for first-pass composition."* That is a
composition placeholder and it will not survive a hero frame.

A flat plane's far edge sits at depression `atan(Δh / D)`. With the camera at +25 m and the plane at
−50 m (Δh = 75 m), a 500 m plane (250 m half-extent) puts its far edge **17.7° below the horizon** — a
hard, visible, measurable line. That is precisely the failure the breakdown doc warns about: the
player reads *"a second plane 150 m lower"*, and the illusion is over in one frame.

**Rule: the plane's edge must never render.** Two ways, use both:

- extend the plane past attenuation extinction in every playable direction — at ~1.2 km extinction a
  **6 km × 6 km** plane is ample and costs nothing (world-UV blend is 1.0 and world texture scale is
  0.0012, so tiling is world-space and independent of plane size);
- let attenuation kill it before the edge is reached, so nothing sharp ever appears.

Subdivision only matters if WPO is used. The false ocean is a static presentation plane with
`WaveSpeed 0.06` / `WaveAmplitude 0.018`; a modest grid is sufficient.

### 4.3 Bell curvature does the edge-hiding for free

For a sphere of radius R, the crown drops by `sag = R − √(R² − d²)` at horizontal distance d.

At R = 3 km and d = 1.2 km (the attenuation horizon): sag = **251 m**. Across the entire visible field
the Bell falls 251 m below its crown — far past extinction — and fades to nothing at the frame edges
on its own geometry.

This satisfies the *"Bell perimeter remains hidden"* gate with no framing trickery, and it is why the
Bell wants to be huge-and-tangent rather than small-and-deep. It also delivers the bible's *"the
viewer does not read a sphere; they read a huge curved biological presence whose total size is
unknown."*

### 4.4 Under-sky

Breakdown §10 already marks the under-sky optional and first to cut. Under this layout it is largely
redundant — the Bell crown occupies the space it would have filled. Keep it only if the Bell's
fade-out leaves a dead value floor. **Cut before cutting the Bell pulse**, per the existing
instruction.

---

## 5. The four perception cues, and the veto rule

The horizon of any sufficiently large flat plane sits at the observer's eye level *regardless of the
plane's altitude*. Both oceans therefore produce a horizon at the same screen-space height and
superimpose. Position cannot separate them. That leaves exactly four cues, and each is a lever:

| Cue | Handling | Parameter already documented |
|---|---|---|
| **Texture gradient** | Match *apparent angular* texel density between the two surfaces, not physical scale. Equal apparent density ⇒ the brain infers equal distance ⇒ the second surface reads as another *world*, not a lower floor. | world texture scale `0.0012`, `WorldUVBlend 1.0` |
| **Motion parallax** | False ocean nearly stationary. Slow motion at apparently-near range = enormous scale (the cloud-layer trick). | `WaveSpeed 0.06`, `WaveAmplitude 0.018`, `FoamIntensity 0.05` |
| **Aerial perspective** | Non-physical attenuation, per §3 — a haze budget of kilometres spent over metres. | SLW `Absorption` / scattering |
| **Occlusion** | The veto rule below. | — |

> **Veto rule: nothing may be visible touching both surfaces in the same frame.**

A single rock, wreck spar, kelp strand, island waterline or shadow that spans the real ocean *and* the
false ocean is a measuring stick, and it collapses the illusion instantly and permanently. This
outranks composition preferences.

**The 12 floating islands (DL_Islands) are the live risk.** An island with a visible waterline on the
real ocean *and* a visible relationship to the false ocean is exactly that ruler. Options, in
preference order: keep islands out of frame in Shots B and C; float them clear of the water so they
have no waterline at all; or place them beyond extinction.

Two smaller levers worth taking:

- **Toon banding as separation.** Research doc §4 establishes the ocean cannot use the Substrate Toon
  BSDF and must band by quantising Base Color (`Toon_Bands`, `Toon_Weight`) before the SLW output.
  Normally a limitation — here it is useful. Run `Toon_Weight` *higher* on the false ocean than the
  real one so the second sea reads as a rendered, non-physical thing. Free art-directable separation.
- **Differential motion for scale**, per tonight-execution §H: near droplets normal speed, mid waves
  slower, false horizon almost stationary, Bell on a 10–20 s contraction with no bobbing.

---

## 6. Camera plan

Three shots, per tonight-execution §G, on the 20–30 s beat sheet in breakdown §11.

### 6.1 Camera height: gain the band with focal length, not altitude

The visible false-ocean band spans from the horizon down to `atan(Δh / D_extinction)`. Raising the
camera widens that band — and a wide band reads as a **floor**, which is the failure mode. So the
overlook wants to be *low*, counter to the instinct to put the player on a big cliff.

With extinction at 1.2 km and the plane at −50 m:

| Eye height | Δh | Band height |
|---|---|---|
| +10 m | 60 m | 2.9° |
| +25 m | 75 m | 3.6° |
| +100 m | 150 m | 7.1° |
| +200 m | 250 m | 11.8° |

**Keep the hero eye under ~30 m above the real sea surface.** Recover the band's presence in frame
with a long lens instead — at 16:9 the vertical FOV is ≈ 22.9° at 50 mm, 13.6° at 85 mm, 11.6° at
100 mm. A 3.6° band is 16 % of frame at 50 mm but **31 % at 100 mm**, with no altitude penalty and no
extra plane surface exposed. That is the forced-perspective play, and it is the camera strategy in one
line.

Check `SeaAbove_ObservationCliff_Prototype` against this and lower it if it puts the eye above ~30 m.

### 6.2 The three shots

| Shot | Lens | Eye | Framing | Purpose |
|---|---|---|---|---|
| **A — Normality** (0–8 s) | 24–28 mm | +10 m | horizon on the upper third, tilt near level, false ocean outside the Fresnel window | serene, readable coast; no monster read |
| **B — Second Horizon** (8–14 s) | 50–65 mm | +10 to +25 m | tilt down 6–10° to open the Fresnel window; band appears in the **mid-ground** | *"another horizon under the sea"* |
| **C — Biological Realization** (14–30 s) | 85–100 mm | unchanged from B | **locked off**, band at ~30 % of frame, pulse travels radially across it | the anatomy read |

The mid-ground placement in Shot B is not arbitrary. At grazing angles near the horizon the real
ocean's Fresnel reflectance is high and you see sky, not through; steeply down, reflectance is low and
you see into the water. The false ocean is therefore naturally most visible in a band at moderate
viewing angles — exactly the "second horizon" the bible describes. Frame for that band; do not fight
it.

### 6.3 Movement rules

- **No dolly toward or away from the horizon, ever.** A push-in changes the two planes' parallax at
  different rates and hands the player the depth solution.
- **Shot C is locked. Zero movement during the pulse.** Any move during the reveal lets the geometry
  be solved at the exact moment the illusion has to hold.
- If B→C wants motion, use a slow **crane down** — it lowers the eye, flattens the band and
  *strengthens* the effect. A lateral dolly is second-safest; a rotation is safe.
- Lens changes between shots, never within a shot. (A dolly-zoom would be thematically apt for
  "geometry stopped being trustworthy" but is a much louder stylistic claim than this reveal needs.)
- Composition rule from tonight-execution §G stands: **the player should need several seconds to
  realise the Bell is present.**

---

## 7. Risks found while planning

1. **The ink/outline blendable may draw an edge on the very thing that must be edgeless.** The unified
   PPV stack is 4 blendables including `MI_StorybookOutline_Premium_Hero_Dream` (weight 1.0) and
   `MI_MelodiaInk_PortfolioHero` (currently **0.31, plan target 1.0**). These are depth/normal-driven
   silhouette passes. A hard ink line on the false-ocean plane boundary or the Bell proxy destroys the
   reveal. **Validate Shot C with ink at its target 1.0, not at 0.31** — otherwise raising the weight
   later silently breaks the shot.
2. **`MI_SeaAbove_FalseOcean_Oceanology` is read-only on disk.** Research doc §8 and closeout §5.6: it
   is in the 2,719 read-only `.uasset` population; saves fail and the API returns False rather than
   raising. Clear the read-only bit before any A/B tuning, or the tuning will appear to work and
   persist nothing.
3. **`AOceanologyWaterVolume` is still a 2 m cube.** Cheap to fix, and the cutscene lookdev reads wrong
   without it (Houdini plan §2.2).
4. **The false ocean must never become a Water Body.** A hard rule in three docs and a stop condition
   in breakdown §14. Nothing here changes that: it stays a presentation plane, never queried by
   `UMelodiaWaterInteractionSubsystem`.
5. **Nothing here has been seen rendered.** Closeout §1 and research doc §8 both flag the graft as
   structurally verified only. Every number in §4 and §6 is a derivation to be confirmed by eye, not a
   measurement.

---

## 8. Order of operations

Ordered so the cheapest thing that can invalidate the rest happens first.

| # | Step | Editor? | Why here |
|---|---|---|---|
| 1 | Open `LV_SeaAbove_Prototype` and look at it. Sweep `Toon_Weight` 0→1, `Toon_Bands` 2→8 | yes | Research doc §7 step 1 — everything downstream is guesswork until the band look is chosen. Wiring is already done. |
| 2 | Measure the real ocean's absorption extinction depth | yes | Sets the false-ocean depth (§3); confirms or moves the −50 m. |
| 3 | Extend the false-ocean plane to ~6 km; confirm no edge renders from the hero camera | yes | §4.2 — the single biggest layout defect. |
| 4 | Lower the hero eye under ~30 m; set Shot C to 85–100 mm; re-frame | yes | §6.1. Cheap, and it changes what every later tuning decision looks like. |
| 5 | Re-seat Bell crown tangent beneath the plane at R ≈ 2.5–3 km; keep Core inside Bell | yes | §2 / §4.3 |
| 6 | Audit the 12 islands against the veto rule; move or float them | yes | §5 |
| 7 | A/B `MI_SeaAbove_FalseOcean_Clean` vs `..._Oceanology` on the plane (clear read-only first) | yes | Closeout §2 — the swap is free; the false ocean is not gameplay authority. |
| 8 | Validate Shot C with the ink blendable at 1.0 | yes | §7.1 |
| 9 | Scale the water volume; then the pulse/PIE evidence run | yes | Houdini plan §2 — the existing P0 pillar path, unchanged by this plan. |

Steps 1–2 are one editor sitting and gate everything else. `LV_SeaAbove_Prototype` is opened for
these steps only; return the editor to `MelodiaIntegrationMap` afterwards.

---

## 9. Gates this plan must pass

Adopted verbatim from breakdown §15 (Visual):

- 16:9 hero frame;
- real ocean reads first;
- false horizon reads as impossible space **before** anatomy;
- Bell perimeter remains hidden;
- pulse creates the biological realization;
- one clean 20–30 second replay passes.

Added by this plan:

- **no visible plane edge** from any playable camera position or any point on the walk-in path;
- **no object visibly touching both surfaces** in any frame of the three shots.

Evidence pair worth capturing while the Data Layers are already authored: toggle `DL_Creature` off for
a "before" frame and on for the "after", from the identical locked Shot C camera. A clean A/B for the
reveal, at the cost of one toggle.
