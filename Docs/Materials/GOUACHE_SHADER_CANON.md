# Gouache / Watercolour Shader - Canon (M_Master_Toon_Universal)

**Status:** WORKING on spheres, 2026-10-22. **NOT yet verified on Melusina's outfit** (see section 7).
**Owner decision:** Toon_Universal carries the general gouache stack; `M_Master_Nikki` stays hero-only
(it keeps its own `MF_MeluGouacheWash`, applied 2026-10-22, hair MI only).

## 1. What it is
One default-OFF static switch, `bGouache_Active`, on `M_Master_Toon_Universal`. Off, every instance renders exactly as before
(the switch picks the original wiring). On, it splices a tagged stage (`ToonGouache:`) in front of three pins of the Substrate Toon BSDF:

| Pin | Stage |
|---|---|
| BaseColor | the full gouache function (Custom HLSL, below) |
| Normal | paper relief from the pigment map's R channel |
| Roughness | lerp toward `Gouache_ChalkRoughness` (chalk matte) |

No new master, no PPV, no post-process. Texture reads: the packed pigment map (2 taps, one rotated/rescaled for de-tiling) + the flipbook (2 taps, frame-lerped).

## 2. The physical model (why each channel exists)
Gouache/watercolour behave like this, and each channel does one job:

| Ch | Content | Physical role | How it is built |
|---|---|---|---|
| R | paper height | what pigment settles into | Rebelle 7 `Papers/Default/Aquarelle.png` (256 px, tileable), FFT-upsampled to 1024 |
| G | granulation | pigment sitting in R's valleys | `(1-R)^1.4 * (0.45 + 0.55*grain)`; grain = real Rebelle granulation extracted from the owner's swatch |
| B | wet edge (signed, 0.5 = neutral) | darker rim, lighter inner halo | gradient magnitude of the band-limited wash density of the swatch; rim minus a blurred halo |
| A | flocculation / backrun bloom | cauliflower-edged density variation | band-pass of the swatch density, roughened by the grain |

Granulation is derived from paper height, never independent noise.

## 3. The function (BaseColor stage), in order
1. **Soft-stepped light:** wrap N.L against `Gouache_KeyLightDir`, two smoothstep bands; the terminator is pushed by the bloom field (`BleedJitter`) so it bleeds like pigment wicking into paper.
2. **Cool-shifted shadows:** shadow side lerps to `Gouache_ShadowTint` (violet) and gains saturation. Hue changes; it does not just darken.
3. **Chalk lift** in the light band; roughness raised by the Roughness stage.
4. **Granulation:** map G, heavier in shadow.
5. **Wet edge:** map B (rim darkens, halo lifts) plus a pooled line where the two light bands meet.
6. **Pooling:** fresnel darkening at the silhouette.
7. **Backrun bloom:** thresholded A: darker cauliflower rim, lifted core.
8. **Paper tooth:** low-contrast R modulation.
9. **De-tiling:** the pigment map is sampled twice, the second rotated ~0.5 rad and scaled by `Gouache_DetileScale`.

## 4. Temporal / animated
- **Flipbook** `T_Gouache_PoolFlipbook`: 4x4 frames of 256 px, a 16-frame loop. R = wet edge, G = bloom, B = smoothed bloom. Swirl is **baked in** by advecting the fields through a periodic curl-noise flow with a two-phase blend (frame 16 equals frame 0). The material owns the clock (`Gouache_FlipFPS`; Fix-A canon: never Niagara SubUV), frame-lerped between neighbours, mips off, clamp.
- **Swirl drift:** a slow sinusoidal UV drift (`Gouache_SwirlSpeed`, `Gouache_SwirlDrift`) on the pigment samples.
- **Boil:** frame-stepped UV jitter (`Gouache_BoilFPS`, `Gouache_BoilAmount`), default OFF (FPS 0), for a hand-painted granulation shimmer.
- Design choice (Jev, advisory only; the model string was `meituan/longcat-2.5-preview:free`, not `jev-1.13.0`): option A, flipbook-first, to avoid runtime flow advection in the instruction budget.

### Live drive from UDS (added 2026-10-22; built, compiles clean, NOT yet proven by eye)
The stage reads UDS's own collection `UltraDynamicWeather_Parameters` (written by the sky every tick; no new writer):
- **Key light:** `lerp(Gouache_KeyLightDir, Gouache_SunSign * 'Sun Vector'.rgb, Gouache_SunFollow)`. UDS's Sun Vector is the direction the light *travels* (its default is straight down), so the toward-sun direction is its negative: `Gouache_SunSign` defaults to -1 and is flippable without recompiling. In the editor viewport the collection holds its asset default, so shading uses a top-down light; the live sun only appears in PIE / gameplay.
- **Wet:** `BleedJitter *= 1 + Wet * Gouache_WetBleedGain` (wet paper bleeds more; UDS `Wet` / rain).
- **Wind:** `SwirlSpeed *= 1 + WindIntensity * Gouache_WindSwirlGain`, `FlipFPS *= 1 + WindIntensity * Gouache_WindFlipGain`.
- **Keyframing:** UDS exposes Time of Day, Wetness / Rain and Wind as actor properties, which Sequencer can key; the gouache follows because it reads the collection. Per-object keyframes: key the `Gouache_*` scalars on a dynamic material instance (Sequencer material parameter track). **A global keyframe-only multiplier collection is NOT possible as a new MPC** (see section 8, the 2-collection limit); it would have to be added to an existing collection, which is an owner decision.

## 5. Parameters (group `08 | Gouache`)
Scalars:

| Name | Default | Range |
|---|---|---|
| `Gouache_Strength` | 1 | 0 - 1.5 |
| `Gouache_UVTiling` | 2.2 | 0.5 - 64 |
| `Gouache_DetileScale` | 0.37 | 0.1 - 2 |
| `Gouache_FlipFPS` | 4 | 0 - 24 |
| `Gouache_FlipAmount` | 1 | 0 - 1 |
| `Gouache_FlipTiling` | 1.2 | 0.25 - 16 |
| `Gouache_SwirlSpeed` | 0.15 | 0 - 2 |
| `Gouache_SwirlDrift` | 0.02 | 0 - 0.1 |
| `Gouache_PaperMean` | 0.5 | 0 - 1 |
| `Gouache_PaperGrain` | 0.14 | 0 - 0.5 |
| `Gouache_Band1` | 0.36 | 0 - 1 |
| `Gouache_Band2` | 0.64 | 0 - 1 |
| `Gouache_BandSoft` | 0.09 | 0 - 0.3 |
| `Gouache_BleedJitter` | 0.6 | 0 - 0.8 |
| `Gouache_ShadowMix` | 0.85 | 0 - 1 |
| `Gouache_ShadowSat` | 0.3 | 0 - 1.5 |
| `Gouache_ChalkLift` | 0.08 | 0 - 0.4 |
| `Gouache_GranAmount` | 0.95 | 0 - 1 |
| `Gouache_EdgePool` | 1 | 0 - 1 |
| `Gouache_EdgeHalo` | 0.6 | 0 - 1 |
| `Gouache_PoolAmount` | 0.55 | 0 - 1 |
| `Gouache_PoolPower` | 3 | 0.5 - 8 |
| `Gouache_BloomThresh` | 0.5 | 0 - 1 |
| `Gouache_BloomSoft` | 0.12 | 0 - 0.3 |
| `Gouache_BloomEdge` | 0.95 | 0 - 1 |
| `Gouache_BloomLift` | 0.7 | 0 - 1 |
| `Gouache_BoilFPS` | 6 | 0 - 24 |
| `Gouache_BoilAmount` | 0.015 | 0 - 0.2 |
| `Gouache_NormalStrength` | 0.18 | 0 - 4 |
| `Gouache_TexelSize` | 0.000976562 | 0.0001 - 0.05 |
| `Gouache_ChalkRoughness` | 0.92 | 0 - 1 |
| `Gouache_SunFollow` | 1 | 0 - 1 |
| `Gouache_SunSign` | -1 | -1 - 1 |
| `Gouache_WetBleedGain` | 2 | 0 - 8 |
| `Gouache_WindSwirlGain` | 1.5 | 0 - 8 |
| `Gouache_WindFlipGain` | 0.5 | 0 - 4 |

Vectors:

| Name | Default (RGBA) |
|---|---|
| `Gouache_ShadowTint` | (0.62, 0.55, 0.96, 1.0) |
| `Gouache_KeyLightDir` | (0.4, -0.3, 0.85, 0.0) |

Textures: `Gouache_PigmentTex` = `T_Gouache_Pigment_RGBA` (BC7, linear, 1024); `Gouache_FlipTex` = `T_Gouache_PoolFlipbook` (BC7, linear, 1024, mips off, clamp).
Both in `/Game/EnvSandbox/Materials/Textures/Gouache/`.

## 6. Build + reproduce
- Offline (repo `tools/gouache/`, Blender 5.2 Python, `-I` mode): `psd_to_gouache.py` (Rebelle PSD paint layer to seamless density), then `final_tiles.py` (clean grain tile), then `build_pigment_rgba.py` (pigment map + flipbook). Verified 2026-10-22: a rerun reproduces the imported maps **byte-identically**.
- In UE: `Content/Python/expand_toon_gouache.py` (`main(compile_now=...)`). It **never deletes nodes** (see section 8): a rerun retags the previous generation as `ToonGouacheLegacy#...` and builds a new one.
- Backup: `/Game/EnvSandbox/Materials/Masters/_Backup/M_Master_Toon_Universal_PreGouache_20261022`.
- Test instances: `/Game/Melodia/Materials/Lookdev/MI_GouacheSphere_Toon_OFF`, `_ON`, `_ONstrong`.

## 7. Verification (evidence, not claims)
Verified 2026-10-22 from editor-viewport screenshots of three spheres, same material, same lighting:
- ON vs OFF clearly differ: OFF is a smooth gradient; ON shows pigment mottling, paper texture and a violet shadow side; ONstrong shows heavy granulation and cell-like wash contours.
- **Animation is live:** two screenshots minutes apart, per-sphere core, mean absolute pixel difference: OFF (control) 0.53, ON 4.07, ONstrong 5.52 (11.5% of ONstrong pixels changed by more than 12 levels).
- Shader compile confirmed from the **log** (no `Failed to compile` for the sphere MIs after the fix). `is_compiled` and the Monolith instruction stats are NOT reliable: they read true / 0 while the permutation had failed.
- Captures: `Saved/Gouache/Sphere/toon_spheres_v4_fixed.png` and `toon_spheres_v4_t2.png`.

**Not verified:** that the key light actually follows the UDS sun (a two-shot test on 2026-10-22 was void: the viewport camera moved between shots; verify in PIE by changing UDS Time of Day and watching a gouache sphere's terminator); the look on Melusina's skirt/outfit; the wet-edge rim as a visible line at game camera distance; the flipbook loop point by eye; pixel-shader instruction count / cost; skinned-mesh behaviour (the stage uses `VertexNormalWS` and `Time`).

## 8. Traps recorded
- **HLSL variable collisions kill the permutation silently.** `float rim` declared twice (`redefinition of 'rim'`) made every gouache-ON instance fall back to the default checker material while `is_compiled` still read true. Always grep `Saved/Logs/BS_GodFile.log` for `Failed to compile Material` after a compile.
- **A material may reference at most TWO MaterialParameterCollections.** Toon_Universal already uses `MPC_Melodia_Palette`; UDS's weather collection is the second. A third (`MPC_Gouache_Live`, created and then abandoned 2026-10-22) failed every gouache-ON permutation with `Material references too many MaterialParameterCollections`. The asset `/Game/EnvSandbox/Materials/Functions/MPC_Gouache_Live` is **unused and should be deleted in a closed editor**.
- **Never `delete_material_expression` from Python on this master:** it crashed the editor with `Assertion failed: !IsRooted()` (MaterialEditor, 2026-10-22). Retag instead; sweep legacy nodes in a closed-editor session.
- **Keep gouache OFF on Melusina's skin, face (`SBW_MELUSINA_006/007`, face SDF), outline and iris materials.** With the earlier crude stage on, the face went black and the eyes disappeared.
- Her outfit is on separate Wardrobe meshes: Shirt/Boots/Accessories on `M_Master_Nikki`, Skirt on Toon_Universal (three MIDs), hair and iris on Nikki. Toon_Universal gouache can only reach the skirt and body/props.
- Unrelated compile errors seen in the same log (`DreamColor`, `DreamIntensity`, `Composition` undeclared in an unnamed material's Custom node) are **not from this work**; they need their own owner.
- Rebelle licence: the paper tile is Rebelle's asset, owner-licensed; confirm the EULA before shipping the raw tile (it is processed and packed here, not shipped raw).

## 9. Instance suite (all on `M_Master_Toon_Universal`, `bGouache_Active` ON, parameter overrides only, `/Game/Melodia/Materials/Lookdev/`)
| Instance | Use | Character |
|---|---|---|
| `MI_Gouache_Toon_Preset` | default starting point | master defaults |
| `MI_Gouache_Toon_Cloth` | skirts, drapery | more bleed, softer relief, lighter chalk |
| `MI_Gouache_Toon_Stone` | architecture, props | heavy granulation, strong pooling, rougher chalk |
| `MI_Gouache_Toon_Soft` | gentle surfaces (NOT skin/face) | soft bands, little granulation, no relief |
| `MI_Gouache_Toon_Wet` | water-adjacent, rain, portals | max bleed, strong wet edge, fast flipbook, more swirl |
| `MI_Gouache_Toon_FoliageLive` | foliage | boil on, high wet/wind gains (leaf textures still to be bound) |
Rule of use: skin, face, outline and iris stay OFF.

## 10. Research basis
- **Curtis, Anderson, Seims, Fleischer, Salesin (1997), "Computer-Generated Watercolor"** - the physical model: shallow-water pigment flow, edge darkening, granulation, backruns; too slow for real time, which is why the stage fakes it with baked fields. [paper](https://www.cs.princeton.edu/courses/archive/fall00/cs597b/papers/curtis97.pdf)
- **Lei & Chang (2004), real-time watercolour with per-pixel hardware** - edge darkening and granulation as shader effects. [paper](https://www.cs.nthu.edu.tw/~chunfa/pcm2004.pdf)
- **Luft & Deussen (2005), interactive watercolor animations** - temporal coherence of the paper texture. [poster](https://graphics.uni-konstanz.de/publikationen/Luft2005InteractiveWatercolorAnimations/Luft2005InteractiveWatercolorAnimations_Poster.pdf)
- **Montesdeoca et al. (2017), art-directed real-time watercolour** - hand tremor, pigment turbulence, colour bleeding, paper distortion, edge darkening, and granulation with pigment accumulating in the paper valleys. This is the model the pigment map's G channel follows. (Described from a search summary; the link was not in the results, so read the paper before citing it externally.)
- Our departure from all of these: the fields are **baked from the owner's own Rebelle swatch** (real wet-media behaviour) and animated by a baked looping flipbook, rather than simulated or filtered per frame.

## 11. Open / tonight (render session + P0 assembly)
1. **Judge the skirt in PIE** (`HighResShot` on the live session), then assign suite MIs by asset class: skirt -> Cloth, architecture/props -> Stone, foliage -> FoliageLive, wet/portal -> Wet. Tune with scalars (no recompile).
2. **Gouache portals + VFX for P0:** portal fixture meshes on `MI_Gouache_Toon_Wet`; sprite/ribbon VFX stay on the canonical Niagara masters (no new masters), as unique MIs that sample `T_Gouache_PoolFlipbook` / `T_Gouache_Pigment_RGBA` for pigment edges (Fix-A canon: material owns the flipbook clock). Needs the P0 portal asset list from `specs/p0/`.
3. **Nikki parity:** move the gouache stage into one `MaterialFunction` called by both masters so her skirt and her Nikki-mastered shirt/boots/hair match; Nikki's `MF_MeluGouacheWash` should read the same pigment map.
4. **Closed-editor session:** sweep the legacy `ToonGouacheLegacy#` nodes, delete the unused `MPC_Gouache_Live` asset, and run the C++ build below.
5. **C++ (henshin / WaveHarp form work):** uncommitted + partly staged in `Source/BS_GodFile/MelodiaIntegration/` (`MelodiaWaveHarpCombatComponent`, `Tests/MelodiaWaveHarpFormTests.cpp`, `MelodiaWaterChorus`). Needs a closed-editor `BS_GodFileEditor Win64 Development` build, then `Melodia.WaveHarp.*` automation tests. Not built or verified by this work.
6. Optional: a soft-skin variant with the face SDF, a second Rebelle swatch for pattern variety, the LiquiGen hair sparkle, the Rebelle EULA check on the paper tile.
